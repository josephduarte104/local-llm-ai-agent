"""
Cosmos DB optimization configuration and best practices implementation.
"""

# Query optimization settings
COSMOS_QUERY_OPTIONS = {
    # Force index usage and disable table scans
    "enable_scan_in_query": False,
    
    # Limit continuation token size to reduce memory usage
    "response_continuation_token_limit_in_kb": 1,
    
    # Optimize for scenarios with known result sizes
    "max_item_count": 1000,
    
    # Enable parallel processing where appropriate
    "max_degree_of_parallelism": 10,
    
    # Buffer settings for better throughput
    "max_buffered_item_count": 1000,
}

# Connection settings for better performance
COSMOS_CONNECTION_CONFIG = {
    "connection_timeout": 30,  # seconds
    "read_timeout": 30,       # seconds
    "consistency_level": "Session",  # Faster than Strong consistency
}

# Retry policy for handling throttling
COSMOS_RETRY_POLICY = {
    "max_retry_attempts_on_throttled_requests": 9,
    "max_retry_wait_time_on_throttled_requests": 30
}

# Caching configuration
CACHE_CONFIG = {
    "installations_cache_ttl": 1800,     # 30 minutes
    "machine_ids_cache_ttl": 300,        # 5 minutes  
    "max_cache_size": 1000,              # Max items in cache
}

# Query patterns to avoid (for monitoring/alerting)
INEFFICIENT_PATTERNS = [
    "SELECT *",                          # Always select specific fields
    "ORDER BY without composite index",  # Requires composite index
    "CROSS PARTITION without optimization", # High RU cost
    "User-defined functions in WHERE",   # Poor performance
    "Complex JOINs",                     # Avoid in NoSQL
]

# Recommended query patterns
EFFICIENT_PATTERNS = [
    "SELECT specific fields only",
    "WHERE clauses with indexed fields first", 
    "Parameterized queries",
    "Point lookups with partition key + id",
    "Composite indexes for multi-field queries",
]

# Monitoring thresholds
PERFORMANCE_THRESHOLDS = {
    "max_query_time_ms": 1000,          # Alert if query takes > 1 second
    "max_ru_per_query": 100,            # Alert if query uses > 100 RUs
    "max_cross_partition_percentage": 20, # Alert if > 20% queries cross partitions
    "min_cache_hit_rate": 80,           # Alert if cache hit rate < 80%
}

def apply_query_optimizations(container):
    """
    Apply performance optimizations to a Cosmos container client.
    
    Args:
        container: Cosmos container client
        
    Returns:
        Optimized container client
    """
    # Note: These would be applied at the query level in actual implementation
    return container

def log_query_performance(query_name: str, execution_time_ms: float, ru_consumed: float):
    """
    Log query performance metrics for monitoring.
    
    Args:
        query_name: Name/identifier of the query
        execution_time_ms: Query execution time in milliseconds  
        ru_consumed: Request Units consumed
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log performance metrics
    logger.info(f"Query Performance - {query_name}: {execution_time_ms:.2f}ms, {ru_consumed:.2f} RU")
    
    # Check thresholds and log warnings
    if execution_time_ms > PERFORMANCE_THRESHOLDS["max_query_time_ms"]:
        logger.warning(f"Slow query detected: {query_name} took {execution_time_ms:.2f}ms")
    
    if ru_consumed > PERFORMANCE_THRESHOLDS["max_ru_per_query"]:
        logger.warning(f"High RU consumption: {query_name} used {ru_consumed:.2f} RU")

# Example usage in cosmos service
def create_optimized_query_options(cross_partition: bool = False, max_items: int = 1000):
    """
    Create optimized query options based on query characteristics.
    
    Args:
        cross_partition: Whether this is a cross-partition query
        max_items: Maximum items to return
        
    Returns:
        Dictionary of query options
    """
    options = COSMOS_QUERY_OPTIONS.copy()
    options["max_item_count"] = max_items
    options["enable_cross_partition_query"] = cross_partition
    
    # Adjust settings for cross-partition queries
    if cross_partition:
        options["max_degree_of_parallelism"] = 5  # Lower for cross-partition
    
    return options
