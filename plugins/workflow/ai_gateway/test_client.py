#!/usr/bin/env python3
"""
Test client for AI Gateway.

This script demonstrates how to interact with the AI Gateway.
"""

import argparse
import asyncio
import json
import sys


async def chat_request(url, api_key, prompt, model="gpt-3.5-turbo"):
    """Send a chat request to the AI Gateway.

    Args:
        url: Gateway URL
        api_key: API key
        prompt: Prompt text
        model: Model name

    Returns:
        Response from the gateway
    """
    import aiohttp

    # Prepare the request
    endpoint = f"{url}/api/v1/llm/chat"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": model,
    }

    # Send the request
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=headers) as response:
            # Print status info
            print(f"Status: {response.status}")

            # Parse and return the response
            response_data = await response.json()
            return response_data


async def completion_request(url, api_key, prompt, model="gpt-3.5-turbo"):
    """Send a completion request to the AI Gateway.

    Args:
        url: Gateway URL
        api_key: API key
        prompt: Prompt text
        model: Model name

    Returns:
        Response from the gateway
    """
    import aiohttp

    # Prepare the request
    endpoint = f"{url}/api/v1/llm/complete"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    payload = {
        "prompt": prompt,
        "model": model,
    }

    # Send the request
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=headers) as response:
            # Print status info
            print(f"Status: {response.status}")

            # Parse and return the response
            response_data = await response.json()
            return response_data


async def check_status(url):
    """Check the gateway status.

    Args:
        url: Gateway URL

    Returns:
        Status information
    """
    import aiohttp

    # Prepare the request
    endpoint = f"{url}/health"

    # Send the request
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            # Print status info
            print(f"Status: {response.status}")

            # Parse and return the response
            response_data = await response.json()
            return response_data


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI Gateway test client")
    parser.add_argument("--url", default="http://localhost:8080", help="Gateway URL")
    parser.add_argument("--api-key", default="pepperpy-demo-key", help="API key")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Model to use")
    parser.add_argument(
        "--operation",
        choices=["chat", "complete", "status"],
        default="chat",
        help="Operation to perform",
    )
    parser.add_argument(
        "prompt", nargs="?", default="Hello, how are you?", help="Prompt text"
    )

    return parser.parse_args()


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_args()

    try:
        # Perform the requested operation
        if args.operation == "chat":
            result = await chat_request(args.url, args.api_key, args.prompt, args.model)
        elif args.operation == "complete":
            result = await completion_request(
                args.url, args.api_key, args.prompt, args.model
            )
        elif args.operation == "status":
            result = await check_status(args.url)
        else:
            print(f"Unknown operation: {args.operation}")
            return 1

        # Print the result
        print(json.dumps(result, indent=2))

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
