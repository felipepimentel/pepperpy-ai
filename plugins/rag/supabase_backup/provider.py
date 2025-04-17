"""Supabase RAG provider implementation."""

from typing import Any, Dict, List, Optional

from supabase._async.client import AsyncClient as Client, create_client

from ..base import RAGProvider
from ..errors import RAGError
from ..models import Document, SearchResult


class SupabaseRAGProvider(RAGProvider):
    """Supabase-based RAG provider."""

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        table_name: str = "documents",
        provider_name: Optional[str] = None,
    ) -> None:
        self.name = provider_name or "supabase"
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.table_name = table_name
        self._client: Optional[Client] = None

    async def initialize(self) -> None:
        if self._client is not None:
            return

        try:
            self._client = await create_client(self.supabase_url, self.supabase_key)
            if self._client is None:
                raise RAGError("Failed to create Supabase client")
        except Exception as e:
            raise RAGError(f"Failed to initialize Supabase client: {e}") from e

    async def store(self, documents: List[Document]) -> None:
        if not documents:
            return

        if self._client is None:
            raise RAGError("Supabase client not initialized")

        try:
            data = [
                {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "embedding": doc.embedding,
                }
                for doc in documents
            ]
            await self._client.table(self.table_name).upsert(data).execute()
        except Exception as e:
            raise RAGError(f"Failed to store documents: {e}") from e

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        if self._client is None:
            raise RAGError("Supabase client not initialized")

        try:
            # Build the match_documents RPC call
            rpc = self._client.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                    "filter": filter_metadata or {},
                },
            )

            # Execute the query
            response = await rpc.execute()
            if not response.data:
                return []

            # Convert response to SearchResults
            results = []
            for item in response.data:
                results.append(
                    SearchResult(
                        document=Document(
                            id=item["id"],
                            content=item["content"],
                            metadata=item.get("metadata", {}),
                            embedding=item.get("embedding"),
                        ),
                        score=float(item["similarity"]),
                    )
                )

            return results
        except Exception as e:
            raise RAGError(f"Failed to search documents: {e}") from e

    def get_config(self) -> Dict[str, Any]:
        return {
            "supabase_url": self.supabase_url,
            "table_name": self.table_name,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "capabilities": ["vector_store", "similarity_search"],
            "supports_metadata_filter": True,
        } 