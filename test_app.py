import os
import requests
import time
from multiprocessing import Process
from elevator_ai_agent.app import app

def run_app():
    # Disable werkzeug reloader for testing
    # Set host to 0.0.0.0 to be accessible from outside the container
    app.run(use_reloader=False, port=5000, host='0.0.0.0')

def test_chat_endpoint():
    # Set dummy environment variables for testing
    os.environ['COSMOS_ENDPOINT'] = 'dummy'
    os.environ['COSMOS_KEY'] = 'dummy'
    os.environ['LLM_API_URL'] = 'http://localhost:1234/v1'
    os.environ['LLM_MODEL'] = 'dummy'

    # Start the server in a separate process
    server_process = Process(target=run_app)
    server_process.daemon = True
    server_process.start()
    time.sleep(5)  # Wait for server to start

    # Send a request to the chat endpoint
    print("Sending request to chat endpoint...")
    try:
        response = requests.post(
            "http://localhost:5000/api/chat",
            json={
                "message": "What was the uptime last week?",
                "installationId": "demo-installation-1"
            },
            timeout=30
        )
        # Print the response
        print("Response status code:", response.status_code)
        print("Response JSON:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    finally:
        # Terminate the server process
        server_process.terminate()
        server_process.join()


if __name__ == "__main__":
    test_chat_endpoint()
