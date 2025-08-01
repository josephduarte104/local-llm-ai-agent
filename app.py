"""
Elevator Operations AI Agent - Flask Application
A ChatGPT-like interface for elevator uptime/downtime analysis
"""

import asyncio
import json
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from src.agent.elevator_agent import ElevatorAgent
from src.config.settings import get_settings

# Initialize Flask app
app = Flask(__name__)

# Load settings from .env
settings = get_settings()

# Configure Flask from environment variables
app.config['SECRET_KEY'] = settings.secret_key
app.config['DEBUG'] = settings.flask_debug

# Enable CORS and SocketIO
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global agent instance
agent = None
agent_initialized = False

def initialize_agent():
    """Initialize the elevator agent"""
    global agent, agent_initialized
    
    try:
        print("Initializing agent...")
        agent_instance = ElevatorAgent(settings)
        success = agent_instance.initialize()  # Now synchronous
        
        if success:
            agent = agent_instance
            agent_initialized = True
            return True
        else:
            print("❌ Failed to initialize agent")
            print("⚠️  Agent initialization failed - some features may not work")
            return False
    except Exception as e:
        print(f"Failed to initialize agent: {str(e)}")
        print("⚠️  Agent initialization failed - some features may not work")
        return False

def process_message_sync(user_message, conversation_history):
    """Synchronous wrapper for message processing"""
    global agent
    
    if not agent:
        return {
            "content": "❌ Agent not initialized. Please check configuration.",
            "tool_results": []
        }
    
    try:
        return agent.process_message(user_message, conversation_history)
    except Exception as e:
        return {
            "content": f"❌ Error processing message: {str(e)}",
            "tool_results": []
        }

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html', 
                         app_title=settings.app_title,
                         agent_ready=agent_initialized)

@app.route('/api/status')
def status():
    """Get agent status"""
    status_info = {
        "agent_initialized": agent_initialized,
        "app_title": settings.app_title,
        "llm_provider": settings.LLM_PROVIDER,
        "installations": []
    }
    
    if agent and agent_initialized:
        try:
            status_info["installations"] = agent.cosmos_client.installations
        except Exception as e:
            status_info["error"] = str(e)
    
    return jsonify(status_info)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        if not agent_initialized:
            return jsonify({
                "content": "❌ Agent not initialized. Please check configuration and restart.",
                "tool_results": []
            })
        
        # Process the message
        response = process_message_sync(user_message, conversation_history)
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "content": f"❌ Error processing request: {str(e)}",
            "tool_results": []
        }), 500

@app.route('/api/quick-actions')
def quick_actions():
    """Get quick action suggestions"""
    actions = [
        {
            "id": "last_week_uptime",
            "title": "📊 Last Week Uptime",
            "query": "What was the uptime and downtime for all elevators last week?"
        },
        {
            "id": "current_issues",
            "title": "⚠️ Current Issues",
            "query": "Show me any elevators currently experiencing downtime or issues"
        },
        {
            "id": "performance_trends",
            "title": "📈 Performance Trends", 
            "query": "Compare elevator performance across installations"
        },
        {
            "id": "detailed_analysis",
            "title": "🔍 Detailed Analysis",
            "query": "Provide a detailed analysis of elevator operations for the past month"
        }
    ]
    return jsonify(actions)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('status', {
        'agent_ready': agent_initialized,
        'message': 'Connected to Elevator Operations Agent'
    })

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle real-time chat message"""
    try:
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            emit('error', {'message': 'No message provided'})
            return
        
        if not agent_initialized:
            emit('chat_response', {
                'content': '❌ Agent not initialized. Please check configuration.',
                'tool_results': []
            })
            return
        
        # Emit typing indicator
        emit('typing', {'typing': True})
        
        # Process message
        response = process_message_sync(user_message, conversation_history)
        
        # Ensure response is JSON serializable
        try:
            json.dumps(response)
        except TypeError as json_error:
            print(f"JSON serialization error: {json_error}")
            print(f"Response type: {type(response)}")
            print(f"Response content: {response}")
            response = {
                "content": "❌ Error: Response contains non-serializable data",
                "tool_results": []
            }
        
        # Emit response
        emit('typing', {'typing': False})
        emit('chat_response', response)
        
    except Exception as e:
        emit('typing', {'typing': False})
        emit('error', {'message': f'Error processing message: {str(e)}'})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html', error=str(error)), 500

if __name__ == '__main__':
    print("🏢 Elevator Operations Agent - Flask Application")
    print("=" * 50)
    
    # Initialize agent
    print("Initializing agent...")
    if initialize_agent():
        print(f"✅ Agent ready!")
        if agent and agent.cosmos_client.installations:
            print(f"📍 Found {len(agent.cosmos_client.installations)} installations")
    else:
        print("⚠️  Agent initialization failed - some features may not work")
    
    print(f"\n🌐 Starting server on {settings.flask_host}:{settings.flask_port}")
    print(f"🔗 Access the application at: http://{settings.flask_host}:{settings.flask_port}")
    
    # Run the application
    socketio.run(
        app,
        host=settings.flask_host,
        port=settings.flask_port,
        debug=settings.flask_debug
    )
