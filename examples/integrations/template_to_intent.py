#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração entre os sistemas de templates e intenção.

Purpose:
    Demonstrar como o sistema de intenção pode utilizar o sistema de templates
    para implementar a funcionalidade associada a uma intenção reconhecida.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/integration/template_to_intent.py
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict


# Simulação de sistema de intenção
class IntentSystem:
    """Sistema de intenção simulado para demonstração."""

    def __init__(self):
        """Inicializar sistema de intenção."""
        self.intent_handlers = {}

    def register_intent_handler(self, intent_name: str, handler_func: callable):
        """Registrar um manipulador de intenção.

        Args:
            intent_name: Nome da intenção
            handler_func: Função manipuladora
        """
        self.intent_handlers[intent_name] = handler_func
        print(f"Manipulador registrado para intenção '{intent_name}'")

    async def recognize_intent(self, text: str) -> Dict[str, Any]:
        """Reconhecer intenção a partir de texto.

        Args:
            text: Texto a ser analisado

        Returns:
            Informações sobre a intenção reconhecida
        """
        print(f"Reconhecendo intenção a partir do texto: '{text}'")

        # Simulação de reconhecimento de intenção
        if (
            "podcast" in text.lower()
            or "áudio" in text.lower()
            or "audio" in text.lower()
        ):
            intent = "podcast"
            confidence = 0.9

            # Extrair parâmetros
            source_url = "https://news.google.com/rss"
            for word in text.split():
                if word.startswith("http"):
                    source_url = word

            voice = "pt-BR"
            if "inglês" in text.lower() or "english" in text.lower():
                voice = "en-US"
            elif "espanhol" in text.lower() or "spanish" in text.lower():
                voice = "es-ES"

            max_items = 5
            for i, word in enumerate(text.split()):
                if (
                    word.isdigit()
                    and i > 0
                    and text.split()[i - 1] in ["itens", "items", "notícias", "news"]
                ):
                    max_items = int(word)

            params = {
                "source_url": source_url,
                "voice": voice,
                "max_items": max_items,
                "output_path": f"outputs/podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3",
            }
        else:
            intent = "unknown"
            confidence = 0.3
            params = {}

        return {
            "intent": intent,
            "confidence": confidence,
            "parameters": params,
        }

    async def process_intent(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processar uma intenção.

        Args:
            intent_data: Dados da intenção

        Returns:
            Resultado do processamento
        """
        intent_name = intent_data.get("intent", "unknown")
        print(f"Processando intenção: {intent_name}")

        if intent_name in self.intent_handlers:
            handler = self.intent_handlers[intent_name]
            return await handler(intent_data.get("parameters", {}))
        else:
            return {
                "status": "error",
                "message": f"Intenção '{intent_name}' não reconhecida",
            }


# Simulação de sistema de templates
class TemplateSystem:
    """Sistema de templates simulado para demonstração."""

    async def execute_template(
        self, template_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executar um template.

        Args:
            template_name: Nome do template
            parameters: Parâmetros para o template

        Returns:
            Resultado da execução
        """
        print(f"Executando template '{template_name}' com parâmetros: {parameters}")

        # Simulação de execução de template
        if template_name == "news_podcast":
            source_url = parameters.get("source_url", "https://news.google.com/rss")
            voice = parameters.get("voice", "pt-BR")
            max_items = parameters.get("max_items", 5)
            output_path = parameters.get("output_path", "outputs/podcast.mp3")

            # Criar diretório de saída se não existir
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Simular geração de podcast
            print(f"Buscando notícias de {source_url}")
            await asyncio.sleep(0.5)  # Simular tempo de busca

            print(f"Processando {max_items} notícias")
            await asyncio.sleep(0.5)  # Simular tempo de processamento

            print(f"Gerando podcast com voz '{voice}'")
            await asyncio.sleep(0.5)  # Simular tempo de geração

            # Criar arquivo simulado
            with open(output_path, "w") as f:
                f.write(f"Simulação de podcast com notícias de {source_url}\n")
                f.write(f"Voz: {voice}\n")
                f.write(
                    f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                for i in range(1, max_items + 1):
                    f.write(f"Notícia {i}: Título da notícia simulada {i}\n")

            return {
                "status": "success",
                "output_path": output_path,
                "message": "Podcast gerado com sucesso",
                "voice": voice,
                "items_count": max_items,
            }
        else:
            return {
                "status": "error",
                "message": f"Template '{template_name}' não encontrado",
            }


# Definir um manipulador de intenção que usa o sistema de templates
async def handle_podcast_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de criar um podcast.

    Este manipulador extrai parâmetros da intenção reconhecida e usa o sistema
    de templates para executar um template pré-configurado que gera um podcast
    de notícias.

    Args:
        intent_data: Dados da intenção reconhecida
            - source_url: URL da fonte de notícias
            - voice: Voz a ser usada (código de idioma)
            - max_items: Número máximo de itens
            - output_path: Caminho para salvar o resultado

    Returns:
        Resultado do processamento da intenção
    """
    # Extrair parâmetros da intenção
    source_url = intent_data.get("source_url", "https://news.google.com/rss")
    voice = intent_data.get("voice", "pt-BR")
    max_items = intent_data.get("max_items", 5)
    output_path = intent_data.get("output_path", "outputs/podcast.mp3")

    print(f"Processando intenção de podcast para '{source_url}'")
    print(f"Voz: {voice}")
    print(f"Máximo de itens: {max_items}")
    print(f"Caminho de saída: {output_path}")

    # Executar o template de podcast
    template_system = TemplateSystem()
    template_result = await template_system.execute_template(
        "news_podcast",
        {
            "source_url": source_url,
            "voice": voice,
            "max_items": max_items,
            "output_path": output_path,
        },
    )

    if template_result["status"] == "success":
        return {
            "status": "success",
            "message": "Podcast gerado com sucesso",
            "output_path": template_result["output_path"],
            "voice": voice,
            "source_url": source_url,
        }
    else:
        return template_result


async def setup():
    """Configuração inicial do sistema."""
    # Criar sistema de intenção
    intent_system = IntentSystem()

    # Registrar manipulador de intenção
    intent_system.register_intent_handler("podcast", handle_podcast_intent)

    return intent_system


async def demo_intent_to_template():
    """Demonstra a integração entre intenção e template."""
    print("\n=== Demonstração de Integração: Intenção → Template ===")

    # Configurar o sistema
    intent_system = await setup()

    # Exemplos de comandos
    commands = [
        "criar um podcast com as notícias de https://news.google.com/rss",
        "gerar áudio de notícias em inglês",
        "fazer um podcast com 3 notícias de tecnologia",
    ]

    # Processar cada comando
    for command in commands:
        print(f"\nComando: '{command}'")

        # Reconhecer intenção
        intent_data = await intent_system.recognize_intent(command)

        # Exibir intenção reconhecida
        print(f"Intenção reconhecida: {intent_data['intent']}")
        print(f"Confiança: {intent_data['confidence']:.2f}")
        print(f"Parâmetros: {intent_data['parameters']}")

        # Processar intenção
        if intent_data["confidence"] > 0.5:
            result = await intent_system.process_intent(intent_data)

            # Exibir resultado
            print(f"Status: {result['status']}")
            print(f"Mensagem: {result['message']}")
            print(f"Arquivo de saída: {result.get('output_path', '')}")
            print(f"Voz: {result.get('voice', '')}")
        else:
            print("Confiança insuficiente para processar a intenção")

        print("-" * 50)


async def main():
    """Função principal."""
    print("=== Exemplo de Integração: Intenção → Template ===")
    print("Este exemplo demonstra como o sistema de intenção pode utilizar")
    print("o sistema de templates para implementar a funcionalidade associada")
    print("a uma intenção reconhecida.")

    await demo_intent_to_template()

    print("\n=== Conceitos Demonstrados ===")
    print("1. Reconhecimento de intenção a partir de texto")
    print("2. Extração de parâmetros da intenção")
    print("3. Uso do sistema de templates para implementar a funcionalidade")
    print("4. Integração entre os sistemas de intenção e templates")


if __name__ == "__main__":
    asyncio.run(main())
