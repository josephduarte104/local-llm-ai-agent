"""
Azure Cosmos DB client for elevator event data
Handles all database operations with memory-efficient patterns
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
import pytz
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError

class CosmosDBClient:
    """
    Memory-efficient Cosmos DB client for elevator event data
    """
    
    def __init__(self, endpoint: str, key: str, database_name: str, container_name: str):
        """Initialize Cosmos DB client"""
        self.endpoint = endpoint
        self.key = key
        self.database_name = database_name
        self.container_name = container_name
        
        self.client = None
        self.database = None
        self.container = None
        self.installations = []
        
    def initialize_sync(self) -> bool:
        """
        Initialize the Cosmos DB connection and load installations (synchronous)
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize client
            self.client = CosmosClient(self.endpoint, self.key)
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.container_name)
            
            # Load installations synchronously
            self._load_installations_sync()
            return True
            
        except Exception as e:
            print(f"Failed to initialize Cosmos DB: {e}")
            return False
        
    async def initialize(self) -> bool:
        """
        Initialize the Cosmos DB connection and load installations
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Initialize client
            self.client = CosmosClient(self.endpoint, self.key)
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.container_name)
            
            # Load installations
            await self._load_installations()
            return True
            
        except Exception as e:
            print(f"Failed to initialize Cosmos DB: {e}")
            return False
    
    def _load_installations_sync(self):
        """Load installations metadata (synchronous)"""
        try:
            # Read installations document with correct ID
            response = self.container.read_item(
                item="installation-list",
                partition_key="installation-list"
            )
            
            # Parse installations - handle both array and object formats
            if "installations" in response:
                self.installations = response["installations"]
            elif isinstance(response.get("installation"), list):
                self.installations = response["installation"]
            else:
                # Parse key-value pairs into installation objects
                installations = []
                for key, value in response.items():
                    if key not in ["id", "_rid", "_self", "_etag", "_attachments", "_ts"]:
                        if isinstance(value, dict) and "timezone" in value:
                            installations.append({
                                "installationId": key,
                                "timezone": value["timezone"],
                                "name": value.get("name", key)
                            })
                        elif isinstance(value, str):
                            # Assume value is timezone
                            installations.append({
                                "installationId": key,
                                "timezone": value,
                                "name": key
                            })
                self.installations = installations
            
            print(f"✅ Loaded {len(self.installations)} installations")
            
        except CosmosResourceNotFoundError:
            print("Installation document not found. Creating empty list.")
            self.installations = []
        except Exception as e:
            print(f"Error loading installations: {e}")
            self.installations = []
    
    async def _load_installations(self):
        """Load installations metadata"""
        try:
            # Read installations document with correct ID
            response = self.container.read_item(
                item="installation-list",
                partition_key="installation-list"
            )
            
            # Parse installations - handle both array and object formats
            if "installations" in response:
                self.installations = response["installations"]
            elif isinstance(response.get("installation"), list):
                self.installations = response["installation"]
            else:
                # Parse key-value pairs into installation objects
                installations = []
                for key, value in response.items():
                    if key not in ["id", "_rid", "_self", "_etag", "_attachments", "_ts"]:
                        if isinstance(value, dict) and "timezone" in value:
                            installations.append({
                                "installationId": key,
                                "timezone": value["timezone"],
                                "name": value.get("name", key)
                            })
                        elif isinstance(value, str):
                            # Assume value is timezone
                            installations.append({
                                "installationId": key,
                                "timezone": value,
                                "name": key
                            })
                self.installations = installations
            
            print(f"✅ Loaded {len(self.installations)} installations")
            
        except CosmosResourceNotFoundError:
            print("Installation document not found. Creating empty list.")
            self.installations = []
        except Exception as e:
            print(f"Error loading installations: {e}")
            self.installations = []
    
    def get_installation_by_id(self, installation_id: str) -> Optional[Dict]:
        """Get installation metadata by ID"""
        for inst in self.installations:
            if inst.get("installationId") == installation_id:
                return inst
        return None
    
    def get_installation_timezone(self, installation_id: str) -> str:
        """Get timezone for installation, default to UTC"""
        inst = self.get_installation_by_id(installation_id)
        return inst.get("timezone", "UTC") if inst else "UTC"
    
    def _convert_iso_to_timestamp(self, iso_string: str, timezone_name: str) -> int:
        """
        Convert ISO string to Unix timestamp in milliseconds
        
        Args:
            iso_string: ISO format datetime string
            timezone_name: IANA timezone name
            
        Returns:
            int: Unix timestamp in milliseconds
        """
        try:
            # Parse the ISO string
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            
            # If timezone is naive, localize it
            if dt.tzinfo is None:
                tz = pytz.timezone(timezone_name)
                dt = tz.localize(dt)
            
            # Convert to UTC and then to timestamp
            utc_dt = dt.astimezone(pytz.UTC)
            return int(utc_dt.timestamp() * 1000)
            
        except Exception as e:
            print(f"Error converting time: {e}")
            return 0
    
    async def query_events(
        self,
        installation_id: str,
        data_type: str,
        start_iso: str,
        end_iso: str,
        machine_ids: Optional[List[int]] = None,
        page_size: int = 5000,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query events with pagination and memory efficiency
        
        Args:
            installation_id: Installation ID to filter by
            data_type: Event data type (e.g., "CarModeChanged")
            start_iso: Start time in ISO format (in installation timezone)
            end_iso: End time in ISO format (in installation timezone)
            machine_ids: Optional list of machine IDs to filter
            page_size: Maximum number of events to return
            continuation_token: Token for pagination
            
        Returns:
            Dict containing events and continuation token
        """
        try:
            # Get timezone for this installation
            timezone_name = self.get_installation_timezone(installation_id)
            
            # Convert ISO times to timestamps
            start_ms = self._convert_iso_to_timestamp(start_iso, timezone_name)
            end_ms = self._convert_iso_to_timestamp(end_iso, timezone_name)
            
            # Build query
            query = """
                SELECT c.kafkaMessage.Timestamp, 
                       c.kafkaMessage.CarModeChanged.MachineId,
                       c.kafkaMessage.CarModeChanged.ModeName,
                       c.kafkaMessage.CarModeChanged.AlarmSeverity,
                       c.installationId
                FROM c
                WHERE c.installationId = @installationId
                  AND c.dataType = @dataType
                  AND c.kafkaMessage.Timestamp >= @startMs
                  AND c.kafkaMessage.Timestamp <= @endMs
            """
            
            parameters = [
                {"name": "@installationId", "value": installation_id},
                {"name": "@dataType", "value": data_type},
                {"name": "@startMs", "value": start_ms},
                {"name": "@endMs", "value": end_ms}
            ]
            
            # Add machine ID filter if provided
            if machine_ids:
                machine_filter = " AND c.kafkaMessage.CarModeChanged.MachineId IN ({})".format(
                    ",".join(str(mid) for mid in machine_ids)
                )
                query += machine_filter
            
            query += " ORDER BY c.kafkaMessage.Timestamp ASC"
            
            # Execute query with pagination
            options = {
                "max_item_count": page_size,
                "enable_cross_partition_query": True
            }
            
            if continuation_token:
                options["continuation_token"] = continuation_token
            
            query_result = self.container.query_items(
                query=query,
                parameters=parameters,
                **options
            )
            
            # Collect results efficiently
            events = []
            result_continuation = None
            
            for item in query_result:
                events.append({
                    "kafkaMessage": {
                        "Timestamp": item.get("Timestamp"),
                        "CarModeChanged": {
                            "MachineId": item.get("MachineId"),
                            "ModeName": item.get("ModeName"),
                            "AlarmSeverity": item.get("AlarmSeverity", 0)
                        }
                    },
                    "installationId": item.get("installationId")
                })
            
            # Get continuation token for next page
            response_headers = query_result.response_headers
            result_continuation = response_headers.get("x-ms-continuation")
            
            return {
                "events": events,
                "continuationToken": result_continuation
            }
            
        except Exception as e:
            print(f"Error querying events: {e}")
            return {"events": [], "continuationToken": None}
    
    async def get_prior_mode(
        self,
        installation_id: str,
        start_iso: str,
        machine_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get the last CarModeChanged event before the start time for each machine
        
        Args:
            installation_id: Installation ID
            start_iso: Start time in ISO format
            machine_ids: Optional list of machine IDs
            
        Returns:
            Dict with prior modes per machine
        """
        try:
            timezone_name = self.get_installation_timezone(installation_id)
            start_ms = self._convert_iso_to_timestamp(start_iso, timezone_name)
            
            # Query for events before start time
            query = """
                SELECT c.kafkaMessage.Timestamp,
                       c.kafkaMessage.CarModeChanged.MachineId,
                       c.kafkaMessage.CarModeChanged.ModeName
                FROM c
                WHERE c.installationId = @installationId
                  AND c.dataType = "CarModeChanged"
                  AND c.kafkaMessage.Timestamp < @startMs
                ORDER BY c.kafkaMessage.Timestamp DESC
            """
            
            parameters = [
                {"name": "@installationId", "value": installation_id},
                {"name": "@startMs", "value": start_ms}
            ]
            
            if machine_ids:
                machine_filter = " AND c.kafkaMessage.CarModeChanged.MachineId IN ({})".format(
                    ",".join(str(mid) for mid in machine_ids)
                )
                query = query.replace("ORDER BY", machine_filter + " ORDER BY")
            
            # Execute query
            result = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )
            
            # Get the most recent event per machine
            prior_modes = {}
            for item in result:
                machine_id = item.get("MachineId")
                if machine_id not in prior_modes:
                    prior_modes[machine_id] = {
                        "MachineId": machine_id,
                        "ModeName": item.get("ModeName"),
                        "Timestamp": item.get("Timestamp")
                    }
            
            return {"priorModes": list(prior_modes.values())}
            
        except Exception as e:
            print(f"Error getting prior modes: {e}")
            return {"priorModes": []}
    
    def get_installations_sync(self) -> List[Dict]:
        """Get all installations (synchronous)"""
        return self.installations
    
    async def get_installations(self) -> List[Dict]:
        """Get all installations"""
        return self.installations
    
    def close(self):
        """Close the client connection"""
        if self.client:
            self.client = None
