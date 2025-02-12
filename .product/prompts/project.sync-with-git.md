---
title: Git Synchronization
description: ALWAYS use when synchronizing local and remote repositories to ensure consistent state management. This prompt guides git operations and conflict resolution.
version: 1.1
category: version-control
tags: [git, sync, deployment]
---

# Context
Guides the process of synchronizing local and remote repositories while maintaining project integrity and task tracking.

# Pre-sync Validation
```yaml
validate:
  status:
    check:
      - current_branch
      - uncommitted_changes
      - stash_contents
    
  knowledge_base:
    query:
      - sync_patterns
      - conflict_resolutions
      - common_issues
```

# Sync Process

## 1. State Analysis
```yaml
analyze:
  local:
    command: "git status"
    check:
      - branch_name
      - changes
      - conflicts
  
  remote:
    command: "git remote -v"
    check:
      - origin_url
      - permissions
```

## 2. Change Management
```yaml
changes:
  uncommitted:
    action: stash
    command: "git stash save 'Pre-sync backup: {timestamp}'"
    tracking:
      - files
      - message
      - timestamp
  
  staged:
    verify:
      - conventional_commits
      - task_references
```

## 3. Sync Operations
```yaml
sync:
  update:
    fetch:
      command: "git fetch origin"
      verify: "remote state"
    
    pull:
      command: "git pull --rebase origin {branch}"
      options:
        - autostash
        - preserve-merges
    
    conflict_handling:
      detect:
        - file_conflicts
        - semantic_conflicts
      resolve:
        strategy: "interactive"
        patterns: "knowledge_base"
  
  push:
    verify:
      - local_tests
      - lint_checks
    command: "git push origin {branch}"
```

## 4. Task Integration
```yaml
tasks:
  update:
    file: ".product/kanban.md"
    fields:
      - branch_status
      - sync_timestamp
      - conflict_resolution
    
  knowledge_base:
    update:
      - sync_patterns
      - resolution_strategies
```

# Example Usage
```yaml
# Initial Check
status:
  branch: "task/001-auth-system"
  changes: true
  conflicts: false

# Sync Process
sync:
  stash:
    message: "Pre-sync backup: 2025-02-12 15:30"
    files:
      - "pepperpy/auth/oauth.py"
      - "tests/test_auth.py"
  
  update:
    fetch: "success"
    pull:
      base: "main"
      result: "success"
  
  push:
    tests: "passed"
    lint: "clean"
    result: "success"

# Task Update
kanban:
  task: "TASK-001"
  status: "synced"
  branch: "task/001-auth-system"
  timestamp: "2025-02-12 15:35"
```

# Safety Measures

## 1. Pre-sync Backup
```yaml
backup:
  stash:
    required: true
    message_template: "Pre-sync backup: {timestamp}"
    include_untracked: true
```

## 2. Conflict Resolution
```yaml
conflicts:
  detection:
    types:
      - file_conflicts
      - merge_conflicts
      - rebase_conflicts
    
  resolution:
    strategy:
      - use_knowledge_base
      - interactive_merge
      - abort_on_critical
```

## 3. Validation
```yaml
validate:
  pre_push:
    - run_tests
    - check_lint
    - verify_structure
  
  post_sync:
    - check_integration
    - verify_state
    - update_tasks
```

# Guidelines

## Sync Strategy
- Always stash changes first
- Use rebase for clean history
- Resolve conflicts carefully
- Validate before push

## Task Management
- Update kanban status
- Document sync issues
- Track resolutions
- Maintain timestamps

## Conflict Resolution
- Use knowledge base patterns
- Document new solutions
- Keep history clean
- Test after resolution

## Quality Assurance
- Run tests before push
- Check project structure
- Verify documentation
- Update task status

Remember: Reference task_management_workflow for status updates and ai_knowledge_base_management for sync patterns.