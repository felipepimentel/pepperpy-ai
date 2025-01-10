"""Embedding types module"""

from dataclasses import dataclass

# Define o tipo para vetores de embedding
EmbeddingVector = list[float]


@dataclass
class EmbeddingResult:
    """Result of embedding operation"""

    embeddings: EmbeddingVector
    dimensions: int
    text: str
    model: str

    def __len__(self) -> int:
        """Get length of embeddings"""
        return len(self.embeddings)
