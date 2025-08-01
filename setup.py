#!/usr/bin/env python3
"""
Setup script for the Elevator Operations Agent
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment configuration"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        print("📝 Creating .env from .env.example...")
        env_example.rename(env_file)
        print("⚠️  Please edit .env with your actual configuration values")
        return True
    else:
        print("❌ .env.example not found")
        return False

def check_llm_service():
    """Check if local LLM service is available"""
    import requests
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama service detected")
            return True
    except requests.RequestException:
        pass
    
    # Check LM Studio
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ LM Studio service detected")
            return True
    except requests.RequestException:
        pass
    
    print("⚠️  No local LLM service detected. Please start Ollama or LM Studio.")
    return False

def generate_sample_data():
    """Generate sample data for testing"""
    try:
        from src.utils.sample_data import save_test_data
        print("📊 Generating sample test data...")
        save_test_data("sample_data.json", days_back=14)
        print("✅ Sample data generated")
        return True
    except Exception as e:
        print(f"❌ Failed to generate sample data: {e}")
        return False

def main():
    """Main setup function"""
    print("🏢 Elevator Operations Agent Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Check LLM service
    check_llm_service()
    
    # Generate sample data
    generate_sample_data()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env with your Azure Cosmos DB credentials")
    print("2. Ensure Ollama or LM Studio is running")
    print("3. Run: python app.py")
    print("\nFor Ollama setup:")
    print("- Install: curl -fsSL https://ollama.ai/install.sh | sh")
    print("- Pull model: ollama pull llama3.1:8b")
    print("- Start server: ollama serve")
    print("\nFor production deployment:")
    print("- Run: gunicorn -w 4 -b 0.0.0.0:5000 app:app")

if __name__ == "__main__":
    main()
