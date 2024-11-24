import logging

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self, socketio):
        self.socketio = socketio

    def handle_message(self, response):
        """Handle message responses and emit to clients"""
        logger.info(f"Handling message response: {response}")
        self.socketio.emit('response', response)

    def emit_state_update(self, state):
        """Emit state updates to clients"""
        logger.info(f"Emitting state update: {state}")
        self.socketio.emit('state_update', state) 