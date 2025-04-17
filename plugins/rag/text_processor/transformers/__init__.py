"""Transformers text processor plugin for RAG.

This plugin provides Hugging Face Transformers-based text processing capabilities.
"""

from plugins.rag.text_processor.transformers.provider import TransformersProcessor

__all__ = ["TransformersProcessor"]
