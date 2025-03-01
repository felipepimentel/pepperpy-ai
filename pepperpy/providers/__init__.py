"""Deprecated: Providers have been moved to domain-specific directories

This module is maintained for backward compatibility only.
Please update your imports to use the domain-specific providers:

- from pepperpy.multimodal.audio.providers import ...
- from pepperpy.multimodal.vision.providers import ...
- from pepperpy.agents.providers import ...
- from pepperpy.storage.providers import ...
- from pepperpy.cloud.providers import ...
- from pepperpy.core.config.providers import ...
- from pepperpy.embedding.providers import ...
- from pepperpy.llm.providers import ...

This module will be removed in a future version.
"""

# Import providers from their new locations for backward compatibility
from pepperpy.agents.providers import *
from pepperpy.cloud.providers import *
from pepperpy.core.config.providers import *
from pepperpy.embedding.providers import *
from pepperpy.llm.providers import *
from pepperpy.multimodal.audio.providers import *
from pepperpy.multimodal.vision.providers import *
from pepperpy.storage.providers import *

# Re-export all imported names
__all__ = []
