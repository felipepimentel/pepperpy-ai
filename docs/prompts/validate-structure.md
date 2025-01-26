---
title: Validate Project Structure
version: "1.0"
scope: "Pepperpy Project"
description: |
  A tool for validating and maintaining project structure integrity.
  Use this prompt when:
  - Adding new modules or components
  - Reorganizing project files
  - Checking structural compliance
  - Updating project architecture
  - Preparing for releases
  
  The prompt ensures the project structure remains aligned with
  the defined architecture and helps prevent structural drift.
---

Run `./scripts/validate_structure.py` to ensure compliance with `project_structure.yml`.  
In case of discrepancies:
- Log unexpected items or missing paths.
- Create or remove files as necessary, aligning with project architecture.
- Update `project_structure.yml` if changes represent valid new features. 