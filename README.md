# Elevator Operations AI Agent

This AI agent analyzes elevator event data stored in Azure Cosmos DB to compute uptime/downtime and explain incidents, returning answers in the installation's local time zone.

## Features

- 🚀 ChatGPT-like interface using Flask and SocketIO
- 🏢 Multi-installation elevator monitoring
- ⏰ Timezone-aware uptime/downtime analysis
- 📊 Interactive visualizations with Plotly
- 🤖 Local LLM integration (Ollama/LM Studio)
- 🔍 Detailed downtime explanations
- 📈 Performance optimized queries
- 💬 Real-time messaging with WebSockets

## Setup

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Azure Cosmos DB credentials
```

### 2. Azure Cosmos DB Configuration

Ensure your Cosmos DB contains:
- Database: `elevatordb` (or as configured)
- Container: `elevatorevents` (or as configured)
- Document with `id = "installations-list"` containing installation metadata

### 3. Local LLM Setup

#### Option A: Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1:8b

# Start Ollama (runs on localhost:11434)
ollama serve
```

#### Option B: LM Studio
1. Download and install LM Studio
2. Load your preferred model
3. Start the local server (typically localhost:1234)
4. Update `.env` with LM Studio configuration

### 4. Run the Application

```bash
# Test the application setup
python test_app.py

# Install dependencies and test (if needed)
python test_app.py --install

# Run the Flask application
python app.py
```

The application will be available at `http://localhost:5000`

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Flask + WS    │───▶│  Agent Core      │───▶│  Cosmos DB      │
│   (Chat Interface) │    │  (Tools & Logic) │    │  (Event Data)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Local LLM      │
                       │ (Ollama/LMStudio)│
                       └──────────────────┘
```

## Usage Examples

1. **Uptime Analysis**: "What was the uptime and downtime for elevators last week?"
2. **Downtime Investigation**: "Explain downtime for elevator 1 at installation 4995d395-...-c6"
3. **Custom Queries**: "Show me elevator performance for the past month"

## Data Model

### Installation Document
```json
{
  "id": "installations-list",
  "installations": [
    {
      "installationId": "4995d395-...-c6",
      "timezone": "America/New_York",
      "name": "Site A"
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

## Mode Reference

| Code | Mode Name | Status | Description |
|------|-----------|--------|-------------|
| NOR  | Normal    | UPTIME | Normal operation |
| DLF  | Door Lock Failure | DOWNTIME | Critical door issue |
| ESB  | Emergency Stop | DOWNTIME | Emergency stop activated |
| ... | ... | ... | ... |

## Performance Considerations

- Queries are optimized with server-side filtering
- Pagination via continuation tokens
- Memory-efficient streaming aggregation
- Timezone-aware date handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details