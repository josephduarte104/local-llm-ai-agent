# 🏗️ Elevator Ops Analyst

A production-ready Flask web application with a **ChatGPT-like interface** that uses a **local LM Studio model** and **Azure Cosmos DB** to analyze elevator operations and answer questions about uptime, downtime, and operational metrics.

## ✨ Features

- **Modern Chat Interface**: Responsive, mobile-friendly chat UI similar to ChatGPT
- **Local LLM Integration**: Uses LM Studio with OpenAI-compatible API
- **Azure Cosmos DB**: Queries elevator event data from Cosmos SQL API
- **Timezone-Aware**: Handles installation-specific timezones correctly
- **Uptime/Downtime Analysis**: Calculates accurate uptime metrics from CarModeChanged events
- **RESTful APIs**: Clean API endpoints for integrations
- **Production Ready**: Proper logging, error handling, and validation

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **LM Studio** running with `liquid/lfm2-1.2b` model on `http://127.0.0.1:1234`
3. **Azure Cosmos DB** with elevator events data

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd elevator_ai_agent
   ```

2. **Install dependencies:**
   ```bash
   make install
   # or manually: pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Azure Cosmos DB credentials
   ```

4. **Start LM Studio:**
   - Download and run [LM Studio](https://lmstudio.ai/)
   - Load the `liquid/lfm2-1.2b` model
   - Start the local server on `http://127.0.0.1:1234`

5. **Run the application:**
   ```bash
   make dev
   # Visit http://localhost:5000
   ```

## 🔧 Configuration

### Environment Variables (.env)

```env
COSMOS_URI=https://your-cosmos-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-primary-key
COSMOS_DB=elevatoreventsdb
COSMOS_CONTAINER=elevatorevents
LM_BASE_URL=http://127.0.0.1:1234/v1
LM_MODEL=liquid/lfm2-1.2b
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
```

### LM Studio Setup

1. **Download LM Studio**: Visit [lmstudio.ai](https://lmstudio.ai)
2. **Install the model**: Search for and download `liquid/lfm2-1.2b`
3. **Start the server**:
   - Load the model in LM Studio
   - Go to "Local Server" tab
   - Click "Start Server"
   - Verify endpoint: `http://127.0.0.1:1234/v1/chat/completions`

## 📊 Data Structure

### Installation List Document
```json
{
  "id": "installation-list",
  "installations": [
    {
      "installationId": "1234",
      "timezone": "America/New_York"
    }
  ]
}
```

### Event Documents
```json
{
  "id": "unique-event-id",
  "installationId": "1234",
  "dataType": "CarModeChanged",
  "kafkaMessage": {
    "Timestamp": 1703980800000,
    "EventCase": "CarModeChanged",
    "CarModeChanged": {
      "MachineId": "Elevator_1",
      "ModeName": "NOR",
      "CarMode": "Normal",
      "AlarmSeverity": "None"
    }
  }
}
```

## 🛠️ API Reference

### GET /api/installations
Returns list of available installations.

**Response:**
```json
[
  {
    "installationId": "1234",
    "timezone": "America/New_York"
  }
]
```

### POST /api/chat
Process chat messages and return AI responses.

**Request:**
```json
{
  "message": "What was the uptime last week?",
  "installationId": "1234",
  "startISO": "2023-12-01",
  "endISO": "2023-12-07"
}
```

**Response:**
```json
{
  "answer": "Analysis of elevator uptime for installation 1234...",
  "tool_results": { "uptime": { ... } },
  "installation_tz": "America/New_York"
}
```

### POST /api/uptime
Get structured uptime/downtime metrics.

**Request:**
```json
{
  "installationId": "1234",
  "startISO": "2023-12-01",
  "endISO": "2023-12-07"
}
```

**Response:**
```json
{
  "installation_summary": {
    "uptime_percentage": 95.2,
    "downtime_percentage": 4.8,
    "uptime_minutes": 9619.2,
    "downtime_minutes": 484.8
  },
  "machine_metrics": [...]
}
```

## 🔍 Example Usage

### Test the API with curl:

```bash
# Get installations
curl http://localhost:5000/api/installations

# Test chat endpoint
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What was the uptime last week?",
    "installationId": "1234"
  }'

# Get uptime metrics
curl -X POST http://localhost:5000/api/uptime \
  -H "Content-Type: application/json" \
  -d '{
    "installationId": "1234",
    "startISO": "2023-12-01",
    "endISO": "2023-12-07"
  }'
```

## 🧪 Testing

### Run the test suite:
```bash
make test
# or manually: python -m pytest tests/ -v
```

### Example Questions to Test:

1. **"What was the uptime and downtime for elevators last week?"**
   - Returns per-machine and rolled-up totals
   - Shows percentages and minutes/hours
   - Includes date range and timezone

2. **"Explain downtime for elevator Elevator_1"**
   - Returns mode intervals during downtime periods
   - Shows timestamps in local timezone
   - Provides concise explanations

## 📁 Project Structure

```
elevator_ai_agent/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── Makefile              # Build and run commands
├── README.md             # This file
├── services/             # Core services
│   ├── cosmos.py         # Cosmos DB client
│   ├── llm.py           # LM Studio client
│   ├── timezone.py      # Timezone utilities
│   └── uptime.py        # Uptime calculations
├── agents/               # Query orchestration
│   └── orchestrator.py  # Main query processor
├── tools/                # Analysis tools
│   ├── base.py          # Tool interface
│   ├── car_mode_changed.py  # Uptime analysis
│   └── basic_tools.py   # Other event tools
├── ui/                   # Web interface
│   ├── templates/
│   │   └── index.html   # Main chat page
│   └── static/
│       ├── app.js       # Frontend JavaScript
│       └── styles.css   # Custom styles
└── logs/                 # Application logs
    └── app.log
```

## 🔄 Development Workflow

```bash
# Start development
make dev

# Code formatting
make format

# Linting
make lint

# Run tests
make test

# Clean temporary files
make clean
```

## 🛡️ Security & Production

- **Environment Variables**: Never commit sensitive data
- **Input Validation**: All user inputs are validated
- **Error Handling**: Graceful error handling with logging
- **CORS**: Configure as needed for your deployment
- **Rate Limiting**: Consider adding for production use
- **SSL/TLS**: Use HTTPS in production

## 🚨 Troubleshooting

### Common Issues:

1. **"Failed to fetch installations"**
   - Check Cosmos DB credentials in `.env`
   - Verify network connectivity to Azure

2. **"LLM endpoint not responding"**
   - Ensure LM Studio is running on `http://127.0.0.1:1234`
   - Check the model is loaded and server is started

3. **"No CarModeChanged events found"**
   - Verify the date range has data
   - Check installation ID is correct
   - Ensure Cosmos DB contains CarModeChanged events

4. **"Timezone conversion errors"**
   - Verify installation timezone is valid IANA format
   - Check timestamp format in Cosmos DB (epoch milliseconds)

## 📄 License

This project is provided as a code example. Adapt as needed for your use case.

---

**Built with:** Flask • Azure Cosmos DB • LM Studio • TailwindCSS
