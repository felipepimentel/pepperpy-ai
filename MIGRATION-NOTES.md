# Communication Module Migration

## Issue

We're refactoring the A2A and MCP protocols from being directly in the core modules:
- `pepperpy/a2a/`
- `pepperpy/mcp/`

To a proper plugin architecture under the communication domain:
- `pepperpy/communication/` (core abstractions)
- `plugins/communication/` (implementations)

## Our Approach

Rather than abruptly removing the old code, we're taking a gradual approach:

1. **Build the new structure** ✅
   - Create core abstractions in `pepperpy/communication/`
   - Implement plugins in `plugins/communication/`

2. **Create compatibility layer** ✅
   - Add compatibility shims in old modules
   - Include deprecation warnings
   - Forward calls to new implementations

3. **Document migration path** ✅
   - Clear instructions for updating imports
   - Examples of converting from old to new APIs
   - Timeline for deprecation and removal

4. **Gradually phase out old code**
   - Move remaining unique functionality (simulation, testing)
   - Remove redundant code in next major version

## Why This Approach?

1. **Zero breaking changes** - Existing code continues to work
2. **Clear migration path** - Developers understand how to update
3. **Clean architecture** - Properly separates framework from implementations
4. **Future extensibility** - New protocols can be added as plugins

## For Developers

- For new code, always use `pepperpy.communication`
- Update existing code during normal maintenance cycles
- Follow migration instructions in `.cursor/tasks/003-communication-migration.md`

## Timeline

- **Current**: Compatibility layer in place
- **Next minor release**: Formal deprecation notices
- **Next major release**: Complete removal of old modules 