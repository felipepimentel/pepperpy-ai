#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testes de integração entre os sistemas de composição e intenção.

Este módulo contém testes que verificam a integração entre o sistema de
composição e o sistema de intenção, garantindo que eles funcionem corretamente
em conjunto.
"""

import asyncio
import os
import unittest
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from pepperpy.core.composition import Outputs, Processors, Sources, compose
from pepperpy.core.intent import (
    process_intent,
    recognize_intent,
    register_intent_handler,
)


class TestCompositionIntentIntegration(unittest.TestCase):
    """Testes de integração entre os sistemas de composição e intenção."""

    def setUp(self):
        """Configuração para os testes."""
        # Criar diretório para saída de testes
        os.makedirs("test_output", exist_ok=True)

        # Limpar manipuladores de intenção registrados
        self.original_handlers = {}

        # Configurar mocks
        self.mock_source = MagicMock()
        self.mock_processor = MagicMock()
        self.mock_output = MagicMock()

        # Configurar resultado do mock
        self.mock_output.output = AsyncMock(return_value="test_output/result.txt")

        # Patches para os componentes
        self.patches = [
            patch(
                "pepperpy.core.composition.Sources.web", return_value=self.mock_source
            ),
            patch(
                "pepperpy.core.composition.Processors.summarize",
                return_value=self.mock_processor,
            ),
            patch(
                "pepperpy.core.composition.Outputs.file", return_value=self.mock_output
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

        async def handle_summarize_intent(
            intent_data: Dict[str, Any],
        ) -> Dict[str, Any]:
            """Manipulador para a intenção de resumir conteúdo."""
            # Extrair parâmetros da intenção
            source_url = intent_data.get("source_url", "https://example.com")
            max_length = intent_data.get("max_length", 150)

            # Criar pipeline de composição
            pipeline = (
                compose("test_pipeline")
                .source(Sources.web(source_url))
                .process(Processors.summarize(max_length=max_length))
                .output(Outputs.file("test_output/summary.txt"))
            )

            # Executar o pipeline
            result = await pipeline.execute()

            return {
                "status": "success",
                "output_path": result,
                "message": f"Resumo gerado com sucesso em {result}",
            }

        # Registrar o manipulador
        register_intent_handler("summarize", handle_summarize_intent)

    @patch("pepperpy.core.intent.recognize_intent")
    async def test_intent_to_composition_flow(self, mock_recognize_intent):
        """Testa o fluxo de intenção para composição."""
        # Configurar o mock para reconhecimento de intenção
        mock_recognize_intent.return_value = {
            "intent": "summarize",
            "parameters": {"source_url": "https://test.example.com", "max_length": 100},
        }

        # Registrar manipulador de intenção
        await self._register_test_handler()

        # Processar um comando de usuário
        command = "Resumir o artigo em https://test.example.com em 100 palavras"
        intent = await recognize_intent(command)
        result = await process_intent(intent)

        # Verificar se o pipeline foi construído corretamente
        Sources.web.assert_called_once_with("https://test.example.com")
        Processors.summarize.assert_called_once_with(max_length=100)
        Outputs.file.assert_called_once_with("test_output/summary.txt")

        # Verificar se o pipeline foi executado
        self.mock_output.output.assert_called_once()

        # Verificar o resultado
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output_path"], "test_output/result.txt")

    def test_run_async(self):
        """Executa o teste assíncrono."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.test_intent_to_composition_flow())


if __name__ == "__main__":
    unittest.main()
