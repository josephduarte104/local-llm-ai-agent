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
            
            # If date range is invalid, return error
            if not date_validation['is_valid']:
                return {
                    'installation_id': installation_id,
                    'error': True,
                    'validation_warnings': date_validation['warnings'],
                    'recommendations': date_validation['recommendations'],
                    'latest_available_date': date_validation['latest_available_date'],
                    'current_time_local': date_validation['current_time_local']
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
            machine_metrics: List[Dict[str, Any]] = []
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
                    
                    machine_metrics.append({
                        'machine_id': mid,
                        'uptime_minutes': metrics.uptime_minutes,
                        'downtime_minutes': metrics.downtime_minutes,
                        'uptime_percentage': metrics.uptime_percentage,
                        'downtime_percentage': metrics.downtime_percentage,
                        'total_minutes': metrics.total_minutes,
                        'uptime_human': timezone_service.format_duration_human(metrics.uptime_minutes),
                        'downtime_human': timezone_service.format_duration_human(metrics.downtime_minutes),
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
                    machine_metrics.append({
                        'machine_id': mid,
                        'uptime_minutes': 0.0,
                        'downtime_minutes': 0.0,
                        'uptime_percentage': 0.0,
                        'downtime_percentage': 0.0,
                        'total_minutes': 0.0,
                        'uptime_human': timezone_service.format_duration_human(0.0),
                        'downtime_human': timezone_service.format_duration_human(0.0),
                        'has_data': False,
                        'data_coverage_percentage': 0.0,
                        'intervals': []
                    })
                    machines_without_data += 1

            # Sort machine metrics by machine_id for consistent ordering
            machine_metrics.sort(key=lambda x: int(x['machine_id']))

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
            
            # Enhanced interpretation with multi-elevator context
            interpretation = []
            
            # Elevator count context
            total_elevators = len(target_machine_ids)
            if total_elevators > 1:
                interpretation.append(f"Analysis for {total_elevators} elevators (Cars/Machine IDs: {', '.join(target_machine_ids)})")
                if machines_without_data > 0:
                    interpretation.append(f"⚠️ {machines_without_data} of {total_elevators} elevators have no data for this time period")
                    if machines_with_data > 0:
                        interpretation.append(f"📊 Analysis based on {machines_with_data} elevators with available data")
                    else:
                        interpretation.append("🚨 No elevators have data for this time period")
            else:
                interpretation.append(f"Analysis for 1 elevator (Car/Machine ID: {target_machine_ids[0]})")

            # Overall performance assessment (only if we have data)
            if machines_with_data > 0:
                if installation_uptime_pct >= 95:
                    interpretation.append("✅ Excellent uptime performance (≥95%)")
                elif installation_uptime_pct >= 90:
                    interpretation.append("⚠️ Good uptime performance (90-95%)")
                elif installation_uptime_pct >= 80:
                    interpretation.append("🟡 Fair uptime performance (80-90%)")
                else:
                    interpretation.append("🔴 Poor uptime performance (<80%)")
            
            # Enhanced data coverage analysis with granular warnings
            if machines_with_data > 0:
                # Add date validation warnings if any
                if 'warnings' in date_validation and date_validation['warnings']:
                    interpretation.extend(date_validation['warnings'])
                if 'recommendations' in date_validation and date_validation['recommendations']:
                    interpretation.extend(date_validation['recommendations'])
                
                # Data coverage analysis
                if data_coverage_percentage < 95:
                    interpretation.append(f"⚠️ PARTIAL DATA: Only {data_coverage_percentage:.1f}% of requested time period has data")
                    interpretation.append(f"📊 Analysis covers {timezone_service.format_duration_human(total_duration)} out of {timezone_service.format_duration_human(expected_total_minutes)} requested")
                    
                    # Add daily breakdown for incomplete data
                    total_range_days = (end_time.date() - start_time.date()).days + 1
                    if total_range_days > 1:
                        interpretation.append(f"\n📅 Daily Data Availability Breakdown ({total_range_days} days):")
                        
                        # Calculate daily breakdown for each elevator with incomplete data
                        for metric in machine_metrics:
                            if metric.get('has_data', False) and metric.get('data_coverage_percentage', 100) < 95:
                                mid = metric['machine_id']
                                intervals = metric.get('intervals', [])
                                
                                daily_breakdown = UptimeService.calculate_daily_availability(
                                    intervals, start_time, end_time, installation_tz
                                )
                                
                                interpretation.append(f"   🏢 Elevator {mid}:")
                                for day_data in daily_breakdown:
                                    date_str = day_data['date']
                                    expected_hrs = day_data['expected_hours']
                                    actual_hrs = day_data['actual_hours']
                                    availability_pct = day_data['availability_percentage']
                                    
                                    if day_data['has_data']:
                                        interpretation.append(f"      • {date_str}: {actual_hrs:.1f}h / {expected_hrs:.1f}h ({availability_pct:.1f}%)")
                                    else:
                                        interpretation.append(f"      • {date_str}: No data (0h / {expected_hrs:.1f}h)")
                                
                                interpretation.append("")  # Add space between elevators
                    
                    # Granular data coverage warnings
                    if data_coverage_percentage < 25:
                        interpretation.append("🚨 CRITICAL: Very limited data (<25%) - results may not be representative")
                        interpretation.append("💡 Recommendation: Choose a different time period with more data availability")
                    elif data_coverage_percentage < 50:
                        interpretation.append("⚠️ WARNING: Limited data (<50%) - interpret results with caution")
                        interpretation.append("🔍 Recommendation: Verify if this period had maintenance or system issues")
                    elif data_coverage_percentage < 75:
                        interpretation.append("ℹ️ NOTE: Moderate data coverage (<75%) - results are generally reliable")
                    
                    # Add per-elevator data coverage context
                    interpretation.append("📋 Each elevator's uptime percentage is calculated only for periods with available data")
                else:
                    interpretation.append(f"✅ Complete data coverage: {data_coverage_percentage:.1f}% of requested period")
            
            # Enhanced individual elevator performance breakdown
            if machine_metrics:
                interpretation.append("\n🏢 Detailed Elevator Performance Analysis:")
                
                # Sort elevators by uptime for better readability
                sorted_metrics = sorted(machine_metrics, key=lambda x: (x.get('has_data', False), x.get('uptime_percentage', 0)), reverse=True)
                
                for i, metric in enumerate(sorted_metrics, 1):
                    mid = metric['machine_id']
                    if metric['has_data']:
                        uptime_pct = metric['uptime_percentage']
                        uptime_human = metric['uptime_human']
                        downtime_human = metric['downtime_human']
                        total_human = metric.get('total_human', timezone_service.format_duration_human(metric['total_minutes']))
                        
                        # Enhanced status indicators
                        if uptime_pct >= 99:
                            emoji = "🟢"
                            status = "Excellent"
                        elif uptime_pct >= 95:
                            emoji = "🟢"
                            status = "Good"
                        elif uptime_pct >= 90:
                            emoji = "🟡"
                            status = "Fair"
                        elif uptime_pct >= 80:
                            emoji = "🟠"
                            status = "Poor"
                        else:
                            emoji = "🔴"
                            status = "Critical"
                        
                        interpretation.append(f"   {emoji} Elevator {mid} ({status}): {uptime_pct:.1f}% uptime")
                        interpretation.append(f"      ⏱️ Operational: {uptime_human} | Downtime: {downtime_human}")
                        interpretation.append(f"      📊 Total monitored time: {total_human}")
                        
                        # Add interval count for transparency
                        interval_count = len(metric.get('intervals', []))
                        if interval_count > 0:
                            interpretation.append(f"      🔄 Mode changes: {interval_count} events")
                        
                        # Add gap between elevators except for the last one
                        if i < len(sorted_metrics):
                            interpretation.append("")
                    else:
                        interpretation.append(f"   ⚫ Elevator {mid}: No data available for this time period")
                        interpretation.append(f"      📅 This elevator may not have been operational during {start_time.date()} to {end_time.date()}")
                        if i < len(sorted_metrics):
                            interpretation.append("")

            # Performance range analysis (only for elevators with data)
            elevators_with_data = [m for m in machine_metrics if m['has_data']]
            if len(elevators_with_data) > 1:
                lowest_machine = min(elevators_with_data, key=lambda m: m['uptime_percentage'])
                highest_machine = max(elevators_with_data, key=lambda m: m['uptime_percentage'])
                
                if highest_machine['uptime_percentage'] != lowest_machine['uptime_percentage']:
                    interpretation.append(f"📈 Performance range: {lowest_machine['uptime_percentage']:.1f}% - {highest_machine['uptime_percentage']:.1f}% across elevators with data")

            return {
                'installation_id': installation_id,
                'machine_metrics': machine_metrics,
                'installation_summary': {
                    'uptime_minutes': total_uptime,
                    'downtime_minutes': total_downtime,
                    'uptime_percentage': installation_uptime_pct,
                    'downtime_percentage': installation_downtime_pct,
                    'total_minutes': total_duration,
                    'uptime_human': timezone_service.format_duration_human(total_uptime),
                    'downtime_human': timezone_service.format_duration_human(total_downtime),
                    'expected_total_minutes': expected_total_minutes,
                    'data_coverage_percentage': data_coverage_percentage,
                    'total_elevators': total_elevators,
                    'elevators_with_data': machines_with_data,
                    'elevators_without_data': machines_without_data
                },
                'interpretation': interpretation,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'timezone': installation_tz
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating uptime metrics: {e}")
            raise


# Global instance
uptime_service = UptimeService()
