---
title: Test Coverage Improvement
version: "1.0"
scope: "Pepperpy Project"
description: |
  A systematic approach to improving test coverage across the project.
  Use this prompt when:
  - Analyzing current test coverage
  - Identifying gaps in testing
  - Adding tests for new features
  - Improving critical module coverage
  - Preparing for releases
  
  The prompt ensures comprehensive test coverage and helps maintain
  code reliability through systematic test improvements.
---

Analyze the current test coverage for the project.  
- Identify files or modules with insufficient coverage (<90%).
- Suggest new test cases for edge scenarios and error conditions.
- Add missing tests to critical modules (e.g., `pepperpy/core` and `pepperpy/providers`).
- Update `/docs/status.md` to reflect test improvements.

Run the following to validate coverage:
```bash
pytest --cov=pepperpy
``` 