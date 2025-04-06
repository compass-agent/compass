import json
import logging
from typing import Generator, Dict, Any, Union, List
from anthropic import Anthropic
from anthropic.types.beta import (
    BetaMessageParam
)

from compass.llm.base import BaseLLMInterface
from compass.types.agent import SystemMessage, HumanMessage, AIMessage, ToolCall, ToolResult
from compass.llm.memory_management import MemoryManager
from compass.constants import (
    ANTHROPIC_MODEL_NAME_MANUAL,
    ANTHROPIC_MODEL_NAME_AUTO,
    MAX_TOKENS,
    PROMPT_CACHING
)
from compass.key import ANTHROPIC_API_KEY
from compass.utils.utility import log_execution_time
from compass.utils.utility import TokenTracker

COMPUTER_USE_BETA_FLAG = "computer-use-2025-01-24" # computer-use-2025-01-24  computer-use-2024-10-22
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"

logger = logging.getLogger(__name__)

class AnthropicLLM(BaseLLMInterface):
    def __init__(self, 
                 memory_manager: MemoryManager, 
                 tools_params: List[Dict[str, Any]], 
                 manual_system_message: SystemMessage,
                 auto_system_message: SystemMessage):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=4)
        self.token_tracker = TokenTracker()
        # Filter tools while keeping required parameters
        self.tools_params = [
            {
                "type": tool["type"],
                "name": tool["name"],
                **({"display_width_px": tool["display_width_px"], 
                    "display_height_px": tool["display_height_px"]} 
                   if tool["type"] == "computer_20250124" else {})
            }
            if tool["name"] in ["computer", "str_replace_editor"]
            else tool
            for tool in tools_params
        ]
        self.memory_manager = memory_manager
        self.betas = [COMPUTER_USE_BETA_FLAG] + ([PROMPT_CACHING_BETA_FLAG] if PROMPT_CACHING else [])
        # We don't need to store system messages as Anthropic handles them differently

    @log_execution_time(logger)
    def stream_call(self, system_message: SystemMessage, manual_mode: bool = False) -> Generator[Union[str, ToolCall], None, None]:
        messages = self.memory_manager.memory
        messages = self.memory_manager.optimize_messages(messages)
        formatted_messages = self.format_messages_for_llm(messages)
        if PROMPT_CACHING:
            system_message_content = [{"type": "text", "text": system_message.content, "cache_control": {"type": "ephemeral"}}]
        else:
            system_message_content = [{"type": "text", "text": system_message.content}]
        # Save formatted messages
        self._save_formatted_messages(formatted_messages, system_message.content)

        try:
            if manual_mode:
                # Preprocess messages for manual mode
                formatted_messages = self._preprocess_messages(formatted_messages)
                with self.client.messages.stream(
                    max_tokens=MAX_TOKENS,
                    messages=formatted_messages, # type: ignore
                    model=ANTHROPIC_MODEL_NAME_MANUAL,
                    system=system_message.content
                ) as stream:
                    for text in stream.text_stream:
                        yield text
            else:
                raw_response = self.client.beta.messages.with_raw_response.create(
                    max_tokens=MAX_TOKENS,
                    messages=formatted_messages, # type: ignore
                    model=ANTHROPIC_MODEL_NAME_AUTO,
                    system=system_message_content, # type: ignore
                    tools=self.tools_params, # type: ignore
                    betas=self.betas,
                )
                response = raw_response.parse()
                self.token_tracker.track_usage(
                    response.usage.input_tokens,
                    response.usage.output_tokens,
                    response.usage.cache_creation_input_tokens or 0,
                    response.usage.cache_read_input_tokens or 0
                )
                for block in response.content:
                    if block.type == "text":
                        yield block.text
                    elif block.type == "tool_use":
                        tool_call = ToolCall(
                            name=block.name,
                            args=block.input, # type: ignore
                            tool_call_id=block.id
                        )
                        yield tool_call

        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

    def _preprocess_messages(self, messages: list[BetaMessageParam]) -> list[BetaMessageParam]:
        """Preprocess messages for manual mode by converting tool-related content to text"""
        processed = []
        for message in messages:
            new_message = {"role": message["role"]}
            new_content = []
            
            for content_item in message["content"]:
                if content_item["type"] == "tool_result": # type: ignore
                    # Flatten tool_result content directly into the message
                    new_content.extend(content_item["content"]) # type: ignore
                elif content_item["type"] == "tool_use": # type: ignore
                    # Convert tool_use to text format
                    tool_text = f"Tool Use - Name: {content_item['name']}, Input: {json.dumps(content_item['input'])}" # type: ignore
                    new_content.append({
                        "type": "text",
                        "text": tool_text
                    })
                else:
                    # Keep other content types (text, image) as is
                    new_content.append(content_item)
            
            new_message["content"] = new_content # type: ignore
            processed.append(new_message)
        return processed

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
                    }) # type: ignore
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
                text_content = message.text or ""
                if message.error:
                    text_content = f"{text_content}\nError: {message.error}"
                if text_content:
                    content.append({"type": "text", "text": text_content})
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

    def _save_formatted_messages(self, formatted_messages: list[BetaMessageParam], system_content: str) -> None:
        """Save the formatted messages that will be sent to Anthropic"""
        prompt_data = {
            "messages": formatted_messages,
            "system": system_content
        }
        
        timestamp = self.memory_manager.history_tracker.get_timestamp_filename()
        save_dir = self.memory_manager.history_tracker.prompts_dir
        filename = f"llm_prompt/prompt_{timestamp}"
        
        # Save to anthropic_prompts_dir
        self.memory_manager.history_tracker.save_messages(prompt_data, filename)
        logger.info(f"Saved formatted Anthropic prompt with timestamp {timestamp}") 