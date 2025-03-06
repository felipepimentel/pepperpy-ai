"""Testes para o módulo de composição universal.

Este módulo contém testes para verificar a funcionalidade da arquitetura
de composição universal.
"""

import asyncio
import os
import tempfile
from typing import Any, Dict, List

import pytest

from pepperpy.core.composition import (
    Outputs,
    Processors,
    Sources,
    compose,
    compose_parallel,
)


@pytest.mark.asyncio
async def test_simple_pipeline():
    """Testa um pipeline simples de processamento de texto."""
    # Criar um arquivo temporário para a saída
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
        output_path = temp.name
    
    try:
        # Criar um pipeline simples
        pipeline = (
            compose("test_pipeline")
            .source(Sources.text("Hello, world!"))
            .process(Processors.translate(target_language="pt"))
            .output(Outputs.file(output_path))
        )
        
        # Executar o pipeline
        result_path = await pipeline.execute()
        
        # Verificar o resultado
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verificar o conteúdo do arquivo
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "[Traduzido para Português]" in content
        assert "Hello, world!" in content
    
    finally:
        # Limpar o arquivo temporário
        if os.path.exists(output_path):
            os.unlink(output_path)


@pytest.mark.asyncio
async def test_parallel_pipeline():
    """Testa um pipeline paralelo de processamento de texto."""
    # Criar um arquivo temporário para a saída
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
        output_path = temp.name
    
    try:
        # Criar um pipeline paralelo
        pipeline = (
            compose_parallel("test_parallel_pipeline")
            .source(Sources.text("Hello, world! This is a test."))
            .process(Processors.translate(target_language="pt"))
            .process(Processors.extract_keywords(max_keywords=3))
            .output(Outputs.file(output_path))
        )
        
        # Executar o pipeline
        result_path = await pipeline.execute()
        
        # Verificar o resultado
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verificar o conteúdo do arquivo (deve conter o resultado do último processador)
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # O último processador é o extrator de palavras-chave, então esperamos uma lista
        assert "Hello" in content or "world" in content or "test" in content
    
    finally:
        # Limpar o arquivo temporário
        if os.path.exists(output_path):
            os.unlink(output_path)


@pytest.mark.asyncio
async def test_rss_pipeline():
    """Testa um pipeline de processamento de feed RSS."""
    # Criar um arquivo temporário para a saída
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
        output_path = temp.name
    
    try:
        # Criar um pipeline para processar um feed RSS
        pipeline = (
            compose("test_rss_pipeline")
            .source(Sources.rss("https://example.com/rss", max_items=3))
            .process(Processors.summarize(max_length=100))
            .output(Outputs.file(output_path))
        )
        
        # Executar o pipeline
        result_path = await pipeline.execute()
        
        # Verificar o resultado
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verificar o conteúdo do arquivo
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert "Resumo dos principais itens" in content
        assert "Item 1" in content
        assert "Item 2" in content
        assert "Item 3" in content
    
    finally:
        # Limpar o arquivo temporário
        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == "__main__":
    asyncio.run(test_simple_pipeline())
    asyncio.run(test_parallel_pipeline())
    asyncio.run(test_rss_pipeline()) 