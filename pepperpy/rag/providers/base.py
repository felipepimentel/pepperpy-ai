"""
PepperPy RAG Providers Base Module.

Este módulo contém as classes base para todos os provedores do sistema RAG.
"""

from __future__ import annotations

import abc
from typing import Any, List, Optional, Tuple, Union

from pepperpy.rag.document.core import Document
from pepperpy.rag.errors import EmbeddingError, GenerationError, RerankingError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Provider Base
# -----------------------------------------------------------------------------


class BaseProvider(abc.ABC):
    """Classe base para todos os provedores do sistema RAG."""

    def __init__(self, model_name: Optional[str] = None):
        """Inicializa o provedor base.

        Args:
            model_name: Nome opcional do modelo a ser utilizado
        """
        self.model_name = model_name

    def __repr__(self) -> str:
        """Representação string do provedor.

        Returns:
            String representando o provedor
        """
        model_str = f", model='{self.model_name}'" if self.model_name else ""
        return f"{self.__class__.__name__}({model_str})"


# -----------------------------------------------------------------------------
# Embedding Provider Base
# -----------------------------------------------------------------------------


class BaseEmbeddingProvider(BaseProvider):
    """Classe base para provedores de embeddings.

    Esta classe define a interface que todos os provedores de embeddings devem implementar.
    """

    @abc.abstractmethod
    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Método interno para gerar embeddings de textos.

        Args:
            texts: Lista de textos para gerar embeddings

        Returns:
            Lista de embeddings para cada texto

        Raises:
            EmbeddingError: Se ocorrer um erro durante a geração de embeddings
        """
        pass

    async def embed_query(self, query: str) -> List[float]:
        """Gera o embedding para uma consulta.

        Args:
            query: A consulta para gerar embedding

        Returns:
            O embedding da consulta

        Raises:
            EmbeddingError: Se ocorrer um erro durante a geração do embedding
        """
        try:
            embeddings = await self._embed_texts([query])
            return embeddings[0]
        except Exception as e:
            error_msg = f"Erro ao gerar embedding para a consulta: {e}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg) from e

    async def embed_documents(
        self, documents: List[Union[str, Document]]
    ) -> List[List[float]]:
        """Gera embeddings para documentos.

        Args:
            documents: Lista de documentos ou textos para gerar embeddings

        Returns:
            Lista de embeddings para cada documento

        Raises:
            EmbeddingError: Se ocorrer um erro durante a geração dos embeddings
        """
        try:
            # Extrair texto dos documentos se for uma lista de Document
            if documents and isinstance(documents[0], Document):
                texts = [doc.content for doc in documents]
            else:
                texts = documents  # type: ignore

            return await self._embed_texts(texts)
        except Exception as e:
            error_msg = f"Erro ao gerar embeddings para os documentos: {e}"
            logger.error(error_msg)
            raise EmbeddingError(error_msg) from e


# -----------------------------------------------------------------------------
# Reranking Provider Base
# -----------------------------------------------------------------------------


class BaseRerankingProvider(BaseProvider):
    """Classe base para provedores de reranking.

    Esta classe define a interface que todos os provedores de reranking devem implementar.
    """

    @abc.abstractmethod
    async def _compute_scores(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Método interno para calcular scores de relevância.

        Args:
            query: A consulta
            documents: Lista de documentos para calcular scores
            scores: Scores iniciais opcionais

        Returns:
            Lista de scores para cada documento

        Raises:
            RerankingError: Se ocorrer um erro durante o cálculo dos scores
        """
        pass

    async def rerank(
        self,
        query: str,
        documents: List[Union[str, Document]],
        scores: Optional[List[float]] = None,
    ) -> List[Tuple[int, float]]:
        """Reordena documentos com base na relevância.

        Args:
            query: A consulta
            documents: Lista de documentos para reordenar
            scores: Scores iniciais opcionais

        Returns:
            Lista de tuplas (índice original, score) ordenada por score

        Raises:
            RerankingError: Se ocorrer um erro durante o reranking
        """
        try:
            # Extrair texto dos documentos se for uma lista de Document
            if documents and isinstance(documents[0], Document):
                texts = [doc.content for doc in documents]
            else:
                texts = documents  # type: ignore

            # Calcular scores
            computed_scores = await self._compute_scores(query, texts, scores)

            # Criar pares (índice, score) e ordenar por score em ordem decrescente
            ranked_pairs = sorted(
                enumerate(computed_scores), key=lambda x: x[1], reverse=True
            )

            return ranked_pairs
        except Exception as e:
            error_msg = f"Erro ao reordenar documentos: {e}"
            logger.error(error_msg)
            raise RerankingError(error_msg) from e

    async def get_scores(
        self,
        query: str,
        documents: List[Union[str, Document]],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Calcula scores de relevância.

        Args:
            query: A consulta
            documents: Lista de documentos para calcular scores
            scores: Scores iniciais opcionais

        Returns:
            Lista de scores para cada documento

        Raises:
            RerankingError: Se ocorrer um erro durante o cálculo dos scores
        """
        try:
            # Extrair texto dos documentos se for uma lista de Document
            if documents and isinstance(documents[0], Document):
                texts = [doc.content for doc in documents]
            else:
                texts = documents  # type: ignore

            return await self._compute_scores(query, texts, scores)
        except Exception as e:
            error_msg = f"Erro ao calcular scores: {e}"
            logger.error(error_msg)
            raise RerankingError(error_msg) from e


# -----------------------------------------------------------------------------
# Generation Provider Base
# -----------------------------------------------------------------------------


class BaseGenerationProvider(BaseProvider):
    """Classe base para provedores de geração.

    Esta classe define a interface que todos os provedores de geração devem implementar.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        default_prompt_template: Optional[str] = None,
    ):
        """Inicializa o provedor de geração base.

        Args:
            model_name: Nome opcional do modelo a ser utilizado
            default_prompt_template: Template de prompt padrão opcional
        """
        super().__init__(model_name)
        self.default_prompt_template = default_prompt_template or (
            "Baseado nos seguintes documentos, responda a pergunta:\n\n"
            "Documentos:\n{documents}\n\n"
            "Pergunta: {query}\n\n"
            "Resposta:"
        )

    def _format_prompt(
        self,
        query: str,
        documents: List[str],
        prompt_template: Optional[str] = None,
    ) -> str:
        """Formata o prompt para geração.

        Args:
            query: A consulta
            documents: Lista de documentos de contexto
            prompt_template: Template de prompt opcional

        Returns:
            O prompt formatado
        """
        template = prompt_template or self.default_prompt_template

        # Junta os documentos com separador
        docs_text = "\n\n---\n\n".join(documents)

        # Substitui os placeholders no template
        prompt = template.format(query=query, documents=docs_text)

        return prompt

    @abc.abstractmethod
    async def _generate_text(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Método interno para gerar texto.

        Args:
            prompt: O prompt para geração
            **kwargs: Parâmetros adicionais para a geração

        Returns:
            O texto gerado

        Raises:
            GenerationError: Se ocorrer um erro durante a geração
        """
        pass

    async def generate(
        self,
        query: str,
        documents: List[Union[str, Document]],
        prompt_template: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Gera resposta com base em documentos de contexto.

        Args:
            query: A consulta
            documents: Lista de documentos de contexto
            prompt_template: Template de prompt opcional
            **kwargs: Parâmetros adicionais para a geração

        Returns:
            A resposta gerada

        Raises:
            GenerationError: Se ocorrer um erro durante a geração
        """
        try:
            # Extrair texto dos documentos se for uma lista de Document
            if documents and isinstance(documents[0], Document):
                texts = [doc.content for doc in documents]
            else:
                texts = documents  # type: ignore

            # Formatar o prompt
            prompt = self._format_prompt(query, texts, prompt_template)

            # Gerar resposta
            response = await self._generate_text(prompt, **kwargs)

            return response
        except Exception as e:
            error_msg = f"Erro ao gerar resposta: {e}"
            logger.error(error_msg)
            raise GenerationError(error_msg) from e
