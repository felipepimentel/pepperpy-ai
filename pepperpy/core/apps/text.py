"""Aplicação para processamento de texto.

Este módulo define a classe TextApp, que fornece funcionalidades
para processamento de texto usando o framework PepperPy.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.apps.base import BaseApp


@dataclass
class TextResult:
    """Resultado de processamento de texto.

    Attributes:
        text: Texto processado
        branches: Resultados de branches (se houver)
        metadata: Metadados do processamento
    """

    text: str
    branches: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TextApp(BaseApp):
    """Aplicação para processamento de texto.

    Esta classe fornece funcionalidades para processamento de texto
    usando o framework PepperPy.

    Attributes:
        pipeline: Pipeline de processamento de texto
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inicializa a aplicação de processamento de texto.

        Args:
            name: Nome da aplicação
            description: Descrição da aplicação
            config: Configuração inicial da aplicação
        """
        super().__init__(name, description, config)
        self.pipeline = None

    async def process(
        self,
        text: str,
        operations: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[str, TextResult]:
        """Processa um texto usando as operações especificadas.

        Args:
            text: Texto a ser processado
            operations: Lista de operações a serem aplicadas

        Returns:
            Texto processado ou resultado do processamento
        """
        await self.initialize()

        # Se operações foram especificadas, criar pipeline temporário
        if operations:
            result = await self._process_with_operations(text, operations)
            return result

        # Se pipeline já foi configurado, usar
        if self.pipeline:
            result = await self._process_with_pipeline(text)
            return result

        # Caso contrário, usar configuração padrão
        return await self._process_with_default(text)

    async def process_text(self, text: str) -> TextResult:
        """Processa um texto usando o pipeline configurado.

        Este método é um alias para process() que sempre retorna um TextResult.

        Args:
            text: Texto a ser processado

        Returns:
            Resultado do processamento
        """
        result = await self.process(text)

        # Converter resultado para TextResult se necessário
        if isinstance(result, str):
            return TextResult(text=result)

        return result

    async def _process_with_operations(
        self,
        text: str,
        operations: List[Dict[str, Any]],
    ) -> str:
        """Processa um texto usando as operações especificadas.

        Args:
            text: Texto a ser processado
            operations: Lista de operações a serem aplicadas

        Returns:
            Texto processado
        """
        self.logger.debug(f"Processando texto com {len(operations)} operações")

        # Simular processamento de texto
        processed_text = text

        for op in operations:
            op_type = op.get("type", "")

            if op_type == "strip":
                processed_text = processed_text.strip()
            elif op_type == "uppercase":
                processed_text = processed_text.upper()
            elif op_type == "lowercase":
                processed_text = processed_text.lower()
            elif op_type == "template":
                template = op.get("template", "{text}")
                processed_text = template.replace("{text}", processed_text)

        return processed_text

    async def _process_with_pipeline(self, text: str) -> TextResult:
        """Processa um texto usando o pipeline configurado.

        Args:
            text: Texto a ser processado

        Returns:
            Resultado do processamento
        """
        self.logger.debug("Processando texto com pipeline configurado")

        # Simular processamento com pipeline
        # Em uma implementação real, isso usaria o pipeline configurado

        # Simular resultado com branches
        result = TextResult(
            text=text.strip().upper(),
            branches=[
                f"Resultado: {text.strip().upper()}",
                f"{text.strip().upper()} (Contém {len(text.split())} palavras)",
            ],
            metadata={"processing_time": 0.1},
        )

        return result

    async def _process_with_default(self, text: str) -> str:
        """Processa um texto usando configuração padrão.

        Args:
            text: Texto a ser processado

        Returns:
            Texto processado
        """
        self.logger.debug("Processando texto com configuração padrão")

        # Processamento padrão: strip e uppercase
        return text.strip().upper()
