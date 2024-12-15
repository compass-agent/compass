import signal
import sys
from flask import Flask
from flask_socketio import SocketIO, emit # type: ignore
from compass.agent.agent import AgentService
from compass.services.state_manager import StateManager
from compass.utils.utility import HistoryLogger
import logging
import asyncio
from functools import partial

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object('compass.config.config.Config')

socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    debug=False)

state_manager = StateManager(socketio)
agent_service = AgentService(state_manager)

def signal_handler(sig, frame):
    logger.info('Shutting down gracefully...')
    socketio.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('status', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('message')
def handle_message(data):
    try:
        asyncio.run(agent_service.process_message(data.get('text', '')))
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('control_update')
def handle_control_update(data):
    logger.info(f'Control update received: {data}')
    try:
        state_manager.update_state(data)
    except Exception as e:
        logger.error(f"Error in handle_control_update: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('execute_next_tool')
def handle_execute_next_tool():
    logger.info('Received execute_next_tool request')
    try:
        asyncio.run(agent_service.execute_next_pending_tool())
    except Exception as e:
        logger.error(f"Error executing tool: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('generate_next_action')
def handle_generate_next_action():
    logger.info('Received generate_next_action request')
    try:
        asyncio.run(agent_service.process_next_action())
    except Exception as e:
        logger.error(f"Error generating next action: {e}", exc_info=True)
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