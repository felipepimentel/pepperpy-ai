---
title: Validate Project Structure
version: "1.2"
scope: "Pepperpy Project"
description: |
  A tool for validating and maintaining project structure integrity.
  Use this prompt to:
  - Validate compliance with `.product/project_structure.yml`.
  - Propose and log changes to the architecture.
  - Prevent unapproved structural drift.
  - Maintain a consistent and scalable project organization.
---

## Current Project Structure

```plaintext
pepperpy/
├── __init__.py
├── py.typed
├── adapters/         # External system adapters
├── agents/          # Agent implementations
├── capabilities/    # Agent capabilities
├── cli/            # Command-line interface
├── core/           # Core functionality
├── hub/            # Asset management
├── memory/         # Memory systems
├── monitoring/     # Logging and metrics
├── providers/      # AI provider integrations
├── runtime/        # Runtime environment
├── search/         # Search functionality
└── tools/          # Utility tools

# Support Directories
.product/           # Project management
├── tasks/         # Task specifications
├── kanban.md      # Project tracking and status
└── architecture.mermaid  # Architecture diagrams

docs/              # Documentation
├── api_reference/
├── development/
└── user_guides/

tests/             # Test suite
├── unit/
├── integration/
└── e2e/

examples/          # Example code
scripts/           # Utility scripts
assets/            # Project assets
logs/              # Log files
.pepper_hub/       # Local AI assets
```

## Validation Rules

### 1. Core Package Structure
- All Python modules must be in `pepperpy/`
- Each module must have `__init__.py`
- All public modules must have type hints
- `py.typed` must be present in root package

### 2. Documentation
- API documentation in `docs/api_reference/`
- Development guides in `docs/development/`
- User guides in `docs/user_guides/`
- Each module must have README.md

### 3. Testing
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- E2E tests in `tests/e2e/`
- Test files must mirror package structure

### 4. Project Management
- Tasks in `.product/tasks/`
- Project tracking in `.product/kanban.md`
- Architecture in `.product/architecture.mermaid`

### 5. Examples and Scripts
- Example code in `examples/`
- Utility scripts in `scripts/`
- Each example must have documentation

### 6. Configuration
- Environment variables in `.env`
- Example config in `.env.example`
- Poetry config in `pyproject.toml`

### 7. Assets and Logs
- Project assets in `assets/`
- Log files in `logs/`
- AI assets in `.pepper_hub/`

## Validation Process

1. **Run Validation Script**  
   ```bash
   ./scripts/validate_structure.py
   ```

2. **Handle Discrepancies**  
   - Log unexpected items
   - Analyze issues
   - Propose solutions
   - Get approval for changes

3. **Update Documentation**  
   - Record changes in kanban.md
   - Update architecture diagrams
   - Revise documentation

4. **Revalidate**  
   - Run validation again
   - Confirm all issues resolved
   - Update kanban board

## Prohibited Actions
- Creating redundant directories
- Bypassing validation rules
- Modifying structure without approval
- Mixing test and source code
- Storing sensitive data in repo

---

### **Example Workflow**
- Validation Script Output:
- Unexpected item in pepperpy: data
- Missing optional path: pepperpy/providers/vector_store/implementations/milvus.py

- Suggested Actions:
1. Remove the redundant `data` directory (log the action and reasoning).
2. Add `milvus.py` under `pepperpy/providers/vector_store/implementations/` (log justification).

- User Confirmation Required:
- Await explicit approval for all proposed actions.

