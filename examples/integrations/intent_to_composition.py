#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração entre os sistemas de intenção e composição.

Purpose:
    Demonstrar como o sistema de intenção pode utilizar o sistema de composição
    para implementar a funcionalidade associada a uma intenção reconhecida.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/integration/intent_to_composition.py
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
        if "resumir" in text.lower() or "summarize" in text.lower():
            intent = "summarize"
            confidence = 0.9

            # Extrair parâmetros
            source_url = "https://example.com/article"
            for word in text.split():
                if word.startswith("http"):
                    source_url = word

            max_length = 150
            for i, word in enumerate(text.split()):
                if (
                    word.isdigit()
                    and i > 0
                    and text.split()[i - 1]
                    in ["tamanho", "length", "palavras", "words"]
                ):
                    max_length = int(word)

            params = {
                "source_url": source_url,
                "max_length": max_length,
                "output_path": f"outputs/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
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


# Definir um manipulador de intenção que usa o sistema de composição
async def handle_summarize_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de resumir conteúdo.

    Este manipulador extrai parâmetros da intenção reconhecida e usa o sistema
    de composição para criar um pipeline que busca o conteúdo, o resume e salva
    o resultado em um arquivo.

    Args:
        intent_data: Dados da intenção reconhecida
            - source_url: URL da fonte de conteúdo
            - max_length: Tamanho máximo do resumo
            - output_path: Caminho para salvar o resultado

    Returns:
        Resultado do processamento da intenção
    """
    # Extrair parâmetros da intenção
    source_url = intent_data.get("source_url", "https://example.com/article")
    max_length = intent_data.get("max_length", 150)
    output_path = intent_data.get("output_path", "outputs/summary.txt")

    print(f"Processando intenção de resumo para '{source_url}'")
    print(f"Tamanho máximo: {max_length} palavras")
    print(f"Caminho de saída: {output_path}")

    # Criar diretório de saída se não existir
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Simular busca de conteúdo
    print(f"Buscando conteúdo de {source_url}")
    await asyncio.sleep(0.5)  # Simular tempo de busca

    # Conteúdo simulado
    content = f"""Este é um artigo simulado de {source_url}.
    
    O artigo contém informações sobre um tópico interessante que será resumido.
    
    Este é um parágrafo adicional com mais detalhes sobre o tópico.
    
    E este é o parágrafo final com a conclusão do artigo.
    """

    # Simular resumo
    print(f"Resumindo conteúdo (máximo de {max_length} palavras)")
    await asyncio.sleep(0.5)  # Simular tempo de processamento

    # Resumo simulado
    summary = f"Este é um resumo simulado do artigo de {source_url}. O resumo foi limitado a {max_length} palavras conforme solicitado."

    # Salvar resumo
    with open(output_path, "w") as f:
        f.write(summary)

    print(f"Resumo salvo em {output_path}")

    return {
        "status": "success",
        "message": "Conteúdo resumido com sucesso",
        "output_path": output_path,
        "summary": summary,
        "source_url": source_url,
    }


async def setup():
    """Configuração inicial do sistema."""
    # Criar sistema de intenção
    intent_system = IntentSystem()

    # Registrar manipulador de intenção
    intent_system.register_intent_handler("summarize", handle_summarize_intent)

    return intent_system


async def demo_intent_to_composition():
    """Demonstra a integração entre intenção e composição."""
    print("\n=== Demonstração de Integração: Intenção → Composição ===")

    # Configurar o sistema
    intent_system = await setup()

    # Exemplos de comandos
    commands = [
        "resumir o artigo em https://example.com/article",
        "summarize this content with a length of 100 words",
        "resumir o texto do site https://example.org/blog/post com tamanho 50",
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
            print(f"Resumo: {result.get('summary', '')[:50]}...")
            print(f"Arquivo de saída: {result.get('output_path', '')}")
        else:
            print("Confiança insuficiente para processar a intenção")

        print("-" * 50)


async def main():
    """Função principal."""
    print("=== Exemplo de Integração: Intenção → Composição ===")
    print("Este exemplo demonstra como o sistema de intenção pode utilizar")
    print("o sistema de composição para implementar a funcionalidade associada")
    print("a uma intenção reconhecida.")

    await demo_intent_to_composition()

    print("\n=== Conceitos Demonstrados ===")
    print("1. Reconhecimento de intenção a partir de texto")
    print("2. Extração de parâmetros da intenção")
    print("3. Uso do sistema de composição para implementar a funcionalidade")
    print("4. Integração entre os sistemas de intenção e composição")


if __name__ == "__main__":
    asyncio.run(main())
