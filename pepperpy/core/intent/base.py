"""Classes base para o domínio de intent.

Este módulo define as classes base para componentes de intent,
incluindo reconhecedores, classificadores e processadores.
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pepperpy.core.intent.types import (
    ClassificationError,
    Intent,
    ProcessingError,
    RecognitionError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Tipo de entrada
U = TypeVar("U")  # Tipo de saída


class BaseIntentRecognizer(Generic[T]):
    """Implementação base para reconhecedores de intenção.

    Esta classe fornece uma implementação base para reconhecedores de intenção,
    com suporte para logging e tratamento de erros.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Inicializa o reconhecedor de intenção.

        Args:
            name: Nome do reconhecedor.
            config: Configuração do reconhecedor.
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

    async def recognize(self, input_data: T) -> Intent:
        """Reconhece a intenção na entrada.

        Args:
            input_data: Dados de entrada (texto, áudio, etc).

        Returns:
            A intenção reconhecida.

        Raises:
            RecognitionError: Se ocorrer um erro durante o reconhecimento.
        """
        try:
            self.logger.debug(f"Reconhecendo intenção para: {input_data}")
            intent = await self._recognize_intent(input_data)
            self.logger.info(f"Intenção reconhecida: {intent}")
            return intent
        except Exception as e:
            self.logger.error(f"Erro ao reconhecer intenção: {e}")
            raise RecognitionError(f"Erro ao reconhecer intenção: {e}") from e

    @abstractmethod
    async def _recognize_intent(self, input_data: T) -> Intent:
        """Implementação específica do reconhecimento de intenção.

        Args:
            input_data: Dados de entrada (texto, áudio, etc).

        Returns:
            A intenção reconhecida.

        Raises:
            RecognitionError: Se ocorrer um erro durante o reconhecimento.
        """
        pass


class BaseIntentProcessor(Generic[T, U]):
    """Implementação base para processadores de intenção.

    Esta classe fornece uma implementação base para processadores de intenção,
    com suporte para logging e tratamento de erros.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Inicializa o processador de intenção.

        Args:
            name: Nome do processador.
            config: Configuração do processador.
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

    async def process(self, intent: Intent, context: Dict[str, Any]) -> U:
        """Processa a intenção.

        Args:
            intent: A intenção a ser processada.
            context: Contexto adicional para o processamento.

        Returns:
            O resultado do processamento.

        Raises:
            ProcessingError: Se ocorrer um erro durante o processamento.
        """
        try:
            self.logger.debug(f"Processando intenção: {intent}")
            result = await self._process_intent(intent, context)
            self.logger.info(f"Intenção processada: {intent}")
            return result
        except Exception as e:
            self.logger.error(f"Erro ao processar intenção: {e}")
            raise ProcessingError(f"Erro ao processar intenção: {e}") from e

    @abstractmethod
    async def _process_intent(self, intent: Intent, context: Dict[str, Any]) -> U:
        """Implementação específica do processamento de intenção.

        Args:
            intent: A intenção a ser processada.
            context: Contexto adicional para o processamento.

        Returns:
            O resultado do processamento.

        Raises:
            ProcessingError: Se ocorrer um erro durante o processamento.
        """
        pass


class BaseIntentClassifier:
    """Implementação base para classificadores de intenção.

    Esta classe fornece uma implementação base para classificadores de intenção,
    com suporte para logging e tratamento de erros.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Inicializa o classificador de intenção.

        Args:
            name: Nome do classificador.
            config: Configuração do classificador.
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

    async def classify(self, text: str) -> List[Intent]:
        """Classifica o texto em intenções.

        Args:
            text: Texto a ser classificado.

        Returns:
            Lista de intenções classificadas, ordenadas por confiança.

        Raises:
            ClassificationError: Se ocorrer um erro durante a classificação.
        """
        try:
            self.logger.debug(f"Classificando texto: {text}")
            intents = await self._classify_text(text)
            self.logger.info(f"Texto classificado com {len(intents)} intenções")
            return intents
        except Exception as e:
            self.logger.error(f"Erro ao classificar texto: {e}")
            raise ClassificationError(f"Erro ao classificar texto: {e}") from e

    @abstractmethod
    async def _classify_text(self, text: str) -> List[Intent]:
        """Implementação específica da classificação de texto.

        Args:
            text: Texto a ser classificado.

        Returns:
            Lista de intenções classificadas, ordenadas por confiança.

        Raises:
            ClassificationError: Se ocorrer um erro durante a classificação.
        """
        pass
