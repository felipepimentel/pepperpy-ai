"""Módulo de descoberta inteligente para PepperPy.

Este módulo fornece funcionalidades para detecção automática de tipos de conteúdo,
análise de intenção e descoberta de capacidades para o sistema de orquestração automática.
"""

from typing import Any, Dict, Optional, Union

from pepperpy.discovery.content_type import detect_content_type

__all__ = [
    "detect_content_type",
]
