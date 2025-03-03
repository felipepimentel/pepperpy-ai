"""Efficient token management system for cost reduction

Implements strategies and mechanisms to optimize token usage in language models,
aiming to reduce operational costs while maintaining response quality.
"""

from pepperpy.optimization.base import TokenManager
from pepperpy.optimization.config import TokenConfig

__version__ = "0.1.0"
__all__ = ["TokenConfig", "TokenManager"]
