import logging
import threading
from typing import Any, Dict, Optional
from enum import StrEnum, Enum
from typing import Any, cast
from anthropic import (
    Anthropic,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)
import time

from compass.tools import ComputerTool, ToolCollection, ToolResult
from compass.key import ANTHROPIC_API_KEY
from compass.agent.prompt import get_system_prompt
from compass.constants import (
    MODEL_NAME,
    MAX_TOKENS,
    PROMPT_CACHING,
    MAX_ITERATIONS,
    COMPUTER_USE_BETA_FLAG,
    PROMPT_CACHING_BETA_FLAG
)
from compass.utils.utility import HistoryLogger, TokenTracker, log_execution_time
from compass.services.state_manager import StateManager, AgentStatus

logger = logging.getLogger(__name__)


def _response_to_params(
    response: BetaMessage,
) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
    res: list[BetaTextBlockParam | BetaToolUseBlockParam] = []
    for block in response.content:
        if isinstance(block, BetaTextBlock):
            res.append({"type": "text", "text": block.text})
        else:
            res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    return res



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

def mock_llm_response(func):
    """Decorator to mock LLM responses during development"""
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_mock_enabled') or not self._mock_enabled:
            return func(self, *args, **kwargs)
            
        # Mock response for development
        return [
            {
                'type': 'text',
                'text': "I see Slack is already open. I'll help you send a message to Sina. Let me click on Sina's name in the Direct messages section first."
            },
            {
                'type': 'tool_use',
                'name': 'computer',
                'id': 'toolu_01XXGSseiucNjr9VDUvw9mTD',
                'input': {
                    'action': 'mouse_move',
                    'coordinate': [94, 462]
                }
            }
        ]
    return wrapper

class AgentService:
    def __init__(self, state_manager: StateManager, history_logger: HistoryLogger):
        logger.info("Initializing Agent")
        self.state_manager = state_manager
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.messages: list[BetaMessageParam] = []
        
        # Initialize beta flags and client
        self.betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)
        # Use provided history_logger
        self.history_tracker = history_logger
        
        # Initialize token tracker
        self.token_tracker = TokenTracker()
        
        # Pass history tracker to ComputerTool
        self.tool_collection = ToolCollection(ComputerTool(history_tracker=self.history_tracker))
        self.tools_params = self.tool_collection.to_params()
        logger.info(f"Tools params: {self.tools_params}")
        self.pending_tool_queue = []
        logger.info("Agent successfully initialized")
        self._mock_enabled = False  # Add this line to control mocking

    def _get_current_system_prompt(self) -> BetaTextBlockParam:
        """Get the appropriate system prompt based on current highlight mode"""
        system_prompts = get_system_prompt()
        mode = "highlight" if self.state_manager.highlight_mode else "tool"
        return BetaTextBlockParam(
            type="text",
            text=system_prompts[mode]
        )

    def _append_message(self, message: BetaMessageParam) -> None:
        """Helper method to append message and save messages state"""
        self.messages.append(message)
        self.history_tracker.save_messages(self.messages)

    def process_message(self, message: str) -> None:
        """Process message with iteration loop based on auto mode"""
        logger.info(f"New message received: {message}")
        self.stop_processing()

        self._append_message({
            "role": "user",
            "content": [{"type": "text", "text": message}]
        })    
        self.state_manager.set_status(AgentStatus.RUNNING, message)
        self.stop_event.clear()
        
        if self.state_manager.auto_mode:
            self.processing_thread = threading.Thread(
                target=self._process_message_loop
            )
        else:
            self.processing_thread = threading.Thread(
                target=self._process_message_single_mode
            )
        self.processing_thread.start()

    def _process_message_single_mode(self) -> None:
        try:
            response_params = self._next_step_proposal()

            if self.state_manager.highlight_mode:
                response_params = [
                    block for block in response_params 
                    if block["type"] == "text"
                ]
                logger.info(f"Skipping tool proposals since in highlight mode")
            else:
                logger.info(f"Storing {len(response_params) - 1} tool proposals in queue")
                self._store_pending_tool_proposals(response_params)
        finally:
            logger.info("Setting status to IDLE, clearing stop event, and cleaning up thread")
            self.state_manager.set_status(AgentStatus.IDLE)
            self.stop_event.clear()
            self.processing_thread = None
            logger.info("Single mode processing completed and cleaned up")

    def _process_message_loop(self) -> None:
        """Internal method to handle message processing loop"""
        logger.info("Starting to process message in loop mode")
        iteration = 1
        try:
            while (iteration <= MAX_ITERATIONS and 
                   not self.stop_event.is_set() and 
                   self.state_manager.status == AgentStatus.RUNNING.value):
                logger.debug(f"Processing iteration {iteration}/{MAX_ITERATIONS}")
                
                response_params = self._next_step_proposal()
                
                tool_blocks = [block for block in response_params if block["type"] == "tool_use"]
                if not tool_blocks:
                    break

                tool_result_content = self._execute_tools(tool_blocks)
                if tool_result_content:
                    self._append_message({"role": "user", "content": tool_result_content})
                iteration += 1

        finally:
            self.state_manager.set_status(AgentStatus.IDLE)
            self.stop_event.clear()
            self.processing_thread = None
            logger.info("Message processing loop completed and cleaned up")

    def _store_pending_tool_proposals(self, response_params):
        """Store tool proposals for later execution"""
        for block in response_params:
            if block["type"] == "tool_use":
                logger.info(f"Tool action: {block['input']}")
                self.pending_tool_queue.append(block)
        self.state_manager.set_pending_tools(len(self.pending_tool_queue))

    @log_execution_time(logger)
    def _execute_tools(self, tool_blocks: list[BetaToolUseBlockParam]) -> list[BetaToolResultBlockParam]:
        """Common method to execute a list of tools and collect results"""
        tool_result_content: list[BetaToolResultBlockParam] = []
        
        for content_block in tool_blocks:
            self.state_manager.emit_response({
                "type": "tool_use",
                "parameters": content_block["input"]
            })
            
            result = self.tool_collection.run(
                name=content_block["name"],
                tool_input=cast(dict[str, Any], content_block["input"]),
            )
            
            tool_result = _make_api_tool_result(result, content_block["id"])
            tool_result_content.append(tool_result)
            
            # Emit individual result
            self.state_manager.emit_response({
                "type": "tool_result",
                "content": tool_result
            })
            
        return tool_result_content

    def execute_next_pending_tool(self):
        if not self.pending_tool_queue:
            logger.info("No pending tools to execute")
            return
            
        self.state_manager.set_status(AgentStatus.RUNNING)
        try:
            tool_result_content = self._execute_tools(self.pending_tool_queue)
            self.pending_tool_queue.clear()
            
            if tool_result_content:
                self._append_message({"role": "user", "content": tool_result_content})
                
        finally:
            self.state_manager.set_status(AgentStatus.IDLE)
            self.state_manager.set_pending_tools(0)

    def process_next_action(self):
        """Generate the next action without executing tools"""
        if not self.processing_thread or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(
                target=self._process_message_single_mode,
                args=(None,)
            )
            self.processing_thread.start()
        else:
            logger.info("Agent is already processing")


    def _next_step_proposal(self):
        
        logger.info("Taking screenshot and cursor position before calling AI")
        self._take_screenshot()
        response_params = self._call_llm() 
        for content_block in response_params:
            if content_block["type"] == "text":
                self.state_manager.emit_response({
                    "type": "ai_response",
                    "content": content_block["text"]
                })
        
        self._append_message(
            {
                "role": "assistant",
                "content": response_params,
            }
        )
        return response_params

    def _inject_prompt_caching(self,
        messages: list[BetaMessageParam],
    ):
        """
        Set cache breakpoints for the 3 most recent turns
        one cache breakpoint is left for tools/system prompt, to be shared across sessions
        """

        breakpoints_remaining = 3
        for message in reversed(messages):
            if message["role"] == "user" and isinstance(
                content := message["content"], list
            ):
                if breakpoints_remaining:
                    breakpoints_remaining -= 1
                    content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                        {"type": "ephemeral"}
                    )
                else:
                    content[-1].pop("cache_control", None)
                    # we'll only every have one extra turn per loop
                    break

    def stop_processing(self) -> None:
        """Stop current processing loop"""
        logger.info("Attempting to stop processing thread if it exists")
        if self.processing_thread and self.processing_thread.is_alive():
            logger.info(f"Stopping active message processing thread: {self.processing_thread}")
            self.stop_event.set()
            self.state_manager.set_status(AgentStatus.STOPPING)
            
            # Try multiple times to join
            max_attempts = 3
            attempt_timeout = 2.0  # seconds per attempt
            
            for attempt in range(max_attempts):
                logger.info(f"Attempt {attempt + 1}/{max_attempts} to stop thread")
                self.processing_thread.join(timeout=attempt_timeout)
                
                if not self.processing_thread.is_alive():
                    logger.info(f"Processing thread successfully stopped on attempt {attempt + 1}")
                    break
                
                if attempt < max_attempts - 1:  # Don't log "failed" for the last attempt
                    logger.warning(f"Thread stop attempt {attempt + 1} failed, retrying...")
            
            if self.processing_thread.is_alive():
                logger.error(f"Failed to stop thread after {max_attempts} attempts")
            
            self.state_manager.set_status(AgentStatus.IDLE)
        else:
            logger.info("No active processing thread to stop")
            self.state_manager.set_status(AgentStatus.IDLE)

    @log_execution_time(logger)
    def _take_screenshot(self) -> None:
        """Takes a screenshot and adds cursor position to the message history"""
        try:
            # Replace direct appends with helper method
            self._append_message({
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "computer",
                        "id": f"tool_cursor_{len(self.messages)}",
                        "input": {"action": "cursor_position"}
                    }
                ]
            })
            
            cursor_result = self.tool_collection.run(
                name="computer",
                tool_input={"action": "cursor_position"}
            )
            
            self._append_message({
                "role": "user",
                "content": [
                    _make_api_tool_result(
                        result=cursor_result,
                        tool_use_id=f"tool_cursor_{len(self.messages)-1}"
                    )
                ]
            })

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
            
            result = self.tool_collection.run(
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
            
            logger.info("Screenshot and cursor position captured and added to message history")
        except Exception as e:
            logger.error(f"Failed to take screenshot or get cursor position: {e}")

    @log_execution_time(logger)
    def _call_llm(self) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        """Call the LLM API
        
        Returns:
            list of content blocks (text or tool use blocks)
        """
        try:
            system = self._get_current_system_prompt()
            if PROMPT_CACHING:
                self._inject_prompt_caching(self.messages)
                system["cache_control"] = {"type": "ephemeral"}
                
            raw_response = self.client.beta.messages.with_raw_response.create(
                max_tokens=MAX_TOKENS,
                messages=self.messages,
                model=MODEL_NAME,
                system=[system],
                tools=self.tools_params,
                betas=self.betas,
            )
            response = raw_response.parse()
            
            # Track token usage
            self.token_tracker.track_usage(
                response.usage.input_tokens,
                response.usage.output_tokens
            )
            
            return _response_to_params(response)
            
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(f"LLM API call failed: {e}")
            raise