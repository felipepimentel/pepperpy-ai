#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de integração completa entre os sistemas de composição, intenção e templates.

Purpose:
    Demonstrar como os três sistemas podem ser usados em conjunto para
    criar uma solução completa, desde o reconhecimento de intenções até a execução
    de templates e pipelines de composição.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/integration/complete_flow.py
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, Optional


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
        if "notícias" in text.lower() or "news" in text.lower():
            intent = "news"
            confidence = 0.9
            params = {
                "source": "https://news.google.com/rss",
                "format": "text" if "texto" in text.lower() else "audio",
                "max_items": 3,
            }
        elif "resumir" in text.lower() or "summarize" in text.lower():
            intent = "summarize"
            confidence = 0.85
            params = {
                "text": text.replace("resumir", "").replace("summarize", "").strip(),
                "max_length": 100,
            }
        elif "traduzir" in text.lower() or "translate" in text.lower():
            intent = "translate"
            confidence = 0.8
            params = {
                "text": text.replace("traduzir", "").replace("translate", "").strip(),
                "target_language": "en"
                if "inglês" in text.lower() or "english" in text.lower()
                else "pt",
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
        if template_name == "news_summary":
            source_url = parameters.get("source_url", "https://news.google.com/rss")
            output_path = parameters.get("output_path", "outputs/news_summary.txt")
            max_items = parameters.get("max_items", 3)

            # Criar diretório de saída se não existir
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Simular geração de resumo
            with open(output_path, "w") as f:
                f.write(f"Resumo de notícias de {source_url}\n")
                f.write(
                    f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                for i in range(1, max_items + 1):
                    f.write(f"Notícia {i}: Título da notícia simulada {i}\n")
                    f.write(f"Resumo: Este é um resumo simulado da notícia {i}.\n\n")

            return {
                "status": "success",
                "output_path": output_path,
                "message": "Resumo de notícias gerado com sucesso",
            }
        else:
            return {
                "status": "error",
                "message": f"Template '{template_name}' não encontrado",
            }


# Definir um pipeline personalizado usando o sistema de composição
async def create_custom_pipeline(
    source_url: str,
    output_format: str = "text",
    max_items: int = 3,
    max_length: int = 150,
    voice: str = "pt",
) -> Dict[str, Any]:
    """Cria um pipeline personalizado para processamento de notícias.

    Args:
        source_url: URL da fonte de notícias
        output_format: Formato de saída (text, audio)
        max_items: Número máximo de itens
        max_length: Tamanho máximo do resumo
        voice: Voz a ser usada (código de idioma)

    Returns:
        Resultado do pipeline
    """
    print(f"Criando pipeline personalizado para {source_url}")
    print(
        f"Configuração: formato={output_format}, max_items={max_items}, max_length={max_length}"
    )

    # Criar diretório de saída
    os.makedirs("outputs", exist_ok=True)

    # Definir caminho de saída
    output_path = f"outputs/news_{'audio' if output_format == 'audio' else 'text'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if output_format == "audio":
        output_path += ".mp3"
    else:
        output_path += ".txt"

    # Simular execução de pipeline
    print(f"Buscando notícias de {source_url}")
    await asyncio.sleep(0.5)  # Simular tempo de busca

    print(f"Processando {max_items} notícias")
    await asyncio.sleep(0.5)  # Simular tempo de processamento

    print(f"Gerando saída em formato {output_format}")

    # Criar arquivo de saída simulado
    with open(output_path, "w") as f:
        f.write(f"Notícias de {source_url}\n")
        f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for i in range(1, max_items + 1):
            f.write(f"Notícia {i}: Título da notícia simulada {i}\n")
            f.write(f"Resumo: Este é um resumo simulado da notícia {i}.\n\n")

    return {
        "status": "success",
        "output_path": output_path,
        "format": output_format,
        "items_count": max_items,
    }


# Manipulador de intenção para notícias
async def handle_news_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de notícias.

    Args:
        intent_data: Dados da intenção
            - source: Fonte de notícias
            - format: Formato de saída
            - max_items: Número máximo de itens

    Returns:
        Resultado do processamento
    """
    source = intent_data.get("source", "https://news.google.com/rss")
    output_format = intent_data.get("format", "text")
    max_items = intent_data.get("max_items", 3)

    print(f"Processando intenção de notícias de '{source}'")

    # Usar o sistema de templates para gerar um resumo de notícias
    template_system = TemplateSystem()
    template_result = await template_system.execute_template(
        "news_summary",
        {
            "source_url": source,
            "output_path": f"outputs/news_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "max_items": max_items,
            "summary_length": 100,
        },
    )

    if template_result["status"] == "success":
        # Se o formato for áudio, usar o pipeline de composição para converter o texto em áudio
        if output_format == "audio":
            # Ler o conteúdo do arquivo de texto
            with open(template_result["output_path"], "r") as f:
                text_content = f.read()

            # Criar um pipeline para converter o texto em áudio
            audio_output_path = template_result["output_path"].replace(".txt", ".mp3")

            # Simular conversão para áudio
            with open(audio_output_path, "w") as f:
                f.write(
                    f"Simulação de arquivo de áudio para o texto: {text_content[:100]}..."
                )

            return {
                "status": "success",
                "message": "Notícias processadas e convertidas em áudio",
                "output_path": audio_output_path,
                "format": "audio",
            }
        else:
            return {
                "status": "success",
                "message": "Notícias processadas com sucesso",
                "output_path": template_result["output_path"],
                "format": "text",
            }
    else:
        return template_result


# Manipulador de intenção para resumo
async def handle_summarize_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de resumo.

    Args:
        intent_data: Dados da intenção
            - text: Texto a ser resumido
            - max_length: Tamanho máximo do resumo

    Returns:
        Resultado do processamento
    """
    text = intent_data.get("text", "")
    max_length = intent_data.get("max_length", 100)

    print(f"Processando intenção de resumo de texto com {len(text)} caracteres")
    print(f"Tamanho máximo: {max_length} caracteres")

    # Simular resumo
    summary = text[:max_length] + "..." if len(text) > max_length else text

    return {
        "status": "success",
        "message": "Texto resumido com sucesso",
        "summary": summary,
        "original_length": len(text),
        "summary_length": len(summary),
    }


# Manipulador de intenção para tradução
async def handle_translate_intent(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manipulador para a intenção de tradução.

    Args:
        intent_data: Dados da intenção
            - text: Texto a ser traduzido
            - target_language: Idioma alvo

    Returns:
        Resultado do processamento
    """
    text = intent_data.get("text", "")
    target_language = intent_data.get("target_language", "en")

    print(f"Processando intenção de tradução de texto com {len(text)} caracteres")
    print(f"Idioma alvo: {target_language}")

    # Simular tradução
    translation = f"[Tradução para {target_language}] {text}"

    return {
        "status": "success",
        "message": f"Texto traduzido com sucesso para {target_language}",
        "translation": translation,
        "source_language": "auto",
        "target_language": target_language,
    }


async def setup():
    """Configuração inicial do sistema."""
    # Criar sistema de intenção
    intent_system = IntentSystem()

    # Registrar manipuladores de intenção
    intent_system.register_intent_handler("news", handle_news_intent)
    intent_system.register_intent_handler("summarize", handle_summarize_intent)
    intent_system.register_intent_handler("translate", handle_translate_intent)

    return intent_system


async def process_user_command(
    command: str, intent_system: IntentSystem
) -> Optional[Dict[str, Any]]:
    """Processa um comando do usuário.

    Args:
        command: Comando do usuário
        intent_system: Sistema de intenção

    Returns:
        Resultado do processamento ou None se o comando for para sair
    """
    if command.lower() in ["sair", "exit", "quit"]:
        return None

    # Reconhecer intenção
    intent_data = await intent_system.recognize_intent(command)

    # Exibir intenção reconhecida
    print(f"Intenção reconhecida: {intent_data['intent']}")
    print(f"Confiança: {intent_data['confidence']:.2f}")
    print(f"Parâmetros: {intent_data['parameters']}")

    # Processar intenção
    if intent_data["confidence"] > 0.5:
        result = await intent_system.process_intent(intent_data)
        return result
    else:
        return {
            "status": "error",
            "message": "Não foi possível reconhecer a intenção com confiança suficiente",
        }


async def main():
    """Função principal."""
    print("=== Exemplo de Integração Completa do PepperPy ===")
    print("Este exemplo demonstra como integrar os sistemas de composição,")
    print("intenção e templates para criar uma solução completa.")

    # Configurar o sistema
    intent_system = await setup()

    # Exemplos de comandos
    commands = [
        "mostrar notícias de https://news.google.com/rss",
        "resumir este é um texto de exemplo que precisa ser resumido para demonstrar a funcionalidade de resumo do sistema",
        "traduzir hello world para português",
    ]

    # Processar comandos
    for command in commands:
        print(f"\nComando: '{command}'")

        # Processar comando
        result = await process_user_command(command, intent_system)

        # Exibir resultado
        if result:
            print(f"Status: {result['status']}")
            print(f"Mensagem: {result['message']}")

            # Exibir detalhes específicos do resultado
            if "output_path" in result:
                print(f"Arquivo de saída: {result['output_path']}")
            if "summary" in result:
                print(f"Resumo: {result['summary']}")
            if "translation" in result:
                print(f"Tradução: {result['translation']}")

        print("-" * 50)

    print("\n=== Demonstração Concluída ===")
    print("Este exemplo demonstrou como integrar os diferentes sistemas do PepperPy:")
    print("1. Sistema de Intenção: Para reconhecer comandos em linguagem natural")
    print("2. Sistema de Templates: Para executar fluxos pré-definidos")
    print("3. Sistema de Composição: Para criar pipelines personalizados")


if __name__ == "__main__":
    asyncio.run(main())
