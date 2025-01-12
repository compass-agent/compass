import anthropic
import asyncio

async def main():
    client = anthropic.Anthropic()

    tools_param = [{
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string", 
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature"
                }
            },
            "required": ["location"]
        }
    }]

    async with client.messages.stream(
        max_tokens=1024,
        messages=[
            {
                "role": "user", 
                "content": "Say hello there!",
            }
        ],
        model="claude-3-5-sonnet-20241022",
        tools=tools_param  # type: ignore
    ) as stream: # type: ignore
        async for event in stream:
            if event.type == "text":
                print(event.text, end="", flush=True)
            elif event.type == 'content_block_stop':
                print('\n\ncontent block finished accumulating:', event.content_block)

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())