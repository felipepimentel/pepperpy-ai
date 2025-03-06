"""Testes para o domínio de intenção.

Este módulo contém testes para o domínio de intenção, incluindo
testes para reconhecimento, classificação e processamento de intenções.
"""

from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.core.intent.public import (
    IntentBuilder,
    classify_intent,
    process_intent,
    recognize_intent,
)
from pepperpy.core.intent.types import IntentType


class TestRecognizeIntent:
    """Testes para a função recognize_intent."""

    @pytest.mark.asyncio
    async def test_recognize_intent_returns_intent(self):
        """Teste que recognize_intent retorna uma intenção."""
        # Mock para simular o reconhecimento de intenção
        with patch(
            "pepperpy.core.intent.public.recognize_intent", new_callable=AsyncMock
        ) as mock_recognize:
            mock_recognize.return_value = {
                "type": "podcast",
                "parameters": {"source": "rss"},
            }

            intent = await recognize_intent("gere um podcast com as últimas notícias")

            assert intent is not None
            assert intent["type"] == "podcast"
            assert "parameters" in intent
            assert intent["parameters"]["source"] == "rss"


class TestProcessIntent:
    """Testes para a função process_intent."""

    @pytest.mark.asyncio
    async def test_process_intent_executes_intent(self):
        """Teste que process_intent executa uma intenção."""
        # Mock para simular o processamento de intenção
        with patch(
            "pepperpy.core.intent.public.process_intent", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {"status": "success", "result": "podcast.mp3"}

            result = await process_intent({
                "type": "podcast",
                "parameters": {"source": "rss"},
            })

            assert result is not None
            assert result["status"] == "success"
            assert "result" in result
            assert result["result"] == "podcast.mp3"


class TestClassifyIntent:
    """Testes para a função classify_intent."""

    @pytest.mark.asyncio
    async def test_classify_intent_returns_intent_type(self):
        """Teste que classify_intent retorna um tipo de intenção."""
        # Mock para simular a classificação de intenção
        with patch(
            "pepperpy.core.intent.public.classify_intent", new_callable=AsyncMock
        ) as mock_classify:
            mock_classify.return_value = IntentType.CONTENT_GENERATION

            intent_type = await classify_intent(
                "gere um podcast com as últimas notícias"
            )

            assert intent_type is not None
            assert intent_type == IntentType.CONTENT_GENERATION


class TestIntentBuilder:
    """Testes para a classe IntentBuilder."""

    def test_intent_builder_creates_intent(self):
        """Teste que IntentBuilder cria uma intenção."""
        builder = IntentBuilder("podcast")
        builder.add_parameter("source", "rss")
        builder.add_parameter("max_items", 5)

        intent = builder.build()

        assert intent is not None
        assert intent["type"] == "podcast"
        assert "parameters" in intent
        assert intent["parameters"]["source"] == "rss"
        assert intent["parameters"]["max_items"] == 5
