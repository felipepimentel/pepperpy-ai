"""Tool for loading and parsing various document types."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
import markdown
from bs4 import BeautifulSoup
from pydantic import BaseModel

from pepperpy.tools.tool import Tool, ToolResult


class Document(BaseModel):
    """Document with metadata and content."""

    path: str
    content: str
    metadata: Dict[str, Any]


class DocumentLoaderTool(Tool):
    """Tool for loading and parsing various document types."""

    def __init__(self) -> None:
        """Initialize document loader tool."""
        pass

    async def initialize(self) -> None:
        """Initialize tool."""
        pass

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