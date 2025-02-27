"""Implementations of different chunking strategies."""

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .base import Chunker
from .config import ChunkingConfig
from .types import Chunk, ChunkType, Document


class TextChunker(Chunker):
    """Chunks text based on tokens or characters."""

    def __init__(self, config: ChunkingConfig):
        super().__init__(name="text_chunker")
        self.config = config

    async def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk a document into smaller pieces."""
        return await self.chunk_text(document.content, document.metadata)

    async def chunk_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text into chunks based on configuration."""
        if self.config.chunking_strategy == "token":
            return await self._chunk_by_tokens(text, metadata or {})
        elif self.config.chunking_strategy == "sentence":
            return await self._chunk_by_sentences(text, metadata or {})
        elif self.config.chunking_strategy == "paragraph":
            return await self._chunk_by_paragraphs(text, metadata or {})
        else:
            raise ValueError(
                f"Unknown chunking strategy: {self.config.chunking_strategy}"
            )

    async def _chunk_by_tokens(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Split text into chunks based on token count."""
        # Simple approximation: split by whitespace
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        start_idx = 0

        for word in words:
            word_size = len(word.split())  # Simple token count approximation
            if current_size + word_size > self.config.chunk_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                end_idx = start_idx + len(chunk_text)
                chunks.append(
                    Chunk(
                        id=f"chunk_{chunk_id}",
                        content=chunk_text,
                        type=ChunkType.TEXT,
                        start_idx=start_idx,
                        end_idx=end_idx,
                        metadata=metadata.copy(),
                    )
                )
                # Start new chunk with overlap
                overlap_tokens = current_chunk[-self.config.chunk_overlap :]
                current_chunk = overlap_tokens + [word]
                current_size = len(overlap_tokens) + word_size
                start_idx = end_idx - len(" ".join(overlap_tokens))
                chunk_id += 1
            else:
                current_chunk.append(word)
                current_size += word_size

        # Handle remaining text
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                Chunk(
                    id=f"chunk_{chunk_id}",
                    content=chunk_text,
                    type=ChunkType.TEXT,
                    start_idx=start_idx,
                    end_idx=start_idx + len(chunk_text),
                    metadata=metadata.copy(),
                )
            )

        return chunks

    async def _chunk_by_sentences(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Split text into chunks based on sentence boundaries."""
        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        start_idx = 0

        for sentence in sentences:
            sentence_size = len(sentence.split())
            if current_size + sentence_size > self.config.chunk_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                end_idx = start_idx + len(chunk_text)
                chunks.append(
                    Chunk(
                        id=f"chunk_{chunk_id}",
                        content=chunk_text,
                        type=ChunkType.TEXT,
                        start_idx=start_idx,
                        end_idx=end_idx,
                        metadata=metadata.copy(),
                    )
                )
                # Start new chunk
                current_chunk = [sentence]
                current_size = sentence_size
                start_idx = text.find(sentence)
                chunk_id += 1
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Handle remaining text
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                Chunk(
                    id=f"chunk_{chunk_id}",
                    content=chunk_text,
                    type=ChunkType.TEXT,
                    start_idx=start_idx,
                    end_idx=start_idx + len(chunk_text),
                    metadata=metadata.copy(),
                )
            )

        return chunks

    async def _chunk_by_paragraphs(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Split text into chunks based on paragraph boundaries."""
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        start_idx = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph.split())
            if current_size + paragraph_size > self.config.chunk_size and current_chunk:
                # Create chunk
                chunk_text = "\n\n".join(current_chunk)
                end_idx = start_idx + len(chunk_text)
                chunks.append(
                    Chunk(
                        id=f"chunk_{chunk_id}",
                        content=chunk_text,
                        type=ChunkType.TEXT,
                        start_idx=start_idx,
                        end_idx=end_idx,
                        metadata=metadata.copy(),
                    )
                )
                # Start new chunk
                current_chunk = [paragraph]
                current_size = paragraph_size
                start_idx = text.find(paragraph)
                chunk_id += 1
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size

        # Handle remaining text
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(
                Chunk(
                    id=f"chunk_{chunk_id}",
                    content=chunk_text,
                    type=ChunkType.TEXT,
                    start_idx=start_idx,
                    end_idx=start_idx + len(chunk_text),
                    metadata=metadata.copy(),
                )
            )

        return chunks


class RecursiveChunker(Chunker):
    """Recursively chunks text based on multiple levels of structure."""

    def __init__(self, config: ChunkingConfig):
        super().__init__(name="recursive_chunker")
        self.config = config

    async def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk a document recursively."""
        return await self.chunk_text(document.content, document.metadata)

    async def chunk_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split text recursively into chunks."""
        # First split by largest structure (e.g., sections)
        sections = self._split_sections(text)
        chunks = []
        chunk_id = 0
        start_idx = 0

        for section in sections:
            # Then split by paragraphs
            paragraphs = re.split(r"\n\s*\n", section)
            current_chunk = []
            current_size = 0

            for paragraph in paragraphs:
                paragraph_size = len(paragraph.split())

                if (
                    current_size + paragraph_size > self.config.chunk_size
                    and current_chunk
                ):
                    # Create chunk from accumulated paragraphs
                    chunk_text = "\n\n".join(current_chunk)
                    end_idx = start_idx + len(chunk_text)
                    chunks.append(
                        Chunk(
                            id=f"chunk_{chunk_id}",
                            content=chunk_text,
                            type=ChunkType.TEXT,
                            start_idx=start_idx,
                            end_idx=end_idx,
                            metadata=metadata.copy() if metadata else {},
                        )
                    )
                    # Start new chunk
                    current_chunk = [paragraph]
                    current_size = paragraph_size
                    start_idx = text.find(paragraph)
                    chunk_id += 1
                else:
                    current_chunk.append(paragraph)
                    current_size += paragraph_size

            # Handle remaining paragraphs in section
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(
                    Chunk(
                        id=f"chunk_{chunk_id}",
                        content=chunk_text,
                        type=ChunkType.TEXT,
                        start_idx=start_idx,
                        end_idx=start_idx + len(chunk_text),
                        metadata=metadata.copy() if metadata else {},
                    )
                )
                chunk_id += 1

        return chunks

    def _split_sections(self, text: str) -> List[str]:
        """Split text into sections based on headers or other markers."""
        # Simple section splitting based on header patterns
        section_pattern = r"(?m)^#{1,6}\s+.+$"
        sections = re.split(section_pattern, text)
        return [s.strip() for s in sections if s.strip()]


class HTMLChunker(Chunker):
    """Chunks HTML content preserving structure."""

    def __init__(self, config: ChunkingConfig):
        super().__init__(name="html_chunker")
        self.config = config

    async def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk an HTML document."""
        return await self.chunk_text(document.content, document.metadata)

    async def chunk_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """Split HTML into semantic chunks."""
        soup = BeautifulSoup(text, "html.parser")
        chunks = []
        chunk_id = 0
        start_idx = 0

        # Process main content blocks
        for block in soup.find_all(["div", "article", "section", "main"]):
            block_text = block.get_text(separator=" ", strip=True)
            if not block_text:
                continue

            # Split block if it exceeds chunk size
            if len(block_text.split()) > self.config.chunk_size:
                # Create sub-chunks from block
                sub_chunks = await self._create_sub_chunks(
                    block_text, start_idx, chunk_id, metadata
                )
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
            else:
                # Use block as a chunk
                chunks.append(
                    Chunk(
                        id=f"chunk_{chunk_id}",
                        content=block_text,
                        type=ChunkType.TEXT,
                        start_idx=start_idx,
                        end_idx=start_idx + len(block_text),
                        metadata={
                            **(metadata or {}),
                            "html_tag": block.name,
                            "classes": " ".join(block.get("class", [])),
                        },
                    )
                )
                chunk_id += 1

            start_idx += len(block_text) + 1

        return chunks

    async def _create_sub_chunks(
        self,
        text: str,
        start_idx: int,
        chunk_id: int,
        metadata: Optional[Dict[str, Any]],
    ) -> List[Chunk]:
        """Create sub-chunks from a large block of text."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        local_start_idx = start_idx

        for word in words:
            word_size = len(word.split())
            if current_size + word_size > self.config.chunk_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                end_idx = local_start_idx + len(chunk_text)
                chunks.append(
                    Chunk(
                        id=f"chunk_{chunk_id}",
                        content=chunk_text,
                        type=ChunkType.TEXT,
                        start_idx=local_start_idx,
                        end_idx=end_idx,
                        metadata=metadata.copy() if metadata else {},
                    )
                )
                # Start new chunk with overlap
                overlap_tokens = current_chunk[-self.config.chunk_overlap :]
                current_chunk = overlap_tokens + [word]
                current_size = len(overlap_tokens) + word_size
                local_start_idx = end_idx - len(" ".join(overlap_tokens))
                chunk_id += 1
            else:
                current_chunk.append(word)
                current_size += word_size

        # Handle remaining text
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                Chunk(
                    id=f"chunk_{chunk_id}",
                    content=chunk_text,
                    type=ChunkType.TEXT,
                    start_idx=local_start_idx,
                    end_idx=local_start_idx + len(chunk_text),
                    metadata=metadata.copy() if metadata else {},
                )
            )

        return chunks
