"""Mocks para testes de componentes de pipeline.

Este módulo fornece implementações de mock para componentes de pipeline,
permitindo testes sem dependências externas.
"""

import os
from typing import Any, Dict, List, Optional


class MockRSSSource:
    """Mock para fonte de conteúdo RSS."""

    def __init__(self, url: str, max_items: int = 5):
        """Inicializa o mock.

        Args:
            url: URL do feed RSS.
            max_items: Número máximo de itens a serem obtidos.
        """
        self.url = url
        self.max_items = max_items

    async def fetch(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Busca dados da fonte.

        Args:
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Lista de itens do feed RSS.
        """
        return [
            {
                "title": f"Item {i} do feed {self.url}",
                "description": f"Descrição do item {i} do feed {self.url}",
                "link": f"{self.url}/item/{i}",
                "published": "2023-01-01T00:00:00Z",
            }
            for i in range(min(5, self.max_items))
        ]


class MockAPISource:
    """Mock para fonte de conteúdo de API."""

    def __init__(
        self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None
    ):
        """Inicializa o mock.

        Args:
            url: URL da API.
            method: Método HTTP a ser usado.
            headers: Cabeçalhos HTTP a serem enviados.
        """
        self.url = url
        self.method = method
        self.headers = headers or {}

    async def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Busca dados da fonte.

        Args:
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Dados da API.
        """
        return {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "data": {
                "message": f"Dados simulados da API {self.url}",
                "status": "success",
                "timestamp": "2023-01-01T00:00:00Z",
            },
        }


class MockFileSource:
    """Mock para fonte de conteúdo de arquivo."""

    def __init__(self, path: str, format: str = "auto"):
        """Inicializa o mock.

        Args:
            path: Caminho do arquivo.
            format: Formato do arquivo.
        """
        self.path = path
        self.format = format

    async def fetch(self, context: Dict[str, Any]) -> str:
        """Busca dados da fonte.

        Args:
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Conteúdo do arquivo.
        """
        return f"Conteúdo simulado do arquivo {self.path} no formato {self.format}"


class MockSummarizationProcessor:
    """Mock para processador de sumarização."""

    def __init__(self, max_length: int = 150, model: str = "default"):
        """Inicializa o mock.

        Args:
            max_length: Tamanho máximo do resumo.
            model: Modelo a ser usado para sumarização.
        """
        self.max_length = max_length
        self.model = model

    async def process(self, content: Any, context: Dict[str, Any]) -> str:
        """Processa conteúdo.

        Args:
            content: Conteúdo a ser processado.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Resumo do conteúdo.
        """
        if isinstance(content, list):
            # Resumo de lista de itens (ex: feed RSS)
            return "\n\n".join(
                f"Resumo do item '{item.get('title', f'Item {i}')}': "
                f"{item.get('description', '')[: self.max_length]}..."
                for i, item in enumerate(content[:5])
            )
        elif isinstance(content, dict):
            # Resumo de dicionário (ex: resposta de API)
            return f"Resumo dos dados: {str(content)[: self.max_length]}..."
        else:
            # Resumo de texto
            content_str = str(content)
            return f"{content_str[: self.max_length]}..."


class MockTranslationProcessor:
    """Mock para processador de tradução."""

    def __init__(self, target_language: str, source_language: Optional[str] = None):
        """Inicializa o mock.

        Args:
            target_language: Idioma de destino.
            source_language: Idioma de origem.
        """
        self.target_language = target_language
        self.source_language = source_language

    async def process(self, content: Any, context: Dict[str, Any]) -> str:
        """Processa conteúdo.

        Args:
            content: Conteúdo a ser processado.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Conteúdo traduzido.
        """
        content_str = str(content)
        return (
            f"[Tradução para {self.target_language} "
            f"de {self.source_language or 'auto'}] {content_str}"
        )


class MockClassificationProcessor:
    """Mock para processador de classificação."""

    def __init__(self, categories: List[str], model: str = "default"):
        """Inicializa o mock.

        Args:
            categories: Categorias para classificação.
            model: Modelo a ser usado para classificação.
        """
        self.categories = categories
        self.model = model

    async def process(self, content: Any, context: Dict[str, Any]) -> Dict[str, float]:
        """Processa conteúdo.

        Args:
            content: Conteúdo a ser processado.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Classificação do conteúdo.
        """
        import random

        # Gerar classificação aleatória
        scores = [random.random() for _ in self.categories]
        total = sum(scores)
        normalized = [score / total for score in scores]

        return {category: score for category, score in zip(self.categories, normalized)}


class MockPodcastGenerator:
    """Mock para gerador de podcast."""

    def __init__(self, voice: str = "en", output_path: str = "output.mp3"):
        """Inicializa o mock.

        Args:
            voice: Voz a ser usada para síntese de fala.
            output_path: Caminho do arquivo de saída.
        """
        self.voice = voice
        self.output_path = output_path

    async def generate(self, content: Any, context: Dict[str, Any]) -> str:
        """Gera saída.

        Args:
            content: Conteúdo a ser usado para gerar a saída.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Caminho do arquivo de podcast.
        """
        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        # Simular criação de arquivo
        with open(self.output_path, "w") as f:
            f.write(f"Podcast simulado com voz {self.voice}\n\n")
            f.write(str(content))

        return self.output_path


class MockFileOutput:
    """Mock para saída de arquivo."""

    def __init__(self, path: str, format: str = "auto"):
        """Inicializa o mock.

        Args:
            path: Caminho do arquivo.
            format: Formato do arquivo.
        """
        self.path = path
        self.format = format

    async def generate(self, content: Any, context: Dict[str, Any]) -> str:
        """Gera saída.

        Args:
            content: Conteúdo a ser usado para gerar a saída.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Caminho do arquivo.
        """
        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        # Simular criação de arquivo
        with open(self.path, "w") as f:
            f.write(str(content))

        return self.path


class MockAPIOutput:
    """Mock para saída de API."""

    def __init__(
        self, url: str, method: str = "POST", headers: Optional[Dict[str, str]] = None
    ):
        """Inicializa o mock.

        Args:
            url: URL da API.
            method: Método HTTP a ser usado.
            headers: Cabeçalhos HTTP a serem enviados.
        """
        self.url = url
        self.method = method
        self.headers = headers or {}

    async def generate(self, content: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gera saída.

        Args:
            content: Conteúdo a ser usado para gerar a saída.
            context: Contexto de execução com parâmetros adicionais.

        Returns:
            Resposta da API.
        """
        return {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "response": {
                "message": "Dados enviados com sucesso",
                "status": "success",
                "timestamp": "2023-01-01T00:00:00Z",
            },
        }
