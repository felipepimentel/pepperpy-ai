#!/usr/bin/env python3
"""
PepperPy AI Mesh Test Client

This script provides a comprehensive test client for the AI Mesh solution,
demonstrating various capabilities and features of the system.
"""

import argparse
import asyncio
import json
import sys

import aiohttp


async def run_test_suite(host: str, port: int, api_key: str) -> None:
    """Run a comprehensive test suite against the AI Mesh.

    Args:
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print(f"Running test suite against AI Mesh at http://{host}:{port}")

    async with aiohttp.ClientSession() as session:
        # Test basic chat
        await test_basic_chat(session, host, port, api_key)

        # Test model-specific chat
        await test_model_specific_chat(session, host, port, api_key)

        # Test cost-optimized routing
        await test_cost_optimized_routing(session, host, port, api_key)

        # Test latency-optimized routing
        await test_latency_optimized_routing(session, host, port, api_key)

        # Test contextual routing
        await test_contextual_routing(session, host, port, api_key)

        # Test fallback routing
        await test_fallback_routing(session, host, port, api_key)

        # Test ensemble methods
        await test_ensemble_methods(session, host, port, api_key)

        # Test calculator tool
        await test_calculator_tool(session, host, port, api_key)

        # Test weather tool
        await test_weather_tool(session, host, port, api_key)

        # Test authentication
        await test_authentication(session, host, port)

        print("\nTest suite completed!")


async def test_basic_chat(session, host: str, port: int, api_key: str) -> None:
    """Test basic chat functionality.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Basic Chat ===")

    url = f"http://{host}:{port}/api/llm"
    headers = {"X-API-Key": api_key}

    data = {
        "operation": "chat",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
    }

    try:
        async with session.post(url, json=data, headers=headers) as response:
            print(f"Status: {response.status}")

            if response.status == 200:
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Error: {e}")


async def test_model_specific_chat(session, host: str, port: int, api_key: str) -> None:
    """Test chat with specific models.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Model-Specific Chat ===")

    models = ["gpt-3.5-turbo", "gpt-4", "claude-instant", "claude-2"]

    for model in models:
        print(f"\nTesting with model: {model}")

        url = f"http://{host}:{port}/api/{model}"
        headers = {"X-API-Key": api_key}

        data = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "What is the capital of France?"}],
        }

        try:
            async with session.post(url, json=data, headers=headers) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"Error: {await response.text()}")
        except Exception as e:
            print(f"Error: {e}")


async def test_cost_optimized_routing(
    session, host: str, port: int, api_key: str
) -> None:
    """Test cost-optimized routing.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Cost-Optimized Routing ===")

    url = f"http://{host}:{port}/api/llm"
    headers = {"X-API-Key": api_key}

    data = {
        "operation": "chat",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
        "routing_strategy": "cost",
    }

    try:
        async with session.post(url, json=data, headers=headers) as response:
            print(f"Status: {response.status}")

            if response.status == 200:
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Error: {e}")


async def test_latency_optimized_routing(
    session, host: str, port: int, api_key: str
) -> None:
    """Test latency-optimized routing.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Latency-Optimized Routing ===")

    url = f"http://{host}:{port}/api/llm"
    headers = {"X-API-Key": api_key}

    data = {
        "operation": "chat",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
        "routing_strategy": "latency",
    }

    try:
        async with session.post(url, json=data, headers=headers) as response:
            print(f"Status: {response.status}")

            if response.status == 200:
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Error: {e}")


async def test_contextual_routing(session, host: str, port: int, api_key: str) -> None:
    """Test contextual routing.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Contextual Routing ===")

    test_cases = [
        {
            "description": "Code-related query",
            "content": "Write a Python function to calculate the factorial of a number.",
        },
        {
            "description": "Math-related query",
            "content": "Solve the equation 2x + 5 = 15.",
        },
        {
            "description": "Creative query",
            "content": "Write a short poem about the ocean.",
        },
        {
            "description": "Reasoning query",
            "content": "Analyze the pros and cons of remote work.",
        },
    ]

    url = f"http://{host}:{port}/api/llm"
    headers = {"X-API-Key": api_key}

    for test_case in test_cases:
        print(f"\nTesting {test_case['description']}")

        data = {
            "operation": "chat",
            "messages": [{"role": "user", "content": test_case["content"]}],
            "routing_strategy": "contextual",
        }

        try:
            async with session.post(url, json=data, headers=headers) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"Error: {await response.text()}")
        except Exception as e:
            print(f"Error: {e}")


async def test_fallback_routing(session, host: str, port: int, api_key: str) -> None:
    """Test fallback routing.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Fallback Routing ===")

    url = f"http://{host}:{port}/api/llm"
    headers = {"X-API-Key": api_key}

    data = {
        "operation": "chat",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
        "routing_strategy": "fallback",
        "model": "nonexistent-model",  # This should trigger fallback
    }

    try:
        async with session.post(url, json=data, headers=headers) as response:
            print(f"Status: {response.status}")

            if response.status == 200:
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Error: {e}")


async def test_ensemble_methods(session, host: str, port: int, api_key: str) -> None:
    """Test ensemble methods.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Ensemble Methods ===")

    ensemble_methods = ["first", "majority", "all"]

    for method in ensemble_methods:
        print(f"\nTesting ensemble method: {method}")

        url = f"http://{host}:{port}/api/llm"
        headers = {"X-API-Key": api_key}

        data = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "What is the capital of France?"}],
            "routing_strategy": "ensemble",
            "ensemble": "diverse",
            "ensemble_method": method,
        }

        try:
            async with session.post(url, json=data, headers=headers) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"Error: {await response.text()}")
        except Exception as e:
            print(f"Error: {e}")


async def test_calculator_tool(session, host: str, port: int, api_key: str) -> None:
    """Test calculator tool.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Calculator Tool ===")

    test_cases = [
        {"description": "Simple addition", "expression": "2 + 2"},
        {"description": "Complex expression", "expression": "(35 * 2) / 7 + 4"},
        {"description": "Mathematical functions", "expression": "pow(2, 8) + sqrt(16)"},
    ]

    url = f"http://{host}:{port}/api/calculator"
    headers = {"X-API-Key": api_key}

    for test_case in test_cases:
        print(f"\nTesting {test_case['description']}")

        data = {"expression": test_case["expression"]}

        try:
            async with session.post(url, json=data, headers=headers) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"Error: {await response.text()}")
        except Exception as e:
            print(f"Error: {e}")


async def test_weather_tool(session, host: str, port: int, api_key: str) -> None:
    """Test weather tool.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
        api_key: API key for authentication
    """
    print("\n=== Testing Weather Tool ===")

    test_cases = [
        {"description": "Weather in Paris", "location": "Paris, France"},
        {"description": "Weather in New York", "location": "New York, USA"},
        {"description": "Weather in Tokyo", "location": "Tokyo, Japan"},
    ]

    url = f"http://{host}:{port}/api/weather"
    headers = {"X-API-Key": api_key}

    for test_case in test_cases:
        print(f"\nTesting {test_case['description']}")

        data = {"location": test_case["location"]}

        try:
            async with session.post(url, json=data, headers=headers) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"Error: {await response.text()}")
        except Exception as e:
            print(f"Error: {e}")


async def test_authentication(session, host: str, port: int) -> None:
    """Test authentication.

    Args:
        session: aiohttp session
        host: AI Mesh host
        port: AI Mesh port
    """
    print("\n=== Testing Authentication ===")

    url = f"http://{host}:{port}/api/llm"

    # Test with invalid API key
    print("\nTesting with invalid API key")

    data = {
        "operation": "chat",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
    }

    try:
        async with session.post(
            url, json=data, headers={"X-API-Key": "invalid-key"}
        ) as response:
            print(f"Status: {response.status}")

            if response.status == 200:
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Error: {e}")

    # Test with missing API key
    print("\nTesting with missing API key")

    try:
        async with session.post(url, json=data) as response:
            print(f"Status: {response.status}")

            if response.status == 200:
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"Error: {await response.text()}")
    except Exception as e:
        print(f"Error: {e}")


def main() -> int:
    """Command-line entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Test the PepperPy AI Mesh")
    parser.add_argument(
        "--host", default="localhost", help="AI Mesh host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8081, help="AI Mesh port (default: 8081)"
    )
    parser.add_argument(
        "--api-key",
        default="test-key-1",
        help="API key for authentication (default: test-key-1)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(run_test_suite(args.host, args.port, args.api_key))
        return 0
    except KeyboardInterrupt:
        print("Test client stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
