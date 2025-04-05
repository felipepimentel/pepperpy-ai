"""
PepperPy Embedding Tasks.

Fluent API for embedding task configuration.
"""

from pathlib import Path
from typing import Any

from pepperpy.agent.task import TaskBase


class Embedding(TaskBase):
    """Text embedding configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize embedding task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["embedding_type"] = "text"
        self._config["model"] = "text-embedding-ada-002"
        self._config["inputs"] = []

    def model(self, model_name: str) -> "Embedding":
        """Set the embedding model to use.

        Args:
            model_name: Model identifier

        Returns:
            Self for method chaining
        """
        self._config["model"] = model_name
        return self

    def provider(self, provider_name: str) -> "Embedding":
        """Set the provider to use.

        Args:
            provider_name: Provider name

        Returns:
            Self for method chaining
        """
        self._config["provider"] = provider_name
        return self

    def input(self, text: str) -> "Embedding":
        """Add a text input for embedding.

        Args:
            text: Text to embed

        Returns:
            Self for method chaining
        """
        self._config["inputs"].append(text)
        return self

    def inputs(self, texts: list[str]) -> "Embedding":
        """Set multiple text inputs for embedding.

        Args:
            texts: List of texts to embed

        Returns:
            Self for method chaining
        """
        self._config["inputs"].extend(texts)
        return self

    def from_file(self, file_path: str | Path) -> "Embedding":
        """Load text from a file for embedding.

        Args:
            file_path: Path to file

        Returns:
            Self for method chaining
        """
        self._config["input_file"] = str(file_path)
        return self

    def normalize(self, enable: bool = True) -> "Embedding":
        """Enable or disable vector normalization.

        Args:
            enable: Whether to normalize vectors

        Returns:
            Self for method chaining
        """
        self._config["normalize"] = enable
        return self

    def output(self, path: str | Path) -> "Embedding":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class Similarity(TaskBase):
    """Text similarity configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize similarity task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["embedding_type"] = "similarity"
        self._config["model"] = "text-embedding-ada-002"
        self._config["query"] = None
        self._config["texts"] = []
        self._config["top_k"] = 5
        self._config["metric"] = "cosine"

    def model(self, model_name: str) -> "Similarity":
        """Set the embedding model to use.

        Args:
            model_name: Model identifier

        Returns:
            Self for method chaining
        """
        self._config["model"] = model_name
        return self

    def query(self, text: str) -> "Similarity":
        """Set the query text to compare against.

        Args:
            text: Query text

        Returns:
            Self for method chaining
        """
        self._config["query"] = text
        return self

    def text(self, text: str) -> "Similarity":
        """Add a comparison text.

        Args:
            text: Text to compare to query

        Returns:
            Self for method chaining
        """
        self._config["texts"].append(text)
        return self

    def texts(self, texts: list[str]) -> "Similarity":
        """Set multiple comparison texts.

        Args:
            texts: List of texts to compare

        Returns:
            Self for method chaining
        """
        self._config["texts"].extend(texts)
        return self

    def top_k(self, k: int) -> "Similarity":
        """Set number of top results to return.

        Args:
            k: Number of results

        Returns:
            Self for method chaining
        """
        self._config["top_k"] = k
        return self

    def metric(self, metric_name: str) -> "Similarity":
        """Set the similarity metric.

        Args:
            metric_name: Metric name (cosine, dot, euclidean)

        Returns:
            Self for method chaining
        """
        self._config["metric"] = metric_name
        return self

    def output(self, path: str | Path) -> "Similarity":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self
