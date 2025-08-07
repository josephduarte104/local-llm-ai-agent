# Elevator Ops Analyst - Makefile
# Production-ready Flask app with local LLM and Azure Cosmos DB

.PHONY: help install dev run test clean lint format

# Variables
PYTHON := python3
PIP := pip3
FLASK_APP := app.py
FLASK_ENV := development
PORT := 5000

# Default target
help:
	@echo "Elevator Ops Analyst - Available commands:"
	@echo "  install    Install all dependencies"
	@echo "  dev        Run development server with auto-reload"
	@echo "  run        Run production server"
	@echo "  test       Run test suite"
	@echo "  lint       Run linting with ruff"
	@echo "  format     Format code with black"
	@echo "  clean      Clean temporary files"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - LM Studio running on http://127.0.0.1:1234"
	@echo "  - .env file configured with Cosmos DB credentials"

# Install dependencies
install:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt

# Development server with auto-reload
dev:
	@echo "Starting development server..."
	@echo "Make sure LM Studio is running on http://127.0.0.1:1234"
	@echo "Visit http://localhost:$(PORT) to access the app"
	FLASK_ENV=development $(PYTHON) $(FLASK_APP)

# Production server
run:
	@echo "Starting production server..."
	@echo "Make sure LM Studio is running on http://127.0.0.1:1234"
	@echo "Visit http://localhost:$(PORT) to access the app"
	FLASK_ENV=production $(PYTHON) $(FLASK_APP)

# Run tests
test:
	@echo "Running test suite..."
	$(PYTHON) -m pytest tests/ -v

# Lint code
lint:
	@echo "Running ruff linter..."
	ruff check .
	@echo "Linting complete!"

# Format code
format:
	@echo "Formatting with black..."
	black .
	@echo "Formatting complete!"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "Cleanup complete!"

# Quick setup for new environments
setup: install
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env with your Azure Cosmos DB credentials"; \
	fi
	@echo "Setup complete! Edit .env with your credentials, then run 'make dev'"
