---
title: Task Execution Template
description: Template for executing planned tasks with strict format maintenance and clear status tracking.
version: 5.1
category: execution
tags: [execution, implementation]
yolo: true
strict_mode: true
---

# Task File Access
All task files are located at `./product/tasks/<TASK-ID>.md`. For example, TASK-004 would be located at `./product/tasks/TASK-004.md`. Always use this path when accessing task files.

# Execution Rules
```yaml
validation:
  pre_execution:
    task_status:
      - if status is "✅ Done": respond "Task is already completed" and stop
      - if status not in ["📋 To Do", "🏃 In Progress"]: stop
    task_format:
      - verify frontmatter completeness
      - verify required sections exist
      - verify requirements format
      - verify task structure matches original plan
      - verify no unauthorized modifications to requirements
    task_content:
      - verify overview section preserved
      - verify requirements list matches plan
      - verify implementation steps preserved
      - verify validation criteria preserved

  status_transitions:
    - "📋 To Do" -> "🏃 In Progress":
        - update mode to Act
        - preserve all planning details
        - maintain validation criteria
    - "🏃 In Progress" -> "✅ Done":
        - validate all requirements complete
        - verify no planning details were lost
    
  kanban_sync:
    file: .product/kanban.md
    required: true
    preserve_metadata: true
```

# Task Template
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

# Requirements

- [-] Requirement: {exact description from plan}  # 🏃 Started: YYYY-MM-DD
  ## Implementation Status
  ```python
  # Only show implemented code with status
  def implemented_feature():  # ✅ Complete
      return "working"

  def in_progress_feature():  # 🏃 In Progress
      pass

  def pending_feature():  # ⏳ Pending
      pass
  ```

  ## Validation Status
  ```python
  # Only show test results
  test_implemented ✅
  test_in_progress 🏃
  test_pending ⏳
  ```

# Progress Updates

## YYYY-MM-DD
- Current Status: {specific implementation detail}
- Completed:
  - {specific implemented item} ✅
- In Progress:
  - {specific item being worked on} 🏃
- Next:
  - {specific next item} ⏳
```

# Rules for Maintaining Format

1. **Requirements Section:**
   - Never add new requirements
   - Never modify requirement descriptions
   - Never remove planning details
   - Never change validation criteria
   - Only update status markers:
     - [ ] -> [-] -> [x]
     - Add start/completion dates with markers
   - Preserve all subtasks and their structure

2. **Implementation Status:**
   - Show only actual implemented code
   - Mark each function/class with status emoji
   - Remove code when complete and tested
   - Never modify planned implementation steps
   - Keep original validation criteria

3. **Validation Status:**
   - List only existing test results
   - Update with clear status emojis
   - Remove passed tests from list
   - Never modify planned validation tests
   - Keep original test structure

4. **Progress Updates:**
   - **Every progress update must reflect in all relevant sections (Requirements, Implementation, Validation, and Progress).**
   - Add new entries at top
   - Keep entries focused and specific
   - Use consistent emoji markers
   - Reference original planning items
   - Track against planned implementation

5. **Status Updates:**
   - Update frontmatter status field
   - Update task status in kanban
   - Add completion date when done
   - Preserve all task metadata
   - Maintain dependencies information

# Example Progress Flow

## Starting Implementation
```markdown
- [ ] Feature: Add error handling  # Original
->
- [-] Feature: Add error handling  # 🏃 Started: 2024-02-14
```

## Implementation Progress
```markdown
## Implementation Status
```python
def handle_error(error: Exception):  # ✅ Complete
    return ErrorResult(str(error))

def process_error(error: Exception):  # 🏃 In Progress
    pass
```

## Validation Status
```python
test_handle_error_basic ✅
test_handle_error_complex 🏃
test_process_error ⏳
```
```

## Completion
```markdown
- [-] Feature: Add error handling  # 🏃 Started: 2024-02-14
->
- [x] Feature: Add error handling  # ✅ 2024-02-14
```

# Important Constraints

1. **Content Preservation:**
   - All planning details must be preserved
   - Implementation structure must match plan
   - Validation criteria must remain unchanged
   - Original requirements must be maintained
   - Task structure must be respected

2. **Format Maintenance:**
   - Keep exact indentation
   - Use specified emojis only
   - Follow status marker format
   - Maintain vertical structure
   - Preserve section hierarchy

3. **Updates Flow:**
   - **Every modification in execution (code and tests) must be reflected immediately in the task status.**
   - Add new progress entries at top
   - Keep implementation current
   - Remove completed code
   - Update validation status
   - Reference original plan items

4. **Completion Rules:**
   - All code implemented
   - All tests passing
   - Status marked as done
   - Kanban updated
   - Original plan verified
