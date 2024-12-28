"""
## States: 

auto_mode: bool (Only FE can set this)
  True: processing message in loop (_process_message_loop)
  False: processing message in single mode (_process_message_single)

highlight_mode: bool (Only FE can set this)
  Condition: it can be active if auto_mode is False
  False: Means the agent only suggests without highlighying/simulating the action in the screen.
  True: Means the agent will highlight/simulate the action in the screen.

pending_tools: int (Only agent can set this)
  This is the number of tools that are pending to be executed.

agent_status: str (Only agent can set this)
  STOPPED: If agent is STOPPED
  RUNNING: If agent is running
  STOPPING: If agent is stopping


## Events

tools_execution:   (FE send this event)
    Active: If agent is 'STOPPED' and automode is False, and pending_tools > 0
    Inactive: O.W.

tools_execution_and_next_step_proposal: (agent send this event)

play: (FE send this event)
    Active: 
      Pause ---> Play: If agent.status is 'STOPPED' and automode is False
         agent.status (in backend) changes to RUNNING
      Play ---> Pause: If agent.status is "Running" 
        agent.status (in backend) changes to STOPPING and then to STOPPED
    Deactive: If agent.status is "STOPPING"

"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"

@dataclass
class AgentState:
    auto_mode: bool = False
    manual_mode: bool = True
    highlight_mode: bool = False
    status: str = AgentStatus.STOPPED.value
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
            'manualMode': self._state.manual_mode,
            'highlightMode': self._state.highlight_mode,
            'status': self._state.status,
            'currentTask': self._state.current_task,
            'pendingTools': self._state.pending_tools
        }

    def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update state from external sources (frontend)"""
        logger.info(f'Update_state state_update: {state_update}')
        if 'autoMode' in state_update:
            self._state.auto_mode = state_update['autoMode']
        if 'highlightMode' in state_update:
            self._state.highlight_mode = state_update['highlightMode']
        if 'status' in state_update:
            self._state.status = state_update['status']
        if 'manualMode' in state_update:
            self._state.manual_mode = state_update['manualMode']
        # QUST?? there is any reason to send state where we have just received it?
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
    def auto_mode(self) -> bool:
        return self._state.auto_mode

    @property
    def highlight_mode(self) -> bool:
        return self._state.highlight_mode
    
    @property
    def manual_mode(self) -> bool:
        return self._state.manual_mode

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
  