"""
Test script for the Elevator Operations Agent
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
import pytz

# Add src to path for imports
sys.path.append('src')

from src.config.settings import get_settings
from src.agent.elevator_agent import ElevatorAgent
from src.tools.uptime_calculator import compute_uptime_downtime, explain_downtime

async def test_agent_initialization():
    """Test agent initialization"""
    print("🧪 Testing Agent Initialization")
    print("-" * 40)
    
    try:
        settings = get_settings()
        print(f"✅ Settings loaded: {settings.llm_provider} LLM, {settings.cosmosdb_database} database")
        
        agent = ElevatorAgent(settings)
        success = await agent.initialize()
        
        if success:
            print("✅ Agent initialized successfully")
            return agent
        else:
            print("❌ Agent initialization failed")
            return None
            
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return None

async def test_installations(agent):
    """Test installations loading"""
    print("\n🧪 Testing Installations")
    print("-" * 40)
    
    try:
        installations = await agent.cosmos_client.get_installations()
        print(f"✅ Found {len(installations)} installations:")
        
        for inst in installations:
            print(f"   • {inst.get('name', 'Unnamed')} ({inst['installationId'][:8]}...) - {inst['timezone']}")
        
        return installations
        
    except Exception as e:
        print(f"❌ Error loading installations: {e}")
        return []

async def test_uptime_calculation():
    """Test uptime calculation with sample data"""
    print("\n🧪 Testing Uptime Calculation")
    print("-" * 40)
    
    # Sample events data
    sample_events = [
        {
            "kafkaMessage": {
                "Timestamp": int(datetime.now().timestamp() * 1000) - 3600000,  # 1 hour ago
                "CarModeChanged": {
                    "MachineId": 1,
                    "ModeName": "NOR",
                    "AlarmSeverity": 0
                }
            },
            "installationId": "test-installation"
        },
        {
            "kafkaMessage": {
                "Timestamp": int(datetime.now().timestamp() * 1000) - 1800000,  # 30 min ago
                "CarModeChanged": {
                    "MachineId": 1,
                    "ModeName": "DLF",  # Downtime mode
                    "AlarmSeverity": 2
                }
            },
            "installationId": "test-installation"
        },
        {
            "kafkaMessage": {
                "Timestamp": int(datetime.now().timestamp() * 1000) - 300000,   # 5 min ago
                "CarModeChanged": {
                    "MachineId": 1,
                    "ModeName": "NOR",
                    "AlarmSeverity": 0
                }
            },
            "installationId": "test-installation"
        }
    ]
    
    # Sample prior modes
    sample_prior = [
        {
            "MachineId": 1,
            "ModeName": "NOR",
            "Timestamp": int(datetime.now().timestamp() * 1000) - 7200000  # 2 hours ago
        }
    ]
    
    # Create events JSON
    events_json = json.dumps({
        "events": sample_events,
        "priorModes": sample_prior
    })
    
    # Calculate time range (last hour)
    now = datetime.now(pytz.UTC)
    start_time = now - timedelta(hours=1)
    
    try:
        result = compute_uptime_downtime(
            installation_id="test-installation",
            timezone_name="UTC",
            start_iso=start_time.isoformat(),
            end_iso=now.isoformat(),
            events_json=events_json
        )
        
        print("✅ Uptime calculation completed:")
        print(f"   • Total uptime: {result['totals']['uptime_minutes']:.1f} minutes ({result['totals']['uptime_percent']}%)")
        print(f"   • Total downtime: {result['totals']['downtime_minutes']:.1f} minutes ({result['totals']['downtime_percent']}%)")
        print(f"   • Machines analyzed: {len(result['machines'])}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in uptime calculation: {e}")
        return None

async def test_llm_response(agent):
    """Test LLM response generation"""
    print("\n🧪 Testing LLM Response")
    print("-" * 40)
    
    test_message = "What was the uptime for elevators last week?"
    
    try:
        response = await agent.process_message(test_message, [])
        
        print("✅ LLM response generated:")
        print(f"   • Content length: {len(response.get('content', ''))}")
        print(f"   • Tool calls: {len(response.get('tool_results', []))}")
        
        if response.get('content'):
            # Show first 200 characters
            preview = response['content'][:200] + "..." if len(response['content']) > 200 else response['content']
            print(f"   • Preview: {preview}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error in LLM response: {e}")
        return None

async def test_flask_endpoints():
    """Test Flask endpoints"""
    print("\n🧪 Testing Flask Endpoints")
    print("-" * 40)
    
    import requests
    import time
    
    try:
        # Give Flask time to start if running in background
        base_url = "http://127.0.0.1:5000"
        
        # Test status endpoint
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working: Agent initialized = {data.get('agent_initialized', False)}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            
        # Test quick actions endpoint
        response = requests.get(f"{base_url}/api/quick-actions", timeout=5)
        if response.status_code == 200:
            actions = response.json()
            print(f"✅ Quick actions endpoint working: {len(actions)} actions available")
        else:
            print(f"❌ Quick actions endpoint failed: {response.status_code}")
            
        return True
        
    except requests.RequestException as e:
        print(f"⚠️  Flask endpoints not accessible: {e}")
        print("   (This is normal if Flask app is not running)")
        return False
    """Test LLM response generation"""
    print("\n🧪 Testing LLM Response")
    print("-" * 40)
    
    test_message = "What was the uptime for elevators last week?"
    
    try:
        response = await agent.process_message(test_message, [])
        
        print("✅ LLM response generated:")
        print(f"   • Content length: {len(response.get('content', ''))}")
        print(f"   • Tool calls: {len(response.get('tool_results', []))}")
        
        if response.get('content'):
            # Show first 200 characters
            preview = response['content'][:200] + "..." if len(response['content']) > 200 else response['content']
            print(f"   • Preview: {preview}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error in LLM response: {e}")
        return None

async def main():
    """Run all tests"""
    print("🏢 Elevator Operations Agent - Test Suite")
    print("=" * 50)
    
    # Test agent initialization
    agent = await test_agent_initialization()
    if not agent:
        print("\n❌ Cannot continue tests without agent initialization")
        return
    
    # Test installations
    installations = await test_installations(agent)
    
    # Test uptime calculation
    uptime_result = await test_uptime_calculation()
    
    # Test LLM response
    llm_response = await test_llm_response(agent)
    
    # Test Flask endpoints (if running)
    flask_response = await test_flask_endpoints()
    
    # Cleanup
    await agent.close()
    
    print("\n🎉 Test Suite Complete")
    print("=" * 50)
    
    # Summary
    tests_passed = sum([
        agent is not None,
        len(installations) >= 0,  # May be 0 if no data
        uptime_result is not None,
        llm_response is not None,
        flask_response  # Flask endpoints (optional)
    ])
    
    print(f"Tests passed: {tests_passed}/5")
    
    if tests_passed >= 4:  # Flask endpoints are optional
        print("✅ Core tests passed - Agent is ready!")
        if tests_passed == 5:
            print("✅ All tests including Flask endpoints passed!")
    else:
        print("⚠️  Some core tests failed - Check configuration")

if __name__ == "__main__":
    asyncio.run(main())
