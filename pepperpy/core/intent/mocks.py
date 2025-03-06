"""Mocks para componentes de intent.

Este módulo fornece implementações mock para componentes de intent,
úteis para testes e desenvolvimento.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from pepperpy.core.intent.base import (
    BaseIntentClassifier,
    BaseIntentProcessor,
    BaseIntentRecognizer,
)
from pepperpy.core.intent.types import Intent, IntentType

logger = logging.getLogger(__name__)


class MockTextIntentRecognizer(BaseIntentRecognizer[str]):
    """Mock para reconhecedor de intenção baseado em texto."""

    def __init__(self, model: str = "default", threshold: float = 0.5):
        """Inicializa o reconhecedor mock.

        Args:
            model: Modelo a ser usado (ignorado no mock).
            threshold: Limiar de confiança (ignorado no mock).
        """
        super().__init__(
            name="mock_text_recognizer", config={"model": model, "threshold": threshold}
        )

    async def _recognize_intent(self, input_data: str) -> Intent:
        """Implementação mock do reconhecimento de intenção.

        Args:
            input_data: Texto a ser analisado.

        Returns:
            Uma intenção mock.
        """
        logger.info(f"Mock reconhecendo intenção para texto: {input_data}")

        # Lógica mock simples baseada em palavras-chave
        if "ajuda" in input_data.lower() or "help" in input_data.lower():
            return Intent(
                intent_type=IntentType.QUERY,
                name="help",
                confidence=0.9,
                entities={},
                raw_text=input_data,
            )
        elif "buscar" in input_data.lower() or "search" in input_data.lower():
            return Intent(
                intent_type=IntentType.COMMAND,
                name="search",
                confidence=0.8,
                entities={
                    "query": input_data.split("buscar ")[-1]
                    if "buscar " in input_data
                    else input_data.split("search ")[-1]
                },
                raw_text=input_data,
            )
        else:
            return Intent(
                intent_type=IntentType.INFORMATION,
                name="unknown",
                confidence=0.5,
                entities={"text": input_data},
                raw_text=input_data,
            )


class MockVoiceIntentRecognizer(BaseIntentRecognizer[bytes]):
    """Mock para reconhecedor de intenção baseado em voz."""

    def __init__(self, model: str = "default", language: str = "en"):
        """Inicializa o reconhecedor mock.

        Args:
            model: Modelo a ser usado (ignorado no mock).
            language: Idioma a ser usado (ignorado no mock).
        """
        super().__init__(
            name="mock_voice_recognizer", config={"model": model, "language": language}
        )

    async def _recognize_intent(self, input_data: bytes) -> Intent:
        """Implementação mock do reconhecimento de intenção.

        Args:
            input_data: Dados de áudio a serem analisados.

        Returns:
            Uma intenção mock.
        """
        logger.info(f"Mock reconhecendo intenção para áudio de {len(input_data)} bytes")

        # Simulação de reconhecimento de voz
        return Intent(
            intent_type=IntentType.COMMAND,
            name="voice_command",
            confidence=0.7,
            entities={"audio_length": len(input_data)},
            raw_text="[Áudio transcrito]",
        )


class MockCommandIntentProcessor(BaseIntentProcessor[Intent, Dict[str, Any]]):
    """Mock para processador de intenção de comando."""

    def __init__(self, handlers: Optional[Dict[str, Any]] = None):
        """Inicializa o processador mock.

        Args:
            handlers: Manipuladores de comando (ignorados no mock).
        """
        super().__init__(
            name="mock_command_processor", config={"handlers": handlers or {}}
        )

    async def _process_intent(
        self, intent: Intent, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implementação mock do processamento de intenção.

        Args:
            intent: Intenção a ser processada.
            context: Contexto adicional para o processamento.

        Returns:
            Resultado do processamento.
        """
        logger.info(f"Mock processando intenção de comando: {intent}")

        if intent.type == IntentType.COMMAND:
            return {
                "success": True,
                "command": intent.name,
                "result": f"Comando '{intent.name}' executado com sucesso",
                "entities": intent.entities,
            }
        else:
            return {
                "success": False,
                "error": "Não é um comando",
                "intent": intent.name,
            }


class MockQueryIntentProcessor(BaseIntentProcessor[Intent, Dict[str, Any]]):
    """Mock para processador de intenção de consulta."""

    def __init__(self, knowledge_base: Any):
        """Inicializa o processador mock.

        Args:
            knowledge_base: Base de conhecimento (ignorada no mock).
        """
        super().__init__(
            name="mock_query_processor", config={"knowledge_base": knowledge_base}
        )

    async def _process_intent(
        self, intent: Intent, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Implementação mock do processamento de intenção.

        Args:
            intent: Intenção a ser processada.
            context: Contexto adicional para o processamento.

        Returns:
            Resultado do processamento.
        """
        logger.info(f"Mock processando intenção de consulta: {intent}")

        if intent.type == IntentType.QUERY:
            return {
                "success": True,
                "query": intent.name,
                "answer": f"Resposta para a consulta '{intent.name}'",
                "confidence": 0.8,
            }
        else:
            return {
                "success": False,
                "error": "Não é uma consulta",
                "intent": intent.name,
            }


class MockRuleBasedIntentClassifier(BaseIntentClassifier):
    """Mock para classificador de intenção baseado em regras."""

    def __init__(self, rules: List[Dict[str, Any]]):
        """Inicializa o classificador mock.

        Args:
            rules: Regras de classificação (ignoradas no mock).
        """
        super().__init__(name="mock_rule_classifier", config={"rules": rules})

    async def _classify_text(self, text: str) -> List[Intent]:
        """Implementação mock da classificação de texto.

        Args:
            text: Texto a ser classificado.

        Returns:
            Lista de intenções classificadas.
        """
        logger.info(f"Mock classificando texto: {text}")

        # Simulação de classificação baseada em palavras-chave
        intents = []

        if "ajuda" in text.lower() or "help" in text.lower():
            intents.append(
                Intent(
                    intent_type=IntentType.QUERY,
                    name="help",
                    confidence=0.9,
                    entities={},
                    raw_text=text,
                )
            )

        if "buscar" in text.lower() or "search" in text.lower():
            intents.append(
                Intent(
                    intent_type=IntentType.COMMAND,
                    name="search",
                    confidence=0.8,
                    entities={
                        "query": text.split("buscar ")[-1]
                        if "buscar " in text
                        else text.split("search ")[-1]
                    },
                    raw_text=text,
                )
            )

        # Sempre adicionar uma intenção genérica com confiança baixa
        intents.append(
            Intent(
                intent_type=IntentType.INFORMATION,
                name="generic",
                confidence=0.3,
                entities={"text": text},
                raw_text=text,
            )
        )

        # Ordenar por confiança
        intents.sort(key=lambda x: x.confidence, reverse=True)

        return intents


class MockMLIntentClassifier(BaseIntentClassifier):
    """Mock para classificador de intenção baseado em machine learning."""

    def __init__(self, model: str = "default", threshold: float = 0.5):
        """Inicializa o classificador mock.

        Args:
            model: Modelo a ser usado (ignorado no mock).
            threshold: Limiar de confiança (ignorado no mock).
        """
        super().__init__(
            name="mock_ml_classifier", config={"model": model, "threshold": threshold}
        )

    async def _classify_text(self, text: str) -> List[Intent]:
        """Implementação mock da classificação de texto.

        Args:
            text: Texto a ser classificado.

        Returns:
            Lista de intenções classificadas.
        """
        logger.info(f"Mock classificando texto com ML: {text}")

        # Simulação de classificação ML com intenções aleatórias
        intents = []

        # Lista de possíveis intenções para simulação
        possible_intents = [
            ("greeting", IntentType.INFORMATION, 0.7 + random.random() * 0.3),
            ("farewell", IntentType.INFORMATION, 0.6 + random.random() * 0.3),
            ("search", IntentType.COMMAND, 0.5 + random.random() * 0.3),
            ("help", IntentType.QUERY, 0.4 + random.random() * 0.3),
            ("feedback", IntentType.INFORMATION, 0.3 + random.random() * 0.3),
        ]

        # Selecionar 3 intenções aleatórias
        selected_intents = random.sample(
            possible_intents, min(3, len(possible_intents))
        )

        for name, intent_type, confidence in selected_intents:
            intents.append(
                Intent(
                    intent_type=intent_type,
                    name=name,
                    confidence=confidence,
                    entities={"text": text},
                    raw_text=text,
                )
            )

        # Ordenar por confiança
        intents.sort(key=lambda x: x.confidence, reverse=True)

        return intents
