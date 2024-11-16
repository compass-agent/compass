import json
import signal
import sys

from flask import Flask
from flask_socketio import SocketIO, emit
from services.agent import AgentService
from services.websocket import WebSocketService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   async_mode='threading',
                   debug=True,
                   engineio_logger=True)

# Initialize services
agent_service = AgentService()
websocket_service = WebSocketService(agent_service)

# Mock agent state
agent_state = {
    'is_auto_mode': False,
    'is_highlight_mode': False,
    'is_playing': False,
    'current_task': None
}

def signal_handler(sig, frame):
    print('Shutting down gracefully...')
    socketio.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    
    try:
        # Process message through agent service
        response = agent_service.process_message(data.get('text', ''))
        websocket_service.handle_message(response)
    except Exception as e:
        print(f"Error in handle_message: {e}")
        emit('error', {'message': str(e)})

@socketio.on('control_update')
def handle_control_update(data):
    print('Control update:', data)
    
    try:
        # Update agent state through agent service
        agent_service.update_state(data)
        
        # Update local state
        if 'auto_mode' in data:
            agent_state['is_auto_mode'] = data['auto_mode']
        if 'highlight_mode' in data:
            agent_state['is_highlight_mode'] = data['highlight_mode']
        if 'playing' in data:
            agent_state['is_playing'] = data['playing']
        
        # Broadcast state update using websocket service
        websocket_service.broadcast_state(agent_state)
    except Exception as e:
        print(f"Error in handle_control_update: {e}")
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    try:
        socketio.run(app, 
                    debug=True, 
                    port=5001,
                    use_reloader=False,
                    log_output=True)
    except KeyboardInterrupt:
        print('Shutting down...')
        socketio.stop()
        sys.exit(0) 