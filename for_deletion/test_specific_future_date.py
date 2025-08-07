#!/usr/bin/env python3
"""Test specific future date validation scenario."""

import requests
import json
from datetime import datetime

# Test the exact scenario described by the user
def test_specific_future_date_scenario():
    """Test the specific scenario where agent accepts 7/26 to 8/7 date range."""
    
    print("🔍 Testing Specific Future Date Scenario")
    print("=" * 50)
    print("Scenario: Agent responding to date range 7/26 to 8/7")
    print("Current Date: August 2, 2025")
    print("Expected: Should reject because 8/7 is in the future")
    print()
    
    # Test with explicit future date range
    payload = {
        'message': 'How many elevators?',
        'installationId': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
        'startISO': '2025-07-26',
        'endISO': '2025-08-07'  # This is in the future!
    }
    
    print(f"📤 Sending Request:")
    print(f"   Message: {payload['message']}")
    print(f"   Start Date: {payload['startISO']}")
    print(f"   End Date: {payload['endISO']}")
    print(f"   Today: {datetime.now().strftime('%Y-%m-%d')}")
    
    try:
        response = requests.post(
            'http://localhost:5004/api/chat', 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', 'No answer provided')
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            # Check if validation error occurred
            metadata = result.get('metadata', {})
            if result.get('error') and metadata.get('validation_error'):
                print("✅ SUCCESS: Date validation correctly rejected future dates")
                print(f"📝 Error Message: {answer}")
            elif 'Cannot analyze data for the requested time range' in answer:
                print("✅ SUCCESS: Tool-level validation caught the issue")
                print(f"📝 Tool Response: {answer[:200]}...")
            elif '2025-08-07' in answer or 'within the valid date range' in answer:
                print("❌ FAILURE: Agent incorrectly accepted future dates!")
                print(f"📝 Incorrect Response: {answer[:500]}...")
                print("\n🚨 CRITICAL ISSUE: Agent thinks 8/7/2025 is valid when today is 8/2/2025")
            else:
                print("⚠️ UNKNOWN: Unexpected response format")
                print(f"📝 Response: {answer[:300]}...")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📝 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request Failed: {str(e)}")

def test_default_range_validation():
    """Test default date range validation (no explicit dates)."""
    
    print("\n🗓️ Testing Default Date Range Validation")
    print("=" * 50)
    print("Scenario: No explicit dates provided, using default range")
    print("Expected: Should use last 7 days (which may include today = valid)")
    
    payload = {
        'message': 'How many elevators?',
        'installationId': '4995d395-9b4b-4234-a8aa-9938ef5620c6'
        # No startISO/endISO provided
    }
    
    print(f"📤 Sending Request:")
    print(f"   Message: {payload['message']}")
    print(f"   Dates: Default (last 7 days)")
    
    try:
        response = requests.post(
            'http://localhost:5004/api/chat', 
            json=payload, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', 'No answer provided')
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"📝 Response: {answer[:400]}...")
            
            # Check for date mentions in response
            if '2025-08-07' in answer or '2025-08-06' in answer or '2025-08-05' in answer or '2025-08-04' in answer or '2025-08-03' in answer:
                print("❌ FAILURE: Default range includes future dates!")
            elif '2025-08-02' in answer and '2025-07-26' in answer:
                print("✅ PARTIAL SUCCESS: Uses reasonable range ending at current date")
            else:
                print("ℹ️ INFO: No specific date range mentioned")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request Failed: {str(e)}")

if __name__ == '__main__':
    test_specific_future_date_scenario()
    test_default_range_validation()
    
    print("\n🎯 Analysis Summary")
    print("=" * 50)
    print("The agent should NEVER accept or mention dates after 2025-08-02")
    print("Any response containing dates like 2025-08-03 through 2025-08-07 is WRONG")
    print("✅ Correct: Reject with clear error message")
    print("❌ Incorrect: Process request and mention future dates")
