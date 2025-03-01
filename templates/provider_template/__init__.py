"""
Provider module for {domain_name}.

This module provides implementations of {domain_name} providers for the PepperPy framework.
"""

from pepperpy.providers.{domain_name}.base import Base{domain_class}Provider

# Import specific provider implementations
# from pepperpy.providers.{domain_name}.specific_provider import SpecificProvider

__all__ = [
    "Base{domain_class}Provider",
    # "SpecificProvider",
]
