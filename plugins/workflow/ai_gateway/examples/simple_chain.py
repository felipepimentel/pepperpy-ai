"""Example of chaining operations with AI Gateway."""

import asyncio

from plugins.workflow.ai_gateway.base_workflow import BaseWorkflow


async def analyze_document_with_tools() -> None:
    """Example of chaining document analysis with tools."""
    async with BaseWorkflow(
        llm_provider="basic", use_rag=True, tools=["calculator", "search"]
    ) as workflow:
        # Chain multiple operations
        result = await workflow.execute_chain(
            [
                # First analyze document
                {
                    "type": "rag",
                    "query": "Extract all numerical values",
                    "context_path": "data/report.pdf",
                },
                # Calculate sum of values
                {
                    "type": "tool",
                    "name": "calculator",
                    "inputs": {"expr": "2500 + 1500 + 3000"},  # Values from doc
                },
                # Search for market context
                {
                    "type": "tool",
                    "name": "search",
                    "inputs": {"query": "latest market trends 2024"},
                },
                # Generate final analysis
                {
                    "type": "chat",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Analyze the document values and market trends",
                        }
                    ],
                },
            ]
        )

        if result.is_success and result.data:
            print("Chain Results:")
            for step in result.data:
                print(f"- {step['type']}: {step['result']}")
        else:
            print(f"Error: {result.error_message or 'No data returned'}")


async def main() -> None:
    """Run example."""
    await analyze_document_with_tools()


if __name__ == "__main__":
    asyncio.run(main())
