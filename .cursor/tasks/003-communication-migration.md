# Communication Migration Plan

## Overview

This document outlines the migration plan for moving A2A and MCP protocols from their original locations in the `pepperpy` package to the new `pepperpy.communication` domain.

## Current Status

1. **New Architecture**
   - Created `pepperpy/communication/base.py` with interfaces and message types
   - Created `pepperpy/communication/__init__.py` exporting the public API
   - Implemented `pepperpy/communication/compat.py` for backward compatibility

2. **Plugin Implementations**
   - Moved implementations to plugins:
     - `plugins/communication/a2a/rest/` - A2A REST implementation
     - `plugins/communication/a2a/adapter.py` - A2A adapter
     - `plugins/communication/mcp/adapter.py` - MCP adapter

3. **Compatibility Layer**
   - Added deprecation warnings to old modules
   - Created compatibility shims for:
     - `pepperpy.a2a.create_provider` → `pepperpy.communication.create_provider`
     - `pepperpy.mcp.create_client` → `pepperpy.communication.create_provider`
     - `pepperpy.mcp.create_server` → `pepperpy.communication.create_provider`

## Files to Remove

The following files are now redundant and should be phased out:

### Phase 1 (After Communication Domain is Stable)

1. **A2A Files to Remove**
   - `pepperpy/a2a/base.py` (move critical types to communication)
   - `pepperpy/a2a/providers/` (move implementations to plugins)

2. **MCP Files to Remove**
   - `pepperpy/mcp/base.py`
   - `pepperpy/mcp/client/`
   - `pepperpy/mcp/server/`
   - `pepperpy/mcp/protocol.py` (move critical types to communication)

### Phase 2 (Complete Removal - Next Major Version)

1. Remove compatibility shims
   - `pepperpy/a2a/__init__.py`
   - `pepperpy/mcp/__init__.py`
   - `pepperpy/communication/compat.py`

2. Remove entire modules
   - `pepperpy/a2a/`
   - `pepperpy/mcp/`

## Migration Instructions for Users

### For Applications Using A2A

```python
# Old imports (deprecated)
from pepperpy.a2a import create_provider, AgentCard, Message

# New imports
from pepperpy.communication import create_provider, CommunicationProtocol
from pepperpy.communication import Message, TextPart, DataPart

# Old usage
provider = await create_provider("rest", base_url="...")

# New usage
provider = await create_provider(
    protocol=CommunicationProtocol.A2A,
    provider_type="rest",
    base_url="..."
)
```

### For Applications Using MCP

```python
# Old imports (deprecated)
from pepperpy.mcp import create_client, MCPRequest

# New imports
from pepperpy.communication import create_provider, CommunicationProtocol
from pepperpy.communication import Message, TextPart, DataPart

# Old usage
client = await create_client("http", base_url="...")

# New usage
client = await create_provider(
    protocol=CommunicationProtocol.MCP,
    provider_type="http",
    base_url="..."
)
```

## Timelines

1. **Now**
   - Start using `pepperpy.communication` in all new code
   - Update existing code to use the new module in normal maintenance cycles

2. **Next Minor Release**
   - Mark old modules as formally deprecated in docs
   - Ensure all public APIs use `pepperpy.communication` internally

3. **Next Major Release**
   - Remove deprecated modules completely 