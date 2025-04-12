# Communication Domain Refactoring

## Summary

This task refactors the A2A and MCP protocols from being directly in the core `pepperpy` module to a proper plugin architecture under the `communication` domain.

## Motivation

The current architecture had several issues:
- A2A and MCP were improperly placed at the root level of `pepperpy`
- Implementation details were mixed with abstractions
- No clear `communication` domain existed to organize different protocols
- Future protocols (e.g., from Amazon) wouldn't have a natural home

## Implemented Changes

1. **Created Communication Domain Abstraction**
   - Added `pepperpy/communication/base.py` with proper interfaces
   - Added `pepperpy/communication/__init__.py` exporting public API
   - Defined fundamental message types and communication interfaces
   - Created `pepperpy/communication/compat.py` for backward compatibility

2. **Created Plugin Structure for Protocols**
   - Set up `plugins/communication/a2a/` and `plugins/communication/mcp/`
   - Implemented proper plugin directory structure
   - Created `plugin.yaml` files for each implementation

3. **Implemented A2A Provider and Adapter**
   - Moved A2A REST implementation to `plugins/communication/a2a/rest/`
   - Created A2A adapter in `plugins/communication/a2a/adapter.py`
   - Ensured proper plugin configuration in `plugin.yaml`

4. **Implemented MCP Provider and Adapter**
   - Moved MCP implementation to `plugins/communication/mcp/`
   - Updated MCP adapter in `plugins/communication/mcp/adapter.py`
   - Created proper plugin configuration in `plugin.yaml`

5. **Handled Legacy Code Compatibility**
   - Added deprecation warnings to old modules
   - Created compatibility shims that redirect to new implementations
   - Documented migration path for complete removal in the future

## Benefits

1. **Cleaner Architecture**
   - Clear separation between the framework and implementations
   - Proper domain-based organization
   - Future protocols can be added as plugins

2. **Plugin-Based Extensibility**
   - Third-party developers can add new protocols without modifying core code
   - Users can easily select which protocol implementations to use

3. **Consistent Interface**
   - All communication implements the same interface
   - Applications can switch protocols without code changes

4. **Safe Migration Path**
   - Existing code continues to work with deprecation warnings
   - Clear documentation on how to update to the new APIs
   - Phased approach to eventual removal of old modules

## Migration Path

Applications currently using A2A or MCP should:

1. Update imports from:
   ```python
   from pepperpy.a2a import ...
   from pepperpy.mcp import ...
   ```
   
   To:
   ```python
   from pepperpy.communication import create_provider, CommunicationProtocol, Message
   
   # Use the protocol adapter via the Communication API
   provider = await create_provider(CommunicationProtocol.A2A)
   # OR
   provider = await create_provider(CommunicationProtocol.MCP)
   ```

2. Adapt any direct usage of protocol-specific classes
   - Use the `Message` class from `pepperpy.communication`
   - Replace protocol-specific message parts with generic ones

## Legacy Code Handling

The legacy code is being handled in three phases:

1. **Phase 1 (Current)**: Implement compatibility shims
   - Old modules now import from and redirect to new implementations
   - Deprecation warnings encourage users to switch to new APIs
   - No functionality is lost, everything continues to work

2. **Phase 2**: Move remaining functionality
   - Move simulation and testing code to proper locations
   - Ensure all features from old modules are available in new structure

3. **Phase 3**: Complete removal
   - Remove old modules in a future major version
   - All code should use the new APIs by then

See the detailed migration plan in [003-communication-migration.md](003-communication-migration.md).

## Future Improvements

1. Complete moving implementations out of core:
   - Finish refactoring `pepperpy/a2a`
   - Finish refactoring `pepperpy/mcp`
   - Update any direct references to these modules

2. Add more providers and protocols:
   - Native WebSocket provider for real-time communication
   - Simple HTTP provider for basic REST communication
   - File-based provider for local testing 