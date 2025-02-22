---
title: Task Execution Template
description: Template for executing planned tasks with strict format maintenance and clear status tracking.
version: 6.0
category: execution
tags: [execution, implementation]
yolo: true
strict_mode: true
---

# Task File Access
All task files are located at `.product/tasks/<TASK-ID>/`. For example:
- Main task file: `.product/tasks/TASK-004/TASK-004.md`
- Requirement files: `.product/tasks/TASK-004/TASK-004-R001.md`

# Execution Rules
```yaml
validation:
  pre_execution:
    task_status:
      - if main task status is "✅ Done": respond "Task is already completed" and stop
      - if main task status not in ["📋 To Do", "🏃 In Progress"]: stop
    task_format:
      - verify main task frontmatter completeness
      - verify requirement files exist and are complete
      - verify requirements format in each file
      - verify task structure matches original plan
      - verify no unauthorized modifications
    task_content:
      - verify overview section preserved in main file
      - verify requirements list matches plan
      - verify implementation steps preserved in requirement files
      - verify validation criteria preserved in requirement files

  status_transitions:
    main_task:
      - "📋 To Do" -> "🏃 In Progress":
          - update mode to Act
          - preserve all planning details
          - maintain validation criteria
      - "🏃 In Progress" -> "✅ Done":
          - validate all requirements complete
          - verify no planning details were lost
    
    requirement:
      - "📋 To Do" -> "🏃 In Progress":
          - update status in both main and requirement file
          - add start date
      - "🏃 In Progress" -> "✅ Done":
          - update status in both main and requirement file
          - add completion date
    
  kanban_sync:
    file: .product/kanban.md
    required: true
    preserve_metadata: true
```

# Main Task File Template
```markdown
---
title: {title}
priority: high|medium|low
points: 1|2|3|5|8|13
status: 🏃 In Progress
mode: Act
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Requirements Overview
- [-] [R001] {title} - [Details](TASK-XXX-R001.md)  # 🏃 Started: YYYY-MM-DD
- [ ] [R002] {title} - [Details](TASK-XXX-R002.md)
- [x] [R003] {title} - [Details](TASK-XXX-R003.md)  # ✅ Done: YYYY-MM-DD

# Progress Updates

## YYYY-MM-DD
- Current Status: {specific implementation detail}
- Completed:
  - [R003] {specific implemented item} ✅
- In Progress:
  - [R001] {specific item being worked on} 🏃
- Next:
  - [R002] {specific next item} ⏳
```

# Requirement File Template
```markdown
---
title: {requirement_title}
task: TASK-XXX
code: R001
status: 🏃 In Progress
created: YYYY-MM-DD
updated: YYYY-MM-DD
started: YYYY-MM-DD
completed: null
---

# Implementation Status
```python
def implemented_feature():  # ✅ Complete
    return "working"

def in_progress_feature():  # 🏃 In Progress
    pass

def pending_feature():  # ⏳ Pending
    pass
```

# Validation Status
```python
test_implemented ✅
test_in_progress 🏃
test_pending ⏳
```

# Progress Updates
## YYYY-MM-DD
- Status: {status}
- Progress: {details}
```

# Rules for Maintaining Format

1. **Main Task File:**
   - Never add new requirements
   - Never modify requirement descriptions
   - Only update status markers and dates
   - Keep overview and progress up to date
   - Sync status with requirement files

2. **Requirement Files:**
   - Never modify original requirement
   - Keep implementation status current
   - Update validation status regularly
   - Add progress updates as needed
   - Sync status with main task file

3. **Status Updates Flow:**
   - Update status in requirement file
   - Reflect status in main task file
   - Update kanban board
   - Add progress updates in both files
   - Keep all files in sync

4. **Completion Rules:**
   - All requirement files marked complete
   - All tests passing in each requirement
   - Main task status updated
   - Kanban updated
   - All documentation current

# Example Progress Flow

## Starting Implementation
```markdown
# In main task file (TASK-007.md):
- [ ] [R001] Feature: Add error handling - [Details](TASK-007-R001.md)
->
- [-] [R001] Feature: Add error handling - [Details](TASK-007-R001.md)  # 🏃 Started: 2024-02-14

# In requirement file (TASK-007-R001.md):
status: 📋 To Do
->
status: 🏃 In Progress
started: 2024-02-14
```

## Implementation Progress
```markdown
# In requirement file (TASK-007-R001.md):
# Implementation Status
```python
def handle_error(error: Exception):  # ✅ Complete
    return ErrorResult(str(error))

def process_error(error: Exception):  # 🏃 In Progress
    pass
```

# Validation Status
```python
test_handle_error_basic ✅
test_handle_error_complex 🏃
test_process_error ⏳
```
```

## Completion
```markdown
# In main task file (TASK-007.md):
- [-] [R001] Feature: Add error handling - [Details](TASK-007-R001.md)  # 🏃 Started: 2024-02-14
->
- [x] [R001] Feature: Add error handling - [Details](TASK-007-R001.md)  # ✅ Done: 2024-02-14

# In requirement file (TASK-007-R001.md):
status: 🏃 In Progress
->
status: ✅ Done
completed: 2024-02-14
```

# Important Constraints

1. **File Organization:**
   - Keep all task files in their directory
   - Maintain clear requirement references
   - Use consistent file naming
   - Keep status markers synchronized
   - Preserve file structure

2. **Content Management:**
   - Never modify original requirements
   - Keep implementation current
   - Update validation status
   - Maintain progress updates
   - Sync status across files

3. **Status Tracking:**
   - Update both main and requirement files
   - Keep dates accurate
   - Use consistent status markers
   - Maintain kanban board
   - Document all changes

4. **Completion Process:**
   - Verify all requirements complete
   - Check all validation criteria
   - Update all status markers
   - Sync all related files
   - Maintain documentation
