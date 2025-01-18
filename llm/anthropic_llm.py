from typing import List, Generator, Optional, Union
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from .base import BaseLLMInterface
from compass.key import ANTHROPIC_API_KEY


class AnthropicLLM(BaseLLMInterface):
    def __init__(self, system_message: SystemMessage, tools: List[BaseTool] = []):
        super().__init__(system_message, tools)
        self.model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=ANTHROPIC_API_KEY,
            temperature=0.7
        ) # type: ignore
        self.model_with_tools = self.model.bind_tools(self.tools)

    def stream_call(self, message: HumanMessage) -> Generator[Union[str, dict], None, None]:
        self.messages.append(message)
        
        # Since Anthropic doesn't support streaming with tools,
        # we'll get the complete response first
        response = self.model_with_tools.invoke(self.messages)
        
        # Handle the content which is now a list of chunks
        if response.content:
            for chunk in response.content:
                if chunk['type'] == 'text':
                    yield chunk['text']
                elif chunk['type'] == 'tool_use':
                    yield {
                        'id': chunk['id'],
                        'name': chunk['name'],
                        'args': chunk['input']  # Anthropic uses 'input' instead of 'args'
                    }

    def add_message(self, message: Union[SystemMessage, HumanMessage, AIMessage]) -> None:
        self.messages.append(message) 