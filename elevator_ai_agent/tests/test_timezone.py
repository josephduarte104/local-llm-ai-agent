"""Tests for timezone service utilities."""

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ..services.timezone import TimezoneService


class TestTimezoneService:
    """Test timezone conversion utilities."""
    
    def test_epoch_to_local_datetime(self, sample_datetime_utc, sample_installation_tz):
        """Test converting epoch milliseconds to local timezone."""
        # UTC datetime: 2023-12-01 12:00:00
        epoch_ms = 1701432000000
        
        result = TimezoneService.epoch_to_local_datetime(epoch_ms, sample_installation_tz)
        
        # Should be 7:00 AM in New York (UTC-5 in December)
        assert result.hour == 7
        assert result.day == 1
        assert result.month == 12
        assert result.year == 2023
        assert str(result.tzinfo) == sample_installation_tz
    
    def test_local_datetime_to_epoch(self, sample_datetime_local):
        """Test converting local datetime to epoch milliseconds."""
        # Local: 2023-12-01 07:00:00 America/New_York = 12:00:00 UTC
        expected_epoch = 1701432000000
        
        result = TimezoneService.local_datetime_to_epoch(sample_datetime_local)
        
        assert result == expected_epoch
    
    def test_parse_iso_with_timezone(self, sample_installation_tz):
        """Test parsing ISO string with timezone."""
        iso_string = "2023-12-01T07:00:00"
        
        result = TimezoneService.parse_iso_with_timezone(iso_string, sample_installation_tz)
        
        assert result is not None
        assert result.hour == 7
        assert result.day == 1
        assert str(result.tzinfo) == sample_installation_tz
    
    def test_format_duration_human(self):
        """Test human-readable duration formatting."""
        # Test minutes
        assert TimezoneService.format_duration_human(30.5) == "30.5 minutes"
        
        # Test hours
        assert TimezoneService.format_duration_human(90) == "1.5 hours"
        
        # Test days
        assert TimezoneService.format_duration_human(2880) == "2.0 days"
    
    def test_get_week_boundaries(self, sample_datetime_local):
        """Test getting week start/end boundaries."""
        # 2023-12-01 is a Friday
        start, end = TimezoneService.get_week_boundaries(sample_datetime_local)
        
        # Should start on Monday (Nov 27) and end on Sunday (Dec 3)
        assert start.weekday() == 0  # Monday
        assert start.day == 27
        assert start.month == 11
        assert start.hour == 0
        
        assert end.weekday() == 6  # Sunday  
        assert end.day == 3
        assert end.month == 12
        assert end.hour == 23
