"""Tests for uptime calculation service."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from services.uptime import UptimeService


class TestUptimeService:
    """Test uptime calculation logic."""
    
    def test_get_mode_status(self):
        """Test mode classification."""
        # Test uptime modes
        assert UptimeService.get_mode_status('NOR') == 'uptime'
        assert UptimeService.get_mode_status('IDL') == 'uptime'
        assert UptimeService.get_mode_status('ATT') == 'uptime'
        
        # Test downtime modes
        assert UptimeService.get_mode_status('COR') == 'downtime'
        assert UptimeService.get_mode_status('NAV') == 'downtime'
        assert UptimeService.get_mode_status('ESB') == 'downtime'
        
        # Test unknown modes
        assert UptimeService.get_mode_status('UNKNOWN') == 'unknown'
        assert UptimeService.get_mode_status('XYZ') == 'unknown'
    
    def test_build_intervals_basic(self, sample_car_mode_events):
        """Test basic interval building from events."""
        tz = ZoneInfo("America/New_York")
        start_time = datetime(2023, 12, 1, 7, 0, 0, tzinfo=tz)  # 7 AM local
        end_time = datetime(2023, 12, 1, 10, 0, 0, tzinfo=tz)    # 10 AM local
        
        intervals = UptimeService.build_intervals(
            events=sample_car_mode_events,
            start_time=start_time,
            end_time=end_time,
            machine_id="Elevator_1",
            tz_name="America/New_York"
        )
        
        # Should have 3 intervals based on the sample events
        assert len(intervals) == 3
        
        # First interval: NOR (uptime)
        assert intervals[0].status == 'uptime'
        assert intervals[0].mode_name == 'NOR'
        
        # Second interval: COR (downtime)  
        assert intervals[1].status == 'downtime'
        assert intervals[1].mode_name == 'COR'
        
        # Third interval: NOR (uptime)
        assert intervals[2].status == 'uptime'
        assert intervals[2].mode_name == 'NOR'
    
    def test_calculate_metrics(self):
        """Test uptime metrics calculation."""
        from services.uptime import ModeInterval
        
        tz = ZoneInfo("America/New_York")
        base_time = datetime(2023, 12, 1, 7, 0, 0, tzinfo=tz)
        
        # Create test intervals: 60 min uptime, 30 min downtime, 30 min uptime
        intervals = [
            ModeInterval(
                start_time=base_time,
                end_time=base_time.replace(hour=8),  # +1 hour
                mode_name='NOR',
                machine_id='Elevator_1',
                status='uptime'
            ),
            ModeInterval(
                start_time=base_time.replace(hour=8),
                end_time=base_time.replace(hour=8, minute=30),  # +30 min
                mode_name='COR',
                machine_id='Elevator_1', 
                status='downtime'
            ),
            ModeInterval(
                start_time=base_time.replace(hour=8, minute=30),
                end_time=base_time.replace(hour=9),  # +30 min
                mode_name='NOR',
                machine_id='Elevator_1',
                status='uptime'
            )
        ]
        
        metrics = UptimeService.calculate_metrics(intervals, 'Elevator_1', 'test_installation')
        
        # Total: 120 minutes (90 uptime + 30 downtime)
        assert metrics.uptime_minutes == 90.0
        assert metrics.downtime_minutes == 30.0
        assert metrics.total_minutes == 120.0
        assert metrics.uptime_percentage == 75.0  # 90/120 * 100
        assert metrics.downtime_percentage == 25.0  # 30/120 * 100
