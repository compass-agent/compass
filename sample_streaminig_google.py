import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

from compass.key import ANTHROPIC_API_KEY, GOOGLE_API_KEY
os.environ["GOOGLE_API_KEY"] = "your-api-key-here"

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

def main():
    try:
        # Initialize the Google model
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # Use a standard Gemini model
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
        
        # Bind the calculate tool
        model_with_tools = model.bind_tools([calculate])
        
        # Prepare messages
        messages = [
            SystemMessage(content="You are a helpful mathematical assistant."),
            HumanMessage(content="What is 5 multiplied by 3? Please first explain the concept of multiplication and then provide the answer.")
        ]
        
        # Stream the response
        print("Streaming response:")
        for chunk in model_with_tools.stream(messages):
            # Check if the chunk has content
            if chunk.content:
                print(chunk.content, end="", flush=True)
            
            # Check for tool calls
            if chunk.tool_calls:
                print("\n\nTool Calls:")
                for tool_call in chunk.tool_calls:
                    print(f"Tool: {tool_call['name']}")
                    print(f"Arguments: {tool_call['args']}")
        
        print("\n\nStreaming complete.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
