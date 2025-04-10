#!/usr/bin/env python3
"""
MCP Demo Tool - CLI for MCP Server and Client.

This script provides a command-line interface for running the MCP server,
client, or a complete workflow demonstration.
"""

import argparse
import asyncio
import json
import sys


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    missing_deps = []
    try:
        import openai
    except ImportError:
        missing_deps.append("openai")

    try:
        import aiohttp
    except ImportError:
        missing_deps.append("aiohttp")

    if missing_deps:
        print("Error: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install them using pip:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False

    return True


# Only try imports if dependencies are present
if check_dependencies():
    try:
        # Ignore linter errors for these imports - they'll be resolved at runtime
        from plugins.workflow.mcp_demo.cli import MCPClientCLI  # type: ignore
        from plugins.workflow.mcp_demo.run_server import MCPServerRunner  # type: ignore
        from plugins.workflow.mcp_demo.workflow import MCPDemoWorkflow  # type: ignore
    except ImportError:
        try:
            # Try relative import if running from within the package
            from cli import MCPClientCLI  # type: ignore
            from run_server import MCPServerRunner  # type: ignore
            from workflow import MCPDemoWorkflow  # type: ignore
        except ImportError as e:
            print(f"Error importing MCP components: {e}")
            sys.exit(1)


async def run_server(args: argparse.Namespace) -> None:
    """Run the MCP server.

    Args:
        args: Command-line arguments
    """
    server = MCPServerRunner(
        host=args.host,
        port=args.port,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
    )

    await server.initialize()
    try:
        await server.run()
    finally:
        await server.cleanup()


async def run_client(args: argparse.Namespace) -> None:
    """Run the MCP client CLI.

    Args:
        args: Command-line arguments
    """
    client = MCPClientCLI(
        host=args.host,
        port=args.port,
    )

    await client.initialize()
    try:
        await client.run()
    finally:
        await client.cleanup()


async def run_workflow(args: argparse.Namespace) -> None:
    """Run the MCP demo workflow.

    Args:
        args: Command-line arguments
    """
    workflow = MCPDemoWorkflow(
        config={
            "host": args.host,
            "port": args.port,
            "provider_type": "http",
            "llm_provider": args.llm_provider,
            "llm_model": args.llm_model,
            "demo_duration": args.duration,
        }
    )

    await workflow.initialize()
    try:
        result = await workflow.execute({"workflow_type": "default"})
        print(json.dumps(result, indent=2))
    finally:
        await workflow.cleanup()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Demo CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run MCP server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    server_parser.add_argument("--llm-provider", default="openai", help="LLM provider")
    server_parser.add_argument("--llm-model", default="gpt-3.5-turbo", help="LLM model")

    # Client command
    client_parser = subparsers.add_parser("client", help="Run MCP client CLI")
    client_parser.add_argument("--host", default="localhost", help="Server host")
    client_parser.add_argument("--port", type=int, default=8000, help="Server port")
    client_parser.add_argument("--llm-model", default="gpt-3.5-turbo", help="LLM model")

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run MCP demo workflow")
    workflow_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    workflow_parser.add_argument("--port", type=int, default=8000, help="Server port")
    workflow_parser.add_argument(
        "--llm-provider", default="openai", help="LLM provider"
    )
    workflow_parser.add_argument(
        "--llm-model", default="gpt-3.5-turbo", help="LLM model"
    )
    workflow_parser.add_argument(
        "--duration", type=int, default=60, help="Demo duration in seconds"
    )

    args = parser.parse_args()

    if not check_dependencies():
        sys.exit(1)

    if args.command == "server":
        asyncio.run(run_server(args))
    elif args.command == "client":
        asyncio.run(run_client(args))
    elif args.command == "workflow":
        asyncio.run(run_workflow(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
