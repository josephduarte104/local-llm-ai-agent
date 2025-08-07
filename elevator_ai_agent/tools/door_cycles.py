"""Tool to analyze door cycles from event data."""

import logging
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

from ..services.cosmos import get_cosmos_service
from ..services.timezone import timezone_service
from .base import BaseTool

logger = logging.getLogger(__name__)

class DoorCyclesTool(BaseTool):
    """Tool to analyze door cycles from event data."""

    def __init__(self):
        super().__init__(
            name="door_cycle_analysis",
            description="Analyzes door open/close cycles for each elevator, deck, and side."
        )

    def run(
        self,
        installation_id: str,
        tz: str,
        start: datetime,
        end: datetime,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Runs the door cycle analysis.
        
        Args:
            installation_id: The installation to analyze.
            tz: IANA timezone string for the installation.
            start: Start datetime (timezone-aware).
            end: End datetime (timezone-aware).
            **kwargs: Additional tool-specific parameters.
            
        Returns:
            A dictionary with the analysis results.
        """
        start_epoch = timezone_service.local_datetime_to_epoch(start)
        end_epoch = timezone_service.local_datetime_to_epoch(end)

        cosmos_service = get_cosmos_service()

        try:
            events = list(cosmos_service.get_door_events(
                installation_id=installation_id,
                start_ts=start_epoch,
                end_ts=end_epoch
            ))
        except Exception as e:
            logger.error(f"Error querying door events from Cosmos DB: {e}", exc_info=True)
            return {
                "summary": "An error occurred while fetching door events.",
                "error": str(e),
                "cycle_counts_by_day": {}
            }

        if not events:
            return {
                "summary": "No door events found for the specified period.",
                "cycle_counts_by_day": {},
                "time_range": {
                    'start': start.isoformat(),
                    'end': end.isoformat(),
                    'timezone': tz
                },
            }

        # Sort events by timestamp to ensure correct sequence processing
        events.sort(key=lambda x: x.get("Timestamp", 0))

        cycle_analysis = self._calculate_cycles_and_timings(events, tz)
        cycle_counts = cycle_analysis["cycle_counts"]
        timing_stats = cycle_analysis["timing_stats"]
        reversal_counts = cycle_analysis["reversal_counts"]
        
        # Calculate total cycles for the summary
        total_cycles = 0
        for elevator_data in cycle_counts.values():
            for door_data in elevator_data.values():
                for day_counts in door_data.values():
                    if isinstance(day_counts, dict):
                        total_cycles += sum(day_counts.values())
                    else:
                        total_cycles += day_counts
        
        # Calculate total reversals for the summary
        total_reversals = 0
        for elevator_data in reversal_counts.values():
            for door_data in elevator_data.values():
                for day_counts in door_data.values():
                    if isinstance(day_counts, dict):
                        total_reversals += sum(day_counts.values())
                    else:
                        total_reversals += day_counts
        
        return {
            "summary": f"Analyzed {len(events)} door events and found {total_cycles} complete door cycles and {total_reversals} door reversals across {len(cycle_counts)} elevators.",
            "cycle_counts_by_day": cycle_counts,
            "reversal_counts_by_day": reversal_counts,
            "timing_statistics": timing_stats,
            "time_range": {
                'start': start.isoformat(),
                'end': end.isoformat(),
                'timezone': tz
            },
        }

    def _get_day_from_timestamp(self, timestamp_ms: int, tz: str) -> str:
        """Converts a timestamp to a date string in YYYY-MM-DD format."""
        dt_local = timezone_service.epoch_to_local_datetime(timestamp_ms, tz)
        return dt_local.strftime('%Y-%m-%d')

    def _calculate_cycles_and_timings(self, events: List[Dict[str, Any]], tz: str) -> Dict[str, Any]:
        """
        Calculates door cycles and timing statistics from a list of door events.
        A full cycle is defined by the sequence: OPENING -> OPENED -> CLOSING -> CLOSED.
        """
        grouped_events = defaultdict(list)
        for event in events:
            try:
                machine_id = event.get('MachineId')
                side = event.get('Side')
                deck = event.get('Deck')

                if machine_id is not None and side and deck:
                    key = (machine_id, side, deck)
                    grouped_events[key].append({
                        "State": event.get("State", "").upper(),
                        "Timestamp": event.get("Timestamp")
                    })
            except (AttributeError, KeyError) as e:
                logger.warning(f"Skipping malformed door event: {event}, error: {e}")

        # This will be a nested dictionary: {elevator: {door: {day: count}}}
        cycle_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        # Timing statistics collections
        timing_data = defaultdict(lambda: {
            "opened_durations": [],
            "closing_to_closed_durations": [],
            "closed_to_opening_durations": []
        })
        
        # Door reversal tracking
        reversal_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        cycle_sequence = ["OPENING", "OPENED", "CLOSING", "CLOSED"]

        for (machine_id, side, deck), event_list in grouped_events.items():
            current_sequence_index = 0
            cycle_timestamps = {}  # Track timestamps for current cycle
            last_closed_timestamp = None
            
            elevator_key = f"Elevator {machine_id}"
            door_key = f"{side.capitalize()} {deck.capitalize()} Door"
            timing_key = f"{elevator_key} - {door_key}"
            
            for event in event_list:
                state = event.get('State')
                timestamp = event.get('Timestamp')
                
                if timestamp is None:
                    continue
                
                if state == cycle_sequence[current_sequence_index]:
                    cycle_timestamps[state] = timestamp
                    current_sequence_index += 1
                elif state == "OPENING":
                    # Check for door reversal: CLOSING -> OPENING
                    if current_sequence_index == 3 and "CLOSING" in cycle_timestamps:  # Was in CLOSING state
                        # Door reversal detected
                        day_str = self._get_day_from_timestamp(timestamp, tz)
                        reversal_counts[elevator_key][door_key][day_str] += 1
                        logger.debug(f"Door reversal detected for {timing_key} at {timestamp}")
                    
                    # Reset cycle and start new one
                    cycle_timestamps = {"OPENING": timestamp}
                    current_sequence_index = 1
                    
                    # Calculate time from last CLOSED to this OPENING
                    if last_closed_timestamp is not None:
                        closed_to_opening_duration = (timestamp - last_closed_timestamp) / 1000.0  # Convert to seconds
                        timing_data[timing_key]["closed_to_opening_durations"].append(closed_to_opening_duration)
                else:
                    current_sequence_index = 0
                    cycle_timestamps = {}

                # Complete cycle found
                if current_sequence_index == len(cycle_sequence):
                    day_str = self._get_day_from_timestamp(timestamp, tz)
                    cycle_counts[elevator_key][door_key][day_str] += 1
                    
                    # Calculate timing statistics for this complete cycle
                    if all(state in cycle_timestamps for state in cycle_sequence):
                        # Time door was in OPENED state (OPENED to CLOSING)
                        opened_duration = (cycle_timestamps["CLOSING"] - cycle_timestamps["OPENED"]) / 1000.0
                        timing_data[timing_key]["opened_durations"].append(opened_duration)
                        
                        # Time from CLOSING to CLOSED
                        closing_to_closed_duration = (cycle_timestamps["CLOSED"] - cycle_timestamps["CLOSING"]) / 1000.0
                        timing_data[timing_key]["closing_to_closed_durations"].append(closing_to_closed_duration)
                    
                    last_closed_timestamp = cycle_timestamps.get("CLOSED")
                    current_sequence_index = 0
                    cycle_timestamps = {}

        # Calculate average timing statistics
        timing_stats = {}
        for door_key, timings in timing_data.items():
            stats = {}
            
            if timings["opened_durations"]:
                stats["avg_opened_duration_seconds"] = sum(timings["opened_durations"]) / len(timings["opened_durations"])
                stats["min_opened_duration_seconds"] = min(timings["opened_durations"])
                stats["max_opened_duration_seconds"] = max(timings["opened_durations"])
            else:
                stats["avg_opened_duration_seconds"] = 0
                stats["min_opened_duration_seconds"] = 0
                stats["max_opened_duration_seconds"] = 0
            
            if timings["closing_to_closed_durations"]:
                stats["avg_closing_to_closed_duration_seconds"] = sum(timings["closing_to_closed_durations"]) / len(timings["closing_to_closed_durations"])
                stats["min_closing_to_closed_duration_seconds"] = min(timings["closing_to_closed_durations"])
                stats["max_closing_to_closed_duration_seconds"] = max(timings["closing_to_closed_durations"])
            else:
                stats["avg_closing_to_closed_duration_seconds"] = 0
                stats["min_closing_to_closed_duration_seconds"] = 0
                stats["max_closing_to_closed_duration_seconds"] = 0
            
            if timings["closed_to_opening_durations"]:
                stats["avg_closed_to_opening_duration_seconds"] = sum(timings["closed_to_opening_durations"]) / len(timings["closed_to_opening_durations"])
                stats["min_closed_to_opening_duration_seconds"] = min(timings["closed_to_opening_durations"])
                stats["max_closed_to_opening_duration_seconds"] = max(timings["closed_to_opening_durations"])
            else:
                stats["avg_closed_to_opening_duration_seconds"] = 0
                stats["min_closed_to_opening_duration_seconds"] = 0
                stats["max_closed_to_opening_duration_seconds"] = 0
                
            stats["sample_counts"] = {
                "opened_samples": len(timings["opened_durations"]),
                "closing_to_closed_samples": len(timings["closing_to_closed_durations"]),
                "closed_to_opening_samples": len(timings["closed_to_opening_durations"])
            }
            
            timing_stats[door_key] = stats
        
        # Convert defaultdicts to regular dicts for clean JSON output
        cycle_counts_clean = {
            elevator: {
                door: dict(day_data)
                for door, day_data in door_data.items()
            }
            for elevator, door_data in cycle_counts.items()
        }
        
        reversal_counts_clean = {
            elevator: {
                door: dict(day_data)
                for door, day_data in door_data.items()
            }
            for elevator, door_data in reversal_counts.items()
        }
        
        return {
            "cycle_counts": cycle_counts_clean,
            "timing_stats": timing_stats,
            "reversal_counts": reversal_counts_clean
        }



# Create a single, global instance of the tool
door_cycles_tool = DoorCyclesTool()

