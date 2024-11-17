import asyncio
import threading
from time import sleep


class AgentService:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.current_task = None
        self.is_running = False
        self.state = {
            'is_auto_mode': False,
            'is_highlight_mode': False,
            'is_playing': False,
            'is_processing': False,
            'current_task': None
        }
        self.processing_thread = None

    def process_message(self, message):
        """
        Process message with iteration loop based on auto mode
        """
        # Stop any existing processing
        self.stop_processing()
        
        # Set playing state to True when starting new message
        self.state['is_playing'] = True
        self.state['is_processing'] = True
        
        print(f"Current state before processing: {self.state}")  # Debug print
        
        # Start new processing thread
        self.processing_thread = threading.Thread(
            target=self._process_message_loop,
            args=(message,)
        )
        self.processing_thread.start()
        
        # Return initial message
        return {
            'type': 'ai',
            'text': f"Starting to process: {message}"
        }

    def _process_message_loop(self, message):
        """
        Internal method to handle message processing loop
        """
        self.state['is_processing'] = True
        max_iterations = 10 if self.state['is_auto_mode'] else 1
        iteration = 1

        print(f"Starting loop - Auto mode: {self.state['is_auto_mode']}, Max iterations: {max_iterations}")
        
        while (iteration <= max_iterations and 
               self.state['is_playing'] and 
               self.state['is_processing']):
            
            print(f"Processing iteration {iteration}/{max_iterations}")
            print(f"State: playing={self.state['is_playing']}, processing={self.state['is_processing']}")
            
            # Use socketio instance instead of emit directly
            if self.socketio:
                self.socketio.emit('response', {
                    'type': 'ai',
                    'text': f"Message {iteration}/{max_iterations}: {message}"
                })

            iteration += 1
            if iteration <= max_iterations:
                # Break the sleep into smaller chunks to check state more frequently
                for _ in range(3):  # 3 seconds total, checking every second
                    if not self.state['is_playing'] or not self.state['is_processing']:
                        print("Loop interrupted by pause")
                        break
                    sleep(1)
                if not self.state['is_playing'] or not self.state['is_processing']:
                    break

        print("Loop ended")
        self.state['is_processing'] = False
        if self.socketio:
            self.socketio.emit('state_update', self.state)

    def stop_processing(self):
        """
        Stop current processing loop
        """
        print("Stopping processing...")  # Debug print
        self.state['is_processing'] = False
        self.state['is_playing'] = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish

    def update_state(self, state_update):
        """
        Handle state updates from the frontend
        """
        print(f"AgentService updating state: {state_update}")
        # Convert frontend keys to backend keys
        key_mapping = {
            'auto_mode': 'is_auto_mode',
            'highlight_mode': 'is_highlight_mode',
            'playing': 'is_playing'
        }
        
        for key, value in state_update.items():
            backend_key = key_mapping.get(key, key)
            if backend_key in self.state:
                self.state[backend_key] = value
                print(f"Updated {backend_key} to {value}")  # Debug print
                
                # Stop processing if paused
                if backend_key == 'is_playing' and not value:
                    self.stop_processing()
        
        # Emit state update after changes
        if self.socketio:
            self.socketio.emit('state_update', self.state)
        
        print(f"Final state after update: {self.state}")  # Debug print
        return self.state 