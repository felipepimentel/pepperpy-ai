"""Document loader tool implementation."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
import markdown
from bs4 import BeautifulSoup
from pydantic import BaseModel

from ....interfaces import Tool
from ...base import BaseTool, ToolConfig
from ...errors import ToolError

logger = logging.getLogger(__name__)


class Document(BaseModel):
    """Document with metadata and content."""

    path: str
    content: str
    metadata: Dict[str, Any]


class DocumentLoaderTool(BaseTool):
    """Tool for loading and parsing various document types."""

    def __init__(self) -> None:
        """Initialize document loader tool."""
        super().__init__(
            config=ToolConfig(
                name="document_loader",
                description="Tool for loading and parsing various document types",
                parameters={
                    "supported_types": ["text", "markdown"],
                },
                metadata={
                    "version": "1.0.0",
                },
            ),
        )
        self._parsers = {
            "text": self._load_text,
            "markdown": self._load_markdown,
        }

    async def _setup(self) -> None:
        """Set up document loader tool."""
        # No setup needed
        pass

    async def _teardown(self) -> None:
        """Clean up document loader tool."""
        # No cleanup needed
        pass

    async def _execute_impl(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Load and parse document.
        
        Args:
            input_data: Document path or dictionary with path and type
            context: Optional execution context
            
        Returns:
            Loaded document
            
        Raises:
            ToolError: If document cannot be loaded
        """
        try:
            if isinstance(input_data, str):
                path = input_data
                doc_type = self._detect_type(path)
            elif isinstance(input_data, dict):
                path = input_data["path"]
                doc_type = input_data.get("type", self._detect_type(path))
            else:
                raise ToolError("Invalid input data")
            
            if doc_type not in self._parsers:
                raise ToolError(f"Unsupported document type: {doc_type}")
                
            return await self._parsers[doc_type](path)
            
        except Exception as e:
            logger.error(f"Failed to load document: {str(e)}")
            raise ToolError(f"Document loading failed: {str(e)}")
    
    def _detect_type(self, path: str) -> str:
        """Detect document type from file extension.
        
        Args:
            path: Document path
            
        Returns:
            Document type
            
        Raises:
            ToolError: If document type cannot be detected
        """
        ext = os.path.splitext(path)[1].lower()
        
        if ext in [".txt"]:
            return "text"
        elif ext in [".md", ".markdown"]:
            return "markdown"
        else:
            raise ToolError(f"Unsupported file extension: {ext}")
    
    async def _load_text(self, path: str) -> Document:
        """Load text document.
        
        Args:
            path: Document path
            
        Returns:
            Loaded document
            
        Raises:
            ToolError: If document cannot be loaded
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                
            return Document(
                path=path,
                content=content,
                metadata={
                    "type": "text",
                    "size": os.path.getsize(path),
                    "modified": os.path.getmtime(path),
                },
            )
        except Exception as e:
            raise ToolError(f"Failed to load text document: {str(e)}")
    
    async def _load_markdown(self, path: str) -> Document:
        """Load markdown document.
        
        Args:
            path: Document path
            
        Returns:
            Loaded document
            
        Raises:
            ToolError: If document cannot be loaded
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                md = f.read()
                
            # Convert to HTML and extract text
            html = markdown.markdown(md)
            soup = BeautifulSoup(html, "html.parser")
            content = soup.get_text()
                
            return Document(
                path=path,
                content=content,
                metadata={
                    "type": "markdown",
                    "size": os.path.getsize(path),
                    "modified": os.path.getmtime(path),
                },
            )
        except Exception as e:
            raise ToolError(f"Failed to load markdown document: {str(e)}")

    def load_text(self, path: str) -> Document:
        """Load text file.
        
        Args:
            path: Path to text file
            
        Returns:
            Document with content and metadata
            
        Raises:
            Exception: If file cannot be loaded
        """
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return Document(
            path=path,
            content=content,
            metadata={
                "type": "text",
                "size": os.path.getsize(path),
                "modified": os.path.getmtime(path),
            }
        )

    def load_markdown(self, path: str) -> Document:
        """Load markdown file.
        
        Args:
            path: Path to markdown file
            
        Returns:
            Document with content and metadata
            
        Raises:
            Exception: If file cannot be loaded
        """
        with open(path, "r", encoding="utf-8") as f:
            md = f.read()
            
        # Convert to HTML and extract text
        html = markdown.markdown(md)
        soup = BeautifulSoup(html, "html.parser")
        content = soup.get_text()
            
        return Document(
            path=path,
            content=content,
            metadata={
                "type": "markdown",
                "size": os.path.getsize(path),
                "modified": os.path.getmtime(path),
            }
        )

    def load_pdf(self, path: str) -> Document:
        """Load PDF file.
        
        Args:
            path: Path to PDF file
            
        Returns:
            Document with content and metadata
            
        Raises:
            Exception: If file cannot be loaded
        """
        doc = fitz.open(path)
        content = []
        
        for page in doc:
            content.append(page.get_text())
            
        return Document(
            path=path,
            content="\n".join(content),
            metadata={
                "type": "pdf",
                "size": os.path.getsize(path),
                "modified": os.path.getmtime(path),
                "pages": len(doc),
            }
        )

    def load_document(self, path: str) -> Document:
        """Load document based on file extension.
        
        Args:
            path: Path to document
            
        Returns:
            Document with content and metadata
            
        Raises:
            Exception: If file type is not supported or file cannot be loaded
        """
        ext = Path(path).suffix.lower()
        
        if ext in {".txt", ".py", ".js", ".html", ".css", ".json", ".yaml", ".yml"}:
            return self.load_text(path)
        elif ext in {".md", ".markdown"}:
            return self.load_markdown(path)
        elif ext == ".pdf":
            return self.load_pdf(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    async def execute(self, **kwargs: Any) -> ToolResult[Document]:
        """Execute document loading.
        
        Args:
            path: Path to document
            
        Returns:
            Loaded document
        """
        path = str(kwargs.get("path", ""))
        if not path:
            return ToolResult(
                success=False,
                error="Path is required"
            )
            
        try:
            document = self.load_document(path)
            return ToolResult(success=True, data=document)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass 