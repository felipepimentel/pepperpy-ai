# Standardize Provider Plugin Imports

## Problem

The codebase has inconsistent import patterns for the `ProviderPlugin` class:

1. Some plugins use the direct import: `from pepperpy.plugin.plugin import ProviderPlugin`
2. Others use the re-export from the parent module: `from pepperpy.plugin import ProviderPlugin`

While both import patterns work (the parent module re-exports the class), using the direct import is more maintainable and explicit about the source of the class.

## Solution

Update all plugin files to use the direct import pattern:

```python
# Use this (preferred)
from pepperpy.plugin.plugin import ProviderPlugin

# Instead of this
from pepperpy.plugin import ProviderPlugin  # Less explicit
```

## Affected Files

The following files use the parent module import and should be updated:

```
plugins/rag/local/provider.py
plugins/agent/topology/teamwork/provider.py
plugins/embedding/openai/provider.py
plugins/embedding/azure/provider.py
plugins/llm/openai/provider.py
plugins/llm/local/provider.py
plugins/a2a/rest/provider.py
plugins/a2a/mock/provider.py
plugins/tts/murf/provider.py
plugins/tts/basic/provider.py
```

## Implementation Notes

1. When updating imports, also check for other potentially outdated patterns:
   - Initialization flag usage (`self.initialized` vs `self._initialized`)
   - Adapter class structure and method signatures
   - Message class structure and conversion methods

2. Update with care to avoid introducing new linter errors:
   - Some plugins may use unconventional patterns
   - Always test changes to ensure functionality is preserved

## Related Files

- `pepperpy/plugin/__init__.py`: Re-exports the ProviderPlugin class
- `pepperpy/plugin/plugin.py`: Contains the actual ProviderPlugin definition
- Documentation files that reference the import pattern

## Progress

- [x] Updated `plugins/communication/a2a/adapter.py`
- [x] Updated `plugins/communication/mcp/adapter.py`
- [x] Updated `plugins/llm/openai/provider.py` (import only, additional linter errors present)
- [ ] *Remaining files to be updated* 