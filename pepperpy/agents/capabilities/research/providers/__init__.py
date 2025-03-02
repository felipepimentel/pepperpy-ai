"""Research capability providers.

This module provides providers for research capabilities.
"""

from pepperpy.agents.capabilities.research.providers.base import BaseResearchProvider
from pepperpy.agents.capabilities.research.providers.registry import (
    get_research_provider_class,
    register_research_provider_class,
)
from pepperpy.agents.capabilities.research.providers.types import (
    ResearchResult,
    Source,
    SourceType,
)

__all__ = [
    "BaseResearchProvider",
    "ResearchResult",
    "Source",
    "SourceType",
    "get_research_provider_class",
    "register_research_provider_class",
]
