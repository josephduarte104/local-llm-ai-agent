"""Uptime/Downtime calculation service for elevator operations."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

from .cosmos import get_cosmos_service
from .timezone import timezone_service

logger = logging.getLogger(__name__)


# Mode name mappings
UPTIME_MODES = {
    'ANS', 'ATT', 'CHC', 'CTL', 'DCP', 'DEF', 'DHB', 'DTC', 'DTO',
    'EFO', 'EFS', 'EHS', 'EPC', 'EPR', 'EPW', 'IDL', 'INI', 'INS',
    'ISC', 'LNS', 'NOR', 'PKS', 'PRK', 'RCY', 'REC', 'SRO', 'STP'
}

DOWNTIME_MODES = {
    'COR', 'DBF', 'DLF', 'ESB', 'HAD', 'HBP', 'NAV'
}


@dataclass
class ModeInterval:
    """Represents a time interval with a specific mode."""
    start_time: datetime
    end_time: datetime
    mode_name: str
    machine_id: str
    status: str  # 'uptime', 'downtime', 'unknown'
    
    @property
    def duration_minutes(self) -> float:
        """Calculate duration in minutes."""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 60


@dataclass
class UptimeMetrics:
    """Uptime metrics for a machine or installation."""
    machine_id: Optional[str]
    installation_id: str
    uptime_minutes: float
    downtime_minutes: float
    unknown_minutes: float
    total_minutes: float
    uptime_percentage: float
    downtime_percentage: float
    intervals: List[ModeInterval]


class UptimeService:
    """Service for calculating uptime and downtime metrics."""
    
    @staticmethod
    def get_mode_status(mode_name: str) -> str:
        """
        Determine if a mode represents uptime or downtime.
        
        Args:
            mode_name: The mode name to classify
            
        Returns:
            'uptime', 'downtime', or 'unknown'
        """
        if mode_name in UPTIME_MODES:
            return 'uptime'
        elif mode_name in DOWNTIME_MODES:
            return 'downtime'
        else:
            return 'unknown'
    
    @staticmethod
    def build_intervals(
        events: List[Dict[str, Any]], 
        start_time: datetime, 
        end_time: datetime,
        machine_id: str,
        tz_name: str
    ) -> List[ModeInterval]:
        """
        Build time intervals from CarModeChanged events.
        
        Args:
            events: List of CarModeChanged events for a single machine
            start_time: Query start time (timezone-aware)
            end_time: Query end time (timezone-aware)
            machine_id: Machine ID
            
        Returns:
            List of mode intervals
        """
        intervals: List[ModeInterval] = []
        
        if not events:
            return intervals
        
        # Sort events by timestamp
        # Handle both flat structure (from SELECT projection) and full document structure
        sorted_events = sorted(events, key=lambda x: x.get('Timestamp') or x['kafkaMessage']['Timestamp'])
        
        for i, event in enumerate(sorted_events):
            # Handle both flat structure and full document structure
            if 'Timestamp' in event:
                # Flat structure from SELECT projection
                timestamp = event['Timestamp']
                mode_name = event['ModeName']
            else:
                # Full document structure
                timestamp = event['kafkaMessage']['Timestamp']
                mode_data = event['kafkaMessage']['CarModeChanged']
                mode_name = mode_data['ModeName']
            
            # Convert timestamp to datetime in installation timezone
            event_time = timezone_service.epoch_to_local_datetime(
                timestamp, tz_name
            )
            
            # Determine interval start and end
            interval_start = max(event_time, start_time)
            
            if i + 1 < len(sorted_events):
                # Next event exists, use its timestamp as end
                if 'Timestamp' in sorted_events[i + 1]:
                    # Flat structure
                    next_timestamp = sorted_events[i + 1]['Timestamp']
                else:
                    # Full document structure
                    next_timestamp = sorted_events[i + 1]['kafkaMessage']['Timestamp']
                next_event_time = timezone_service.epoch_to_local_datetime(
                    next_timestamp, tz_name
                )
                interval_end = min(next_event_time, end_time)
            else:
                # Last event, extend to query end time
                interval_end = end_time
            
            # Only create interval if it's within our time range
            if interval_start < interval_end:
                status = UptimeService.get_mode_status(mode_name)
                interval = ModeInterval(
                    start_time=interval_start,
                    end_time=interval_end,
                    mode_name=mode_name,
                    machine_id=machine_id,
                    status=status
                )
                intervals.append(interval)
        
        return intervals
    
    @staticmethod
    def calculate_metrics(intervals: List[ModeInterval], machine_id: str, installation_id: str) -> UptimeMetrics:
        """
        Calculate uptime metrics from intervals.
        
        Args:
            intervals: List of mode intervals
            machine_id: Machine ID
            installation_id: Installation ID
            
        Returns:
            UptimeMetrics object
        """
        uptime_minutes = 0.0
        downtime_minutes = 0.0
        unknown_minutes = 0.0
        
        for interval in intervals:
            duration = interval.duration_minutes
            if interval.status == 'uptime':
                uptime_minutes += duration
            elif interval.status == 'downtime':
                downtime_minutes += duration
            else:
                unknown_minutes += duration
        
        total_minutes = uptime_minutes + downtime_minutes + unknown_minutes
        
        # Calculate percentages (avoid division by zero)
        if total_minutes > 0:
            uptime_percentage = (uptime_minutes / total_minutes) * 100
            downtime_percentage = (downtime_minutes / total_minutes) * 100
        else:
            uptime_percentage = 0.0
            downtime_percentage = 0.0
        
        return UptimeMetrics(
            machine_id=machine_id,
            installation_id=installation_id,
            uptime_minutes=uptime_minutes,
            downtime_minutes=downtime_minutes,
            unknown_minutes=unknown_minutes,
            total_minutes=total_minutes,
            uptime_percentage=uptime_percentage,
            downtime_percentage=downtime_percentage,
            intervals=intervals
        )
    
    @staticmethod
    def calculate_daily_availability(
        intervals: List[Any], 
        start_time: datetime, 
        end_time: datetime,
        installation_tz: str
    ) -> List[Dict[str, Any]]:
        """
        Calculate availability by day for the given intervals.
        
        Args:
            intervals: List of mode intervals (can be ModeInterval objects or dictionaries)
            start_time: Start time (timezone-aware)
            end_time: End time (timezone-aware)  
            installation_tz: Installation timezone
            
        Returns:
            List of daily availability dictionaries
        """
        from datetime import timedelta
        
        daily_data = []
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            # Define day boundaries
            day_start = current_date
            day_end = current_date
            
            # Convert to datetime in installation timezone
            day_start_dt = timezone_service.parse_iso_with_timezone(
                f"{day_start}T00:00:00", installation_tz
            )
            day_end_dt = timezone_service.parse_iso_with_timezone(
                f"{day_end}T23:59:59", installation_tz
            )
            
            # Skip if datetime parsing failed
            if not day_start_dt or not day_end_dt:
                current_date += timedelta(days=1)
                continue
            
            # Ensure we don't go beyond the requested range
            day_start_dt = max(day_start_dt, start_time)
            day_end_dt = min(day_end_dt, end_time)
            
            # Calculate expected hours for this day
            expected_minutes = (day_end_dt - day_start_dt).total_seconds() / 60.0
            expected_hours = expected_minutes / 60.0
            
            # Calculate actual data hours for this day
            actual_minutes = 0.0
            has_data = False
            
            for interval in intervals:
                # Handle both ModeInterval objects and dictionaries
                if isinstance(interval, dict):
                    interval_start = timezone_service.parse_iso_with_timezone(interval['start'], installation_tz)
                    interval_end = timezone_service.parse_iso_with_timezone(interval['end'], installation_tz)
                    interval_duration = interval['duration_minutes']
                else:
                    # ModeInterval object
                    interval_start = interval.start_time
                    interval_end = interval.end_time
                    interval_duration = interval.duration_minutes
                
                if not interval_start or not interval_end:
                    continue
                
                # Check if interval overlaps with this day
                overlap_start = max(interval_start, day_start_dt)
                overlap_end = min(interval_end, day_end_dt)
                
                if overlap_start < overlap_end:
                    # There's an overlap
                    overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60.0
                    actual_minutes += overlap_minutes
                    has_data = True
            
            actual_hours = actual_minutes / 60.0
            availability_percentage = (actual_hours / expected_hours * 100) if expected_hours > 0 else 0.0
            
            daily_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'expected_hours': expected_hours,
                'actual_hours': actual_hours,
                'availability_percentage': availability_percentage,
                'has_data': has_data
            })
            
            current_date += timedelta(days=1)
        
        return daily_data
    
    @staticmethod
    def get_uptime_metrics(
        installation_id: str,
        start_time: datetime,
        end_time: datetime,
        installation_tz: str,
        machine_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get uptime metrics for installation or specific machine.
        
        Args:
            installation_id: Installation to analyze
            start_time: Start time (timezone-aware)
            end_time: End time (timezone-aware)
            machine_id: Optional machine ID filter
            
        Returns:
            Dictionary with uptime metrics and breakdowns
        """
        try:
            # Validate date range and handle future dates
            date_validation = timezone_service.validate_date_range(start_time, end_time, installation_tz)
            
            # Adjust end time if it's in the future
            if 'adjusted_end_time' in date_validation:
                end_time = date_validation['adjusted_end_time']
                logger.info(f"Adjusted end time to current: {end_time}")
            
            # If date range is invalid, return error with validation details
            if not date_validation.get('is_valid', True):
                return {
                    'error': 'Invalid date range',
                    'date_validation': date_validation
                }
            
            # Convert to epoch milliseconds for Cosmos query
            start_epoch = timezone_service.local_datetime_to_epoch(start_time)
            end_epoch = timezone_service.local_datetime_to_epoch(end_time)

            # Get Cosmos service
            cosmos_service = get_cosmos_service()
            
            # First, get ALL machine IDs that exist for this installation (across all time)
            all_machine_ids = cosmos_service.get_all_machine_ids(installation_id)
            
            # If specific machine ID requested, filter to just that one
            if machine_id:
                target_machine_ids = [machine_id] if machine_id in all_machine_ids else []
            else:
                target_machine_ids = all_machine_ids
            
            # Get CarModeChanged events for the time period
            events = list(cosmos_service.get_car_mode_changes(
                installation_id=installation_id,
                start_ts=start_epoch,
                end_ts=end_epoch,
                machine_id=machine_id  # This may be None for all machines
            ))

            # Group events by machine ID
            events_by_machine: defaultdict[str, List[Dict[str, Any]]] = defaultdict(list)
            for event in events:
                # Handle both flat structure and full document structure
                if 'MachineId' in event:
                    # Flat structure from SELECT projection
                    mid: str = str(event['MachineId'])
                else:
                    # Full document structure
                    mid: str = str(event['kafkaMessage']['CarModeChanged']['MachineId'])
                events_by_machine[mid].append(event)
            
            # Calculate metrics for each target machine (including those with no data)
            machine_metrics_list: List[Dict[str, Any]] = []
            total_uptime = 0.0
            total_downtime = 0.0
            total_duration = 0.0
            machines_with_data = 0
            machines_without_data = 0
            
            for mid in target_machine_ids:
                machine_events = events_by_machine.get(mid, [])
                
                if machine_events:
                    # Machine has data - calculate normal metrics
                    intervals = UptimeService.build_intervals(
                        machine_events, start_time, end_time, mid, installation_tz
                    )
                    metrics = UptimeService.calculate_metrics(intervals, mid, installation_id)
                    
                    # Calculate expected time for this machine for data coverage percentage
                    expected_minutes = (end_time - start_time).total_seconds() / 60.0
                    data_coverage_percentage = (metrics.total_minutes / expected_minutes * 100) if expected_minutes > 0 else 0.0
                    
                    machine_metrics_list.append({
                        'machine_id': mid,
                        'uptime_minutes': metrics.uptime_minutes,
                        'downtime_minutes': metrics.downtime_minutes,
                        'uptime_percentage': metrics.uptime_percentage,
                        'downtime_percentage': metrics.downtime_percentage,
                        'total_minutes': metrics.total_minutes,
                        'has_data': True,
                        'data_coverage_percentage': data_coverage_percentage,
                        'intervals': [
                            {
                                'start': interval.start_time.isoformat(),
                                'end': interval.end_time.isoformat(),
                                'mode': interval.mode_name,
                                'status': interval.status,
                                'duration_minutes': interval.duration_minutes
                            }
                            for interval in metrics.intervals
                        ]
                    })
                    
                    total_uptime += metrics.uptime_minutes
                    total_downtime += metrics.downtime_minutes
                    total_duration += metrics.total_minutes
                    machines_with_data += 1
                else:
                    # Machine has no data for this period
                    machine_metrics_list.append({
                        'machine_id': mid,
                        'uptime_minutes': 0.0,
                        'downtime_minutes': 0.0,
                        'uptime_percentage': 0.0,
                        'downtime_percentage': 0.0,
                        'total_minutes': 0.0,
                        'has_data': False,
                        'data_coverage_percentage': 0.0,
                        'intervals': []
                    })
                    machines_without_data += 1

            # Sort machine metrics by machine_id for consistent ordering
            machine_metrics_list.sort(key=lambda x: int(x['machine_id']))

            # Calculate installation summary (only from machines with data)
            if total_duration > 0:
                installation_uptime_pct = (total_uptime / total_duration) * 100
                installation_downtime_pct = (total_downtime / total_duration) * 100
            else:
                installation_uptime_pct = 0.0
                installation_downtime_pct = 0.0
            
            # Calculate expected vs actual coverage
            expected_total_minutes = (end_time - start_time).total_seconds() / 60.0
            data_coverage_percentage = (total_duration / expected_total_minutes) * 100 if expected_total_minutes > 0 else 0.0
            
            # Add daily breakdown to each machine's metrics
            for metric in machine_metrics_list:
                if metric['has_data']:
                    metric['daily_availability'] = UptimeService.calculate_daily_availability(
                        metric['intervals'], start_time, end_time, installation_tz
                    )
                else:
                    metric['daily_availability'] = []

            return {
                'installation_id': installation_id,
                'machine_metrics': machine_metrics_list,
                'installation_summary': {
                    'uptime_minutes': total_uptime,
                    'downtime_minutes': total_downtime,
                    'uptime_percentage': installation_uptime_pct,
                    'downtime_percentage': installation_downtime_pct,
                    'total_minutes': total_duration,
                    'expected_total_minutes': expected_total_minutes,
                    'data_coverage_percentage': data_coverage_percentage,
                    'total_elevators': len(target_machine_ids),
                    'elevators_with_data': machines_with_data,
                    'elevators_without_data': machines_without_data
                },
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'timezone': installation_tz
                },
                'date_validation': date_validation
            }
            
        except Exception as e:
            logger.error(f"Error calculating uptime metrics: {e}")
            raise


# Global instance
uptime_service = UptimeService()
