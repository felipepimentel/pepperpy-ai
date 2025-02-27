---
title: Task Implementation Template
description: Direct, sequential template focusing only on implementation needs
version: 1.1
---

# Task Structure
All tasks follow this exact file structure:
- Main task file: `.product/tasks/<TASK-ID>/<TASK-ID>.md`

# Task Template
```markdown
---
title: {Task Title}
priority: medium
status: 📋 To Do
created: YYYY-MM-DD
---

## 1. Objective
Clear description of what needs to be implemented.

## 2. Project Structure Context
- Relevant existing files: {paths to relevant files}
- New files to create: {exact paths for new files}

## 3. Implementation Plan
Sequential list of changes to make:

1. {First step: specific change in specific file}
2. {Second step: another specific change}
3. {Third step: create new file with specific content}

## 4. Code Changes

### Existing File: {path/to/file.py}
```python
# Exact code changes to make
```

### New File: {path/to/new_file.py}
```python
# Exact content for the new file
```

## 5. Validation Approach
Manual verification steps to ensure implementation works correctly.
```

# Important Guidelines

1. **ONLY generate exactly what is requested** - no extra tests, docs, or other artifacts unless explicitly asked for

2. **Follow strict sequential implementation order** - each step should build on the previous

3. **Reference existing project structure** - always check `.product/project_structure.yml` first

4. **Keep implementation focused** - include only what's necessary for the specific task

5. **Use absolute file paths** - always specify exact locations for new files

6. **Follow existing patterns** - maintain consistency with the current codebase

7. **Prioritize clarity over completeness** - it's better to be clear about what's needed than to add unnecessary details

DO NOT include sections for tests, documentation, metrics, breaking changes, or other elements unless specifically requested in the task description.
