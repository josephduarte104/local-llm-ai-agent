#!/usr/bin/env python3
"""
Entry point script for the Elevator Operations Agent Flask application.
This script properly handles the package imports and runs the Flask app.
"""

import sys
import os
from dotenv import load_dotenv

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables from .env file
load_dotenv()

def main():
    """Main entry point for the Flask application."""
    # Import the Flask app from the package
    from elevator_ai_agent.app import app
    
    # Get configuration from environment or use defaults
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    print(f"Starting Elevator Operations Agent on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    # Print Cosmos DB configuration for debugging
    cosmos_endpoint = os.environ.get('COSMOSDB_ENDPOINT', 'Not set')
    cosmos_database = os.environ.get('COSMOSDB_DATABASE', 'Not set')
    print(f"Cosmos DB Endpoint: {cosmos_endpoint}")
    print(f"Cosmos DB Database: {cosmos_database}")
    
    # Print LLM configuration for debugging
    llm_provider = os.environ.get('LLM_PROVIDER', 'Not set')
    if llm_provider.lower() == 'lmstudio':
        llm_url = os.environ.get('LMSTUDIO_BASE_URL', 'Not set')
        llm_model = os.environ.get('LMSTUDIO_MODEL', 'Not set')
    elif llm_provider.lower() == 'ollama':
        llm_url = os.environ.get('OLLAMA_BASE_URL', 'Not set')
        llm_model = os.environ.get('OLLAMA_MODEL', 'Not set')
    else:
        llm_url = os.environ.get('LLM_API_URL', 'Not set')
        llm_model = os.environ.get('LLM_MODEL', 'Not set')
    
    print(f"LLM Provider: {llm_provider}")
    print(f"LLM URL: {llm_url}")
    print(f"LLM Model: {llm_model}")
    
    # Run the Flask application
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
