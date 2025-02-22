---
title: Task Planning Template
description: Template for task planning with clear specifications and implementation details.
version: 4.0
category: planning
tags: [planning, task-management]
yolo: true
strict_mode: true
---

# Task File Location
Tasks should be created in the `.product/tasks/<TASK-ID>/` directory following the naming convention:
- Main task file: `.product/tasks/<TASK-ID>/<TASK-ID>.md`
- Requirement files: `.product/tasks/<TASK-ID>/<TASK-ID>-R{XXX}.md`
- Example: `.product/tasks/TASK-005/TASK-005.md` and `.product/tasks/TASK-005/TASK-005-R001.md`

# Main Task File Template
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

# Objetivo
{Clear task objective and expected outcomes}

# Métricas de Sucesso
- {Metric 1}
- {Metric 2}
- {Metric N}

# Requirements Overview
- [ ] [R001] {Requirement title} - [Details](TASK-XXX-R001.md)
- [ ] [R002] {Requirement title} - [Details](TASK-XXX-R002.md)
- [ ] [R003] {Requirement title} - [Details](TASK-XXX-R003.md)

# Progress Updates

## YYYY-MM-DD
- Current Status: {status}
- Completed: {items}
- Next Steps: {next actions}

# Validation Checklist
- [ ] {Validation item 1}
- [ ] {Validation item 2}

# Breaking Changes
{List of breaking changes}

# Migration Guide
{Migration steps}

# Dependencies
{List of dependencies}
```

# Requirement File Template
```markdown
---
title: {requirement_title}
task: TASK-XXX
code: R001
status: 📋 To Do
created: YYYY-MM-DD
updated: YYYY-MM-DD
started: null
completed: null
---

# Requirement
{Clear requirement description}

# Dependencies
- {Dependency 1}
- {Dependency 2}

## Current State
```python
# Existing code or structure to be modified
```

## Implementation
```python
# Exact code changes and implementation
```

## Validation
```python
def test_requirement():
    # Specific tests for this change
```

## Rollback Plan
1. {Step 1}
2. {Step 2}

## Success Metrics
- [ ] {Metric 1}
- [ ] {Metric 2}

# Progress Updates

## YYYY-MM-DD
- Status: {status}
- Progress: {details}
```

# Task Creation Process

1. **Create Task Directory**
   ```bash
   mkdir -p .product/tasks/TASK-XXX
   ```

2. **Create Main Task File**
   ```bash
   touch .product/tasks/TASK-XXX/TASK-XXX.md
   ```

3. **Create Initial Requirements**
   ```bash
   touch .product/tasks/TASK-XXX/TASK-XXX-R001.md
   touch .product/tasks/TASK-XXX/TASK-XXX-R002.md
   ```

4. **Fill Templates**
   - Use the templates above
   - Keep requirements atomic
   - Include all necessary sections
   - Maintain clear links

# Example Task Structure

```
.product/tasks/TASK-007/
├── TASK-007.md                # Main task file
├── TASK-007-R001.md          # Remove dashboard web
├── TASK-007-R002.md          # Consolidate providers
└── TASK-007-R003.md          # Restructure capabilities
```

Remember: 
1. Each task has its own directory
2. Main task file contains overview and status tracking
3. Each requirement has its own file with complete details
4. Use requirement codes (R001, R002, etc.) for clear referencing
5. Keep all files in sync regarding status updates
6. Include rollback plans for each requirement
7. Maintain clear dependencies between requirements