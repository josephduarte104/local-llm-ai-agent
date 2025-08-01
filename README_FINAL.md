# 🏢 Elevator Operations AI Agent

A comprehensive AI agent that analyzes elevator event data stored in Azure Cosmos DB to compute uptime/downtime and explain incidents, with timezone-aware analysis and a ChatGPT-like interface.

## 🚀 Features

- **ChatGPT-like Interface**: Clean, intuitive chat interface built with Streamlit
- **Multi-Installation Support**: Analyze multiple elevator installations with timezone awareness
- **Uptime/Downtime Analysis**: Precise calculations with elevator mode transitions
- **Local LLM Integration**: Works with Ollama or LM Studio for privacy and cost efficiency
- **Interactive Visualizations**: Charts, timelines, and detailed breakdowns
- **Memory Efficient**: Optimized for large datasets with pagination and streaming
- **Tool-Based Architecture**: Extensible function-calling system

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- Azure Cosmos DB account
- Local LLM service (Ollama or LM Studio)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd local-llm-ai-agent

# Run setup script
python setup.py
# or use the bash script
./quickstart.sh

# Configure your environment
cp .env.example .env
# Edit .env with your Azure Cosmos DB credentials
```

### Local LLM Setup

#### Option A: Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1:8b

# Start the server
ollama serve
```

#### Option B: LM Studio
1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load your preferred model
3. Start the local server (usually on port 1234)
4. Update `.env`: `LLM_PROVIDER=lmstudio`

### Run the Application

```bash
streamlit run app.py
```

Visit `http://localhost:8501` to access the chat interface.

## 📊 Usage Examples

### Basic Queries
- "What was the uptime and downtime for elevators last week?"
- "Show me elevator performance for all installations"
- "Explain downtime for elevator 1 at installation ABC123"

### Advanced Analysis
- "Compare elevator performance across different timezones"
- "Show me the most problematic elevators this month"
- "Generate a detailed maintenance report"

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │───▶│  Elevator Agent  │───▶│   Cosmos DB     │
│ (Chat Interface)│    │ (Orchestrator)   │    │ (Event Data)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Local LLM      │
                       │ (Ollama/LMStudio)│
                       └──────────────────┘
```

### Core Components

1. **ElevatorAgent**: Main orchestrator handling conversation flow and tool coordination
2. **Tools**: Specialized functions for data analysis and computation
3. **CosmosDBClient**: Memory-efficient database operations with pagination
4. **LocalLLMClient**: Interface to local language models
5. **ChatInterface**: Streamlit-based UI with visualizations

## 📋 Data Model

### Installation Document
```json
{
  "id": "installations-list",
  "installations": [
    {
      "installationId": "4995d395-...-c6",
      "timezone": "America/New_York",
      "name": "Corporate Tower NYC"
    }
  ]
}
```

### Event Document
```json
{
  "kafkaMessage": {
    "Timestamp": 1751909536958,
    "EventCase": "CarModeChanged",
    "CarModeChanged": {
      "MachineId": 1,
      "ModeName": "NOR",
      "CarMode": 142,
      "AlarmSeverity": 0
    }
  },
  "installationId": "4995d395-...-c6",
  "dataType": "CarModeChanged"
}
```

## 🎯 Elevator Mode Reference

### Uptime Modes (Normal Operation)
- **NOR**: Normal operation
- **IDL**: Idle state
- **INS**: Inspection mode
- **ATT**: Attendant mode
- **PRK**: Parking operation
- [See full list in code]

### Downtime Modes (Out of Service)
- **DLF**: Door Lock Failure
- **ESB**: Emergency Stop Button
- **COR**: Correction mode
- **NAV**: Not Available
- **DBF**: Drive Brake Fault
- [See full list in code]

## ⚙️ Configuration

### Environment Variables
```bash
# Azure Cosmos DB
COSMOSDB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOSDB_KEY=your-cosmosdb-key
COSMOSDB_DATABASE=elevatordb
COSMOSDB_CONTAINER=elevatorevents

# Local LLM (choose one)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Or for LM Studio
# LLM_PROVIDER=lmstudio
# LMSTUDIO_BASE_URL=http://localhost:1234
# LMSTUDIO_MODEL=your-model-name

# Performance
MAX_EVENTS_PER_QUERY=5000
QUERY_TIMEOUT_SECONDS=30
MEMORY_LIMIT_MB=512
```

## 🧪 Testing

```bash
# Run the test suite
python test_agent.py

# Generate sample data for testing
python -c "from src.utils.sample_data import save_test_data; save_test_data()"
```

## 📈 Performance Features

- **Memory Efficiency**: Pagination, streaming, and configurable limits
- **Query Optimization**: Server-side filtering and proper indexing
- **Timezone Handling**: Full IANA timezone support with DST awareness
- **Async Architecture**: Non-blocking operations throughout

## 🔧 Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Detailed architecture documentation
- Adding new features
- Performance optimization
- Debugging techniques

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🆘 Support

- Check the [DEVELOPMENT.md](DEVELOPMENT.md) for troubleshooting
- Ensure your `.env` configuration is correct
- Verify that your local LLM service is running
- Test your Cosmos DB connection

## 🎉 Acknowledgments

Built following the detailed system prompt specifications for elevator operations analysis with timezone awareness and local LLM integration.
