"""
COMPATIBILITY STUB: This module has been moved to pepperpy.providers.llm.openrouter
This stub exists for backward compatibility and will be removed in a future version.
"""

import importlib
import warnings

warnings.warn(
    "The module pepperpy.llm.providers.openrouter has been moved to pepperpy.providers.llm.openrouter. "
    "Please update your imports. This stub will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Import the module from the new location
_module = importlib.import_module("pepperpy.providers.llm.openrouter")

# Copy all attributes from the imported module to this module's namespace
for _attr in dir(_module):
    if not _attr.startswith("_"):
        globals()[_attr] = getattr(_module, _attr)
