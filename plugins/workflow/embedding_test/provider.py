from typing import Any

from pepperpy.core.embedding import EmbeddingProvider
from pepperpy.core.plugin import WorkflowProvider
from pepperpy.core.state import State
from pepperpy.core.types import WorkflowResult


class EmbeddingTestWorkflow(WorkflowProvider):
    def __init__(self, config: dict[str, Any], state: State):
        super().__init__(config, state)
        self.model = config.get("model", "text-embedding-ada-002")
        self.batch_size = config.get("batch_size", 100)
        self.normalize = config.get("normalize", True)
        self.embedding_provider: EmbeddingProvider | None = None

    async def initialize(self) -> None:
        """Initialize the embedding provider."""
        self.embedding_provider = await self.state.get_embedding_provider()

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass

    async def execute(
        self, texts: list[str], query: str | None = None
    ) -> WorkflowResult:
        if not texts:
            return WorkflowResult(success=False, error="No texts provided")

        try:
            if not self.embedding_provider:
                raise ValueError("Embedding provider not initialized")

            embeddings = await self.embedding_provider.get_embeddings(
                texts, batch_size=self.batch_size
            )
            result = {"embeddings": embeddings}

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
            return WorkflowResult(success=False, error=str(e))
