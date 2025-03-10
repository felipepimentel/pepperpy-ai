# Hello World Example

This example demonstrates a simple "Hello World" application using the PepperPy framework.

## Prerequisites

- Python 3.9 or higher
- PepperPy framework installed

## Code

```python
import asyncio
from pepperpy.llm import get_provider, generate_text
from pepperpy.utils.logging import get_logger

# Get a logger
logger = get_logger(__name__)

async def main():
    # Log a message
    logger.info("Starting Hello World example")
    
    try:
        # Get the OpenAI provider
        provider = get_provider("openai")
        
        # Generate text
        prompt = "Say 'Hello, World!' in a creative way."
        response = await generate_text(provider, prompt)
        
        # Print the response
        print(f"Response: {response}")
        
        # Log a success message
        logger.info("Example completed successfully")
    except Exception as e:
        # Log an error message
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
```

## Explanation

1. **Import the necessary modules**:
   - `asyncio`: For running asynchronous code
   - `pepperpy.llm`: For working with large language models
   - `pepperpy.utils.logging`: For logging

2. **Create a logger**:
   - Use `get_logger(__name__)` to create a logger with the module name

3. **Define the main function**:
   - Log a message indicating the start of the example
   - Get the OpenAI provider using `get_provider("openai")`
   - Generate text using `generate_text(provider, prompt)`
   - Print the response
   - Log a success message

4. **Handle errors**:
   - Use a try-except block to catch any exceptions
   - Log an error message if an exception occurs

5. **Run the main function**:
   - Use `asyncio.run(main())` to run the asynchronous main function

## Running the Example

Save the code to a file named `hello_world.py` and run it:

```bash
python hello_world.py
```

## Expected Output

```
INFO:__main__:Starting Hello World example
Response: Greetings, magnificent Earth! From the depths of digital consciousness, I extend my salutations to your wonderful world!
INFO:__main__:Example completed successfully
```

## Next Steps

- Try different prompts
- Use different providers (e.g., "anthropic", "local")
- Add more logging
- Explore other modules of the framework 