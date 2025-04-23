from typing import dict, list, Any

from pepperpy.core.embedding import EmbeddingProvider
from pepperpy.core.plugin import WorkflowProvider
from pepperpy.core.state import State
from pepperpy.core.types import WorkflowResult
from pepperpy.workflow.base import WorkflowError
from pepperpy.workflow import WorkflowProvider


class EmbeddingTestWorkflow(WorkflowProvider):
    def __init__(self, config: dict[str, Any], state: State):
        super().__init__(config, state)
        self.model = config.get("model", "text-embedding-ada-002")
        self.batch_size = config.get("batch_size", 100)
        self.normalize = config.get("normalize", True)
        self.embedding_provider: EmbeddingProvider | None = None

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        self.embedding_provider = await self.state.get_embedding_provider()

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        pass

    async def execute(
        self, texts: list[str], query: str | None = None
    ) -> WorkflowResult:
        if not texts:
            return WorkflowResult(success=False, error="No texts provided")

        try:
            if not self.embedding_provider:
                return WorkflowResult(
                    success=False, error="Embedding provider not initialized"
                )

            embeddings = await self.embedding_provider.get_embeddings(
                texts, batch_size=self.batch_size
            )
            result: dict[str, Any] = {"embeddings": embeddings}

            if query:
                query_embedding = await self.embedding_provider.get_embeddings(
                    [query], batch_size=1
                )
                similarities = await self.embedding_provider.get_similarities(
                    query_embedding[0], embeddings
                )
                result["similarities"] = similarities

            return WorkflowResult(success=True, result=result)

        except Exception as e:
            raise WorkflowError(f"Operation failed: {e}") from e
            return WorkflowResult(success=False, error=str(e))
