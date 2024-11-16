import logging

# Configure logging BEFORE other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

# Disable engineio logging completely
engineio_logger = logging.getLogger('engineio.server')
engineio_logger.setLevel(logging.WARNING)  # Only show warnings and errors

# Disable werkzeug logging (Flask's default logger)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)

# Now import other modules
import json
import signal
import sys

from flask import Flask
from flask_socketio import SocketIO, emit
from services.agent import AgentService
from services.websocket import WebSocketService

# Create logger for this module
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize SocketIO with logging disabled
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    debug=False)

# Initialize services
agent_service = AgentService(socketio=socketio)
websocket_service = WebSocketService(agent_service)

# Mock agent state
agent_state = {
    'autoMode': False,
    'highlightMode': False,
    'playing': False,
    'processing': False,
    'currentTask': None
}

def signal_handler(sig, frame):
    logger.info('Shutting down gracefully...')
    socketio.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('status', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('message')
def handle_message(data):
    logger.info(f'Received message: {data}')
    
    try:
        response = agent_service.process_message(data.get('text', ''))
        websocket_service.handle_message(response)
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('control_update')
def handle_control_update(data):
    logger.info(f'Control update received: {data}')
    
    try:
        # Update agent state through agent service
        agent_service.update_state(data)
        
        # Broadcast full state update using websocket service
        websocket_service.broadcast_state(agent_state)
    except Exception as e:
        logger.error(f"Error in handle_control_update: {e}", exc_info=True)
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    try:
        socketio.run(app, 
                    debug=True, 
                    port=5001,
                    use_reloader=False,
                    log_output=True)
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        socketio.stop()
        sys.exit(0) 