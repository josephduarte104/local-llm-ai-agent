"""Test configuration and fixtures for elevator ops tests."""

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


@pytest.fixture
def sample_installation_tz():
    """Sample installation timezone for testing."""
    return "America/New_York"


@pytest.fixture 
def sample_datetime_utc():
    """Sample UTC datetime for testing."""
    return datetime(2023, 12, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_datetime_local():
    """Sample local datetime for testing."""
    tz = ZoneInfo("America/New_York")
    return datetime(2023, 12, 1, 7, 0, 0, tzinfo=tz)  # UTC-5 in December


@pytest.fixture
def sample_car_mode_events():
    """Sample CarModeChanged events for testing."""
    return [
        {
            'kafkaMessage': {
                'Timestamp': 1701432000000,  # 2023-12-01 12:00:00 UTC
                'CarModeChanged': {
                    'MachineId': 'Elevator_1',
                    'ModeName': 'NOR',  # Uptime
                    'CarMode': 'Normal',
                    'AlarmSeverity': 'None'
                }
            }
        },
        {
            'kafkaMessage': {
                'Timestamp': 1701435600000,  # 2023-12-01 13:00:00 UTC (1 hour later)
                'CarModeChanged': {
                    'MachineId': 'Elevator_1', 
                    'ModeName': 'COR',  # Downtime
                    'CarMode': 'Corrective',
                    'AlarmSeverity': 'Critical'
                }
            }
        },
        {
            'kafkaMessage': {
                'Timestamp': 1701439200000,  # 2023-12-01 14:00:00 UTC (2 hours from start)
                'CarModeChanged': {
                    'MachineId': 'Elevator_1',
                    'ModeName': 'NOR',  # Back to uptime
                    'CarMode': 'Normal', 
                    'AlarmSeverity': 'None'
                }
            }
        }
    ]
