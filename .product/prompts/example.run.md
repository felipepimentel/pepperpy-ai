---
title: Example Execution & Validation
description: ALWAYS use when executing and validating example files to ensure proper functionality and integration. This prompt guides example testing and issue resolution.
version: 1.0
category: validation
tags: [examples, testing, fixes]
yolo: true
---

# Context
Guides the process of executing, validating, and fixing example files while maintaining project standards and best practices.

# Pre-execution Validation
```yaml
validate:
  project_structure:
    file: ".product/project_structure.yml"
    required: true
  
  knowledge_base:
    query:
      - common_issues
      - best_practices
      - example_patterns
  
  environment:
    check:
      - poetry_installation
      - required_env_vars
      - python_version
```

# Execution Process

## 1. Initial Run
```yaml
execute:
  command: string        # e.g., "poetry run python {example_path}"
  mode: yolo|standard   # Default: standard
  environment:
    preserve: true      # Don't modify existing env vars
    validate: true      # Check required vars exist
```

## 2. Error Handling
```yaml
on_error:
  analyze:
    - error_type
    - error_location
    - potential_causes
  
  fix_strategy:
    scope:
      - example_code
      - library_code
      - environment
    
    constraints:
      - maintain_structure
      - respect_interfaces
      - follow_standards
    
    priorities:
      - fix_root_cause
      - minimize_changes
      - maintain_flexibility
```

## 3. Validation
```yaml
verify:
  execution:
    - exit_code: 0
    - expected_output: matched
    - no_errors: true
  
  logs:
    - level: configured
    - format: correct
    - content: relevant
  
  quality:
    - code_style: consistent
    - best_practices: followed
    - documentation: updated
```

# Example Usage
```yaml
# Example Execution
execution:
  file: "examples/research_assistant.py"
  command: "poetry run python examples/research_assistant.py"
  mode: yolo
  
  validation:
    env_vars:
      - PEPPERPY_API_KEY
      - PEPPERPY_PROVIDER
      - PEPPERPY_MODEL
    
    structure:
      check: ".product/project_structure.yml"
    
    quality:
      style: true
      practices: true
      docs: true

# Error Resolution
if_error:
  analyze:
    type: import_error
    location: "research_assistant.py"
    cause: "missing dependency"
  
  fix:
    scope: example_code
    changes:
      - add_import
      - update_requirements
      - verify_dependencies
  
  verify:
    - rerun_example
    - check_logs
    - validate_output
```

# Guidelines

## Example Execution
- Run with specified command
- Preserve environment variables
- Follow project structure
- Monitor for issues

## Error Resolution
- Analyze root cause
- Choose appropriate fix scope
- Maintain project standards
- Verify solution

## Code Quality
- Follow best practices
- Maintain flexibility
- Keep code straightforward
- Update documentation

## Validation
- Check execution success
- Verify log outputs
- Ensure quality standards
- Document changes

Remember: Reference project_structure rule for structural requirements and coding_standards rule for style guidelines.