import logging
import asyncio
from typing import Any, cast, Union

from compass.tools import BashExecutor, ToolCollection, ComputerTool, FileOperationsTool
from compass.constants import MAX_ITERATIONS, PRE_RUN_SCREENSHOTS, AGENT_NAME, AGENT_TOOLS
from compass.utils.utility import HistoryLogger, log_execution_time
from compass.services.state_manager import StateManager, AgentStatus, AgentMode
from compass.types.agent import SystemMessage, HumanMessage, AIMessage, ToolCall
from compass.llm.anthropic_llm import AnthropicLLM
from compass.llm.memory_management import MemoryManager
from compass.agent.prompt import get_prompt_handler

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, state_manager: StateManager):
        logger.info("Initializing Agent")
        self.state_manager = state_manager
        self.processing_task = None
        self.stop_event = asyncio.Event()
        self.messages: list[Union[SystemMessage, HumanMessage, AIMessage]] = []
        self.history_tracker = HistoryLogger()
        self.memory_manager = MemoryManager(self.history_tracker)
        self.tool_collection = ToolCollection(
            ComputerTool(state_manager), 
            FileOperationsTool(), 
            BashExecutor()
        )
        self.system_prompt = get_prompt_handler(AGENT_NAME)
        # TODO: pass in system message and tools params
        self.llm = AnthropicLLM(self.memory_manager, self.tool_collection.to_params())

        self.pending_tool_queue = []
        self.recording_iteration = 0
        logger.info("Agent successfully initialized")
        # self._mock_enabled = False

        # Configure tools based on agent type
        tools = []
        agent_tool_config = AGENT_TOOLS.get(AGENT_NAME, ["computer", "file", "bash"])  # Default to all tools
        
        if "computer" in agent_tool_config:
            tools.append(ComputerTool(state_manager))
        if "file" in agent_tool_config:
            tools.append(FileOperationsTool())
        if "bash" in agent_tool_config:
            tools.append(BashExecutor())
        
        self.tool_collection = ToolCollection(*tools)


    async def process_message(self, message: str) -> None:
        """Process message with iteration loop based on auto mode"""
        logger.info(f"New message received: {message}")
        await self.stop_processing()

        # Skip appending empty messages if last message was from user
        if not message:
            logger.info("Skipping empty user message since last message was from user")
        else:
            self.memory_manager.add_message(
                HumanMessage(content=message)
            )
        self.state_manager.set_status(AgentStatus.RUNNING, message)
        self.stop_event.clear()

        logger.info("Taking screenshot and cursor position before calling AI")
        if PRE_RUN_SCREENSHOTS:
            await self._take_screenshot()

        if self.state_manager.mode == AgentMode.AUTO:
            self.processing_task = asyncio.create_task(self._process_message_loop())
        else:
            self.processing_task = asyncio.create_task(self._process_message_single_mode())

    async def _process_message_single_mode(self, *args, **kwargs) -> None:
        try:
            tool_calls = await self._next_step_proposal()
            for tool_call in tool_calls:
                self.pending_tool_queue.append(tool_call)
            self.state_manager.set_pending_tools(len(self.pending_tool_queue))
            logger.info(f"Pending tool queue: {self.pending_tool_queue}")
        except Exception as e: # FIXME: handle this better
            logger.error(f"Error in _process_message_single_mode: {e}")
        finally:
            logger.info(
                "Setting status to STOPPED, clearing stop event, and cleaning up task"
            )
            self.state_manager.set_status(AgentStatus.STOPPED)
            self.stop_event.clear()
            self.processing_task = None
            logger.info("Single mode processing completed and cleaned up")

    async def _process_message_loop(self) -> None:
        """Internal method to handle message processing loop"""
        logger.info("Starting to process message in loop mode")
        iteration = 1
        try:
            while (
                iteration <= MAX_ITERATIONS
                and not self.stop_event.is_set()
                and self.state_manager.status == AgentStatus.RUNNING.value
            ):
                logger.debug(f"Processing iteration {iteration}/{MAX_ITERATIONS}")
                logger.info(f"Processing iteration {iteration} status {self.state_manager.status}")
                tool_calls = await self._next_step_proposal()
                if not tool_calls:
                    break
                await self._execute_tools(tool_calls)
                iteration += 1
        except asyncio.CancelledError:
            logger.info("Message processing loop was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in message processing loop: {e}")
        finally:
            self.state_manager.set_status(AgentStatus.STOPPED)
            self.stop_event.clear()
            self.processing_task = None
            logger.info("Message processing loop completed and cleaned up")

    @log_execution_time(logger)
    async def _execute_tools( 
        self, tool_calls: list[ToolCall]
    ):
        """Common method to execute a list of tools and collect results"""
        for tool_call in tool_calls:
            logger.info(f"Expected to execute tool: {tool_call.name} with input: {tool_call.args}")
        for tool_call in tool_calls: 
            logger.info(f"Executing tool: {tool_call.name} with input: {tool_call.args}")
            tool_result = await self.tool_collection.run(tool_call)
            self.memory_manager.add_message(AIMessage(tool_calls=[tool_call]))
            self.memory_manager.add_message(tool_result)
            self.state_manager.emit_response({
                "type": "tool_result",
                "toolUseId": tool_call.tool_call_id,
                "content": tool_result.text,
                "isError": tool_result.error is not None
            })

    async def execute_all_pending_tools(self):
        if not self.pending_tool_queue:
            logger.info("No pending tools to execute")
            return
        self.state_manager.set_status(AgentStatus.RUNNING)
        try:
            await self._execute_tools(self.pending_tool_queue)
            self.pending_tool_queue.clear()
        finally:
            self.state_manager.set_status(AgentStatus.STOPPED)
            self.state_manager.set_pending_tools(0)

    async def process_next_action(self): # TBR
        if not self.processing_task or self.processing_task.done():
            self.processing_task = asyncio.create_task(
                self._process_message_single_mode(None)
            )
        else:
            logger.info("Agent is already processing")

    async def _next_step_proposal(self) -> list[ToolCall]:
        system_message = self.system_prompt.get_system_prompt(
            manual_mode=self.state_manager.mode == AgentMode.MANUAL, 
            highlight_mode=False)
        
        response = self.llm.stream_call(system_message, manual_mode=self.state_manager.mode == AgentMode.MANUAL)
        text_response_content = []
        tool_calls = []
        
        for chunk in response:
            if isinstance(chunk, str):
                text_response_content.append(chunk)
                self.state_manager.emit_response({
                    "type": "ai_response",
                    "content": chunk,
                    #"is_final": False
                })
                logger.info(f"AI response stream: {chunk}")
            elif isinstance(chunk, ToolCall):
                tool_calls.append(chunk)
                logger.info(f"Tool call chunk: {chunk}")
        
        # if text_response_content:
        #     self.state_manager.emit_response({
        #         "type": "ai_response_stream",
        #         "content": "",
        #         "is_final": True
        #     })
        
        if tool_calls:
            tool_use_group = {
                "type": "tool_use_group",
                "tools": [{
                    "id": tool.tool_call_id,
                    "name": tool.name,
                    "input": tool.args
                } for tool in tool_calls]
            }
            logger.info(f"Emitting tool use group: {tool_use_group}")
            self.state_manager.emit_response(tool_use_group)
        
        self.memory_manager.add_message(AIMessage(content="".join(text_response_content)))
        return tool_calls
    

    async def stop_processing(self) -> None:
        """Stop current processing loop"""
        logger.info("Attempting to stop processing task if it exists")
        if self.processing_task and not self.processing_task.done():
            logger.info(f"Stopping active message processing task: {self.processing_task}")
            self.stop_event.set()
            self.state_manager.set_status(AgentStatus.STOPPING)
            try:
                await asyncio.wait_for(self.processing_task, timeout=6.0)
                logger.info("Processing task successfully stopped")
            except asyncio.TimeoutError:
                logger.error("Failed to stop task within timeout")
            self.state_manager.set_status(AgentStatus.STOPPED)
        else:
            logger.info("No active processing task to stop")
            self.state_manager.set_status(AgentStatus.STOPPED)

    @log_execution_time(logger)
    async def _take_screenshot(self) -> None:
        """Takes a screenshot and adds cursor position to the message history"""
        try:
            tool_call = ToolCall(name="computer", args={"action": "screenshot"}, tool_call_id=f"tool_screenshot_{len(self.messages)}")
            tool_result = await self.tool_collection.run(tool_call)
            self.memory_manager.add_message(AIMessage(tool_calls=[tool_call]))
            self.memory_manager.add_message(tool_result)
            logger.info("Taking auto screenshot")
        except Exception as e:
            logger.error(f"Failed to take initial screenshot [skipping]: {e}")
