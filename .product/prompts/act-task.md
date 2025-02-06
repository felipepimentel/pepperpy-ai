---
title: Act Task
description: Template for executing tasks and creating necessary rules
version: "1.2"
category: execution
tags: [execution, implementation, rules]
---

# Context
This prompt helps in executing tasks, including:
1. Creating necessary rules
2. Implementing changes
3. Updating documentation
4. Validating changes
5. Updating task status

# Safety Rules

## 1. Task File Validation (CRITICAL)
- **MUST** have access to `.product/tasks/TASK-{ID}.md`
- **MUST** validate task file exists before ANY action
- **MUST** prevent hallucination of requirements
- **MUST** stop execution if task file not found
- **MUST** validate task ID matches the file content

## 2. Task Status Updates (REQUIRED)
- **MUST** update task file after EVERY action
- **MUST** mark requirements as they are completed
- **MUST** document progress, blockers, and issues
- **MUST** maintain an audit trail of changes
- **MUST** update timestamps for each change

## 3. Task File Structure
- **MUST** maintain original task structure
- **MUST** use consistent markdown formatting
- **MUST** update progress in designated sections
- **MUST** preserve task metadata
- **MUST** follow the template format

# Input Format
```yaml
task:
  id: string  # Task ID (e.g., "TASK-008")
  file: string  # Path to task file (REQUIRED)
  mode: init|execute|validate  # Execution mode
```

# Validation Steps

## 1. Pre-Execution Validation
```python
def validate_task_file(task_id: str, file_path: str) -> bool:
    """
    MUST be called before any execution.
    Returns False if validation fails, stopping execution.
    """
    if not os.path.exists(file_path):
        logger.error(f"Task file not found: {file_path}")
        return False
        
    content = read_file(file_path)
    if not content.startswith(f"# TASK-{task_id}"):
        logger.error(f"Task ID mismatch in {file_path}")
        return False
        
    return True
```

## 2. Task Update Format
```markdown
## Requirements
- [x] Completed requirement  # ✅ Done: 2024-03-21
- [-] In progress requirement  # ⏳ Started: 2024-03-21
- [ ] Pending requirement

## Progress Notes
- 2024-03-21 14:30: Completed initial setup
  - Added base structure
  - Implemented core interface
  - BLOCKER: Waiting for API access

## Validation
- ✅ Type checking passed
- ⏳ Integration tests running
- ❌ Performance tests failed
```

# Example Usage

## 1. Task File Validation
```yaml
# First, validate task file exists
validation:
  task_file: ".product/tasks/TASK-008.md"
  exists: true  # MUST be true to proceed
  content_valid: true  # MUST be true to proceed
  
# Only proceed if validation passes
execution:
  task_updates:
    - requirement: "Create provider protocol"
      status: "complete"
      timestamp: "2024-03-21T14:30:00Z"
      notes: "Implemented base protocol with type safety"
```

## 2. Progress Update
```yaml
# After each action, update task file
updates:
  file: ".product/tasks/TASK-008.md"
  changes:
    - type: "requirement_update"
      requirement: "Implement OpenAI provider"
      status: "complete"
      timestamp: "2024-03-21T15:45:00Z"
    
    - type: "progress_note"
      timestamp: "2024-03-21T15:45:00Z"
      note: "Completed OpenAI provider implementation"
      details:
        - "Added async support"
        - "Implemented rate limiting"
        - "Added comprehensive error handling"
```

# Task Update Rules

## 1. Requirement Updates
- Use checkboxes: `- [x]`, `- [-]`, `- [ ]`
- Add timestamps for changes
- Document partial progress
- Note any blockers

## 2. Progress Notes
- Include timestamp for each entry
- Be specific about changes made
- Document any issues or decisions
- Reference related components

## 3. Validation Updates
- Document test results
- Note any failures
- Track performance metrics
- List pending validations

# Error Handling

## 1. Task File Missing
```yaml
error:
  type: "TASK_FILE_MISSING"
  message: "Cannot proceed: Task file not found"
  action: "STOP_EXECUTION"
```

## 2. Task ID Mismatch
```yaml
error:
  type: "TASK_ID_MISMATCH"
  message: "Task ID in file does not match requested ID"
  action: "STOP_EXECUTION"
```

## 3. Invalid Update
```yaml
error:
  type: "INVALID_UPDATE"
  message: "Cannot update task: Invalid format"
  action: "RETRY_WITH_VALID_FORMAT"
```

# Implementation Guidelines

1. **Always Validate First**
   - Check task file exists
   - Validate task ID
   - Verify file structure

2. **Update After Each Action**
   - Mark completed requirements
   - Add progress notes
   - Document any issues

3. **Maintain Consistency**
   - Follow template format
   - Use consistent timestamps
   - Preserve metadata

4. **Error Prevention**
   - Stop on missing task file
   - Validate before updates
   - Document all errors

# Output Format
```yaml
execution:
  # Task File Validation
  task_validation:
    exists: bool  # Whether task file exists
    requirements: list[str]  # List of requirements from task
    current_status: dict  # Current completion status
  
  # Rule Creation (if needed)
  rule:
    path: string  # Rule file path
    content: string  # Rule content
    validation: dict  # Validation results
  
  # Implementation
  changes:
    - file: string  # File path
      type: create|modify|delete
      content: string  # Changes to make
  
  # Documentation Updates
  documentation:
    - path: string
      updates: string
  
  # Task Updates
  task_updates:
    - requirement: string  # Requirement being updated
      status: complete|in_progress|blocked
      notes: string  # Update notes
  
  # Validation
  validation:
    status: pass|fail
    issues: list[string]
    next_steps: list[string]
```

# Example Usage
```yaml
input:
  task:
    id: "TASK-008"
    file: ".product/tasks/TASK-008.md"
    plan:  # From plan-task.md output
      task_id: "TASK-008"
      required_rules:
        - name: "providers-rules"
          reason: "Define provider implementation standards"
          scope: "pepperpy.providers"
      # ... other plan details ...
    
    current_subtask: "TASK-008.1"
    mode: "init"  # Creating initial setup including rules

output:
  execution:
    task_validation:
      exists: true
      requirements:
        - "Create clean module interface through __init__.py"
        - "Implement provider protocol and core interfaces"
        # ... other requirements ...
      current_status:
        completed: []
        in_progress: ["Create clean module interface through __init__.py"]
        pending: ["Implement provider protocol and core interfaces"]
    
    rule:
      path: ".cursor/rules/providers-rules.mdc"
      content: |
        # Provider implementation rules...
    
    changes:
      - file: "pepperpy/providers/__init__.py"
        type: "create"
        content: |
          """Clean module interface..."""
    
    documentation:
      - path: ".product/tasks/TASK-008.md"
        updates: |
          ## Requirements
          - [x] Create clean module interface through __init__.py
          - [ ] Implement provider protocol and core interfaces
          # ... other updates ...
    
    task_updates:
      - requirement: "Create clean module interface through __init__.py"
        status: complete
        notes: "Created clean public API with proper exports and documentation"
    
    validation:
      status: "pass"
      issues: []
      next_steps:
        - "Implement provider protocol"
        - "Add core interfaces"
```

# Usage
1. Start with task file validation
2. Execute in phases:
   - init: Setup including rules
   - execute: Implement changes
   - validate: Verify changes
3. Update task file with progress

# Execution Modes

## YOLO Mode (Continuous Execution)
- Validate task file exists
- Enable continuous execution
- Auto-proceed through requirements
- Maintain execution context
- Update progress continuously
- Stop only on completion or critical error

## Init Mode
- Validate task file exists
- Create necessary rules
- Setup initial structure
- Prepare documentation
- Update task status

## Execute Mode
- Validate current requirements
- Implement changes
- Update documentation
- Update task progress
- Apply rules

## Validate Mode
- Check rule compliance
- Run tests
- Verify documentation
- Update task completion status

# Task File Updates

## Progress Tracking
```markdown
## Requirements
- [x] Requirement 1  # Completed
- [-] Requirement 2  # In Progress
- [ ] Requirement 3  # Pending
```

## Status Updates
```markdown
## Progress Notes
- 2024-03-21: Completed initial setup
- 2024-03-22: Implementing core features
  - Added base protocol
  - Working on provider engine
```

## Blocker Documentation
```markdown
## Blockers
- [ ] Dependency X needs update
- [ ] Waiting for API access
```

# Task Completion Rules

## 1. Completion Validation (CRITICAL)
- **MUST** validate ALL requirements are met
- **MUST** check ALL validation criteria
- **MUST** verify ALL documentation is updated
- **MUST** confirm task file reflects completion
- **MUST** update kanban.md with completion status

## 2. Completion Markers
```yaml
completion:
  status: complete|incomplete
  requirements_met: bool
  validation_passed: bool
  documentation_updated: bool
  timestamp: datetime
  summary: string
  
  # If complete, MUST include
  completion_notice: |
    =====================================
    🎉 TASK-XXX COMPLETED SUCCESSFULLY 🎉
    =====================================
    Summary: Brief completion summary
    Time: 2024-03-21 15:45:00 UTC
    All requirements met: ✅
    All validation passed: ✅
    Documentation updated: ✅
    
    No further actions required.
    =====================================
```

## 3. Scope Control
```yaml
scope_validation:
  in_scope: bool  # MUST be true to proceed
  remaining_requirements: list[str]  # MUST be empty for completion
  blocked_by: list[str]  # MUST be empty for completion
  dependencies_met: bool  # MUST be true to proceed
```

## 4. Completion Checklist
```markdown
## Final Validation
- [ ] All requirements marked complete
- [ ] All validation criteria passed
- [ ] All documentation updated
- [ ] All tests passing
- [ ] Kanban status updated
- [ ] Task file updated
- [ ] No remaining TODOs
- [ ] No pending validations

## Completion Declaration
When ALL items above are checked:

✨ TASK COMPLETION NOTICE ✨
- Status: COMPLETED
- Date: YYYY-MM-DD HH:MM:SS UTC
- All requirements satisfied
- All validation criteria met
- Documentation fully updated

NO FURTHER ACTIONS AUTHORIZED
```

# Output Format
```yaml
execution:
  # ... existing validation and updates ...
  
  # Completion Status (REQUIRED)
  completion:
    is_complete: bool
    requirements_status:
      total: int
      completed: int
      remaining: list[str]
    validation_status:
      passed: bool
      pending: list[str]
    documentation_status:
      updated: bool
      pending: list[str]
    
    # If complete, MUST include completion notice
    completion_notice: |
      =====================================
      🎉 TASK COMPLETION NOTIFICATION 🎉
      =====================================
      Task ID: TASK-XXX
      Status: COMPLETED
      Time: YYYY-MM-DD HH:MM:SS UTC
      
      All requirements met: ✅
      All validation passed: ✅
      Documentation updated: ✅
      
      Summary:
      - What was accomplished
      - Key implementations
      - Notable outcomes
      
      No further actions required.
      =====================================
```

# Implementation Guidelines

## 1. Completion Validation
- Check EVERY requirement is met
- Verify EVERY validation criteria
- Confirm ALL documentation updated
- Ensure task file reflects completion
- Update kanban.md status

## 2. Scope Control
- Stop execution if task complete
- Prevent actions outside scope
- Validate remaining requirements
- Check dependency completion

## 3. Completion Notice
- MUST be visually distinct
- MUST include all validation statuses
- MUST include timestamp
- MUST include summary
- MUST declare no further actions

## 4. Error Prevention
- Stop if attempting post-completion actions
- Validate scope before each action
- Prevent partial completion declarations
- Require all checks before completion

# Error Handling

## 1. Post-Completion Attempt
```yaml
error:
  type: "POST_COMPLETION_ACTION_ATTEMPTED"
  message: "⛔ Task already completed. No further actions allowed."
  action: "STOP_EXECUTION"
```

## 2. Incomplete Declaration
```yaml
error:
  type: "INVALID_COMPLETION_DECLARATION"
  message: "Cannot declare completion: Pending requirements or validations"
  action: "LIST_PENDING_ITEMS"
```

# YOLO Mode Execution

## 1. Continuous Execution Rules
- **MUST** continue execution until task is fully complete
- **MUST** validate completion status after each action
- **MUST** automatically proceed to next requirement if current is complete
- **MUST** maintain execution context between actions
- **MUST** track progress and update task file continuously

## 2. YOLO Mode Configuration
```yaml
execution_mode:
  yolo: true  # Enable continuous execution
  stop_conditions:
    - task_completed: true
    - critical_error: true
    - user_interrupt: true
  
  progress_tracking:
    update_frequency: "after_each_action"
    persist_context: true
    auto_proceed: true
```

## 3. Execution Flow
```python
async def yolo_execution(task: Task):
    """Execute task in YOLO mode until completion."""
    while not task.is_completed():
        # Get next action
        action = await task.get_next_action()
        
        # Execute action
        try:
            result = await action.execute()
            await task.update_progress(action, result)
            
            # Validate and proceed
            if action.is_complete():
                await task.proceed_to_next()
        except CriticalError:
            await task.mark_blocked()
            break
            
        # Update task file
        await task.save_state()
```

## 4. Progress Persistence
```yaml
yolo_state:
  current_action: str
  completed_actions: list[str]
  pending_actions: list[str]
  context:
    last_update: datetime
    execution_path: list[str]
    results: dict
```

## 5. Auto-Proceed Rules
- Complete current requirement ➔ Auto-start next
- Complete subtask ➔ Auto-start next subtask
- Complete validation ➔ Auto-start next validation
- Complete implementation ➔ Auto-start testing
- Complete testing ➔ Auto-start documentation

## 6. State Management
```yaml
state_management:
  persist:
    frequency: "after_each_action"
    locations:
      - task_file
      - execution_log
      - progress_tracker
  
  recovery:
    enabled: true
    strategy: "resume_from_last_action"
    context_preservation: true
```

# Task Execution Guidelines

## Pre-execution Checklist
1. Review task requirements and dependencies
2. Check current project state
3. Validate project structure:
   ```bash
   python scripts/validate_structure.py
   ```
   - If validation fails, fix structure issues before proceeding
   - All code must follow the defined project structure

## During Execution
1. Follow task specifications
2. Maintain project structure integrity
3. Run structure validation after any file/directory changes:
   ```bash
   python scripts/validate_structure.py
   ```
4. Fix any structural violations immediately

## Post-execution Checklist
1. Verify all changes follow project structure
2. Run final structure validation:
   ```bash
   python scripts/validate_structure.py
   ```
3. Update documentation if needed
4. Commit changes with appropriate message

## Structure Rules
- All code must be in appropriate modules
- Follow defined directory structure
- No tests in main package
- Each module must have __init__.py
- Use correct import patterns
- No direct model access outside providers
- Use centralized logging

## Common Issues
1. Wrong module placement
   - Check `.product/project_structure.yml`
   - Move files to correct location
2. Missing __init__.py
   - Add to all package directories
3. Incorrect imports
   - Use proper import paths
   - Follow dependency rules
4. Direct model access
   - Use provider abstractions
   - No direct API calls

## Validation Errors
If structure validation fails:
1. Read error messages carefully
2. Fix each violation
3. Re-run validation
4. Do not proceed until all checks pass

Remember: Structure validation is mandatory before, during, and after task execution. 