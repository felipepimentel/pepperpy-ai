---
title: Plan Task
description: Template for planning tasks and identifying required rules
version: 1.1
category: planning
tags: [planning, architecture, rules, kanban]
---

# Context
This prompt helps in planning tasks by:
1. Breaking down requirements into actionable items
2. Identifying needed rules and dependencies
3. Planning architecture and components
4. Defining validation criteria
5. Integrating with kanban board tracking

# Input Format
```yaml
task:
  name: string  # Task name
  description: string  # Task description
  type: feature|bugfix|refactor  # Task type
  scope: string  # Module/component scope
  priority: high|medium|low  # Task priority
  points: number  # Story points (1,2,3,5,8,13)
```

# Output Format
```yaml
plan:
  task_id: string  # Generated task ID (e.g., TASK-004)
  
  # Task Details (for kanban.md)
  kanban_entry:
    name: string
    description: string
    type: feature|bugfix|refactor
    scope: string
    priority: high|medium|low
    points: number
    dependencies: list[string]
    branch: string  # e.g., task/004-provider-system
    steps: list[string]  # Concrete steps to implement
  
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
    - id: string  # Subtask ID (e.g., TASK-004.1)
      description: string
      dependencies: list[string]
      validation: list[string]
      points: number  # Story points for subtask
  
  # Validation Criteria
  validation:
    functional: list[string]  # Functional requirements
    technical: list[string]  # Technical requirements
    security: list[string]  # Security requirements

  # Task Lifecycle Steps
  lifecycle:
    planning:
      - Review and adjust this plan
      - Create task documentation in .product/tasks/
      - Update .product/kanban.md with new task
    implementation:
      - Create feature branch
      - Follow steps sequence
      - Update documentation
    review:
      - Code review checklist
      - Documentation review
      - Architecture validation
    completion:
      - Merge to main
      - Update .product/kanban.md status
      - Document outcomes
```

# Example Usage
```yaml
input:
  task:
    name: "Implement Provider System"
    description: "Create provider-agnostic system for AI services"
    type: "feature"
    scope: "pepperpy.providers"
    priority: "high"
    points: 8

output:
  plan:
    task_id: "TASK-004"
    
    kanban_entry:
      name: "Implement Provider System"
      description: "Create provider-agnostic system for AI services"
      type: "feature"
      scope: "pepperpy.providers"
      priority: "high"
      points: 8
      dependencies: ["TASK-001"]
      branch: "task/004-provider-system"
      steps:
        - "Create provider rules and base interface"
        - "Implement core provider protocol"
        - "Add OpenAI implementation"
        - "Add additional providers"
        - "Write comprehensive tests"
    
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
        points: 3
        validation:
          - "Rule file exists and validates"
          - "Base interface includes required methods"
      - id: "TASK-004.2"
        description: "Implement provider factory"
        dependencies: ["TASK-004.1"]
        points: 5
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

    lifecycle:
      planning:
        - "Review plan with team"
        - "Create task/004-provider-system.md in .product/tasks/"
        - "Add task to .product/kanban.md in To Do section"
      implementation:
        - "Create task/004-provider-system branch"
        - "Follow implementation steps sequence"
        - "Update documentation as needed"
      review:
        - "Run full test suite"
        - "Verify against validation criteria"
        - "Update architecture diagrams"
      completion:
        - "Merge to main branch"
        - "Move task to Done in .product/kanban.md"
        - "Document implementation details"
```

# Task Planning Workflow

## 1. Plan Creation
1. Fill out task details
2. Generate structured plan
3. Review and adjust components
4. Validate against project structure

## 2. Kanban Integration
1. Add task to .product/kanban.md in To Do section
2. Include all required metadata
3. Create detailed task doc in .product/tasks/
4. Link related documentation

## 3. Implementation Tracking
1. Move task to In Progress in .product/kanban.md
2. Update progress regularly
3. Track completion of steps
4. Document challenges/decisions

## 4. Completion Process
1. Verify all validation criteria
2. Update documentation
3. Move to Done in .product/kanban.md
4. Record final outcome

# Guidelines

## Task Breakdown
- Split into manageable subtasks
- Define clear dependencies
- Include validation criteria
- Assign story points

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

## Progress Tracking
- Update .product/kanban.md status
- Document step completion
- Track time and points
- Record decisions made

# Next Steps
1. Review and adjust the plan
2. Create task documentation in .product/tasks/
3. Update .product/kanban.md with new task
4. Begin implementation following lifecycle steps 