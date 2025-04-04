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
    AgentTask,
    # Fluent API (anteriormente em core/fluent.py)
    Analysis,
    # Enums
    AnalysisLevel,
    AnalysisScope,
    AnalysisType,
    # Enhancers
    BestPracticesEnhancer,
    ChatSession,
    ConversationTask,
    DeepContextEnhancer,
    Enhancer,
    EnhancerProxy,
    FluentBase,
    # Core classes
    GitRepository,
    HistoricalTrendsEnhancer,
    # Results (anteriormente em core/results.py)
    JSONResult,
    KnowledgeBase,
    KnowledgeTask,
    Logger,
    MemoryResult,
    PepperPy,
    PepperResult,
    PepperResultError,
    PerformanceEnhancer,
    Processor,
    RepositoryAnalysis,
    Result,
    SecurityEnhancer,
    TextResult,
    # Decorators
    code_analysis,
    enhancer,
    event_handler,
    on_analysis_complete,
    repository_task,
)

# Plugin API
from .plugins.plugin import PepperpyPlugin
from .plugins.registry import get_plugin
