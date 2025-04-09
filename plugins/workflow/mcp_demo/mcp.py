#!/usr/bin/env python3
"""MCP Demo Command Line Tool.

This script provides a unified command-line interface for running the MCP server,
client, or the complete demo workflow.
"""

import argparse
import asyncio
import sys

from pepperpy.core.logging import get_logger

logger = get_logger("mcp.cli")


async def run_server(args: argparse.Namespace) -> int:
    """Run the MCP server with the provided arguments.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    # Import locally to avoid circular imports
    from run_server import MCPServerRunner

    try:
        server_runner = MCPServerRunner(
            host=args.host,
            port=args.port,
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            api_key=args.api_key,
        )
        await server_runner.run()
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1


async def run_client(args: argparse.Namespace) -> int:
    """Run the MCP client with the provided arguments.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    # Import locally to avoid circular imports
    from cli import MCPClientCLI

    try:
        cli = MCPClientCLI(host=args.host, port=args.port)
        await cli.run()
        return 0
    except Exception as e:
        logger.error(f"Client error: {e}")
        return 1


async def run_workflow(args: argparse.Namespace) -> int:
    """Run the complete MCP demo workflow.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    from workflow import MCPDemoWorkflow

    try:
        # Create config from args
        config = {
            "host": args.host,
            "port": args.port,
            "provider_type": "http",
            "llm_provider": args.llm_provider,
            "llm_model": args.llm_model,
            "demo_duration": args.duration,
            "run_real_demo": True,
        }

        # Create and run workflow
        workflow = MCPDemoWorkflow(config=config)
        await workflow.initialize()

        try:
            result = await workflow.execute({})
            if result.get("status") == "success":
                logger.info("Workflow completed successfully")
                return 0
            else:
                logger.error(
                    f"Workflow failed: {result.get('message', 'Unknown error')}"
                )
                return 1
        finally:
            await workflow.cleanup()
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return 1


def main() -> int:
    """Main entry point for the MCP command-line tool.

    Returns:
        Exit code
    """
    # Create the top-level parser
    parser = argparse.ArgumentParser(
        description="MCP Demo Command Line Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run server only
  python mcp.py server
  
  # Run client only connecting to a remote server
  python mcp.py client --host api.example.com --port 443
  
  # Run complete workflow with OpenAI model
  python mcp.py workflow --llm-model gpt-4
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Create parser for server command
    server_parser = subparsers.add_parser("server", help="Run MCP server")
    server_parser.add_argument(
        "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    server_parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    server_parser.add_argument(
        "--llm-provider", default="openai", help="LLM provider (default: openai)"
    )
    server_parser.add_argument(
        "--llm-model",
        default="gpt-3.5-turbo",
        help="LLM model (default: gpt-3.5-turbo)",
    )
    server_parser.add_argument(
        "--api-key", help="API key for LLM provider (defaults to OPENAI_API_KEY)"
    )

    # Create parser for client command
    client_parser = subparsers.add_parser("client", help="Run MCP client")
    client_parser.add_argument(
        "--host", default="localhost", help="Server host (default: localhost)"
    )
    client_parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )

    # Create parser for workflow command
    workflow_parser = subparsers.add_parser(
        "workflow", help="Run complete MCP demo workflow"
    )
    workflow_parser.add_argument(
        "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    workflow_parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    workflow_parser.add_argument(
        "--llm-provider", default="openai", help="LLM provider (default: openai)"
    )
    workflow_parser.add_argument(
        "--llm-model",
        default="gpt-3.5-turbo",
        help="LLM model (default: gpt-3.5-turbo)",
    )
    workflow_parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Demo duration in seconds (default: 60)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Run appropriate command
    if args.command == "server":
        return asyncio.run(run_server(args))
    elif args.command == "client":
        return asyncio.run(run_client(args))
    elif args.command == "workflow":
        return asyncio.run(run_workflow(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
