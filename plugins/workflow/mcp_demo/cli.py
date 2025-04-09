#!/usr/bin/env python3
"""CLI tool for interacting with MCP server.

This provides a command-line interface for testing MCP server capabilities.
"""

import argparse
import asyncio
import sys
import uuid
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.mcp.client.providers.http import HTTPClientProvider
from pepperpy.mcp.protocol import MCPOperationType, MCPRequest, MCPStatusCode

logger = get_logger("mcp.cli")


class MCPClientCLI:
    """Command-line interface for MCP client interactions."""

    def __init__(self, host: str = "localhost", port: int = 8000) -> None:
        """Initialize the CLI.

        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.client: HTTPClientProvider | None = None
        self.history: list[dict[str, str]] = []
        self.running = False
        self.model_id = "gpt-3.5-turbo"  # Default model

    async def initialize(self) -> None:
        """Initialize the client."""
        self.client = HTTPClientProvider(url=f"http://{self.host}:{self.port}")
        await self.client.initialize()
        logger.info(f"Connected to MCP server at {self.host}:{self.port}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.cleanup()
            self.client = None

    async def chat(self, message: str) -> dict[str, Any]:
        """Send a chat message to the server.

        Args:
            message: User message

        Returns:
            Response data
        """
        if not self.client:
            return {"status": MCPStatusCode.ERROR, "message": "Client not initialized"}

        # Add message to history
        self.history.append({"role": "user", "content": message})

        # Create request
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            model_id=self.model_id,
            operation=MCPOperationType.CHAT,
            inputs={"messages": self.history},
        )

        try:
            # Send request
            response = await self.client.request(request)

            # Add response to history
            if response.status == MCPStatusCode.SUCCESS:
                content = response.outputs.get("content", "")
                self.history.append({"role": "assistant", "content": content})
                return {"status": response.status, "content": content}
            else:
                return {
                    "status": response.status,
                    "error": response.error or "Unknown error",
                }
        except Exception as e:
            logger.error(f"Error sending chat request: {e}")
            return {"status": MCPStatusCode.ERROR, "error": str(e)}

    async def use_tool(self, tool_name: str, content: str) -> dict[str, Any]:
        """Use a specific tool.

        Args:
            tool_name: Tool name
            content: Tool input

        Returns:
            Tool response
        """
        if not self.client:
            return {"status": MCPStatusCode.ERROR, "message": "Client not initialized"}

        # Format content based on tool
        if tool_name == "calculate":
            formatted_content = f"calculate: {content}"
        elif tool_name == "weather":
            formatted_content = f"get_weather: {content}"
        elif tool_name == "translate":
            formatted_content = f"translate: {content}"
        else:
            return {
                "status": MCPStatusCode.ERROR,
                "error": f"Unknown tool: {tool_name}",
            }

        # Create request
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            model_id=tool_name,
            operation=MCPOperationType.CHAT,
            inputs={"messages": [{"role": "user", "content": formatted_content}]},
        )

        try:
            # Send request
            response = await self.client.request(request)
            return {"status": response.status, "outputs": response.outputs}
        except Exception as e:
            logger.error(f"Error using tool {tool_name}: {e}")
            return {"status": MCPStatusCode.ERROR, "error": str(e)}

    def print_help(self) -> None:
        """Print help information."""
        print("\nAvailable commands:")
        print("  /help              - Show this help information")
        print("  /quit or /exit     - Exit the CLI")
        print("  /clear             - Clear conversation history")
        print("  /models            - List available models")
        print("  /model <model_id>  - Change the current model")
        print("  /calc <expression> - Use the calculate tool")
        print("  /weather <location> - Use the weather tool")
        print("  /translate <text> to <lang> - Use the translate tool")
        print("\nOr just type a message to chat with the AI.\n")

    async def run(self) -> None:
        """Run the CLI interface."""
        try:
            await self.initialize()
            self.running = True
            print("\n=== MCP Client CLI ===")
            print(f"Connected to server at {self.host}:{self.port}")
            self.print_help()

            while self.running:
                try:
                    user_input = input("\n> ")
                    if not user_input.strip():
                        continue

                    # Process commands
                    if user_input.startswith("/"):
                        await self.process_command(user_input)
                    else:
                        # Regular chat
                        print("Sending message...")
                        result = await self.chat(user_input)
                        if result["status"] == MCPStatusCode.SUCCESS:
                            print(f"\nAI: {result['content']}")
                        else:
                            print(f"\nError: {result.get('error', 'Unknown error')}")

                except KeyboardInterrupt:
                    print("\nExiting...")
                    self.running = False
                except Exception as e:
                    print(f"Error: {e}")

        finally:
            await self.cleanup()

    async def process_command(self, command: str) -> None:
        """Process a command.

        Args:
            command: Command string
        """
        parts = command.strip().split(" ", 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ["/quit", "/exit"]:
            print("Exiting...")
            self.running = False

        elif cmd == "/help":
            self.print_help()

        elif cmd == "/clear":
            self.history = []
            print("Conversation history cleared.")

        elif cmd == "/models":
            print("Available models:")
            print(f"  Current: {self.model_id}")
            print("  Supported: gpt-3.5-turbo, gpt-4 (if configured)")

        elif cmd == "/model":
            if args:
                self.model_id = args.strip()
                print(f"Model changed to: {self.model_id}")
            else:
                print(f"Current model: {self.model_id}")

        elif cmd == "/calc":
            if args:
                print(f"Calculating: {args}")
                result = await self.use_tool("calculate", args)
                if result["status"] == MCPStatusCode.SUCCESS:
                    print(f"Result: {result['outputs'].get('result', 'No result')}")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
            else:
                print("Usage: /calc <expression>")

        elif cmd == "/weather":
            if args:
                print(f"Getting weather for: {args}")
                result = await self.use_tool("weather", args)
                if result["status"] == MCPStatusCode.SUCCESS:
                    weather = result["outputs"].get("weather", {})
                    if weather:
                        print(f"Weather for {weather.get('location', 'Unknown')}:")
                        print(f"  Temperature: {weather.get('temperature', 'N/A')}°C")
                        print(f"  Condition: {weather.get('condition', 'N/A')}")
                    else:
                        print("No weather data returned")
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
            else:
                print("Usage: /weather <location>")

        elif cmd == "/translate":
            if "to" in args:
                parts = args.split(" to ", 1)
                if len(parts) == 2:
                    text, lang = parts
                    print(f"Translating '{text}' to {lang}")
                    result = await self.use_tool("translate", args)
                    if result["status"] == MCPStatusCode.SUCCESS:
                        print(
                            f"Translation: {result['outputs'].get('translated_text', 'No translation')}"
                        )
                    else:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                else:
                    print("Usage: /translate <text> to <language>")
            else:
                print("Usage: /translate <text> to <language>")

        else:
            print(f"Unknown command: {cmd}")


async def main() -> int:
    """Run the CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="MCP Client CLI")
    parser.add_argument(
        "--host", default="localhost", help="MCP server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="MCP server port (default: 8000)"
    )
    args = parser.parse_args()

    try:
        cli = MCPClientCLI(host=args.host, port=args.port)
        await cli.run()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
