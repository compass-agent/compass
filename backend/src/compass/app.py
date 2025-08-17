import logging
import os
from pathlib import Path

import dns.resolver

os.environ['EVENTLET_NO_GREENDNS'] = 'yes' 

import os
import sys

env = os.environ.get('COMPASS_ENV', 'development')
# Define user-accessible log directory in AppData
appdata_dir = os.environ.get('APPDATA', '.')
log_dir = os.path.join(appdata_dir, 'Compass', 'logs')
Path(log_dir).mkdir(parents=True, exist_ok=True)

# Configure file handler for logging
log_file = os.path.join(log_dir, 'compass_backend.log')
file_handler = logging.FileHandler(log_file)

# Configure logging first
if env == 'production':
    logging.basicConfig(level=logging.INFO, handlers=[file_handler])
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logger.info(f"Starting backend in {env} environment")

import eventlet

# Windows-specific optimizations
logger.info("==== Applying eventlet monkey patching ====")
eventlet.monkey_patch(
    os=False,  # Reduce OS-level monkey patching on Windows
    select=True,
    socket=True,
    thread=False,  # Don't patch threading by default
    time=True
)


# Windows DNS configuration
if os.name == 'nt':  # Windows-specific configuration
    try:
        import dns.resolver
        dns.resolver.get_default_resolver().cache = dns.resolver.Cache()
    except Exception as dns_error:
        logger.warning(f"✗ Failed to configure DNS resolver: {dns_error}")

import asyncio
import signal

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
    ping_timeout=6000,
    ping_interval=25,
    debug=True, # type: ignore
    async_handlers=False if os.environ.get('FLASK_DEBUG') == '1' else True,  # Disable async handlers in debug mode
    max_http_buffer_size=int(20 * 1024 * 1024),  # Reduce buffer size
    manage_session=False  # Disable session management if not needed
)

# Now import application modules
from compass.agent.agent import AgentService
from compass.constants import DEFAULT_AGENT_TYPE
from compass.services.state_manager import StateManager
from compass.services.workflow_manager import WorkflowManager
from compass.training_agent.training_agent import TrainingAgent

# Initialize services
state_manager = StateManager(socketio)
agent_service = AgentService(state_manager)
workflow_manager = WorkflowManager()
training_agent = TrainingAgent()
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

@socketio.on('connect_to_sap')
def handle_connect_to_sap():
    logger.info('Received connect_to_sap request')
    try:
        async def connect_sap():
            try:
                result = await agent_service.tool_collection.connect_tool('sap_com')
                status = agent_service.tool_collection.get_tool_connection_status('sap_com') or "UNKNOWN"
                
                # Create a response dictionary 
                response = {
                    'status': status,
                    'message': result.text if not result.error else result.error
                }
                
                # Queue the response to be sent in the main thread
                socketio.start_background_task(lambda: socketio.emit('sap_connection_status', response))
            except Exception as e:
                logger.error(f"Error in connect_sap async task: {e}", exc_info=True)
                socketio.start_background_task(lambda: socketio.emit('sap_connection_status', 
                                             {'status': 'DISCONNECTED', 'message': str(e)}))
            
        with app.app_context():
            eventlet.spawn(asyncio.run, connect_sap())
    except Exception as e:
        logger.error(f"Error connecting to SAP2000: {e}", exc_info=True)
        emit('error', {'message': str(e)})
        emit('sap_connection_status', {'status': 'DISCONNECTED', 'message': str(e)})

@socketio.on('load_sap_config')
def handle_load_sap_config(data):
    logger.info('Received load_sap_config request')
    try:
        # Get the config path from frontend
        relative_config_path = data.get('config_path')
        
        # Get project root and construct the absolute config path
        project_root = os.getenv('WORKSPACE_FOLDER')
        if not project_root:
            # If no env var, get current working directory and go up to project root
            current_dir = os.getcwd()
            # If we're in the backend directory, go up one level to project root
            if current_dir.endswith('backend'):
                project_root = os.path.dirname(current_dir)
            else:
                project_root = current_dir
        
        # Remove './' prefix if present and join with project root
        if relative_config_path and relative_config_path.startswith('./'):
            relative_config_path = relative_config_path[2:]
        
        config_path = os.path.join(project_root, relative_config_path) if relative_config_path else None
        logger.info(f'project_root: {project_root}')
        logger.info(f'config_path: {config_path}')
        async def load_config():
            # Get the SAP tool from the tool collection
            tool = agent_service.tool_collection.tool_map.get('sap_com')
            if not tool:
                socketio.emit('error', {'message': 'SAP2000 tool not available'})
                return
                
            # Check if the tool has load_sap_config method dynamically
            load_config_method = getattr(tool, 'load_sap_config', None)
            if not load_config_method or not callable(load_config_method):
                socketio.emit('error', {'message': 'SAP2000 configuration loading not supported'})
                return
                
            result = await load_config_method(config_path) # type: ignore
            socketio.emit('sap_config_status', {
                'success': not result.error,
                'message': result.text if not result.error else result.error
            })
            
        with app.app_context():
            eventlet.spawn(asyncio.run, load_config())
    except Exception as e:
        logger.error(f"Error loading SAP2000 config: {e}", exc_info=True)
        emit('error', {'message': str(e)})
        emit('sap_config_status', {'success': False, 'message': str(e)})

@socketio.on('get_sap_connection_status')
def handle_get_sap_connection_status():
    logger.info('Received get_sap_connection_status request')
    try:
        status = agent_service.tool_collection.get_tool_connection_status('sap_com') or "DISCONNECTED"
        emit('sap_connection_status', {'status': status})
    except Exception as e:
        logger.error(f"Error getting SAP2000 connection status: {e}", exc_info=True)
        emit('error', {'message': str(e)})
        emit('sap_connection_status', {'status': 'UNKNOWN'})

@socketio.on('connect_to_desktop')
def handle_connect_to_desktop():
    logger.info('Received connect_to_desktop request')
    try:
        async def connect_desktop():
            try:
                result = await agent_service.tool_collection.connect_tool('computer')  # type: ignore
                status = agent_service.tool_collection.get_tool_connection_status('computer') or "UNKNOWN"
                
                # Create a response dictionary 
                response = {
                    'status': status,
                    'message': result.text if not result.error else result.error
                }
                
                # Queue the response to be sent in the main thread
                socketio.start_background_task(lambda: socketio.emit('desktop_connection_status', response))
            except Exception as e:
                logger.error(f"Error in connect_desktop async task: {e}", exc_info=True)
                socketio.start_background_task(lambda: socketio.emit('desktop_connection_status', 
                                             {'status': 'DISCONNECTED', 'message': str(e)}))
            
        with app.app_context():
            eventlet.spawn(asyncio.run, connect_desktop())
    except Exception as e:
        logger.error(f"Error connecting to Desktop: {e}", exc_info=True)
        emit('error', {'message': str(e)})
        emit('desktop_connection_status', {'status': 'DISCONNECTED', 'message': str(e)})

@socketio.on('get_desktop_connection_status')
def handle_get_desktop_connection_status():
    logger.info('Received get_desktop_connection_status request')
    try:
        status = agent_service.tool_collection.get_tool_connection_status('computer') or "DISCONNECTED"
        emit('desktop_connection_status', {'status': status})
    except Exception as e:
        logger.error(f"Error getting Desktop connection status: {e}", exc_info=True)
        emit('error', {'message': str(e)})
        emit('desktop_connection_status', {'status': 'UNKNOWN'})

# Template Training handlers
@socketio.on('upload_screenshot')
def handle_upload_screenshot(data):
    """Handle screenshot upload for template training"""
    logger.info('Received upload_screenshot request')
    try:
        image_data = data.get('image')
        agent_name = data.get('agent_name', 'structural-engineer')
        
        # Process screenshot using training agent
        result = training_agent.process_screenshot(image_data, agent_name)
        
        # Emit detection results
        emit('detection_result', {
            'detections': result.get('detections', []),
            'success': True
        })
    except Exception as e:
        logger.error(f"Error processing screenshot: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('save_templates')
def handle_save_templates(data):
    """Save multiple templates from training UI"""
    logger.info('Received save_templates request')
    try:
        image_data = data.get('image')
        agent_name = data.get('agent_name', 'structural-engineer')
        page_name = data.get('page_name', '')
        templates = data.get('templates', [])
        
        # Save each template
        for template in templates:
            training_agent.save_template(
                image_data=image_data,
                caption=template.get('caption', ''),
                bbox=template.get('bbox', []),
                agent_name=agent_name,
                page_name=page_name
            )
        
        emit('templates_saved', {
            'success': True,
            'message': f'Successfully saved {len(templates)} templates'
        })
    except Exception as e:
        logger.error(f"Error saving templates: {e}", exc_info=True)
        emit('templates_saved', {
            'success': False,
            'message': str(e)
        })

@socketio.on('get_screenshots')
def handle_get_screenshots(data):
    """Get screenshots/pages for an agent"""
    logger.info('Received get_screenshots request')
    try:
        agent_name = data.get('agent_name', 'structural-engineer')
        
        screenshots = training_agent.get_screenshots(agent_name)
        
        emit('screenshots_list', {
            'screenshots': screenshots,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error getting screenshots: {e}", exc_info=True)
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