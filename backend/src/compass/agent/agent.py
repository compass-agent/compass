import logging
import threading
from typing import Any, Dict
from enum import StrEnum, Enum
import httpx
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
from compass.constants import MODEL_NAME, MAX_TOKENS, PROMPT_CACHING
from compass.utils.utility import JSONLogger


COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

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


class AgentStatus(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"

class AgentService:
    def __init__(self, websocket_service):
        self.websocket_service = websocket_service
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.state = {
            'autoMode': False,
            'highlightMode': False,
            'playing': False,
            'status': AgentStatus.IDLE.value,
            'currentTask': None
        }
        self.messages: list[BetaMessageParam] = []
        self.system_prompt = get_system_prompt()
        
        # Initialize beta flags and client
        self.betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)
        
        # Initialize tool collection and system prompt
        self.tool_collection = ToolCollection(ComputerTool())
        self.system = BetaTextBlockParam(
            type="text",
            text=self.system_prompt
        )
        
        # Initialize JSON logger
        self.json_logger = JSONLogger()
        
        logger.info("AgentService initialized")

    def _update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update internal state and emit the new state"""
        self.state.update(state_update)
        logger.debug(f"State updated: {self.state}")
        self.websocket_service.emit_state_update(self.state.copy())
        return self.state.copy()

    def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state updates and return the new state"""
        logger.info(f"Updating state: {state_update}")
        
        if state_update.get('playing') is False:
            self.stop_processing()
        
        return self._update_state(state_update)

    def process_message(self, message: str) -> None:
        """Process message with iteration loop based on auto mode"""
        logger.info(f"Processing new message: {message}")
        self.stop_processing()  # Stop any existing processing
        
        # Update state to RUNNING - remove 'playing'
        self._update_state({
            'status': AgentStatus.RUNNING.value,
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

    def _process_message_loop(self, message: str) -> None:
        """Internal method to handle message processing loop"""
        max_iterations = 10 if self.state['autoMode'] else 1
        iteration = 1
        self.messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
        ]
        
        try:
            while (iteration <= max_iterations and 
                   not self.stop_event.is_set() and 
                   self.state['status'] == AgentStatus.RUNNING.value):
                logger.debug(f"Processing iteration {iteration}/{max_iterations}")
                
                # Add delay between iterations (skip delay for first iteration)
                if iteration > 1:
                    logger.debug("Waiting 4 seconds before next iteration...")
                    time.sleep(4)
                
                self._take_screenshot()
                
                # Get response from LLM and send to frontend
                response_params = self._call_llm()  # Set to False for production
                
                # Log the AI response
                self.json_logger.log_action('ai_response', response_params)
                
                # Send AI response to frontend
                for content_block in response_params:
                    if content_block["type"] == "text":
                        self.websocket_service.handle_message({
                            "type": "ai_response",
                            "content": content_block["text"]
                        })
                
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": response_params,
                    }
                )
                
                tool_result_content: list[BetaToolResultBlockParam] = []
                for content_block in response_params:
                    if content_block["type"] == "tool_use":
                        # Log tool usage
                        self.json_logger.log_action('tool_use', content_block)
                        
                        # Send tool usage to frontend - simplified
                        self.websocket_service.handle_message({
                            "type": "tool_use",
                            "parameters": content_block["input"]
                        })
                        
                        result = self.tool_collection.run(
                            name=content_block["name"],
                            tool_input=cast(dict[str, Any], content_block["input"]),
                        )
                        
                        # Log tool result
                        self.json_logger.log_action('tool_result', {
                            "output": result.output,
                            "error": result.error,
                            "has_image": bool(result.base64_image)
                        })
                        
                        # Send tool result to frontend - simplified
                        self.websocket_service.handle_message({
                            "type": "tool_result",
                            "output": result.output,
                            "error": result.error,
                            "has_image": bool(result.base64_image)
                        })
                        
                        tool_result_content.append(
                            _make_api_tool_result(result, content_block["id"])
                        )

                if not tool_result_content:
                    # Job is done
                    break

                self.messages.append({"role": "user", "content": tool_result_content})
                iteration += 1

        finally:
            self._update_state({
                'status': AgentStatus.IDLE.value,
                'currentTask': None
            })
            logger.info("Message processing completed")

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
        if self.processing_thread and self.processing_thread.is_alive():
            logger.info("Stopping active message processing thread")
            self.stop_event.set()
            self._update_state({'status': AgentStatus.STOPPING.value})
            
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
            self._update_state({
                'status': AgentStatus.IDLE.value,
                'currentTask': None
            })
        else:
            logger.info("No active processing thread to stop")
            self._update_state({
                'status': AgentStatus.IDLE.value,
                'currentTask': None
            })

    def get_state(self) -> Dict[str, Any]:
        """Return the current state"""
        return self.state.copy()

    def _take_screenshot(self) -> None:
        """Takes a screenshot and adds it to the message history"""
        try:
            # First, add assistant message requesting screenshot
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
            
            # Convert the tool result to API format
            tool_result = _make_api_tool_result(
                result=result,
                tool_use_id=f"tool_screenshot_{len(self.messages)-1}"  # Match the ID from assistant's message
            )
            
            # Add screenshot result to messages
            self.messages.append({
                "role": "user",
                "content": [tool_result]
            })
            
            logger.info("Screenshot captured and added to message history")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")

    def _call_llm(self) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        """Call the LLM API
        
        Returns:
            list of content blocks (text or tool use blocks)
        """
        # MOCK CODE - TO BE REMOVED LATER
        # Simulate API delay
        logger.debug("Simulating LLM API call delay...")
        time.sleep(4)
        
        # Mock response for development
        return [
            {
                'type': 'text',
                'text': 'I see a desktop environment with several windows open. The main window appears to be a messaging or chat application with a dark theme. Let me take another screenshot to analyze further.'
            },
            {
                'type': 'tool_use',
                'name': 'computer',
                'id': 'mock_tool_1',
                'input': {
                    'action': 'screenshot'
                }
            }
        ]
        
        # Real API call implementation below
        try:
            if PROMPT_CACHING:
                self._inject_prompt_caching(self.messages)
                self.system["cache_control"] = {"type": "ephemeral"}
                
            raw_response = self.client.beta.messages.with_raw_response.create(
                max_tokens=MAX_TOKENS,
                messages=self.messages,
                model=MODEL_NAME,
                system=[self.system],
                tools=self.tool_collection.to_params(),
                betas=self.betas,
            )
            response = raw_response.parse()
            return _response_to_params(response)
            
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(f"LLM API call failed: {e}")
            raise