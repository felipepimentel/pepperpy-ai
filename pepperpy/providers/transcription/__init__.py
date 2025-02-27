"""Provedores para transcrição de áudio

Este módulo implementa integrações com provedores de transcrição,
fornecendo:

- Transcrição de Áudio (STT)
  - Fala para texto
  - Identificação de falantes
  - Detecção de idiomas
  - Pontuação automática

- Reconhecimento Ótico (OCR)
  - Documentos digitalizados
  - Imagens de texto
  - Formulários e tabelas
  - Múltiplos idiomas

- Análise de Vídeo
  - Extração de legendas
  - Reconhecimento de cenas
  - Detecção de objetos
  - Análise de sentimento

Provedores suportados:
- OpenAI Whisper
- Google Speech-to-Text
- Amazon Transcribe
- Microsoft Azure Speech
- Outros conforme necessário
"""

from typing import Dict, List, Optional, Union

__version__ = "0.1.0"
__all__ = []  # Will be populated as implementations are added
