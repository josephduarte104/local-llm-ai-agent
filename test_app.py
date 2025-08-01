#!/usr/bin/env python3
"""
Test script for the Elevator Operations Agent Flask Application
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found. Please copy .env.example to .env and configure your settings.")
        return False
    
    with open(env_file) as f:
        env_content = f.read()
    
    required_vars = [
        'COSMOS_ENDPOINT',
        'COSMOS_KEY', 
        'COSMOS_DATABASE_NAME',
        'COSMOS_CONTAINER_NAME',
        'LLM_MODEL_NAME',
        'FLASK_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in env_content or f'{var}=' in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or empty environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment file configured")
    return True

def generate_sample_data():
    """Generate sample data for testing"""
    print("🔧 Generating sample data...")
    
    try:
        from src.utils.sample_data import save_test_data
        save_test_data("test_data.json", days_back=7)
        print("✅ Sample data generated")
        return True
    except Exception as e:
        print(f"❌ Failed to generate sample data: {e}")
        return False

def test_cosmos_connection():
    """Test Cosmos DB connection"""
    print("🔧 Testing Cosmos DB connection...")
    
    try:
        from src.config.settings import Settings
        from src.database.cosmos_client import CosmosDBClient
        
        settings = Settings()
        client = CosmosDBClient(settings)
        
        # Test connection by trying to list containers
        database = client.client.get_database_client(settings.COSMOS_DATABASE_NAME)
        containers = list(database.list_containers())
        
        print(f"✅ Connected to Cosmos DB - found {len(containers)} containers")
        return True
    except Exception as e:
        print(f"❌ Cosmos DB connection failed: {e}")
        print("   This is expected if you haven't configured Cosmos DB yet")
        return False

def test_llm_connection():
    """Test LLM connection"""
    print("🔧 Testing LLM connection...")
    
    try:
        from src.config.settings import Settings
        from src.llm.client import LLMClient
        
        settings = Settings()
        llm_client = LLMClient(settings)
        
        # Test with a simple query
        response = llm_client.query("Test connection - respond with 'OK'")
        
        if response and "ok" in response.lower():
            print("✅ LLM connection successful")
            return True
        else:
            print(f"⚠️  LLM responded but unexpected response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ LLM connection failed: {e}")
        print("   Make sure your local LLM server (Ollama/LM Studio) is running")
        return False

def test_agent_initialization():
    """Test agent initialization"""
    print("🔧 Testing agent initialization...")
    
    try:
        from src.agent.elevator_agent import ElevatorOperationsAgent
        from src.config.settings import Settings
        
        settings = Settings()
        agent = ElevatorOperationsAgent(settings)
        
        print("✅ Agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

def test_flask_app():
    """Test Flask application startup"""
    print("🔧 Testing Flask application...")
    
    try:
        # Import the Flask app to test initialization
        from app import app, socketio
        
        # Test app creation
        if app and socketio:
            print("✅ Flask application initialized successfully")
            return True
        else:
            print("❌ Flask application initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Flask application test failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("🚀 Testing Elevator Operations Agent")
    print("=" * 50)
    
    tests = [
        ("Environment Configuration", check_env_file),
        ("Sample Data Generation", generate_sample_data),
        ("Agent Initialization", test_agent_initialization),
        ("Flask Application", test_flask_app),
        ("Cosmos DB Connection", test_cosmos_connection),
        ("LLM Connection", test_llm_connection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        results[test_name] = test_func()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! You can now run the application:")
        print("   python app.py")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration:")
        print("   1. Copy .env.example to .env and configure settings")
        print("   2. Start your local LLM server (Ollama/LM Studio)")
        print("   3. Configure Cosmos DB credentials (optional for demo)")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Elevator Operations Agent")
    parser.add_argument("--install", action="store_true", help="Install dependencies first")
    parser.add_argument("--run", action="store_true", help="Run the Flask app after tests")
    
    args = parser.parse_args()
    
    if args.install:
        if not install_dependencies():
            sys.exit(1)
    
    # Run tests
    run_tests()
    
    if args.run:
        print("\n🚀 Starting Flask application...")
        try:
            subprocess.run([sys.executable, "app.py"])
        except KeyboardInterrupt:
            print("\n👋 Application stopped")
