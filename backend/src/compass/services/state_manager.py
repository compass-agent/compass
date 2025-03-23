from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
from compass.constants import DEFAULT_AGENT_TYPE

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    
class AgentMode(Enum):
    MANUAL = "MANUAL"
    SEMI_AUTO = "SEMI_AUTO"
    AUTO = "AUTO"
    
@dataclass
class AgentState:
    mode: AgentMode = AgentMode.MANUAL
    status: str = AgentStatus.STOPPED.value
    current_task: Optional[str] = None
    pending_tools: int = 0
    agent_type: str = DEFAULT_AGENT_TYPE  # Use default agent type from constants

class StateManager:
    def __init__(self, socketio):
        self._state = AgentState()
        self._socketio = socketio

    def get_state(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return {
            'mode': self._state.mode.value,
            'status': self._state.status,
            'currentTask': self._state.current_task,
            'pendingTools': self._state.pending_tools,
            'agentType': self._state.agent_type
        }

    def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update state from external sources (frontend)"""
        logger.info(f'Update_state state_update: {state_update}')
        if 'status' in state_update:
            self._state.status = state_update['status']
        if 'mode' in state_update:
            self._state.mode = AgentMode[state_update['mode']]
        if 'agentType' in state_update:
            self._state.agent_type = state_update['agentType']
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
        
    def emit_window_minimize(self, action: str) -> None:
        """Minimize Compass app window"""
        self._socketio.emit('minimize-window','minimize')
            
    def emit_window_restore(self, action: str) -> None:
        """Restore Compass app window"""
        self._socketio.emit('restore-window','restore')

    @property
    def mode(self) -> AgentMode:
        return self._state.mode

    @property
    def status(self) -> str:
        return self._state.status

    def set_pending_tools(self, count: int) -> None:
        """Update pending tools count"""
        self._state.pending_tools = count
        self._emit_state_update()

    async def transition_status(self, status: AgentStatus, current_task: Optional[str] = None) -> None:
        """Async version of set_status for use in async contexts"""
        self.set_status(status, current_task)

    def broadcast_scaling_factors(self, x_factor: float, y_factor: float) -> None:
        """Broadcast the current scaling factors to all connected clients."""
        self._socketio.emit('scaling_factors', {
            'x_factor': x_factor,
            'y_factor': y_factor
        })
        logger.info(f"Broadcasting scaling factors: x={x_factor}, y={y_factor}")

    @property
    def agent_type(self) -> str:
        return self._state.agent_type
  