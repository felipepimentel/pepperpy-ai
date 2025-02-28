"""
COMPATIBILITY STUB: This module has been moved to pepperpy.pepperpy-ai.pepperpy.workflows.core.manager
This stub exists for backward compatibility and will be removed in a future version.
"""

import warnings
import importlib

warnings.warn(
    f"The module /home/pimentel/Workspace/pepperpy/pepperpy-ai/pepperpy/workflow/core/manager.py has been moved to pepperpy.pepperpy-ai.pepperpy.workflows.core.manager. "
    f"Please update your imports. This stub will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Import the module from the new location
_module = importlib.import_module("pepperpy.pepperpy-ai.pepperpy.workflows.core.manager")

# Copy all attributes from the imported module to this module's namespace
for _attr in dir(_module):
    if not _attr.startswith("_"):
        globals()[_attr] = getattr(_module, _attr)
