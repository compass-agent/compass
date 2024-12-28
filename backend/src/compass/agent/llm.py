import logging
from typing import Any, cast
from anthropic import (
    Anthropic,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaMessage,
    BetaCacheControlEphemeralParam,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from compass.key import ANTHROPIC_API_KEY
from compass.agent.prompt import get_system_prompt
from compass.utils.utility import TokenTracker
from compass.constants import (
    MODEL_NAME,
    MODEL_NAME_MANUAL,
    MODEL_NAME_AUTO,
    MAX_TOKENS,
    PROMPT_CACHING,
    COMPUTER_USE_BETA_FLAG,
    PROMPT_CACHING_BETA_FLAG
)
from compass.utils.utility import log_execution_time

logger = logging.getLogger(__name__)

SCREENSHOT_KEEP_COUNT = 1

async def _response_to_params(
    response: BetaMessage,
) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
    res: list[BetaTextBlockParam | BetaToolUseBlockParam] = []
    for block in response.content:
        if isinstance(block, BetaTextBlock):
            res.append({"type": "text", "text": block.text})
        else:
            res.append(cast(BetaToolUseBlockParam, block.model_dump()))
    return res

def _get_current_system_prompt(highlight_mode: bool):
    """Get the appropriate system prompt based on current highlight mode"""
    system_prompts = get_system_prompt()
    mode = "highlight" if highlight_mode else "tool"
    return {
        "type": "text",
        "text": system_prompts[mode],
        "cache_control": {"type": "ephemeral"} if PROMPT_CACHING else None
    }

def _remove_old_screenshots(
    messages: list[BetaMessageParam],
    images_to_keep: int | None
):
    """
    Remove all but the final `images_to_keep` tool_result images in place.
    If images_to_keep is None, keeps all images.
    """
    if images_to_keep is None:
        return messages

    kept_images = 0
    for message in reversed(messages):
        content = cast(list[dict[str, Any]], message.get("content", []))
        new_content = []
        for content_block in reversed(content):
            if isinstance(content_block, dict) and content_block.get("type") == "tool_result":
                tool_content = cast(list[dict[str, Any]], content_block.get("content", []))
                filtered_tool_content = []
                for item in tool_content:
                    if isinstance(item, dict) and item.get("type") == "image":
                        if kept_images < images_to_keep:
                            kept_images += 1
                            filtered_tool_content.append(item)
                    else:
                        filtered_tool_content.append(item)
                content_block["content"] = filtered_tool_content
            new_content.append(content_block)
        message["content"] = list(reversed(new_content))
    return messages

class LLM:
    def __init__(self, tools_params):
        self.token_tracker = TokenTracker()
        self.tools_params = tools_params
        logger.info(f"Tools params: {self.tools_params}")
        self.betas = [COMPUTER_USE_BETA_FLAG] + ([PROMPT_CACHING_BETA_FLAG] if PROMPT_CACHING else [])
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)

    #@log_execution_time(logger)
    async def call(
        self, 
        messages: list[BetaMessageParam], 
        highlight_mode: bool,
        manual_mode: bool
    ) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        """Call the LLM API asynchronously
        
        Returns:
            list of content blocks (text or tool use blocks)
        """
        try:
            system = _get_current_system_prompt(highlight_mode)
            logger.info(f"LLM model name: {MODEL_NAME_MANUAL if manual_mode else MODEL_NAME_AUTO}")
            messages = _remove_old_screenshots(
                messages,
                SCREENSHOT_KEEP_COUNT,
            )

            # Using with_raw_response for better error handling
            raw_response = self.client.beta.messages.with_raw_response.create(
                max_tokens=MAX_TOKENS,
                messages=messages,
                model= MODEL_NAME_MANUAL if manual_mode else MODEL_NAME_AUTO,
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
            
            return await _response_to_params(response)
            
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(f"LLM API call failed: {e}")
            raise
