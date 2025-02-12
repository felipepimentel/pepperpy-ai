---
title: Product Roadmap Management
description: ALWAYS use when planning or updating product roadmap to ensure strategic alignment and clear delivery paths. This prompt guides roadmap maintenance and feature planning.
version: 1.1
category: product-planning
tags: [roadmap, strategy, planning]
yolo: true
---

# Context
Manages the product roadmap, ensuring alignment between strategic goals and tactical execution while integrating with our task management system.

# Roadmap Analysis

## 1. Current State
```yaml
analyze:
  completed:
    milestones: list
    features: list
    metrics:
      - adoption_rate
      - performance
      - user_feedback
  
  in_progress:
    features: list
    status: percentage
    timeline: date
    blockers: list
  
  knowledge_base:
    query:
      - implementation_patterns
      - completion_metrics
      - common_challenges
```

## 2. Strategic Planning
```yaml
planning_horizons:
  short_term:  # 1-2 months
    features:
      - name: string
        priority: high|medium|low
        effort: story_points
        dependencies: list
        target_date: date
  
  medium_term:  # 3-6 months
    features:
      - name: string
        priority: high|medium|low
        effort: story_points
        dependencies: list
        target_quarter: Q#
  
  long_term:  # 6+ months
    features:
      - name: string
        category: core|enhancement|innovation
        strategic_value: description
        estimated_effort: t-shirt_size
```

# Feature Definition

## Feature Template
```yaml
feature:
  name: string
  description: string
  value_proposition: string
  target_users: list[string]
  success_metrics:
    - metric: string
      target: value
  
  technical_aspects:
    complexity: high|medium|low
    dependencies: list
    architectural_impact: description
    security_considerations: list
  
  implementation:
    estimated_tasks: number
    story_points: number
    required_skills: list
    target_completion: date
```

# Roadmap Document

## Structure
```markdown
# Product Roadmap

## Vision
[Product vision statement]

## Current Status (as of YYYY-MM-DD)
- Completed Features: [list with metrics]
- In Progress: [list with status]
- Planned: [list with dates]

## Short-term Goals (1-2 months)
### Feature Name
- Priority: [high|medium|low]
- Target: YYYY-MM-DD
- Value: [description]
- Tasks: TASK-XXX, TASK-XXX

## Medium-term Goals (3-6 months)
### Q# YYYY
- Feature 1
  - Description
  - Target: Month YYYY
  - Dependencies: [list]

## Long-term Vision (6+ months)
- Strategic Initiative 1
  - Expected Impact
  - Estimated Timeline
  - Success Criteria
```

# Integration Points

## 1. Task Management
```yaml
task_creation:
  location: ".product/tasks/"
  format: task_management_workflow.template
  priority_mapping:
    strategic: high
    enhancement: medium
    maintenance: low
```

## 2. Knowledge Base
```yaml
knowledge_integration:
  patterns:
    - implementation_success
    - common_challenges
    - effort_estimation
  
  metrics:
    - completion_time
    - resource_usage
    - user_adoption
```

# Example Usage
```yaml
# Feature Planning
new_feature:
  name: "Vector Store Integration"
  description: "Implement efficient vector storage for embeddings"
  priority: high
  timeline: "Q1 2025"
  
  tasks:
    - id: "TASK-001"
      description: "Design vector store interface"
      points: 3
    - id: "TASK-002"
      description: "Implement core functionality"
      points: 5
  
  success_metrics:
    - metric: "Query Performance"
      target: "<50ms for 1M vectors"
    - metric: "Storage Efficiency"
      target: "<2GB for 1M vectors"

# Roadmap Update
roadmap_entry: |
  ## Short-term Goals
  ### Vector Store Integration
  - Priority: High
  - Target: March 2025
  - Value: Enable efficient similarity search
  - Dependencies: None
  - Tasks: TASK-001, TASK-002
```

# Guidelines

## Strategic Alignment
- Align features with product vision
- Consider market dynamics
- Balance new features vs improvements
- Account for technical debt

## Resource Planning
- Consider team capacity
- Evaluate skill requirements
- Plan for dependencies
- Include buffer for unknowns

## Documentation
- Keep roadmap up-to-date
- Link to detailed specs
- Document decisions
- Track changes

## Success Tracking
- Define clear metrics
- Set measurable targets
- Monitor progress
- Update based on learnings

Remember: Reference task_management_workflow for task creation and ai_knowledge_base_management for pattern tracking.