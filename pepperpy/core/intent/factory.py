"""Factory para componentes de intent.

Este módulo fornece factory methods para criar componentes de intent,
como reconhecedores, classificadores e processadores.
"""

import logging
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


def create_recognizer(recognizer_type: str, **kwargs) -> Any:
    """Cria um reconhecedor de intenção com base no tipo especificado.

    Args:
        recognizer_type: Tipo de reconhecedor a ser criado (text, voice, etc).
        **kwargs: Parâmetros específicos para o tipo de reconhecedor.

    Returns:
        Uma instância de IntentRecognizer.

    Raises:
        ValueError: Se o tipo de reconhecedor não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    if recognizer_type == "text":
        model = kwargs.get("model", "default")
        threshold = kwargs.get("threshold", 0.5)

        try:
            from pepperpy.nlp.intent.text import TextIntentRecognizer

            return TextIntentRecognizer(model=model, threshold=threshold)
        except ImportError:
            logger.warning("Módulo TextIntentRecognizer não encontrado. Usando mock.")
            from pepperpy.core.intent.mocks import MockTextIntentRecognizer

            return MockTextIntentRecognizer(model=model, threshold=threshold)

    elif recognizer_type == "voice":
        model = kwargs.get("model", "default")
        language = kwargs.get("language", "en")

        try:
            from pepperpy.speech.intent import VoiceIntentRecognizer

            return VoiceIntentRecognizer(model=model, language=language)
        except ImportError:
            logger.warning("Módulo VoiceIntentRecognizer não encontrado. Usando mock.")
            from pepperpy.core.intent.mocks import MockVoiceIntentRecognizer

            return MockVoiceIntentRecognizer(model=model, language=language)

    else:
        raise ValueError(f"Tipo de reconhecedor não suportado: {recognizer_type}")


def create_processor(processor_type: str, **kwargs) -> Any:
    """Cria um processador de intenção com base no tipo especificado.

    Args:
        processor_type: Tipo de processador a ser criado (command, query, etc).
        **kwargs: Parâmetros específicos para o tipo de processador.

    Returns:
        Uma instância de IntentProcessor.

    Raises:
        ValueError: Se o tipo de processador não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    if processor_type == "command":
        handlers = kwargs.get("handlers", {})

        try:
            from pepperpy.nlp.intent.processors import CommandIntentProcessor

            return CommandIntentProcessor(handlers=handlers)
        except ImportError:
            logger.warning("Módulo CommandIntentProcessor não encontrado. Usando mock.")
            from pepperpy.core.intent.mocks import MockCommandIntentProcessor

            return MockCommandIntentProcessor(handlers=handlers)

    elif processor_type == "query":
        knowledge_base = kwargs.get("knowledge_base")

        if not knowledge_base:
            raise ValueError(
                "Knowledge base é obrigatório para processadores de consulta"
            )

        try:
            from pepperpy.nlp.intent.processors import QueryIntentProcessor

            return QueryIntentProcessor(knowledge_base=knowledge_base)
        except ImportError:
            logger.warning("Módulo QueryIntentProcessor não encontrado. Usando mock.")
            from pepperpy.core.intent.mocks import MockQueryIntentProcessor

            return MockQueryIntentProcessor(knowledge_base=knowledge_base)

    else:
        raise ValueError(f"Tipo de processador não suportado: {processor_type}")


def create_classifier(classifier_type: str, **kwargs) -> Any:
    """Cria um classificador de intenção com base no tipo especificado.

    Args:
        classifier_type: Tipo de classificador a ser criado (rule, ml, etc).
        **kwargs: Parâmetros específicos para o tipo de classificador.

    Returns:
        Uma instância de IntentClassifier.

    Raises:
        ValueError: Se o tipo de classificador não for suportado.
        ImportError: Se o módulo necessário não estiver disponível.
    """
    if classifier_type == "rule":
        rules = kwargs.get("rules", [])

        if not rules:
            raise ValueError(
                "Rules é obrigatório para classificadores baseados em regras"
            )

        try:
            from pepperpy.nlp.intent.classifiers import RuleBasedIntentClassifier

            return RuleBasedIntentClassifier(rules=rules)
        except ImportError:
            logger.warning(
                "Módulo RuleBasedIntentClassifier não encontrado. Usando mock."
            )
            from pepperpy.core.intent.mocks import MockRuleBasedIntentClassifier

            return MockRuleBasedIntentClassifier(rules=rules)

    elif classifier_type == "ml":
        model = kwargs.get("model", "default")
        threshold = kwargs.get("threshold", 0.5)

        try:
            from pepperpy.nlp.intent.classifiers import MLIntentClassifier

            return MLIntentClassifier(model=model, threshold=threshold)
        except ImportError:
            logger.warning("Módulo MLIntentClassifier não encontrado. Usando mock.")
            from pepperpy.core.intent.mocks import MockMLIntentClassifier

            return MockMLIntentClassifier(model=model, threshold=threshold)

    else:
        raise ValueError(f"Tipo de classificador não suportado: {classifier_type}")
