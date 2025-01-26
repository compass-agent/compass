import json
import logging
from typing import Generator, Dict, Any, Union, List, Optional
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, FunctionDeclaration, Tool

from compass.llm.base import BaseLLMInterface
from compass.types.agent import SystemMessage, HumanMessage, AIMessage, ToolCall, ToolResult
from compass.llm.memory_management import MemoryManager
from compass.utils.utility import log_execution_time
from compass.constants import (
    MAX_TOKENS
)
from compass.key import GOOGLE_API_KEY
from compass.constants import GOOGLE_MODEL_NAME
logger = logging.getLogger(__name__)

class GoogleLLM(BaseLLMInterface):
    def __init__(self, 
                 memory_manager: MemoryManager, 
                 tools_params: List[Dict[str, Any]], 
                 manual_system_message: SystemMessage,
                 auto_system_message: SystemMessage):
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            GOOGLE_MODEL_NAME,
            generation_config={"temperature": 0.7, "max_output_tokens": MAX_TOKENS}
        )
        self.memory_manager = memory_manager
        
        # Initialize both manual and auto mode chats as None
        self.manual_chat = None
        self.auto_chat = None
        
        # Convert tool params to Gemini Tools format
        self.tools = []
        for tool in tools_params:
            if "input_schema" in tool:
                self.tools.append(Tool(
                    function_declarations=[
                        FunctionDeclaration(
                            name=tool["name"],
                            description=tool["description"],
                            parameters=tool["input_schema"]
                        )
                    ]
                ))

        # Initialize both chats with their respective system messages
        self.initialize_chats(manual_system_message, auto_system_message)

        # Add tracking for last processed message index
        self.last_processed_index = 0

    def initialize_chats(self, manual_system_message: SystemMessage, auto_system_message: SystemMessage):
        """Initialize both manual and auto mode chats with their respective system messages"""
        logger.info("Initializing Google chats with system messages")
        
        # Initialize manual mode chat
        self.manual_chat = self.model.start_chat()
        self.manual_chat.send_message({"text": manual_system_message.content})
        
        # Initialize auto mode chat with tools
        self.auto_chat = self.model.start_chat()
        self.auto_chat.send_message(
            {"text": auto_system_message.content},
            tools=self.tools
        )

    def format_messages_for_llm(self, messages: list[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]) -> list[Dict[str, Any]]:
        formatted_messages = []
        
        for message in messages:
            if isinstance(message, (SystemMessage, HumanMessage)):
                parts = [{"text": message.content}]
                if isinstance(message, HumanMessage) and message.image_data:
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": message.image_data
                        }
                    }) # type: ignore
                formatted_messages.append({"role": "user", "parts": parts})
            
            elif isinstance(message, AIMessage):
                if message.content:
                    formatted_messages.append({
                        "role": "model",
                        "parts": [{"text": message.content}]
                    })
            
            elif isinstance(message, ToolResult):
                parts = []
                if message.text:
                    parts.append({"text": message.text})
                if message.image:
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": message.image
                        }
                    })
                if parts:
                    formatted_messages.append({"role": "user", "parts": parts})
        
        return formatted_messages

    @log_execution_time(logger)
    def stream_call(self, system_message: SystemMessage, manual_mode: bool = False) -> Generator[Union[str, ToolCall], None, None]:
        try:
            messages = self.memory_manager.memory
            # Get only new messages since last processing
            new_messages = messages[self.last_processed_index:]
            formatted_messages = self.format_messages_for_llm(new_messages)
            
            # Update the last processed index
            self.last_processed_index = len(messages)

            # Select appropriate chat based on mode
            active_chat = self.manual_chat if manual_mode else self.auto_chat
            
            if active_chat is None:
                raise RuntimeError("Chats not initialized. Please initialize with system message first.")
            
            # Send message to selected chat with all new messages
            response = active_chat.send_message(
                [part for msg in formatted_messages for part in msg["parts"]],
                stream=True,
                tools=self.tools if not manual_mode else None
            )
            
            # Process response based on mode
            chunks = []
            for chunk in response:
                chunks.append(chunk)
                if chunk.candidates:
                    for candidate in chunk.candidates:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                yield part.text
                            elif not manual_mode and hasattr(part, 'function_call'):
                                # Parse function call arguments
                                args_dict = {}
                                if hasattr(part.function_call.args, '_pb'):
                                    for key, value in part.function_call.args._pb.items():
                                        string_value = getattr(value, 'string_value', None)
                                        if string_value:  # This will be False for empty strings
                                            args_dict[key] = string_value
                                        elif hasattr(value, 'list_value'):
                                            # Convert list values to Python list
                                            args_dict[key] = [
                                                v.number_value if hasattr(v, 'number_value')
                                                else v.string_value if getattr(v, 'string_value', '') 
                                                else None
                                                for v in value.list_value.values
                                            ]
                                        elif hasattr(value, 'number_value'):
                                            args_dict[key] = value.number_value
                                
                                yield ToolCall(
                                    name=part.function_call.name,
                                    args=args_dict,
                                    tool_call_id=part.function_call.name
                                )
            logger.info(f"Processed {len(messages)} messages, last processed index: {self.last_processed_index}")
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise 