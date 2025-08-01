"""
Sample data generator for testing the Elevator Operations Agent
"""

import json
import random
from datetime import datetime, timedelta
import pytz

# Sample installations
SAMPLE_INSTALLATIONS = {
    "id": "installations-list",
    "installations": [
        {
            "installationId": "4995d395-b8c7-4e4a-9f2b-1a2b3c4d5e6c",
            "timezone": "America/New_York",
            "name": "Corporate Tower NYC"
        },
        {
            "installationId": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
            "timezone": "Europe/London",
            "name": "London Office Complex"
        },
        {
            "installationId": "xyz789ab-cdef-1234-5678-9abcdefghijk",
            "timezone": "Asia/Tokyo",
            "name": "Tokyo Business Center"
        }
    ]
}

# Mode codes and their frequencies
UPTIME_MODES = [
    ("NOR", 0.7),  # Normal operation - most common
    ("IDL", 0.15), # Idle
    ("PRK", 0.05), # Parking
    ("INS", 0.03), # Inspection
    ("ATT", 0.02), # Attendant mode
    ("EFS", 0.02), # Emergency fireman service
    ("CTL", 0.015), # Car to landing
    ("REC", 0.01),  # Recover operation
    ("STP", 0.005)  # Car stall protection
]

DOWNTIME_MODES = [
    ("DLF", 0.4),  # Door lock failure - most common downtime
    ("ESB", 0.3),  # Emergency stop button
    ("COR", 0.15), # Correction
    ("NAV", 0.1),  # Not available
    ("DBF", 0.03), # Drive brake fault
    ("HAD", 0.02)  # Hoistway access detection
]

def generate_mode_events(installation_id, machine_id, start_time, end_time, uptime_ratio=0.95):
    """
    Generate realistic CarModeChanged events for testing
    
    Args:
        installation_id: Installation ID
        machine_id: Machine ID (1, 2, 3, etc.)
        start_time: Start timestamp (datetime)
        end_time: End timestamp (datetime)
        uptime_ratio: Ratio of uptime vs downtime (0.95 = 95% uptime)
    
    Returns:
        List of event documents
    """
    events = []
    current_time = start_time
    current_mode = "NOR"  # Start in normal mode
    
    while current_time < end_time:
        # Determine how long to stay in current mode
        if current_mode in [mode[0] for mode in UPTIME_MODES]:
            # Uptime mode - stay longer (30 min to 4 hours)
            duration_minutes = random.uniform(30, 240)
        else:
            # Downtime mode - shorter duration (1 min to 30 min)
            duration_minutes = random.uniform(1, 30)
        
        # Add some randomness
        duration_minutes *= random.uniform(0.5, 1.5)
        
        # Calculate next event time
        next_time = current_time + timedelta(minutes=duration_minutes)
        
        if next_time > end_time:
            break
        
        # Choose next mode based on current state and uptime ratio
        if random.random() < uptime_ratio:
            # Choose uptime mode
            modes_weights = UPTIME_MODES
        else:
            # Choose downtime mode
            modes_weights = DOWNTIME_MODES
        
        # Weighted random selection
        total_weight = sum(weight for _, weight in modes_weights)
        r = random.uniform(0, total_weight)
        cumulative = 0
        
        for mode, weight in modes_weights:
            cumulative += weight
            if r <= cumulative:
                current_mode = mode
                break
        
        # Create event document
        event = {
            "kafkaMessage": {
                "Timestamp": int(next_time.timestamp() * 1000),
                "GroupId": 1,
                "Transaction": random.randint(30000, 40000),
                "EventCase": "CarModeChanged",
                "CarModeChanged": {
                    "MachineId": machine_id,
                    "ModeName": current_mode,
                    "CarMode": random.randint(100, 200),
                    "AlarmSeverity": random.randint(0, 3) if current_mode in [mode[0] for mode in DOWNTIME_MODES] else 0
                }
            },
            "pk": f"{installation_id}-{machine_id}",
            "id": f"{installation_id}-{machine_id}-{int(next_time.timestamp())}",
            "installationId": installation_id,
            "dataType": "CarModeChanged",
            "kafkaOffset": random.randint(3000000, 4000000),
            "_ts": int(next_time.timestamp())
        }
        
        events.append(event)
        current_time = next_time
    
    return events

def generate_test_data(days_back=7):
    """
    Generate test data for the last N days
    
    Args:
        days_back: Number of days of data to generate
        
    Returns:
        Dict with installations and events
    """
    data = {
        "installations": SAMPLE_INSTALLATIONS,
        "events": []
    }
    
    # Generate events for each installation
    for installation in SAMPLE_INSTALLATIONS["installations"]:
        installation_id = installation["installationId"]
        timezone_name = installation["timezone"]
        
        # Get timezone
        tz = pytz.timezone(timezone_name)
        
        # Calculate time range
        end_time = datetime.now(tz).replace(hour=23, minute=59, second=59, microsecond=0)
        start_time = end_time - timedelta(days=days_back)
        
        # Generate events for 3 machines per installation
        for machine_id in [1, 2, 3]:
            # Vary uptime ratio per machine (some have more issues)
            if machine_id == 1:
                uptime_ratio = 0.98  # Very reliable
            elif machine_id == 2:
                uptime_ratio = 0.95  # Normal
            else:
                uptime_ratio = 0.90  # More issues
            
            machine_events = generate_mode_events(
                installation_id, 
                machine_id, 
                start_time, 
                end_time, 
                uptime_ratio
            )
            
            data["events"].extend(machine_events)
    
    return data

def save_test_data(filename="sample_data.json", days_back=7):
    """Save generated test data to JSON file"""
    data = generate_test_data(days_back)
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"Generated {len(data['events'])} events for {len(data['installations']['installations'])} installations")
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    # Generate and save sample data
    save_test_data("sample_data.json", days_back=14)
