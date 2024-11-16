from flask_socketio import emit


class WebSocketService:
    def __init__(self, agent_service):
        self.agent_service = agent_service

    def handle_message(self, response):
        """
        Handle incoming WebSocket messages
        """
        print(f"WebSocketService handling message: {response}")
        emit('response', response)

    def broadcast_state(self, state):
        """
        Broadcast state updates to all clients
        """
        print(f"WebSocketService broadcasting state: {state}")
        emit('state_update', state, broadcast=True) 