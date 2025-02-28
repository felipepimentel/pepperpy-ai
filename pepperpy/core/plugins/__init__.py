"""Plugin system for PepperPy.

This module provides a plugin architecture for the PepperPy framework:
- Plugin discovery: Automatically discover and load plugins
- Extension points: Define extension points for plugins to hook into
- Plugin management: Register, enable, disable, and configure plugins
- Plugin isolation: Isolate plugins to prevent conflicts

The plugin system enables the framework to be extended with new functionality
without modifying the core codebase, facilitating modularity and customization.
"""

# Export public API
__all__ = []
