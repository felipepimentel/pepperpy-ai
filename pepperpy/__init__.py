"""
@file: __init__.py
@purpose: Package initialization and version
@component: Core
@created: 2024-03-20
@task: TASK-001
@status: active
"""

from pepperpy.common.config import config, get_config, initialize_config

__version__ = "0.1.0"
__author__ = "Felipe Pimentel"
__email__ = "felipe.pimentel@gmail.com"

__all__ = [
    "config",
    "get_config",
    "initialize_config",
]
