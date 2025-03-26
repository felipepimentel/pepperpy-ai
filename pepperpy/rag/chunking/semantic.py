"""Semantic text chunking using language models."""

import re
from typing import Any, Dict, List, Optional, cast

import spacy
from spacy.language import Language
from spacy.tokens import Doc

from pepperpy.rag.chunking.base import (
    Chunk,
    ChunkingError,
    ChunkingOptions,
    TextChunker,
)


class SemanticChunker(TextChunker):
    """Chunker that uses language models to identify semantic boundaries.

    This chunker uses SpaCy's language models to:
    1. Identify sentence boundaries
    2. Parse dependency trees
    3. Extract semantic units (e.g. paragraphs, sections)
    4. Maintain semantic coherence in chunks
    """

    def __init__(
        self,
        model: str = "en_core_web_sm",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize semantic chunker.

        Args:
            model: SpaCy model to use
            config: Optional configuration
            **kwargs: Additional configuration options
        """
        super().__init__(name="semantic", config=config, **kwargs)
        self._model_name = model
        self._nlp: Optional[Language] = None

    async def _initialize(self) -> None:
        """Initialize the language model."""
        try:
            nlp = spacy.load(self._model_name)
            # Add sentence segmentation pipeline if not present
            if "senter" not in nlp.pipe_names:
                nlp.add_pipe("senter")
            self._nlp = nlp
        except Exception as e:
            raise ChunkingError(f"Failed to load SpaCy model: {e}")

    async def _cleanup(self) -> None:
        """Clean up resources."""
        self._nlp = None

    def _get_semantic_boundaries(self, doc: Doc) -> List[int]:
        """Get semantic boundary positions in text.

        This method identifies natural break points in the text by looking at:
        1. Sentence boundaries
        2. Paragraph breaks
        3. Section headings
        4. Topic changes

        Args:
            doc: SpaCy Doc object

        Returns:
            List of boundary positions
        """
        boundaries = []

        # Add sentence boundaries
        for sent in doc.sents:
            boundaries.append(sent.end_char)

        # Add paragraph breaks (double newlines)
        for match in re.finditer(r"\n\s*\n", doc.text):
            boundaries.append(match.end())

        # Add section headings (basic heuristic)
        for match in re.finditer(r"^[A-Z][^.!?]*[:]\s*$", doc.text, re.MULTILINE):
            boundaries.append(match.end())

        return sorted(list(set(boundaries)))

    async def chunk_text(
        self, text: str, options: Optional[ChunkingOptions] = None
    ) -> List[Chunk]:
        """Split text into semantically coherent chunks.

        Args:
            text: Text to split
            options: Optional chunking options

        Returns:
            List of chunks

        Raises:
            ChunkingError: If chunking fails
        """
        if not self._nlp:
            await self.initialize()

        nlp = cast(Language, self._nlp)
        options = options or ChunkingOptions()

        try:
            # Process text with SpaCy
            doc = nlp(text)

            # Get semantic boundaries
            boundaries = self._get_semantic_boundaries(doc)

            # Create chunks based on boundaries and size constraints
            chunks = []
            start = 0
            current_chunk = ""

            for boundary in boundaries:
                # Add text up to boundary
                current_chunk += text[start:boundary].strip()

                # Check if chunk is within size constraints
                if (
                    len(current_chunk) >= options.min_chunk_size
                    and len(current_chunk) <= options.max_chunk_size
                ):
                    # Create chunk
                    chunks.append(
                        Chunk(
                            text=current_chunk,
                            start=start,
                            end=boundary,
                            metadata={"type": "semantic", "model": self._model_name},
                        )
                    )
                    current_chunk = ""
                    start = boundary
                elif len(current_chunk) > options.max_chunk_size:
                    # Split oversized chunk at last sentence boundary
                    last_sent = list(nlp(current_chunk).sents)[-1]
                    split_pos = len(current_chunk) - len(last_sent.text)

                    chunks.append(
                        Chunk(
                            text=current_chunk[:split_pos].strip(),
                            start=start,
                            end=start + split_pos,
                            metadata={"type": "semantic", "model": self._model_name},
                        )
                    )
                    current_chunk = current_chunk[split_pos:].strip()
                    start = start + split_pos

            # Add final chunk if any
            if current_chunk:
                chunks.append(
                    Chunk(
                        text=current_chunk,
                        start=start,
                        end=len(text),
                        metadata={"type": "semantic", "model": self._model_name},
                    )
                )

            return chunks

        except Exception as e:
            raise ChunkingError(f"Failed to chunk text: {e}")

    async def merge_chunks(
        self, chunks: List[Chunk], options: Optional[ChunkingOptions] = None
    ) -> str:
        """Merge chunks back into text.

        Args:
            chunks: Chunks to merge
            options: Optional chunking options

        Returns:
            Merged text

        Raises:
            ChunkingError: If merging fails
        """
        try:
            # Sort chunks by start position
            sorted_chunks = sorted(chunks, key=lambda x: x.start)

            # Merge chunks with appropriate spacing
            merged = []
            for chunk in sorted_chunks:
                # Add double newline between semantic chunks
                if merged and chunk.metadata.get("type") == "semantic":
                    merged.append("\n\n")
                merged.append(chunk.text)

            return "".join(merged)

        except Exception as e:
            raise ChunkingError(f"Failed to merge chunks: {e}")
