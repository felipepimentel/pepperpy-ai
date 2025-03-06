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
import random
from typing import Any, Dict, Optional

from pepperpy.core.composition import compose
from pepperpy.core.composition.types import (
    OutputComponent,
    ProcessorComponent,
    SourceComponent,
)


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
    """Saída da tradução.

    Responsável por formatar e exibir o resultado da tradução.
    """

    def __init__(self, config: Dict[str, Any]):
        """Inicializa a saída da tradução.

        Args:
            config: Configuração da saída
                - format: Formato de saída (text, json, html)
                - include_metadata: Se deve incluir metadados
                - output_file: Caminho para salvar o resultado (opcional)
        """
        self.format = config.get("format", "text")
        self.include_metadata = config.get("include_metadata", False)
        self.output_file = config.get("output_file", None)

    async def write(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formata e exibe o resultado da tradução.

        Args:
            data: Dados contendo o texto traduzido e metadados

        Returns:
            Dicionário contendo o resultado formatado
        """
        original_text = data.get("original_text", "")
        translated_text = data.get("translated_text", "")
        source_lang = data.get("source_language", {})
        target_lang = data.get("target_language", {})
        statistics = data.get("statistics", {})
        quality = data.get("quality", "standard")

        print(f"Formatando saída no formato '{self.format}'")

        # Formatar saída de acordo com o formato especificado
        if self.format == "text":
            output_content = "=== TRADUÇÃO ===\n\n"
            output_content += (
                f"De: {source_lang.get('name')} ({source_lang.get('code')})\n"
            )
            output_content += (
                f"Para: {target_lang.get('name')} ({target_lang.get('code')})\n\n"
            )
            output_content += f"Texto original:\n{original_text}\n\n"
            output_content += f"Texto traduzido:\n{translated_text}\n"

            if self.include_metadata:
                output_content += "\n=== METADADOS ===\n"
                output_content += f"Palavras: {statistics.get('word_count')}\n"
                output_content += f"Caracteres: {statistics.get('character_count')}\n"
                output_content += f"Tempo de processamento: {statistics.get('processing_time_ms')} ms\n"
                output_content += f"Qualidade: {quality}\n"

        elif self.format == "json":
            import json

            output_data = {
                "translation": {
                    "original": original_text,
                    "translated": translated_text,
                    "source_language": source_lang,
                    "target_language": target_lang,
                }
            }

            if self.include_metadata:
                output_data["metadata"] = {
                    "statistics": statistics,
                    "quality": quality,
                }

            output_content = json.dumps(output_data, indent=2, ensure_ascii=False)

        elif self.format == "html":
            output_content = "<!DOCTYPE html>\n<html>\n<head>\n"
            output_content += "<meta charset='utf-8'>\n"
            output_content += "<title>Tradução</title>\n"
            output_content += "<style>body{font-family:Arial,sans-serif;margin:20px;line-height:1.6}</style>\n"
            output_content += "</head>\n<body>\n"
            output_content += "<h1>Tradução</h1>\n"
            output_content += f"<p><strong>De:</strong> {source_lang.get('name')} ({source_lang.get('code')})</p>\n"
            output_content += f"<p><strong>Para:</strong> {target_lang.get('name')} ({target_lang.get('code')})</p>\n"
            output_content += "<h2>Texto original</h2>\n"
            output_content += f"<div>{original_text}</div>\n"
            output_content += "<h2>Texto traduzido</h2>\n"
            output_content += f"<div>{translated_text}</div>\n"

            if self.include_metadata:
                output_content += "<h2>Metadados</h2>\n<ul>\n"
                output_content += f"<li><strong>Palavras:</strong> {statistics.get('word_count')}</li>\n"
                output_content += f"<li><strong>Caracteres:</strong> {statistics.get('character_count')}</li>\n"
                output_content += f"<li><strong>Tempo de processamento:</strong> {statistics.get('processing_time_ms')} ms</li>\n"
                output_content += f"<li><strong>Qualidade:</strong> {quality}</li>\n"
                output_content += "</ul>\n"

            output_content += "</body>\n</html>"

        else:
            output_content = translated_text

        # Exibir resultado
        print("\n=== RESULTADO DA TRADUÇÃO ===")
        print(f"Formato: {self.format}")
        if self.format == "text":
            print(output_content)
        else:
            print(f"Conteúdo formatado ({len(output_content)} caracteres)")

        # Salvar em arquivo, se especificado
        if self.output_file:
            print(f"Salvando resultado em: {self.output_file}")
            # Em uma implementação real, salvaríamos o arquivo
            # with open(self.output_file, "w", encoding="utf-8") as f:
            #     f.write(output_content)

        return {
            "format": self.format,
            "content": output_content,
            "output_file": self.output_file,
            "translation": {
                "original": original_text,
                "translated": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
            },
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
    """Traduz um texto para o idioma especificado.

    Args:
        text: Texto a ser traduzido
        target_language: Idioma de destino
        quality: Qualidade da tradução (draft, standard, premium)
        output_format: Formato de saída (text, json, html)
        include_metadata: Se deve incluir metadados
        output_file: Caminho para salvar o resultado (opcional)

    Returns:
        Dicionário contendo o resultado da tradução
    """
    print(f"Iniciando tradução para {target_language}")
    print(f"Texto: '{text[:50]}...' ({len(text)} caracteres)")

    # Criar pipeline de tradução
    result = await (
        compose("translator")
        .source(
            TextSource({
                "text": text,
                "detect_language": True,
            })
        )
        .process(
            TranslationProcessor({
                "target_language": target_language,
                "preserve_formatting": True,
                "quality": quality,
            })
        )
        .output(
            TranslationOutput({
                "format": output_format,
                "include_metadata": include_metadata,
                "output_file": output_file,
            })
        )
        .execute()
    )

    return result


async def demo_translator():
    """Demonstra o uso do tradutor multilíngue."""
    print("=== Demonstração do Tradutor Multilíngue ===\n")

    # Exemplo 1: Tradução simples para inglês
    print("--- Exemplo 1: Tradução para inglês ---")
    await translate_text(
        "Este é um exemplo de texto em português que será traduzido para inglês.",
        target_language="en",
        quality="standard",
        output_format="text",
        include_metadata=True,
    )

    print("\n--- Exemplo 2: Tradução para espanhol com saída em JSON ---")
    await translate_text(
        "This is an example text in English that will be translated to Spanish.",
        target_language="es",
        quality="premium",
        output_format="json",
        include_metadata=True,
    )

    print("\n--- Exemplo 3: Tradução para francês com saída em HTML ---")
    await translate_text(
        "Dies ist ein Beispieltext auf Deutsch, der ins Französische übersetzt wird.",
        target_language="fr",
        quality="draft",
        output_format="html",
        include_metadata=True,
    )

    print("\n=== Demonstração Concluída ===")
    print("O tradutor multilíngue demonstrou:")
    print("1. Detecção automática de idioma")
    print("2. Tradução para diferentes idiomas")
    print("3. Diferentes níveis de qualidade")
    print("4. Múltiplos formatos de saída")
    print("5. Inclusão de metadados")


async def main():
    """Função principal."""
    await demo_translator()


if __name__ == "__main__":
    asyncio.run(main())
