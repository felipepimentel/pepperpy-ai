---
title: Task Planning & Initialization
description: ALWAYS use when planning and creating new tasks to ensure thorough analysis and proper setup. This prompt guides task planning, discussion, and initialization.
version: 1.3
category: planning
tags: [planning, discussion, initialization]
yolo: true
---

# Initial Input
```yaml
task:
  name: string          # Brief task description
  context: string       # Background information
  expected: string      # Desired outcome
  priority: high|medium|low
```

# Pre-planning Validation
```yaml
validate:
  kanban:
    file: ".product/kanban.md"
    exists: required
  
  knowledge_base:
    query:
      - similar_tasks
      - common_patterns
      - estimation_metrics
      - known_challenges
```

# Planning Discussion

## 1. Understanding Phase
Let's discuss:
- What problem are we solving?
- Who are the stakeholders?
- What are the success criteria?
- What are the constraints?

## 2. Exploration Phase
Let's explore:
- Possible approaches
- Technical implications
- Potential challenges
- Similar patterns from our knowledge base
- Required components

## 3. Solution Design
Let's define:
- Best approach selection
- Architecture considerations
- Implementation strategy
- Required changes
- Dependencies

## 4. Risk Assessment
Let's evaluate:
- Technical risks
- Integration challenges
- Performance implications
- Security considerations
- Testing requirements

## 5. Resource Planning
Let's determine:
- Required skills
- External dependencies
- Timeline estimates
- Story points (1,2,3,5,8,13)
- Success metrics

# Task Creation

## 1. Task Setup
```yaml
initialization:
  validate:
    dependencies: resolved
    resources: available
    patterns: exist
  
  create_task:
    file:
      path: ".product/tasks/TASK-{ID}.md"
      template: task_management_workflow.template
      initial_status: 📋 To Do
    
    branch:
      name: "task/{ID}-{description}"
      base: main
    
    kanban:
      section: 📋 To Do
      format: |
        - TASK-{ID}: {name}
          **Priority**: {priority} | **Points**: {points} | **Mode**: Plan
          **Updated**: {date}
          [Details](tasks/TASK-{ID}.md)
          **AI-Tags**: {generated_tags}
```

## 2. Knowledge Base Integration
```yaml
knowledge_base:
  query:
    patterns:
      - implementation_patterns
      - similar_tasks
      - known_issues
    
    metrics:
      - complexity_estimates
      - duration_patterns
    
  update:
    - task_creation_record
    - pattern_references
    - estimation_metrics
```

# Example Usage

## Input
```yaml
task:
  name: "Vector Store Implementation"
  context: "Need efficient storage for embeddings"
  expected: "Fast, scalable vector operations"
  priority: "high"
```

## Discussion Flow
```yaml
discussion:
  understanding:
    - "What types of vectors need to be stored?"
    - "What are the performance requirements?"
    - "How will this integrate with existing systems?"

  exploration:
    approaches:
      - "Could we use an existing solution like FAISS?"
      - "What about building a custom implementation?"
      - "Should we consider a hybrid approach?"
    
    considerations:
      - "How will this scale?"
      - "What's our memory budget?"
      - "Do we need persistence?"

  design:
    selected: "Hybrid approach with custom interface"
    components:
      - "Abstract storage interface"
      - "Multiple backend support"
      - "Optimization layer"
```

## Task Creation
```yaml
setup:
  task:
    id: "TASK-042"
    file: ".product/tasks/TASK-042.md"
    content:
      title: "Implement Vector Store"
      status:
        current: 📋 To Do
        priority: high
        points: 8
        mode: Plan
      
      requirements:
        - "Design storage interface"
        - "Implement core functionality"
        - "Add optimizations"
      
      dependencies:
        systems: ["Storage System"]
        apis: ["Vector Operations"]
  
  kanban_entry: |
    - TASK-042: Implement Vector Store
      **Priority**: High | **Points**: 8 | **Mode**: Plan
      **Updated**: 2025-02-13
      [Details](tasks/TASK-042.md)
      **AI-Tags**: #vectorstore #performance
```

# Guidelines

## Discussion Flow
- Keep exploration open
- Question assumptions
- Consider alternatives
- Document decisions
- Note uncertainties

## Task Creation
- Follow task_management_workflow rule
- Use correct templates
- Include all required sections
- Set proper initial state
- Tag appropriately

## Knowledge Integration
- Reference similar patterns
- Use historical metrics
- Document new patterns
- Update estimations

Remember: 
- Discussion comes before implementation
- Document all key decisions
- Consider all stakeholders
- Plan for validation
- Create clear success criteria
- Initialize task with proper structure