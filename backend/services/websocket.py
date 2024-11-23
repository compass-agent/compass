import logging

from flask_socketio import emit

logger = logging.getLogger(__name__)

class WebSocketService:
    def __init__(self, agent_service):
        self.agent_service = agent_service

    def handle_message(self, response):
        """
        Handle message responses and emit to clients
        """
        logger.info(f"Handling message response: {response}")
        emit('response', response, broadcast=True) 