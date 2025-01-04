import logging
import json
from typing import Any, cast, AsyncGenerator
from anthropic import (
    Anthropic,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolUseBlockParam
)

from compass.key import ANTHROPIC_API_KEY
from compass.agent.prompt import get_system_prompt
from compass.utils.utility import TokenTracker
from compass.constants import (
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

class LLM:
    def __init__(self, tools_params):
        self.token_tracker = TokenTracker()
        self.tools_params = tools_params
        logger.info(f"Tools params: {self.tools_params}")
        self.betas = [COMPUTER_USE_BETA_FLAG] + ([PROMPT_CACHING_BETA_FLAG] if PROMPT_CACHING else [])
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)

    def _remove_old_screenshots(
        self,
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

    async def call_llm_with_tools(
        self, 
        messages: list[BetaMessageParam],
    ) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        """Call the LLM API using beta tools API"""
        try:
            system = get_system_prompt(manual_mode = False, highlight_mode = False)
            messages = self._remove_old_screenshots(
                messages,
                SCREENSHOT_KEEP_COUNT,
            )

            # Using with_raw_response for better error handling
            raw_response = self.client.beta.messages.with_raw_response.create(
                max_tokens=MAX_TOKENS,
                messages=messages,
                model= MODEL_NAME_AUTO,
                system=[system], # type: ignore
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

    async def call_llm_wo_tools(
        self, 
        messages: list[BetaMessageParam]
    ):
        """Call the LLM API without tools and not streaming"""
        try:
            system = get_system_prompt(manual_mode = True, highlight_mode = False)
            messages_updated = self.preprocess_messages(messages)

            raw_response = self.client.messages.create(
                max_tokens=MAX_TOKENS,
                messages=messages_updated,
                model=MODEL_NAME_MANUAL,
                system=system["text"]
            )

            return raw_response.content[0].text # type: ignore
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(f"LLM API call failed: {e}")
            raise


    async def call_llm_wo_tools_stream(
        self, 
        messages: list[BetaMessageParam]
    ) -> AsyncGenerator[str, None] | str:
        """Call the LLM API using streaming"""
        try:
            system = get_system_prompt(manual_mode = True, highlight_mode = False)
            messages_updated = self.preprocess_messages(messages)
            with self.client.messages.stream(
                max_tokens=MAX_TOKENS,
                messages=messages_updated,
                model=MODEL_NAME_MANUAL,
                system=system["text"]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except (APIStatusError, APIResponseValidationError) as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    @staticmethod
    def preprocess_messages(messages):
        processed = []
        for message in messages:
            new_message = {"role": message["role"]}
            new_content = []
            
            for content_item in message["content"]:
                if content_item["type"] == "tool_result":
                    # Flatten tool_result content directly into the message
                    new_content.extend(content_item["content"])
                elif content_item["type"] == "tool_use":
                    # Convert tool_use to text format
                    tool_text = f"Tool Use - Name: {content_item['name']}, Input: {json.dumps(content_item['input'])}"
                    new_content.append({
                        "type": "text",
                        "text": tool_text
                    })
                else:
                    # Keep other content types (text, image) as is
                    new_content.append(content_item)
            
            new_message["content"] = new_content
            processed.append(new_message)
        return processed