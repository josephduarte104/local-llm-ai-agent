"""Tests for uptime calculation service."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from elevator_ai_agent.services.uptime import UptimeService


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
        from elevator_ai_agent.services.uptime import ModeInterval
        
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

    def test_get_uptime_metrics_comprehensive(self, mocker):
        """
        Comprehensive test for get_uptime_metrics with multiple elevators,
        downtime modes (COR, NAV), and installation summary validation.
        """
        # 1. Mock external dependencies
        mock_cosmos_service = mocker.MagicMock()
        mocker.patch('elevator_ai_agent.services.uptime.get_cosmos_service', return_value=mock_cosmos_service)

        # 2. Define test data
        installation_id = "test-install-1"
        tz_name = "America/New_York"
        tz = ZoneInfo(tz_name)
        start_time = datetime(2024, 8, 1, 0, 0, 0, tzinfo=tz)
        end_time = datetime(2024, 8, 1, 4, 0, 0, tzinfo=tz) # 4-hour window
        start_epoch = int(start_time.timestamp() * 1000)
        end_epoch = int(end_time.timestamp() * 1000)

        mock_cosmos_service.get_all_machine_ids.return_value = ["101", "102"]

        # Elevator 101: 1 hour NOR, 1 hour COR (downtime)
        # Elevator 102: 1 hour NOR, 1 hour NAV (downtime)
        mock_events = [
            # Elevator 101
            {"Timestamp": start_epoch, "MachineId": "101", "ModeName": "NOR"},
            {"Timestamp": int((start_time.replace(hour=1)).timestamp() * 1000), "MachineId": "101", "ModeName": "COR"},
            # Elevator 102
            {"Timestamp": start_epoch, "MachineId": "102", "ModeName": "NOR"},
            {"Timestamp": int((start_time.replace(hour=1)).timestamp() * 1000), "MachineId": "102", "ModeName": "NAV"},
        ]
        mock_cosmos_service.get_car_mode_changes.return_value = mock_events

        # 3. Call the function to be tested
        result = UptimeService.get_uptime_metrics(
            installation_id=installation_id,
            start_time=start_time,
            end_time=end_time,
            installation_tz=tz_name
        )

        # 4. Assert results
        
        # Overall summary
        summary = result['installation_summary']
        assert summary['total_elevators'] == 2
        
        # Total uptime: 60 mins (Elevator 1) + 60 mins (Elevator 2) = 120 mins
        assert summary['uptime_minutes'] == pytest.approx(120.0)
        # Total downtime: 180 mins (Elevator 1) + 180 mins (Elevator 2) = 360 mins
        # Elevator 101 from 1am to 4am is COR (180 mins)
        # Elevator 102 from 1am to 4am is NAV (180 mins)
        # The events extend to the end of the query time.
        assert summary['downtime_minutes'] == pytest.approx(180.0 + 180.0)
        
        # Total duration is uptime + downtime
        total_duration = 120.0 + 360.0
        expected_uptime_pct = (120.0 / total_duration) * 100
        expected_downtime_pct = (360.0 / total_duration) * 100
        
        assert summary['uptime_percentage'] == pytest.approx(expected_uptime_pct)
        assert summary['downtime_percentage'] == pytest.approx(expected_downtime_pct)

        # Per-machine metrics
        machine_metrics = result['machine_metrics']
        assert len(machine_metrics) == 2

        # Elevator 101
        metrics_101 = next(m for m in machine_metrics if m['machine_id'] == "101")
        assert metrics_101['uptime_minutes'] == pytest.approx(60.0)
        assert metrics_101['downtime_minutes'] == pytest.approx(180.0)
        assert metrics_101['downtime_percentage'] == pytest.approx(75.0)
        assert len(metrics_101['intervals']) == 2
        assert metrics_101['intervals'][1]['mode'] == 'COR'

        # Elevator 102
        metrics_102 = next(m for m in machine_metrics if m['machine_id'] == "102")
        assert metrics_102['uptime_minutes'] == pytest.approx(60.0)
        assert metrics_102['downtime_minutes'] == pytest.approx(180.0) # 1am to 4am
        assert metrics_102['downtime_percentage'] == pytest.approx(75.0) # 180 / 240
        assert len(metrics_102['intervals']) == 2
        assert metrics_102['intervals'][1]['mode'] == 'NAV'


