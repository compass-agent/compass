from abc import ABC, abstractmethod
from typing import List, Generator, Union
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

class BaseLLMInterface(ABC):
    def __init__(self, system_message: SystemMessage, tools: List[BaseTool] = []):
        self.messages: List[BaseMessage] = []
        self.tools = tools or []
        
        if system_message:
            self.messages.append(system_message)

    @abstractmethod
    def stream_call(self)  -> Generator[Union[str, dict], None, None]:
        pass 