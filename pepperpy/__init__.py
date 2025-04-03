"""
PepperPy Framework - Biblioteca declarativa para análise de código com IA.
"""

# Version information
__version__ = "0.3.0"

# Core framework
# Logging
# Registro de handlers e hooks registrados dinamicamente
# Este módulo deve ser carregado para registrar eles
# import pepperpy.hooks

from .core.logging import get_logger

# Factory functions - remover a importação do factory.py já que foi integrado ao pepperpy.py
# from .factory import (
#     create_agent,
#     create_content,
#     create_embeddings,
#     create_llm,
#     create_plugin,
#     create_rag,
#     create_storage,
#     create_tts,
#     create_workflow,
# )
from .pepperpy import (
    AnalysisLevel,
    AnalysisScope,
    # Enums
    AnalysisType,
    BestPracticesEnhancer,
    DeepContextEnhancer,
    # Enhancers
    Enhancer,
    GitRepository,
    HistoricalTrendsEnhancer,
    # Core classes
    PepperPy,
    PerformanceEnhancer,
    RepositoryAnalysis,
    Result,
    SecurityEnhancer,
    code_analysis,
    enhancer,
    event_handler,
    on_analysis_complete,
    # Decorators
    repository_task,
)

# Plugin API
from .plugins.plugin import PepperpyPlugin
from .plugins.registry import get_plugin
