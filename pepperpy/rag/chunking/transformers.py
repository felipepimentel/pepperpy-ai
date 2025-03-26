"""Sentence transformers text chunking."""

from typing import Any, Dict, List, Optional, cast

import nltk
import numpy as np
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

from pepperpy.rag.chunking.base import (
    Chunk,
    ChunkingError,
    ChunkingOptions,
    TextChunker,
)


class SentenceTransformersChunker(TextChunker):
    """Chunker that uses sentence transformers for semantic chunking.

    This chunker:
    1. Splits text into sentences
    2. Computes sentence embeddings
    3. Groups similar sentences into chunks
    4. Maintains semantic coherence using embedding similarity
    """

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize sentence transformers chunker.

        Args:
            model: Sentence transformers model to use
            config: Optional configuration
            **kwargs: Additional configuration options
        """
        super().__init__(name="transformers", config=config, **kwargs)
        self._model_name = model
        self._model: Optional[SentenceTransformer] = None
        self._nltk_downloaded = False

    async def _initialize(self) -> None:
        """Initialize the model and NLTK data."""
        try:
            # Download NLTK data if needed
            if not self._nltk_downloaded:
                nltk.download("punkt", quiet=True)
                self._nltk_downloaded = True

            # Load model
            self._model = SentenceTransformer(self._model_name)

        except Exception as e:
            raise ChunkingError(f"Failed to initialize: {e}")

    async def _cleanup(self) -> None:
        """Clean up resources."""
        self._model = None

    def _compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between embeddings.

        Args:
            emb1: First embedding
            emb2: Second embedding

        Returns:
            Similarity score between 0 and 1
        """
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

    def _group_sentences(
        self, sentences: List[str], embeddings: np.ndarray, options: ChunkingOptions
    ) -> List[List[int]]:
        """Group sentences into semantically coherent chunks.

        Uses embedding similarity to group sentences while respecting
        size constraints from options.

        Args:
            sentences: List of sentences
            embeddings: Sentence embeddings
            options: Chunking options

        Returns:
            List of sentence index groups
        """
        groups = []
        current_group = []
        current_length = 0

        for i, sentence in enumerate(sentences):
            # Start new group if current would exceed max size
            if current_length + len(sentence) > options.max_chunk_size:
                if current_group:
                    groups.append(current_group)
                current_group = []
                current_length = 0

            # Add to current group if empty or similar to last sentence
            if (
                not current_group
                or self._compute_similarity(
                    embeddings[current_group[-1]], embeddings[i]
                )
                > 0.5
            ):
                current_group.append(i)
                current_length += len(sentence)
            # Start new group if dissimilar
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [i]
                current_length = len(sentence)

        # Add final group
        if current_group:
            groups.append(current_group)

        return groups

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
        if not self._model:
            await self.initialize()

        model = cast(SentenceTransformer, self._model)
        options = options or ChunkingOptions()

        try:
            # Split into sentences
            sentences = sent_tokenize(text)
            if not sentences:
                return []

            # Get sentence embeddings
            embeddings = model.encode(
                sentences, convert_to_numpy=True, show_progress_bar=False
            )

            # Group similar sentences
            groups = self._group_sentences(sentences, embeddings, options)

            # Create chunks from groups
            chunks = []
            current_pos = 0

            for group in groups:
                # Get text span for group
                start_sent = sentences[group[0]]
                end_sent = sentences[group[-1]]

                # Find start position
                start = text.find(start_sent, current_pos)
                if start == -1:
                    continue

                # Find end position
                end = text.find(end_sent, start) + len(end_sent)
                if end == -1:
                    continue

                # Create chunk
                chunk_text = text[start:end]
                if (
                    len(chunk_text) >= options.min_chunk_size
                    and len(chunk_text) <= options.max_chunk_size
                ):
                    chunks.append(
                        Chunk(
                            text=chunk_text,
                            start=start,
                            end=end,
                            metadata={
                                "type": "transformers",
                                "model": self._model_name,
                                "num_sentences": len(group),
                            },
                        )
                    )

                current_pos = end

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
                # Add newline between transformer chunks
                if merged and chunk.metadata.get("type") == "transformers":
                    merged.append("\n")
                merged.append(chunk.text)

            return "".join(merged)

        except Exception as e:
            raise ChunkingError(f"Failed to merge chunks: {e}")
