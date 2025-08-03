#!/usr/bin/env python3
"""
Test script to verify daily breakdown functionality in uptime calculations.
Tests the enhanced uptime service that provides daily hour breakdowns.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'elevator_ai_agent'))

from services.uptime import UptimeService
from services.cosmos import CosmosService
from services.timezone import TimezoneService
from datetime import datetime

def test_daily_breakdown():
    """Test the daily breakdown functionality for incomplete data scenarios."""
    print("🧪 Testing Daily Breakdown Functionality")
    print("=" * 50)
    
    # Initialize services
    cosmos_service = CosmosService()
    timezone_service = TimezoneService()
    uptime_service = UptimeService(cosmos_service, timezone_service)
    
    # Installation and machine IDs
    installation_id = "4995d395-9b4b-4234-a8aa-9938ef5620c6"
    machine_ids = ["1", "2"]
    
    # Test with a date range that should have limited data
    start_date = "2025-07-26"  # Past dates for testing
    end_date = "2025-08-01"
    
    print(f"📊 Testing uptime calculation for {start_date} to {end_date}")
    print(f"🏢 Installation: {installation_id}")
    print(f"🛗 Machine IDs: {machine_ids}")
    print()
    
    try:
        # Get uptime metrics
        result = uptime_service.get_uptime_metrics(
            installation_id=installation_id,
            machine_ids=machine_ids,
            start_date=start_date,
            end_date=end_date
        )
        
        print("✅ Uptime calculation completed!")
        print(f"📈 Result type: {type(result)}")
        print(f"📝 Result length: {len(str(result))} characters")
        print()
        print("🔍 Result content:")
        print("-" * 30)
        print(result)
        print("-" * 30)
        
        # Check if daily breakdown is included
        if "Daily Data Availability" in result or "daily" in result.lower():
            print("✅ Daily breakdown functionality appears to be working!")
        else:
            print("⚠️  Daily breakdown may not be triggered or visible in this result")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_daily_breakdown()
