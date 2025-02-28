"""
COMPATIBILITY STUB: This module has been moved to pepperpy.providers.llm.anthropic
This stub exists for backward compatibility and will be removed in a future version.
"""

import warnings
import importlib

warnings.warn(
    "The module pepperpy.llm.providers.anthropic has been moved to pepperpy.providers.llm.anthropic. "
    "Please update your imports. This stub will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Import the module from the new location
_module = importlib.import_module("pepperpy.providers.llm.anthropic")

# Copy all attributes from the imported module to this module's namespace
for _attr in dir(_module):
    if not _attr.startswith("_"):
        globals()[_attr] = getattr(_module, _attr)
