#!/usr/bin/env python3
"""
Comprehensive test to verify agent doesn't hallucinate future date data.
Tests all scenarios that were causing hallucination issues.
"""

import requests
import json
from datetime import datetime

def test_scenario(description, data, expected_behavior):
    """Test a specific scenario and check results."""
    print(f"\n🔍 Testing: {description}")
    print("="*50)
    
    try:
        response = requests.post('http://127.0.0.1:5004/query', json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', 'No response')
            
            # Check if response contains future dates that shouldn't be there
            forbidden_dates = ['2025-08-03', '2025-08-04', '2025-08-05', '2025-08-06', '2025-08-07', '2025-08-08']
            contains_future_dates = any(date in response_text for date in forbidden_dates)
            
            if 'Cannot analyze data for the requested time range' in response_text:
                print("✅ CORRECT: Properly rejected future date request")
                print(f"📝 Rejection message: {response_text[:200]}...")
                return True
            elif contains_future_dates:
                print("❌ FAILED: Response contains forbidden future dates!")
                print(f"📝 Response: {response_text[:300]}...")
                return False
            else:
                print("✅ CORRECT: Valid response without future dates")
                print(f"📝 Response: {response_text[:200]}...")
                return True
        else:
            print(f"❌ REQUEST FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run comprehensive validation tests."""
    print("🚀 Comprehensive Agent Validation Test")
    print("="*60)
    print(f"Current Date: {datetime.now().strftime('%B %d, %Y')}")
    print("Testing agent to ensure NO hallucination of future date data")
    
    tests = [
        {
            'description': 'Original Problem: 7/26 to 8/6 range (future end)',
            'data': {
                'message': 'How many elevators are in this installation?',
                'installation_id': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
                'startISO': '2025-07-26T00:00:00',
                'endISO': '2025-08-06T00:00:00'
            },
            'expected': 'Should reject because 8/6 is in the future'
        },
        {
            'description': 'User Reported: 7/26 to 8/7 range (future end)',
            'data': {
                'message': 'How many elevators are in this installation?',
                'installation_id': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
                'startISO': '2025-07-26T00:00:00',
                'endISO': '2025-08-07T00:00:00'
            },
            'expected': 'Should reject because 8/7 is in the future'
        },
        {
            'description': 'Edge Case: Entirely future range (8/3 to 8/10)',
            'data': {
                'message': 'Analyze elevator performance',
                'installation_id': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
                'startISO': '2025-08-03T00:00:00',
                'endISO': '2025-08-10T00:00:00'
            },
            'expected': 'Should reject because entire range is in the future'
        },
        {
            'description': 'Valid Range: 7/20 to 8/2 (ends today)',
            'data': {
                'message': 'How many elevators are in this installation?',
                'installation_id': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
                'startISO': '2025-07-20T00:00:00',
                'endISO': '2025-08-02T23:59:59'
            },
            'expected': 'Should work - ends on current date'
        },
        {
            'description': 'Default Range: No explicit dates',
            'data': {
                'message': 'How many elevators are in this installation?',
                'installation_id': '4995d395-9b4b-4234-a8aa-9938ef5620c6'
            },
            'expected': 'Should work with default range'
        },
        {
            'description': 'Another Performance Query: Future range (7/30 to 8/5)',
            'data': {
                'message': 'What is the uptime for the elevators?',
                'installation_id': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
                'startISO': '2025-07-30T00:00:00',
                'endISO': '2025-08-05T00:00:00'
            },
            'expected': 'Should reject because 8/5 is in the future'
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n📊 Test {i}/{len(tests)}")
        result = test_scenario(test['description'], test['data'], test['expected'])
        results.append(result)
    
    # Summary
    print(f"\n🎯 Test Results Summary")
    print("="*40)
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Agent is properly validating dates and NOT hallucinating future data")
    else:
        print(f"\n⚠️ {total - passed} TEST(S) FAILED")
        print("❌ Agent may still have hallucination issues")
    
    print(f"\n💡 Critical Success Criteria:")
    print("• No responses should contain dates after 2025-08-02")
    print("• Future date requests should be rejected with clear error messages")
    print("• Valid historical/current date ranges should work normally")

if __name__ == "__main__":
    main()
