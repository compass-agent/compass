import signal
import sys
from flask import Flask
from flask_socketio import SocketIO, emit # type: ignore
from compass.agent.agent import AgentService
from compass.services.state_manager import StateManager
from compass.utils.utility import HistoryLogger
import logging
import asyncio
from threading import Thread

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object('compass.config.config.Config')

socketio = SocketIO(app, 
    cors_allowed_origins="*",
    async_mode='threading',  # Back to threading mode
    logger=False,
    engineio_logger=False,
    debug=False)

# Create a new event loop for the background thread
async_loop = asyncio.new_event_loop()

def run_event_loop_in_thread(loop):
    """Sets up and runs the event loop in a separate thread"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Start the event loop in a background thread
background_thread = Thread(target=run_event_loop_in_thread, args=(async_loop,), daemon=True)
background_thread.start()

state_manager = StateManager(socketio)
agent_service = AgentService(state_manager)

def run_async(coro):
    """Helper function to run coroutines in the background event loop"""
    try:
        future = asyncio.run_coroutine_threadsafe(coro, async_loop)
        return future.result()
    except Exception as e:
        logger.error(f"Error in async execution: {e}", exc_info=True)
        raise

def cleanup():
    """Cleanup function to handle graceful shutdown"""
    logger.info('Shutting down gracefully...')
    try:
        async def cleanup_tasks():
            tasks = asyncio.all_tasks(async_loop)
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        
        future = asyncio.run_coroutine_threadsafe(cleanup_tasks(), async_loop)
        future.result(timeout=5.0)
        
        async_loop.call_soon_threadsafe(async_loop.stop)
        background_thread.join(timeout=5.0)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
    finally:
        socketio.stop()
        sys.exit(0)

def signal_handler(sig, frame):
    cleanup()

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
    try:
        run_async(agent_service.process_message(data.get('text', '')))
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
        
@socketio.on('stop_processing')
def handle_stop_processing():
    logger.info('Stop processing request received')
    try:
        run_async(agent_service.stop_processing())
    except Exception as e:
        logger.error(f"Error in handle_stop_processing: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('execute_next_tool')
def handle_execute_next_tool():
    logger.info('Received execute_next_tool request')
    try:
        run_async(agent_service.execute_next_pending_tool())
    except Exception as e:
        logger.error(f"Error executing tool: {e}", exc_info=True)
        emit('error', {'message': str(e)})

@socketio.on('generate_next_action')
def handle_generate_next_action():
    logger.info('Received generate_next_action request')
    try:
        run_async(agent_service.process_next_action())
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
        cleanup() 