# Check Resolution Strategy

## Overview
This document describes a consolidated approach for identifying and resolving linting, type-checking, and test-related issues in the Pepperpy project. All relevant tool configurations (including lint rules, formatting, testing, type checking, and extras) reside in a single **`pyproject.toml`** file. Any additions or changes should be made directly in this file, ensuring the entire team follows a uniform configuration.

## Resolution Process

### 1. Initial Check
Run the primary check script to see the current status of lint, type checks, and tests:
```bash
./scripts/check.sh
```

### 2. Categorize Issues by Priority

1. **Critical**
   - Security vulnerabilities  
   - Missing/incorrect module imports  
   - Syntax or parsing errors  
   - Fatal type checker failures

2. **High**
   - Missing or incorrect type annotations  
   - Unused imports or variables  
   - Missing essential docstrings

3. **Medium**
   - Code formatting violations (line length, import sorting)  
   - Partial docstring or annotation inconsistencies  
   - Non-urgent style refinements

4. **Low**
   - Cosmetic improvements  
   - Performance tweaks  
   - Minor documentation clarifications

### 3. Resolution Order

1. **Module & Dependencies**
   - Update import paths and structures  
   - Manage optional/extra dependencies as defined in `pyproject.toml`  
   - Apply overrides (`ignore_missing_imports`) for optional modules

2. **Type System**
   - Add or correct annotations  
   - Resolve generics and protocol mismatches  
   - Reference Mypy overrides in `pyproject.toml` for modules lacking stubs

3. **Code & Architecture**
   - Ensure function signatures align with usage  
   - Fix or refine class attributes  
   - Resolve inheritance or interface issues

4. **Documentation**
   - Add or update docstrings  
   - Align doc comments with type hints  
   - Fix stale examples and references

### 4. Verification Steps

1. **Re-run checks**:
   ```bash
   ./scripts/check.sh
   ```
2. **Ensure**:
   - No regression or newly introduced errors  
   - Tests pass without failures  
   - Type checks are successful  
   - Lint warnings are resolved

3. **Document**:
   - Note open issues requiring architectural changes  
   - Indicate problems needing user or stakeholder input  
   - Provide alternative solutions if appropriate

### 5. Final Validation

1. Run the full test suite  
2. Confirm all lint rules pass  
3. Verify consistent type coverage  
4. Update or generate final documentation  
5. Assess any potential security implications

## Guidelines

1. **Use the `pyproject.toml`** as the single source of tool configurations (lint, type checks, extras).  
2. **Maintain backward compatibility** where possible.  
3. **Document any significant API or structural changes**.  
4. **Address security issues promptly**.  
5. **Uphold code quality standards and typing best practices**.

## Common Issues & Solutions

### Extra Dependencies
```toml
[tool.poetry.extras]
semantic_kernel = ["semantic-kernel"]

[[tool.mypy.overrides]]
module = "semantic_kernel.*"
ignore_missing_imports = true
```
Install extras when needed (`poetry install --extras "semantic_kernel"`) to avoid lint or type errors for optional modules.

### Import Errors
```python
# Before
from pepperpy.agents.core import BaseAgent

# After
from pepperpy.core.base import BaseAgent
```

### Type Annotation Fixes
```python
# Before
def process_data(data):
    return data.value

# After
def process_data(data: DataType) -> ResultType:
    return data.value
```

### Documentation Updates
```python
# Before
def validate():
    pass

# After
def validate() -> bool:
    """
    Validate the current configuration.

    Returns:
        bool: True if validation passes, otherwise False.

    Raises:
        ValidationError: For critical validation failures.
    """
    pass
```

## Reporting

1. Document notable changes and fixes  
2. Log any pending or postponed issues  
3. Identify follow-up tasks  
4. Update relevant project documentation

## Maintenance

1. **Perform regular lint checks**  
2. **Use automated type checks in your pipeline**  
3. **Refresh documentation on API updates**  
4. **Engage in thorough code reviews**

All configurations (formatting, lint, type checks, coverage, etc.) are centralized in **`pyproject.toml`**. This ensures a single, authoritative source of truth, simplifies tool updates, and helps maintain a consistent workflow across the team.