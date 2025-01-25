"""RAG (Retrieval Augmented Generation) agent implementation."""

import logging
from typing import Any, Dict, List, Optional, cast

from pepperpy.core.utils.errors import PepperpyError
from pepperpy.providers.llm.base import BaseLLMProvider
from pepperpy.providers.vector_store.base import BaseVectorStoreProvider
from pepperpy.providers.embedding.base import BaseEmbeddingProvider
from pepperpy.agents.base.base_agent import BaseAgent, AgentError


logger = logging.getLogger(__name__)


class RAGAgentError(AgentError):
    """RAG agent error class."""
    pass


@BaseAgent.register("rag")
class RAGAgent(BaseAgent):
    """RAG (Retrieval Augmented Generation) agent implementation.
    
    This agent combines vector store retrieval with LLM generation to provide
    context-aware responses based on retrieved documents.
    """
    
    def __init__(
        self,
        name: str,
        llm_provider: BaseLLMProvider,
        vector_store_provider: BaseVectorStoreProvider,
        embedding_provider: BaseEmbeddingProvider,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RAG agent.
        
        Args:
            name: Agent name
            llm_provider: LLM provider instance
            vector_store_provider: Vector store provider instance
            embedding_provider: Embedding provider instance
            config: Optional configuration
            
        Raises:
            RAGAgentError: If required providers are missing
        """
        if not vector_store_provider:
            raise RAGAgentError("Vector store provider is required")
        if not embedding_provider:
            raise RAGAgentError("Embedding provider is required")
            
        super().__init__(
            name=name,
            llm_provider=llm_provider,
            vector_store_provider=vector_store_provider,
            embedding_provider=embedding_provider,
            config=config,
        )
        
        self._top_k = config.get('top_k', 3) if config else 3
        self._similarity_threshold = config.get('similarity_threshold', 0.7) if config else 0.7
        
    async def _setup(self) -> None:
        """Set up RAG agent resources."""
        try:
            await self.vector_store.initialize()
            await self.embeddings.initialize()
        except Exception as e:
            raise RAGAgentError(f"Failed to set up RAG agent: {e}")
            
    async def _teardown(self) -> None:
        """Clean up RAG agent resources."""
        try:
            await self.vector_store.cleanup()
            await self.embeddings.cleanup()
        except Exception as e:
            raise RAGAgentError(f"Failed to clean up RAG agent: {e}")
            
    def _validate(self) -> None:
        """Validate RAG agent configuration."""
        if not isinstance(self._top_k, int) or self._top_k < 1:
            raise RAGAgentError("top_k must be a positive integer")
        if not isinstance(self._similarity_threshold, float) or not 0 <= self._similarity_threshold <= 1:
            raise RAGAgentError("similarity_threshold must be a float between 0 and 1")
            
    async def process(
        self,
        input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process input with RAG pipeline.
        
        Args:
            input: Input text
            context: Optional processing context
            
        Returns:
            Dictionary containing:
                - response: Generated response
                - documents: Retrieved documents
                - metadata: Processing metadata
                
        Raises:
            RAGAgentError: If processing fails
        """
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.embed_text(input)
            
            # Retrieve relevant documents
            results = await self.vector_store.search_vectors(
                query_embedding,
                k=self._top_k,
                threshold=self._similarity_threshold,
            )
            
            # Extract documents and metadata
            documents = []
            metadata = []
            for result in results:
                documents.append(result['document'])
                metadata.append(result['metadata'])
                
            # Generate response with context
            prompt = self._build_prompt(input, documents)
            response = await self.llm.generate(prompt, context)
            
            return {
                'response': response,
                'documents': documents,
                'metadata': {
                    'retrieved_docs': metadata,
                    'similarity_scores': [r['score'] for r in results],
                },
            }
        except Exception as e:
            raise RAGAgentError(f"Failed to process input: {e}")
            
    def _build_prompt(self, query: str, documents: List[str]) -> str:
        """Build prompt with retrieved documents.
        
        Args:
            query: User query
            documents: Retrieved documents
            
        Returns:
            Formatted prompt
        """
        context = "\n\n".join(f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents))
        return f"""Context information is below.
---------------------
{context}
---------------------
Given the context information, please answer the following question:
{query}

Answer:""" 