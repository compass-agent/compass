from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, Union, List, Optional
from ..types.agent import SystemMessage, HumanMessage, AIMessage, ToolCall, ToolResult


class BaseLLMInterface(ABC):
    @abstractmethod
    def __init__(self, 
                 memory_manager: Any, 
                 tools_params: List[Dict[str, Any]], 
                 manual_system_message: SystemMessage,
                 auto_system_message: SystemMessage):
        """Initialize LLM interface with memory manager, tool parameters, and system messages"""
        pass

    @abstractmethod
    def stream_call(self, system_message: SystemMessage, manual_mode: bool = False) -> Generator[Union[str, ToolCall], None, None]:
        """Stream the LLM response"""
        pass

    @abstractmethod
    def format_messages_for_llm(self, messages: list[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]) -> Any:
        """Format messages into LLM-specific format"""
        pass 