"""Módulo de logging do PepperPy.

Este módulo fornece funções para configurar e obter loggers
para aplicações PepperPy.
"""

import logging
import os
import sys
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """Obtém um logger configurado.

    Args:
        name: Nome do logger

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Configurar logger se ainda não foi configurado
    if not logger.handlers:
        # Definir nível de log
        log_level = os.environ.get("PEPPERPY_LOG_LEVEL", "INFO")
        logger.setLevel(getattr(logging, log_level))

        # Criar handler para console
        handler = logging.StreamHandler(sys.stdout)

        # Definir formato
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # Adicionar handler ao logger
        logger.addHandler(handler)

    return logger


def configure_logging(
    level: str = "INFO",
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[str] = None,
) -> None:
    """Configura o logging global.

    Args:
        level: Nível de log
        format: Formato do log
        log_file: Caminho do arquivo de log
    """
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))

    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Criar formatter
    formatter = logging.Formatter(format)

    # Adicionar handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Adicionar handler para arquivo se especificado
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
