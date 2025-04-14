"""RAG test workflow provider implementation."""

import logging
from typing import Any

from pepperpy import PepperPy
from pepperpy.core.base import PepperpyError
from pepperpy.workflow.base import WorkflowProvider
from pepperpy.workflow.decorators import workflow


class WorkflowError(PepperpyError):
    """Base error for workflow errors."""


@workflow(
    name="rag_test",
    description="Test workflow for RAG capabilities",
    version="0.1.0",
)
class RAGTestWorkflow(WorkflowProvider):
    """Test workflow for RAG capabilities."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration."""
        super().__init__(**kwargs)

        # Configuration values with defaults
        self.config = kwargs
        self.collection = self.config.get("collection", "test_collection")
        self.embedding_model = self.config.get(
            "embedding_model", "text-embedding-ada-002"
        )
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)

        # Initialize state
        self.initialized = False
        self.rag = None
        self.logger = logging.getLogger(__name__)
        self.pepperpy = None

    async def initialize(self) -> None:
        """Initialize resources."""
        if self.initialized:
            return

        try:
            # Initialize RAG provider
            self.pepperpy = PepperPy()
            self.rag = self.pepperpy.get_rag(
                provider="chroma",
                collection=self.collection,
                embedding_model=self.embedding_model,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            await self.rag.initialize()
            self.initialized = True
            self.logger.info("Initialized RAG test workflow")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG test workflow: {e}")
            raise WorkflowError("Failed to initialize RAG") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        try:
            if self.rag:
                await self.rag.cleanup()
            self.initialized = False
            self.logger.info("Cleaned up RAG test workflow")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute workflow.

        Args:
            input_data: Contains task and parameters

        Returns:
            Execution result
        """
        try:
            # Initialize if needed
            if not self.initialized:
                await self.initialize()

            # Get task from input
            task = input_data.get("task", "query")

            if task == "add_documents":
                return await self._add_documents(input_data)
            elif task == "query":
                return await self._query(input_data)
            else:
                raise WorkflowError(f"Unknown task: {task}")

        except Exception as e:
            self.logger.error(f"Error executing RAG test: {e}")
            return {
                "status": "error",
                "message": str(e),
                "task": input_data.get("task"),
            }

    async def _add_documents(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Add documents to the RAG system.

        Args:
            input_data: Contains documents to add

        Returns:
            Result of document addition
        """
        documents = input_data.get("documents", [])
        if not documents:
            raise WorkflowError("No documents provided")

        try:
            # Add documents to RAG system
            doc_ids = await self.rag.add_documents(documents)

            return {
                "status": "success",
                "task": "add_documents",
                "documents_added": len(doc_ids),
                "document_ids": doc_ids,
            }
        except Exception as e:
            raise WorkflowError(f"Failed to add documents: {e}") from e

    async def _query(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Query the RAG system.

        Args:
            input_data: Contains query and parameters

        Returns:
            Query results
        """
        query = input_data.get("query")
        if not query:
            raise WorkflowError("No query provided")

        try:
            # Get optional parameters
            top_k = input_data.get("top_k", 5)
            threshold = input_data.get("threshold", 0.5)

            # Execute query
            results = await self.rag.query(
                query=query, top_k=top_k, threshold=threshold
            )

            return {
                "status": "success",
                "task": "query",
                "query": query,
                "results": results,
                "metadata": {
                    "top_k": top_k,
                    "threshold": threshold,
                    "collection": self.collection,
                },
            }
        except Exception as e:
            raise WorkflowError(f"Failed to execute query: {e}") from e
