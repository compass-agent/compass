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
from compass.utils.utility import HistoryLogger
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


class AgentService:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.messages: list[BetaMessageParam] = []
        
        # Initialize beta flags and client
        self.betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)
        
        # Initialize history logger
        self.logger = HistoryLogger()
        
        # Pass logger to ComputerTool
        self.tool_collection = ToolCollection(ComputerTool(logger=self.logger))
        
        logger.info("AgentService initialized")
        self.pending_tool_queue = []  # Add queue for pending tools

    def _get_current_system_prompt(self) -> BetaTextBlockParam:
        """Get the appropriate system prompt based on current highlight mode"""
        system_prompts = get_system_prompt()
        mode = "highlight" if self.state_manager.highlight_mode else "tool"
        return BetaTextBlockParam(
            type="text",
            text=system_prompts[mode]
        )

    def process_message(self, message: str) -> None:
        """Process message with iteration loop based on auto mode"""
        logger.info(f"Processing new message: {message}")
        self.stop_processing()

        self.messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": message}]
            }
        ]
        
        self.state_manager.set_status(AgentStatus.RUNNING, message)
        self.stop_event.clear()
        
        if self.state_manager.auto_mode:
            self.processing_thread = threading.Thread(
                target=self._process_message_loop,
                args=(message,)
            )
        else:
            self.processing_thread = threading.Thread(
                target=self._process_message_single_mode,
                args=(message,)
            )

        self.processing_thread.start()

    def _process_message_single_mode(self, message: Optional[str]) -> None:
        try:
            logger.info("Processing message in single mode")
            response_params = self._next_step_proposal()

            if self.state_manager.highlight_mode:
                # In highlight mode, only keep text responses
                response_params = [
                    block for block in response_params 
                    if block["type"] == "text"
                ]
            else:
                # Store tool proposals without executing
                self._store_pending_tool_proposals(response_params)


        finally:
            self.state_manager.set_status(AgentStatus.IDLE)
            self.stop_event.clear()
            self.processing_thread = None
            logger.info("Single mode processing completed and cleaned up")

    def _store_pending_tool_proposals(self, response_params):
        """Store tool proposals for later execution"""
        for block in response_params:
            if block["type"] == "tool_use":
                self.pending_tool_queue.append(block)
        
        # Update pending tools count in state
        self.state_manager.set_pending_tools(len(self.pending_tool_queue))

    def execute_next_pending_tool(self):
        """Execute all pending tools in the queue"""
        if not self.pending_tool_queue:
            logger.info("No pending tools to execute")
            return

        self.state_manager.set_status(AgentStatus.RUNNING)
        
        try:
            # Process all pending tools
            while self.pending_tool_queue:
                content_block = self.pending_tool_queue.pop(0)
                
                # Execute the tool
                result = self.tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast(dict[str, Any], content_block["input"]),
                )

                # Log tool result
                self.logger.log_action('tool_result', {
                    "output": result.output,
                    "error": result.error,
                    "has_image": bool(result.base64_image)
                })

                # Convert result to API format
                tool_result_content = _make_api_tool_result(result, content_block["id"])

                # Append tool result to messages
                self.messages.append({"role": "user", "content": [tool_result_content]})

                # Send tool result to frontend
                self.state_manager.emit_response({
                    "type": "tool_result",
                    "content": tool_result_content,
                })

        finally:
            self.state_manager.set_status(AgentStatus.IDLE)
            # Update pending tools count
            self.state_manager.set_pending_tools(len(self.pending_tool_queue))

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

    def _process_message_loop(self, message: str) -> None:
        """Internal method to handle message processing loop"""
        iteration = 1
        try:
            while (iteration <= MAX_ITERATIONS and 
                   not self.stop_event.is_set() and 
                   self.state_manager.status == AgentStatus.RUNNING.value):
                logger.debug(f"Processing iteration {iteration}/{MAX_ITERATIONS}")
                
                response_params = self._next_step_proposal()
                
                tool_result_content = self._execute_tool(response_params)
                if not tool_result_content:
                    break
                iteration += 1

        finally:
            self.state_manager.set_status(AgentStatus.IDLE)
            # Clear the stop event and thread reference
            self.stop_event.clear()
            self.processing_thread = None
            logger.info("Message processing loop completed and cleaned up")


    def _next_step_proposal(self):
        self._take_screenshot()
        # Get response from LLM and send to frontend
        response_params = self._call_llm()  # Set to False for production
        # Log the AI response
        self.logger.log_action('ai_response', response_params)
        
        # Send AI response to frontend
        for content_block in response_params:
            if content_block["type"] == "text":
                self.state_manager.emit_response({
                    "type": "ai_response",
                    "content": content_block["text"]
                })
        
        self.messages.append(
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


    def _execute_tool(self, response_params):
        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in response_params:
            if content_block["type"] == "tool_use":
                # Log tool usage
                self.logger.log_action('tool_use', content_block)
                
                # Send tool usage to frontend - simplified
                self.state_manager.emit_response({
                    "type": "tool_use",
                    "parameters": content_block["input"]
                })
                
                result = self.tool_collection.run(
                    name=content_block["name"],
                    tool_input=cast(dict[str, Any], content_block["input"]),
                )
                
                # Log tool result
                self.logger.log_action('tool_result', {
                    "output": result.output,
                    "error": result.error,
                    "has_image": bool(result.base64_image)
                })
                                        
                tool_result_content.append(
                    _make_api_tool_result(result, content_block["id"])
                )

        if not tool_result_content:
            # Job is done
            return
        else:
            self.messages.append({"role": "user", "content": tool_result_content})
            return tool_result_content

    def stop_processing(self) -> None:
        """Stop current processing loop"""
        if self.processing_thread and self.processing_thread.is_alive():
            logger.info("Stopping active message processing thread")
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
            
            # Final check and state update
            if self.processing_thread.is_alive():
                logger.error(f"Failed to stop thread after {max_attempts} attempts")
                # We still update the state to IDLE since we can't do anything else
                # The thread might continue running in the background
            
            # Update state to IDLE regardless of thread state
            self.state_manager.set_status(AgentStatus.IDLE)
        else:
            logger.info("No active processing thread to stop")
            self.state_manager.set_status(AgentStatus.IDLE)

    def _take_screenshot(self) -> None:
        """Takes a screenshot and adds cursor position to the message history"""
        try:
            # First get cursor position
            self.messages.append({
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
            
            # Execute cursor position check
            cursor_result = self.tool_collection.run(
                name="computer",
                tool_input={"action": "cursor_position"}
            )
            
            # Add cursor position result
            self.messages.append({
                "role": "user",
                "content": [
                    _make_api_tool_result(
                        result=cursor_result,
                        tool_use_id=f"tool_cursor_{len(self.messages)-1}"
                    )
                ]
            })

            # Then take screenshot (existing code)
            self.messages.append({
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
            
            # Execute screenshot action using tool collection
            result = self.tool_collection.run(
                name="computer",
                tool_input={"action": "screenshot"}
            )
            
            # Add screenshot result
            self.messages.append({
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

    def _call_llm(self) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        """Call the LLM API
        
        Returns:
            list of content blocks (text or tool use blocks)
        """
        

        logger.debug("Simulating LLM API call delay...")
        time.sleep(1)
        
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
                    'coordinate': [94, 462]  # You'll need to add the actual coordinates here
                }
            }
        ]
        
        # Real API call implementation below
        # try:
        #     system = self._get_current_system_prompt()
        #     if PROMPT_CACHING:
        #         self._inject_prompt_caching(self.messages)
        #         system["cache_control"] = {"type": "ephemeral"}
                
        #     raw_response = self.client.beta.messages.with_raw_response.create(
        #         max_tokens=MAX_TOKENS,
        #         messages=self.messages,
        #         model=MODEL_NAME,
        #         system=[system],
        #         tools=self.tool_collection.to_params(),
        #         betas=self.betas,
        #     )
        #     response = raw_response.parse()
        #     return _response_to_params(response)
            
        # except (APIStatusError, APIResponseValidationError) as e:
        #     logger.error(f"LLM API call failed: {e}")
        #     raise