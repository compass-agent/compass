from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, Union
from ..types.agent import SystemMessage, HumanMessage, AIMessage, ToolCall, ToolResult


class BaseLLMInterface(ABC):
    @abstractmethod
    def __init__(self, memory_manager: Any, tools_params: Dict[str, Any]):
        """Initialize LLM interface with memory manager and tool parameters"""
        pass

    @abstractmethod
    def stream_call(self, system_message: SystemMessage) -> Generator[Union[str, ToolCall], None, None]:
        """
        Stream the LLM response, yielding either text chunks or tool calls.
        
        Args:
            system_message: SystemMessage containing the system prompt
            
        Yields:
            Union[str, ToolCall]: Either a text chunk or a tool call object
        """
        pass

    @abstractmethod
    def format_messages_for_llm(self, messages: list[Union[SystemMessage, HumanMessage, AIMessage, ToolResult]]) -> Any:
        """
        Format messages into LLM-specific format
        
        Args:
            messages: List of message objects
            
        Returns:
            Formatted messages in LLM-specific format
        """
        pass 