"""Fontes de dados baseadas em web.

Este módulo define classes para acesso a dados em recursos web.
"""

import json
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from pepperpy.core.sources.base import BaseSource, SourceConfig


class WebSource(BaseSource):
    """Fonte de dados baseada em recursos web.

    Esta classe fornece funcionalidades para ler dados de URLs.
    """

    def __init__(
        self,
        url: str,
        config: Optional[SourceConfig] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> None:
        """Inicializa a fonte de dados web.

        Args:
            url: URL do recurso
            config: Configuração da fonte de dados
            headers: Cabeçalhos HTTP
            timeout: Tempo limite em segundos
        """
        if config is None:
            parsed_url = urlparse(url)
            name = f"web_{parsed_url.netloc}"
            config = SourceConfig(name=name)

        super().__init__(config)

        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self._session = None

    async def _initialize(self) -> None:
        """Inicializa a fonte de dados web.

        Cria uma sessão HTTP.
        """
        try:
            import aiohttp

            self._session = aiohttp.ClientSession(headers=self.headers)
        except ImportError:
            self.logger.error(
                "Módulo aiohttp não encontrado. Instale com: pip install aiohttp"
            )
            raise

    async def read(
        self, method: str = "GET", params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> bytes:
        """Lê dados do recurso web.

        Args:
            method: Método HTTP (GET, POST, etc.)
            params: Parâmetros da requisição
            **kwargs: Argumentos adicionais para a requisição

        Returns:
            Conteúdo da resposta como bytes
        """
        await self.initialize()

        if self._session is None:
            raise RuntimeError("Sessão HTTP não inicializada")

        self.logger.debug(f"Acessando URL: {self.url} (método: {method})")

        try:
            import aiohttp
            # Criar objeto de timeout adequado
            timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
            
            async with self._session.request(
                method, self.url, params=params, timeout=timeout_obj, **kwargs
            ) as response:
                response.raise_for_status()
                content = await response.read()
                return content
        except Exception as e:
            self.logger.error(f"Erro ao acessar URL {self.url}: {e}")
            raise

    async def _close(self) -> None:
        """Fecha a fonte de dados web.

        Fecha a sessão HTTP.
        """
        if self._session is not None:
            await self._session.close()
            self._session = None


class WebAPISource(WebSource):
    """Fonte de dados baseada em API web.

    Esta classe fornece funcionalidades para interagir com APIs web
    que retornam dados em formato JSON.
    """

    def __init__(
        self,
        url: str,
        config: Optional[SourceConfig] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        auth_token: Optional[str] = None,
        auth_type: str = "Bearer",
    ) -> None:
        """Inicializa a fonte de dados de API web.

        Args:
            url: URL da API
            config: Configuração da fonte de dados
            headers: Cabeçalhos HTTP
            timeout: Tempo limite em segundos
            auth_token: Token de autenticação
            auth_type: Tipo de autenticação (Bearer, Basic, etc.)
        """
        headers = headers or {}

        # Adicionar token de autenticação se fornecido
        if auth_token:
            headers["Authorization"] = f"{auth_type} {auth_token}"

        # Adicionar cabeçalho de aceitação JSON se não especificado
        if "Accept" not in headers:
            headers["Accept"] = "application/json"

        super().__init__(url, config, headers, timeout)

    async def read(
        self,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """Lê dados da API web.

        Args:
            method: Método HTTP (GET, POST, etc.)
            params: Parâmetros da URL
            json_data: Dados JSON para enviar no corpo da requisição
            **kwargs: Argumentos adicionais para a requisição

        Returns:
            Dados JSON decodificados
        """
        # Adicionar dados JSON se fornecidos
        if json_data is not None:
            kwargs["json"] = json_data

            # Adicionar cabeçalho de conteúdo JSON se não especificado
            if "Content-Type" not in self.headers:
                self.headers["Content-Type"] = "application/json"

        content = await super().read(method, params, **kwargs)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON da API: {e}")
            # Logar o conteúdo para depuração
            self.logger.debug(
                f"Conteúdo recebido: {content.decode('utf-8', errors='replace')}"
            )
            raise
