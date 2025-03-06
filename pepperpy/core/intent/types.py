"""Definições de tipos para o módulo de intent.

Este módulo define as interfaces e tipos para os componentes de intent,
incluindo reconhecimento, classificação e processamento de intenções.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, List, TypeVar

# Definição de tipos genéricos para entrada e saída de componentes
T = TypeVar("T")  # Tipo de entrada
U = TypeVar("U")  # Tipo de saída


class IntentType(Enum):
    """Tipos de intenções reconhecidas pelo sistema."""

    QUERY = "query"
    COMMAND = "command"
    INFORMATION = "information"
    UNKNOWN = "unknown"


class Intent:
    """Representação de uma intenção reconhecida.

    Attributes:
        type: Tipo da intenção.
        name: Nome da intenção.
        confidence: Nível de confiança na classificação.
        entities: Entidades extraídas da intenção.
        raw_text: Texto original da intenção.
    """

    def __init__(
        self,
        intent_type: IntentType,
        name: str,
        confidence: float,
        entities: Dict[str, Any],
        raw_text: str,
    ):
        """Inicializa uma nova intenção.

        Args:
            intent_type: Tipo da intenção.
            name: Nome da intenção.
            confidence: Nível de confiança na classificação.
            entities: Entidades extraídas da intenção.
            raw_text: Texto original da intenção.
        """
        self.type = intent_type
        self.name = name
        self.confidence = confidence
        self.entities = entities
        self.raw_text = raw_text

    def __str__(self) -> str:
        """Retorna uma representação em string da intenção.

        Returns:
            Representação em string da intenção.
        """
        return (
            f"Intent({self.type.value}:{self.name}, confidence={self.confidence:.2f})"
        )


class IntentRecognizer(Generic[T], ABC):
    """Interface base para reconhecedores de intenção.

    Os reconhecedores de intenção são responsáveis por identificar a intenção
    em uma entrada de usuário.
    """

    @abstractmethod
    async def recognize(self, input_data: T) -> Intent:
        """Reconhece a intenção na entrada.

        Args:
            input_data: Dados de entrada (texto, áudio, etc).

        Returns:
            A intenção reconhecida.

        Raises:
            RecognitionError: Se ocorrer um erro durante o reconhecimento.
        """
        pass


class IntentProcessor(Generic[T, U], ABC):
    """Interface base para processadores de intenção.

    Os processadores de intenção são responsáveis por executar ações
    com base na intenção reconhecida.
    """

    @abstractmethod
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
        pass


class IntentClassifier(ABC):
    """Interface base para classificadores de intenção.

    Os classificadores de intenção são responsáveis por classificar
    a intenção em categorias predefinidas.
    """

    @abstractmethod
    async def classify(self, text: str) -> List[Intent]:
        """Classifica o texto em intenções.

        Args:
            text: Texto a ser classificado.

        Returns:
            Lista de intenções classificadas, ordenadas por confiança.

        Raises:
            ClassificationError: Se ocorrer um erro durante a classificação.
        """
        pass


# Erros específicos
class RecognitionError(Exception):
    """Erro lançado quando ocorre um problema ao reconhecer uma intenção."""

    pass


class ProcessingError(Exception):
    """Erro lançado quando ocorre um problema ao processar uma intenção."""

    pass


class ClassificationError(Exception):
    """Erro lançado quando ocorre um problema ao classificar uma intenção."""

    pass
