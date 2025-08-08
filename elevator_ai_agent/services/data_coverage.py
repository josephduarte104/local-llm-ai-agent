"""Data coverage service for analyzing data availability and completeness."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

from .cosmos import get_cosmos_service
from .timezone import timezone_service

logger = logging.getLogger(__name__)


@dataclass
class DataCoverageReport:
    """Comprehensive data coverage report for a time period."""
    installation_id: str
    start_time: datetime
    end_time: datetime
    timezone: str
    
    # Overall coverage
    total_expected_minutes: float
    total_available_minutes: float
    overall_coverage_percentage: float
    
    # Machine-level coverage
    machines_total: int
    machines_with_data: int
    machines_without_data: int
    
    # Data types available
    data_types_available: List[str]
    
    # Coverage by machine
    machine_coverage: List[Dict[str, Any]]
    
    # Daily breakdown
    daily_coverage: List[Dict[str, Any]]
    
    # Data gaps and issues
    data_gaps: List[Dict[str, Any]]
    coverage_warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'installation_id': self.installation_id,
            'time_range': {
                'start': self.start_time.isoformat(),
                'end': self.end_time.isoformat(),
                'timezone': self.timezone
            },
            'overall_coverage': {
                'total_expected_minutes': self.total_expected_minutes,
                'total_available_minutes': self.total_available_minutes,
                'coverage_percentage': round(self.overall_coverage_percentage, 1)
            },
            'machines': {
                'total': self.machines_total,
                'with_data': self.machines_with_data,
                'without_data': self.machines_without_data,
                'coverage_by_machine': self.machine_coverage
            },
            'data_types_available': self.data_types_available,
            'daily_coverage': self.daily_coverage,
            'data_gaps': self.data_gaps,
            'coverage_warnings': self.coverage_warnings
        }


class DataCoverageService:
    """Service for analyzing data coverage and availability."""
    
    @staticmethod
    def analyze_coverage(
        installation_id: str,
        start_time: datetime,
        end_time: datetime,
        installation_tz: str,
        machine_id: Optional[str] = None
    ) -> DataCoverageReport:
        """
        Analyze data coverage for the specified time period.
        
        Args:
            installation_id: Installation to analyze
            start_time: Start time (timezone-aware)
            end_time: End time (timezone-aware)
            installation_tz: Installation timezone
            machine_id: Optional specific machine filter
            
        Returns:
            Comprehensive data coverage report
        """
        try:
            cosmos_service = get_cosmos_service()
            
            # Get all machine IDs for this installation
            all_machine_ids = cosmos_service.get_all_machine_ids(installation_id)
            target_machine_ids = [machine_id] if machine_id and machine_id in all_machine_ids else all_machine_ids
            
            # Calculate expected time
            total_expected_minutes = (end_time - start_time).total_seconds() / 60.0
            
            # Use parallel processing for coverage analysis to reduce latency
            from concurrent.futures import ThreadPoolExecutor
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Run CarMode and Door coverage analysis in parallel
                car_mode_future = executor.submit(
                    DataCoverageService._analyze_car_mode_coverage,
                    installation_id, start_time, end_time, installation_tz, target_machine_ids
                )
                door_future = executor.submit(
                    DataCoverageService._analyze_door_coverage,
                    installation_id, start_time, end_time, installation_tz, target_machine_ids
                )
                
                # Get results
                car_mode_coverage = car_mode_future.result()
                door_coverage = door_future.result()
            
            # Determine available data types
            data_types_available = []
            if car_mode_coverage['has_data']:
                data_types_available.append('CarModeChanged')
            if door_coverage['has_data']:
                data_types_available.append('Door')
            
            # Calculate daily coverage breakdown
            daily_coverage = DataCoverageService._calculate_daily_coverage(
                car_mode_coverage, start_time, end_time, installation_tz
            )
            
            # Identify data gaps and issues
            data_gaps = DataCoverageService._identify_data_gaps(
                car_mode_coverage, target_machine_ids, start_time, end_time
            )
            
            # Generate coverage warnings
            coverage_warnings = DataCoverageService._generate_coverage_warnings(
                car_mode_coverage, door_coverage, total_expected_minutes
            )
            
            # Calculate overall metrics
            overall_coverage_percentage = car_mode_coverage['overall_coverage_percentage']
            machines_with_data = car_mode_coverage['machines_with_data']
            machines_without_data = len(target_machine_ids) - machines_with_data
            
            return DataCoverageReport(
                installation_id=installation_id,
                start_time=start_time,
                end_time=end_time,
                timezone=installation_tz,
                total_expected_minutes=total_expected_minutes,
                total_available_minutes=car_mode_coverage['total_available_minutes'],
                overall_coverage_percentage=overall_coverage_percentage,
                machines_total=len(target_machine_ids),
                machines_with_data=machines_with_data,
                machines_without_data=machines_without_data,
                data_types_available=data_types_available,
                machine_coverage=car_mode_coverage['machine_coverage'],
                daily_coverage=daily_coverage,
                data_gaps=data_gaps,
                coverage_warnings=coverage_warnings
            )
            
        except Exception as e:
            logger.error(f"Error analyzing data coverage: {e}")
            # Return minimal coverage report on error
            return DataCoverageReport(
                installation_id=installation_id,
                start_time=start_time,
                end_time=end_time,
                timezone=installation_tz,
                total_expected_minutes=(end_time - start_time).total_seconds() / 60.0,
                total_available_minutes=0.0,
                overall_coverage_percentage=0.0,
                machines_total=0,
                machines_with_data=0,
                machines_without_data=0,
                data_types_available=[],
                machine_coverage=[],
                daily_coverage=[],
                data_gaps=[],
                coverage_warnings=[f"Error analyzing data coverage: {str(e)}"]
            )
    
    @staticmethod
    def _analyze_car_mode_coverage(
        installation_id: str,
        start_time: datetime,
        end_time: datetime,
        installation_tz: str,
        target_machine_ids: List[str]
    ) -> Dict[str, Any]:
        """Analyze CarModeChanged data coverage."""
        try:
            cosmos_service = get_cosmos_service()
            start_epoch = timezone_service.local_datetime_to_epoch(start_time)
            end_epoch = timezone_service.local_datetime_to_epoch(end_time)
            
            # Get CarModeChanged events
            events = list(cosmos_service.get_car_mode_changes(
                installation_id=installation_id,
                start_ts=start_epoch,
                end_ts=end_epoch
            ))
            
            # Group events by machine
            events_by_machine = defaultdict(list)
            for event in events:
                if 'MachineId' in event:
                    machine_id = str(event['MachineId'])
                else:
                    machine_id = str(event.get('kafkaMessage', {}).get('CarModeChanged', {}).get('MachineId', ''))
                
                if machine_id:
                    events_by_machine[machine_id].append(event)
            
            # Calculate coverage for each machine
            machine_coverage = []
            total_available_minutes = 0.0
            machines_with_data = 0
            expected_minutes_per_machine = (end_time - start_time).total_seconds() / 60.0
            
            for machine_id in target_machine_ids:
                machine_events = events_by_machine.get(machine_id, [])
                
                if machine_events:
                    # Estimate coverage based on event distribution
                    coverage_minutes = DataCoverageService._estimate_coverage_from_events(
                        machine_events, start_time, end_time, installation_tz
                    )
                    coverage_percentage = (coverage_minutes / expected_minutes_per_machine * 100) if expected_minutes_per_machine > 0 else 0.0
                    
                    machine_coverage.append({
                        'machine_id': machine_id,
                        'has_data': True,
                        'event_count': len(machine_events),
                        'coverage_minutes': coverage_minutes,
                        'coverage_percentage': round(coverage_percentage, 1),
                        'first_event': min(event.get('Timestamp', 0) for event in machine_events),
                        'last_event': max(event.get('Timestamp', 0) for event in machine_events)
                    })
                    
                    total_available_minutes += coverage_minutes
                    machines_with_data += 1
                else:
                    machine_coverage.append({
                        'machine_id': machine_id,
                        'has_data': False,
                        'event_count': 0,
                        'coverage_minutes': 0.0,
                        'coverage_percentage': 0.0,
                        'first_event': None,
                        'last_event': None
                    })
            
            total_expected_minutes = expected_minutes_per_machine * len(target_machine_ids)
            overall_coverage_percentage = (total_available_minutes / total_expected_minutes * 100) if total_expected_minutes > 0 else 0.0
            
            return {
                'has_data': len(events) > 0,
                'total_events': len(events),
                'machines_with_data': machines_with_data,
                'total_available_minutes': total_available_minutes,
                'overall_coverage_percentage': overall_coverage_percentage,
                'machine_coverage': machine_coverage
            }
            
        except Exception as e:
            logger.error(f"Error analyzing CarModeChanged coverage: {e}")
            return {
                'has_data': False,
                'total_events': 0,
                'machines_with_data': 0,
                'total_available_minutes': 0.0,
                'overall_coverage_percentage': 0.0,
                'machine_coverage': []
            }
    
    @staticmethod
    def _analyze_door_coverage(
        installation_id: str,
        start_time: datetime,
        end_time: datetime,
        installation_tz: str,
        target_machine_ids: List[str]
    ) -> Dict[str, Any]:
        """Analyze Door event data coverage."""
        try:
            cosmos_service = get_cosmos_service()
            start_epoch = timezone_service.local_datetime_to_epoch(start_time)
            end_epoch = timezone_service.local_datetime_to_epoch(end_time)
            
            # Get Door events
            door_events = list(cosmos_service.get_door_events(
                installation_id=installation_id,
                start_ts=start_epoch,
                end_ts=end_epoch
            ))
            
            return {
                'has_data': len(door_events) > 0,
                'total_events': len(door_events)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Door coverage: {e}")
            return {
                'has_data': False,
                'total_events': 0
            }
    
    @staticmethod
    def _estimate_coverage_from_events(
        events: List[Dict[str, Any]],
        start_time: datetime,
        end_time: datetime,
        installation_tz: str
    ) -> float:
        """
        Estimate data coverage minutes from event distribution.
        This is a heuristic based on event frequency and distribution.
        """
        if not events:
            return 0.0
        
        # Get timestamps
        timestamps = []
        for event in events:
            ts = event.get('Timestamp', 0)
            if ts:
                timestamps.append(ts)
        
        if not timestamps:
            return 0.0
        
        timestamps.sort()
        
        # Convert to datetime objects
        start_epoch = timezone_service.local_datetime_to_epoch(start_time)
        end_epoch = timezone_service.local_datetime_to_epoch(end_time)
        
        # Estimate coverage based on event span and density
        first_event_ts = max(timestamps[0], start_epoch)
        last_event_ts = min(timestamps[-1], end_epoch)
        
        # If we have events spanning the period, assume good coverage
        coverage_span_minutes = (last_event_ts - first_event_ts) / (1000 * 60)
        
        # Apply coverage factor based on event density
        total_period_minutes = (end_epoch - start_epoch) / (1000 * 60)
        
        # Heuristic: if events span >80% of period, assume near-full coverage
        span_ratio = coverage_span_minutes / total_period_minutes if total_period_minutes > 0 else 0
        
        if span_ratio > 0.8:
            return total_period_minutes * 0.95  # Assume 95% coverage
        elif span_ratio > 0.5:
            return total_period_minutes * 0.8   # Assume 80% coverage
        elif span_ratio > 0.2:
            return total_period_minutes * 0.6   # Assume 60% coverage
        else:
            return total_period_minutes * 0.3   # Assume 30% coverage
    
    @staticmethod
    def _calculate_daily_coverage(
        car_mode_coverage: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        installation_tz: str
    ) -> List[Dict[str, Any]]:
        """Calculate daily coverage breakdown."""
        daily_coverage = []
        
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            # Count machines with data for this day
            machines_with_data_today = 0
            total_machines = len(car_mode_coverage.get('machine_coverage', []))
            
            for machine in car_mode_coverage.get('machine_coverage', []):
                if machine.get('has_data', False):
                    # Simple heuristic: if machine has data in the overall period,
                    # assume it has data for most days
                    machines_with_data_today += 1
            
            coverage_percentage = (machines_with_data_today / total_machines * 100) if total_machines > 0 else 0.0
            
            daily_coverage.append({
                'date': current_date.isoformat(),
                'machines_with_data': machines_with_data_today,
                'total_machines': total_machines,
                'coverage_percentage': round(coverage_percentage, 1)
            })
            
            current_date += timedelta(days=1)
        
        return daily_coverage
    
    @staticmethod
    def _identify_data_gaps(
        car_mode_coverage: Dict[str, Any],
        target_machine_ids: List[str],
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Identify significant data gaps."""
        data_gaps = []
        
        # Check for machines with no data
        for machine in car_mode_coverage.get('machine_coverage', []):
            if not machine.get('has_data', False):
                data_gaps.append({
                    'type': 'machine_no_data',
                    'machine_id': machine.get('machine_id'),
                    'description': f"No CarModeChanged events found for elevator {machine.get('machine_id')}",
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'impact': 'high'
                })
        
        # Check for low coverage machines
        for machine in car_mode_coverage.get('machine_coverage', []):
            coverage_pct = machine.get('coverage_percentage', 0.0)
            if machine.get('has_data', False) and coverage_pct < 50.0:
                data_gaps.append({
                    'type': 'low_coverage',
                    'machine_id': machine.get('machine_id'),
                    'description': f"Low data coverage ({coverage_pct:.1f}%) for elevator {machine.get('machine_id')}",
                    'coverage_percentage': coverage_pct,
                    'impact': 'medium'
                })
        
        return data_gaps
    
    @staticmethod
    def _generate_coverage_warnings(
        car_mode_coverage: Dict[str, Any],
        door_coverage: Dict[str, Any],
        total_expected_minutes: float
    ) -> List[str]:
        """Generate warnings about data coverage issues."""
        warnings = []
        
        # Overall coverage warning
        overall_coverage = car_mode_coverage.get('overall_coverage_percentage', 0.0)
        if overall_coverage < 70.0:
            warnings.append(f"⚠️ Low overall data coverage ({overall_coverage:.1f}%) - results may be incomplete")
        
        # Machine coverage warnings
        machines_with_data = car_mode_coverage.get('machines_with_data', 0)
        total_machines = len(car_mode_coverage.get('machine_coverage', []))
        
        if machines_with_data == 0:
            warnings.append("❌ No elevator data found for the selected period")
        elif machines_with_data < total_machines:
            missing_count = total_machines - machines_with_data
            warnings.append(f"⚠️ {missing_count} of {total_machines} elevators have no data for this period")
        
        # Data type warnings
        if not car_mode_coverage.get('has_data', False):
            warnings.append("❌ No operational data (CarModeChanged events) found")
        
        if not door_coverage.get('has_data', False):
            warnings.append("ℹ️ No door cycle data available for this period")
        
        return warnings


# Global instance
data_coverage_service = DataCoverageService()
