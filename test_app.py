import os
import sys
import requests
import time
import subprocess
import signal
from threading import Thread

def run_flask_server():
    """Run the Flask app using subprocess in the background."""
    # Set environment variables for testing
    env = os.environ.copy()
    env.update({
        'COSMOSDB_ENDPOINT': 'dummy',
        'COSMOSDB_KEY': 'dummy', 
        'LLM_PROVIDER': 'lmstudio',
        'LMSTUDIO_BASE_URL': 'http://localhost:1234/v1/chat/completions',
        'LMSTUDIO_MODEL': 'dummy',
        'FLASK_HOST': '0.0.0.0',
        'FLASK_PORT': '5001',
        'FLASK_DEBUG': 'false'  # Disable debug mode in tests to avoid reloader
    })
    
    # Start the Flask app using subprocess
    return subprocess.Popen(
        [sys.executable, 'run_app.py'], 
        env=env, 
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def test_chat_endpoint():
    """Test the chat endpoint by starting the Flask app and sending a request."""
    # Start the Flask server
    print("Starting Flask server...")
    server_process = run_flask_server()
    
    # Wait for server to start
    time.sleep(8)  # Give it a bit more time to start
    
    try:
        # Send a request to the chat endpoint
        print("Sending request to chat endpoint...")
        response = requests.post(
            "http://localhost:5001/api/chat",
            json={
                "message": "What was the uptime last week?",
                "installationId": "demo-installation-1"
            },
            timeout=30
        )
        
        # Print the response
        print("Response status code:", response.status_code)
        print("Response headers:", dict(response.headers))
        print("Response text:", response.text)
        
        # Only try to parse JSON if response is successful and has content
        if response.status_code == 200 and response.text.strip():
            try:
                print("Response JSON:", response.json())
            except ValueError as json_error:
                print(f"Failed to parse JSON: {json_error}")
        else:
            print("Non-200 response or empty body, skipping JSON parsing")
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    finally:
        # Terminate the server process
        print("Stopping Flask server...")
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    test_chat_endpoint()
