"""
PepperPy RAG Reranking Providers Module.

Este módulo contém a implementação dos provedores de reranking para o sistema RAG.
"""

from __future__ import annotations

import random
from typing import Any, List, Optional

import numpy as np

from pepperpy.rag.errors import RerankingError
from pepperpy.rag.providers.base import BaseRerankingProvider
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Mock Reranking Provider
# -----------------------------------------------------------------------------


class MockRerankingProvider(BaseRerankingProvider):
    """Provider de reranking simulado para testes.

    Este provider gera scores aleatórios ou baseados em heurísticas simples.
    """

    def __init__(
        self,
        model_name: str = "mock-reranking-model",
        seed: Optional[int] = None,
        score_pattern: str = "random",
    ):
        """Inicializa o provider de reranking simulado.

        Args:
            model_name: Nome do modelo simulado
            seed: Semente para o gerador de números aleatórios
            score_pattern: Padrão para geração de scores ('random', 'keyword' ou 'length')
        """
        super().__init__(model_name=model_name)
        self.random = random.Random(seed)
        self.score_pattern = score_pattern

    async def _compute_scores(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Gera scores de relevância simulados para os documentos.

        Args:
            query: A consulta
            documents: Lista de documentos para calcular scores
            scores: Scores iniciais opcionais

        Returns:
            Lista de scores para cada documento
        """
        logger.debug(f"Computando scores simulados para {len(documents)} documentos")

        # Se não houver documentos, retorna uma lista vazia
        if not documents:
            return []

        # Usa os scores iniciais se fornecidos, ou cria uma nova lista
        computed_scores = list(scores) if scores else [0.0] * len(documents)

        # Cálculo simulado de scores
        if self.score_pattern == "random":
            # Gera scores aleatórios entre 0 e 1
            for i in range(len(documents)):
                computed_scores[i] = self.random.random()

        elif self.score_pattern == "keyword":
            # Scores baseados em palavras-chave da consulta
            query_words = query.lower().split()
            for i, doc in enumerate(documents):
                # Conta quantas palavras da consulta estão presentes no documento
                doc_lower = doc.lower()
                matches = sum(1 for word in query_words if word in doc_lower)
                # Calcula um score baseado na proporção de palavras encontradas
                computed_scores[i] = matches / len(query_words) if query_words else 0.0
                # Adiciona aleatoriedade para evitar empates
                computed_scores[i] += self.random.uniform(0, 0.1)
                # Limita o score a 1.0
                computed_scores[i] = min(computed_scores[i], 1.0)

        elif self.score_pattern == "length":
            # Scores baseados no comprimento do documento
            # Documentos de comprimento médio recebem scores mais altos
            doc_lengths = [len(doc) for doc in documents]
            avg_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0

            for i, length in enumerate(doc_lengths):
                # Calcula um score que favorece documentos próximos ao comprimento médio
                distance = abs(length - avg_length) / (avg_length or 1)
                computed_scores[i] = max(0, 1 - (distance / 2))
                # Adiciona aleatoriedade para evitar empates
                computed_scores[i] += self.random.uniform(0, 0.1)
                # Limita o score a 1.0
                computed_scores[i] = min(computed_scores[i], 1.0)

        return computed_scores

    def __repr__(self) -> str:
        return f"MockRerankingProvider(model='{self.model_name}', pattern='{self.score_pattern}')"


# -----------------------------------------------------------------------------
# Cross-Encoder Reranking Provider
# -----------------------------------------------------------------------------


class CrossEncoderProvider(BaseRerankingProvider):
    """Provider de reranking usando modelos Cross-Encoder da Hugging Face.

    Este provider requer que o pacote sentence-transformers esteja instalado.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        batch_size: int = 16,
        device: Optional[str] = None,
        **kwargs: Any,
    ):
        """Inicializa o provider de Cross-Encoder.

        Args:
            model_name: Nome do modelo no Hugging Face
            batch_size: Tamanho do lote para processamento em batches
            device: Dispositivo para inferência ('cpu', 'cuda', etc.)
            **kwargs: Parâmetros adicionais para o modelo
        """
        super().__init__(model_name=model_name)
        self.batch_size = batch_size
        self.device = device
        self.kwargs = kwargs

        # Modelo será inicializado na primeira chamada
        self._model = None

    async def _load_model(self):
        """Carrega o modelo Cross-Encoder.

        Returns:
            Modelo Cross-Encoder inicializado

        Raises:
            RerankingError: Se ocorrer um erro ao carregar o modelo
        """
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                # Verifica se o dispositivo é válido
                model_params = {}
                if self.device:
                    model_params["device"] = self.device

                # Adiciona outros parâmetros
                model_params.update(self.kwargs)

                # Carrega o modelo
                self._model = CrossEncoder(self.model_name, **model_params)

            except ImportError:
                raise RerankingError(
                    "A biblioteca sentence-transformers não está instalada. "
                    "Instale-a com: pip install sentence-transformers"
                )
            except Exception as e:
                raise RerankingError(
                    f"Erro ao carregar o modelo Cross-Encoder: {str(e)}"
                ) from e

        return self._model

    async def _compute_scores(
        self,
        query: str,
        documents: List[str],
        scores: Optional[List[float]] = None,
    ) -> List[float]:
        """Calcula scores de relevância usando o modelo Cross-Encoder.

        Args:
            query: A consulta
            documents: Lista de documentos para calcular scores
            scores: Scores iniciais opcionais (ignorados pelo Cross-Encoder)

        Returns:
            Lista de scores para cada documento

        Raises:
            RerankingError: Se ocorrer um erro ao calcular os scores
        """
        try:
            logger.debug(
                f"Calculando scores para {len(documents)} documentos com Cross-Encoder"
            )

            # Se não houver documentos, retorna uma lista vazia
            if not documents:
                return []

            # Carrega o modelo
            model = await self._load_model()

            # Prepara os pares query+document para o modelo
            sentence_pairs = [(query, doc) for doc in documents]

            # Para execução assíncrona, usamos um executor de thread para não bloquear
            import asyncio
            from concurrent.futures import ThreadPoolExecutor

            # Função para executar a inferência do modelo em um thread separado
            def predict_scores():
                return model.predict(
                    sentence_pairs, batch_size=self.batch_size, show_progress_bar=False
                )

            # Executa a inferência em um thread separado
            with ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                model_scores = await loop.run_in_executor(executor, predict_scores)

            # Converte os scores para uma lista de floats
            if isinstance(model_scores, np.ndarray):
                model_scores = model_scores.tolist()

            # Normaliza os scores se necessário
            if not isinstance(model_scores, list):
                model_scores = [float(score) for score in model_scores]

            # Se o modelo retornar scores entre -inf e +inf, normaliza para 0 a 1
            if model_scores and (min(model_scores) < 0 or max(model_scores) > 1):
                min_score = min(model_scores)
                max_score = max(model_scores)
                range_score = max_score - min_score if max_score > min_score else 1
                model_scores = [
                    (score - min_score) / range_score for score in model_scores
                ]

            return model_scores

        except Exception as e:
            raise RerankingError(
                f"Erro ao calcular scores com Cross-Encoder: {str(e)}"
            ) from e

    def __repr__(self) -> str:
        device_str = f", device='{self.device}'" if self.device else ""
        return f"CrossEncoderProvider(model='{self.model_name}', batch_size={self.batch_size}{device_str})"
