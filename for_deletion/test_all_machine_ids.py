#!/usr/bin/env python3
"""Extended test script to find all machine IDs for installation across a wider time range"""

import os
import sys
from datetime import datetime, timezone

# Add the elevator_ai_agent directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'elevator_ai_agent'))

from services.cosmos import get_cosmos_service


def main():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('elevator_ai_agent/.env')
    
    installation_id = "4995d395-9b4b-4234-a8aa-9938ef5620c6"
    
    cosmos = get_cosmos_service()
    
    print(f"Searching for all machine IDs in installation {installation_id}")
    print("Checking across ALL time periods...\n")
    
    # Query all distinct machine IDs for this installation (no time filter)
    distinct_query = """
        SELECT DISTINCT c.kafkaMessage.CarModeChanged.MachineId
        FROM c
        WHERE c.installationId = @installationId
          AND c.dataType = "CarModeChanged"
    """
    
    parameters = [
        {"name": "@installationId", "value": installation_id}
    ]
    
    print("Querying all machine IDs across all time periods...")
    distinct_items = list(cosmos.container.query_items(
        query=distinct_query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))
    
    print(f"Found {len(distinct_items)} machine IDs for this installation:")
    for item in distinct_items:
        machine_id = item.get('MachineId')
        print(f"  Machine ID: {machine_id}")
        print()


if __name__ == "__main__":
    main()
