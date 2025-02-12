---
title: Continuous Test Resolution
description: Instructions for AI to continuously execute and resolve test issues
version: 1.0.0
tags: [testing, automation, continuous]
---

# Continuous Test Resolution Instructions

Execute and resolve test issues continuously until all checks pass. Follow this systematic approach:

1. Run the validation script:
   ```bash
   python ./scripts/check.py
   ```

2. For each iteration:
   - Analyze the output for:
     - Test failures
     - Deprecation warnings
     - Coverage gaps
     - Linting issues
   - Prioritize issues by severity
   - Apply fixes systematically
   - Verify changes with another run

3. Common Issues and Solutions:
   - AttributeError: Check class definitions and imports
   - TypeError: Validate parameter types and function signatures
   - ImportError: Verify import paths and package installation
   - IndentationError: Fix code formatting
   - Coverage gaps: Add missing test cases

4. Error Resolution Strategy:
   - Start with quick wins (formatting, imports)
   - Group similar issues for batch fixes
   - Address test failures systematically
   - Improve coverage with targeted tests
   - Document patterns for future reference

5. Stop Conditions:
   - All tests passing
   - No warnings
   - Coverage meets threshold (≥80%)
   - Clean linting report

6. Learning Loop:
   - Track successful fix patterns
   - Note recurring issues
   - Update resolution strategies
   - Share insights with user

Remember:
- Use --fix flag when appropriate
- Keep user informed of progress
- Request guidance if stuck
- Document new patterns learned 