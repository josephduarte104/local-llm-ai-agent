#!/usr/bin/env python3
"""Test uptime calculation for specific date range 7/27-8/2."""

import requests
import json
from datetime import datetime

def test_uptime_calculation():
    """Test uptime calculation for both elevators in the specified date range."""
    
    print("🔍 Testing Uptime Calculation")
    print("=" * 50)
    print("Scenario: User asks 'what is the uptime for both elevators?'")
    print("Date Range: 7/27-8/2 (2025-07-27 to 2025-08-02)")
    print("Expected: Should calculate actual uptime percentages from data")
    print()
    
    # Test with the exact date range mentioned
    payload = {
        'message': 'what is the uptime for both elevators?',
        'installationId': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
        'startISO': '2025-07-27',
        'endISO': '2025-08-02'
    }
    
    print(f"📤 Sending Request:")
    print(f"   Message: {payload['message']}")
    print(f"   Installation: {payload['installationId']}")
    print(f"   Start Date: {payload['startISO']}")
    print(f"   End Date: {payload['endISO']}")
    print()
    
    try:
        response = requests.post(
            'http://localhost:5004/api/chat', 
            json=payload, 
            timeout=60  # Increased timeout for uptime calculation
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', 'No answer provided')
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"📝 Full Response:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
            print()
            
            # Check if the response actually calculated uptime
            uptime_indicators = [
                'uptime', 'percentage', '%', 'operational', 'downtime',
                'availability', 'running', 'operational time', 'total time'
            ]
            
            calculation_indicators = [
                'calculated', 'analysis', 'data shows', 'based on',
                'during this period', 'from the data'
            ]
            
            data_indicators = [
                'Elevator 1', 'Elevator 2', 'Machine ID 1', 'Machine ID 2',
                'each elevator', 'both elevators'
            ]
            
            has_uptime_content = any(indicator.lower() in answer.lower() for indicator in uptime_indicators)
            has_calculation_content = any(indicator.lower() in answer.lower() for indicator in calculation_indicators)
            has_data_content = any(indicator.lower() in answer.lower() for indicator in data_indicators)
            
            print("🔍 Response Analysis:")
            print(f"   Contains uptime-related content: {'✅' if has_uptime_content else '❌'}")
            print(f"   Contains calculation language: {'✅' if has_calculation_content else '❌'}")
            print(f"   Contains elevator-specific data: {'✅' if has_data_content else '❌'}")
            
            # Check for specific issues
            if 'This response provides' in answer or 'clear and detailed analysis' in answer:
                print("❌ CRITICAL ISSUE: Response is meta-commentary, not actual analysis!")
            elif not has_uptime_content:
                print("❌ ISSUE: No uptime calculation performed")
            elif not has_data_content:
                print("❌ ISSUE: No elevator-specific data provided")
            else:
                print("✅ Response appears to contain uptime analysis")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📝 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request Failed: {str(e)}")

def test_debug_tool_execution():
    """Test what tools are being called for uptime queries."""
    
    print("\n🔧 Testing Tool Execution Debug")
    print("=" * 50)
    print("Let's see what happens when we ask about uptime...")
    
    # Simple uptime question
    payload = {
        'message': 'Show me the uptime data',
        'installationId': '4995d395-9b4b-4234-a8aa-9938ef5620c6',
        'startISO': '2025-07-27',
        'endISO': '2025-08-02'
    }
    
    try:
        response = requests.post(
            'http://localhost:5004/api/chat', 
            json=payload, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if we have metadata about tool execution
            metadata = result.get('metadata', {})
            tools_used = metadata.get('tools_used', [])
            
            print(f"Tools executed: {tools_used}")
            print(f"Response length: {len(result.get('answer', ''))}")
            
            # Check the answer for generic vs specific content
            answer = result.get('answer', '')
            if len(answer) < 100:
                print("⚠️ Very short response - may indicate tool failure")
            elif 'based on the data' not in answer.lower():
                print("⚠️ Response may not be using actual data")
                
    except Exception as e:
        print(f"❌ Debug test failed: {str(e)}")

if __name__ == '__main__':
    test_uptime_calculation()
    test_debug_tool_execution()
    
    print("\n🎯 Summary")
    print("=" * 50)
    print("For uptime questions, the agent should:")
    print("✅ Use the uptime_downtime tool to get actual data")
    print("✅ Calculate specific uptime percentages for each elevator")
    print("✅ Provide data-driven analysis, not generic responses")
    print("✅ Show availability for the specific date range requested")
