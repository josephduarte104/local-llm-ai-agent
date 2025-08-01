"""
Configuration settings for the Elevator Operations Agent
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Settings:
    """Application settings loaded from environment variables"""
    
    # Cosmos DB Configuration
    cosmosdb_endpoint: str
    cosmosdb_key: str
    cosmosdb_database: str
    cosmosdb_container: str
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # ollama or lmstudio
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    LMSTUDIO_BASE_URL: str = "http://localhost:1234"
    LMSTUDIO_MODEL: str = "local-model"
    
    # Flask Configuration
    flask_app: str = "app.py"
    flask_env: str = "development"
    flask_debug: bool = True
    flask_host: str = "127.0.0.1"
    flask_port: int = 5000
    secret_key: str = "dev-secret-key"
    
    # UI Configuration
    app_title: str = "Elevator Operations Agent"
    default_timezone: str = "UTC"
    debug: bool = False
    
    # Performance settings
    max_events_per_query: int = 5000
    query_timeout_seconds: int = 30
    memory_limit_mb: int = 512

def get_settings() -> Settings:
    """
    Load and validate settings from environment variables
    
    Returns:
        Settings: Configured settings object
        
    Raises:
        ValueError: If required settings are missing
    """
    # Required settings
    required_vars = [
        "COSMOSDB_ENDPOINT",
        "COSMOSDB_KEY", 
        "COSMOSDB_DATABASE",
        "COSMOSDB_CONTAINER"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return Settings(
        # Cosmos DB
        cosmosdb_endpoint=os.getenv("COSMOSDB_ENDPOINT"),
        cosmosdb_key=os.getenv("COSMOSDB_KEY"),
        cosmosdb_database=os.getenv("COSMOSDB_DATABASE"),
        cosmosdb_container=os.getenv("COSMOSDB_CONTAINER"),
        
        # LLM
        LLM_PROVIDER=os.getenv("LLM_PROVIDER", "ollama").lower(),
        OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        LMSTUDIO_BASE_URL=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234"),
        LMSTUDIO_MODEL=os.getenv("LMSTUDIO_MODEL", "local-model"),
        
        # Flask
        flask_app=os.getenv("FLASK_APP", "app.py"),
        flask_env=os.getenv("FLASK_ENV", "development"),
        flask_debug=os.getenv("FLASK_DEBUG", "true").lower() == "true",
        flask_host=os.getenv("FLASK_HOST", "127.0.0.1"),
        flask_port=int(os.getenv("FLASK_PORT", "5000")),
        secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
        
        # UI
        app_title=os.getenv("APP_TITLE", "Elevator Operations Agent"),
        default_timezone=os.getenv("DEFAULT_TIMEZONE", "UTC"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        
        # Performance
        max_events_per_query=int(os.getenv("MAX_EVENTS_PER_QUERY", "5000")),
        query_timeout_seconds=int(os.getenv("QUERY_TIMEOUT_SECONDS", "30")),
        memory_limit_mb=int(os.getenv("MEMORY_LIMIT_MB", "512"))
    )

def validate_llm_connection(settings: Settings) -> bool:
    """
    Validate that the configured LLM service is available
    
    Args:
        settings: Application settings
        
    Returns:
        bool: True if LLM service is available
    """
    import requests
    
    try:
        if settings.LLM_PROVIDER == "ollama":
            response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        elif settings.LLM_PROVIDER == "lmstudio":
            response = requests.get(f"{settings.LMSTUDIO_BASE_URL.replace('/chat/completions', '')}/v1/models", timeout=5)
            return response.status_code == 200
        else:
            return False
    except requests.RequestException:
        return False

def validate_cosmos_connection(settings: Settings) -> bool:
    """
    Validate that Cosmos DB connection is working
    
    Args:
        settings: Application settings
        
    Returns:
        bool: True if Cosmos DB is accessible
    """
    try:
        from azure.cosmos import CosmosClient
        
        client = CosmosClient(settings.cosmosdb_endpoint, settings.cosmosdb_key)
        database = client.get_database_client(settings.cosmosdb_database)
        container = database.get_container_client(settings.cosmosdb_container)
        
        # Try to read a single item to test connection
        container.read_item("installations-list", partition_key="installations-list")
        return True
    except Exception:
        return False
