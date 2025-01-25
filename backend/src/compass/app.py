import eventlet
import os

# Configure eventlet for debugging
if os.environ.get('FLASK_DEBUG') == '1':
    eventlet.monkey_patch(all=True, thread=False, os=True)  # Don't patch threading in debug mode
else:
    eventlet.monkey_patch(all=True, thread=True, os=True)

import signal
import sys
import logging
import asyncio

# Configure logging before other imports
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask and SocketIO imports
from flask import Flask, request
from flask_socketio import SocketIO, emit

# Initialize Flask
app = Flask(__name__)
app.config.from_object('compass.config.config.Config')

# Initialize SocketIO with debug-specific settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    debug=True,
    async_handlers=False if os.environ.get('FLASK_DEBUG') == '1' else True  # Disable async handlers in debug mode
)

# Now import application modules
from compass.agent.agent import AgentService
from compass.services.state_manager import StateManager
from compass.utils.utility import HistoryLogger
from compass.training_agent.training_agent import TrainingAgent

# Initialize services
training_agent = TrainingAgent()
state_manager = StateManager(socketio)
agent_service = AgentService(state_manager)

def cleanup():
    """Cleanup function to handle graceful shutdown"""
    logger.info('Shutting down gracefully...')
    try:
        socketio.stop()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
    finally:
        sys.exit(0)

def signal_handler(sig, frame):
    cleanup()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected with sid: {request.sid}')  # type: ignore
    emit('status', {'data': 'Connected to server', 'sid': request.sid})  # type: ignore

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected with sid: {request.sid}')  # type: ignore

@socketio.on('message')
def handle_message(data):
    try:
        logger.info("Handling new message")
        text = data.get('text', '')
        image_data = data.get('image_data')
        
        # Create a HumanMessage with both text and image
        message = {
            'text': text,
            'image_data': image_data
        }
        
        with app.app_context():
            eventlet.spawn(asyncio.run, agent_service.process_message(message))
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('control_update')
def handle_control_update(data):
    logger.info(f'Control update received: {data}')
    try:
        with app.app_context():
            state_manager.update_state(data)
    except Exception as e:
        logger.error(f"Error in handle_control_update: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('execute_next_tool')
def handle_execute_next_tool():
    logger.info('Received execute_next_tool request')
    try:
        with app.app_context():
            eventlet.spawn(asyncio.run, agent_service.execute_all_pending_tools())
    except Exception as e:
        logger.error(f"Error executing tool: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('generate_next_action')
def handle_generate_next_action():
    logger.info('Received generate_next_action request')
    try:
        with app.app_context():
            eventlet.spawn(asyncio.run, agent_service.process_next_action())
    except Exception as e:
        logger.error(f"Error generating next action: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('execute_tool_and_generate_action')
def handle_execute_tool_and_generate_action():
    logger.info('Received execute_tool_and_generate_action request')
    try:
        async def combined_operation():
            await agent_service.execute_all_pending_tools()
            await agent_service.process_next_action()
            
        with app.app_context():
            eventlet.spawn(asyncio.run, combined_operation())
    except Exception as e:
        logger.error(f"Error in combined operation: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('upload_screenshot')
def handle_screenshot_upload(data):
    try:
        result = training_agent.process_screenshot(
            image_data=data['image'],
            agent_name=data['agent_name']
        )
        emit('detection_result', result)
    except Exception as e:
        logger.error(f"Error processing screenshot: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('save_template')
def handle_save_template(data):
    try:
        training_agent.save_template(
            image_data=data['image'],
            caption=data['caption'],
            bbox=data['bbox']
        )
        emit('template_saved', {'success': True})
    except Exception as e:
        logger.error(f"Error saving template: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('ping')
def handle_ping():
    emit('pong')

@socketio.on('new_chat')
def handle_new_chat():
    logger.info('Starting new chat')
    try:
        # Reinitialize the services
        global agent_service, state_manager
        state_manager = StateManager(socketio)
        agent_service = AgentService(state_manager)
        emit('chat_reset', {'status': 'success'})
    except Exception as e:
        logger.error(f"Error starting new chat: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on_error()
def error_handler(e):
    logger.error(f"SocketIO error: {str(e)}")
    emit('error', {'message': str(e)})

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f"SocketIO default error: {str(e)}")
    emit('error', {'message': str(e)})

if __name__ == '__main__':
    try:
        socketio.run(app, 
            host='0.0.0.0',
            debug=True, 
            port=5001,
            use_reloader=False,
            log_output=True)
    except KeyboardInterrupt:
        cleanup() 