#!/usr/bin/env python3
"""Test script for enhanced uptime analysis with date validation and granular reporting."""

import sys
import os
import json
from datetime import datetime, timedelta, timezone

# Add the elevator_ai_agent directory to the path
sys.path.append('/Users/jduarte/DevOps/local-llm-ai-agent/elevator_ai_agent')

from services.timezone import timezone_service
from tools.car_mode_changed import car_mode_changed_tool

def test_enhanced_uptime_analysis():
    """Test the enhanced uptime analysis functionality."""
    
    print("🔧 Testing Enhanced Uptime Analysis Features")
    print("=" * 60)
    
    # Test installation ID
    installation_id = "4995d395-9b4b-4234-a8aa-9938ef5620c6"
    tz = "America/New_York"
    
    print(f"Installation ID: {installation_id}")
    print(f"Timezone: {tz}")
    print()
    
    # Test 1: Future date validation
    print("🚀 Test 1: Future Date Validation")
    print("-" * 40)
    
    # Create timezone-aware future dates using UTC then convert
    now_utc = datetime.now(timezone.utc)
    future_start = now_utc + timedelta(days=1)
    future_end = future_start + timedelta(days=1)
    
    print(f"Testing future date range: {future_start.date()} to {future_end.date()}")
    
    try:
        date_validation = timezone_service.validate_date_range(future_start, future_end, tz)
        print("✅ Date validation executed successfully")
        print(f"Warnings: {date_validation.get('warnings', [])}")
        print(f"Recommendations: {date_validation.get('recommendations', [])}")
        print(f"Latest available date: {date_validation.get('latest_available_date', 'Not provided')}")
    except Exception as e:
        print(f"❌ Date validation failed: {e}")
    
    print()
    
    # Test 2: Historical date with good data (August 1-2, 2025) 
    print("📊 Test 2: Historical Analysis with Granular Details")
    print("-" * 50)
    
    # Use the parse_iso_with_timezone method
    start_dt = timezone_service.parse_iso_with_timezone("2025-08-01", tz)
    end_dt = timezone_service.parse_iso_with_timezone("2025-08-02", tz)
    
    if start_dt is None or end_dt is None:
        print("❌ Failed to parse date strings")
        return
    
    # Adjust end time to be end of day
    end_dt = end_dt.replace(hour=23, minute=59, second=59)
    
    print(f"Analyzing period: {start_dt.date()} to {end_dt.date()}")
    
    try:
        result = car_mode_changed_tool.run(
            installation_id=installation_id,
            tz=tz,
            start=start_dt,
            end=end_dt
        )
        
        print("✅ Analysis completed successfully")
        print()
        
        # Display the enhanced interpretation
        if 'interpretation' in result:
            print("🎯 Enhanced Analysis Results:")
            print("-" * 30)
            for line in result['interpretation']:
                print(line)
        
        print()
        
        # Display summary metrics
        if 'installation_summary' in result:
            summary = result['installation_summary']
            print("📈 Summary Metrics:")
            uptime = summary.get('uptime_percentage', 0)
            machines = summary.get('machines_with_data', 0)
            coverage = summary.get('data_coverage_percentage', 0)
            
            print(f"  • Overall uptime: {uptime:.1f}%")
            print(f"  • Machines analyzed: {machines}")
            print(f"  • Data coverage: {coverage:.1f}%")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🏁 Enhanced uptime analysis test completed!")

if __name__ == "__main__":
    test_enhanced_uptime_analysis()
