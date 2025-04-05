"""Knowledge management workflow plugin."""

import logging
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from pepperpy.workflow.base import PipelineContext, PipelineStage, WorkflowProvider


class DocumentChunkingStage(PipelineStage):
    """Stage for chunking documents into manageable pieces."""

    def __init__(self, chunk_size: int = 1000, **kwargs: Any) -> None:
        """Initialize document chunking stage.

        Args:
            chunk_size: Size of document chunks
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="document_chunking",
            description="Chunk documents into manageable pieces",
        )
        self._chunk_size = chunk_size
        self._overlap = kwargs.get("chunk_overlap", 200)  # Default 20% overlap

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Chunk documents into manageable pieces.

        Args:
            input_data: Input data with documents
            context: Pipeline context

        Returns:
            Chunked documents
        """
        try:
            documents = input_data.get("documents", [])
            if not documents:
                raise ValueError("No documents provided for chunking")

            # Process each document
            chunked_docs = []
            for doc in documents:
                chunks = self._chunk_document(doc)
                chunked_docs.extend(chunks)

            # Store metadata
            context.set_metadata("original_doc_count", len(documents))
            context.set_metadata("chunk_count", len(chunked_docs))
            context.set_metadata("chunk_size", self._chunk_size)

            return {
                "chunks": chunked_docs,
                "count": len(chunked_docs),
                "success": True,
                "message": f"Documents chunked into {len(chunked_docs)} pieces",
                "metadata": {
                    "original_doc_count": len(documents),
                    "chunk_size": self._chunk_size,
                    "overlap": self._overlap,
                },
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "chunks": [],
                "count": 0,
                "success": False,
                "message": f"Document chunking failed: {e}",
                "metadata": {},
            }

    def _chunk_document(self, document: str) -> list[str]:
        """Chunk a document into smaller pieces.

        This is a simple implementation that chunks by character count.
        A more sophisticated implementation would chunk by sentences or paragraphs.
        """
        chunks = []

        # Simple chunking strategy - split by characters with overlap
        doc_len = len(document)
        for i in range(0, doc_len, self._chunk_size - self._overlap):
            end = min(i + self._chunk_size, doc_len)
            chunk = document[i:end]
            chunks.append(chunk)

            if end == doc_len:
                break

        return chunks


class EmbeddingGenerationStage(PipelineStage):
    """Stage for generating embeddings from text chunks."""

    def __init__(
        self, embedding_model: str = "text-embedding-ada-002", **kwargs: Any
    ) -> None:
        """Initialize embedding generation stage.

        Args:
            embedding_model: Model to use for embeddings
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="embedding_generation",
            description="Generate embeddings from text chunks",
        )
        self._model_name = embedding_model
        self._model: SentenceTransformer | None = None
        self._batch_size = kwargs.get("batch_size", 32)

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Generate embeddings from text chunks.

        Args:
            input_data: Input data with text chunks
            context: Pipeline context

        Returns:
            Generated embeddings
        """
        try:
            chunks = input_data.get("chunks", [])
            if not chunks:
                raise ValueError("No text chunks provided for embedding generation")

            # Initialize model if not already done
            if not self._model:
                # In a real implementation, this would use the specified model
                # For this placeholder, we'll use a small SentenceTransformer model
                self._model = SentenceTransformer("all-MiniLM-L6-v2")

            # Generate embeddings
            embeddings = self._generate_embeddings(chunks)

            # Store metadata
            context.set_metadata("embedding_model", self._model_name)
            context.set_metadata("embedding_count", len(embeddings))
            context.set_metadata(
                "embedding_dim", len(embeddings[0]) if embeddings else 0
            )

            return {
                "chunks": chunks,
                "embeddings": embeddings,
                "success": True,
                "message": f"Generated {len(embeddings)} embeddings",
                "metadata": {
                    "embedding_model": self._model_name,
                    "embedding_dim": len(embeddings[0]) if embeddings else 0,
                    "chunk_count": len(chunks),
                },
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "chunks": [],
                "embeddings": [],
                "success": False,
                "message": f"Embedding generation failed: {e}",
                "metadata": {},
            }

    def _generate_embeddings(self, chunks: list[str]) -> list[list[float]]:
        """Generate embeddings for text chunks.

        This is a placeholder implementation that uses SentenceTransformer.
        In a real implementation, this might use OpenAI's embedding API or another service.
        """
        if not chunks:
            return []

        if self._model is None:
            # This should never happen as we initialize in process()
            # but we need to handle it for type checking
            return [[0.0] * 384] * len(chunks)  # Default dimension for all-MiniLM-L6-v2

        # Process in batches to avoid memory issues
        all_embeddings = []
        for i in range(0, len(chunks), self._batch_size):
            batch = chunks[i : i + self._batch_size]
            batch_embeddings = self._model.encode(batch).tolist()
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


class KnowledgeBaseCreationStage(PipelineStage):
    """Stage for creating or updating a knowledge base."""

    def __init__(self, vector_store: str = "chroma", **kwargs: Any) -> None:
        """Initialize knowledge base creation stage.

        Args:
            vector_store: Vector store backend to use
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="knowledge_base_creation",
            description="Create or update a knowledge base",
        )
        self._vector_store_type = vector_store
        self._vector_store: Any | None = None
        self._persistent = kwargs.get("persistent", True)
        self._store_path = kwargs.get("store_path", "./knowledge_bases")

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Create or update a knowledge base with chunks and embeddings.

        Args:
            input_data: Input data with chunks and embeddings
            context: Pipeline context

        Returns:
            Knowledge base information
        """
        try:
            name = input_data.get("name", "default_kb")
            description = input_data.get("description", "")
            chunks = input_data.get("chunks", [])
            embeddings = input_data.get("embeddings", [])

            if not chunks or not embeddings:
                raise ValueError(
                    "No chunks or embeddings provided for knowledge base creation"
                )

            if len(chunks) != len(embeddings):
                raise ValueError(
                    f"Number of chunks ({len(chunks)}) does not match number of embeddings ({len(embeddings)})"
                )

            # Initialize vector store if not already done
            if not self._vector_store:
                self._vector_store = self._initialize_vector_store(name)

            # Create unique IDs for chunks
            ids = [f"chunk_{i}" for i in range(len(chunks))]

            # Create metadata for each chunk
            metadatas = [{"source": f"document_{i // 10}"} for i in range(len(chunks))]

            # Add chunks to knowledge base
            self._add_to_knowledge_base(ids, chunks, embeddings, metadatas)

            # Create KB info
            kb_info = {
                "kb_id": name,
                "description": description,
                "vector_store": self._vector_store_type,
                "chunk_count": len(chunks),
                "persistent": self._persistent,
            }

            # Store metadata
            context.set_metadata("kb_id", name)
            context.set_metadata("vector_store", self._vector_store_type)
            context.set_metadata("chunk_count", len(chunks))

            return {
                "kb_info": kb_info,
                "success": True,
                "message": f"Knowledge base '{name}' created with {len(chunks)} chunks",
                "metadata": {
                    "kb_id": name,
                    "vector_store": self._vector_store_type,
                    "chunk_count": len(chunks),
                    "persistent": self._persistent,
                },
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "kb_info": {},
                "success": False,
                "message": f"Knowledge base creation failed: {e}",
                "metadata": {},
            }

    def _initialize_vector_store(self, name: str) -> Any:
        """Initialize a vector store.

        This is a placeholder implementation using ChromaDB.
        In a real implementation, this would be extended to support multiple vector stores.
        """
        # For demonstration purposes, use an in-memory Chroma client
        client = chromadb.Client()

        # Create or get collection
        try:
            collection = client.get_collection(name=name)
        except:
            collection = client.create_collection(name=name)

        return collection

    def _add_to_knowledge_base(
        self,
        ids: list[str],
        chunks: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add chunks and embeddings to knowledge base.

        This is a placeholder implementation using ChromaDB.
        """
        # Add items to collection
        if self._vector_store is None:
            # This should never happen as we initialize in process()
            # but we need to handle it for type checking
            return

        self._vector_store.add(
            ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas
        )


class RAGQueryStage(PipelineStage):
    """Stage for querying a knowledge base and generating a response."""

    def __init__(self, detail_level: str = "medium", **kwargs: Any) -> None:
        """Initialize RAG query stage.

        Args:
            detail_level: Level of detail in response
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="rag_query", description="Query knowledge base and generate response"
        )
        self._detail_level = detail_level
        self._num_docs = self._determine_doc_count(detail_level)
        self._vector_store: Any | None = None
        self._embedding_model: SentenceTransformer | None = None

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Query knowledge base and generate response.

        Args:
            input_data: Input data with query and knowledge base info
            context: Pipeline context

        Returns:
            Query results and generated response
        """
        try:
            query = input_data.get("query", "")
            kb_id = input_data.get("kb_id", "")
            kb_info = input_data.get("kb_info", {})
            num_docs = input_data.get("num_docs", self._num_docs)

            if not query:
                raise ValueError("No query provided for RAG")

            if not kb_id and not kb_info:
                raise ValueError("No knowledge base specified for RAG query")

            # Use kb_id from kb_info if not provided directly
            if not kb_id and kb_info:
                kb_id = kb_info.get("kb_id", "")

            if not kb_id:
                raise ValueError("No knowledge base ID found")

            # Initialize vector store and embedding model if not already done
            if not self._vector_store:
                self._vector_store = self._get_vector_store(kb_id)

            if not self._embedding_model:
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Generate query embedding
            query_embedding = self._embedding_model.encode(query).tolist()

            # Query the vector store
            results = self._query_knowledge_base(query_embedding, num_docs)

            # Generate response
            response = self._generate_response(query, results)

            # Store metadata
            context.set_metadata("kb_id", kb_id)
            context.set_metadata("query", query)
            context.set_metadata("num_docs", num_docs)
            context.set_metadata("detail_level", self._detail_level)

            return {
                "query": query,
                "results": results,
                "response": response,
                "success": True,
                "message": "RAG query executed successfully",
                "metadata": {
                    "kb_id": kb_id,
                    "num_docs": num_docs,
                    "detail_level": self._detail_level,
                },
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "query": input_data.get("query", ""),
                "results": [],
                "response": "",
                "success": False,
                "message": f"RAG query failed: {e}",
                "metadata": {},
            }

    def _determine_doc_count(self, detail_level: str) -> int:
        """Determine the number of documents to retrieve based on detail level."""
        if detail_level == "low":
            return 3
        elif detail_level == "high":
            return 10
        else:  # medium or default
            return 5

    def _get_vector_store(self, kb_id: str) -> Any:
        """Get a vector store for the specified knowledge base.

        This is a placeholder implementation using ChromaDB.
        """
        client = chromadb.Client()
        try:
            return client.get_collection(name=kb_id)
        except:
            # Return empty collection for demonstration purposes
            return client.create_collection(name=kb_id)

    def _query_knowledge_base(
        self, query_embedding: list[float], num_docs: int
    ) -> list[dict[str, Any]]:
        """Query the knowledge base with an embedding.

        This is a placeholder implementation using ChromaDB.
        """
        try:
            if self._vector_store is None:
                # This should never happen as we initialize in process()
                # but we need to handle it for type checking
                return []

            results = self._vector_store.query(
                query_embeddings=[query_embedding], n_results=num_docs
            )

            # Format results
            formatted_results = []
            for i in range(len(results.get("documents", [[]])[0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "id": results["ids"][0][i],
                    "metadata": results["metadatas"][0][i]
                    if "metadatas" in results
                    else {},
                    "score": results["distances"][0][i]
                    if "distances" in results
                    else 0.0,
                })

            return formatted_results
        except Exception:
            # Return empty results on error
            return []

    def _generate_response(self, query: str, results: list[dict[str, Any]]) -> str:
        """Generate a response based on retrieved documents.

        This is a placeholder implementation. In a real implementation, this would use an LLM.
        """
        if not results:
            return "No relevant information found."

        # Simple demonstration response
        response = f"Query: {query}\n\nBased on the retrieved information:\n\n"

        for i, result in enumerate(results, 1):
            content = result.get("content", "").strip()
            response += f"{i}. {content[:100]}...\n\n"

        response += (
            "In summary, the retrieved documents provide information about the query."
        )

        return response


class ConversationMemoryStage(PipelineStage):
    """Stage for managing conversation memory and context."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize conversation memory stage.

        Args:
            **kwargs: Additional configuration options
        """
        super().__init__(
            name="conversation_memory",
            description="Manage conversation memory and context",
        )
        self._memory: dict[str, list[dict[str, str]]] = {}  # Simple in-memory storage

    async def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> dict[str, Any]:
        """Process conversation with memory management.

        Args:
            input_data: Input data with prompt, history, and conversation ID
            context: Pipeline context

        Returns:
            Conversation results
        """
        try:
            prompt = input_data.get("prompt", "")
            history = input_data.get("history", [])
            conversation_id = input_data.get("conversation_id", "default")

            if not prompt:
                raise ValueError("No prompt provided for conversation")

            # Retrieve existing memory or create new
            memory = self._get_memory(conversation_id)

            # Merge provided history with stored memory
            combined_history = self._merge_history(memory, history)

            # Generate response based on prompt and history
            response = self._generate_response(prompt, combined_history)

            # Update memory with new interaction
            updated_history = self._update_memory(
                conversation_id, combined_history, prompt, response
            )

            # Store metadata
            context.set_metadata("conversation_id", conversation_id)
            context.set_metadata("history_length", len(updated_history))

            return {
                "prompt": prompt,
                "response": response,
                "conversation_id": conversation_id,
                "history": updated_history,
                "success": True,
                "message": "Conversation processed successfully",
                "metadata": {
                    "conversation_id": conversation_id,
                    "history_length": len(updated_history),
                },
            }
        except Exception as e:
            context.set_metadata("error", str(e))
            return {
                "prompt": input_data.get("prompt", ""),
                "response": "",
                "conversation_id": input_data.get("conversation_id", "default"),
                "history": input_data.get("history", []),
                "success": False,
                "message": f"Conversation processing failed: {e}",
                "metadata": {},
            }

    def _get_memory(self, conversation_id: str) -> list[dict[str, str]]:
        """Retrieve conversation memory for the specified ID."""
        return self._memory.get(conversation_id, [])

    def _merge_history(
        self, memory: list[dict[str, str]], history: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Merge stored memory with provided history.

        If history is provided, it takes precedence over stored memory.
        """
        if not history:
            return memory
        return history

    def _update_memory(
        self,
        conversation_id: str,
        history: list[dict[str, str]],
        prompt: str,
        response: str,
    ) -> list[dict[str, str]]:
        """Update conversation memory with new interaction."""
        # Add new messages to history
        updated_history = history.copy()
        updated_history.append({"role": "user", "content": prompt})
        updated_history.append({"role": "assistant", "content": response})

        # Limit history length (prevent memory growth)
        if len(updated_history) > 20:  # Arbitrary limit
            updated_history = updated_history[-20:]

        # Store updated history
        self._memory[conversation_id] = updated_history

        return updated_history

    def _generate_response(self, prompt: str, history: list[dict[str, str]]) -> str:
        """Generate a response based on prompt and conversation history.

        This is a placeholder implementation. In a real implementation, this would use an LLM.
        """
        # Format history for output
        history_text = ""
        for message in history:
            role = message.get("role", "")
            content = message.get("content", "")
            if role and content:
                history_text += f"{role.capitalize()}: {content}\n"

        # Simple demonstration response
        if "RAG" in prompt:
            return "RAG stands for Retrieval Augmented Generation. It's a technique that enhances LLM responses by retrieving relevant information from a knowledge base before generating a response."

        if history and "previous" in prompt.lower():
            return f"Based on our previous conversation, I can elaborate further on the topics we discussed. I see you mentioned {history[-1].get('content', '')[:30]}..."

        return f"This is a response to your prompt: {prompt}. In a real implementation, this would use an LLM that takes into account the conversation history."


class KnowledgeManagementWorkflow(WorkflowProvider):
    """Workflow for knowledge management and RAG."""

    def __init__(self, **config: Any) -> None:
        """Initialize workflow provider.

        Args:
            **config: Provider configuration
        """
        super().__init__(**config)

        # Set default configuration
        self.embedding_model = config.get("embedding_model", "text-embedding-ada-002")
        self.vector_store = config.get("vector_store", "chroma")
        self.chunk_size = config.get("chunk_size", 1000)
        self.auto_save_results = config.get("auto_save_results", True)
        self.detail_level = config.get("detail_level", "medium")
        self.response_format = config.get("response_format", "text")

        # Initialize pipeline stages
        self._document_chunker: DocumentChunkingStage | None = None
        self._embedding_generator: EmbeddingGenerationStage | None = None
        self._kb_creator: KnowledgeBaseCreationStage | None = None
        self._rag_query: RAGQueryStage | None = None
        self._conversation_memory: ConversationMemoryStage | None = None

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Store knowledge bases
        self._knowledge_bases: dict[str, dict[str, Any]] = {}

        # Track initialization state
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize workflow components."""
        if self._initialized:
            return

        self.logger.info("Initializing knowledge management workflow")

        # Create pipeline stages
        self._document_chunker = DocumentChunkingStage(chunk_size=self.chunk_size)

        self._embedding_generator = EmbeddingGenerationStage(
            embedding_model=self.embedding_model
        )

        self._kb_creator = KnowledgeBaseCreationStage(vector_store=self.vector_store)

        self._rag_query = RAGQueryStage(detail_level=self.detail_level)

        self._conversation_memory = ConversationMemoryStage()

        self._initialized = True
        self.logger.info("Knowledge management workflow initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.logger.info("Cleaning up knowledge management workflow resources")
        self._initialized = False
        self._knowledge_bases = {}

    async def create_workflow(self, workflow_config: dict[str, Any]) -> dict[str, Any]:
        """Create a workflow configuration.

        Args:
            workflow_config: Workflow configuration

        Returns:
            Workflow configuration object
        """
        # Combine default config with provided config
        config = {**self.config, **workflow_config}
        return config

    async def create_knowledge_base(
        self, name: str, documents: list[str], description: str = "", **options: Any
    ) -> str:
        """Create a knowledge base from documents.

        Args:
            name: Knowledge base name
            documents: List of documents to add
            description: Knowledge base description
            **options: Additional options

        Returns:
            Knowledge base ID
        """
        if not self._initialized:
            await self.initialize()

        # Create workflow config with options
        workflow = await self.create_workflow(options)

        # Process documents through chunking stage
        if self._document_chunker is None:
            raise ValueError("Document chunker not initialized")

        chunking_result = await self._document_chunker.process(
            {"documents": documents}, PipelineContext()
        )

        if not chunking_result.get("success", False):
            raise ValueError(
                f"Document chunking failed: {chunking_result.get('message')}"
            )

        # Process chunks through embedding stage
        if self._embedding_generator is None:
            raise ValueError("Embedding generator not initialized")

        embedding_result = await self._embedding_generator.process(
            chunking_result, PipelineContext()
        )

        if not embedding_result.get("success", False):
            raise ValueError(
                f"Embedding generation failed: {embedding_result.get('message')}"
            )

        # Create knowledge base
        if self._kb_creator is None:
            raise ValueError("Knowledge base creator not initialized")

        kb_result = await self._kb_creator.process(
            {
                "name": name,
                "description": description,
                "chunks": embedding_result.get("chunks", []),
                "embeddings": embedding_result.get("embeddings", []),
            },
            PipelineContext(),
        )

        if not kb_result.get("success", False):
            raise ValueError(
                f"Knowledge base creation failed: {kb_result.get('message')}"
            )

        # Store knowledge base info
        kb_info = kb_result.get("kb_info", {})
        kb_id = kb_info.get("kb_id", name)
        self._knowledge_bases[kb_id] = kb_info

        # Save results if configured
        if self.auto_save_results:
            self.logger.info(f"Auto-saving knowledge base: {kb_id}")

        return kb_id

    async def query_knowledge_base(
        self, kb_id: str, query: str, detail_level: str | None = None, **options: Any
    ) -> dict[str, Any]:
        """Query a knowledge base.

        Args:
            kb_id: Knowledge base ID
            query: Query string
            detail_level: Level of detail in response
            **options: Additional options

        Returns:
            Query results and generated response
        """
        if not self._initialized:
            await self.initialize()

        # Create workflow config with options
        workflow = await self.create_workflow(options)

        # Get knowledge base info
        kb_info = self._knowledge_bases.get(kb_id, {})

        # Use specified detail level or default
        detail_level = detail_level or self.detail_level

        # Determine number of documents to retrieve
        num_docs = options.get("num_docs", 5)
        if detail_level == "low":
            num_docs = options.get("num_docs", 3)
        elif detail_level == "high":
            num_docs = options.get("num_docs", 10)

        # Query the knowledge base
        if self._rag_query is None:
            raise ValueError("RAG query engine not initialized")

        query_result = await self._rag_query.process(
            {"query": query, "kb_id": kb_id, "kb_info": kb_info, "num_docs": num_docs},
            PipelineContext(),
        )

        # Save results if configured
        if self.auto_save_results:
            self.logger.info(f"Auto-saving query results for KB: {kb_id}")

        return query_result

    async def generate_rag_response(
        self, kb_id: str, prompt: str, num_docs: int = 5, **options: Any
    ) -> dict[str, Any]:
        """Generate a response using RAG.

        Args:
            kb_id: Knowledge base ID
            prompt: Prompt for generation
            num_docs: Number of documents to retrieve
            **options: Additional options

        Returns:
            Generated response
        """
        if not self._initialized:
            await self.initialize()

        # Just use query_knowledge_base with the specified parameters
        return await self.query_knowledge_base(
            kb_id=kb_id, query=prompt, num_docs=num_docs, **options
        )

    async def process_with_memory(
        self,
        prompt: str,
        conversation_id: str = "default",
        history: list[dict[str, str]] | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Process a conversation with memory.

        Args:
            prompt: Prompt for conversation
            conversation_id: Conversation ID
            history: Conversation history
            **options: Additional options

        Returns:
            Conversation results
        """
        if not self._initialized:
            await self.initialize()

        # Create workflow config with options
        workflow = await self.create_workflow(options)

        # Process conversation with memory
        if self._conversation_memory is None:
            raise ValueError("Conversation memory engine not initialized")

        memory_result = await self._conversation_memory.process(
            {
                "prompt": prompt,
                "conversation_id": conversation_id,
                "history": history or [],
            },
            PipelineContext(),
        )

        # Save results if configured
        if self.auto_save_results:
            self.logger.info(f"Auto-saving conversation for ID: {conversation_id}")

        return memory_result

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow with the given input.

        Args:
            input_data: Input data with the following structure:
                {
                    "task": str,             # Task type (create_kb, query_kb, rag, memory)
                    "input": Dict[str, Any], # Task-specific input
                    "options": Dict[str, Any] # Task options (optional)
                }

        Returns:
            Dictionary with task results
        """
        if not self._initialized:
            await self.initialize()

        task = input_data.get("task")
        task_input = input_data.get("input", {})
        options = input_data.get("options", {})

        if not task:
            raise ValueError("Input must contain 'task' field")

        if task == "create_kb":
            name = task_input.get("name", "")
            documents = task_input.get("documents", [])
            description = task_input.get("description", "")
            kb_id = await self.create_knowledge_base(
                name, documents, description, **options
            )
            return {
                "kb_id": kb_id,
                "success": True,
                "message": f"Knowledge base '{name}' created successfully",
                "kb_info": self._knowledge_bases.get(kb_id, {}),
            }

        elif task == "query_kb":
            kb_id = task_input.get("kb_id", "")
            query = task_input.get("query", "")
            detail_level = task_input.get("detail_level")
            return await self.query_knowledge_base(
                kb_id, query, detail_level, **options
            )

        elif task == "rag":
            kb_id = task_input.get("kb_id", "")
            prompt = task_input.get("prompt", "")
            num_docs = task_input.get("num_docs", 5)
            return await self.generate_rag_response(kb_id, prompt, num_docs, **options)

        elif task == "memory":
            prompt = task_input.get("prompt", "")
            conversation_id = task_input.get("conversation_id", "default")
            history = task_input.get("history", None)
            return await self.process_with_memory(
                prompt, conversation_id, history, **options
            )

        else:
            raise ValueError(f"Unknown task type: {task}")
