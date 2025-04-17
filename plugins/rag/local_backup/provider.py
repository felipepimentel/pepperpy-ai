"""Local RAG provider implementation for PepperPy.

This module provides a local Retrieval-Augmented Generation (RAG) provider
that stores and retrieves documents from the local filesystem using embeddings.
"""

import asyncio
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, List, Optional, Set, Union

from langchain.docstore.document import Document as LCDocument
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_community.vectorstores import Chroma

from pepperpy.plugin import ProviderPlugin
from pepperpy.rag import Document, Query, RAGProvider, SearchResult

# File extension to loader mapping
FILE_LOADERS = {
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
}


class LocalRAGProvider(RAGProvider, ProviderPlugin):
    """Local RAG provider using LangChain and ChromaDB.

    This provider stores documents and their embeddings locally using ChromaDB
    and performs retrieval using the specified embedding model.
    """

    # Type-annotated config attributes that match plugin.yaml schema
    storage_path: str = "./data/rag"
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    similarity_top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    cache_results: bool = True
    file_extensions: List[str] = ["txt", "md", "pdf", "docx", "html"]

    def __init__(self) -> None:
        """Initialize the provider."""
        super().__init__()
        self.embeddings = None
        self.vector_db = None
        self.text_splitter = None
        self._loaded_docs: Set[str] = set()

    async def initialize(self) -> None:
        """Initialize the RAG system.

        This is called automatically when the provider is first used.
        """
        if self.initialized:
            return

        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)

        # Run initialization in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._init_components)

        self.initialized = True
        self.logger.debug(f"Initialized with storage_path={self.storage_path}")

    def _init_components(self) -> None:
        """Initialize components in a separate thread."""
        try:
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                cache_folder=os.path.join(self.storage_path, "embeddings_cache"),
            )

            # Initialize vector store
            self.vector_db = Chroma(
                persist_directory=os.path.join(self.storage_path, "chroma_db"),
                embedding_function=self.embeddings,
            )

            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize RAG components: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources.

        This is called automatically when the context manager exits.
        """
        # Persist vector store if needed
        if self.vector_db and hasattr(self.vector_db, "persist"):
            await asyncio.to_thread(self.vector_db.persist)

        self.vector_db = None
        self.embeddings = None
        self.text_splitter = None

        self.initialized = False
        self.logger.debug("Resources cleaned up")

    def _pepperpy_to_langchain_doc(self, doc: Document) -> LCDocument:
        """Convert PepperPy document to LangChain document.

        Args:
            doc: PepperPy document

        Returns:
            LangChain document
        """
        metadata = doc.metadata.copy() if doc.metadata else {}
        # Generate a unique ID if not present
        doc_id = getattr(doc, "id", None)
        if doc_id:
            metadata["id"] = doc_id

        return LCDocument(
            page_content=doc.text,
            metadata=metadata,
        )

    def _langchain_to_search_result(
        self, doc: LCDocument, score: float = 0.0
    ) -> SearchResult:
        """Convert LangChain document to SearchResult.

        Args:
            doc: LangChain document
            score: Relevance score

        Returns:
            SearchResult
        """
        metadata = doc.metadata.copy() if hasattr(doc, "metadata") else {}
        doc_id = metadata.pop("id", None) or metadata.get("source", "unknown")

        return SearchResult(
            id=str(doc_id), text=doc.page_content, metadata=metadata, score=score
        )

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in the RAG system.

        Args:
            docs: Document or list of documents to add
        """
        if not self.initialized:
            await self.initialize()

        if not isinstance(docs, list):
            docs = [docs]

        # Convert to LangChain documents
        langchain_docs = [self._pepperpy_to_langchain_doc(doc) for doc in docs]

        # Split documents into chunks if text splitter is available
        if self.text_splitter and self.vector_db:
            split_docs = await asyncio.to_thread(
                self.text_splitter.split_documents, langchain_docs
            )

            # Add to vector store
            if split_docs:
                await asyncio.to_thread(self.vector_db.add_documents, split_docs)

                # Track document IDs for later retrieval
                for doc in docs:
                    doc_id = getattr(doc, "id", None)
                    if doc_id:
                        self._loaded_docs.add(doc_id)

                self.logger.debug(
                    f"Added {len(docs)} documents ({len(split_docs)} chunks)"
                )

    async def search(
        self, query: Union[str, Query], limit: int = 5, **kwargs: Any
    ) -> Sequence[SearchResult]:
        """Search for documents matching the query.

        Args:
            query: Query string or Query object
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        if not self.initialized:
            await self.initialize()

        # Extract query string
        if isinstance(query, Query):
            query_text = query.text
            kwargs.update(query.metadata or {})
        else:
            query_text = query

        # Use configured limit if not specified
        limit = limit or self.similarity_top_k

        # Perform search
        try:
            if not self.vector_db:
                self.logger.error("Vector DB not initialized")
                return []

            # Make sure vector_db is properly initialized
            if not hasattr(self.vector_db, "similarity_search_with_score"):
                self.logger.error("Vector DB does not support similarity search")
                return []

            results = await asyncio.to_thread(
                self.vector_db.similarity_search_with_score,
                query_text,
                k=limit,
            )

            # Convert to search results
            search_results = []
            for doc, score in results:
                # Calculate relevance between 0-1 (ChromaDB returns distance)
                # Convert to similarity score (assuming distance is between 0-2)
                relevance = max(0, min(1, 1 - score / 2))

                search_results.append(self._langchain_to_search_result(doc, relevance))

            return search_results

        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []

    async def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document if found, None otherwise
        """
        if not self.initialized:
            await self.initialize()

        # Check if document is loaded
        if doc_id not in self._loaded_docs:
            return None

        try:
            if not self.vector_db:
                self.logger.error("Vector DB not initialized")
                return None

            # Make sure vector_db is properly initialized
            if not hasattr(self.vector_db, "similarity_search_with_score"):
                self.logger.error("Vector DB does not support similarity search")
                return None

            # Search by ID
            results = await asyncio.to_thread(
                self.vector_db.similarity_search_with_score,
                "",  # Empty query
                k=100,  # Get a lot of documents to search through
                filter={"id": doc_id},  # Filter by ID
            )

            # Find matching document
            for doc, _ in results:
                if doc.metadata.get("id") == doc_id:
                    # Convert to Document
                    search_result = self._langchain_to_search_result(doc)
                    return search_result.to_document()

            return None

        except Exception as e:
            self.logger.error(f"Error getting document {doc_id}: {e}")
            return None

    # Additional utility method for loading files (not part of the base interface)
    async def add_from_files(self, file_paths: Union[str, List[str]]) -> List[Document]:
        """Add documents from files.

        Args:
            file_paths: Path or list of paths to files

        Returns:
            List of added documents
        """
        if not self.initialized:
            await self.initialize()

        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        documents = []

        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"File not found: {file_path}")
                continue

            suffix = path.suffix.lower()

            # Check if file extension is supported
            if suffix not in FILE_LOADERS:
                self.logger.warning(f"Unsupported file type: {suffix}")
                continue

            try:
                # Load document
                loader_cls = FILE_LOADERS[suffix]
                loader = loader_cls(file_path)
                docs = await asyncio.to_thread(loader.load)

                # Convert to PepperPy documents
                for i, doc in enumerate(docs):
                    # Add file info to metadata
                    if not hasattr(doc, "metadata") or doc.metadata is None:
                        doc.metadata = {}

                    doc.metadata["source"] = file_path
                    doc.metadata["file_name"] = path.name
                    doc.metadata["file_type"] = suffix[1:]  # Remove leading dot

                    # Create unique ID
                    doc_id = f"{path.stem}_{i}"
                    doc.metadata["id"] = doc_id

                    # Create SearchResult first
                    search_result = self._langchain_to_search_result(doc)
                    # Then convert to Document
                    document = search_result.to_document()
                    documents.append(document)

            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")

        # Store documents in the vector database
        if documents:
            await self.store(documents)

        return documents
