"""API pública para o módulo de intent.

Este módulo fornece uma API pública para o módulo de intent,
permitindo o acesso fácil a funcionalidades de reconhecimento,
classificação e processamento de intenções.
"""

import logging
from typing import Any, Dict, List, TypeVar

from pepperpy.core.intent.factory import (
    create_classifier,
    create_processor,
    create_recognizer,
)
from pepperpy.core.intent.types import Intent, IntentType

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


async def recognize_intent(
    text: str, recognizer_type: str = "text", **kwargs
) -> Intent:
    """Reconhece a intenção em um texto.

    Args:
        text: Texto a ser analisado.
        recognizer_type: Tipo de reconhecedor a ser usado.
        **kwargs: Parâmetros adicionais para o reconhecedor.

    Returns:
        A intenção reconhecida.

    Raises:
        ValueError: Se o tipo de reconhecedor não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    recognizer = create_recognizer(recognizer_type, **kwargs)
    return await recognizer.recognize(text)


async def process_intent(
    intent: Intent, processor_type: str = "command", **kwargs
) -> Any:
    """Processa uma intenção.

    Args:
        intent: Intenção a ser processada.
        processor_type: Tipo de processador a ser usado.
        **kwargs: Parâmetros adicionais para o processador.

    Returns:
        O resultado do processamento.

    Raises:
        ValueError: Se o tipo de processador não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    processor = create_processor(processor_type, **kwargs)
    return await processor.process(intent, kwargs.get("context", {}))


async def classify_intent(
    text: str, classifier_type: str = "rule", **kwargs
) -> List[Intent]:
    """Classifica um texto em intenções.

    Args:
        text: Texto a ser classificado.
        classifier_type: Tipo de classificador a ser usado.
        **kwargs: Parâmetros adicionais para o classificador.

    Returns:
        Lista de intenções classificadas, ordenadas por confiança.

    Raises:
        ValueError: Se o tipo de classificador não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    classifier = create_classifier(classifier_type, **kwargs)
    return await classifier.classify(text)


class IntentBuilder:
    """Construtor fluente para intenções.

    Esta classe permite a construção fluente de intenções,
    facilitando a criação de intenções personalizadas.
    """

    def __init__(self, name: str):
        """Inicializa o construtor de intenção.

        Args:
            name: Nome da intenção.
        """
        self.name = name
        self.intent_type = IntentType.UNKNOWN
        self.confidence = 0.0
        self.entities: Dict[str, Any] = {}
        self.raw_text = ""

    def with_type(self, intent_type: IntentType) -> "IntentBuilder":
        """Define o tipo da intenção.

        Args:
            intent_type: Tipo da intenção.

        Returns:
            O próprio construtor, para permitir encadeamento de métodos.
        """
        self.intent_type = intent_type
        return self

    def with_confidence(self, confidence: float) -> "IntentBuilder":
        """Define o nível de confiança da intenção.

        Args:
            confidence: Nível de confiança.

        Returns:
            O próprio construtor, para permitir encadeamento de métodos.
        """
        self.confidence = confidence
        return self

    def with_entity(self, name: str, value: Any) -> "IntentBuilder":
        """Adiciona uma entidade à intenção.

        Args:
            name: Nome da entidade.
            value: Valor da entidade.

        Returns:
            O próprio construtor, para permitir encadeamento de métodos.
        """
        self.entities[name] = value
        return self

    def with_text(self, text: str) -> "IntentBuilder":
        """Define o texto original da intenção.

        Args:
            text: Texto original.

        Returns:
            O próprio construtor, para permitir encadeamento de métodos.
        """
        self.raw_text = text
        return self

    def build(self) -> Intent:
        """Constrói a intenção.

        Returns:
            A intenção construída.
        """
        return Intent(
            intent_type=self.intent_type,
            name=self.name,
            confidence=self.confidence,
            entities=self.entities,
            raw_text=self.raw_text,
        )
