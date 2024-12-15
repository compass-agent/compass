import logging
import asyncio
from typing import Any, cast

from anthropic.types.beta import (
    BetaImageBlockParam,
    BetaMessageParam,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from compass.tools import ComputerTool, ToolCollection, ToolResult
from compass.constants import MAX_ITERATIONS
from compass.utils.utility import HistoryLogger, log_execution_time
from compass.services.state_manager import StateManager, AgentStatus
from compass.agent.llm import LLM

logger = logging.getLogger(__name__)


def _make_api_tool_result(
    result: ToolResult, tool_use_id: str
) -> BetaToolResultBlockParam:
    """Convert an agent ToolResult to an API ToolResultBlockParam."""
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = _maybe_prepend_system_tool_result(result, result.error)
    else:
        if result.output:
            tool_result_content.append(
                {
                    "type": "text",
                    "text": _maybe_prepend_system_tool_result(result, result.output),
                }
            )
        if result.base64_image:
            tool_result_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": result.base64_image,
                    },
                }
            )
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text


class AgentService:
    def __init__(self, state_manager: StateManager):
        logger.info("Initializing Agent")
        self.state_manager = state_manager

        self.processing_task = None
        self.stop_event = asyncio.Event()
        self.messages: list[BetaMessageParam] = []

        self.history_tracker = HistoryLogger()

        self.tool_collection = ToolCollection(ComputerTool(state_manager))
        self.llm = LLM(self.tool_collection.to_params())

        self.pending_tool_queue = []
        self.recording_iteration = 0
        logger.info("Agent successfully initialized")
        # self._mock_enabled = False

    def _append_message(self, message: BetaMessageParam) -> None:
        """Helper method to append message and save messages state"""
        self.messages.append(message)
        self.history_tracker.save_messages(self.messages, self.recording_iteration)
        logger.info(f"Saved messages for iteration {self.recording_iteration} as a json file")
        self.recording_iteration += 1

    async def process_message(self, message: str) -> None:
        """Process message with iteration loop based on auto mode"""
        logger.info(f"New message received: {message}")
        await self.stop_processing()

        self._append_message(
            {"role": "user", "content": [{"type": "text", "text": message}]}
        )
        self.state_manager.set_status(AgentStatus.RUNNING, message)
        self.stop_event.clear()

        logger.info("Taking screenshot and cursor position before calling AI")
        await self._take_screenshot()

        if self.state_manager.auto_mode:
            self.processing_task = asyncio.create_task(
                self._process_message_loop()
            )
        else:
            self.processing_task = asyncio.create_task(
                self._process_message_single_mode()
            )

    async def _process_message_single_mode(self, *args, **kwargs) -> None:
        try:
            response_params = await self._next_step_proposal()
            if self.state_manager.highlight_mode:
                response_params = [
                    block for block in response_params if block["type"] == "text"
                ]
                logger.info(f"Skipping tool proposals since in highlight mode")
            else:
                logger.info(
                    f"Storing {len(response_params) - 1} tool proposals in queue"
                )
                self._store_pending_tool_proposals(response_params)
        finally:
            logger.info("Setting status to IDLE, clearing stop event, and cleaning up task")
            self.state_manager.set_status(AgentStatus.IDLE)
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
                
                response_params = await self._next_step_proposal()
                self._append_message({"role": "assistant", "content": response_params})

                tool_blocks = [
                    block for block in response_params if block["type"] == "tool_use"
                ]
                if not tool_blocks:
                    break

                tool_result_content = await self._execute_tools(tool_blocks)
                if tool_result_content:
                    self._append_message(
                        {"role": "user", "content": tool_result_content}
                    )
                iteration += 1
        except asyncio.CancelledError:
            logger.info("Message processing loop was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in message processing loop: {e}")
        finally:
            self.state_manager.set_status(AgentStatus.IDLE)
            self.stop_event.clear()
            self.processing_task = None
            logger.info("Message processing loop completed and cleaned up")

    def _store_pending_tool_proposals(self, response_params):
        """Store tool proposals for later execution"""
        for block in response_params:
            if block["type"] == "tool_use":
                logger.info(f"Tool action: {block['input']}")
                self.pending_tool_queue.append(block)
        self.state_manager.set_pending_tools(len(self.pending_tool_queue))

    @log_execution_time(logger)
    async def _execute_tools(self, tool_blocks: list[BetaToolUseBlockParam]) -> list[BetaToolResultBlockParam]:
        """Common method to execute a list of tools and collect results"""
        tool_result_content: list[BetaToolResultBlockParam] = []
        
        # log the list of tool blocks expected to be executed:
        for content_block in tool_blocks:
            logger.info(f"Expected to execute tool: {content_block['name']} with input: {content_block['input']}")
        for content_block in tool_blocks:
            self.state_manager.emit_response({
                "type": "tool_use",
                "parameters": content_block["input"]
            })
            logger.info(f"Executing tool: {content_block['name']} with input: {content_block['input']}")
            result = await self.tool_collection.run(
                name=content_block["name"],
                tool_input=cast(dict[str, Any], content_block["input"]),
            )

            tool_result = _make_api_tool_result(result, content_block["id"])
            tool_result_content.append(tool_result)

            # Emit individual result
            self.state_manager.emit_response(
                {"type": "tool_result", "content": tool_result}
            )

        return tool_result_content

    async def execute_next_pending_tool(self):
        if not self.pending_tool_queue:
            logger.info("No pending tools to execute")
            return

        self.state_manager.set_status(AgentStatus.RUNNING)
        try:
            tool_result_content = await self._execute_tools(self.pending_tool_queue)
            self.pending_tool_queue.clear()

            if tool_result_content:
                self._append_message({"role": "user", "content": tool_result_content})

        finally:
            self.state_manager.set_status(AgentStatus.IDLE)
            self.state_manager.set_pending_tools(0)

    async def process_next_action(self):
        """Generate the next action without executing tools"""
        if not self.processing_task or self.processing_task.done():
            self.processing_task = asyncio.create_task(
                self._process_message_single_mode(None)
            )
        else:
            logger.info("Agent is already processing")

    async def _next_step_proposal(self):
        response_params = await self.llm.call(self.messages, self.state_manager.highlight_mode) 
        for content_block in response_params:
            if content_block["type"] == "text":
                self.state_manager.emit_response(
                    {"type": "ai_response", "content": content_block["text"]}
                )
        return response_params

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
            
            self.state_manager.set_status(AgentStatus.IDLE)
        else:
            logger.info("No active processing task to stop")
            self.state_manager.set_status(AgentStatus.IDLE)

    @log_execution_time(logger)
    async def _take_screenshot(self) -> None:
        """Takes a screenshot and adds cursor position to the message history"""
        try:
            self._append_message({
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "computer",
                        "id": f"tool_screenshot_{len(self.messages)}",
                        "input": {"action": "screenshot"}
                    }
                ]
            })
            
            result = await self.tool_collection.run(
                name="computer",
                tool_input={"action": "screenshot"}
            )

            self._append_message({
                "role": "user",
                "content": [
                    _make_api_tool_result(
                        result=result,
                        tool_use_id=f"tool_screenshot_{len(self.messages)-1}"
                    )
                ]
            })
            
            logger.info("Screenshot with cursor position captured and added to message history")
        except Exception as e:
            logger.error(
                f"Failed to take initial screenshot due to the following error, skipping this step: {e}"
            )
