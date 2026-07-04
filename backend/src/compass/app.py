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
file_handler = logging.FileHandler(log_file, encoding='utf-8')

# Configure logging first: always log to the AppData file so packaged-app
# issues are diagnosable, and also to the console in development.
if env == 'production':
    logging.basicConfig(level=logging.INFO, handlers=[file_handler])
else:
    logging.basicConfig(level=logging.INFO, handlers=[file_handler, logging.StreamHandler()])
logger = logging.getLogger(__name__)


logger.info(f"Starting backend in {env} environment")
debug_mode = env != 'production'

# Frozen-build runtime setup: seed user data (RAG database) into AppData and
# redirect the comtypes code-generation cache to a writable directory. Must
# run before application modules import comtypes / chromadb.
from compass import runtime_paths

runtime_paths.seed_user_data()
runtime_paths.setup_comtypes_cache()

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
    debug=debug_mode, # type: ignore
    async_handlers=False if os.environ.get('FLASK_DEBUG') == '1' else True,  # Disable async handlers in debug mode
    max_http_buffer_size=int(20 * 1024 * 1024),  # Reduce buffer size
    manage_session=False  # Disable session management if not needed
)

# Now import application modules
from compass.agent.agent import AgentService
from compass.constants import DEFAULT_AGENT_TYPE, LLM_PROVIDER
from compass.key import get_anthropic_api_key, get_google_api_key, get_openai_api_key
from compass.services.state_manager import StateManager
from compass.services.workflow_manager import WorkflowManager
from compass.training_agent.training_agent import TrainingAgent

# Initialize services
state_manager = StateManager(socketio)
workflow_manager = WorkflowManager()
training_agent = TrainingAgent()

# The agent service needs a valid LLM API key. On a fresh install no key is
# configured yet, so initialization is allowed to fail: the backend keeps
# running, reports its status to the UI, and retries once the user has saved
# a key in the onboarding/settings screen.
agent_service = None
agent_service_error = None


def initialize_agent_service():
    """(Re)create the agent service. Returns True on success."""
    global agent_service, agent_service_error
    try:
        agent_service = AgentService(state_manager)
        agent_service_error = None
        logger.info("Agent service initialized successfully")
        return True
    except Exception as e:
        agent_service = None
        agent_service_error = str(e)
        if 'API key' in agent_service_error:
            logger.warning(f"Agent service initialization deferred: {e}")
        else:
            logger.error(f"Agent service initialization failed: {e}", exc_info=True)
        return False


def get_backend_status() -> dict:
    return {
        'llm_ready': agent_service is not None,
        'llm_error': agent_service_error,
        'provider': LLM_PROVIDER,
        'anthropic_key_set': bool(get_anthropic_api_key()),
        'openai_key_set': bool(get_openai_api_key()),
        'google_key_set': bool(get_google_api_key()),
    }


def ensure_agent_service() -> bool:
    """Make sure the agent service exists, retrying init if keys appeared."""
    if agent_service is not None:
        return True
    return initialize_agent_service()


initialize_agent_service()
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
    emit('backend_status', get_backend_status())

@socketio.on('get_backend_status')
def handle_get_backend_status():
    # Retry agent initialization on demand: keys may have been saved since boot.
    if agent_service is None:
        ensure_agent_service()
    emit('backend_status', get_backend_status())

@socketio.on('validate_api_key')
def handle_validate_api_key(data):
    """Check an API key against its provider before saving it."""
    provider = (data or {}).get('provider', 'anthropic')
    api_key = ((data or {}).get('api_key') or '').strip()
    logger.info(f'Received validate_api_key request for provider: {provider}')

    def validate():
        result = {'provider': provider, 'valid': False, 'error': None}
        try:
            if not api_key:
                result['error'] = 'API key is empty'
            elif provider == 'anthropic':
                from anthropic import Anthropic
                Anthropic(api_key=api_key, max_retries=1).models.list(limit=1)
                result['valid'] = True
            elif provider == 'openai':
                from openai import OpenAI
                OpenAI(api_key=api_key, max_retries=1).models.list()
                result['valid'] = True
            else:
                result['error'] = f'Unknown provider: {provider}'
        except Exception as e:
            message = str(e)
            if 'authentication' in message.lower() or '401' in message:
                result['error'] = 'Invalid API key'
            else:
                result['error'] = message
        socketio.start_background_task(
            lambda: socketio.emit('api_key_validation', result))

    eventlet.spawn(validate)

@socketio.on('initialize_agent')
def handle_initialize_agent():
    """Re-initialize the agent service (e.g. after API keys were saved)."""
    logger.info('Received initialize_agent request')
    initialize_agent_service()
    emit('backend_status', get_backend_status())

@socketio.on('disconnect')
def handle_disconnect(reason):
    logger.info(f'Client disconnected with sid: {request.sid}')  # type: ignore

NOT_CONFIGURED_MESSAGE = (
    "The AI agent is not configured yet. Please add your Anthropic API key "
    "in Settings and try again."
)

@socketio.on('message')
def handle_message(data):
    try:
        logger.info("Handling new message")
        if not ensure_agent_service():
            emit('backend_status', get_backend_status())
            emit('error', {'message': NOT_CONFIGURED_MESSAGE})
            return
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
        if not ensure_agent_service():
            emit('backend_status', get_backend_status())
            emit('error', {'message': NOT_CONFIGURED_MESSAGE})
            return
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
        agent_name = data.get('agent_name') or DEFAULT_AGENT_TYPE  # Use default from constants if not specified
        state_manager.update_state({'agentType': agent_name})

        # Reinitialize just the agent service
        if initialize_agent_service():
            emit('chat_reset', {'status': 'success'})
        else:
            emit('backend_status', get_backend_status())
            emit('error', {'message': NOT_CONFIGURED_MESSAGE})
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
        if not ensure_agent_service():
            emit('backend_status', get_backend_status())
            emit('sap_connection_status', {'status': 'DISCONNECTED', 'message': NOT_CONFIGURED_MESSAGE})
            return
        emit('sap_connection_status', {'status': 'CONNECTING', 'message': 'Connecting to SAP2000...'})
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
        if not ensure_agent_service():
            emit('backend_status', get_backend_status())
            emit('sap_config_status', {'success': False, 'message': NOT_CONFIGURED_MESSAGE})
            return
        # Get the config path from frontend
        relative_config_path = data.get('config_path')
        
        # Get project root and construct the absolute config path.
        # Absolute paths from the frontend are used as-is (os.path.join
        # ignores project_root when the second part is absolute).
        project_root = str(runtime_paths.get_workspace_dir())

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
        if agent_service is None:
            emit('sap_connection_status', {'status': 'DISCONNECTED'})
            return
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
        if not ensure_agent_service():
            emit('backend_status', get_backend_status())
            emit('desktop_connection_status', {'status': 'DISCONNECTED', 'message': NOT_CONFIGURED_MESSAGE})
            return
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
        if agent_service is None:
            emit('desktop_connection_status', {'status': 'DISCONNECTED'})
            return
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
        agent_name = data.get('agent_name', None)
        
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
        agent_name = data.get('agent_name', None)
        page_name = data.get('page_name', '')
        templates = data.get('templates', [])
        
        # Save all templates at once (page saved once inside the method)
        training_agent.save_template(
            image_data=image_data,
            templates=templates,
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

@socketio.on('get_agents')
def handle_get_agents(data=None):
    """Get list of available agents"""
    logger.info('Received get_agents request')
    try:
        agents = training_agent.list_agents()
        
        emit('agents_list', {
            'agents': agents,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error getting agents: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('agent_hub')
def handle_agent_hub(data):
    """Handle Agent Hub CRUD/import/export actions."""
    action = (data or {}).get('action')
    logger.info(f'Received agent_hub action: {action}')
    response = {'action': action, 'success': False}

    try:
        if action == 'list':
            response.update({
                'success': True,
                'agents': training_agent.list_agents(),
            })
        elif action == 'create':
            agent = training_agent.create_agent(data or {})
            response.update({'success': True, 'agent': agent})
        elif action == 'update':
            agent_id = (data or {}).get('agentId')
            agent = training_agent.update_agent(agent_id, data or {})
            response.update({'success': True, 'agent': agent})
        elif action == 'import':
            agent = training_agent.import_agent((data or {}).get('importData') or '')
            response.update({'success': True, 'agent': agent})
        elif action == 'export':
            export_data = training_agent.export_agent((data or {}).get('agentId'))
            response.update({'success': True, **export_data})
        elif action == 'delete':
            result = training_agent.delete_agent((data or {}).get('agentId'))
            response.update({
                'success': True,
                'agentId': result['agentId'],
                'message': result['agentName'],
                'pagesDeleted': result['pagesDeleted'],
                'templatesDeleted': result['templatesDeleted'],
            })
        else:
            response['message'] = f'Unknown Agent Hub action: {action}'
    except Exception as e:
        logger.error(f"Agent Hub action failed: {e}", exc_info=True)
        response['message'] = str(e)

    emit('agent_hub_result', response)

@socketio.on('get_screenshots')
def handle_get_screenshots(data):
    """Get screenshots/pages for an agent"""
    logger.info('Received get_screenshots request')
    try:
        agent_name = data.get('agent_name', None)
        
        screenshots = training_agent.get_screenshots(agent_name)
        
        emit('screenshots_list', {
            'screenshots': screenshots,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error getting screenshots: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('delete_page')
def handle_delete_page(data):
    """Delete a training page and associated templates."""
    logger.info('Received delete_page request')
    try:
        page_id = (data or {}).get('pageId')
        result = training_agent.delete_page(page_id)
        emit('delete_page_result', {
            'success': True,
            **result,
        })
    except Exception as e:
        logger.error(f"Error deleting page: {e}", exc_info=True)
        emit('delete_page_result', {
            'success': False,
            'pageId': (data or {}).get('pageId'),
            'message': str(e),
        })

if __name__ == '__main__':
    try:
        socketio.run(app,
            host='0.0.0.0',
            debug=debug_mode,
            port=5001,
            use_reloader=False,
            log_output=debug_mode)
    except KeyboardInterrupt:
        cleanup()
