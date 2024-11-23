import asyncio
import logging
import threading
from typing import Any, Dict

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.state = {
            'autoMode': False,
            'highlightMode': False,
            'playing': False,
            'processing': False,
            'currentTask': None
        }
        logger.info("AgentService initialized")

    def _update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update internal state and return the new state"""
        self.state.update(state_update)
        logger.debug(f"State updated: {self.state}")
        return self.state.copy()

    def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state updates and return the new state"""
        logger.info(f"Updating state: {state_update}")
        
        if state_update.get('playing') is False:
            self.stop_processing()
        
        return self._update_state(state_update)

    def process_message(self, message: str) -> Dict[str, Any]:
        """Process message with iteration loop based on auto mode"""
        logger.info(f"Processing new message: {message}")
        self.stop_processing()  # Stop any existing processing
        
        # Update state
        self._update_state({
            'playing': True,
            'processing': True,
            'currentTask': message
        })
        
        # Clear stop event before starting new thread
        self.stop_event.clear()
        
        # Start new processing thread
        self.processing_thread = threading.Thread(
            target=self._process_message_loop,
            args=(message,)
        )
        self.processing_thread.start()
        
        return {
            'type': 'ai',
            'text': f"Starting to process: {message}"
        }

    def _process_message_loop(self, message: str) -> None:
        """Internal method to handle message processing loop"""
        max_iterations = 10 if self.state['autoMode'] else 1
        iteration = 1
        
        try:
            while (iteration <= max_iterations and 
                   not self.stop_event.is_set() and 
                   self.state['processing']):
                
                logger.debug(f"Processing iteration {iteration}/{max_iterations}")
                
                if self.socketio:
                    # Check stop event every second instead of sleeping for 6 seconds
                    for _ in range(6):
                        if self.stop_event.is_set():
                            logger.info("Processing interrupted by stop event")
                            break
                        threading.Event().wait(1.0)  # Non-blocking sleep
                    
                    if not self.stop_event.is_set():
                        self.socketio.emit('response', {
                            'type': 'ai',
                            'text': f"Message {iteration}/{max_iterations}: {message}"
                        })

                iteration += 1

        finally:
            # Ensure state is updated when processing ends
            self._update_state({
                'processing': False,
                'currentTask': None
            })
            logger.info("Message processing completed")

    def stop_processing(self) -> None:
        """Stop current processing loop"""
        if self.processing_thread and self.processing_thread.is_alive():
            logger.info("Stopping active message processing thread")
            self.stop_event.set()
            self._update_state({'playing': False})
            
            self.processing_thread.join(timeout=2.0)
            if self.processing_thread.is_alive():
                logger.warning("Processing thread did not stop within timeout")
            else:
                logger.info("Processing thread successfully stopped")
        else:
            logger.info("No active processing thread to stop")

    def get_state(self) -> Dict[str, Any]:
        """Return the current state"""
        return self.state.copy()