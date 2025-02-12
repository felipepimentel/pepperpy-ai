---
title: Project Structure Validation
description: ALWAYS use when validating or modifying project structure to ensure compliance with standards. This prompt guides structural validation and maintenance.
version: 1.3
category: validation
tags: [structure, validation, architecture]
---

# Context
Guides the validation and maintenance of project structure according to established standards and patterns.

# Pre-validation Setup
```yaml
validate:
  required_files:
    structure: ".product/project_structure.yml"
    architecture: ".product/architecture.mermaid"
    knowledge_base: ".product/ai/knowledge.json"
  
  knowledge_base:
    query:
      - structure_patterns
      - common_violations
      - approved_changes
```

# Structure Definition

## 1. Core Package
```yaml
pepperpy:
  required:
    files:
      - __init__.py
      - py.typed
    
    modules:
      adapters:
        purpose: "External system adapters"
        requires: ["__init__.py", "README.md"]
      
      agents:
        purpose: "Agent implementations"
        requires: ["__init__.py", "README.md"]
      
      capabilities:
        purpose: "Agent capabilities"
        requires: ["__init__.py", "README.md"]
      
      core:
        purpose: "Core functionality"
        requires: ["__init__.py", "README.md"]
      
      providers:
        purpose: "AI provider integrations"
        requires: ["__init__.py", "README.md"]
```

## 2. Support Directories
```yaml
support:
  .product:
    required:
      - tasks/
      - kanban.md
      - architecture.mermaid
      - project_structure.yml
  
  docs:
    required:
      - api_reference/
      - development/
      - user_guides/
      - README.md
  
  tests:
    required:
      - unit/
      - integration/
      - e2e/
      - conftest.py
  
  config:
    required:
      - pyproject.toml
      - .env.example
    optional:
      - .env
```

# Validation Process

## 1. Structure Check
```yaml
validation:
  command: "./scripts/validate_structure.py"
  checks:
    directories:
      - existence
      - permissions
      - naming
    
    files:
      - required_presence
      - proper_location
      - naming_convention
    
    modules:
      - init_files
      - type_hints
      - documentation
```

## 2. Issue Analysis
```yaml
analyze:
  violations:
    categorize:
      critical:
        - missing_required
        - wrong_location
      warning:
        - missing_optional
        - documentation
      info:
        - style_suggestions
        - optimizations
  
  patterns:
    check:
      - common_issues
      - recurring_problems
      - known_solutions
```

## 3. Resolution Process
```yaml
resolve:
  steps:
    - document_issue
    - analyze_impact
    - propose_solution
    - get_approval
    - implement_fix
    - verify_change
  
  tracking:
    - log_changes
    - update_docs
    - record_pattern
```

# Validation Rules

## File Organization
```yaml
rules:
  naming:
    modules: snake_case
    directories: snake_case
    test_files: test_*.py
  
  location:
    source: pepperpy/
    tests: tests/
    docs: docs/
    config: ./
  
  content:
    python:
      - proper_imports
      - type_hints
      - docstrings
    
    documentation:
      - clear_purpose
      - usage_examples
      - api_reference
```

## Prohibited Actions
```yaml
prohibited:
  structure:
    - redundant_directories
    - mixed_test_source
    - invalid_locations
  
  content:
    - sensitive_data
    - compiled_files
    - temporary_files
  
  process:
    - unauthorized_changes
    - bypass_validation
    - undocumented_changes
```

# Example Usage
```yaml
# Validation Run
validation:
  command: "./scripts/validate_structure.py"
  output:
    issues:
      - type: "critical"
        issue: "Missing __init__.py in pepperpy/providers/new_module"
        fix: "Create missing file"
      
      - type: "warning"
        issue: "Incomplete documentation in providers/README.md"
        fix: "Update documentation with required sections"
    
    actions:
      - create_file:
          path: "pepperpy/providers/new_module/__init__.py"
          content: |
            """New module initialization."""
            from typing import Any
      
      - update_docs:
          path: "providers/README.md"
          sections:
            - Purpose
            - Usage
            - API Reference
```

# Guidelines

## Validation Strategy
- Run validation regularly
- Address issues promptly
- Document all changes
- Maintain consistency

## Documentation Updates
- Keep README files current
- Update architecture diagrams
- Maintain API documentation
- Track changes in kanban

## Change Management
- Get approval for changes
- Update knowledge base
- Follow naming conventions
- Maintain hierarchy

## Quality Assurance
- Verify all changes
- Run test suite
- Check documentation
- Update diagrams

Remember: Reference project_structure rule for details and ai_knowledge_base_management for pattern learning.