"""
Elevator Ops Analyst - Flask Web Application

A production-ready Flask web app with chat-style UI that uses a local LM Studio model
and Azure Cosmos DB to answer questions about elevator operations.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify
from typing import Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import services and agents
from services.cosmos import get_cosmos_service
from services.uptime import uptime_service
from services.timezone import timezone_service
from agents.orchestrator import query_orchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, 
           template_folder='ui/templates',
           static_folder='ui/static')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)


@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')


@app.route('/api/installations', methods=['GET'])
def get_installations():
    """
    Get list of installations with their timezones.
    
    Returns:
        JSON array of {installationId, timezone} objects
    """
    try:
        cosmos_service = get_cosmos_service()
        installations = cosmos_service.get_installations()
        return jsonify(installations)
    except Exception as e:
        logger.error(f"Error fetching installations: {e}")
        # Return fallback data when Cosmos DB is unavailable
        fallback_installations = [
            {"installationId": "demo-installation-1", "timezone": "America/New_York"},
            {"installationId": "demo-installation-2", "timezone": "America/Chicago"},
            {"installationId": "demo-installation-3", "timezone": "America/Los_Angeles"}
        ]
        logger.info("Returning fallback installation data due to database connection issues")
        return jsonify(fallback_installations)


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat messages and return AI responses.
    
    Expected JSON body:
    {
        "message": "User's question",
        "installationId": "Installation ID",
        "startISO": "Optional start date (YYYY-MM-DD)",
        "endISO": "Optional end date (YYYY-MM-DD)"
    }
    
    Returns:
        JSON with answer and metadata
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        message = data.get('message', '').strip()
        installation_id = data.get('installationId', '').strip()
        start_iso = data.get('startISO')
        end_iso = data.get('endISO')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        if not installation_id:
            return jsonify({'error': 'Installation ID is required'}), 400
        
        # Validate installation exists
        try:
            cosmos_service = get_cosmos_service()
            installations = cosmos_service.get_installations()
        except Exception as e:
            logger.warning(f"Could not fetch installations from Cosmos DB: {e}. Using fallback data.")
            installations = []
        
        # Always add demo installations for testing purposes
        demo_installations = [
            {"installationId": "demo-installation-1", "timezone": "America/New_York"},
            {"installationId": "demo-installation-2", "timezone": "America/Chicago"},
            {"installationId": "demo-installation-3", "timezone": "America/Los_Angeles"}
        ]
        installations.extend(demo_installations)
        
        if not any(inst['installationId'] == installation_id for inst in installations):
            return jsonify({'error': f'Installation {installation_id} not found'}), 400
        
        # Process query through orchestrator
        result = query_orchestrator.process_query(
            message=message,
            installation_id=installation_id,
            start_iso=start_iso,
            end_iso=end_iso
        )
        
        # Log the query (without sensitive data)
        logger.info(f"Query processed - Installation: {installation_id}, "
                   f"Tools used: {list(result.get('tool_results', {}).keys())}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/uptime', methods=['POST'])
def get_uptime_metrics():
    """
    Get structured uptime/downtime metrics.
    
    Expected JSON body:
    {
        "installationId": "Installation ID",
        "startISO": "Start date (YYYY-MM-DD)",
        "endISO": "End date (YYYY-MM-DD)"
    }
    
    Returns:
        JSON with detailed uptime metrics
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        installation_id = data.get('installationId', '').strip()
        start_iso = data.get('startISO', '').strip()
        end_iso = data.get('endISO', '').strip()
        
        if not all([installation_id, start_iso, end_iso]):
            return jsonify({'error': 'installationId, startISO, and endISO are required'}), 400
        
        # Get installation timezone
        cosmos_service = get_cosmos_service()
        installations = cosmos_service.get_installations()
        installation_info = next(
            (inst for inst in installations if inst['installationId'] == installation_id),
            None
        )
        
        if not installation_info:
            return jsonify({'error': f'Installation {installation_id} not found'}), 400
        
        installation_tz = installation_info['timezone']
        
        # Parse dates
        start_time = timezone_service.parse_iso_with_timezone(start_iso, installation_tz)
        end_time = timezone_service.parse_iso_with_timezone(end_iso, installation_tz)
        
        if not start_time or not end_time:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get uptime metrics
        metrics = uptime_service.get_uptime_metrics(
            installation_id=installation_id,
            start_time=start_time,
            end_time=end_time,
            installation_tz=installation_tz
        )
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Error getting uptime metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error: Any) -> tuple[Any, int]:
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error: Any) -> tuple[Any, int]:
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


def validate_environment():
    """Validate that required environment variables are set."""
    required_vars = ['COSMOS_ENDPOINT', 'COSMOS_KEY', 'LLM_API_URL', 'LLM_MODEL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    return True


if __name__ == '__main__':
    if not validate_environment():
        logger.error("Environment validation failed. Check your .env file.")
        exit(1)
    
    # Development server settings
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('FLASK_PORT', 5000))
    
    logger.info(f"Starting Elevator Ops Analyst on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"LLM endpoint: {os.getenv('LLM_API_URL')}")
    logger.info(f"Cosmos DB: {os.getenv('COSMOS_DATABASE_NAME')}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
