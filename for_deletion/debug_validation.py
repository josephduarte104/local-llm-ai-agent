#!/usr/bin/env python3
"""Debug the timezone validation logic directly."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'elevator_ai_agent'))

from services.timezone import timezone_service
from datetime import datetime
from zoneinfo import ZoneInfo

def test_timezone_validation():
    """Test the timezone validation logic directly."""
    
    print("🔧 Debug: Testing Timezone Validation Logic")
    print("=" * 50)
    
    # Test current time detection
    tz_name = "America/New_York"
    tz = ZoneInfo(tz_name)
    current_time = datetime.now(tz)
    
    print(f"Current Time ({tz_name}): {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Current Date: {current_time.date()}")
    print()
    
    # Test specific dates
    test_cases = [
        ("2025-07-26", "2025-08-02", "Should be valid - end date is today"),
        ("2025-07-26", "2025-08-07", "Should be INVALID - end date is future"),
        ("2025-08-03", "2025-08-07", "Should be INVALID - both dates are future"),
        ("2025-07-01", "2025-07-31", "Should be valid - both dates are past"),
    ]
    
    for start_str, end_str, expected in test_cases:
        print(f"Testing: {start_str} to {end_str}")
        print(f"Expected: {expected}")
        
        # Parse dates
        start_time = timezone_service.parse_iso_with_timezone(start_str, tz_name)
        end_time = timezone_service.parse_iso_with_timezone(end_str, tz_name)
        
        if start_time and end_time:
            print(f"Parsed Start: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            print(f"Parsed End: {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Test validation
            validation = timezone_service.validate_date_range(start_time, end_time, tz_name)
            
            is_valid = validation.get('is_valid', True)
            warnings = validation.get('warnings', [])
            recommendations = validation.get('recommendations', [])
            
            print(f"Result: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
            if warnings:
                print("Warnings:")
                for warning in warnings:
                    print(f"  - {warning}")
            
            if recommendations:
                print("Recommendations:")
                for rec in recommendations:
                    print(f"  - {rec}")
        else:
            print("❌ Failed to parse dates")
        
        print("-" * 30)

def test_orchestrator_validation():
    """Test the orchestrator validation logic."""
    
    print("\n🔧 Debug: Testing Orchestrator Validation Logic")
    print("=" * 50)
    
    from agents.orchestrator import query_orchestrator
    
    tz_name = "America/New_York"
    
    # Test the validation method directly
    start_time = timezone_service.parse_iso_with_timezone("2025-07-26", tz_name)
    end_time = timezone_service.parse_iso_with_timezone("2025-08-07", tz_name)
    
    if start_time and end_time:
        print(f"Testing orchestrator validation for:")
        print(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"End: {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        is_valid, error_message = query_orchestrator.validate_date_range_and_give_feedback(
            start_time, end_time, tz_name
        )
        
        print(f"Orchestrator Result: {'✅ Valid' if is_valid else '❌ Invalid'}")
        if not is_valid:
            print(f"Error Message:\n{error_message}")
    else:
        print("❌ Failed to parse test dates")

if __name__ == '__main__':
    test_timezone_validation()
    test_orchestrator_validation()
