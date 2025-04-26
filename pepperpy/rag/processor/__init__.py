"""Text processing for RAG."""

from typing import Any, Dict, List, Optional, TypeVar, Type, Union

from pepperpy.core.config import ConfigManager
from pepperpy.core.errors import DomainError
from .base import ProcessedText, ProcessingOptions, TextProcessor, TextProcessingError

T = TypeVar('T', bound=TextProcessor)

__all__ = [
    "ProcessedText",
    "ProcessingOptions",
    "TextProcessor",
    "TextProcessingError",
    "create_processor",
]

def create_processor(
    processor_type: Optional[str] = None, 
    **kwargs: Any
) -> TextProcessor:
    """Create a text processor instance.
    
    Args:
        processor_type: Type of processor to create ('spacy', 'nltk', 'transformers')
        **kwargs: Additional configuration parameters
        
    Returns:
        Initialized processor instance
        
    Raises:
        DomainError: If processor type is unknown or cannot be created
    """
    config_manager = ConfigManager()
    
    # If no processor type is specified, try to find the default from config
    if processor_type is None:
        default_processor = None
        for processor_key in ["rag.processor.spacy", "rag.processor.nltk", "rag.processor.transformers"]:
            config = config_manager.get_plugin_config(processor_key)
            if config and config.get("default_processor", False):
                if processor_key == "rag.processor.spacy":
                    default_processor = "spacy"
                elif processor_key == "rag.processor.nltk":
                    default_processor = "nltk"
                elif processor_key == "rag.processor.transformers":
                    default_processor = "transformers"
                break
        
        # If no default processor is configured, use SpaCy as the default
        processor_type = default_processor or "spacy"
    
    # Import processor based on type
    try:
        if processor_type.lower() == "spacy":
            from plugins.rag.spacy import SpacyProcessor
            return SpacyProcessor(**kwargs)
        elif processor_type.lower() == "nltk":
            from plugins.rag.nltk import NLTKProcessor
            return NLTKProcessor(**kwargs)
        elif processor_type.lower() == "transformers":
            from plugins.rag.transformers import TransformersProcessor
            return TransformersProcessor(**kwargs)
        else:
            raise DomainError(f"Unknown processor type: {processor_type}")
    except ImportError as e:
        raise DomainError(f"Failed to import processor {processor_type}: {e}") from e
    except Exception as e:
        raise DomainError(f"Failed to create processor {processor_type}: {e}") from e 