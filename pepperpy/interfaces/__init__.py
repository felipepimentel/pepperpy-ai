"""
Public Interfaces Package

This package provides stable public interfaces for the PepperPy framework.
These interfaces are guaranteed to be backward compatible across minor versions.

The public interfaces are organized by domain:
- core: Core framework functionality and base components
- capabilities: Domain-specific AI capabilities
- workflows: Workflow definition and execution
- embeddings: Vector embedding functionality
- llm: Language model integration
- providers: Service provider integrations
- rag: Retrieval Augmented Generation
- security: Security and authentication

Users of the framework should import from these interfaces rather than
directly from implementation modules to ensure compatibility with future versions.
"""

# Import all public interfaces
from .capabilities import *
from .core import *
from .embeddings import *
from .llm import *
from .providers import *
from .rag import *
from .security import *
from .workflows import *
