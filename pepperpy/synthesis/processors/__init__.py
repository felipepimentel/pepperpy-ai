"""Processadores para síntese de conteúdo.

Este módulo implementa processadores especializados para síntese de conteúdo,
incluindo:

- Processamento de Texto
  - Tokenização
  - Normalização
  - Formatação
  - Estilização

- Processamento de Áudio
  - Normalização
  - Filtragem
  - Efeitos
  - Mixagem

- Processamento de Imagem
  - Redimensionamento
  - Filtros
  - Composição
  - Otimização

O módulo fornece:
- Interfaces padronizadas
- Configuração flexível
- Pipeline modular
- Extensibilidade
"""

from typing import Dict, List, Optional, Union

from .audio import AudioProcessor
from .image import ImageProcessor
from .text import TextProcessor

__version__ = "0.1.0"
__all__ = [
    "AudioProcessor",
    "ImageProcessor",
    "TextProcessor",
]
