---
title: Task Execution Template
description: ALWAYS use when executing task actions to ensure systematic progress following established task management standards. This protocol ensures deterministic AI-driven task execution.
version: 2.0
category: execution
tags: [execution, implementation, task-management]
yolo: true
strict_mode: true
---

# Task Execution Rules

## 1. State Validation
```yaml
validate:
  task_file:
    exists: required
    mode: Plan      # Must start in Plan mode
    format: markdown
    frontmatter:
      complete: required
      valid: required
  
  kanban:
    entry_exists: required
    format_valid: required
```

## 2. Execution Flow
```yaml
execution_flow:
  # 1. Task Start
  start:
    - Validate task file
    - Update frontmatter:
        mode: Act
        status: 🏗️ In Progress
    - Update kanban entry
    - Create progress section
  
  # 2. Implementation
  implement:
    - Follow implementation plan
    - Update requirements status
    - Document progress
    - Track breaking changes
  
  # 3. Testing
  test:
    - Execute test strategy
    - Validate requirements
    - Update documentation
  
  # 4. Completion
  complete:
    - Verify all requirements
    - Update status to ✅ Done
    - Update kanban board
    - Document outcomes
```

## 3. Progress Updates
```yaml
progress_format:
  markdown: |
    # Progress Updates
    
    ## {YYYY-MM-DD}
    - Current Status: {status_detail}
    - Completed:
      - {item1}
      - {item2}
    - Next Steps:
      1. {step1}
      2. {step2}
    [if blocked] - Blockers:
      - Issue: {issue}
      - Plan: {resolution}
```

## 4. Requirement Updates
```yaml
requirement_format:
  in_progress: "- [-] {requirement}  # 🏃 Started: {YYYY-MM-DD}"
  completed: "- [x] {requirement}  # ✅ {YYYY-MM-DD}"
  blocked: "- [ ] {requirement}  # ⏳ Blocked: {reason}"
```

# Example Execution

## 1. Starting Task
```markdown
# Initial State (TASK-002.md)
---
title: Code Organization and Structure Improvements
priority: high
points: 5
status: 📋 To Do
mode: Plan
created: 2024-02-14
updated: 2024-02-14
---

# Action: Start Implementation
## 1. Update Frontmatter
---
title: Code Organization and Structure Improvements
priority: high
points: 5
status: 🏗️ In Progress
mode: Act
created: 2024-02-14
updated: 2024-02-14
---

## 2. Add Progress Section
# Progress Updates

## 2024-02-14
- Current Status: Starting implementation
- Completed:
  - Repository setup
  - Branch creation
- Next Steps:
  1. Flatten capabilities structure
  2. Move agent code to hub

## 3. Update Kanban
- TASK-002: Code Organization and Structure Improvements
  **Priority**: high | **Points**: 5 | **Mode**: Act
  **Updated**: 2024-02-14
  **Branch**: task/002-code-organization
  [Details](tasks/TASK-002.md)
  **AI-Tags**: #refactoring #organization #architecture
```

## 2. Implementation Progress
```markdown
# Progress Updates

## 2024-02-15
- Current Status: Implementing capabilities restructure
- Completed:
  - Created new capabilities structure
  - Moved error definitions
- Next Steps:
  1. Update import paths
  2. Add migration guides

# Requirements
- [x] Flatten capabilities structure  # ✅ 2024-02-15
  - Single level hierarchy implemented
  - Error handling centralized
  - Directory structure verified
- [-] Move agents to hub  # 🏃 Started: 2024-02-15
  - In progress: Moving code
  - Next: Update imports
```

## 3. Task Completion
```markdown
# Final State
---
title: Code Organization and Structure Improvements
priority: high
points: 5
status: ✅ Done
mode: Act
created: 2024-02-14
updated: 2024-02-16
---

# Progress Updates

## 2024-02-16
- Current Status: Implementation complete
- Completed:
  - All requirements implemented
  - Tests passing
  - Documentation updated
- Validation:
  - Directory structure simplified
  - All imports working
  - No scattered errors
  - Agents properly moved to hub

# Requirements
- [x] Flatten capabilities structure  # ✅ 2024-02-15
- [x] Move agents to hub  # ✅ 2024-02-16
- [x] Update import paths  # ✅ 2024-02-16
- [x] Consolidate error handling  # ✅ 2024-02-16

# Kanban Update
## ✅ Done
- TASK-002: Code Organization and Structure Improvements
  **Priority**: high | **Points**: 5 | **Mode**: Act
  **Updated**: 2024-02-16
  **Branch**: task/002-code-organization
  [Details](tasks/TASK-002.md)
  **AI-Tags**: #refactoring #organization #architecture #completed
```