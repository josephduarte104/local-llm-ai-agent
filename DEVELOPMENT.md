# Development Guide

## Project Structure

```
local-llm-ai-agent/
├── src/
│   ├── agent/               # Main agent logic
│   │   ├── elevator_agent.py    # Core agent orchestrator
│   │   └── llm_client.py        # Local LLM client
│   ├── config/              # Configuration management
│   │   └── settings.py          # Environment settings
│   ├── database/            # Database clients
│   │   └── cosmos_client.py     # Azure Cosmos DB client
│   ├── tools/               # Analysis tools
│   │   └── uptime_calculator.py # Uptime/downtime logic
│   ├── ui/                  # User interface
│   │   └── chat_interface.py    # Streamlit chat UI
│   └── utils/               # Utilities
│       └── sample_data.py       # Test data generator
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── setup.py                # Setup script
├── quickstart.sh           # Quick start script
└── test_agent.py           # Test suite
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone and setup
git clone <repository>
cd local-llm-ai-agent

# Run setup
python setup.py
# or
./quickstart.sh

# Edit configuration
cp .env.example .env
# Edit .env with your credentials
```

### 2. Local LLM Setup

#### Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1:8b

# Start server
ollama serve
```

#### LM Studio
1. Download LM Studio
2. Load your preferred model
3. Start local server
4. Update .env: `LLM_PROVIDER=lmstudio`

### 3. Azure Cosmos DB Setup

1. Create Azure Cosmos DB account
2. Create database (e.g., `elevatordb`)
3. Create container (e.g., `elevatorevents`)
4. Add installation document:

```json
{
  "id": "installations-list",
  "installations": [
    {
      "installationId": "your-installation-id",
      "timezone": "America/New_York", 
      "name": "Your Site Name"
    }
  ]
}
```

### 4. Testing

```bash
# Run test suite
python test_agent.py

# Generate sample data
python -c "from src.utils.sample_data import save_test_data; save_test_data()"

# Start application
streamlit run app.py
```

## Code Architecture

### Agent Pattern
The system follows an agent pattern where:
- `ElevatorAgent` orchestrates all operations
- Tools provide specific functionality (uptime calculation, etc.)
- LLM client handles model communication
- Database client manages data access

### Memory Efficiency
- Pagination for large datasets
- Streaming query results
- Configurable memory limits
- Server-side filtering

### Timezone Handling
- All calculations use installation-specific timezones
- IANA timezone names (e.g., "America/New_York")
- Proper DST handling with pytz

## Key Components

### ElevatorAgent
Main orchestrator that:
- Processes user messages
- Coordinates tool execution
- Manages conversation state
- Handles error recovery

### Tools
Function implementations for:
- `read_installations()`: Get installation metadata
- `query_events()`: Fetch event data with pagination
- `get_prior_mode()`: Get last mode before time window
- `compute_uptime_downtime()`: Calculate metrics
- `explain_downtime()`: Provide detailed analysis

### LLM Integration
- Supports Ollama and LM Studio
- Tool calling capability
- Async request handling
- Error handling and retries

## Configuration

### Environment Variables
```bash
# Cosmos DB
COSMOSDB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOSDB_KEY=your-key
COSMOSDB_DATABASE=elevatordb
COSMOSDB_CONTAINER=elevatorevents

# LLM
LLM_PROVIDER=ollama  # or lmstudio
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Performance
MAX_EVENTS_PER_QUERY=5000
QUERY_TIMEOUT_SECONDS=30
MEMORY_LIMIT_MB=512
```

## Adding New Features

### 1. New Tool
```python
# In elevator_agent.py
async def _tool_your_function(self, **kwargs):
    """Tool: Your new functionality"""
    try:
        # Implementation
        return {"result": "success"}
    except Exception as e:
        return {"error": str(e)}

# Add to tool definitions
{
    "type": "function",
    "function": {
        "name": "your_function",
        "description": "What it does",
        "parameters": {...}
    }
}
```

### 2. New UI Component
```python
# In chat_interface.py
def _create_your_visualization(self, data):
    """Create custom visualization"""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    # Your chart logic
    st.plotly_chart(fig)
```

### 3. New Data Type
```python
# In uptime_calculator.py
NEW_MODE_CODES = {
    "YOUR_MODE": "Your Mode Description"
}

# Update mode mappings
UPTIME_MODES.add("YOUR_MODE")
```

## Performance Optimization

### Query Optimization
- Use server-side filtering
- Implement pagination
- Add proper indexes in Cosmos DB
- Cache frequently accessed data

### Memory Management
- Stream large result sets
- Use generators for data processing
- Implement configurable limits
- Monitor memory usage

### LLM Optimization
- Use appropriate temperature settings
- Implement request batching
- Add response caching
- Handle rate limiting

## Debugging

### Debug Mode
Enable in Streamlit sidebar to see:
- Tool execution results
- LLM request/response details
- Query performance metrics
- Error stack traces

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing
```bash
# Run specific test
python -c "import asyncio; from test_agent import test_uptime_calculation; asyncio.run(test_uptime_calculation())"

# Test with sample data
python -c "from src.utils.sample_data import generate_test_data; print(generate_test_data(1))"
```

## Deployment Considerations

### Production Setup
- Use environment variables for all config
- Implement proper error handling
- Add health checks
- Set up monitoring and alerts

### Security
- Never commit secrets to git
- Use Azure Key Vault for production
- Implement rate limiting
- Validate all inputs

### Scalability
- Consider connection pooling
- Implement caching strategies
- Use async patterns throughout
- Monitor resource usage
