#!/usr/bin/env python
"""
CLI tool for interacting with the MCP demo server.
This provides a simple interface to send requests to a running MCP server.
"""

import argparse
import asyncio
import json
import sys
import uuid
from dataclasses import dataclass
from enum import Enum

from pepperpy.mcp.client.providers.http import HTTPClientProvider
from pepperpy.mcp.protocol import (
    MCPOperationType,
    MCPRequest,
    MCPStatusCode,
)


class MCPMessageRole(str, Enum):
    """Role of a chat message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class MCPChatMessage:
    """Chat message for MCP requests."""

    role: MCPMessageRole
    content: str

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role if isinstance(self.role, str) else self.role.value,
            "content": self.content,
        }


class MCPDemoCLI:
    """Simple CLI for interacting with an MCP server."""

    def __init__(self, host: str = "localhost", port: int = 8042):
        """Initialize the CLI with server connection details.

        Args:
            host: The host where the MCP server is running
            port: The port on which the MCP server is listening
        """
        self.host = host
        self.port = port
        self.server_url = f"http://{host}:{port}"
        self.client = HTTPClientProvider()
        self.history: list[MCPChatMessage] = []

    async def connect(self) -> bool:
        """Connect to the MCP server.

        Returns:
            True if the connection was successful, False otherwise
        """
        try:
            await self.client.initialize()
            await self.client.connect(server_url=self.server_url)
            return True
        except ConnectionError:
            print(f"Failed to connect to MCP server at {self.host}:{self.port}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        await self.client.disconnect()
        await self.client.cleanup()

    async def list_models(self) -> None:
        """List available models from the server."""
        try:
            # Create a special request to list models - this is implementation-specific
            # and might not be supported by the actual server
            request = MCPRequest(
                request_id=str(uuid.uuid4()),
                model_id="system",
                operation=MCPOperationType.COMPLETION,
                parameters={"action": "list_models"},
            )

            response = await self.client.request(request)

            if response.status != MCPStatusCode.SUCCESS:
                print(f"\nError listing models: {response.error}")
                return

            # The response format depends on the server implementation
            models = response.outputs.get("models", [])
            print("\nAvailable models:")
            for model in models:
                print(f"- {model}")
        except Exception as e:
            print(f"Error listing models: {e}")
            print("Note: Model listing may not be supported by this server")

    async def send_chat_request(self, message: str, stream: bool = True) -> None:
        """Send a chat request to the server.

        Args:
            message: The user message to send
            stream: Whether to stream the response or not
        """
        # Add the user message to history
        self.history.append(MCPChatMessage(role=MCPMessageRole.USER, content=message))

        # Create the request
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            model_id="gpt-3.5-turbo",
            operation=MCPOperationType.CHAT,
            parameters={
                "max_tokens": 1000,
                "temperature": 0.7,
            },
            inputs={
                "messages": [msg.to_dict() for msg in self.history],
            },
        )

        if stream:
            # Handle streaming response
            try:
                response_stream = self.client.stream(request)

                assistant_message = MCPChatMessage(
                    role=MCPMessageRole.ASSISTANT, content=""
                )
                print("\nAssistant: ", end="", flush=True)

                async for chunk in response_stream:
                    if chunk.status != MCPStatusCode.SUCCESS:
                        print(f"\nError: {chunk.error}")
                        return

                    content = chunk.outputs.get("content", "")
                    if content:
                        assistant_message.content += content
                        print(content, end="", flush=True)

                print("\n")
                self.history.append(assistant_message)

            except Exception as e:
                print(f"\nError during streaming: {e}")
        else:
            # Handle regular response
            try:
                response = await self.client.request(request)

                if response.status != MCPStatusCode.SUCCESS:
                    print(f"\nError: {response.error}")
                    return

                content = response.outputs.get("content", "")
                self.history.append(
                    MCPChatMessage(role=MCPMessageRole.ASSISTANT, content=content)
                )
                print(f"\nAssistant: {content}\n")

            except Exception as e:
                print(f"\nError: {e}")

    async def send_tool_request(self, tool_name: str, tool_input: str) -> None:
        """Send a tool request to the server.

        Args:
            tool_name: The name of the tool to use
            tool_input: The input for the tool
        """
        try:
            # Create a message with the tool syntax
            message = f"{tool_name}: {tool_input}"

            # Create the request
            request = MCPRequest(
                request_id=str(uuid.uuid4()),
                model_id=tool_name,  # Use the tool name as the model ID
                operation=MCPOperationType.CHAT,
                inputs={"messages": [{"role": "user", "content": message}]},
            )

            response = await self.client.request(request)

            if response.status != MCPStatusCode.SUCCESS:
                print(f"\nError: {response.error}")
                return

            print(f"\nTool response: {json.dumps(response.outputs, indent=2)}\n")

        except Exception as e:
            print(f"\nError with tool execution: {e}")

    def print_help(self) -> None:
        """Print help information."""
        print("\nAvailable commands:")
        print("  /help          - Show this help message")
        print("  /quit, /exit   - Exit the CLI")
        print("  /clear         - Clear the conversation history")
        print("  /models        - List available models")
        print("  /calc <expr>   - Use the calculate tool")
        print("  /weather <loc> - Use the weather tool")
        print("  /translate <text> to <lang> - Use the translate tool")
        print("  Any other text will be sent as a chat message\n")

    async def interactive_loop(self) -> None:
        """Run the interactive CLI loop."""
        self.print_help()

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["/quit", "/exit"]:
                    break

                elif user_input.lower() == "/help":
                    self.print_help()

                elif user_input.lower() == "/clear":
                    self.history = []
                    print("Conversation history cleared.")

                elif user_input.lower() == "/models":
                    await self.list_models()

                elif user_input.lower().startswith("/calc "):
                    expr = user_input[6:].strip()
                    await self.send_tool_request("calculate", expr)

                elif user_input.lower().startswith("/weather "):
                    location = user_input[9:].strip()
                    await self.send_tool_request("get_weather", location)

                elif user_input.lower().startswith("/translate "):
                    text = user_input[11:].strip()
                    await self.send_tool_request("translate", text)

                else:
                    await self.send_chat_request(user_input)

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")


async def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="MCP Demo CLI Client")
    parser.add_argument(
        "--host", type=str, default="localhost", help="Host address of the MCP server"
    )
    parser.add_argument("--port", type=int, default=8042, help="Port of the MCP server")

    args = parser.parse_args()
    cli = MCPDemoCLI(host=args.host, port=args.port)

    print(f"Connecting to MCP server at {args.host}:{args.port}...")
    if not await cli.connect():
        sys.exit(1)

    try:
        await cli.interactive_loop()
    finally:
        await cli.disconnect()
        print("Disconnected from server. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
