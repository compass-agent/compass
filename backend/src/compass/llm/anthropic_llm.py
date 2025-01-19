import json
import logging
from typing import Generator, Dict, Any, Union
from anthropic import Anthropic
from anthropic.types.beta import (
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolUseBlockParam
)

from .base import BaseLLMInterface
from ..types.agent import SystemMessage, HumanMessage, AIMessage, ToolCall, ToolResult
from .memory_management import MemoryManager
from ..constants import (
    MODEL_NAME_MANUAL,
    MODEL_NAME_AUTO,
    MAX_TOKENS,
    COMPUTER_USE_BETA_FLAG,
    PROMPT_CACHING_BETA_FLAG,
    PROMPT_CACHING
)
from compass.key import ANTHROPIC_API_KEY
from ..utils.utility import log_execution_time

logger = logging.getLogger(__name__)

class AnthropicLLM(BaseLLMInterface):
    def __init__(self, memory_manager: MemoryManager, tools_params: Dict[str, Any]):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)
        self.tools_params = tools_params
        self.memory_manager = memory_manager
        self.betas = [COMPUTER_USE_BETA_FLAG] + ([PROMPT_CACHING_BETA_FLAG] if PROMPT_CACHING else [])

    async def _response_to_params(
        self,
        response: BetaMessage,
    ) -> list[BetaTextBlockParam | BetaToolUseBlockParam]:
        res: list[BetaTextBlockParam | BetaToolUseBlockParam] = []
        for block in response.content:
            if isinstance(block, BetaTextBlock):
                res.append({"type": "text", "text": block.text})
            else:
                res.append(block.model_dump())
        return res

    def preprocess_messages(self, messages: list[dict]) -> list[dict]:
        """Preprocess messages for manual mode by converting tool-related content to text"""
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

    @log_execution_time(logger)
    def stream_call(self, system_message: SystemMessage, manual_mode: bool = False) -> Generator[Union[str, ToolCall], None, None]:
        messages = self.memory_manager.memory
        #messages = self.memory_manager.optimize_messages(messages)
        formatted_messages = self.format_messages_for_llm(messages)

        try:
            if manual_mode:
                # Preprocess messages for manual mode
                formatted_messages = self.preprocess_messages(formatted_messages)
                with self.client.messages.stream(
                    max_tokens=MAX_TOKENS,
                    messages=formatted_messages,
                    model=MODEL_NAME_MANUAL,
                    system=system_message.content
                ) as stream:
                    for text in stream.text_stream:
                        yield text
            else:
                raw_response = self.client.beta.messages.with_raw_response.create(
                    max_tokens=MAX_TOKENS,
                    messages=formatted_messages,
                    model=MODEL_NAME_AUTO,
                    system=system_message.content,
                    tools=self.tools_params,
                    betas=self.betas,
                )
                response = raw_response.parse()
                # Process each content block
                for block in response.content:
                    logger.info(f"checkout point 1, block: {block}")
                    if block.type == "text":
                        logger.info(f"checkout point 2, block: {block}")
                        yield block.text
                    elif block.type == "tool_use":
                        logger.info(f"checkout point 3, block: {block}")
                        # Convert to our custom ToolCall type
                        tool_call = ToolCall(
                            name=block.name,
                            args=block.input,
                            tool_call_id=block.id
                        )
                        yield tool_call

        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

    def format_messages_for_llm(self, messages: list[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]) -> list[BetaMessageParam]:
        """Convert our generic message types to Anthropic's beta message format"""
        formatted_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                formatted_messages.append({
                    "role": "system",
                    "content": [{"type": "text", "text": message.content}]
                })
            elif isinstance(message, HumanMessage):
                content = [{"type": "text", "text": message.content}]
                if message.image_data:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": message.image_data
                        }
                    })
                formatted_messages.append({"role": "user", "content": content})
            elif isinstance(message, AIMessage):
                if message.content:
                    formatted_messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": message.content}]
                    })
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        formatted_messages.append({
                            "role": "assistant",
                            "content": [{
                                "type": "tool_use",
                                "name": tool_call.name,
                                "input": tool_call.args,
                                "id": tool_call.tool_call_id
                            }]
                        })
            elif isinstance(message, ToolResult):
                content = []
                if message.text:
                    content.append({"type": "text", "text": message.text})
                if message.image:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": message.image
                        }
                    })
                formatted_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "content": content,
                        "tool_use_id": message.tool_call_id
                    }]
                })
        
        return formatted_messages 