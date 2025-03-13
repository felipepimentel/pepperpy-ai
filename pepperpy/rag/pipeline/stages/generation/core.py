"""
PepperPy RAG Pipeline Generation Stage Module.

This module contains the generation stage for the RAG pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from pepperpy.errors import PepperpyError, PepperpyValueError
from pepperpy.rag.interfaces import GenerationProvider, PipelineStage
from pepperpy.rag.models import Document, GenerationResult, Metadata, RerankingResult
from pepperpy.rag.pipeline.stages.base import StageConfig


@dataclass
class GenerationStageConfig(StageConfig):
    """Configuration for the generation stage."""

    prompt_template: str = "Baseado nos seguintes documentos, responda a pergunta:\n\nDocumentos: {documents}\n\nPergunta: {query}\n\nResposta:"
    document_separator: str = "\n---\n"

    def __post_init__(self):
        if not self.type:
            self.type = "generation"


class GenerationStage(PipelineStage):
    """Generation stage for the RAG pipeline."""

    def __init__(
        self,
        generation_provider: GenerationProvider,
        config: Optional[GenerationStageConfig] = None,
    ):
        """Initialize the generation stage.

        Args:
            generation_provider: The generation provider.
            config: The stage configuration.
        """
        self.generation_provider = generation_provider
        self.config = config or GenerationStageConfig(
            name="generation", type="generation"
        )

    def process(self, reranking_result: RerankingResult) -> GenerationResult:
        """Process reranking results.

        Args:
            reranking_result: The reranking results to process.

        Returns:
            The generation results.

        Raises:
            PepperpyError: If the generation fails.
        """
        try:
            query = reranking_result.query
            documents = reranking_result.documents

            if not documents:
                # Generate a response indicating no documents were found
                prompt = f"Não foi possível encontrar documentos relevantes para a pergunta: {query}. Por favor, forneça uma resposta geral ou sugira como reformular a pergunta."
                response = self.generation_provider.generate(prompt)
                return GenerationResult(
                    response=response,
                    documents=[],
                    query=query,
                    prompt=prompt,
                )

            # Prepare the documents text
            documents_text = self._prepare_documents_text(documents)

            # Prepare the prompt
            prompt = self.config.prompt_template.format(
                documents=documents_text, query=query
            )

            # Generate the response
            response = self.generation_provider.generate(prompt)

            # Return the results
            return GenerationResult(
                response=response,
                documents=documents,
                query=query,
                prompt=prompt,
            )
        except Exception as e:
            raise PepperpyError(
                f"Failed to generate response for query: {reranking_result.query}. Error: {str(e)}"
            ) from e

    def _prepare_documents_text(self, documents: List[Document]) -> str:
        """Prepare documents text for the prompt.

        Args:
            documents: The documents to prepare.

        Returns:
            The prepared documents text.
        """
        texts = []
        for i, doc in enumerate(documents):
            # Get document content and metadata
            content = doc.content or ""
            metadata: Union[Metadata, Dict[str, Any]] = doc.metadata or {}

            # Format document metadata
            metadata_str = ""
            if metadata:
                # Use dictionary access for metadata which could be a dict
                source = (
                    metadata.get("source", "") if isinstance(metadata, dict) else ""
                )
                title = metadata.get("title", "") if isinstance(metadata, dict) else ""

                if source and title:
                    metadata_str = f"[Documento {i + 1}: {title} (Fonte: {source})]"
                elif source:
                    metadata_str = f"[Documento {i + 1} (Fonte: {source})]"
                elif title:
                    metadata_str = f"[Documento {i + 1}: {title}]"
                else:
                    metadata_str = f"[Documento {i + 1}]"

            # Add document with metadata
            if metadata_str:
                texts.append(f"{metadata_str}\n{content}")
            else:
                texts.append(content)

        return self.config.document_separator.join(texts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the stage to a dictionary.

        Returns:
            The stage as a dictionary.
        """
        return {
            "type": self.config.type,
            "name": self.config.name,
            "enabled": self.config.enabled,
            "params": {
                "prompt_template": self.config.prompt_template,
                "document_separator": self.config.document_separator,
                **self.config.params,
            },
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], generation_provider: GenerationProvider
    ) -> "GenerationStage":
        """Create a stage from a dictionary.

        Args:
            data: The stage data.
            generation_provider: The generation provider.

        Returns:
            The created stage.

        Raises:
            PepperpyValueError: If the data is invalid.
        """
        if not isinstance(data, dict):
            raise PepperpyValueError(f"Expected dictionary, got {type(data).__name__}")

        if data.get("type") != "generation":
            raise PepperpyValueError(
                f"Expected type 'generation', got {data.get('type')}"
            )

        params = data.get("params", {})
        config = GenerationStageConfig(
            name=data.get("name", "generation"),
            type="generation",
            enabled=data.get("enabled", True),
            params=params,
        )

        if "prompt_template" in params:
            config.prompt_template = params["prompt_template"]
        if "document_separator" in params:
            config.document_separator = params["document_separator"]

        return cls(
            generation_provider=generation_provider,
            config=config,
        )
