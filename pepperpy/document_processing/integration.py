"""RAG integration for document processing.

This module provides integration between document processing and
RAG (Retrieval Augmented Generation) capabilities within PepperPy.
"""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, Union

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)


class DocumentRAGError(PepperpyError):
    """Error raised during document RAG operations."""

    pass


class DocumentRAGProcessor:
    """Processor for integrating document processing with RAG.

    This class provides functionality for processing documents and loading
    them into a RAG system with minimal configuration.
    """

    def __init__(
        self,
        rag_module: Optional[Any] = None,
        document_processor: Optional[Any] = None,
        storage_provider: Optional[str] = None,
        embedding_provider: Optional[str] = None,
        vectorstore_provider: Optional[str] = None,
        chunking_config: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize document RAG processor.

        Args:
            rag_module: RAG module from PepperPy (if None, will be imported)
            document_processor: Document processor instance
            storage_provider: RAG storage provider name
            embedding_provider: RAG embedding provider name
            vectorstore_provider: RAG vector store provider name
            chunking_config: Configuration for text chunking
            include_metadata: Whether to include document metadata in chunks
            **kwargs: Additional configuration options
        """
        # Import RAG module if not provided
        if rag_module is None:
            try:
                from pepperpy import rag

                self.rag = rag
            except ImportError:
                raise DocumentRAGError(
                    "Cannot import RAG module from PepperPy. "
                    "Please install PepperPy with RAG support."
                )
        else:
            self.rag = rag_module

        # Import document processor if not provided
        if document_processor is None:
            try:
                from pepperpy.document_processing import get_processor

                self.document_processor = get_processor()
            except ImportError:
                raise DocumentRAGError(
                    "Cannot import document processor. "
                    "Please initialize document processor first."
                )
        else:
            self.document_processor = document_processor

        # Set configuration
        self.storage_provider = storage_provider or os.environ.get(
            "PEPPERPY_RAG__STORAGE_PROVIDER", "memory"
        )
        self.embedding_provider = embedding_provider or os.environ.get(
            "PEPPERPY_RAG__EMBEDDING_PROVIDER", "default"
        )
        self.vectorstore_provider = vectorstore_provider or os.environ.get(
            "PEPPERPY_RAG__VECTORSTORE_PROVIDER", "chroma"
        )

        # Set chunking configuration
        self.chunking_config = {
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "separator": "\n",
        }
        if chunking_config:
            self.chunking_config.update(chunking_config)

        self.include_metadata = include_metadata
        self.config = kwargs

        # Initialize RAG components
        self._initialize_rag()

    def _initialize_rag(self) -> None:
        """Initialize RAG components."""
        try:
            # Initialize RAG storage
            self.storage = self.rag.get_storage(provider=self.storage_provider)

            # Initialize RAG embedding provider
            self.embeddings = self.rag.get_embeddings(provider=self.embedding_provider)

            # Initialize RAG vector store
            self.vectorstore = self.rag.get_vectorstore(
                provider=self.vectorstore_provider,
                embedding_provider=self.embedding_provider,
            )

            # Initialize chunker
            self.chunker = self.rag.get_chunker(
                chunk_size=self.chunking_config.get("chunk_size", 1000),
                chunk_overlap=self.chunking_config.get("chunk_overlap", 200),
                separator=self.chunking_config.get("separator", "\n"),
            )

            # Initialize retriever
            self.retriever = self.rag.get_retriever(
                vectorstore=self.vectorstore,
            )
        except Exception as e:
            raise DocumentRAGError(f"Error initializing RAG components: {e}")

    def process_document(
        self,
        document_path: Union[str, Path],
        collection_name: Optional[str] = None,
        document_id: Optional[str] = None,
        extract_metadata: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process a document and index it for RAG.

        Args:
            document_path: Path to document
            collection_name: Name of RAG collection/namespace
            document_id: Unique ID for the document
            extract_metadata: Whether to extract metadata from document
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            DocumentRAGError: If processing fails
        """
        if isinstance(document_path, str):
            document_path = Path(document_path)

        if not document_path.exists():
            raise DocumentRAGError(f"Document not found: {document_path}")

        try:
            # Set document ID if not provided
            if document_id is None:
                document_id = str(document_path.stem)

            # Set collection name if not provided
            if collection_name is None:
                collection_name = "documents"

            # Process document to extract text and metadata
            processor_result = self.document_processor.process_document(
                document_path=document_path,
                extract_metadata=extract_metadata,
                **kwargs,
            )

            # Check if text was extracted
            if not processor_result.get("text"):
                raise DocumentRAGError(
                    f"No text extracted from document: {document_path}"
                )

            # Chunk text
            chunks = self.chunker.create_chunks(processor_result["text"])

            # Prepare documents for indexing
            rag_documents = []
            for i, chunk in enumerate(chunks):
                # Create document metadata
                metadata = {
                    "source": str(document_path),
                    "document_id": document_id,
                    "chunk_index": i,
                }

                # Add document metadata if available and requested
                if self.include_metadata and "metadata" in processor_result:
                    for key, value in processor_result["metadata"].items():
                        # Skip non-serializable values
                        if isinstance(value, (str, int, float, bool, list, dict)):
                            metadata[f"doc_{key}"] = value

                # Create RAG document
                rag_document = self.rag.Document(
                    page_content=chunk,
                    metadata=metadata,
                )
                rag_documents.append(rag_document)

            # Index documents
            self.vectorstore.add_documents(
                documents=rag_documents,
                collection_name=collection_name,
            )

            # Return results
            return {
                "document_id": document_id,
                "collection_name": collection_name,
                "num_chunks": len(chunks),
                "document": processor_result,
            }
        except Exception as e:
            raise DocumentRAGError(f"Error processing document for RAG: {e}")

    def process_directory(
        self,
        directory_path: Union[str, Path],
        collection_name: Optional[str] = None,
        recursive: bool = True,
        file_extensions: Optional[Set[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Process all documents in a directory and index them for RAG.

        Args:
            directory_path: Path to directory
            collection_name: Name of RAG collection/namespace
            recursive: Whether to process subdirectories
            file_extensions: Set of file extensions to process
            progress_callback: Callback for reporting progress
            **kwargs: Additional processing options

        Returns:
            Dictionary with processing results

        Raises:
            DocumentRAGError: If processing fails
        """
        if isinstance(directory_path, str):
            directory_path = Path(directory_path)

        if not directory_path.exists() or not directory_path.is_dir():
            raise DocumentRAGError(f"Directory not found: {directory_path}")

        try:
            # Set collection name if not provided
            if collection_name is None:
                collection_name = directory_path.name

            # Collect files to process
            files_to_process = []
            if recursive:
                # Use rglob to find files recursively
                all_files = list(directory_path.rglob("*"))
            else:
                # Use glob to find files in current directory only
                all_files = list(directory_path.glob("*"))

            # Filter by file extension if provided
            for file_path in all_files:
                if file_path.is_file():
                    if (
                        file_extensions is None
                        or file_path.suffix.lower() in file_extensions
                    ):
                        files_to_process.append(file_path)

            # Check if any files found
            if not files_to_process:
                return {
                    "collection_name": collection_name,
                    "num_documents": 0,
                    "num_chunks": 0,
                    "processed_documents": [],
                }

            # Process each file
            processed_documents = []
            total_chunks = 0

            for i, file_path in enumerate(files_to_process):
                # Report progress
                if progress_callback:
                    progress_callback(i, len(files_to_process), str(file_path))

                try:
                    # Process document
                    document_id = str(file_path.relative_to(directory_path))
                    result = self.process_document(
                        document_path=file_path,
                        collection_name=collection_name,
                        document_id=document_id,
                        **kwargs,
                    )
                    processed_documents.append(result)
                    total_chunks += result.get("num_chunks", 0)
                except Exception as e:
                    logger.warning(f"Error processing document {file_path}: {e}")

            # Return results
            return {
                "collection_name": collection_name,
                "num_documents": len(processed_documents),
                "num_chunks": total_chunks,
                "processed_documents": processed_documents,
            }
        except Exception as e:
            raise DocumentRAGError(f"Error processing directory for RAG: {e}")

    def query(
        self,
        query_text: str,
        collection_name: Optional[str] = None,
        num_results: int = 3,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Query the indexed documents.

        Args:
            query_text: Query text
            collection_name: Name of RAG collection/namespace
            num_results: Number of results to return
            **kwargs: Additional query options

        Returns:
            Dictionary with query results

        Raises:
            DocumentRAGError: If query fails
        """
        try:
            # Set default collection name if not provided
            if collection_name is not None:
                # Update retriever to use specific collection
                self.retriever.search_kwargs = {
                    "k": num_results,
                    "filter": {"collection_name": collection_name},
                }
            else:
                # Use default retriever settings
                self.retriever.search_kwargs = {"k": num_results}

            # Execute query
            results = self.retriever.get_relevant_documents(query_text)

            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append({
                    "content": result.page_content,
                    "metadata": result.metadata,
                    "relevance_score": getattr(result, "score", None),
                    "document_id": result.metadata.get("document_id"),
                    "source": result.metadata.get("source"),
                })

            # Return results
            return {
                "query": query_text,
                "collection_name": collection_name,
                "num_results": len(formatted_results),
                "results": formatted_results,
            }
        except Exception as e:
            raise DocumentRAGError(f"Error querying documents: {e}")

    def get_document_by_id(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID.

        Args:
            document_id: Document ID
            collection_name: Name of RAG collection/namespace
            **kwargs: Additional query options

        Returns:
            Document data or None if not found

        Raises:
            DocumentRAGError: If query fails
        """
        try:
            # Set filter based on collection name
            filter_dict = {"document_id": document_id}
            if collection_name is not None:
                filter_dict["collection_name"] = collection_name

            # Query vectorstore
            results = self.vectorstore.similarity_search(
                query="",  # Empty query returns based on filter
                k=100,  # Get many chunks to ensure we get all from document
                filter=filter_dict,
            )

            if not results:
                return None

            # Extract document information
            source = results[0].metadata.get("source")
            chunks = [result.page_content for result in results]

            # Sort chunks by index if available
            sorted_chunks = sorted(
                results, key=lambda x: x.metadata.get("chunk_index", 0)
            )

            # Reconstruct document text
            text = "\n".join([chunk.page_content for chunk in sorted_chunks])

            # Get metadata from first chunk
            metadata = {}
            for key, value in results[0].metadata.items():
                if key.startswith("doc_"):
                    metadata[key[4:]] = value

            # Return document data
            return {
                "document_id": document_id,
                "collection_name": collection_name,
                "source": source,
                "text": text,
                "metadata": metadata,
                "num_chunks": len(results),
            }
        except Exception as e:
            raise DocumentRAGError(f"Error getting document by ID: {e}")

    def delete_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> bool:
        """Delete a document from the index.

        Args:
            document_id: Document ID
            collection_name: Name of RAG collection/namespace
            **kwargs: Additional options

        Returns:
            True if document was deleted, False otherwise

        Raises:
            DocumentRAGError: If deletion fails
        """
        try:
            # Set filter based on collection name
            filter_dict = {"document_id": document_id}
            if collection_name is not None:
                filter_dict["collection_name"] = collection_name

            # Delete from vectorstore
            result = self.vectorstore.delete(filter=filter_dict)

            return result
        except Exception as e:
            raise DocumentRAGError(f"Error deleting document: {e}")


# Global document RAG processor instance
_document_rag_processor: Optional[DocumentRAGProcessor] = None


def get_document_rag_processor(
    rag_module: Optional[Any] = None,
    document_processor: Optional[Any] = None,
    storage_provider: Optional[str] = None,
    embedding_provider: Optional[str] = None,
    vectorstore_provider: Optional[str] = None,
    chunking_config: Optional[Dict[str, Any]] = None,
    include_metadata: bool = True,
    **kwargs: Any,
) -> DocumentRAGProcessor:
    """Get document RAG processor instance.

    Args:
        rag_module: RAG module from PepperPy
        document_processor: Document processor instance
        storage_provider: RAG storage provider name
        embedding_provider: RAG embedding provider name
        vectorstore_provider: RAG vector store provider name
        chunking_config: Configuration for text chunking
        include_metadata: Whether to include document metadata in chunks
        **kwargs: Additional configuration options

    Returns:
        Document RAG processor instance
    """
    global _document_rag_processor

    if _document_rag_processor is None:
        _document_rag_processor = DocumentRAGProcessor(
            rag_module=rag_module,
            document_processor=document_processor,
            storage_provider=storage_provider,
            embedding_provider=embedding_provider,
            vectorstore_provider=vectorstore_provider,
            chunking_config=chunking_config,
            include_metadata=include_metadata,
            **kwargs,
        )

    return _document_rag_processor
