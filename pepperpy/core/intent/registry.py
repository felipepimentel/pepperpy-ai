"""Registro de componentes de intent.

Este módulo fornece um registro centralizado para componentes de intent,
permitindo o acesso a componentes por nome.
"""

import logging
from typing import Dict, List, Type, TypeVar

from pepperpy.core.intent.types import (
    IntentClassifier,
    IntentProcessor,
    IntentRecognizer,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


class ComponentNotFoundError(Exception):
    """Erro lançado quando um componente não é encontrado no registro."""

    pass


class IntentRegistry:
    """Registro centralizado para componentes de intent.

    Esta classe fornece um registro centralizado para componentes de intent,
    permitindo o acesso a componentes por nome.
    """

    _recognizers: Dict[str, Type[IntentRecognizer]] = {}
    _processors: Dict[str, Type[IntentProcessor]] = {}
    _classifiers: Dict[str, Type[IntentClassifier]] = {}

    @classmethod
    def register_recognizer(
        cls, name: str, recognizer_class: Type[IntentRecognizer]
    ) -> None:
        """Registra um reconhecedor de intenção.

        Args:
            name: Nome do reconhecedor.
            recognizer_class: Classe do reconhecedor.
        """
        cls._recognizers[name] = recognizer_class
        logger.info(f"Reconhecedor de intenção registrado: {name}")

    @classmethod
    def register_processor(
        cls, name: str, processor_class: Type[IntentProcessor]
    ) -> None:
        """Registra um processador de intenção.

        Args:
            name: Nome do processador.
            processor_class: Classe do processador.
        """
        cls._processors[name] = processor_class
        logger.info(f"Processador de intenção registrado: {name}")

    @classmethod
    def register_classifier(
        cls, name: str, classifier_class: Type[IntentClassifier]
    ) -> None:
        """Registra um classificador de intenção.

        Args:
            name: Nome do classificador.
            classifier_class: Classe do classificador.
        """
        cls._classifiers[name] = classifier_class
        logger.info(f"Classificador de intenção registrado: {name}")

    @classmethod
    def get_recognizer(cls, name: str) -> Type[IntentRecognizer]:
        """Obtém um reconhecedor de intenção pelo nome.

        Args:
            name: Nome do reconhecedor.

        Returns:
            Classe do reconhecedor.

        Raises:
            ComponentNotFoundError: Se o reconhecedor não for encontrado.
        """
        if name not in cls._recognizers:
            raise ComponentNotFoundError(
                f"Reconhecedor de intenção não encontrado: {name}"
            )
        return cls._recognizers[name]

    @classmethod
    def get_processor(cls, name: str) -> Type[IntentProcessor]:
        """Obtém um processador de intenção pelo nome.

        Args:
            name: Nome do processador.

        Returns:
            Classe do processador.

        Raises:
            ComponentNotFoundError: Se o processador não for encontrado.
        """
        if name not in cls._processors:
            raise ComponentNotFoundError(
                f"Processador de intenção não encontrado: {name}"
            )
        return cls._processors[name]

    @classmethod
    def get_classifier(cls, name: str) -> Type[IntentClassifier]:
        """Obtém um classificador de intenção pelo nome.

        Args:
            name: Nome do classificador.

        Returns:
            Classe do classificador.

        Raises:
            ComponentNotFoundError: Se o classificador não for encontrado.
        """
        if name not in cls._classifiers:
            raise ComponentNotFoundError(
                f"Classificador de intenção não encontrado: {name}"
            )
        return cls._classifiers[name]

    @classmethod
    def list_recognizers(cls) -> List[str]:
        """Lista os nomes dos reconhecedores registrados.

        Returns:
            Lista de nomes de reconhecedores.
        """
        return list(cls._recognizers.keys())

    @classmethod
    def list_processors(cls) -> List[str]:
        """Lista os nomes dos processadores registrados.

        Returns:
            Lista de nomes de processadores.
        """
        return list(cls._processors.keys())

    @classmethod
    def list_classifiers(cls) -> List[str]:
        """Lista os nomes dos classificadores registrados.

        Returns:
            Lista de nomes de classificadores.
        """
        return list(cls._classifiers.keys())
