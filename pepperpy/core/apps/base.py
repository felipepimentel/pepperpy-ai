"""Classe base para aplicações PepperPy.

Este módulo define a classe base para todas as aplicações PepperPy,
fornecendo funcionalidades comuns como configuração, logging e gerenciamento de estado.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.logging import get_logger


class BaseApp:
    """Classe base para aplicações PepperPy.

    Esta classe fornece funcionalidades comuns para todas as aplicações PepperPy,
    como configuração, logging e gerenciamento de estado.

    Attributes:
        name: Nome da aplicação
        config: Configuração da aplicação
        logger: Logger da aplicação
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inicializa a aplicação.

        Args:
            name: Nome da aplicação
            description: Descrição da aplicação
            config: Configuração inicial da aplicação
        """
        self.name = name
        self.description = description or f"Aplicação {name}"
        self.config = config or {}
        self.logger = get_logger(f"pepperpy.apps.{name}")
        self.output_path = None
        self._initialized = False

        # Carregar configurações de variáveis de ambiente
        self._load_env_config()

        self.logger.info(f"Aplicação {name} inicializada")

    def _load_env_config(self) -> None:
        """Carrega configurações de variáveis de ambiente."""
        env_prefix = f"PEPPERPY_{self.name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix) :].lower()
                self.config[config_key] = value
                self.logger.debug(f"Carregada configuração de ambiente: {config_key}")

    def configure(self, **kwargs: Any) -> "BaseApp":
        """Configura a aplicação.

        Args:
            **kwargs: Parâmetros de configuração

        Returns:
            A própria aplicação para encadeamento de métodos
        """
        self.config.update(kwargs)
        self.logger.debug(f"Configuração atualizada: {kwargs}")
        return self

    def set_output_path(self, path: Union[str, Path]) -> "BaseApp":
        """Define o caminho de saída para a aplicação.

        Args:
            path: Caminho de saída

        Returns:
            A própria aplicação para encadeamento de métodos
        """
        self.output_path = Path(path)
        # Criar diretório pai se não existir
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Caminho de saída definido: {self.output_path}")
        return self

    async def initialize(self) -> None:
        """Inicializa a aplicação.

        Este método deve ser chamado antes de usar a aplicação.
        Pode ser sobrescrito por subclasses para realizar inicialização específica.
        """
        if self._initialized:
            return

        self.logger.info(f"Inicializando aplicação {self.name}")
        self._initialized = True

    async def cleanup(self) -> None:
        """Limpa recursos da aplicação.

        Este método deve ser chamado quando a aplicação não for mais necessária.
        Pode ser sobrescrito por subclasses para realizar limpeza específica.
        """
        self.logger.info(f"Limpando recursos da aplicação {self.name}")

    def __repr__(self) -> str:
        """Retorna uma representação em string da aplicação."""
        return f"{self.__class__.__name__}(name='{self.name}')"
