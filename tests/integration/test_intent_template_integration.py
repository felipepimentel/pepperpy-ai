#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testes de integração entre os sistemas de intenção e templates.

Este módulo contém testes que verificam a integração entre o sistema de
intenção e o sistema de templates, garantindo que eles funcionem corretamente
em conjunto.
"""

import asyncio
import unittest
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from pepperpy.core.intent import (
    process_intent,
    recognize_intent,
    register_intent_handler,
)
from pepperpy.workflows.templates.public import execute_template
from pepperpy.workflows.types import WorkflowResult


class TestIntentTemplateIntegration(unittest.TestCase):
    """Testes de integração entre os sistemas de intenção e templates."""

    def setUp(self):
        """Configuração para os testes."""
        # Configurar mocks
        self.mock_execute_template = AsyncMock()

        # Configurar resultado do mock
        mock_result = MagicMock(spec=WorkflowResult)
        mock_result.status = "success"
        mock_result.result = {"output_path": "test_output/podcast.mp3"}
        self.mock_execute_template.return_value = mock_result

        # Patches
        self.patches = [
            patch(
                "pepperpy.workflows.templates.public.execute_template",
                self.mock_execute_template,
            ),
        ]

        # Aplicar patches
        for p in self.patches:
            p.start()

    def tearDown(self):
        """Limpeza após os testes."""
        # Remover patches
        for p in self.patches:
            p.stop()

    async def _register_test_handler(self):
        """Registra um manipulador de intenção de teste."""

        async def handle_podcast_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
            """Manipulador para a intenção de criar um podcast."""
            # Mapear parâmetros da intenção para parâmetros do template
            template_params = {
                "source_url": intent_data.get("source_url", "https://example.com"),
                "output_path": intent_data.get(
                    "output_path", "test_output/podcast.mp3"
                ),
                "voice": intent_data.get("voice", "pt"),
                "max_articles": intent_data.get("max_items", 3),
                "summary_length": intent_data.get("max_length", 150),
            }

            # Executar o template
            result = await execute_template("news_podcast", template_params)

            return {
                "status": result.status,
                "output_path": result.result.get("output_path"),
                "message": f"Podcast gerado com sucesso em {result.result.get('output_path')}",
            }

        # Registrar o manipulador
        register_intent_handler("create_podcast", handle_podcast_intent)

    @patch("pepperpy.core.intent.recognize_intent")
    async def test_intent_to_template_flow(self, mock_recognize_intent):
        """Testa o fluxo de intenção para template."""
        # Configurar o mock para reconhecimento de intenção
        mock_recognize_intent.return_value = {
            "intent": "create_podcast",
            "parameters": {
                "source_url": "https://test.example.com",
                "voice": "en",
                "max_items": 5,
            },
        }

        # Registrar manipulador de intenção
        await self._register_test_handler()

        # Processar um comando de usuário
        command = "Criar um podcast em inglês com as 5 principais notícias de https://test.example.com"
        intent = await recognize_intent(command)
        result = await process_intent(intent)

        # Verificar se o template foi executado com os parâmetros corretos
        self.mock_execute_template.assert_called_once()
        call_args = self.mock_execute_template.call_args[0]
        self.assertEqual(call_args[0], "news_podcast")

        template_params = call_args[1]
        self.assertEqual(template_params["source_url"], "https://test.example.com")
        self.assertEqual(template_params["voice"], "en")
        self.assertEqual(template_params["max_articles"], 5)

        # Verificar o resultado
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output_path"], "test_output/podcast.mp3")

    def test_run_async(self):
        """Executa o teste assíncrono."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.test_intent_to_template_flow())


if __name__ == "__main__":
    unittest.main()
