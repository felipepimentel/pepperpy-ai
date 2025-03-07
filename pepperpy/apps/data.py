"""Aplicação para processamento de dados.

Este módulo define a classe DataApp, que fornece funcionalidades
para processamento de dados estruturados usando o framework PepperPy.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from pepperpy.apps.base import BaseApp


@dataclass
class DataResult:
    """Resultado de processamento de dados.

    Attributes:
        data: Dados processados
        parallels: Resultados de processamento paralelo (se houver)
        metadata: Metadados do processamento
    """

    data: Dict[str, Any]
    parallels: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class DataApp(BaseApp):
    """Aplicação para processamento de dados.

    Esta classe fornece funcionalidades para processamento de dados estruturados
    usando o framework PepperPy.

    Attributes:
        pipeline: Pipeline de processamento de dados
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inicializa a aplicação de processamento de dados.

        Args:
            name: Nome da aplicação
            description: Descrição da aplicação
            config: Configuração inicial da aplicação
        """
        super().__init__(name, description, config)
        self.pipeline = None

    async def process(
        self,
        data: Dict[str, Any],
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[Dict[str, Any], DataResult]:
        """Processa dados usando os passos especificados.

        Args:
            data: Dados a serem processados
            steps: Lista de passos a serem aplicados

        Returns:
            Dados processados ou resultado do processamento
        """
        await self.initialize()

        # Se passos foram especificados, criar pipeline temporário
        if steps:
            result = await self._process_with_steps(data, steps)
            return result

        # Se pipeline já foi configurado, usar
        if self.pipeline:
            result = await self._process_with_pipeline(data)
            return result

        # Caso contrário, usar configuração padrão
        return await self._process_with_default(data)

    async def process_data(self, data: Dict[str, Any]) -> DataResult:
        """Processa dados usando o pipeline configurado.

        Este método é um alias para process() que sempre retorna um DataResult.

        Args:
            data: Dados a serem processados

        Returns:
            Resultado do processamento
        """
        result = await self.process(data)

        # Converter resultado para DataResult se necessário
        if isinstance(result, dict):
            return DataResult(data=result)

        return result

    async def _process_with_steps(
        self,
        data: Dict[str, Any],
        steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Processa dados usando os passos especificados.

        Args:
            data: Dados a serem processados
            steps: Lista de passos a serem aplicados

        Returns:
            Dados processados
        """
        self.logger.debug(f"Processando dados com {len(steps)} passos")

        # Simular processamento de dados
        processed_data = data.copy()

        for step in steps:
            step_type = step.get("type", "")

            if step_type == "filter":
                # Simular filtragem de itens
                target = step.get("target", "items")
                condition = step.get("condition", "")

                if target in processed_data and isinstance(
                    processed_data[target], list
                ):
                    if "price > 50" in condition:
                        processed_data[target] = [
                            item
                            for item in processed_data[target]
                            if isinstance(item, dict) and item.get("price", 0) > 50
                        ]

            elif step_type == "aggregate":
                # Simular agregação
                operation = step.get("operation", "")
                source = step.get("source", "")
                target = step.get("target", "")

                if operation == "sum" and "items.price" in source:
                    processed_data[target] = sum(
                        item.get("price", 0)
                        for item in processed_data.get("items", [])
                        if isinstance(item, dict)
                    )

                elif operation == "average" and "items.price" in source:
                    items = processed_data.get("items", [])
                    if items:
                        processed_data[target] = sum(
                            item.get("price", 0)
                            for item in items
                            if isinstance(item, dict)
                        ) / len(items)
                    else:
                        processed_data[target] = 0

            elif step_type == "template":
                # Simular formatação com template
                template_file = step.get("template_file", "")
                output = step.get("output", "")

                # Simular template
                if "report" in output:
                    customer = processed_data.get("customer", "")
                    items = processed_data.get("items", [])
                    total = processed_data.get("total", 0)
                    average = processed_data.get("average", 0)

                    report = f"Relatório para {customer}\n"
                    report += f"Total de itens: {len(items)}\n"
                    report += f"Valor total: R${total:.2f}\n"
                    report += f"Valor médio: R${average:.2f}\n\n"
                    report += "Itens:\n"

                    for item in items:
                        if isinstance(item, dict):
                            report += f"- {item.get('name', '')}: R${item.get('price', 0):.2f}\n"

                    processed_data[output] = report

        return processed_data

    async def _process_with_pipeline(self, data: Dict[str, Any]) -> DataResult:
        """Processa dados usando o pipeline configurado.

        Args:
            data: Dados a serem processados

        Returns:
            Resultado do processamento
        """
        self.logger.debug("Processando dados com pipeline configurado")

        # Simular processamento com pipeline
        # Em uma implementação real, isso usaria o pipeline configurado

        # Filtrar itens com preço > 50
        filtered_items = [
            item
            for item in data.get("items", [])
            if isinstance(item, dict) and item.get("price", 0) > 50
        ]

        # Simular resultado com processamento paralelo
        expensive_items = [
            item for item in filtered_items if item.get("price", 0) > 100
        ]

        cheap_items = [item for item in filtered_items if item.get("price", 0) <= 100]

        # Criar resultado
        result = DataResult(
            data={"items": filtered_items, "customer": data.get("customer", "")},
            parallels=[
                {
                    "expensive_count": len(expensive_items),
                    "expensive_total": sum(
                        item.get("price", 0) for item in expensive_items
                    ),
                },
                {
                    "cheap_count": len(cheap_items),
                    "cheap_total": sum(item.get("price", 0) for item in cheap_items),
                },
            ],
            metadata={"processing_time": 0.1},
        )

        return result

    async def _process_with_default(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa dados usando configuração padrão.

        Args:
            data: Dados a serem processados

        Returns:
            Dados processados
        """
        self.logger.debug("Processando dados com configuração padrão")

        # Processamento padrão: copiar dados
        return data.copy()
