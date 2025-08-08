"""Cosmos DB service for elevator events data."""

import os
import logging
import time
from typing import Iterator, List, Dict, Any, Optional
from functools import lru_cache
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

logger = logging.getLogger(__name__)


class CosmosService:
    """Service for interacting with Azure Cosmos DB."""
    
    def __init__(self):
        """Initialize Cosmos DB client with configuration from environment."""
        self.uri = os.getenv('COSMOSDB_ENDPOINT')
        self.key = os.getenv('COSMOSDB_KEY')
        self.database_name = os.getenv('COSMOSDB_DATABASE', 'bmsdb')
        self.container_name = os.getenv('COSMOSDB_CONTAINER', 'elevatorevents')
        
        if not self.uri or not self.key:
            raise ValueError("COSMOSDB_ENDPOINT and COSMOSDB_KEY must be set in environment")
        
        self.client = CosmosClient(self.uri, self.key)
        self.database = self.client.get_database_client(self.database_name)
        self.container = self.database.get_container_client(self.container_name)
        
        # Cache for frequently accessed data
        self._machine_ids_cache = {}
        self._cache_ttl = 300  # 5 minutes TTL
    
    @lru_cache(maxsize=128)
    def get_installations(self) -> List[Dict[str, str]]:
        """
        Get list of installations with their timezones (cached).
        
        Returns:
            List of {installationId, timezone} dictionaries
        """
        try:
            query = "SELECT c.installations FROM c WHERE c.id = 'installation-list'"
            # Use point lookup instead of cross-partition query when possible
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True,  # Keep for now, optimize later with partition key
                max_item_count=1
            ))
            
            if items and 'installations' in items[0]:
                raw_installations = items[0]['installations']
                # Transform data format to match frontend expectations
                return [
                    {
                        'installationId': inst.get('id', ''),
                        'timezone': inst.get('tz', 'UTC')
                    }
                    for inst in raw_installations
                ]
            else:
                logger.warning("No installation-list document found")
                return []
                
        except CosmosResourceNotFoundError:
            logger.error("Installation list not found")
            return []
        except Exception as e:
            logger.error(f"Error fetching installations: {e}")
            return []
    
    def query_events(
        self,
        installation_id: str,
        data_type: str,
        start_ts: int,
        end_ts: int,
        machine_id: Optional[str] = None,
        max_items: int = 1000
    ) -> Iterator[Dict[str, Any]]:
        """
        Query events for a specific installation and data type within time range.
        
        Args:
            installation_id: The installation to query
            data_type: The event data type (e.g., "CarModeChanged")
            start_ts: Start timestamp (epoch milliseconds)
            end_ts: End timestamp (epoch milliseconds)
            machine_id: Optional machine ID filter
            max_items: Maximum items per page
            
        Yields:
            Event documents
        """
        try:
            # Optimized query with specific field selection to reduce data transfer
            query_text = (
                "SELECT c.kafkaMessage.Timestamp, c.kafkaMessage.EventCase, c.kafkaMessage[@dataType] AS EventDetails "
                "FROM c "
                "WHERE c.installationId = @installationId "
                "AND c.dataType = @dataType "
                "AND c.kafkaMessage.Timestamp >= @startTs "
                "AND c.kafkaMessage.Timestamp <= @endTs "
                "AND IS_DEFINED(c.kafkaMessage[@dataType])"
            )
            
            parameters = [
                {"name": "@installationId", "value": installation_id},
                {"name": "@dataType", "value": data_type},
                {"name": "@startTs", "value": start_ts},
                {"name": "@endTs", "value": end_ts},
            ]

            if machine_id:
                query_text += " AND c.kafkaMessage[@dataType].MachineId = @machineId"
                parameters.append({"name": "@machineId", "value": machine_id})

            logger.info(f"Executing query: {query_text} with params: {parameters}")

            query_iterator = self.container.query_items(
                query=query_text,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=max_items,
            )
            
            for item in query_iterator:
                # The result is now nested under 'EventDetails', so we need to un-nest it
                # to match the structure expected by the tools.
                event_details = item.pop('EventDetails', {})
                item[data_type] = event_details
                yield item
                    
        except Exception as e:
            logger.error(f"Error querying events: {e}", exc_info=True)
            raise
    
    def get_car_mode_changes(
        self,
        installation_id: str,
        start_ts: int,
        end_ts: int,
        machine_id: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Get CarModeChanged events for uptime/downtime analysis.
        
        Args:
            installation_id: The installation to query
            start_ts: Start timestamp (epoch milliseconds)
            end_ts: End timestamp (epoch milliseconds)
            machine_id: Optional machine ID filter
            
        Yields:
            CarModeChanged event documents
        """
        try:
            # First, let's examine the actual data structure
            explore_query = """
                SELECT TOP 2 c.installationId, c.dataType, c.kafkaMessage
                FROM c 
                WHERE c.installationId = @installationId
                  AND c.dataType = "CarModeChanged"
            """
            
            explore_params: List[Dict[str, Any]] = [{"name": "@installationId", "value": installation_id}]
            
            logger.info(f"Exploring data structure for installation: {installation_id}")
            
            try:
                explore_items = list(self.container.query_items(
                    query=explore_query,
                    parameters=explore_params,
                    enable_cross_partition_query=True,
                    max_item_count=2
                ))
                logger.info(f"Data exploration returned {len(explore_items)} items")
                if explore_items:
                    first_item = explore_items[0]
                    kafka_msg = first_item.get('kafkaMessage', {})
                    logger.info(f"Sample kafka message keys: {list(kafka_msg.keys())}")
                    logger.info(f"Full sample item: {first_item}")
            except Exception as explore_e:
                logger.error(f"Data exploration failed: {explore_e}")
                raise
            
            # Optimized query with better field selection and index-friendly WHERE order
            query = """
                SELECT 
                    c.kafkaMessage.Timestamp as Timestamp,
                    c.kafkaMessage.CarModeChanged.MachineId as MachineId,
                    c.kafkaMessage.CarModeChanged.ModeName as ModeName,
                    c.kafkaMessage.CarModeChanged.CarMode as CarMode,
                    c.kafkaMessage.CarModeChanged.AlarmSeverity as AlarmSeverity
                FROM c
                WHERE c.installationId = @installationId
                  AND c.dataType = @dataType
                  AND c.kafkaMessage.Timestamp >= @startTs 
                  AND c.kafkaMessage.Timestamp <= @endTs
                  AND IS_DEFINED(c.kafkaMessage.CarModeChanged.MachineId)
            """
            
            parameters: List[Dict[str, Any]] = [
                {"name": "@installationId", "value": installation_id},
                {"name": "@dataType", "value": "CarModeChanged"},
                {"name": "@startTs", "value": start_ts},
                {"name": "@endTs", "value": end_ts}
            ]
            
            # Debug logging
            logger.info(f"Cosmos query - Installation: {installation_id}, Start: {start_ts}, End: {end_ts}")
            logger.info(f"Query: {query.strip()}")
            logger.info(f"Parameters: {parameters}")
            
            if machine_id:
                query += " AND c.kafkaMessage.CarModeChanged.MachineId = @machineId"
                parameters.append({"name": "@machineId", "value": machine_id})
            
            # Don't use ORDER BY to avoid composite index requirement
            # We'll sort the results in Python instead
            
            query_iterator = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )
            
            for item in query_iterator:
                yield item
                
        except Exception as e:
            logger.error(f"Error querying car mode changes: {e}")
            raise

    def get_all_machine_ids(self, installation_id: str, data_type: str = "CarModeChanged") -> List[str]:
        """
        Get all machine IDs that exist for an installation for a specific data type (with caching).
        
        Args:
            installation_id: The installation to query
            data_type: The event data type (e.g., "CarModeChanged", "Door")
            
        Returns:
            List of machine IDs as strings
        """
        # Check cache first
        cache_key = f"{installation_id}:{data_type}"
        current_time = time.time()
        
        if cache_key in self._machine_ids_cache:
            cached_data, cache_time = self._machine_ids_cache[cache_key]
            if current_time - cache_time < self._cache_ttl:
                logger.info(f"Using cached machine IDs for {installation_id}:{data_type}")
                return cached_data
        
        try:
            # Construct the field name dynamically
            machine_id_field = f"c.kafkaMessage.{data_type}.MachineId"

            # Optimized query with limited result set
            query = f"""
                SELECT DISTINCT VALUE {machine_id_field}
                FROM c
                WHERE c.installationId = @installationId
                  AND c.dataType = @dataType
                  AND IS_DEFINED({machine_id_field})
            """
            
            parameters = [
                {"name": "@installationId", "value": installation_id},
                {"name": "@dataType", "value": data_type}
            ]
            
            logger.info(f"Fetching machine IDs for installation: {installation_id} and data type: {data_type}")
            
            query_iterator = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=100  # Machine IDs should be a small set
            )
            
            machine_ids = [str(item) for item in query_iterator if item is not None]
            
            # Remove duplicates and sort
            unique_machine_ids = sorted(list(set(machine_ids)))
            
            # Cache the result
            self._machine_ids_cache[cache_key] = (unique_machine_ids, current_time)
            
            logger.info(f"Found and cached {len(unique_machine_ids)} machine IDs")
            return unique_machine_ids
                
        except Exception as e:
            logger.error(f"Error getting machine IDs for installation {installation_id}: {e}")
            return []


    def get_door_events(
        self,
        installation_id: str,
        start_ts: int,
        end_ts: int
    ) -> Iterator[Dict[str, Any]]:
        """
        Get Door events for door cycle analysis.
        
        Args:
            installation_id: The installation to query
            start_ts: Start timestamp (epoch milliseconds)
            end_ts: End timestamp (epoch milliseconds)
            
        Yields:
            Door event documents with flattened structure
        """
        try:
            # Optimized query - move timestamp filtering to SQL to reduce data transfer
            query = """
                SELECT 
                    c.kafkaMessage.Timestamp as Timestamp,
                    c.kafkaMessage.Door.MachineId as MachineId,
                    c.kafkaMessage.Door.State as State,
                    c.kafkaMessage.Door.Door.Deck as Deck,
                    c.kafkaMessage.Door.Door.Side as Side
                FROM c
                WHERE c.installationId = @installationId
                  AND c.dataType = @dataType
                  AND c.kafkaMessage.Timestamp >= @startTs
                  AND c.kafkaMessage.Timestamp <= @endTs
                  AND IS_DEFINED(c.kafkaMessage.Door)
            """
            
            parameters = [
                {"name": "@installationId", "value": installation_id},
                {"name": "@dataType", "value": "Door"},
                {"name": "@startTs", "value": start_ts},
                {"name": "@endTs", "value": end_ts}
            ]
            
            logger.info(f"Optimized door events query for installation: {installation_id}, range: {start_ts} to {end_ts}")
            
            query_iterator = self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=1000
            )
            
            for item in query_iterator:
                # Data is already filtered and flattened by SQL query
                timestamp = item.get("Timestamp")
                
                # Skip if timestamp is still None (shouldn't happen with SQL filtering)
                if timestamp is None:
                    continue
                
                # Data is already flattened by the SELECT statement
                flattened_event = {
                    "Timestamp": timestamp,
                    "MachineId": item.get("MachineId"),
                    "State": item.get("State"),
                    "Deck": item.get("Deck"),
                    "Side": item.get("Side")
                }
                
                yield flattened_event
                
        except Exception as e:
            logger.error(f"Error querying door events: {e}", exc_info=True)
            raise

    def clear_cache(self):
        """Clear all caches for fresh data."""
        self._machine_ids_cache.clear()
        self.get_installations.cache_clear()
        logger.info("Cosmos service caches cleared")


# Global instance - will be initialized when needed
cosmos_service = None


def get_cosmos_service():
    """Get or create the global cosmos service instance."""
    global cosmos_service
    if cosmos_service is None:
        cosmos_service = CosmosService()
    return cosmos_service
