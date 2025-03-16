## Task: Restructure PepperPy Library

**Progress: 95%**

### Overview

This task involves restructuring the PepperPy library to improve its organization, reduce redundancy, and enhance maintainability. The restructuring will be done in phases, focusing on different aspects of the codebase.

### Phase 1: Core Functionality Consolidation

1. ✅ Fix linter errors in the codebase
   - Fixed linter errors in pepperpy/infra directory
   - Fixed linter errors in pepperpy/core directory
   - Fixed type errors in pepperpy/core/batching.py
   - Fixed import conflicts in pepperpy/core/__init__.py
   - Fixed type errors in pepperpy/core/errors.py using proper type casting
   - Fixed type errors in pepperpy/rag/document/loaders.py

2. ✅ Consolidate registry functionality
   - Updated pepperpy/core/registry.py to include all registry functionality
   - Created a unified registry system with Registry, TypeRegistry, and ProviderRegistry classes
   - Created pepperpy/llm/registry.py using the consolidated registry system
   - Updated pepperpy/providers/registry.py to use the consolidated registry system

3. ✅ Reorganize provider interfaces
   - Created a unified provider interface system in pepperpy/core/providers.py
   - Defined base Provider, RESTProvider, and StorageProvider interfaces
   - Updated pepperpy/providers/base.py to use the new interfaces
   - Updated pepperpy/llm/core.py to use the new provider interfaces

4. ✅ Standardize error handling
   - Created a unified error hierarchy in pepperpy/core/errors.py
   - Updated all modules to use the new error classes
   - Ensured consistent error handling across the codebase

5. ✅ Remove deprecated code and compatibility layers
   - Removed deprecated load_and_split methods from document loaders
   - Fixed inconsistencies in RAGPipelineConfig
   - Removed backward compatibility aliases in pepperpy/providers/base.py
   - Updated pepperpy/data/public.py to use the new error classes
   - Updated docstrings to reflect the removal of backward compatibility
   - Verified no linter errors in modified files

### Phase 2: Module Reorganization

1. ⬜ Reorganize LLM module
   - Consolidate LLM provider implementations
   - Standardize LLM interfaces

2. ⬜ Reorganize RAG module
   - Consolidate RAG components
   - Standardize RAG interfaces

3. ⬜ Reorganize workflow module
   - Consolidate workflow components
   - Standardize workflow interfaces

### Phase 3: API Refinement

1. ⬜ Define public API
   - Identify and document public interfaces
   - Create stable API entry points

2. ⬜ Create comprehensive examples
   - Update examples to use new structure
   - Ensure examples cover all major functionality

3. ⬜ Update documentation
   - Update API documentation
   - Create migration guide for users

### Notes

- No need for backward compatibility as the library is still in development
- Each phase should be completed before moving to the next
- Tests should be updated to reflect the new structure
- Documentation should be updated as changes are made 