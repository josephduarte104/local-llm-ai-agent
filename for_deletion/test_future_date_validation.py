#!/usr/bin/env python3
"""Test script to validate future date handling in the elevator agent."""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = 'http://localhost:5004'
INSTALLATION_ID = '4995d395-9b4b-4234-a8aa-9938ef5620c6'

def test_future_date_query():
    """Test queries with future dates to ensure proper validation."""
    
    print("🧪 Testing Future Date Validation for Elevator AI Agent")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        {
            'name': 'Future Date Range (7/26 to 8/6)',
            'message': 'How many elevators?',
            'start_date': '2025-07-26',
            'end_date': '2025-08-06',
            'expected_behavior': 'Should reject due to future dates'
        },
        {
            'name': 'Mixed Past/Future (8/1 to 8/6)', 
            'message': 'Analyze uptime for August 1 to August 6',
            'start_date': '2025-08-01',
            'end_date': '2025-08-06',
            'expected_behavior': 'Should adjust end date to current time'
        },
        {
            'name': 'All Future (8/3 to 8/6)',
            'message': 'What is the uptime status?',
            'start_date': '2025-08-03',
            'end_date': '2025-08-06',
            'expected_behavior': 'Should completely reject - all dates in future'
        },
        {
            'name': 'Valid Historical Range',
            'message': 'How many elevators?',
            'start_date': '2025-07-01',
            'end_date': '2025-07-31',
            'expected_behavior': 'Should work normally'
        },
        {
            'name': 'No Date Range Specified',
            'message': 'How many elevators?',
            'start_date': None,
            'end_date': None,
            'expected_behavior': 'Should use default range (should work)'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Query: {test_case['message']}")
        
        if test_case['start_date'] and test_case['end_date']:
            print(f"   Date Range: {test_case['start_date']} to {test_case['end_date']}")
        else:
            print(f"   Date Range: Default (last 7 days)")
            
        print(f"   Expected: {test_case['expected_behavior']}")
        
        # Prepare request payload
        payload = {
            'message': test_case['message'],
            'installationId': INSTALLATION_ID
        }
        
        if test_case['start_date'] and test_case['end_date']:
            payload['startISO'] = test_case['start_date']
            payload['endISO'] = test_case['end_date']
        
        try:
            # Send request
            response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'No answer provided')
                
                print(f"   ✅ Status: SUCCESS (HTTP {response.status_code})")
                
                # Check for validation errors
                if result.get('error') and 'validation_error' in result.get('metadata', {}):
                    print(f"   🚫 Validation Error: Date range properly rejected")
                elif 'Cannot analyze data for the requested time range' in answer:
                    print(f"   🚫 Tool-level Validation: Properly rejected by tools")
                elif '⚠️' in answer or 'future' in answer.lower():
                    print(f"   ⚠️ Warning: Future date warning provided")
                else:
                    print(f"   ✅ Normal Response: Processing completed")
                
                # Show first 200 chars of response
                response_preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"   📝 Response Preview: {response_preview}")
                
            else:
                print(f"   ❌ Status: FAILED (HTTP {response.status_code})")
                print(f"   📝 Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Status: REQUEST FAILED")
            print(f"   📝 Error: {str(e)}")
        
        print("-" * 40)

def test_current_date_detection():
    """Test that the system correctly identifies current date."""
    print(f"\n🗓️ Current Date Detection Test")
    print("=" * 40)
    
    # Get current date
    now = datetime.now()
    print(f"System Current Date: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Today: {now.strftime('%Y-%m-%d')}")
    print(f"Tomorrow: {(now + timedelta(days=1)).strftime('%Y-%m-%d')}")
    print(f"Yesterday: {(now - timedelta(days=1)).strftime('%Y-%m-%d')}")

if __name__ == '__main__':
    test_current_date_detection()
    test_future_date_query()
    
    print("\n🎯 Test Summary")
    print("=" * 40)
    print("✅ If validation errors show up for future dates: SUCCESS")
    print("❌ If agent provides made-up data for future dates: FAILURE")
    print("\n💡 The agent should:")
    print("  • Reject queries with future start dates")
    print("  • Adjust future end dates to current time")
    print("  • Provide clear error messages for invalid ranges")
    print("  • Never invent data for dates that don't exist")
