---
title: Plan Task
description: Quick prompt for planning new tasks
version: 1.0
yolo: true
---

Create a new task using the established task management rule format. 

# Input Required
```yaml
task:
  name: string        # Brief, descriptive name
  description: string # Full task description
  priority: high|medium|low
  points: 1|2|3|5|8|13
  mode: plan|act
```

# Output Expected
1. Task file content for `.product/tasks/TASK-XXX.md`
2. Kanban entry for `.product/kanban.md`
3. Knowledge base queries and expected updates

# Example
```yaml
input:
  task:
    name: "Implement Vector Store"
    description: "Create a vector storage system for embedding management"
    priority: "high"
    points: 8
    mode: "plan"
```
