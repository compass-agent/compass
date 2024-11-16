import logging

from flask_socketio import emit

# Configure logger for this module
logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self, agent_service):
        self.agent_service = agent_service
        logger.info("WebSocketService initialized")

    def handle_message(self, response):
        """
        Handle incoming WebSocket messages
        """
        logger.info(f"Handling WebSocket message: {response}")
        emit('response', response)

    def broadcast_state(self, state):
        """
        Broadcast full state updates to all clients
        """
        # Fetch the full state from agent_service
        full_state = self.agent_service.get_full_state()
        logger.info(f"Broadcasting full state update: {full_state}")
        emit('state_update', full_state, broadcast=True) 