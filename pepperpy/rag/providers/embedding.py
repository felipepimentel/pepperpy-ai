"""
PepperPy RAG Embedding Providers Module.

Este módulo contém a implementação dos provedores de embedding para o sistema RAG.
"""

from __future__ import annotations

import random
from typing import Any, List, Optional

from pepperpy.rag.errors import EmbeddingError
from pepperpy.rag.providers.base import BaseEmbeddingProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Mock Embedding Provider
# -----------------------------------------------------------------------------


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Provider de embedding simulado para testes.

    Este provider gera embeddings aleatórios com dimensão fixa.
    """

    def __init__(
        self,
        embedding_dim: int = 384,
        model_name: str = "mock-embedding-model",
        seed: Optional[int] = None,
    ):
        """Inicializa o provider de embedding simulado.

        Args:
            embedding_dim: Dimensão dos embeddings gerados
            model_name: Nome do modelo simulado
            seed: Semente para o gerador de números aleatórios
        """
        super().__init__(model_name=model_name)
        self.embedding_dim = embedding_dim
        self.random = random.Random(seed)

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings aleatórios para os textos.

        Args:
            texts: Lista de textos para gerar embeddings

        Returns:
            Lista de embeddings para cada texto
        """
        logger.debug(f"Gerando embeddings simulados para {len(texts)} textos")

        # Gera embeddings aleatórios para cada texto
        embeddings = []
        for text in texts:
            # Usa o hash do texto como seed para ter consistência
            text_seed = hash(text) % 10000
            local_random = random.Random(text_seed)

            # Gera um embedding aleatório normalizado
            embedding = [local_random.uniform(-1, 1) for _ in range(self.embedding_dim)]

            # Normaliza o embedding para ter norma 1
            norm = sum(x**2 for x in embedding) ** 0.5
            if norm > 0:
                embedding = [x / norm for x in embedding]

            embeddings.append(embedding)

        return embeddings

    def __repr__(self) -> str:
        return f"MockEmbeddingProvider(model='{self.model_name}', dim={self.embedding_dim})"


# -----------------------------------------------------------------------------
# OpenAI Embedding Provider
# -----------------------------------------------------------------------------


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Provider de embedding usando a API da OpenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "text-embedding-ada-002",
        batch_size: int = 100,
        **kwargs: Any,
    ):
        """Inicializa o provider de embedding da OpenAI.

        Args:
            api_key: Chave API da OpenAI
            model_name: Nome do modelo de embedding
            batch_size: Tamanho do lote para processamento em batches
            **kwargs: Parâmetros adicionais para a API da OpenAI
        """
        super().__init__(model_name=model_name)
        self.api_key = api_key
        self.batch_size = batch_size
        self.kwargs = kwargs

        # Client será inicializado na primeira chamada
        self._client = None

    async def _get_client(self):
        """Obtém um cliente OpenAI.

        Returns:
            Cliente OpenAI inicializado
        """
        if self._client is None:
            try:
                # Importação condicional para não depender da biblioteca OpenAI se não for usada
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise EmbeddingError(
                    "A biblioteca openai não está instalada. "
                    "Instale-a com: pip install openai"
                )

        return self._client

    async def _process_batch(self, batch: List[str]) -> List[List[float]]:
        """Processa um lote de textos.

        Args:
            batch: Lote de textos

        Returns:
            Lista de embeddings para o lote

        Raises:
            EmbeddingError: Se ocorrer um erro na API da OpenAI
        """
        try:
            client = await self._get_client()

            # Faz a chamada à API
            response = await client.embeddings.create(
                input=batch, model=self.model_name, **self.kwargs
            )

            # Extrair os embeddings do resultado
            batch_embeddings = [embedding.embedding for embedding in response.data]

            return batch_embeddings

        except Exception as e:
            raise EmbeddingError(f"Erro na API OpenAI: {str(e)}") from e

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para os textos usando a API da OpenAI.

        Args:
            texts: Lista de textos para gerar embeddings

        Returns:
            Lista de embeddings para cada texto

        Raises:
            EmbeddingError: Se ocorrer um erro na API da OpenAI
        """
        logger.debug(f"Gerando embeddings com OpenAI para {len(texts)} textos")

        # Nenhum texto para processar
        if not texts:
            return []

        # Processa em lotes para evitar limite de tamanho da API
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batch_embeddings = await self._process_batch(batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    def __repr__(self) -> str:
        return f"OpenAIEmbeddingProvider(model='{self.model_name}', batch_size={self.batch_size})"
