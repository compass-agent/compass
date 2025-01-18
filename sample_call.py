from llm.google_llm import GoogleLLM
from llm.anthropic_llm import AnthropicLLM
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage, SystemMessage

@tool
def calculate(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@tool
def screenshot(name: str) -> str:
    return "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"
    

def main():
    model = GoogleLLM(
        system_message=SystemMessage(content="You are a helpful mathematical assistant."),
        tools=[calculate]
    )
    model = AnthropicLLM(
        system_message=SystemMessage(content="You are a helpful mathematical assistant."),
        tools=[calculate]
    )

    questions = [
        "What is 5 multiplied by 3? Please explain the concept first.",
        "Now, what is 7 times 8? Again make sure to explain the concept first.",
    ]
    questions = [
        "tell me content of page1,
    ]
    for question in questions:
        print(f"\nQuestion: {question}")
        print("Response:")
        response_content = []
        tool_calls = []
        for chunk in model.stream_call(HumanMessage(content=question)):
            if isinstance(chunk, str):
                response_content.append(chunk)
                print(chunk, end="", flush=True)
            elif isinstance(chunk, dict):
                tool_calls.append(chunk)

        # After collecting all chunks, create and add the AI message
        ai_message = AIMessage(content="".join(response_content))
        model.add_message(ai_message)

        # If there were tool calls, add them as a separate message
        if tool_calls:
            tool_call_message = AIMessage(
                content="",
                tool_calls=tool_calls
            )
            model.add_message(tool_call_message)

        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']

            # Execute the tool
            tool_result = calculate.invoke(tool_args)

            # Construct a ToolMessage
            tool_message = ToolMessage(
                content="tool_result",
                tool_call_id=tool_call['id']
            )

            # Add tool result to the model's message history
            model.add_message(tool_message)

        print("\n")

if __name__ == "__main__":
    main() 