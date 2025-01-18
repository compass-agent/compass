from typing import Generator, Dict, Any, Union
from .base import BaseLLMInterface
from .schema import SystemMessage, HumanMessage, AIMessage, ToolCall

class AnthropicLLM(BaseLLMInterface):
    def __init__(self, system_message: SystemMessage, tools_params: Dict[str, Any]):
        self.system_message = system_message
        self.tools_params = tools_params
        
    def stream_call(self, message: HumanMessage) -> Generator[Union[str, ToolCall], None, None]:
        """Mock implementation that yields a fixed response with both text and tool calls"""
        
        # First yield some text chunks
        yield "Let me help you with that. "
        yield "I'll need to take a screenshot first.\n"
        
        # Yield a tool call
        tool_call = ToolCall(
            name="screenshot",
            args={"name": "page1"},
            tool_call_id="call_123"
        )
        yield tool_call
        
        # Yield more text after the tool call
        yield "\nNow that I have the screenshot, "
        yield "I can analyze it for you." 