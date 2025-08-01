#!/bin/bash

# Elevator Operations Agent - Quick Start Script

echo "🏢 Elevator Operations Agent - Quick Start"
echo "========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found"

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env from .env.example..."
        cp .env.example .env
        echo "⚠️  Please edit .env with your actual configuration"
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Check if Ollama is running
echo "🤖 Checking for local LLM services..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama service detected"
elif curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "✅ LM Studio service detected"
else
    echo "⚠️  No local LLM service detected"
    echo "Please start Ollama or LM Studio:"
    echo ""
    echo "For Ollama:"
    echo "1. Install: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "2. Pull model: ollama pull llama3.1:8b"
    echo "3. Start server: ollama serve"
    echo ""
    echo "For LM Studio:"
    echo "1. Download and install LM Studio"
    echo "2. Load a model"
    echo "3. Start the local server"
fi

# Generate sample data
echo "📊 Generating sample data..."
python3 -c "from src.utils.sample_data import save_test_data; save_test_data('sample_data.json', 14)"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Azure Cosmos DB credentials"
echo "2. Ensure your local LLM service is running"
echo "3. Run: python app.py"
echo ""
echo "To start the application:"
echo "python app.py"
echo ""
echo "For production:"
echo "gunicorn -w 4 -b 0.0.0.0:5000 app:app"
