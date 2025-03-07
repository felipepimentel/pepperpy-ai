"""Fonte de dados RSS.

Este módulo define a classe RSSSource, que fornece funcionalidades
para acessar feeds RSS como fonte de dados para aplicações PepperPy.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from pepperpy.core.sources.base import BaseSource, SourceConfig


class RSSSource(BaseSource):
    """Fonte de dados RSS.

    Esta classe fornece funcionalidades para acessar feeds RSS
    como fonte de dados para aplicações PepperPy.
    """

    def __init__(
        self,
        url: str,
        config: Optional[SourceConfig] = None,
        max_items: int = 10,
    ) -> None:
        """Inicializa a fonte de dados RSS.

        Args:
            url: URL do feed RSS
            config: Configuração da fonte de dados
            max_items: Número máximo de itens a buscar por padrão
        """
        if config is None:
            config = SourceConfig(name=f"rss_{url.split('//')[1].split('/')[0]}")

        super().__init__(config)

        self.url = url
        self.max_items = max_items

    async def read(
        self, max_items: Optional[int] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        """Lê dados do feed RSS.

        Args:
            max_items: Número máximo de itens a buscar (sobrescreve o valor padrão)
            **kwargs: Argumentos adicionais

        Returns:
            Lista de itens do feed
        """
        await self.initialize()

        # Usar o valor padrão se não especificado
        if max_items is None:
            max_items = self.max_items

        self.logger.debug(f"Buscando feed RSS: {self.url} (max_items: {max_items})")

        # Em uma implementação real, aqui seria feita a busca no feed RSS
        # Para este exemplo, vamos simular
        await asyncio.sleep(0.5)  # Simular tempo de busca

        items = []
        for i in range(max_items):
            items.append({
                "title": f"Notícia {i + 1}",
                "link": f"https://example.com/news/{i + 1}",
                "description": f"Descrição da notícia {i + 1}. Este é um texto simulado para demonstrar o processamento de feeds RSS.",
                "pubDate": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
                "guid": f"https://example.com/news/{i + 1}",
            })

        return items

    def __str__(self) -> str:
        """Retorna uma representação em string da fonte de dados."""
        return f"RSSSource(url='{self.url}')"
