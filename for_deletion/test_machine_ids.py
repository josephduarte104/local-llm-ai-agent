#!/usr/bin/env python3
"""Test script to find all machine IDs for installation 4995d395-9b4b-4234-a8aa-9938ef5620c6"""

import os
import sys
from datetime import datetime, timezone

# Add the elevator_ai_agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'elevator_ai_agent'))

from services.cosmos import get_cosmos_service
from services.timezone import timezone_service


def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('elevator_ai_agent/.env')
    
    installation_id = "4995d395-9b4b-4234-a8aa-9938ef5620c6"
    
    # Get installation timezone
    cosmos = get_cosmos_service()
    installations = cosmos.get_installations()
    
    installation_tz = None
    for inst in installations:
        if inst['installationId'] == installation_id:
            installation_tz = inst['timezone']
            break
    
    if not installation_tz:
        print(f"Installation {installation_id} not found")
        return
    
    print(f"Installation timezone: {installation_tz}")
    
    # Convert time range to timestamps  
    start_time = timezone_service.parse_iso_with_timezone("2025-08-01T00:00:00", installation_tz)
    end_time = timezone_service.parse_iso_with_timezone("2025-08-02T23:59:59", installation_tz)
    
    start_ts = timezone_service.local_datetime_to_epoch(start_time)
    end_ts = timezone_service.local_datetime_to_epoch(end_time)
    
    print(f"Time range: {start_time} to {end_time}")
    print(f"Timestamp range: {start_ts} to {end_ts}")
    
    # Query distinct machine IDs
    distinct_query = """
        SELECT DISTINCT c.kafkaMessage.CarModeChanged.MachineId
        FROM c
        WHERE c.installationId = @installationId
          AND c.dataType = "CarModeChanged"
          AND c.kafkaMessage.Timestamp >= @startTs 
          AND c.kafkaMessage.Timestamp <= @endTs
    """
    
    parameters = [
        {"name": "@installationId", "value": installation_id},
        {"name": "@startTs", "value": start_ts},
        {"name": "@endTs", "value": end_ts}
    ]
    
    print("\nQuerying distinct machine IDs...")
    distinct_items = list(cosmos.container.query_items(
        query=distinct_query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    
    print(f"Found {len(distinct_items)} distinct machine IDs:")
    for item in distinct_items:
        machine_id = item.get('MachineId')
        print(f"  Machine ID: {machine_id}")
    
    # Also query all events to see the actual data
    print("\nQuerying all CarModeChanged events...")
    all_events = list(cosmos.get_car_mode_changes(installation_id, start_ts, end_ts))
    
    machine_counts = {}
    for event in all_events:
        if 'MachineId' in event:
            mid = str(event['MachineId'])
        else:
            mid = str(event['kafkaMessage']['CarModeChanged']['MachineId'])
        
        machine_counts[mid] = machine_counts.get(mid, 0) + 1
    
    print(f"Found {len(all_events)} total events")
    print("Event counts by machine ID:")
    for mid, count in sorted(machine_counts.items()):
        print(f"  Machine {mid}: {count} events")


if __name__ == "__main__":
    main()
