---
title: Start New Task
description: ALWAYS use when initiating a new task to ensure proper setup and tracking. This prompt guides task selection and initialization process.
version: 1.1
category: task-management
tags: [task-initialization, planning]
yolo: true
---

# Context
Guides the process of selecting and initiating new tasks from the kanban board while maintaining alignment with established rules.

# Pre-start Validation
```yaml
validate:
  kanban:
    file: ".product/kanban.md"
    required: true
  
  knowledge_base:
    query:
      - similar_tasks
      - common_patterns
      - estimation_metrics
```

# Task Selection Process

## 1. Task Analysis
```yaml
selection_criteria:
  priority: high|medium|low
  dependencies: 
    - all_resolved: true
    - blockers: none
  knowledge_base:
    patterns: available
    metrics: sufficient
```

## 2. Status Check
```yaml
current_state:
  to_do_tasks: list
  in_progress: count <= 1
  dependencies: resolved
  resources: available
```

# Initialization Steps

## 1. Knowledge Base Query
```yaml
query:
  patterns:
    type: implementation
    similar_tasks: true
  metrics:
    type: estimation
    complexity: true
```

## 2. Task Setup
```yaml
setup:
  task_file:
    create: ".product/tasks/TASK-{ID}.md"
    template: task_management_workflow.template
    status: 🏃 In Progress
  
  branch:
    create: "task/{ID}-{description}"
    base: main
```

## 3. Status Update
```yaml
kanban_update:
  move:
    from: 📋 To Do
    to: 🏃 In Progress
  add:
    timestamp: current
    branch: task_branch
    ai_tags: relevant_tags
```

# Example Usage
```yaml
# Task Selection
selected_task:
  id: "TASK-001"
  priority: high
  dependencies: []
  knowledge_base:
    similar_tasks: 2
    suggested_patterns: ["auth_flow", "security"]

# Initialization
initialization:
  task_file:
    path: ".product/tasks/TASK-001.md"
    status: 🏃 In Progress
    timestamp: "2025-02-12T10:00:00Z"
  
  branch:
    name: "task/001-auth-system"
    created: true
  
  kanban_entry: |
    ## 🏃 In Progress
    - TASK-001: Implement Authentication System
      **Priority**: High | **Points**: 5 | **Mode**: Act
      **Started**: 2025-02-12
      **Branch**: task/001-auth-system
      [Details](tasks/TASK-001.md)
      **AI-Tags**: #security #auth
```

# Guidelines

## Selection Criteria
- Highest priority first
- All dependencies resolved
- Resources available
- Knowledge base patterns exist

## Initialization Requirements
- Follow task_management_workflow rule
- Create proper task file
- Update kanban correctly
- Create feature branch
- Document start time

## Knowledge Integration
- Query similar patterns
- Check estimation metrics
- Tag for AI processing
- Update learning context

Remember: Reference task_management_workflow and ai_knowledge_base_management rules for complete requirements.