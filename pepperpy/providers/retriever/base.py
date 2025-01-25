"""Base retriever provider module."""

import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from ..base import BaseProvider


logger = logging.getLogger(__name__)


class BaseRetrieverProvider(BaseProvider):
    """Base class for retriever providers.
    
    This class defines the interface for retriever providers, which are responsible
    for retrieving relevant documents from a vector store based on a query.
    """
    
    def __init__(
        self,
        config: Dict[str, Any]
    ) -> None:
        """Initialize retriever provider.
        
        Args:
            config: Provider configuration dictionary.
        """
        super().__init__(config=config)
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> Sequence[Dict[str, Any]]:
        """Retrieve relevant documents based on a query.
        
        Args:
            query: The query to retrieve documents for.
            limit: Optional limit on the number of documents to retrieve.
            
        Returns:
            A sequence of dictionaries containing the retrieved documents and their metadata.
        """
        pass
    
    @abstractmethod
    async def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a document to the retriever's storage.
        
        Args:
            text: The text content of the document.
            metadata: Optional metadata associated with the document.
        """
        pass 