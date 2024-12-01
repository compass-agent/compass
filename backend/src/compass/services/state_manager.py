from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"

@dataclass
class AgentState:
    auto_mode: bool = False
    highlight_mode: bool = False
    playing: bool = False
    status: str = AgentStatus.IDLE.value
    current_task: Optional[str] = None
    pending_tools: int = 0

class StateManager:
    def __init__(self, socketio):
        self._state = AgentState()
        self._socketio = socketio

    def get_state(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return {
            'autoMode': self._state.auto_mode,
            'highlightMode': self._state.highlight_mode,
            'playing': self._state.playing,
            'status': self._state.status,
            'currentTask': self._state.current_task,
            'pendingTools': self._state.pending_tools
        }

    def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update state from external sources (frontend)"""
        if 'autoMode' in state_update:
            self._state.auto_mode = state_update['autoMode']
        if 'highlightMode' in state_update:
            self._state.highlight_mode = state_update['highlightMode']
        if 'playing' in state_update:
            self._state.playing = state_update['playing']
            
        self._emit_state_update()
        return self.get_state()

    def set_status(self, status: AgentStatus, current_task: Optional[str] = None) -> None:
        """Update internal agent status"""
        self._state.status = status.value
        if current_task is not None:
            self._state.current_task = current_task
        self._emit_state_update()

    def _emit_state_update(self) -> None:
        """Emit state update through websocket"""
        self._socketio.emit('state_update', self.get_state())

    def emit_response(self, response: Dict[str, Any]) -> None:
        """Emit agent response"""
        self._socketio.emit('response', response)

    @property
    def auto_mode(self) -> bool:
        return self._state.auto_mode

    @property
    def highlight_mode(self) -> bool:
        return self._state.highlight_mode

    @property
    def status(self) -> str:
        return self._state.status

    def set_pending_tools(self, count: int) -> None:
        """Update pending tools count"""
        self._state.pending_tools = count
        self._emit_state_update()
  