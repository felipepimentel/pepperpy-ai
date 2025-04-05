"""
RAG processor plugin implementations.

This module contains implementations of different text processors for RAG pipelines.
"""

# Import the plugin base classes
from pepperpy.plugin.rag.base import (
    ProcessedText,
    ProcessingOptions,
    TextProcessingError,
    TextProcessor,
)

# Register processors as plugins
from pepperpy.plugin.registry import register_plugin

# Import concrete implementations
from plugins.rag.nltk import NLTKProcessor
from plugins.rag.spacy import SpacyProcessor
from plugins.rag.transformers import TransformersProcessor

# Register the processors - the global version takes just name and plugin
register_plugin("rag.nltk", NLTKProcessor)
register_plugin("rag.spacy", SpacyProcessor)
register_plugin("rag.transformers", TransformersProcessor)

__all__ = [
    "NLTKProcessor",
    "ProcessedText",
    "ProcessingOptions",
    "SpacyProcessor",
    "TextProcessingError",
    "TextProcessor",
    "TransformersProcessor",
]
