---
title: Adaptive Task Execution Template
description: Intelligent execution framework ensuring structural integrity, contextual conflict resolution, and automated validation before modifying the project.
version: 9.0
category: execution
tags: [execution, validation, structure, refactoring, automation, contextual-analysis]
yolo: true
strict_mode: true
---

# Task File Access
All task files are located at `.product/tasks/<TASK-ID>/`. For example:
- Main task file: `.product/tasks/TASK-004/TASK-004.md`
- Requirement files: `.product/tasks/TASK-004/TASK-004-R001.md`

# **Execution Environment**
Before running any command, **always ensure the correct environment is loaded**:

```sh
export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
export PYTHONHOME=""
export PYTHONPATH=""
poetry <desired_command>
```

---

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
      - **Instead of just checking names, approximate intent and functionality:**
        - List all **existing** directories and files under `pepperpy/`
        - Classify each directory based on **role (e.g., core logic, integrations, utilities, tests)**
        - Identify **structural patterns** (e.g., multiple `handlers/` directories in different places)
      - **If a new file or directory is about to be created:**
        - Approximate its **intended role** and compare with existing elements
        - **If an equivalent structure already exists:**
          - Stop new creation
          - Suggest refactoring into the existing structure
          - Update all module references
        - **If structure evolution is required:**
          - Allow creation but ensure proper linking
      - Always execute:
        ```sh
        export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
        export PYTHONHOME=""
        export PYTHONPATH=""
        poetry run python ./scripts/export_structure.py
        ```
```

---

# **Context-Aware Structural Conflict Resolution**
```yaml
conflict_resolution:
  - before creating a new folder or file:
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      tree pepperpy/ > .product/current_structure.txt
      ```
  - Analyze `.product/current_structure.txt` to:
      - **Classify each directory and file based on purpose**
      - **Detect similar names and similar roles**
      - **If two directories/files serve the same functional purpose, merge them**
      - **If duplication is found, automatically refactor and update references**
  - After **any** modification, validate again:
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      poetry run python ./scripts/export_structure.py
      ```
```

---

# **Duplication Prevention with Semantic Matching**
```yaml
code_maintenance:
  pre_execution:
    - Before implementing a feature, **search for conceptually similar logic, not just identical names:**
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      rg '<feature_concept>' pepperpy/
      ```
    - If a similar implementation exists:
      - **Extend or refactor the existing module instead of creating a new one**
      - Ensure **feature flags or modular architecture** if different behaviors are needed
  post_execution:
    - Detect function redefinitions:
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      poetry run ruff check --select=F811
      ```
    - Detect and remove unused imports:
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      poetry run ruff check --select=F401
      ```
```

---

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

---

# **Automated Structure Update**
```yaml
structure_update:
  - After any structural change, **immediately validate the project structure**:
      ```sh
      export PATH="/home/pimentel/.pyenv/versions/3.12.4/bin:$PATH"
      export PYTHONHOME=""
      export PYTHONPATH=""
      poetry run python ./scripts/export_structure.py
      ```
  - If validation fails:
      - Halt further execution
      - Print **detailed errors** to diagnose the issue
      - Suggest a refactor plan before retrying
```