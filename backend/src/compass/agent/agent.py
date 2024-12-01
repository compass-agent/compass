import logging
import threading
from typing import Any, Dict
from enum import StrEnum
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

from compass.tools import ComputerTool, ToolCollection, ToolResult
from compass.key import ANTHROPIC_API_KEY
from compass.agent.prompt import get_system_prompt
from compass.constants import MODEL_NAME, MAX_TOKENS


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


class AgentService:
    def __init__(self, websocket_service):
        self.websocket_service = websocket_service
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.state = {
            'autoMode': False,
            'highlightMode': False,
            'playing': False,
            'procgessing': False,
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
                   self.state['processing']):
                logger.debug(f"Processing iteration {iteration}/{max_iterations}")
                
                self._inject_prompt_caching(self.messages)
                self.system["cache_control"] = {"type": "ephemeral"}
                try:
                    raw_response = self.client.beta.messages.with_raw_response.create(
                        max_tokens=MAX_TOKENS,
                        messages=self.messages,
                        model=MODEL_NAME,
                        system=[self.system],
                        tools=self.tool_collection.to_params(),
                        betas=self.betas,
                    )
                except (APIStatusError, APIResponseValidationError) as e:
                    # TODO: handle errors appropriately
                    pass
                response = raw_response.parse()
                response_params = _response_to_params(response)
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": response_params,
                    }
                )
                tool_result_content: list[BetaToolResultBlockParam] = []
                for content_block in response_params:
                    if content_block["type"] == "tool_use":
                        result = self.tool_collection.run(
                            name=content_block["name"],
                            tool_input=cast(dict[str, Any], content_block["input"]),
                        )
                        tool_result_content.append(
                            _make_api_tool_result(result, content_block["id"])
                        )

                if not tool_result_content:
                    # Job is done
                    break

                self.messages.append({"role": "user", "content": tool_result_content})
                iteration += 1

        finally:
            # Ensure state is updated when processing ends
            self._update_state({
                'processing': False,
                'playing': False,
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