---
title: Code Style Check
version: "1.0"
scope: "Pepperpy Project"
description: |
  A comprehensive code style validation and enforcement guide.
  Use this prompt when:
  - Reviewing code style compliance
  - Enforcing PEP 8 standards
  - Checking type annotations
  - Implementing style automation
  - Preparing code for review
  
  The prompt helps maintain consistent code style across the project
  and suggests improvements for better code quality.
---

Perform a code style check across the project to ensure adherence to PEP 8 and type annotation standards.
- Run the following tools:
```bash
ruff .
black --check .
```
- Suggest corrections for any non-compliance.
- Log significant findings in `.product/status.md`.

If major style inconsistencies are detected, propose automation scripts or Git hooks for enforcement. 