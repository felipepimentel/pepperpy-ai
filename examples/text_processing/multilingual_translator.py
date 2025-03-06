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

from pepperpy.core.composition import Output, Processor, Source, compose


class TextSource(Source):
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


class TranslationProcessor(Processor):
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


class TranslationOutput(Output):
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

    async def output(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

        elif self.format == "html":
            output_content = "<div class='translation'>\n"
            output_content += "  <div class='translation-header'>\n"
            output_content += f"    <div class='source-language'>De: {source_lang.get('name')} ({source_lang.get('code')})</div>\n"
            output_content += f"    <div class='target-language'>Para: {target_lang.get('name')} ({target_lang.get('code')})</div>\n"
            output_content += "  </div>\n"
            output_content += "  <div class='translation-content'>\n"
            output_content += "    <div class='original-text'>\n"
            output_content += "      <h3>Texto original:</h3>\n"
            output_content += f"      <p>{original_text}</p>\n"
            output_content += "    </div>\n"
            output_content += "    <div class='translated-text'>\n"
            output_content += "      <h3>Texto traduzido:</h3>\n"
            output_content += f"      <p>{translated_text}</p>\n"
            output_content += "    </div>\n"
            output_content += "  </div>\n"

            if self.include_metadata:
                output_content += "  <div class='translation-metadata'>\n"
                output_content += "    <h4>Metadados:</h4>\n"
                output_content += "    <ul>\n"
                output_content += (
                    f"      <li>Palavras: {statistics.get('word_count')}</li>\n"
                )
                output_content += (
                    f"      <li>Caracteres: {statistics.get('character_count')}</li>\n"
                )
                output_content += f"      <li>Tempo de processamento: {statistics.get('processing_time_ms')} ms</li>\n"
                output_content += f"      <li>Qualidade: {quality}</li>\n"
                output_content += "    </ul>\n"
                output_content += "  </div>\n"

            output_content += "</div>"

        elif self.format == "json":
            output_content = {
                "translation": {
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "original_text": original_text,
                    "translated_text": translated_text,
                }
            }

            if self.include_metadata:
                output_content["metadata"] = {
                    "statistics": statistics,
                    "quality": quality,
                }

        else:
            output_content = f"Formato não suportado: {self.format}"

        # Salvar em arquivo se especificado
        if self.output_file and self.format != "json":
            try:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    f.write(output_content)
                print(f"Resultado salvo em: {self.output_file}")
            except Exception as e:
                print(f"Erro ao salvar arquivo: {str(e)}")

        return {
            "format": self.format,
            "content": output_content,
            "file_path": self.output_file if self.output_file else None,
        }


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
        target_language: Código do idioma de destino
        quality: Qualidade da tradução (draft, standard, premium)
        output_format: Formato de saída (text, json, html)
        include_metadata: Se deve incluir metadados
        output_file: Caminho para salvar o resultado (opcional)

    Returns:
        Resultado da tradução
    """
    # Configurar componentes
    source = TextSource({"text": text, "detect_language": True})

    processor = TranslationProcessor({
        "target_language": target_language,
        "preserve_formatting": True,
        "quality": quality,
    })

    output = TranslationOutput({
        "format": output_format,
        "include_metadata": include_metadata,
        "output_file": output_file,
    })

    # Compor pipeline
    pipeline = await compose(source, processor, output)

    # Executar pipeline
    result = await pipeline.execute()

    return result


async def demo_translator():
    """Demonstra o uso do tradutor multilíngue."""
    print("\n=== Demonstração do Tradutor Multilíngue ===")

    # Exemplo 1: Tradução simples para inglês
    print("\n--- Exemplo 1: Tradução simples para inglês ---")
    text1 = "Este é um exemplo de texto que será traduzido para o inglês."
    result1 = await translate_text(
        text=text1,
        target_language="en",
        quality="standard",
        output_format="text",
        include_metadata=True,
    )

    print("\nResultado:")
    print(result1["content"])

    # Exemplo 2: Tradução para espanhol com alta qualidade
    print("\n--- Exemplo 2: Tradução para espanhol com alta qualidade ---")
    text2 = "Este texto será traduzido para o espanhol com alta qualidade."
    result2 = await translate_text(
        text=text2,
        target_language="es",
        quality="premium",
        output_format="text",
        include_metadata=True,
    )

    print("\nResultado:")
    print(result2["content"])

    # Exemplo 3: Tradução para francês com saída em HTML
    print("\n--- Exemplo 3: Tradução para francês com saída em HTML ---")
    text3 = "Este texto será traduzido para o francês e formatado em HTML."
    result3 = await translate_text(
        text=text3,
        target_language="fr",
        quality="standard",
        output_format="html",
        include_metadata=True,
    )

    print("\nResultado (HTML):")
    print(result3["content"][:200] + "...\n(HTML truncado)")

    # Exemplo 4: Tradução rápida para alemão
    print("\n--- Exemplo 4: Tradução rápida para alemão ---")
    text4 = "Este é um texto curto para tradução rápida."
    result4 = await translate_text(
        text=text4,
        target_language="de",
        quality="draft",
        output_format="text",
        include_metadata=False,
    )

    print("\nResultado:")
    print(result4["content"])


async def main():
    """Função principal."""
    print("=== Tradutor Multilíngue ===")
    print(
        "Este exemplo demonstra como criar um sistema de tradução multilíngue usando o PepperPy."
    )

    await demo_translator()

    print("\n=== Recursos Demonstrados ===")
    print("1. Detecção automática de idioma")
    print("2. Tradução para múltiplos idiomas")
    print("3. Diferentes níveis de qualidade de tradução")
    print("4. Múltiplos formatos de saída (texto, HTML, JSON)")
    print("5. Inclusão opcional de metadados")
    print("6. Composição de pipeline com Source, Processor e Output")


if __name__ == "__main__":
    asyncio.run(main())
