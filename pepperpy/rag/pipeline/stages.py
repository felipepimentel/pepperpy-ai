"""
PepperPy RAG Pipeline Stages Module.

Este módulo contém os estágios para o pipeline RAG.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from pepperpy.errors import PepperpyError, PepperpyValueError
from pepperpy.rag.document.core import Document

# -----------------------------------------------------------------------------
# Base / Interfaces comuns para estágios
# -----------------------------------------------------------------------------


class PipelineStage(abc.ABC):
    """Classe base para todos os estágios do pipeline RAG."""

    @abc.abstractmethod
    def process(self, inputs: Any) -> Any:
        """Processa os inputs do estágio.

        Args:
            inputs: Os inputs para o estágio.

        Returns:
            Os outputs do estágio.
        """
        pass


@dataclass
class StageConfig:
    """Configuração base para estágios do pipeline."""

    name: str
    type: str
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


# -----------------------------------------------------------------------------
# Estágio de Retrieval
# -----------------------------------------------------------------------------


class EmbeddingProvider(Protocol):
    """Interface para provedores de embeddings."""

    def embed_query(self, query: str) -> List[float]:
        """Gera um embedding para a query.

        Args:
            query: A query para gerar o embedding.

        Returns:
            O embedding da query.
        """
        ...

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """Gera embeddings para documentos.

        Args:
            documents: Os documentos para gerar embeddings.

        Returns:
            Os embeddings dos documentos.
        """
        ...


@dataclass
class RetrievalResult:
    """Resultado de uma operação de retrieval."""

    documents: List[Document]
    query: str
    query_embedding: Optional[List[float]] = None
    scores: Optional[List[float]] = None


@dataclass
class RetrievalStageConfig(StageConfig):
    """Configuração para o estágio de retrieval."""

    top_k: int = 5

    def __post_init__(self):
        if not self.type:
            self.type = "retrieval"


class RetrievalStage(PipelineStage):
    """Estágio de retrieval do pipeline RAG."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        document_store: Any,  # DocumentStore
        config: Optional[RetrievalStageConfig] = None,
    ):
        """Inicializa o estágio de retrieval.

        Args:
            embedding_provider: O provedor de embeddings.
            document_store: O armazenamento de documentos.
            config: A configuração do estágio.
        """
        self.embedding_provider = embedding_provider
        self.document_store = document_store
        self.config = config or RetrievalStageConfig(name="retrieval", type="retrieval")

        # Validação do top_k
        if self.config.top_k <= 0:
            raise PepperpyValueError("top_k deve ser maior que zero")

    def process(self, query: str) -> RetrievalResult:
        """Processa a query para recuperar documentos relevantes.

        Args:
            query: A query de busca.

        Returns:
            O resultado da recuperação.
        """
        # Verifica se o estágio está habilitado
        if not self.config.enabled:
            return RetrievalResult(documents=[], query=query)

        try:
            # Gera o embedding da query
            query_embedding = self.embedding_provider.embed_query(query)

            # Busca documentos similares
            search_results = self.document_store.search(
                query_embedding=query_embedding,
                limit=self.config.top_k,
                **self.config.params,
            )

            # Extrai documentos e scores
            documents = [result.document for result in search_results]
            scores = [result.score for result in search_results]

            return RetrievalResult(
                documents=documents,
                query=query,
                query_embedding=query_embedding,
                scores=scores,
            )

        except Exception as e:
            # Em caso de erro, registra e retorna uma lista vazia
            raise PepperpyError(f"Erro no estágio de retrieval: {e}") from e

    def to_dict(self) -> Dict[str, Any]:
        """Converte o estágio para um dicionário.

        Returns:
            O estágio como um dicionário.
        """
        return {
            "type": self.config.type,
            "name": self.config.name,
            "enabled": self.config.enabled,
            "params": self.config.params,
            "top_k": self.config.top_k,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        embedding_provider: EmbeddingProvider,
        document_store: Any,
    ) -> "RetrievalStage":
        """Cria um estágio de retrieval a partir de um dicionário.

        Args:
            data: O dicionário com os dados do estágio.
            embedding_provider: O provedor de embeddings.
            document_store: O armazenamento de documentos.

        Returns:
            O estágio de retrieval criado.
        """
        config = RetrievalStageConfig(
            name=data.get("name", "retrieval"),
            type=data.get("type", "retrieval"),
            enabled=data.get("enabled", True),
            params=data.get("params", {}),
            top_k=data.get("top_k", 5),
        )

        return cls(
            embedding_provider=embedding_provider,
            document_store=document_store,
            config=config,
        )


# -----------------------------------------------------------------------------
# Estágio de Reranking
# -----------------------------------------------------------------------------


class RerankerProvider(Protocol):
    """Interface para provedores de reranking."""

    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """Reordena documentos com base na relevância.

        Args:
            query: A query de busca.
            documents: Os documentos a serem reordenados.

        Returns:
            Os documentos reordenados.
        """
        ...

    def get_scores(self, query: str, documents: List[Document]) -> List[float]:
        """Calcula os scores de relevância.

        Args:
            query: A query de busca.
            documents: Os documentos a serem pontuados.

        Returns:
            Os scores dos documentos.
        """
        ...


@dataclass
class RerankingResult:
    """Resultado de uma operação de reranking."""

    documents: List[Document]
    query: str
    scores: Optional[List[float]] = None


@dataclass
class RerankingStageConfig(StageConfig):
    """Configuração para o estágio de reranking."""

    top_k: int = 3

    def __post_init__(self):
        if not self.type:
            self.type = "reranking"


class RerankingStage(PipelineStage):
    """Estágio de reranking do pipeline RAG."""

    def __init__(
        self,
        reranker_provider: RerankerProvider,
        config: Optional[RerankingStageConfig] = None,
    ):
        """Inicializa o estágio de reranking.

        Args:
            reranker_provider: O provedor de reranking.
            config: A configuração do estágio.
        """
        self.reranker_provider = reranker_provider
        self.config = config or RerankingStageConfig(name="reranking", type="reranking")

        # Validação do top_k
        if self.config.top_k <= 0:
            raise PepperpyValueError("top_k deve ser maior que zero")

    def process(self, retrieval_result: RetrievalResult) -> RerankingResult:
        """Reordena os documentos recuperados.

        Args:
            retrieval_result: O resultado do estágio de retrieval.

        Returns:
            O resultado do reranking.
        """
        # Verifica se o estágio está habilitado
        if not self.config.enabled:
            return RerankingResult(
                documents=retrieval_result.documents,
                query=retrieval_result.query,
                scores=retrieval_result.scores,
            )

        # Verifica se há documentos para reordenar
        if not retrieval_result.documents:
            return RerankingResult(documents=[], query=retrieval_result.query)

        try:
            # Reordena os documentos
            scores = self.reranker_provider.get_scores(
                retrieval_result.query, retrieval_result.documents
            )

            # Combina documentos e scores
            doc_with_scores = list(zip(retrieval_result.documents, scores))

            # Ordena por score (em ordem decrescente)
            doc_with_scores.sort(key=lambda x: x[1], reverse=True)

            # Limita o número de documentos
            doc_with_scores = doc_with_scores[: self.config.top_k]

            # Separa documentos e scores novamente
            documents = [doc for doc, _ in doc_with_scores]
            scores = [score for _, score in doc_with_scores]

            return RerankingResult(
                documents=documents,
                query=retrieval_result.query,
                scores=scores,
            )

        except Exception as e:
            # Em caso de erro, retorna os documentos originais
            raise PepperpyError(f"Erro no estágio de reranking: {e}") from e

    def to_dict(self) -> Dict[str, Any]:
        """Converte o estágio para um dicionário.

        Returns:
            O estágio como um dicionário.
        """
        return {
            "type": self.config.type,
            "name": self.config.name,
            "enabled": self.config.enabled,
            "params": self.config.params,
            "top_k": self.config.top_k,
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], reranker_provider: RerankerProvider
    ) -> "RerankingStage":
        """Cria um estágio de reranking a partir de um dicionário.

        Args:
            data: O dicionário com os dados do estágio.
            reranker_provider: O provedor de reranking.

        Returns:
            O estágio de reranking criado.
        """
        config = RerankingStageConfig(
            name=data.get("name", "reranking"),
            type=data.get("type", "reranking"),
            enabled=data.get("enabled", True),
            params=data.get("params", {}),
            top_k=data.get("top_k", 3),
        )

        return cls(
            reranker_provider=reranker_provider,
            config=config,
        )


# -----------------------------------------------------------------------------
# Estágio de Generation
# -----------------------------------------------------------------------------


class GenerationProvider(Protocol):
    """Interface para provedores de geração."""

    def generate(self, prompt: str, **kwargs) -> str:
        """Gera uma resposta com base no prompt.

        Args:
            prompt: O prompt para geração.
            **kwargs: Parâmetros adicionais.

        Returns:
            A resposta gerada.
        """
        ...


@dataclass
class GenerationResult:
    """Resultado de uma operação de geração."""

    response: str
    documents: List[Document]
    query: str
    prompt: str


@dataclass
class GenerationStageConfig(StageConfig):
    """Configuração para o estágio de geração."""

    prompt_template: str = "Baseado nos seguintes documentos, responda a pergunta:\n\nDocumentos: {documents}\n\nPergunta: {query}\n\nResposta:"
    document_separator: str = "\n---\n"

    def __post_init__(self):
        if not self.type:
            self.type = "generation"


class GenerationStage(PipelineStage):
    """Estágio de geração do pipeline RAG."""

    def __init__(
        self,
        generation_provider: GenerationProvider,
        config: Optional[GenerationStageConfig] = None,
    ):
        """Inicializa o estágio de geração.

        Args:
            generation_provider: O provedor de geração.
            config: A configuração do estágio.
        """
        self.generation_provider = generation_provider
        self.config = config or GenerationStageConfig(
            name="generation", type="generation"
        )

    def process(self, reranking_result: RerankingResult) -> GenerationResult:
        """Gera uma resposta com base nos documentos recuperados.

        Args:
            reranking_result: O resultado do estágio de reranking.

        Returns:
            O resultado da geração.
        """
        # Verifica se o estágio está habilitado
        if not self.config.enabled:
            return GenerationResult(
                response="",
                documents=reranking_result.documents,
                query=reranking_result.query,
                prompt="",
            )

        try:
            # Prepara o texto dos documentos
            documents_text = self._prepare_documents_text(reranking_result.documents)

            # Formata o prompt
            prompt = self.config.prompt_template.format(
                documents=documents_text,
                query=reranking_result.query,
                **self.config.params,
            )

            # Gera a resposta
            response = self.generation_provider.generate(prompt)

            return GenerationResult(
                response=response,
                documents=reranking_result.documents,
                query=reranking_result.query,
                prompt=prompt,
            )

        except Exception as e:
            # Em caso de erro, retorna uma resposta vazia
            raise PepperpyError(f"Erro no estágio de geração: {e}") from e

    def _prepare_documents_text(self, documents: List[Document]) -> str:
        """Prepara o texto dos documentos para o prompt.

        Args:
            documents: Os documentos a serem preparados.

        Returns:
            O texto formatado dos documentos.
        """
        if not documents:
            return ""

        document_texts = []

        for i, doc in enumerate(documents):
            # Obtém o texto do documento
            text = doc.content

            # Adiciona metadados se disponíveis
            meta_str = ""
            if doc.metadata.source:
                meta_str += f"Fonte: {doc.metadata.source}\n"
            if doc.metadata.title:
                meta_str += f"Título: {doc.metadata.title}\n"

            # Adiciona informações adicionais dos metadados personalizados
            if "page" in doc.metadata.custom:
                meta_str += f"Página: {doc.metadata.custom['page']}\n"

            # Formata o texto final do documento
            if meta_str:
                document_texts.append(f"{meta_str}\nConteúdo: {text}")
            else:
                document_texts.append(f"Documento {i + 1}: {text}")

        # Junta os textos dos documentos com o separador configurado
        return self.config.document_separator.join(document_texts)

    def to_dict(self) -> Dict[str, Any]:
        """Converte o estágio para um dicionário.

        Returns:
            O estágio como um dicionário.
        """
        return {
            "type": self.config.type,
            "name": self.config.name,
            "enabled": self.config.enabled,
            "params": self.config.params,
            "prompt_template": self.config.prompt_template,
            "document_separator": self.config.document_separator,
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], generation_provider: GenerationProvider
    ) -> "GenerationStage":
        """Cria um estágio de geração a partir de um dicionário.

        Args:
            data: O dicionário com os dados do estágio.
            generation_provider: O provedor de geração.

        Returns:
            O estágio de geração criado.
        """
        config = GenerationStageConfig(
            name=data.get("name", "generation"),
            type=data.get("type", "generation"),
            enabled=data.get("enabled", True),
            params=data.get("params", {}),
            prompt_template=data.get(
                "prompt_template", GenerationStageConfig.prompt_template
            ),
            document_separator=data.get(
                "document_separator", GenerationStageConfig.document_separator
            ),
        )

        return cls(
            generation_provider=generation_provider,
            config=config,
        )
