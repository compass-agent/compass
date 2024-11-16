class AgentService:
    def __init__(self):
        self.current_task = None
        self.is_running = False
        self.state = {
            'is_auto_mode': False,
            'is_highlight_mode': False,
            'is_playing': False,
            'current_task': None
        }

    def process_message(self, message):
        """
        Mock message processing
        """
        print(f"AgentService processing message: {message}")
        return {
            'type': 'ai',
            'text': f"Mock processing of: {message}"
        }

    def update_state(self, state_update):
        """
        Handle state updates from the frontend
        """
        print(f"AgentService updating state: {state_update}")
        # Update internal state
        for key, value in state_update.items():
            if key in self.state:
                self.state[key] = value
        return self.state 