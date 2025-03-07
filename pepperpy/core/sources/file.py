"""Fontes de dados baseadas em arquivos.

Este módulo define classes para acesso a dados em arquivos locais.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional, Union

from pepperpy.core.sources.base import BaseSource, SourceConfig


class FileSource(BaseSource):
    """Fonte de dados baseada em arquivo.

    Esta classe fornece funcionalidades para ler e escrever dados
    em arquivos locais.
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        config: Optional[SourceConfig] = None,
        mode: str = "r",
        encoding: str = "utf-8",
    ) -> None:
        """Inicializa a fonte de dados de arquivo.

        Args:
            file_path: Caminho para o arquivo
            config: Configuração da fonte de dados
            mode: Modo de abertura do arquivo
            encoding: Codificação do arquivo
        """
        if config is None:
            name = os.path.basename(str(file_path))
            config = SourceConfig(name=f"file_{name}")

        super().__init__(config)

        self.file_path = Path(file_path)
        self.mode = mode
        self.encoding = encoding
        self.file = None

    async def _initialize(self) -> None:
        """Inicializa a fonte de dados de arquivo.

        Verifica se o arquivo existe e pode ser acessado.
        """
        # Verificar se o diretório existe
        if self.mode.startswith("w") or self.mode.startswith("a"):
            os.makedirs(self.file_path.parent, exist_ok=True)

        # Verificar se o arquivo existe para leitura
        if self.mode.startswith("r") and not self.file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {self.file_path}")

    async def read(self, **kwargs) -> bytes:
        """Lê dados do arquivo.

        Args:
            **kwargs: Argumentos adicionais

        Returns:
            Conteúdo do arquivo como bytes
        """
        await self.initialize()

        # Verificar se o modo permite leitura
        if not any(c in self.mode for c in "r+"):
            raise IOError(
                f"Arquivo aberto em modo que não permite leitura: {self.mode}"
            )

        self.logger.debug(f"Lendo arquivo: {self.file_path}")

        # Ler arquivo de forma assíncrona
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, lambda: self.file_path.read_bytes())

        return content

    async def write(self, data: Union[str, bytes], **kwargs) -> None:
        """Escreve dados no arquivo.

        Args:
            data: Dados a serem escritos
            **kwargs: Argumentos adicionais
        """
        await self.initialize()

        # Verificar se o modo permite escrita
        if not any(c in self.mode for c in "wa+"):
            raise IOError(
                f"Arquivo aberto em modo que não permite escrita: {self.mode}"
            )

        self.logger.debug(f"Escrevendo no arquivo: {self.file_path}")

        # Converter para bytes se for string
        if isinstance(data, str):
            data = data.encode(self.encoding)

        # Escrever arquivo de forma assíncrona
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.file_path.write_bytes(data))


class TextFileSource(FileSource):
    """Fonte de dados baseada em arquivo de texto.

    Esta classe fornece funcionalidades para ler e escrever dados
    de texto em arquivos locais.
    """

    async def read(self, **kwargs) -> str:
        """Lê dados do arquivo de texto.

        Args:
            **kwargs: Argumentos adicionais

        Returns:
            Conteúdo do arquivo como string
        """
        content = await super().read(**kwargs)
        return content.decode(self.encoding)

    async def write(self, data: str, **kwargs) -> None:
        """Escreve dados no arquivo de texto.

        Args:
            data: Dados a serem escritos
            **kwargs: Argumentos adicionais
        """
        await super().write(data, **kwargs)


class JSONFileSource(TextFileSource):
    """Fonte de dados baseada em arquivo JSON.

    Esta classe fornece funcionalidades para ler e escrever dados
    JSON em arquivos locais.
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        config: Optional[SourceConfig] = None,
        mode: str = "r",
        encoding: str = "utf-8",
        indent: int = 2,
    ) -> None:
        """Inicializa a fonte de dados de arquivo JSON.

        Args:
            file_path: Caminho para o arquivo
            config: Configuração da fonte de dados
            mode: Modo de abertura do arquivo
            encoding: Codificação do arquivo
            indent: Indentação para escrita JSON
        """
        super().__init__(file_path, config, mode, encoding)
        self.indent = indent

    async def read(self, **kwargs) -> Any:
        """Lê dados do arquivo JSON.

        Args:
            **kwargs: Argumentos adicionais

        Returns:
            Dados JSON decodificados
        """
        content = await super().read(**kwargs)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON: {e}")
            raise

    async def write(self, data: Any, **kwargs) -> None:
        """Escreve dados no arquivo JSON.

        Args:
            data: Dados a serem escritos
            **kwargs: Argumentos adicionais
        """
        try:
            json_str = json.dumps(data, indent=self.indent, ensure_ascii=False)
            await super().write(json_str, **kwargs)
        except (TypeError, ValueError) as e:
            self.logger.error(f"Erro ao codificar JSON: {e}")
            raise
