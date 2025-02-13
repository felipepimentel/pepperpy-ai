---
title: AI Task Execution Protocol
description: ALWAYS use when executing task actions to ensure systematic progress following established task management standards. This protocol ensures deterministic AI-driven task execution aligned with workflow rules.
version: 1.2
category: task-execution
tags: [execution, ai-driven]
yolo: true
strict_mode: true
---

# Task Processing Protocol

## 1. Initial Validation
```yaml
validate:
  file:
    path: ".product/tasks/TASK-{ID}.md"
    exists: required
    format: required

  required_sections:
    - Status
    - Business Context
    - Technical Scope
    - Requirements
    - Dependencies
    - Progress Updates
    - Outcome

  status_format:
    current: "^(📋 To Do|🏃 In Progress|⏳ Blocked|✅ Done)$"
    priority: "^(High|Medium|Low)$"
    points: "^(1|2|3|5|8|13)$"
    mode: "^(Plan|Act)$"
```

## 2. State Analysis
```yaml
analyze:
  current_state:
    extract:
      - status: required
      - requirements: required
      - progress: required
      - dependencies: required

  requirements:
    patterns:
      completed: "^- \\[x\\] ([^\\n]+)  # ✅ \\d{4}-\\d{2}-\\d{2}$"
      in_progress: "^- \\[-\\] ([^\\n]+)  # 🏃 Started: \\d{4}-\\d{2}-\\d{2}$"
      pending: "^- \\[ \\] ([^\\n]+)$"

  dependencies:
    check:
      - systems
      - apis
      - tasks
      - tools
```

# Execution Flow

## 1. Status Transitions
```yaml
transitions:
  📋 To Do -> 🏃 In Progress:
    validate:
      - task_branch_created
      - all_requirements_defined
      - dependencies_resolved
      - technical_scope_approved
    
  🏃 In Progress -> ✅ Done:
    validate:
      - all_requirements_implemented
      - tests_passing
      - documentation_updated
      - code_reviewed
    
  🏃 In Progress -> ⏳ Blocked:
    validate:
      - blocker_identified
      - next_steps_documented
      - timeline_estimated
```

## 2. Progress Documentation
```yaml
progress_update:
  format: |
    - {YYYY-MM-DD}:
      - Current Status: {specific_details}
      - Completed Items: 
        - {item_1}
        - {item_2}
      - Next Steps:
        1. {step_1}
        2. {step_2}
      [if blocked] - Blockers: {specific_issues}
```

## 3. Requirement Updates
```yaml
requirement_update:
  completion:
    format: "- [x] {requirement}  # ✅ {YYYY-MM-DD}"
    requires:
      - implementation_verified
      - tests_passed
      - docs_updated
  
  in_progress:
    format: "- [-] {requirement}  # 🏃 Started: {YYYY-MM-DD}"
    requires:
      - clear_next_steps
      - no_other_active
```

# Knowledge Base Integration

## 1. Read Operations
```yaml
knowledge_query:
  task_creation:
    - patterns
    - dependency_patterns
  
  status_change:
    - duration_tracking
    - metrics
  
  complexity_estimation:
    - similar_tasks
    - effort_patterns
```

## 2. Write Operations
```yaml
knowledge_update:
  completion:
    patterns:
      - implementation_pattern
      - challenges_faced
      - resolution_steps
    
  status_change:
    metrics:
      - duration
      - blockers

  validation:
    - schema_check
    - data_consistency
```

# Execution Examples

## 1. Starting Task
```yaml
# Initial State
task:
  status: 📋 To Do
  ready:
    - branch_created: true
    - requirements_defined: true
    - dependencies_resolved: true

# Execution
action:
  1. Update Status:
     status: 🏃 In Progress
     update_timestamp: true
  
  2. Add Progress:
     - 2025-02-12:
       - Current Status: Starting implementation
       - Completed Items:
         - Repository setup
         - Initial structure
       - Next Steps:
         1. Implement base classes
         2. Add unit tests
```

## 2. Requirement Management
```yaml
# Update Requirement
requirement:
  completion:
    before: "- [-] Implement API Authentication  # 🏃 Started: 2025-02-12"
    after: "- [x] Implement API Authentication  # ✅ 2025-02-12"
    
  progress_update:
    - Current Status: Authentication implementation complete
    - Completed Items:
      - OAuth flow implemented
      - Tests added
      - Documentation updated
    - Next Steps:
      1. Start error handling implementation
```

# Validation Rules

## 1. Pre-execution
```yaml
validate:
  task_file:
    - exists
    - correct_format
    - valid_status
  
  requirements:
    - defined
    - no_duplicates
    - clear_criteria
  
  dependencies:
    - resolved
    - accessible
```

## 2. During Execution
```yaml
monitor:
  status_changes:
    - valid_transition
    - requirements_met
    - documentation_updated
  
  progress:
    - specific_updates
    - clear_next_steps
    - blocker_documentation
```

## 3. Post-execution
```yaml
verify:
  completion:
    - all_requirements_met
    - tests_passing
    - documentation_complete
  
  knowledge_base:
    - patterns_updated
    - metrics_recorded
```

Remember: 
- Follow task_management_workflow rule exactly
- Update knowledge base on specified triggers
- Maintain precise formatting
- Keep updates specific and actionable
- Document all transitions fully
- Validate all requirements before status changes