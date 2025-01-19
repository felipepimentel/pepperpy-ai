"""Example demonstrating API expert agent."""

import asyncio
import os

from dotenv import load_dotenv

from pepperpy.agents.api_agent import APIAgent, APIAgentConfig
from pepperpy.llms.huggingface import HuggingFaceLLM, LLMConfig
from pepperpy.tools.functions.api import APITool


# Load environment variables
load_dotenv()


# Example API documentation for JSONPlaceholder
API_DOCS = """
JSONPlaceholder API Documentation:

Base URL: https://jsonplaceholder.typicode.com

Endpoints:
- GET /posts: Get all posts
- GET /posts/{id}: Get post by ID
- GET /posts/{id}/comments: Get comments for post
- GET /users: Get all users
- GET /users/{id}: Get user by ID
- GET /users/{id}/posts: Get posts by user

All endpoints return JSON data.
"""


async def main() -> None:
    """Run the API expert example."""
    # Initialize LLM configuration
    llm_config = LLMConfig(
        model_name=os.getenv("PEPPERPY_MODEL", "anthropic/claude-2"),
        model_kwargs={
            "api_key": os.getenv("PEPPERPY_API_KEY", ""),
            "provider": os.getenv("PEPPERPY_PROVIDER", "openrouter"),
        },
    )

    # Create LLM and tools
    llm = HuggingFaceLLM(llm_config)
    api_tool = APITool(rate_limit=1.0)  # 1 request per second

    try:
        # Create API agent
        agent = APIAgent(
            config=APIAgentConfig(
                llm=llm,
                api_tool=api_tool,
                api_docs=API_DOCS,
            )
        )

        # Initialize agent
        await agent.initialize()

        print("\n=== API Expert Agent ===\n")
        
        # Example requests
        requests = [
            "get all posts",
            "get user with ID 1",
            "get comments for post 1",
            "get all posts by user 1",
        ]
        
        for request in requests:
            print(f"\nRequest: {request}")
            print("-" * 50)
            result = await agent.process(request)
            print(result)
            print()

    finally:
        # Cleanup
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 