"""Provedores de integração com serviços externos

Este módulo implementa os provedores que integram o framework com serviços externos,
incluindo:

- Provedores de IA e LLMs
  - OpenAI
  - Anthropic
  - Google
  - Outros

- Provedores de Nuvem
  - AWS
  - Azure
  - GCP
  - Outros

- Provedores de Síntese
  - Text-to-Speech
  - Image Generation
  - Video Synthesis
  - Outros

- Provedores de Transcrição
  - Speech-to-Text
  - OCR
  - Video Analysis
  - Outros

O módulo de provedores é fundamental para:
- Abstrair integrações externas
- Padronizar interfaces
- Gerenciar credenciais
- Otimizar custos
- Garantir resiliência
"""

from typing import Dict, List, Optional, Union

__version__ = "0.1.0"
__all__ = []  # Will be populated as implementations are added
