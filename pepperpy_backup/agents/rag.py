"""RAG (Retrieval-Augmented Generation) agent implementation."""
import logging
from typing import Any, Dict, List, Optional, cast, Sequence

from .base import BaseAgent
from ..providers.llm.base import BaseLLMProvider
from ..providers.memory.base import BaseMemoryProvider, Message
from ..providers.vector_store.base import BaseVectorStoreProvider
from ..providers.embeddings.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

@BaseAgent.register("rag")
class RAGAgent(BaseAgent):
    """RAG agent implementation."""
    
    def __init__(
        self,
        llm: BaseLLMProvider,
        capabilities: Dict[str, Any],
        config: Dict[str, Any]
    ):
        """Initialize the RAG agent.
        
        Args:
            llm: LLM provider instance.
            capabilities: Dictionary of agent capabilities.
            config: Agent configuration.
        """
        super().__init__(llm, capabilities, config)
        
        # Verify required capabilities
        if not self.vector_store:
            raise ValueError("Vector store provider required")
        if not self.embeddings:
            raise ValueError("Embedding provider required")
            
        # Cast providers for type checking
        self.vector_store = cast(BaseVectorStoreProvider, self.vector_store)
        self.embeddings = cast(BaseEmbeddingProvider, self.embeddings)
        
        # RAG-specific configuration
        self.system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
        self.max_history = config.get("max_history", 10)
        self.temperature = config.get("temperature", 0.7)
        self.num_chunks = config.get("num_chunks", 3)
        
        # Message history
        self.messages: List[Message] = []
        
        # Memory provider (from base class)
        self.memory: Optional[BaseMemoryProvider] = self.memory
    
    async def process(self, input_data: str) -> str:
        """Process user input and generate a response.
        
        Args:
            input_data: User input text.
            
        Returns:
            Generated response.
            
        Raises:
            ValueError: If agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
            
        if not self.embeddings or not self.vector_store:
            raise ValueError("Required providers not initialized")
            
        try:
            # Add user message to history
            user_message = Message(content=input_data, role="user")
            await self._add_message(user_message)
            
            # Get relevant chunks from vector store
            query_embedding = await self.embeddings.embed_text(input_data)
            if isinstance(query_embedding, list):
                # Single embedding
                if all(isinstance(x, float) for x in query_embedding):
                    chunks = await self.vector_store.search(
                        query_vector=cast(List[float], query_embedding),
                        k=self.num_chunks
                    )
                else:
                    raise ValueError("Invalid embedding format")
            else:
                raise ValueError("Invalid embedding format")
            
            # Build conversation history with context
            history = self._build_history(chunks)
            
            # Generate response
            response = await self.llm.generate(
                prompt=history,
                temperature=self.temperature
            )
            
            # Add assistant message to history
            assistant_message = Message(content=response, role="assistant")
            await self._add_message(assistant_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process input: {str(e)}")
            raise RuntimeError(f"Failed to process input: {str(e)}")
    
    async def _add_message(self, message: Message) -> None:
        """Add a message to history and memory.
        
        Args:
            message: Message to add.
        """
        # Add to in-memory history
        self.messages.append(message)
        
        # Trim history if needed
        if len(self.messages) > self.max_history * 2:  # Keep extra for context
            self.messages = self.messages[-self.max_history * 2:]
        
        # Add to persistent memory if available
        if self.memory:
            await self.memory.add_message(message)
    
    def _build_history(self, chunks: List[Dict[str, Any]]) -> str:
        """Build conversation history string with context.
        
        Args:
            chunks: Retrieved context chunks.
            
        Returns:
            Formatted conversation history.
        """
        # Start with system prompt
        history = [f"System: {self.system_prompt}"]
        
        # Add context
        if chunks:
            history.append("Context:")
            for chunk in chunks:
                if "metadata" in chunk and "content" in chunk["metadata"]:
                    history.append(chunk["metadata"]["content"])
        
        # Add recent messages
        history.append("Conversation:")
        for msg in self.messages[-self.max_history * 2:]:
            role = msg.role.title()
            history.append(f"{role}: {msg.content}")
        
        return "\n\n".join(history)
    
    async def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a document to the vector store.
        
        Args:
            content: Document content.
            metadata: Optional document metadata.
            
        Raises:
            ValueError: If agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
            
        if not self.embeddings or not self.vector_store:
            raise ValueError("Required providers not initialized")
            
        try:
            # Generate embedding
            embedding = await self.embeddings.embed_text(content)
            if isinstance(embedding, list):
                # Single embedding
                if all(isinstance(x, float) for x in embedding):
                    # Add to vector store
                    metadata = metadata or {}
                    metadata["content"] = content
                    await self.vector_store.add_vectors(
                        vectors=[cast(List[float], embedding)],
                        metadata=[metadata]
                    )
                else:
                    raise ValueError("Invalid embedding format")
            else:
                raise ValueError("Invalid embedding format")
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            raise RuntimeError(f"Failed to add document: {str(e)}")
    
    async def search_history(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Search conversation history.
        
        Args:
            query: Search query.
            limit: Optional limit on number of results.
            
        Returns:
            List of matching messages.
            
        Raises:
            ValueError: If agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
            
        if not self.memory:
            # Search in-memory history
            messages = []
            for msg in reversed(self.messages):
                if query.lower() in msg.content.lower():
                    messages.append(msg)
                    if limit and len(messages) >= limit:
                        break
            return messages
            
        # Search in persistent memory
        return await self.memory.search_messages(query, limit)
    
    async def clear_history(self) -> None:
        """Clear conversation history.
        
        Raises:
            ValueError: If agent is not initialized.
        """
        if not self.is_initialized:
            raise ValueError("Agent not initialized")
            
        # Clear in-memory history
        self.messages.clear()
        
        # Clear persistent memory if available
        if self.memory:
            await self.memory.clear_messages() 