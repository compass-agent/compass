from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, Union
from .schema import SystemMessage, HumanMessage, AIMessage, ToolCall

class BaseLLMInterface(ABC):
    @abstractmethod
    def __init__(self, system_message: SystemMessage, tools_params: Dict[str, Any]):
        pass

    @abstractmethod
    def stream_call(self, message: HumanMessage) -> Generator[Union[str, ToolCall], None, None]:
        """
        Stream the LLM response, yielding either text chunks or tool calls
        """
        pass 