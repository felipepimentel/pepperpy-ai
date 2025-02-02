---
title: Plan Task
description: Template for planning tasks and identifying required rules
version: 1.0
category: planning
tags: [planning, architecture, rules]
---

# Context
This prompt helps in planning tasks, including:
1. Breaking down requirements
2. Identifying needed rules
3. Planning architecture
4. Defining validation criteria

# Input Format
```yaml
task:
  name: string  # Task name
  description: string  # Task description
  type: feature|bugfix|refactor  # Task type
  scope: string  # Module/component scope
```

# Output Format
```yaml
plan:
  task_id: string  # Generated task ID
  
  # Task Details
  name: string
  description: string
  type: feature|bugfix|refactor
  scope: string
  
  # Required Rules
  required_rules:
    - name: string  # Rule name
      reason: string  # Why this rule is needed
      scope: string  # Rule scope
  
  # Architecture
  components:
    - name: string
      path: string
      purpose: string
      dependencies: list[string]
  
  # Implementation Plan
  subtasks:
    - id: string  # Subtask ID
      description: string
      dependencies: list[string]
      validation: list[string]
  
  # Validation Criteria
  validation:
    functional: list[string]  # Functional requirements
    technical: list[string]  # Technical requirements
    security: list[string]  # Security requirements
```

# Example Usage
```yaml
input:
  task:
    name: "Implement Provider System"
    description: "Create provider-agnostic system for AI services"
    type: "feature"
    scope: "pepperpy.providers"

output:
  plan:
    task_id: "TASK-004"
    name: "Implement Provider System"
    description: "Create provider-agnostic system for AI services"
    type: "feature"
    scope: "pepperpy.providers"
    
    required_rules:
      - name: "providers-rules"
        reason: "Define provider implementation standards"
        scope: "pepperpy.providers"
        
    components:
      - name: "BaseProvider"
        path: "pepperpy/providers/base.py"
        purpose: "Define provider interface"
        dependencies: []
      - name: "ProviderFactory"
        path: "pepperpy/providers/factory.py"
        purpose: "Create provider instances"
        dependencies: ["BaseProvider"]
        
    subtasks:
      - id: "TASK-004.1"
        description: "Create provider rules and base interface"
        dependencies: []
        validation:
          - "Rule file exists and validates"
          - "Base interface includes required methods"
      - id: "TASK-004.2"
        description: "Implement provider factory"
        dependencies: ["TASK-004.1"]
        validation:
          - "Factory creates providers dynamically"
          - "Error handling for unknown providers"
          
    validation:
      functional:
        - "Can create providers dynamically"
        - "Providers implement required interface"
      technical:
        - "Type-safe implementation"
        - "Async/await support"
        - "Error handling"
      security:
        - "No hardcoded credentials"
        - "Input validation"
```

# Usage
1. Provide task details
2. Get structured plan with:
   - Task breakdown
   - Required rules
   - Architecture components
   - Validation criteria

# Planning Guidelines

## Task Breakdown
- Split into manageable subtasks
- Define clear dependencies
- Include validation criteria

## Rule Requirements
- Identify needed rules
- Specify rule scope
- Justify rule creation

## Architecture Planning
- Define key components
- Specify dependencies
- Document interfaces

## Validation Planning
- Define functional requirements
- Specify technical requirements
- Include security considerations

# Next Steps
1. Review and adjust the plan
2. Create task documentation
3. Execute task using act-task.md 