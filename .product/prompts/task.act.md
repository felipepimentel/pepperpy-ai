---
title: Task Execution Template
description: Template for executing planned tasks with precise implementation tracking.
version: 3.0
category: execution
tags: [execution, implementation]
yolo: true
strict_mode: true
---

```markdown
---
title: {task_title}
priority: high|medium|low
points: 1|2|3|5|8|13
status: 🏃 In Progress
mode: Act
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Requirements

- [-] Requirement 1  # 🏃 Started: YYYY-MM-DD
  ## Implementation Progress
  1. Step 1 completed ✅
     \```python
     # Implemented code
     \```

  2. Step 2 in progress 🏃
     \```python
     # Current implementation
     \```

  3. Step 3 pending ⏳

  ## Validation Status
  \```python
  # Test results or validation status
  \```

# Progress Updates

## YYYY-MM-DD
- Current Status: {specific details}
- Completed:
  - {item 1} ✅
  - {item 2} ✅
- In Progress:
  - {item 3} 🏃
- Next:
  - {item 4} ⏳
```

Example Usage:
```markdown
---
title: Code Organization and Structure Improvements
priority: high
points: 8
status: 🏃 In Progress
mode: Act
created: 2024-02-14
updated: 2024-02-14
---

# Requirements

- [-] Flatten capabilities structure  # 🏃 Started: 2024-02-14
  ## Implementation Progress
  1. Created new errors.py ✅
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

  2. Updating implementations 🏃
     \```python
     # capabilities/learning.py
     from .errors import CapabilityError, ErrorType

     class LearningCapability:
         def process(self):
             try:
                 # Implementation
                 pass
             except Exception as e:
                 raise CapabilityError(ErrorType.LEARNING, str(e))
     \```

  3. Update remaining imports ⏳

  ## Validation Status
  \```python
  # Current test results:
  test_error_types ✅
  test_error_messages ✅
  test_learning_capability 🏃
  \```

# Progress Updates

## 2024-02-14
- Current Status: Implementing capabilities restructure
- Completed:
  - Created errors.py with consolidated error handling ✅
  - Implemented ErrorType enum ✅
  - Created CapabilityError class ✅
- In Progress:
  - Updating learning capability implementation 🏃
  - Migrating error handling 🏃
- Next:
  - Update remaining imports ⏳
  - Run full validation suite ⏳
```
Remember: Reference task_management_workflow for task creation and ai_knowledge_base_management for pattern tracking.