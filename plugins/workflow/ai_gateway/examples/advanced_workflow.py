"""Example of advanced AI Gateway workflow usage."""

import asyncio
from typing import Any

from pepperpy.core.base import PepperpyError
from plugins.workflow.ai_gateway.base_workflow import BaseWorkflow, WorkflowResult


class DocumentAnalyzer(BaseWorkflow):
    """Advanced document analysis workflow."""

    def __init__(self) -> None:
        """Initialize with all needed capabilities."""
        super().__init__(
            llm_provider="gpt4", llm_model="gpt-4", use_rag=True, use_vision=True
        )

    async def analyze_document(
        self, document_path: str, query: str, image_paths: list[str] | None = None
    ) -> WorkflowResult[dict[str, Any]]:
        """Analyze document with RAG and optional images.

        Args:
            document_path: Path to main document
            query: Analysis query
            image_paths: Optional paths to related images

        Returns:
            Analysis result
        """
        try:
            # Load and analyze document
            rag_result = await self.execute_rag(query=query, context_path=document_path)
            if not rag_result.success:
                return rag_result

            # Analyze images if provided
            image_results = {}
            if image_paths:
                for image_path in image_paths:
                    vision_result = await self.execute_vision(
                        prompt="Analyze this image in detail", image_path=image_path
                    )
                    if vision_result.success:
                        image_results[image_path] = vision_result.data

            # Combine analysis
            final_prompt = {
                "query": query,
                "document_analysis": rag_result.data,
                "image_analysis": image_results,
            }

            # Get final analysis
            return await self.execute_chat(
                messages=[
                    {
                        "role": "user",
                        "content": f"Provide a comprehensive analysis combining this information: {final_prompt}",
                    }
                ]
            )

        except Exception as e:
            return WorkflowResult(success=False, error=str(e))


class ToolChainExecutor(BaseWorkflow):
    """Advanced tool chain execution workflow."""

    def __init__(self) -> None:
        """Initialize with tools and analysis capability."""
        super().__init__(llm_provider="mock", tools=["calculator", "weather", "search"])

    async def execute_chain(
        self, operations: list[dict[str, Any]]
    ) -> WorkflowResult[list[dict[str, Any]]]:
        """Execute a chain of tool operations with analysis.

        Args:
            operations: List of tool operations to execute

        Returns:
            Results and analysis for each operation
        """
        try:
            results = []
            for op in operations:
                # Execute tool
                tool_result = await self.execute_tool(
                    tool_name=op["tool"], inputs=op.get("inputs", {})
                )
                if not tool_result.success:
                    return WorkflowResult(
                        success=False,
                        error=f"Tool execution failed: {tool_result.error}",
                    )

                # Analyze result
                analysis = await self.execute_chat(
                    messages=[
                        {
                            "role": "user",
                            "content": f"Analyze this tool result: {tool_result.data}",
                        }
                    ]
                )

                results.append({
                    "tool": op["tool"],
                    "result": tool_result.data,
                    "analysis": analysis.data if analysis.success else None,
                })

            return WorkflowResult(success=True, data=results)

        except Exception as e:
            return WorkflowResult(success=False, error=str(e))


async def main() -> None:
    """Run advanced workflow examples."""
    try:
        # Document analysis example
        async with DocumentAnalyzer() as analyzer:
            doc_result = await analyzer.analyze_document(
                document_path="path/to/report.pdf",
                query="What are the key findings?",
                image_paths=["path/to/chart1.png", "path/to/chart2.png"],
            )
            if doc_result.success:
                print(f"Document Analysis: {doc_result.data}")
            else:
                print(f"Analysis Error: {doc_result.error}")

        # Tool chain example
        async with ToolChainExecutor() as executor:
            chain_result = await executor.execute_chain([
                {"tool": "calculator", "inputs": {"expression": "2 + 2"}},
                {"tool": "weather", "inputs": {"location": "London"}},
                {"tool": "search", "inputs": {"query": "latest AI news"}},
            ])
            if chain_result.success:
                print(f"Tool Chain Results: {chain_result.data}")
            else:
                print(f"Chain Error: {chain_result.error}")

    except PepperpyError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
