from typing import List, Generator, Optional, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.messages import ToolMessage
from .base import BaseLLMInterface
from compass.key import GOOGLE_API_KEY

class GoogleLLM(BaseLLMInterface):
    def __init__(self, system_message: SystemMessage, tools: List[BaseTool] = []):
        super().__init__(system_message, tools)
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
        self.model_with_tools = self.model.bind_tools(self.tools)

    def stream_call(self, message: HumanMessage) -> Generator[Union[str, dict], None, None]:
        self.messages.append(message)
        
        response_content = []
        for chunk in self.model_with_tools.stream(self.messages):
            if chunk.content:
                response_content.append(chunk.content)
                yield chunk.content
            if chunk.tool_calls:
                for tool_call in chunk.tool_calls:
                    yield tool_call

    def add_message(self, message: Union[SystemMessage, HumanMessage, AIMessage]) -> None:
        self.messages.append(message)
