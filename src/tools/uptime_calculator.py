"""
Tools for elevator uptime/downtime analysis
Implements the core business logic for elevator mode analysis
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import pytz

# Mode status mappings as defined in the specification
UPTIME_MODES = {
    "ANS", "ATT", "CHC", "CTL", "DCP", "DEF", "DHB", "DTC", "DTO", 
    "EFO", "EFS", "EHS", "EPC", "EPR", "EPW", "IDL", "INI", "INS", 
    "ISC", "LNS", "NOR", "PKS", "PRK", "RCY", "REC", "SRO", "STP"
}

DOWNTIME_MODES = {
    "COR", "DBF", "DLF", "ESB", "HAD", "HBP", "NAV"
}

# Mode descriptions for explanations
MODE_DESCRIPTIONS = {
    "ANS": "Anti-Nuisance",
    "ATT": "Attendant Mode", 
    "CHC": "Cancel Hall Call",
    "COR": "Correction",
    "CTL": "Car to Landing",
    "DBF": "Drive Brake Fault",
    "DCP": "Delayed Car Protection",
    "DEF": "Default Initialization", 
    "DHB": "Door Hold Button",
    "DLF": "Door Lock Failure",
    "DTC": "Door Close Timeout",
    "DTO": "Door Open Timeout",
    "EFO": "Emergency Fire Operation",
    "EFS": "Emergency Fireman Service",
    "EHS": "Emergency Hospital Service", 
    "EPC": "Emergency Power Correction",
    "EPR": "Emergency Power Rescue",
    "EPW": "Emergency Power Waiting",
    "ESB": "Emergency Stop Button",
    "HAD": "Hoistway Access Detection",
    "HBP": "Hall Button Protection",
    "IDL": "Idle",
    "INI": "Initialization",
    "INS": "Inspection",
    "ISC": "Independent Service",
    "LNS": "Load Nonstop", 
    "NAV": "Not Available",
    "NOR": "Normal",
    "PKS": "Park & Shutdown",
    "PRK": "Parking Operation",
    "RCY": "Recycle Operation (Hydro)",
    "REC": "Recover Operation",
    "SRO": "Separate Riser Operation",
    "STP": "Car Stall Protection"
}

def get_mode_status(mode_name: str) -> str:
    """
    Get the status (UPTIME/DOWNTIME/UNKNOWN) for a mode
    
    Args:
        mode_name: Mode code (e.g., "NOR", "DLF")
        
    Returns:
        str: "UPTIME", "DOWNTIME", or "UNKNOWN"
    """
    if mode_name in UPTIME_MODES:
        return "UPTIME"
    elif mode_name in DOWNTIME_MODES:
        return "DOWNTIME"
    else:
        return "UNKNOWN"

def timestamp_to_localized_datetime(timestamp_ms: int, timezone_name: str) -> datetime:
    """
    Convert Unix timestamp to localized datetime
    
    Args:
        timestamp_ms: Unix timestamp in milliseconds
        timezone_name: IANA timezone name
        
    Returns:
        datetime: Localized datetime object
    """
    # Convert to UTC datetime
    utc_dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC)
    
    # Convert to local timezone
    local_tz = pytz.timezone(timezone_name)
    return utc_dt.astimezone(local_tz)

def compute_uptime_downtime(
    installation_id: str,
    timezone_name: str,
    start_iso: str,
    end_iso: str,
    events_json: str
) -> Dict[str, Any]:
    """
    Compute uptime/downtime for an installation
    
    Args:
        installation_id: Installation ID
        timezone_name: IANA timezone name
        start_iso: Start time in ISO format
        end_iso: End time in ISO format  
        events_json: JSON string containing events and prior modes
        
    Returns:
        Dict with uptime/downtime analysis results
    """
    try:
        data = json.loads(events_json)
        events = data.get("events", [])
        prior_modes = data.get("priorModes", [])
        
        # Parse time window
        tz = pytz.timezone(timezone_name)
        start_dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
        
        if start_dt.tzinfo is None:
            start_dt = tz.localize(start_dt)
        if end_dt.tzinfo is None:
            end_dt = tz.localize(end_dt)
            
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        # Group events by machine
        machine_events = {}
        for event in events:
            kafka_msg = event.get("kafkaMessage", {})
            car_mode = kafka_msg.get("CarModeChanged", {})
            machine_id = car_mode.get("MachineId")
            
            if machine_id is not None:
                if machine_id not in machine_events:
                    machine_events[machine_id] = []
                machine_events[machine_id].append({
                    "timestamp": kafka_msg.get("Timestamp"),
                    "mode": car_mode.get("ModeName"),
                    "alarm_severity": car_mode.get("AlarmSeverity", 0)
                })
        
        # Group prior modes by machine
        machine_prior_modes = {}
        for prior in prior_modes:
            machine_id = prior.get("MachineId")
            if machine_id is not None:
                machine_prior_modes[machine_id] = prior.get("ModeName")
        
        # Analyze each machine
        machine_results = []
        total_uptime_minutes = 0
        total_downtime_minutes = 0
        total_excluded_minutes = 0
        
        all_machines = set(machine_events.keys()) | set(machine_prior_modes.keys())
        
        for machine_id in all_machines:
            events_for_machine = machine_events.get(machine_id, [])
            prior_mode = machine_prior_modes.get(machine_id)
            
            # Sort events by timestamp
            events_for_machine.sort(key=lambda x: x["timestamp"])
            
            # Build intervals
            intervals = _build_intervals(
                events_for_machine, prior_mode, start_ms, end_ms
            )
            
            # Calculate durations
            uptime_mins, downtime_mins, excluded_mins = _calculate_durations(intervals)
            
            machine_results.append({
                "machineId": machine_id,
                "uptime_minutes": uptime_mins,
                "downtime_minutes": downtime_mins,
                "uptime_percent": _safe_percentage(uptime_mins, uptime_mins + downtime_mins),
                "downtime_percent": _safe_percentage(downtime_mins, uptime_mins + downtime_mins)
            })
            
            total_uptime_minutes += uptime_mins
            total_downtime_minutes += downtime_mins
            total_excluded_minutes += excluded_mins
        
        # Calculate overall percentages
        total_tracked_minutes = total_uptime_minutes + total_downtime_minutes
        
        return {
            "installationId": installation_id,
            "timezone": timezone_name,
            "window": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            },
            "machines": machine_results,
            "totals": {
                "uptime_minutes": total_uptime_minutes,
                "downtime_minutes": total_downtime_minutes,
                "uptime_percent": _safe_percentage(total_uptime_minutes, total_tracked_minutes),
                "downtime_percent": _safe_percentage(total_downtime_minutes, total_tracked_minutes)
            },
            "excluded_minutes": total_excluded_minutes
        }
        
    except Exception as e:
        return {
            "error": f"Failed to compute uptime/downtime: {str(e)}",
            "installationId": installation_id,
            "timezone": timezone_name
        }

def _build_intervals(events: List[Dict], prior_mode: Optional[str], start_ms: int, end_ms: int) -> List[Dict]:
    """Build time intervals from events"""
    intervals = []
    
    # Determine starting mode
    if events:
        current_mode = prior_mode
        current_time = start_ms
        
        # Add intervals between events
        for event in events:
            event_time = event["timestamp"]
            
            if current_mode and current_time < event_time:
                intervals.append({
                    "start": current_time,
                    "end": event_time,
                    "mode": current_mode,
                    "status": get_mode_status(current_mode)
                })
            
            current_mode = event["mode"]
            current_time = event_time
        
        # Add final interval
        if current_mode and current_time < end_ms:
            intervals.append({
                "start": current_time,
                "end": end_ms,
                "mode": current_mode,
                "status": get_mode_status(current_mode)
            })
    elif prior_mode:
        # No events in window, but we have prior mode
        intervals.append({
            "start": start_ms,
            "end": end_ms,
            "mode": prior_mode,
            "status": get_mode_status(prior_mode)
        })
    
    return intervals

def _calculate_durations(intervals: List[Dict]) -> Tuple[float, float, float]:
    """Calculate uptime, downtime, and excluded minutes from intervals"""
    uptime_ms = 0
    downtime_ms = 0
    excluded_ms = 0
    
    for interval in intervals:
        duration_ms = interval["end"] - interval["start"]
        status = interval["status"]
        
        if status == "UPTIME":
            uptime_ms += duration_ms
        elif status == "DOWNTIME":
            downtime_ms += duration_ms
        else:
            excluded_ms += duration_ms
    
    # Convert to minutes
    return (
        uptime_ms / (1000 * 60),
        downtime_ms / (1000 * 60),
        excluded_ms / (1000 * 60)
    )

def _safe_percentage(numerator: float, denominator: float) -> float:
    """Calculate percentage safely, avoiding division by zero"""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)

def explain_downtime(
    installation_id: str,
    machine_id: int,
    timezone_name: str,
    start_iso: str,
    end_iso: str,
    events_json: str
) -> Dict[str, Any]:
    """
    Explain downtime intervals for a specific machine
    
    Args:
        installation_id: Installation ID
        machine_id: Machine ID to analyze
        timezone_name: IANA timezone name
        start_iso: Start time in ISO format
        end_iso: End time in ISO format
        events_json: JSON string containing events and prior modes
        
    Returns:
        Dict with downtime explanation
    """
    try:
        data = json.loads(events_json)
        events = data.get("events", [])
        prior_modes = data.get("priorModes", [])
        
        # Parse time window
        tz = pytz.timezone(timezone_name)
        start_dt = datetime.fromisoformat(start_iso.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_iso.replace('Z', '+00:00'))
        
        if start_dt.tzinfo is None:
            start_dt = tz.localize(start_dt)
        if end_dt.tzinfo is None:
            end_dt = tz.localize(end_dt)
            
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        # Filter events for this machine
        machine_events = []
        for event in events:
            kafka_msg = event.get("kafkaMessage", {})
            car_mode = kafka_msg.get("CarModeChanged", {})
            
            if car_mode.get("MachineId") == machine_id:
                machine_events.append({
                    "timestamp": kafka_msg.get("Timestamp"),
                    "mode": car_mode.get("ModeName"),
                    "alarm_severity": car_mode.get("AlarmSeverity", 0)
                })
        
        # Get prior mode for this machine
        prior_mode = None
        for prior in prior_modes:
            if prior.get("MachineId") == machine_id:
                prior_mode = prior.get("ModeName")
                break
        
        # Sort events by timestamp
        machine_events.sort(key=lambda x: x["timestamp"])
        
        # Build intervals
        intervals = _build_intervals(machine_events, prior_mode, start_ms, end_ms)
        
        # Extract downtime intervals
        downtime_intervals = []
        total_downtime_minutes = 0
        
        for interval in intervals:
            if interval["status"] == "DOWNTIME":
                duration_minutes = (interval["end"] - interval["start"]) / (1000 * 60)
                
                start_local = timestamp_to_localized_datetime(interval["start"], timezone_name)
                end_local = timestamp_to_localized_datetime(interval["end"], timezone_name)
                
                mode_name = interval["mode"]
                reason = MODE_DESCRIPTIONS.get(mode_name, f"Unknown mode: {mode_name}")
                
                downtime_intervals.append({
                    "start": start_local.isoformat(),
                    "end": end_local.isoformat(),
                    "minutes": round(duration_minutes, 1),
                    "mode": mode_name,
                    "reason": reason
                })
                
                total_downtime_minutes += duration_minutes
        
        return {
            "installationId": installation_id,
            "machineId": machine_id,
            "timezone": timezone_name,
            "downtime_intervals": downtime_intervals,
            "total_downtime_minutes": round(total_downtime_minutes, 1)
        }
        
    except Exception as e:
        return {
            "error": f"Failed to explain downtime: {str(e)}",
            "installationId": installation_id,
            "machineId": machine_id
        }
