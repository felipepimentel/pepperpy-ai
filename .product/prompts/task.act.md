---
title: Task Execution Template 
description: Direct execution framework for implementing planned tasks
version: 8.0
mode: Act
---

# CRITICAL EXECUTION CONSTRAINTS
1. IMPLEMENT ONLY what's explicitly defined in the task plan
2. DO NOT create tests unless specifically requested in the plan
3. DO NOT create documentation unless specifically requested in the plan
4. DO NOT add features beyond what's in the requirements
5. DO NOT refactor anything outside the specified scope
6. FOLLOW EXACTLY the file locations specified in the plan

# Task Structure Reference
Tasks are defined at `.product/tasks/<TASK-ID>/`:
- Main task: `.product/tasks/<TASK-ID>/<TASK-ID>.md`
- Requirements: `.product/tasks/<TASK-ID>/<TASK-ID>-R00X.md`

# STEP-BY-STEP EXECUTION SEQUENCE

## 1. Verify Task Status 
- Check main task status in frontmatter
- If status is "✅ Done", respond "Task already completed" and stop
- If status is not "📋 To Do" or "🏃 In Progress", respond "Task not ready" and stop

## 2. Verify Structure Before Implementation
```bash
# Verify project structure to avoid duplication
grep -r "<relevant_keyword>" pepperpy/
```

## 3. Implementation Sequence
- Update main task status to "🏃 In Progress"
- For each requirement, in order:
  1. Mark requirement as "🏃 Started" 
  2. Implement EXACTLY what's defined in the requirement
  3. Mark requirement as "✅ Done" after implementation
  4. Update progress in main task file

## 4. File Operations
- When modifying existing files:
  - Show the exact changes being made
  - Maintain indentation and coding style
- When creating new files:
  - Use EXACTLY the path specified in the plan
  - Create all necessary parent directories

## 5. Update Progress
After completing each requirement:
```markdown
## YYYY-MM-DD
- Completed:
  - [R00X] Implemented <specific feature>
- Next:
  - [R00Y] Will implement <next feature>
```

# Environment Setup
For any command execution:
```bash
export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
export PYTHONHOME=""
export PYTHONPATH=""
poetry <command>
```

# Structure Conflict Resolution
If a file or directory would conflict with existing structure:
1. DO NOT proceed with creating duplicates
2. Identify the exact conflict
3. Request guidance before proceeding
4. DO NOT automatically refactor unless specified in plan

# Implementation Checklist
For each implementation:
- [ ] Verify implementation matches EXACTLY what's in the requirement
- [ ] Check that no additional files are created beyond what's specified
- [ ] Ensure no tests are added unless explicitly requested
- [ ] Ensure no documentation is added unless explicitly requested
- [ ] Update task status correctly after implementation

# SUCCESSFUL EXECUTION EXAMPLE

Task TASK-042-R001 requires creating a new utility function in `pepperpy/core/utils/formatting.py`:

1. First, check file existence:
```bash
ls -la pepperpy/core/utils/formatting.py
```

2. Implement the required function:
```python
# Adding to pepperpy/core/utils/formatting.py

def format_timestamp(timestamp, format_string="%Y-%m-%d %H:%M:%S"):
    """Format timestamp according to specified format string."""
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime(format_string)
```

3. Update task status:
```markdown
## 2025-02-27
- Completed:
  - [R001] Implemented timestamp formatting utility ✅
- Next:
  - [R002] Will implement date validation function ⏳
```

Remember: Your sole task is to implement exactly what is specified in the plan - nothing more, nothing less.