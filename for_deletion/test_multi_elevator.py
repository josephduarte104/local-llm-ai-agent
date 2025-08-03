#!/usr/bin/env python3
"""Test the enhanced multi-elevator uptime functionality directly"""

import os
import sys
from datetime import datetime

# Add the elevator_ai_agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'elevator_ai_agent'))

from services.uptime import uptime_service
from services.timezone import timezone_service


def test_multi_elevator_uptime():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('elevator_ai_agent/.env')
    
    installation_id = "4995d395-9b4b-4234-a8aa-9938ef5620c6"
    installation_tz = "America/New_York"
    
    # Parse date range
    start_time = timezone_service.parse_iso_with_timezone("2025-08-01T00:00:00", installation_tz)
    end_time = timezone_service.parse_iso_with_timezone("2025-08-02T23:59:59", installation_tz)
    
    print(f"Testing multi-elevator uptime for installation: {installation_id}")
    print(f"Date range: {start_time} to {end_time}")
    print("=" * 80)
    
    # Get uptime metrics using the enhanced service
    result = uptime_service.get_uptime_metrics(
        installation_id=installation_id,
        start_time=start_time,
        end_time=end_time,
        installation_tz=installation_tz
    )
    
    # Print summary
    summary = result['installation_summary']
    print(f"\n📊 INSTALLATION SUMMARY:")
    print(f"   Total Elevators: {summary.get('total_elevators', 'N/A')}")
    print(f"   Elevators with Data: {summary.get('elevators_with_data', 'N/A')}")
    print(f"   Elevators without Data: {summary.get('elevators_without_data', 'N/A')}")
    print(f"   Overall Uptime: {summary['uptime_percentage']:.1f}%")
    print(f"   Data Coverage: {summary['data_coverage_percentage']:.1f}%")
    
    # Print machine metrics
    print(f"\n🔧 INDIVIDUAL ELEVATOR METRICS:")
    for machine in result['machine_metrics']:
        mid = machine['machine_id']
        has_data = machine.get('has_data', True)
        
        if has_data:
            uptime_pct = machine['uptime_percentage']
            uptime_human = machine['uptime_human']
            downtime_human = machine['downtime_human']
            print(f"   Elevator {mid}: {uptime_pct:.1f}% uptime ({uptime_human} up, {downtime_human} down)")
        else:
            print(f"   Elevator {mid}: No data for this time period")
    
    # Print interpretation
    print(f"\n💡 INTERPRETATION:")
    for line in result['interpretation']:
        print(f"   {line}")
    
    print("=" * 80)
    print("✅ Multi-elevator enhancement test completed!")


if __name__ == "__main__":
    test_multi_elevator_uptime()
