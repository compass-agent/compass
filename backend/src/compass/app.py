import eventlet
import os

# Windows-specific optimizations
eventlet.monkey_patch(
    os=False,  # Reduce OS-level monkey patching on Windows
    select=True,
    socket=True,
    thread=False,  # Don't patch threading by default
    time=True
)

# Configure DNS resolution for Windows
if os.name == 'nt':  # Windows-specific configuration
    import dns.resolver
    dns.resolver.get_default_resolver().cache = dns.resolver.Cache()

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

# Initialize SocketIO with Windows-optimized settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    debug=True,
    async_handlers=False if os.environ.get('FLASK_DEBUG') == '1' else True,  # Disable async handlers in debug mode
    max_http_buffer_size=1e4,  # Reduce buffer size
    manage_session=False  # Disable session management if not needed
)

# Now import application modules
from compass.agent.agent import AgentService
from compass.services.state_manager import StateManager
from compass.services.workflow_manager import WorkflowManager
from compass.constants import DEFAULT_AGENT_TYPE

# Initialize services
state_manager = StateManager(socketio)
agent_service = AgentService(state_manager)
workflow_manager = WorkflowManager()
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
def handle_disconnect(reason):
    logger.info(f'Client disconnected with sid: {request.sid}')  # type: ignore

@socketio.on('message')
def handle_message(data):
    try:
        logger.info("Handling new message")
        text = data.get('text', '')
        image_data = data.get('image_data')
        workflow_name = data.get('workflow_name')
        
        # Create a message with text, image, and workflow
        message = {
            'text': text,
            'image_data': image_data,
            'workflow_name': workflow_name
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

@socketio.on('ping')
def handle_ping():
    emit('pong')

@socketio.on('new_chat')
def handle_new_chat(data):
    logger.info('Starting new chat')
    try:
        # Update state manager with new agent type
        agent_name = data.get('agent_name', DEFAULT_AGENT_TYPE)  # Use default from constants if not specified
        state_manager.update_state({'agentType': agent_name})
        
        # Reinitialize just the agent service
        global agent_service
        agent_service = AgentService(state_manager)
        emit('chat_reset', {'status': 'success'})
    except Exception as e:
        logger.error(f"Error starting new chat: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('get_workflows')
def handle_get_workflows():
    logger.info('Received get_workflows request')
    try:
        workflows = workflow_manager.get_workflow_names()
        logger.info(f'Retrieved workflows: {workflows}')
        emit('workflows_list', {'workflows': workflows})
        logger.info('Successfully sent workflows_list event')
    except Exception as e:
        logger.error(f"Error getting workflows: {e}", exc_info=True)
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