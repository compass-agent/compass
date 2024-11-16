import asyncio
import logging
import threading
from time import sleep
from typing import Any, Dict

# Configure logger for this module
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.processing_thread = None
        # Add state management
        self.state = {
            'autoMode': False,
            'highlightMode': False,
            'playing': False,
            'processing': False,
            'currentTask': None
        }
        logger.info("AgentService initialized")

    def _update_state(self, state_update: Dict[str, Any]) -> None:
        """Update internal state and emit update through socketio"""
        # Update internal state
        self.state.update(state_update)
        
        if self.socketio:
            logger.debug(f"Emitting state update: {state_update}")
            self.socketio.emit('state_update', state_update)

    def _get_state(self, key: str) -> Any:
        """Get current state from internal state"""
        logger.debug(f"Getting state for key: {key}")
        return self.state.get(key)

    def _get_full_state(self) -> Dict[str, Any]:
        """Get full current state"""
        logger.debug("Getting full state")
        return self.state.copy()

    def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state updates from the frontend"""
        logger.info(f"Updating state: {state_update}")
        self._update_state(state_update)
        
        if state_update.get('playing') is False:
            self.stop_processing()
            
        return self._get_full_state()

    def get_full_state(self) -> Dict[str, Any]:
        """Get full current state"""
        logger.debug("Getting full state")
        return self.state.copy()

    def process_message(self, message: str) -> Dict[str, Any]:
        """Process message with iteration loop based on auto mode"""
        logger.info(f"Processing new message: {message}")
        self.stop_processing()
        
        # Update state
        self._update_state({
            'playing': True,
            'processing': True
        })
        
        # Start new processing thread
        self.processing_thread = threading.Thread(
            target=self._process_message_loop,
            args=(message,)
        )
        self.processing_thread.start()
        logger.info("Started new processing thread")
        
        return {
            'type': 'ai',
            'text': f"Starting to process: {message}"
        }

    def _process_message_loop(self, message: str) -> None:
        """Internal method to handle message processing loop"""
        max_iterations = 10 if self._get_state('autoMode') else 1
        iteration = 1
        
        logger.info(f"Starting message loop - playing: {self._get_state('playing')}, processing: {self._get_state('processing')}, autoMode: {self._get_state('autoMode')}")
        
        while (iteration <= max_iterations and 
               self._get_state('playing') and 
               self._get_state('processing')):
            
            logger.debug(f"Processing iteration {iteration}/{max_iterations}")
            if self.socketio:
                # Simulate LLM processing time
                sleep(6)  # Add 3-second delay before response
                self.socketio.emit('response', {
                    'type': 'ai',
                    'text': f"Message {iteration}/{max_iterations}: {message}"
                })

            iteration += 1
            if iteration <= max_iterations:
                for _ in range(3):
                    if not self._get_state('playing') or not self._get_state('processing'):
                        logger.info(f"Processing interrupted - playing: {self._get_state('playing')}, processing: {self._get_state('processing')}")
                        break
                    sleep(1)
                if not self._get_state('playing') or not self._get_state('processing'):
                    break

        logger.info("Message processing completed")
        self._update_state({'processing': False})

    def stop_processing(self) -> None:
        """Stop current processing loop"""
        if self.processing_thread and self.processing_thread.is_alive():
            logger.info("Stopping active message processing thread")
            # Only update playing state, keep processing true
            self._update_state({
                'playing': False
            })
            
            self.processing_thread.join(timeout=1.0)
            if self.processing_thread.is_alive():
                logger.warning("Processing thread did not stop within timeout")
            else:
                logger.info("Processing thread successfully stopped")
        else:
            logger.info("No active processing thread to stop")