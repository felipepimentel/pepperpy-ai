"""Example of a comprehensive development assistant using PepperPy agents.

This example demonstrates a full-featured development assistant that combines:
1. Interactive code review with constructive feedback
2. Technical concept explanations and best practices
3. Refactoring suggestions with implementation help
4. Test and documentation assistance
5. Integration with technical documentation through RAG
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, List, Optional, Union

from dotenv import load_dotenv

from pepperpy.agents import create_agent_group, execute_task, cleanup_group
from pepperpy.agents.provider import Message
from pepperpy.rag.providers.supabase import SupabaseRAGProvider


async def search_docs(query: str) -> str:
    """Search technical documentation."""
    # In a real implementation, this would search actual documentation
    docs = {
        "list comprehension": """
        List comprehension is a concise way to create lists in Python.
        Syntax: [expression for item in iterable if condition]
        Example: squares = [x**2 for x in range(10)]
        Benefits:
        - More readable than loops
        - Often faster than manual list building
        - Follows functional programming principles
        """,
        "type hints": """
        Type hints in Python provide static type information.
        Key concepts:
        - Basic types: str, int, float, bool
        - Container types: List[T], Dict[K, V], Optional[T]
        - Union types: Union[T1, T2]
        - Custom types: TypeVar, Protocol
        Benefits:
        - Better code documentation
        - IDE support
        - Static type checking
        """,
        "testing": """
        Python testing best practices:
        1. Use pytest for testing
        2. Follow AAA pattern: Arrange, Act, Assert
        3. Test edge cases and error conditions
        4. Use fixtures for test setup
        5. Aim for high test coverage
        Example:
        def test_function():
            # Arrange
            data = [1, 2, 3]
            # Act
            result = process_data(data)
            # Assert
            assert result == [1, 2, 3]
        """
    }
    return docs.get(query.lower(), f"No documentation found for: {query}")


async def run_tests(code: str) -> str:
    """Run tests on the provided code."""
    # Simulated test execution with more realistic output
    return """
    === Test Results ===
    test_empty_input ✓
    test_none_values ✓
    test_invalid_types ✓
    test_missing_keys ✓
    test_valid_input ✓
    
    5 passed, 0 failed
    Coverage: 95%
    """


async def analyze_complexity(code: str) -> str:
    """Analyze code complexity."""
    # Simulated analysis with more realistic output
    return """
    === Complexity Analysis ===
    Time Complexity: O(n) - Linear time
    Space Complexity: O(n) - Linear space
    
    Breakdown:
    - Single loop through input: O(n)
    - Dictionary operations: O(1)
    - List append: O(1)
    
    Recommendations:
    - Current implementation is optimal for the task
    - Consider using list comprehension for better readability
    """


async def print_stream(stream: Union[List[Message], AsyncGenerator[Message, None]]) -> None:
    """Print messages or stream with appropriate formatting."""
    if isinstance(stream, list):
        for msg in stream:
            print(f"\n{msg.role}: {msg.content}\n")
            print("-" * 80)
    else:
        current_role = None
        async for msg in stream:
            if msg.role != current_role:
                if current_role is not None:
                    print("\n" + "-" * 80)
                print(f"\n{msg.role}: ", end="", flush=True)
                current_role = msg.role
            print(msg.content, end="", flush=True)
        print("\n" + "-" * 80)


async def main() -> None:
    """Run the development assistant example."""
    # Load environment variables
    load_dotenv()

    # Initialize RAG system with Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
    
    rag_provider = SupabaseRAGProvider(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )

    # Define development tools
    tools = [
        {
            "name": "search_docs",
            "description": "Search technical documentation for references",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'list comprehension', 'type hints', 'testing')",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "run_tests",
            "description": "Run tests on the provided code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to test",
                    },
                },
                "required": ["code"],
            },
        },
        {
            "name": "analyze_complexity",
            "description": "Analyze code complexity",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The code to analyze",
                    },
                },
                "required": ["code"],
            },
        },
    ]

    # Configure LLM
    llm_config = {
        "config_list": [{
            "model": "anthropic/claude-3-opus-20240229",
            "api_key": os.getenv("PEPPERPY_LLM__OPENROUTER_API_KEY", ""),
            "base_url": "https://openrouter.ai/api/v1",
            "api_type": "openai",
        }],
        "temperature": 0.7,
        "functions": tools,
    }

    # Create development team
    group_id = await create_agent_group(
        agents=[
            {
                "type": "user",
                "name": "user",
                "system_message": "",
                "config": {},
            },
            {
                "type": "assistant",
                "name": "dev_assistant",
                "system_message": (
                    "You are a comprehensive development assistant with expertise in:\n"
                    "1. Code review and quality assessment\n"
                    "2. Technical design and architecture\n"
                    "3. Testing and quality assurance\n"
                    "4. Best practices and patterns\n"
                    "\nYou can use these tools to help:\n"
                    "- search_docs: Look up technical documentation\n"
                    "- run_tests: Execute tests on code\n"
                    "- analyze_complexity: Analyze code complexity\n"
                ),
                "config": {},
            }
        ],
        name="Development Assistant",
        description="A comprehensive development assistant that helps with code review, testing, and technical guidance.",
        use_group_chat=False,
        llm_config=llm_config,
    )

    try:
        # Example 1: Code Review
        print("\n=== Code Review Session ===")
        code_to_review = """
def process_data(data):
    results = []
    for item in data:
        if item != None:
            if type(item) == dict:
                if 'value' in item.keys():
                    results.append(item['value'])
    return results
"""
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Please review this code and suggest improvements. Consider:\n"
                "1. Code style and readability\n"
                "2. Performance optimizations\n"
                "3. Type safety and error handling\n"
                "4. Best practices for Python\n"
                f"\nCode:\n```python\n{code_to_review}\n```"
            ),
        )
        await print_stream(messages)

        # Example 2: Test Implementation
        print("\n=== Test Implementation Session ===")
        improved_code = """
from typing import List, Any, Dict

def process_data(data: List[Any]) -> List[Any]:
    \"\"\"
    Process the input data and return a list of values from dictionaries.

    Args:
        data: A list of items to be processed.

    Returns:
        A list of values extracted from dictionaries in the input data.
    \"\"\"
    return [item['value'] for item in data if isinstance(item, dict) and 'value' in item]
"""
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Let's write comprehensive tests for this improved version of the code:\n"
                f"```python\n{improved_code}\n```\n\n"
                "Please help me:\n"
                "1. Identify test cases including edge cases\n"
                "2. Implement the tests following best practices\n"
                "3. Ensure good test coverage\n"
                "4. Add appropriate test documentation"
            ),
        )
        await print_stream(messages)

        # Example 3: Documentation and Type Hints
        print("\n=== Documentation Session ===")
        messages = await execute_task(
            group_id=group_id,
            task=(
                "Let's improve the documentation for this function:\n"
                f"```python\n{improved_code}\n```\n\n"
                "Please enhance the documentation with:\n"
                "1. More detailed type hints for better type safety\n"
                "2. A more comprehensive docstring following standards\n"
                "3. More examples in the documentation\n"
                "4. Clearer parameter and return value descriptions\n"
                "5. Any additional documentation best practices you recommend"
            ),
        )
        await print_stream(messages)

    finally:
        # Clean up
        await cleanup_group(group_id)
        await rag_provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 