---
title: Repository Cleanup
description: ALWAYS use when performing repository cleanup to ensure systematic and safe maintenance. This prompt guides automated cleanup operations.
version: 1.2
category: maintenance
tags: [cleanup, optimization, maintenance]
---

# Context
Guides the automated cleanup of repository while maintaining project integrity and following established patterns.

# Pre-cleanup Validation
```yaml
validate:
  structure:
    file: ".product/project_structure.yml"
    required: true
  
  knowledge_base:
    query:
      - cleanup_patterns
      - safe_removals
      - known_issues
  
  backup:
    create:
      - important_logs
      - custom_artifacts
      - local_configs
```

# Cleanup Operations

## 1. Python Artifacts
```yaml
cleanup:
  python:
    find_remove:
      directories:
        - "__pycache__"
        - "*.egg-info"
        - ".pytest_cache"
        - ".mypy_cache"
        - ".ruff_cache"
      files:
        - "*.pyc"
        - "*.pyo"
        - "*.pyd"
    
    preserve:
      - ".gitignore"
      - "py.typed"
```

## 2. Environment Cleanup
```yaml
environment:
  virtual_env:
    action: "remove"
    target: ".venv"
    backup: false
  
  dependencies:
    analyze:
      file: "pyproject.toml"
      check:
        - unused_deps
        - outdated_deps
    update:
      - remove_unused
      - sort_groups
```

## 3. Log Management
```yaml
logs:
  analyze:
    path: "logs/"
    patterns:
      - "*.log"
      - "*.log.*"
  
  archive:
    active_logs:
      target: "logs/archive"
      format: "tar.gz"
      date_suffix: true
  
  cleanup:
    remove:
      - empty_logs
      - archived_logs
      - temp_logs
```

## 4. Code Cleanup
```yaml
code:
  analyze:
    find:
      - dead_code
      - unused_imports
      - commented_code
      - duplicate_functions
    
    tools:
      - ruff
      - vulture
      - pyflakes
    
    preserve:
      - important_comments
      - documentation
      - type_hints
```

## 5. Documentation Update
```yaml
documentation:
  check:
    - README.md
    - docs/**/*.md
    - **/README.md
  
  update:
    - remove_outdated
    - sync_contents
    - verify_links
```

# Safety Measures

## 1. Backup Strategy
```yaml
backup:
  pre_cleanup:
    critical:
      - .env
      - logs/important/
      - custom_configs/
    
    temporary:
      path: ".cleanup_backup"
      format: "tar.gz"
      retention: "24h"
```

## 2. Validation Steps
```yaml
validate:
  pre_cleanup:
    - project_structure
    - essential_files
    - git_status
  
  post_cleanup:
    - project_integrity
    - test_suite
    - documentation
```

## 3. Recovery Process
```yaml
recovery:
  triggers:
    - test_failure
    - missing_essential
    - broken_imports
  
  actions:
    - restore_backup
    - log_issue
    - notify_system
```

# Execution Flow

## 1. Initial Setup
```yaml
setup:
  steps:
    - validate_structure
    - create_backup
    - analyze_state
```

## 2. Cleanup Execution
```yaml
execute:
  sequence:
    - python_artifacts
    - virtual_env
    - dependencies
    - logs
    - code
    - documentation
  
  monitoring:
    - track_changes
    - validate_steps
    - log_actions
```

## 3. Verification
```yaml
verify:
  checks:
    - project_structure
    - dependencies
    - tests
    - documentation
  
  report:
    generate:
      - actions_taken
      - space_freed
      - improvements
```

# Example Usage
```yaml
# Cleanup Execution
cleanup:
  validate:
    structure: valid
    backup: created
  
  operations:
    python:
      removed:
        - "__pycache__ directories"
        - "*.pyc files"
    
    environment:
      cleaned:
        - ".venv"
        - "unused dependencies"
    
    logs:
      archived:
        - "active logs"
      removed:
        - "empty logs"
    
    code:
      optimized:
        - "removed dead code"
        - "fixed imports"
    
    documentation:
      updated:
        - "README.md"
        - "API docs"

  verification:
    status: "success"
    tests: "passing"
    structure: "valid"
```

# Guidelines

## Execution Strategy
- Run validations first
- Create safety backups
- Execute systematically
- Verify each step

## Safety First
- Preserve essential files
- Maintain structure
- Keep backups
- Validate changes

## Documentation
- Update READMEs
- Sync API docs
- Remove outdated
- Maintain clarity

## Verification
- Run test suite
- Check structure
- Validate imports
- Verify functionality

Remember: Reference project_structure rule for valid structure and ai_knowledge_base_management for cleanup patterns.