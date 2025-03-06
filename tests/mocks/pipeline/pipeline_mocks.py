"""Mocks para componentes do framework PepperPy.

Este módulo implementa mocks para componentes do framework,
permitindo o uso de componentes simulados quando os reais não estão disponíveis.
"""

import asyncio
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from pepperpy.core.protocols.composition import (
    OutputProtocol,
    ProcessorProtocol,
    SourceProtocol,
)

logger = logging.getLogger(__name__)


class MockRSSSource:
    """Mock para fonte de conteúdo RSS."""

    def __init__(self, url: str, max_items: int = 5):
        """Inicializa uma nova fonte de conteúdo RSS simulada.

        Args:
            url: URL do feed RSS.
            max_items: Número máximo de itens a serem obtidos.
        """
        self.url = url
        self.max_items = max_items

    async def fetch(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca dados da fonte RSS simulada.

        Args:
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Lista de itens do feed RSS.
        """
        logger.info(f"Buscando dados de {self.url}")
        await asyncio.sleep(0.1)  # Simular latência de rede

        # Gerar itens simulados
        items = []
        for i in range(self.max_items):
            items.append({
                "title": f"Notícia {i + 1}",
                "link": f"{self.url}/item/{i + 1}",
                "description": f"Descrição da notícia {i + 1}",
                "content": f"Conteúdo completo da notícia {i + 1}. " * 5,
                "published": datetime.now().isoformat(),
            })

        return items

    def __str__(self) -> str:
        return f"MockRSSSource(url={self.url}, max_items={self.max_items})"


class MockAPISource:
    """Mock para fonte de conteúdo de API."""

    def __init__(
        self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None
    ):
        """Inicializa uma nova fonte de conteúdo de API simulada.

        Args:
            url: URL da API.
            method: Método HTTP a ser usado.
            headers: Cabeçalhos HTTP a serem enviados.
        """
        self.url = url
        self.method = method
        self.headers = headers or {}

    async def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Busca dados da fonte de API simulada.

        Args:
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Dados da API.
        """
        logger.info(f"Buscando dados de {self.url} com método {self.method}")
        await asyncio.sleep(0.1)  # Simular latência de rede

        # Gerar dados simulados
        return {
            "status": "success",
            "data": {
                "items": [
                    {"id": i, "name": f"Item {i}", "value": random.randint(1, 100)}
                    for i in range(5)
                ]
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": self.url,
            },
        }

    def __str__(self) -> str:
        return f"MockAPISource(url={self.url}, method={self.method})"


class MockFileSource:
    """Mock para fonte de conteúdo de arquivo."""

    def __init__(self, path: str, format: str = "auto"):
        """Inicializa uma nova fonte de conteúdo de arquivo simulada.

        Args:
            path: Caminho do arquivo.
            format: Formato do arquivo. Se "auto", será detectado automaticamente.
        """
        self.path = path
        self.format = format

    async def fetch(self, context: Dict[str, Any]) -> Any:
        """Busca dados da fonte de arquivo simulada.

        Args:
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Conteúdo do arquivo.
        """
        logger.info(f"Lendo arquivo {self.path}")
        await asyncio.sleep(0.1)  # Simular latência de disco

        # Simular conteúdo do arquivo
        if self.format == "json" or (
            self.format == "auto" and self.path.endswith(".json")
        ):
            return {"data": [f"Item {i}" for i in range(5)]}
        elif self.format == "csv" or (
            self.format == "auto" and self.path.endswith(".csv")
        ):
            return "id,name,value\n1,Item 1,10\n2,Item 2,20\n3,Item 3,30\n4,Item 4,40\n5,Item 5,50"
        else:
            return "Conteúdo simulado do arquivo " + self.path

    def __str__(self) -> str:
        return f"MockFileSource(path={self.path}, format={self.format})"


class MockSummarizationProcessor:
    """Mock para processador de sumarização."""

    def __init__(self, max_length: int = 150, model: str = "default"):
        """Inicializa um novo processador de sumarização simulado.

        Args:
            max_length: Tamanho máximo do resumo.
            model: Modelo a ser usado para sumarização.
        """
        self.max_length = max_length
        self.model = model

    async def process(
        self, content: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Processa conteúdo com o processador de sumarização simulado.

        Args:
            content: Conteúdo a ser processado.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Conteúdo processado.
        """
        logger.info(f"Sumarizando conteúdo com modelo {self.model}")
        await asyncio.sleep(0.1)  # Simular processamento

        # Processar cada item
        result = []
        for item in content:
            # Copiar o item
            processed_item = item.copy()

            # Adicionar resumo
            if "content" in item:
                text = item["content"]
                # Simular resumo truncando o texto
                summary = text[: self.max_length]
                if len(text) > self.max_length:
                    summary += "..."
                processed_item["summary"] = summary

            result.append(processed_item)

        return result

    def __str__(self) -> str:
        return f"MockSummarizationProcessor(max_length={self.max_length}, model={self.model})"


class MockTranslationProcessor:
    """Mock para processador de tradução."""

    def __init__(self, target_language: str, source_language: Optional[str] = None):
        """Inicializa um novo processador de tradução simulado.

        Args:
            target_language: Idioma de destino.
            source_language: Idioma de origem. Se None, será detectado automaticamente.
        """
        self.target_language = target_language
        self.source_language = source_language

    async def process(self, content: Any, context: Dict[str, Any]) -> Any:
        """Processa conteúdo com o processador de tradução simulado.

        Args:
            content: Conteúdo a ser processado.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Conteúdo processado.
        """
        logger.info(f"Traduzindo para {self.target_language}")
        await asyncio.sleep(0.1)  # Simular processamento

        # Simular tradução
        if isinstance(content, list):
            return [self._translate_item(item) for item in content]
        elif isinstance(content, dict):
            return self._translate_item(content)
        elif isinstance(content, str):
            return f"[{self.target_language}] {content}"
        else:
            return content

    def _translate_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Traduz um item.

        Args:
            item: Item a ser traduzido.

        Returns:
            Item traduzido.
        """
        result = item.copy()

        # Traduzir campos de texto
        for key, value in item.items():
            if isinstance(value, str):
                result[key] = f"[{self.target_language}] {value}"

        return result

    def __str__(self) -> str:
        return f"MockTranslationProcessor(target_language={self.target_language})"


class MockClassificationProcessor:
    """Mock para processador de classificação."""

    def __init__(self, categories: List[str], model: str = "default"):
        """Inicializa um novo processador de classificação simulado.

        Args:
            categories: Categorias para classificação.
            model: Modelo a ser usado para classificação.
        """
        self.categories = categories
        self.model = model

    async def process(
        self, content: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Processa conteúdo com o processador de classificação simulado.

        Args:
            content: Conteúdo a ser processado.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Conteúdo processado.
        """
        logger.info(f"Classificando conteúdo em {len(self.categories)} categorias")
        await asyncio.sleep(0.1)  # Simular processamento

        # Processar cada item
        result = []
        for item in content:
            # Copiar o item
            processed_item = item.copy()

            # Adicionar classificação
            processed_item["category"] = random.choice(self.categories)
            processed_item["confidence"] = random.uniform(0.7, 1.0)

            result.append(processed_item)

        return result

    def __str__(self) -> str:
        return f"MockClassificationProcessor(categories={self.categories}, model={self.model})"


class MockPodcastGenerator:
    """Mock para gerador de podcast."""

    def __init__(self, voice: str = "en", output_path: str = "output.mp3"):
        """Inicializa um novo gerador de podcast simulado.

        Args:
            voice: Voz a ser usada para síntese de fala.
            output_path: Caminho do arquivo de saída.
        """
        self.voice = voice
        self.output_path = output_path

    async def generate(
        self, content: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Path:
        """Gera podcast com o gerador simulado.

        Args:
            content: Conteúdo a ser usado para gerar o podcast.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Caminho do arquivo de podcast gerado.
        """
        logger.info(f"Gerando podcast com voz {self.voice} em {self.output_path}")
        await asyncio.sleep(0.1)  # Simular processamento

        # Criar conteúdo do podcast
        podcast_content = "\n\n".join([
            f"# {item['title']}\n\n{item.get('summary', item.get('content', ''))}"
            for item in content
        ])

        # Criar arquivo de saída
        output_file = Path(self.output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(podcast_content)

        return output_file

    def __str__(self) -> str:
        return (
            f"MockPodcastGenerator(voice={self.voice}, output_path={self.output_path})"
        )


class MockFileOutput:
    """Mock para saída de arquivo."""

    def __init__(self, path: str, format: str = "auto"):
        """Inicializa uma nova saída de arquivo simulada.

        Args:
            path: Caminho do arquivo.
            format: Formato do arquivo. Se "auto", será detectado automaticamente.
        """
        self.path = path
        self.format = format

    async def generate(self, content: Any, context: Dict[str, Any]) -> Path:
        """Gera arquivo com a saída simulada.

        Args:
            content: Conteúdo a ser usado para gerar o arquivo.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Caminho do arquivo gerado.
        """
        logger.info(f"Gerando arquivo {self.path}")
        await asyncio.sleep(0.1)  # Simular processamento

        # Criar arquivo de saída
        output_file = Path(self.path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Escrever conteúdo no formato apropriado
        if self.format == "json" or (
            self.format == "auto" and self.path.endswith(".json")
        ):
            output_file.write_text(json.dumps(content, indent=2))
        elif self.format == "csv" or (
            self.format == "auto" and self.path.endswith(".csv")
        ):
            if isinstance(content, list) and all(
                isinstance(item, dict) for item in content
            ):
                # Converter lista de dicionários para CSV
                headers = list(content[0].keys())
                rows = [
                    ",".join(str(item.get(h, "")) for h in headers) for item in content
                ]
                csv_content = ",".join(headers) + "\n" + "\n".join(rows)
                output_file.write_text(csv_content)
            else:
                output_file.write_text(str(content))
        else:
            output_file.write_text(str(content))

        return output_file

    def __str__(self) -> str:
        return f"MockFileOutput(path={self.path}, format={self.format})"


class MockAPIOutput:
    """Mock para saída de API."""

    def __init__(
        self, url: str, method: str = "POST", headers: Optional[Dict[str, str]] = None
    ):
        """Inicializa uma nova saída de API simulada.

        Args:
            url: URL da API.
            method: Método HTTP a ser usado.
            headers: Cabeçalhos HTTP a serem enviados.
        """
        self.url = url
        self.method = method
        self.headers = headers or {}

    async def generate(self, content: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Envia conteúdo para a API simulada.

        Args:
            content: Conteúdo a ser enviado para a API.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Resposta da API.
        """
        logger.info(f"Enviando dados para {self.url} com método {self.method}")
        await asyncio.sleep(0.1)  # Simular latência de rede

        # Simular resposta da API
        return {
            "status": "success",
            "message": "Dados enviados com sucesso",
            "timestamp": datetime.now().isoformat(),
            "request_id": f"req_{random.randint(1000, 9999)}",
        }

    def __str__(self) -> str:
        return f"MockAPIOutput(url={self.url}, method={self.method})"
