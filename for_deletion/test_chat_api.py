import requests
import json
from datetime import datetime

# Define the API endpoint
url = "http://127.0.0.1:5001/api/chat"

# Define the request payload
payload = {
    "message": "can you analyze uptime and downtime for elevators in installation 4995d395-9b4b-4234-a8aa-9938ef5620c6 for dates 7-31-2025 - 8/6/2025. remember today is 8/7/2025 and the dates are not in the future.",
    "installationId": "4995d395-9b4b-4234-a8aa-9938ef5620c6",
    "startISO": "2025-07-31",
    "endISO": "2025-08-06",
    "today_override": "2025-08-07T12:00:00"
}

# Send the POST request
try:
    response = requests.post(url, json=payload)
    response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

    # Print the response
    print(json.dumps(response.json(), indent=2))

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

