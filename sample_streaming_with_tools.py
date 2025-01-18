import os 
from typing import List, Dict, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from compass.key import ANTHROPIC_API_KEY, GOOGLE_API_KEY

class UnifiedToolCallingInterface:
    def __init__(self, provider: str, api_key: Optional[str] = None):
        """
        Initialize a unified interface for different AI providers
        
        Args:
            provider (str): 'openai', 'google', or 'anthropic'
            api_key (Optional[str]): API key for the selected provider
        """
        self._providers = {
            'openai': self._init_openai,
            'google': self._init_google,
            'anthropic': self._init_anthropic
        }
        
        if provider.lower() not in self._providers:
            raise ValueError(f"Unsupported provider: {provider}. Choose from {list(self._providers.keys())}")
        
        self.model = self._providers[provider.lower()](api_key)
    
    def _init_openai(self, api_key: Optional[str] = None) -> BaseChatModel:
        return ChatOpenAI(
            model="gpt-4o-mini", 
            api_key=ANTHROPIC_API_KEY,
            temperature=0.7
        )
    
    def _init_google(self, api_key: Optional[str] = None) -> BaseChatModel:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
    
    def _init_anthropic(self, api_key: Optional[str] = None) -> BaseChatModel:
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=ANTHROPIC_API_KEY,
            temperature=0.7
        )
    
    def call_with_tools(
        self, 
        messages: List[Dict[str, str]], 
        tools: List[BaseTool], 
        system_message: Optional[str] = None
    ):
        # Prepare messages
        prepared_messages = []
        
        # Add system message if provided
        if system_message:
            prepared_messages.append(SystemMessage(content=system_message))
        
        # Convert input messages to appropriate message types
        for msg in messages:
            if msg['role'] == 'human':
                prepared_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'ai':
                prepared_messages.append(AIMessage(content=msg['content']))
        
        # Bind tools to model
        model_with_tools = self.model.bind_tools(tools)
        
        # Invoke model
        response = model_with_tools.invoke(prepared_messages)
        
        return response

# Example Usage
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information"""
    return f"Search results for: {query}"

@tool
def calculate(operation: str, a: float, b: float) -> float:
    """Perform mathematical calculations"""
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    elif operation == 'multiply':
        return a * b
    elif operation == 'divide':
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unsupported operation: {operation}")

# Example Usage Demonstration
def main(provider: str = 'anthropic'):

    try:
        interface = UnifiedToolCallingInterface(provider=provider)
        
        response = interface.call_with_tools(
            messages=[{"role": "human", "content": "What is 5 multiplied by 3?"}],
            tools=[calculate],
            system_message="You are a helpful mathematical assistant."
        )
        print(f"{provider.capitalize()} Response:", response)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # {'openai', 'google', 'anthropic'}
    import sys
    provider = sys.argv[1] if len(sys.argv) > 1 else 'google'
    main(provider)