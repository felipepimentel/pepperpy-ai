---
title: Task Execution Template
description: Structured execution framework ensuring format integrity, automated conflict resolution, and duplication prevention.
version: 7.1
category: execution
tags: [execution, implementation, refactoring, conflict-resolution, automation, structure]
yolo: true
strict_mode: true
---

# Task File Access
All task files are located at `.product/tasks/<TASK-ID>/`. For example:
- Main task file: `.product/tasks/TASK-004/TASK-004.md`
- Requirement files: `.product/tasks/TASK-004/TASK-004-R001.md`

# **Execution Environment**
Before running any `poetry` command, always execute the following setup to ensure the correct environment is loaded:

```sh
export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
export PYTHONHOME=""
export PYTHONPATH=""
poetry <desired_command>
```

# **Execution Rules**
```yaml
validation:
  pre_execution:
    task_status:
      - if main task status is "✅ Done": respond "Task is already completed" and stop
      - if main task status not in ["📋 To Do", "🏃 In Progress"]: stop
    task_format:
      - verify main task frontmatter completeness
      - verify requirement files exist and are complete
      - verify requirements format in each file
      - verify task structure matches original plan
      - verify no unauthorized modifications
    structure_analysis:
      - before creating any file or folder:
        - list all existing directories and files under `pepperpy/`
        - analyze potential **structural conflicts**
        - if a conflict is detected:
          - refactor existing structure instead of creating a duplicate
          - update **all module imports and references** accordingly
          - execute:
            ```sh
            export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
            export PYTHONHOME=""
            export PYTHONPATH=""
            poetry run python ./scripts/export_structure.py
            ```
```

# **Structural Conflict Resolution**
```yaml
conflict_resolution:
  - before creating a new folder or file:
      ```sh
      tree pepperpy/ > .product/current_structure.txt
      ```
  - analyze `.product/current_structure.txt` to:
      - check if a similar folder or file already exists
      - determine if the existing module/folder should be reused instead of duplicating
      - refactor and integrate new logic into the existing structure when needed
      - update all references to ensure consistency
      - delete redundant folders/files only after successful refactoring
  - after any structural modification, **ensure the project structure is updated** by running:
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      poetry run python ./scripts/export_structure.py
      ```
```

# **Code Duplication Prevention**
```yaml
code_maintenance:
  pre_execution:
    - before implementing a feature, scan all modules for similar logic:
      ```sh
      rg '<feature_keyword>' pepperpy/
      ```
    - if a similar implementation exists:
      - **extend or refactor** the existing module instead of creating a new one
      - ensure **feature flags or modular architecture** if different behaviors are needed
  post_execution:
    - detect function redefinitions:
      ```sh
      ruff check --select=F811
      ```
    - detect and remove unused imports:
      ```sh
      ruff check --select=F401
      ```
```

# **Main Task File Template**
```markdown
---
title: {title}
priority: high|medium|low
points: 1|2|3|5|8|13
status: 🏃 In Progress
mode: Act
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Requirements Overview
- [-] [R001] {title} - [Details](TASK-XXX-R001.md)  # 🏃 Started: YYYY-MM-DD
- [ ] [R002] {title} - [Details](TASK-XXX-R002.md)
- [x] [R003] {title} - [Details](TASK-XXX-R003.md)  # ✅ Done: YYYY-MM-DD

# Progress Updates

## YYYY-MM-DD
- Current Status: {specific implementation detail}
- Completed:
  - [R003] {specific implemented item} ✅
- In Progress:
  - [R001] {specific item being worked on} 🏃
- Next:
  - [R002] {specific next item} ⏳
```

# **Refactoring Strategy**
```yaml
refactoring:
  structure:
    - consolidate duplicated modules before implementing new features
    - extract shared logic into reusable components
    - modularize features to avoid code repetition
  automation:
    - automatically remove dead code:
      ```sh
      ruff check --select=F401,F841
      ```
    - format code for consistency:
      ```sh
      black pepperpy/
      ```
```

# **Example Conflict Resolution Flow**
### **Before Creating a New Folder**
**Scenario:** A new folder `pepperpy/core/new_feature/` is about to be created, but `pepperpy/new_feature/` already exists.

### **Correct Approach**
1. **List the current project structure**
    ```sh
    tree pepperpy/ > .product/current_structure.txt
    ```
2. **Check if a similar module already exists**
    ```sh
    rg 'new_feature' pepperpy/
    ```
3. **Refactor and integrate the new logic within the existing structure**
4. **Update all import references**
5. **Ensure the project structure is updated**
    ```sh
    export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
    export PYTHONHOME=""
    export PYTHONPATH=""
    poetry run python ./scripts/export_structure.py
    ```
6. **Remove the redundant directory (if applicable)**
    ```sh
    rm -rf pepperpy/core/new_feature/
    ```

---

# **Automated Structure Update**
```yaml
structure_update:
  - after any structural change, **immediately update the project structure**:
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      poetry run python ./scripts/export_structure.py
      ```
```