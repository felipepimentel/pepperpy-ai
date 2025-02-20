---
title: Task Planning Template
description: Template for task planning with clear specifications and implementation details.
version: 3.0
category: planning
tags: [planning, task-management]
yolo: true
strict_mode: true
---

# Task File Location
Tasks should be created in the `.product/tasks/` directory following the naming convention:
- File path: `.product/tasks/TASK-{ID}.md`
- Example: `.product/tasks/TASK-005.md`

```markdown
---
title: {task_title}
priority: high|medium|low
points: 1|2|3|5|8|13
status: 📋 To Do
mode: Plan
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Requirements
Note: Requirements follow sequential order. Each builds upon previous changes.

- [ ] Requirement 1: {Clear objective}
  ## Current State
  \```python
  # Existing code or structure to be modified
  \```

  ## Implementation
  \```python
  # Exact code changes and implementation
  \```

  ## Validation
  \```python
  def test_requirement():
      # Specific tests for this change
  \```

# Progress Updates

## YYYY-MM-DD
- Current Status: {status}
- Completed: {items}
- Next Steps: {next actions}
```

Example Usage:
```markdown
---
title: Code Organization and Structure Improvements
priority: high
points: 8
status: 📋 To Do
mode: Plan
created: 2024-02-14
updated: 2024-02-14
---

# Requirements

- [ ] Flatten capabilities structure
  ## Current State
  \```python
  # capabilities/learning/errors.py
  class LearningError(Exception):
      pass

  # capabilities/planning/errors.py
  class PlanningError(Exception):
      pass
  \```

  ## Implementation
  \```python
  # capabilities/errors.py
  from enum import Enum

  class ErrorType(Enum):
      LEARNING = "learning"
      PLANNING = "planning"

  class CapabilityError(Exception):
      def __init__(self, type: ErrorType, message: str):
          self.type = type
          self.message = message
  \```

  ## Validation
  \```python
  def test_capability_errors():
      error = CapabilityError(ErrorType.LEARNING, "test")
      assert error.type == ErrorType.LEARNING
      assert str(error) == "learning: test"
  \```

# Progress Updates

## 2024-02-14
- Current Status: Planning phase
- Completed: Initial requirements definition
- Next Steps: Begin implementation
```
Remember: 
1. All tasks must be saved in `.product/tasks/TASK-{ID}.md`
2. Reference task_management_workflow for task creation
3. Reference ai_knowledge_base_management for pattern tracking