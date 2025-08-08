"""Timezone utilities for handling installation-specific timezones."""

import logging
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

logger = logging.getLogger(__name__)


class TimezoneService:
    """Service for timezone-aware datetime operations."""
    
    @staticmethod
    def epoch_to_local_datetime(epoch_ms: int, tz_name: str) -> datetime:
        """
        Convert epoch milliseconds to timezone-aware datetime.
        
        Args:
            epoch_ms: Epoch timestamp in milliseconds
            tz_name: IANA timezone name (e.g., 'America/New_York')
            
        Returns:
            Timezone-aware datetime object
        """
        try:
            # Convert to seconds and create UTC datetime
            utc_dt = datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
            
            # Convert to target timezone
            target_tz = ZoneInfo(tz_name)
            local_dt = utc_dt.astimezone(target_tz)
            
            return local_dt
            
        except Exception as e:
            logger.error(f"Error converting epoch {epoch_ms} to timezone {tz_name}: {e}")
            # Fallback to UTC if timezone conversion fails
            return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
    
    @staticmethod
    def local_datetime_to_epoch(dt: datetime) -> int:
        """
        Convert timezone-aware datetime to epoch milliseconds.
        
        Args:
            dt: Timezone-aware datetime
            
        Returns:
            Epoch timestamp in milliseconds
        """
        return int(dt.timestamp() * 1000)
    
    @staticmethod
    def parse_iso_with_timezone(iso_string: str, tz_name: str) -> Optional[datetime]:
        """
        Parse ISO date string and convert to specified timezone.
        
        Args:
            iso_string: ISO format date string (e.g., '2023-12-01T00:00:00')
            tz_name: IANA timezone name
            
        Returns:
            Timezone-aware datetime or None if parsing fails
        """
        try:
            # Parse the ISO string (assuming it's naive)
            if 'T' in iso_string:
                naive_dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            else:
                # Just date, assume start of day
                naive_dt = datetime.fromisoformat(f"{iso_string}T00:00:00")
            
            # If it's already timezone-aware, convert to target timezone
            if naive_dt.tzinfo is not None:
                target_tz = ZoneInfo(tz_name)
                return naive_dt.astimezone(target_tz)
            else:
                # Assume it's in the target timezone
                target_tz = ZoneInfo(tz_name)
                return naive_dt.replace(tzinfo=target_tz)
                
        except Exception as e:
            logger.error(f"Error parsing ISO string {iso_string}: {e}")
            return None
    
    @staticmethod
    def format_duration_human(minutes: float) -> str:
        """
        Format duration in minutes to human-readable string.
        
        Args:
            minutes: Duration in minutes
            
        Returns:
            Human-readable duration string
        """
        if minutes < 60:
            return f"{minutes:.1f} minutes"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes / 60
            return f"{hours:.1f} hours"
        else:  # Days
            days = minutes / 1440
            return f"{days:.1f} days"
    
    @staticmethod
    def get_week_boundaries(dt: datetime) -> tuple[datetime, datetime]:
        """
        Get start and end of week for given datetime (Monday to Sunday).
        
        Args:
            dt: Reference datetime (timezone-aware)
            
        Returns:
            Tuple of (week_start, week_end) datetimes
        """
        # Get Monday of the week
        days_since_monday = dt.weekday()
        week_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = week_start - timedelta(days=days_since_monday)
        
        # Get Sunday end of week
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return week_start, week_end

    @staticmethod
    def validate_date_range(
        start_time: datetime, 
        end_time: datetime, 
        tz_name: str, 
        today_override: Optional[datetime] = None
    ) -> dict:
        """
        Validate date range and provide guidance for future dates.
        Enforces 2-week maximum range excluding current day.
        
        Args:
            start_time: Start datetime (timezone-aware)
            end_time: End datetime (timezone-aware)
            tz_name: IANA timezone name
            today_override: Optional override for "today" (for testing)
            
        Returns:
            Dictionary with validation results and recommendations
        """
        from datetime import datetime, timezone as dt_timezone
        
        # Get current time in the installation's timezone
        if today_override:
            current_local = today_override
        else:
            current_utc = datetime.now(dt_timezone.utc)
            target_tz = ZoneInfo(tz_name)
            current_local = current_utc.astimezone(target_tz)
        
        result = {
            'is_valid': True,
            'warnings': [],
            'recommendations': [],
            'latest_available_date': current_local.date().isoformat(),
            'current_time_local': current_local.isoformat()
        }
        
        # Check for future dates - reject ANY future date completely
        if start_time.date() > current_local.date():
            result['is_valid'] = False
            result['warnings'].append(f"⚠️ Start date {start_time.date().isoformat()} is in the future")
            result['recommendations'].append(f"📅 Latest available date: {current_local.date().isoformat()}")
            result['recommendations'].append(f"🕐 Current time ({tz_name}): {current_local.strftime('%Y-%m-%d %H:%M:%S')}")
        elif end_time.date() > current_local.date():
            # Do NOT adjust - reject the entire request if end date is in future
            result['is_valid'] = False
            result['warnings'].append(f"⚠️ End date {end_time.date().isoformat()} is in the future")
            result['recommendations'].append(f"📅 Latest available date: {current_local.date().isoformat()}")
            result['recommendations'].append(f"🕐 Current time ({tz_name}): {current_local.strftime('%Y-%m-%d %H:%M:%S')}")
            result['recommendations'].append("💡 Please use a date range that ends today or in the past")
        
        # Check date range validity
        if start_time >= end_time:
            result['is_valid'] = False
            result['warnings'].append("⚠️ Start date must be before end date")
        
        # NEW: Check for 2-week maximum range (excluding current day)
        # Calculate the latest valid end date (yesterday)
        yesterday = current_local.date() - timedelta(days=1)
        
        # Check if end date is current day (not allowed)
        if end_time.date() >= current_local.date():
            result['is_valid'] = False
            result['warnings'].append(f"⚠️ End date cannot be current day ({current_local.date().isoformat()})")
            result['recommendations'].append(f"📅 Latest allowed end date: {yesterday.isoformat()}")
            result['recommendations'].append("💡 Date range cannot include the current day")
        
        # Check 2-week (14 days) maximum range for valid dates
        if result['is_valid']:
            range_days = (end_time.date() - start_time.date()).days
            max_days = 14  # 2 weeks
            
            if range_days > max_days:
                result['is_valid'] = False
                result['warnings'].append(f"⚠️ Date range too large: {range_days} days (maximum: {max_days} days)")
                
                # Calculate the earliest valid start date for the given end date
                earliest_start = end_time.date() - timedelta(days=max_days)
                result['recommendations'].append(f"📅 For end date {end_time.date().isoformat()}, earliest start date: {earliest_start.isoformat()}")
                result['recommendations'].append(f"💡 Maximum allowed range: {max_days} days (2 weeks)")
                result['recommendations'].append("🔧 Please select a shorter date range")
        
        # Check for very large date ranges (this warning is now less relevant due to 14-day limit)
        range_days = (end_time - start_time).days
        if range_days > 365:
            result['warnings'].append(f"⚠️ Large date range: {range_days} days. Consider smaller ranges for better performance")
            result['recommendations'].append("💡 Recommended: Analyze periods of 30-90 days for optimal performance")
        
        return result


# Global instance
timezone_service = TimezoneService()
