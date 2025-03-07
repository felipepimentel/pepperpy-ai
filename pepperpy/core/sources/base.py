"""Classes base para fontes de dados.

Este módulo define as classes base para todas as fontes de dados
do framework PepperPy.
"""

import abc
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SourceConfig:
    """Configuração para fontes de dados.

    Attributes:
        name: Nome da fonte de dados
        description: Descrição da fonte de dados
        metadata: Metadados adicionais
    """

    name: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseSource(abc.ABC):
    """Classe base para todas as fontes de dados.

    Esta classe define a interface comum para todas as fontes de dados
    do framework PepperPy.
    """

    def __init__(
        self,
        config: Optional[SourceConfig] = None,
    ) -> None:
        """Inicializa a fonte de dados.

        Args:
            config: Configuração da fonte de dados
        """
        self.config = config or SourceConfig(name="unnamed_source")
        self.logger = logging.getLogger(f"pepperpy.sources.{self.config.name}")
        self._initialized = False

    async def initialize(self) -> None:
        """Inicializa a fonte de dados.

        Este método deve ser chamado antes de usar a fonte de dados.
        Implementações podem sobrescrever este método para realizar
        inicialização específica.
        """
        if not self._initialized:
            self.logger.debug(f"Inicializando fonte de dados: {self.config.name}")
            await self._initialize()
            self._initialized = True

    async def _initialize(self) -> None:
        """Implementação específica da inicialização.

        Este método deve ser sobrescrito por classes derivadas para
        realizar inicialização específica.
        """
        pass

    @abc.abstractmethod
    async def read(self, **kwargs) -> Any:
        """Lê dados da fonte.

        Args:
            **kwargs: Argumentos específicos da fonte

        Returns:
            Dados lidos da fonte
        """
        pass

    async def write(self, data: Any, **kwargs) -> None:
        """Escreve dados na fonte.

        Args:
            data: Dados a serem escritos
            **kwargs: Argumentos específicos da fonte

        Raises:
            NotImplementedError: Se a fonte não suporta escrita
        """
        raise NotImplementedError("Esta fonte de dados não suporta escrita")

    async def close(self) -> None:
        """Fecha a fonte de dados e libera recursos.

        Este método deve ser chamado quando a fonte não for mais necessária.
        Implementações podem sobrescrever este método para realizar
        limpeza específica.
        """
        self.logger.debug(f"Fechando fonte de dados: {self.config.name}")
        await self._close()
        self._initialized = False

    async def _close(self) -> None:
        """Implementação específica do fechamento.

        Este método deve ser sobrescrito por classes derivadas para
        realizar limpeza específica.
        """
        pass

    async def __aenter__(self) -> "BaseSource":
        """Suporte para uso com 'async with'.

        Returns:
            A própria fonte de dados
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Suporte para uso com 'async with'.

        Args:
            exc_type: Tipo da exceção, se ocorreu
            exc_val: Valor da exceção, se ocorreu
            exc_tb: Traceback da exceção, se ocorreu
        """
        await self.close()
