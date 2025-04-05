"""
PepperPy RAG Tasks.

Fluent API for RAG task configuration.
"""

from pathlib import Path
from typing import Any

from pepperpy.agent.task import TaskBase


class KnowledgeTask(TaskBase):
    """Base class for knowledge operations."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize knowledge task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["knowledge_type"] = name

    def output(self, path: str | Path) -> "KnowledgeTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class KnowledgeBase(KnowledgeTask):
    """Knowledge base configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize knowledge base.

        Args:
            name: Knowledge base name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["knowledge_type"] = "kb"
        self._config["sources"] = []
        self._config["embedding_model"] = "text-embedding-ada-002"
        self._config["chunk_size"] = 1000
        self._config["chunk_overlap"] = 200

    def source(self, source_path: str | Path) -> "KnowledgeBase":
        """Add a source document or directory.

        Args:
            source_path: Path to document or directory

        Returns:
            Self for method chaining
        """
        self._config["sources"].append(str(source_path))
        return self

    def sources(self, source_paths: list[str | Path]) -> "KnowledgeBase":
        """Add multiple source documents or directories.

        Args:
            source_paths: List of paths to documents or directories

        Returns:
            Self for method chaining
        """
        self._config["sources"].extend([str(p) for p in source_paths])
        return self

    def embedding(self, model: str) -> "KnowledgeBase":
        """Set the embedding model.

        Args:
            model: Embedding model name

        Returns:
            Self for method chaining
        """
        self._config["embedding_model"] = model
        return self

    def chunking(self, size: int, overlap: int = 200) -> "KnowledgeBase":
        """Configure document chunking.

        Args:
            size: Chunk size in tokens
            overlap: Overlap between chunks

        Returns:
            Self for method chaining
        """
        self._config["chunk_size"] = size
        self._config["chunk_overlap"] = overlap
        return self

    def filter(self, file_types: list[str]) -> "KnowledgeBase":
        """Filter source documents by type.

        Args:
            file_types: List of file extensions

        Returns:
            Self for method chaining
        """
        self._config["file_types"] = file_types
        return self


class Retrieval(KnowledgeTask):
    """Retrieval task configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize retrieval task.

        Args:
            name: Retrieval task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["knowledge_type"] = "retrieval"
        self._config["kb_name"] = None
        self._config["search_type"] = "similarity"
        self._config["top_k"] = 5

    def from_kb(self, kb_name: str) -> "Retrieval":
        """Set the knowledge base to query.

        Args:
            kb_name: Knowledge base name

        Returns:
            Self for method chaining
        """
        self._config["kb_name"] = kb_name
        return self

    def query(self, query_text: str) -> "Retrieval":
        """Set the query text.

        Args:
            query_text: Query text

        Returns:
            Self for method chaining
        """
        self._config["query"] = query_text
        return self

    def top_k(self, k: int) -> "Retrieval":
        """Set the number of results to retrieve.

        Args:
            k: Number of results

        Returns:
            Self for method chaining
        """
        self._config["top_k"] = k
        return self

    def search_type(self, method: str) -> "Retrieval":
        """Set the search method.

        Args:
            method: Search method (similarity, mmr, etc.)

        Returns:
            Self for method chaining
        """
        self._config["search_type"] = method
        return self


class RAG(KnowledgeTask):
    """RAG task configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize RAG task.

        Args:
            name: RAG task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["knowledge_type"] = "rag"
        self._config["kb_name"] = None
        self._config["query"] = None
        self._config["model"] = None
        self._config["top_k"] = 4
        self._config["temperature"] = 0.7

    def from_kb(self, kb_name: str) -> "RAG":
        """Set the knowledge base to query.

        Args:
            kb_name: Knowledge base name

        Returns:
            Self for method chaining
        """
        self._config["kb_name"] = kb_name
        return self

    def query(self, query_text: str) -> "RAG":
        """Set the query text.

        Args:
            query_text: Query text

        Returns:
            Self for method chaining
        """
        self._config["query"] = query_text
        return self

    def model(self, model_name: str) -> "RAG":
        """Set the model to use.

        Args:
            model_name: Model name

        Returns:
            Self for method chaining
        """
        self._config["model"] = model_name
        return self

    def top_k(self, k: int) -> "RAG":
        """Set the number of results to retrieve.

        Args:
            k: Number of results

        Returns:
            Self for method chaining
        """
        self._config["top_k"] = k
        return self

    def temperature(self, temp: float) -> "RAG":
        """Set the temperature.

        Args:
            temp: Temperature value

        Returns:
            Self for method chaining
        """
        self._config["temperature"] = temp
        return self

    def system_prompt(self, prompt: str) -> "RAG":
        """Set the system prompt.

        Args:
            prompt: System prompt text

        Returns:
            Self for method chaining
        """
        self._config["system_prompt"] = prompt
        return self
