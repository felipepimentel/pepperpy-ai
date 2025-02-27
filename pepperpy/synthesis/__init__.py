"""Módulo para síntese de conteúdo multimodal.

Este módulo implementa funcionalidades para síntese de diferentes tipos de conteúdo,
incluindo:

- Síntese de Texto
  - Geração de texto
  - Resumos
  - Paráfrases
  - Traduções

- Síntese de Voz
  - Text-to-Speech
  - Clonagem de voz
  - Prosódia e emoção
  - Múltiplos idiomas

- Síntese de Imagem
  - Text-to-Image
  - Edição e manipulação
  - Estilos e filtros
  - Composição

- Síntese de Vídeo
  - Animações
  - Avatares
  - Efeitos
  - Renderização

Este módulo é diferente do processamento em multimodal/
pois é focado em:
- Gerar novo conteúdo
- Aplicar transformações criativas
- Produzir saídas de alta qualidade
- Personalizar resultados

O módulo fornece:
- Interfaces unificadas
- Pipeline modular
- Otimizações específicas
- Controle de qualidade
"""

from typing import Dict, List, Optional, Union

from .generators import AudioGenerator, ImageGenerator, TextGenerator
from .optimizers import AudioOptimizer, ImageOptimizer, TextOptimizer
from .processors import AudioProcessor, ImageProcessor, TextProcessor

__version__ = "0.1.0"
__all__ = [
    # Processors
    "AudioProcessor",
    "ImageProcessor",
    "TextProcessor",
    # Generators
    "AudioGenerator",
    "ImageGenerator",
    "TextGenerator",
    # Optimizers
    "AudioOptimizer",
    "ImageOptimizer",
    "TextOptimizer",
]
