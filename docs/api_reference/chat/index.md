# Chat System

PepperPy AI provides a sophisticated chat system for managing conversations with AI models.

## Overview

The chat system provides:
- Conversation management
- Message history tracking
- Context handling
- Role-based interactions
- Streaming support

## Core Components

### Conversation

The `Conversation` class manages chat interactions:

```python
from pepperpy.chat import Conversation, Message
from pepperpy.config import Config

async def chat_example():
    config = Config()
    conversation = Conversation(config)
    
    # Add messages
    conversation.add_message(Message(
        role="user",
        content="Tell me about Python"
    ))
    
    # Get response
    response = await conversation.get_response()
    print(response)
```

### Message Types

Different types of messages are supported:

```python
from pepperpy.chat import Message, SystemMessage, UserMessage, AssistantMessage

# System message (instructions)
system_msg = SystemMessage("You are a helpful assistant")

# User message (input)
user_msg = UserMessage("How do I use Python's asyncio?")

# Assistant message (response)
assistant_msg = AssistantMessage("Here's how to use asyncio...")
```

## Chat Configuration

Configure chat behavior:

```python
from pepperpy.chat.config import ChatConfig

config = ChatConfig(
    max_history=10,
    temperature=0.7,
    system_prompt="You are a Python expert",
    stream_enabled=True
)
```

## Advanced Features

### Streaming Chat

```python
from pepperpy.chat import StreamingConversation

async def streaming_chat():
    config = Config(stream_enabled=True)
    conversation = StreamingConversation(config)
    
    async for chunk in conversation.stream("Tell me about Python"):
        print(chunk, end="", flush=True)
```

### Context Management

```python
from pepperpy.chat import ConversationContext

async def context_example():
    context = ConversationContext(
        topic="Python Programming",
        skill_level="intermediate",
        code_context="async/await"
    )
    
    conversation = Conversation(config, context=context)
    response = await conversation.get_response("Explain generators")
```

### Role-Based Chat

```python
from pepperpy.chat import RoleBasedConversation

async def role_chat():
    conversation = RoleBasedConversation(
        system_role="Python Expert",
        user_role="Student"
    )
    
    await conversation.add_message("How do I use decorators?")
    response = await conversation.get_response()
```

## Best Practices

1. **Message Management**
   - Keep conversation history focused
   - Clear context when changing topics
   - Use appropriate message types

2. **Context Handling**
   - Provide relevant context
   - Update context when needed
   - Clear context when appropriate

3. **Performance**
   - Use streaming for long responses
   - Manage conversation history size
   - Clear old conversations

4. **Error Handling**
   - Handle message failures
   - Implement retry logic
   - Validate message content

## Environment Variables

Configure chat settings:

```bash
PEPPERPY_CHAT_MAX_HISTORY=10
PEPPERPY_CHAT_TEMPERATURE=0.7
PEPPERPY_CHAT_STREAM_ENABLED=true
PEPPERPY_CHAT_SYSTEM_PROMPT="You are a helpful assistant"
```

## Examples

### Basic Chat

```python
from pepperpy.chat import Conversation
from pepperpy.config import Config

async def basic_chat():
    config = Config()
    conversation = Conversation(config)
    
    # Single message
    response = await conversation.send("Hello!")
    print(response)
    
    # Multiple turns
    await conversation.send("What is Python?")
    await conversation.send("Tell me more about its features")
```

### Contextual Chat

```python
from pepperpy.chat import Conversation, Context

async def contextual_chat():
    context = Context(
        language="Python",
        version="3.9",
        topic="async programming"
    )
    
    conversation = Conversation(config, context=context)
    response = await conversation.send("How do I create an async function?")
```

### Function Calling

```python
from pepperpy.chat import Conversation, Function

async def function_chat():
    # Define available functions
    functions = [
        Function(
            name="get_weather",
            description="Get weather information",
            parameters={
                "location": "string",
                "unit": "string"
            }
        )
    ]
    
    conversation = Conversation(
        config,
        functions=functions
    )
    
    response = await conversation.send("What's the weather in London?")
``` 