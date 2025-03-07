#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Exemplo de tradutor multilíngue usando PepperPy.

Purpose:
    Demonstrar como criar um sistema de tradução multilíngue que pode
    traduzir textos entre vários idiomas, utilizando o framework PepperPy
    para orquestrar o fluxo de processamento.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install pepperpy

    2. Run the example:
       python examples/text_processing/multilingual_translator.py
"""

import asyncio
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

from pepperpy.core.composition import compose
from pepperpy.core.composition.types import (
    OutputComponent,
    ProcessorComponent,
    SourceComponent,
)

# Definir pasta de saída para os artefatos gerados
OUTPUT_DIR = Path("examples/outputs/text_processing")

# Garantir que a pasta de saída existe
os.makedirs(OUTPUT_DIR, exist_ok=True)


class TextSource(SourceComponent[Dict[str, Any]]):
    """Fonte de texto para tradução.

    Responsável por fornecer o texto a ser traduzido, com detecção
    automática do idioma de origem.
    """

    def __init__(self, config: Dict[str, Any]):
        """Inicializa a fonte de texto.

        Args:
            config: Configuração da fonte
                - text: Texto a ser traduzido
                - detect_language: Se deve detectar automaticamente o idioma
        """
        self.text = config.get("text", "")
        self.detect_language = config.get("detect_language", True)

    async def read(self) -> Dict[str, Any]:
        """Lê o texto da fonte.

        Returns:
            Dicionário contendo o texto e o idioma detectado
        """
        return await self.fetch()

    async def fetch(self) -> Dict[str, Any]:
        """Busca o texto e detecta o idioma.

        Returns:
            Dicionário contendo o texto e o idioma detectado
        """
        print(
            f"Processando texto de entrada: '{self.text[:50]}...' ({len(self.text)} caracteres)"
        )

        # Simular detecção de idioma
        if self.detect_language:
            # Idiomas suportados para detecção
            languages = {
                "pt": "Português",
                "en": "Inglês",
                "es": "Espanhol",
                "fr": "Francês",
                "de": "Alemão",
                "it": "Italiano",
                "ja": "Japonês",
            }

            # Simular processo de detecção
            # Em um caso real, usaria uma biblioteca como langdetect
            detected_lang = random.choice(list(languages.keys()))
            confidence = random.uniform(0.7, 0.99)

            print(
                f"Idioma detectado: {languages[detected_lang]} (código: {detected_lang})"
            )
            print(f"Confiança na detecção: {confidence:.2f}")

            return {
                "text": self.text,
                "detected_language": {
                    "code": detected_lang,
                    "name": languages[detected_lang],
                    "confidence": confidence,
                },
            }

        return {"text": self.text, "detected_language": None}


class TranslationProcessor(ProcessorComponent[Dict[str, Any], Dict[str, Any]]):
    """Processador de tradução.

    Responsável por traduzir o texto do idioma de origem para o idioma de destino.
    """

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o processador de tradução.

        Args:
            config: Configuração do processador
                - target_language: Idioma de destino
                - preserve_formatting: Se deve preservar a formatação
                - quality: Qualidade da tradução (draft, standard, premium)
        """
        self.target_language = config.get("target_language", "en")
        self.preserve_formatting = config.get("preserve_formatting", True)
        self.quality = config.get("quality", "standard")

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa os dados para tradução.

        Args:
            data: Dados contendo o texto e o idioma detectado

        Returns:
            Dicionário contendo o texto traduzido e metadados
        """
        return await self.transform(data)

    async def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Traduz o texto para o idioma de destino.

        Args:
            data: Dados contendo o texto e o idioma detectado

        Returns:
            Dicionário contendo o texto traduzido e metadados
        """
        text = data.get("text", "")
        source_lang = data.get("detected_language", {}).get("code", "unknown")

        # Mapeamento de idiomas
        languages = {
            "pt": "Português",
            "en": "Inglês",
            "es": "Espanhol",
            "fr": "Francês",
            "de": "Alemão",
            "it": "Italiano",
            "ja": "Japonês",
        }

        target_lang_name = languages.get(self.target_language, "Desconhecido")
        source_lang_name = languages.get(source_lang, "Desconhecido")

        print(f"Traduzindo de {source_lang_name} para {target_lang_name}")
        print(f"Qualidade: {self.quality}")
        print(f"Preservar formatação: {'Sim' if self.preserve_formatting else 'Não'}")

        # Simular tempo de processamento baseado na qualidade
        processing_time = {
            "draft": (0.2, 0.5),
            "standard": (0.5, 1.0),
            "premium": (1.0, 2.0),
        }.get(self.quality, (0.5, 1.0))

        await asyncio.sleep(random.uniform(*processing_time))

        # Simular tradução
        # Em um caso real, usaria uma API de tradução como Google Translate ou DeepL

        # Prefixos simulados para demonstrar a tradução
        prefixes = {
            "en": "Translated to English: ",
            "pt": "Traduzido para Português: ",
            "es": "Traducido al Español: ",
            "fr": "Traduit en Français: ",
            "de": "Übersetzt auf Deutsch: ",
            "it": "Tradotto in Italiano: ",
            "ja": "日本語に翻訳: ",
        }

        # Simular texto traduzido
        translated_text = f"{prefixes.get(self.target_language, '')}{text}"

        # Simular estatísticas de tradução
        word_count = len(text.split())
        character_count = len(text)

        return {
            "original_text": text,
            "translated_text": translated_text,
            "source_language": {"code": source_lang, "name": source_lang_name},
            "target_language": {"code": self.target_language, "name": target_lang_name},
            "statistics": {
                "word_count": word_count,
                "character_count": character_count,
                "processing_time_ms": int(random.uniform(*processing_time) * 1000),
            },
            "quality": self.quality,
        }


class TranslationOutput(OutputComponent[Dict[str, Any]]):
    """Componente de saída para tradução.

    Este componente formata e exibe o resultado da tradução.
    """

    def __init__(self, config: Dict[str, Any]):
        """Inicializa o componente de saída.

        Args:
            config: Configuração do componente
                - format: Formato de saída (text, json, html)
                - include_metadata: Incluir metadados na saída
                - output_file: Caminho para salvar o resultado (opcional)
        """
        self.format = config.get("format", "text")
        self.include_metadata = config.get("include_metadata", False)
        self.output_file = config.get("output_file", None)

        # Se output_file for especificado, garantir que é relativo à pasta de saída
        if self.output_file:
            self.output_file = OUTPUT_DIR / self.output_file

    async def write(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Escreve os dados processados na saída.

        Args:
            data: Dados processados

        Returns:
            Dados de saída com informações adicionais
        """
        # Extrair dados
        original_text = data.get("original_text", "")
        translated_text = data.get("translated_text", "")
        source_language = data.get("source_language", "")
        target_language = data.get("target_language", "")
        quality = data.get("quality", "")
        metadata = data.get("statistics", {})

        # Formatar saída
        if self.format == "text":
            output_content = f"Texto original ({source_language}):\n{original_text}\n\n"
            output_content += f"Tradução ({target_language}):\n{translated_text}"

            if self.include_metadata:
                output_content += "\n\nMetadados:\n"
                output_content += f"- Qualidade: {quality}\n"
                output_content += f"- Tempo de processamento: {metadata.get('processing_time_ms', 0) / 1000:.2f}s\n"
                output_content += f"- Caracteres: {len(original_text)}\n"

        elif self.format == "json":
            output_data = {
                "translation": {
                    "original": {
                        "text": original_text,
                        "language": source_language,
                    },
                    "translated": {
                        "text": translated_text,
                        "language": target_language,
                    },
                    "quality": quality,
                }
            }

            if self.include_metadata:
                output_data["metadata"] = metadata

            output_content = json.dumps(output_data, indent=2, ensure_ascii=False)

        elif self.format == "html":
            output_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tradução</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ display: flex; }}
        .column {{ flex: 1; padding: 10px; }}
        .original {{ background-color: #f0f0f0; }}
        .translated {{ background-color: #e0f0e0; }}
        .metadata {{ margin-top: 20px; font-size: 0.8em; color: #666; }}
    </style>
</head>
<body>
    <h1>Tradução</h1>
    <div class="container">
        <div class="column original">
            <h2>Texto Original ({source_language})</h2>
            <p>{original_text}</p>
        </div>
        <div class="column translated">
            <h2>Tradução ({target_language})</h2>
            <p>{translated_text}</p>
        </div>
    </div>
"""

            if self.include_metadata:
                output_content += f"""
    <div class="metadata">
        <h3>Metadados</h3>
        <ul>
            <li>Qualidade: {quality}</li>
            <li>Tempo de processamento: {metadata.get("processing_time_ms", 0) / 1000:.2f}s</li>
            <li>Caracteres: {len(original_text)}</li>
        </ul>
    </div>
"""

            output_content += """
</body>
</html>
"""
        else:
            output_content = translated_text

        # Exibir resultado
        if self.format == "text":
            print(output_content)
        else:
            print(f"Conteúdo formatado ({len(output_content)} caracteres)")

        # Salvar em arquivo, se especificado
        if self.output_file:
            print(f"Salvando resultado em: {self.output_file}")
            # Salvar o arquivo
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(output_content)

        return {
            "format": self.format,
            "content": output_content,
            "output_file": self.output_file,
            "metadata": metadata,
        }

    async def output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formata e exibe o resultado da tradução.

        Args:
            data: Dados contendo o texto traduzido e metadados

        Returns:
            Dicionário contendo o resultado formatado
        """
        return await self.write(data)


async def translate_text(
    text: str,
    target_language: str = "en",
    quality: str = "standard",
    output_format: str = "text",
    include_metadata: bool = False,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Traduz um texto para outro idioma.

    Args:
        text: Texto a ser traduzido
        target_language: Idioma de destino (código ISO)
        quality: Qualidade da tradução (draft, standard, professional)
        output_format: Formato de saída (text, json, html)
        include_metadata: Incluir metadados na saída
        output_file: Caminho para salvar o resultado (opcional)

    Returns:
        Resultado da tradução com metadados
    """
    print(f"Traduzindo texto para {target_language} (qualidade: {quality})")

    # Configurar componentes
    source_config = {
        "text": text,
        "detect_language": True,
    }

    processor_config = {
        "target_language": target_language,
        "quality": quality,
    }

    output_config = {
        "format": output_format,
        "include_metadata": include_metadata,
        "output_file": output_file,
    }

    # Criar pipeline de tradução
    pipeline = (
        compose("translator")
        .source(TextSource(source_config))
        .process(TranslationProcessor(processor_config))
        .output(TranslationOutput(output_config))
    )

    # Executar pipeline
    result = await pipeline.execute()

    return result


async def demo_translator():
    """Demonstra o uso do tradutor multilíngue."""
    print("=== Demonstração do Tradutor Multilíngue ===\n")

    # Exemplo 1: Tradução simples
    print("\n--- Exemplo 1: Tradução Simples ---")
    text = "Olá, mundo! Este é um exemplo de tradução usando o PepperPy."
    result = await translate_text(
        text=text,
        target_language="en",
        quality="standard",
        output_format="text",
    )
    print("\nTradução concluída!")

    # Exemplo 2: Tradução com metadados e saída em JSON
    print("\n--- Exemplo 2: Tradução com Metadados (JSON) ---")
    text = """
    A inteligência artificial (IA) é um campo da ciência da computação que se concentra
    no desenvolvimento de sistemas capazes de realizar tarefas que normalmente exigiriam
    inteligência humana. Isso inclui aprendizado, raciocínio, resolução de problemas,
    percepção e compreensão de linguagem natural.
    """
    result = await translate_text(
        text=text,
        target_language="fr",
        quality="professional",
        output_format="json",
        include_metadata=True,
        output_file="traducao_ia_fr.json",
    )
    print("\nTradução concluída!")

    # Exemplo 3: Tradução com saída em HTML
    print("\n--- Exemplo 3: Tradução com Saída HTML ---")
    text = """
    O framework PepperPy oferece uma maneira elegante e flexível de criar pipelines
    de processamento de dados e texto. Com sua arquitetura baseada em componentes,
    é possível construir fluxos complexos de forma modular e reutilizável.
    """
    result = await translate_text(
        text=text,
        target_language="es",
        quality="standard",
        output_format="html",
        include_metadata=True,
        output_file="traducao_framework_es.html",
    )
    print("\nTradução concluída!")

    print("\n=== Demonstração Concluída ===")
    print(f"Os arquivos de saída foram salvos em: {OUTPUT_DIR}")


async def main():
    """Função principal."""
    await demo_translator()


if __name__ == "__main__":
    asyncio.run(main())
