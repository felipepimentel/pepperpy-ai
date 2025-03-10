"""
PepperPy RAG Pipeline Module.

This module provides pipeline functionality for the RAG system.
"""

# Define empty __all__ by default
__all__ = []

# Try to import pipeline components, but don't fail if dependencies are missing
try:
    from pepperpy.rag.pipeline.core import BasePipelineStage

    __all__ = [
        "BasePipelineStage",
    ]
except ImportError:
    pass
