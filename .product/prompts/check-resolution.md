---
title: "Check Resolution"
description: "Instructions for AI to continuously execute check.sh and resolve issues"
version: "1.0.1"
tags: [checks, automation, continuous]
---

# Check Resolution Instructions

Execute and resolve `check.sh` issues continuously until all checks pass. This process should be iterative, learning from each failure, applying fixes, and refining strategies as needed.

---

## 1. Run the Unified Check Script

```bash
./scripts/check.sh [--fix]
```

This script performs multiple validations in sequence:

- **Code formatting** (`black`)
- **Import sorting** (`isort`)
- **Linting** (`ruff`)
- **Type checking** (`mypy`)
- **Unit tests** (`pytest`)
- **Project structure validation**

> **Tip**: Always check if `--fix` is supported for auto-remediations (e.g., `black`, `isort`, and some `ruff` fixes).  

---

## 2. Iterate and Analyze Output

For each iteration:
- Parse the output of `check.sh` to identify pass/fail indicators, such as:
  ```
  ✓ Code Formatting
  ✓ Import Sorting
  ✓ Linting
  ✓ Type Checking
  ✓ Unit Tests
  ✓ Project Structure
  ```
- Prioritize failures by severity:
  1. **Critical**: Security concerns, serious type errors
  2. **High**: Test failures, structural issues
  3. **Medium**: Coverage gaps
  4. **Low**: Style/formatting discrepancies

> **Note**: Collect any error messages or logs associated with each failure to better inform subsequent fixes.

---

## 3. Resolution Strategy

1. **Start with Auto-Fixable Issues**  
   - Run:
     ```bash
     ./scripts/check.sh --fix
     ```
   - Apply all safe automated fixes first to reduce the list of failures.

2. **Group Similar Issues**  
   - If multiple files share the same type of error, address them in batches for consistency.

3. **Fix One Category at a Time**  
   - For instance, tackle formatting first, then import sorting, followed by linting, type checks, etc.

4. **Verify After Each Fix**  
   - Rerun `check.sh` to confirm that the applied fix indeed resolved the issue (and didn't introduce new ones).

5. **Document Patterns Found**  
   - Keep track of recurring errors or anti-patterns to streamline future corrections.

---

## 4. Common Issues

- **Black formatting**: Typically resolved by running with `--fix`.
- **Import sorting**: Also typically resolved by running with `--fix`.
- **Ruff linting**: Check which specific error codes are triggered (e.g., `F401` for unused imports).
- **Mypy errors**: Investigate missing or incorrect type hints.
- **Test failures**: Verify test logic, especially assertion correctness.
- **Coverage gaps**: Add or refine tests to increase coverage.
- **Structure issues**: 
  - Strictly validate against `project_structure.yml`
  - Do not create directories not defined in the structure
  - All code must be organized within existing defined modules
  - No ad-hoc creation of new top-level directories
  - Use only the defined module structure (core, memory, capabilities, etc.)
  - Report any structural violations immediately
  - Ensure all imports follow the defined structure
  - No duplicate functionality between modules
  - Core functionality must stay in core module
  - No creation of alternative core-like modules (e.g., common, shared, etc.)

---

## 5. Stop Conditions

- All `check.sh` validations pass (exit code 0).
- No warnings appear in the output.
- Coverage meets or exceeds the defined threshold (e.g., ≥80%).
- A clean summary report indicates no further issues.

---

## 6. Learning Loop

- **Track Successful Fixes**: Note which remediation steps consistently solve particular errors.
- **Observe Recurring Issues**: Identify patterns or repeated mistakes to improve processes or documentation.
- **Refine Strategies**: Update your resolution approach as new tools or complexities arise.
- **Share Insights with the User**: Communicate any newly discovered best practices or configurations.

---

### Remember

- Use `--fix` for safe auto-fixes whenever possible.
- Keep the user informed of progress and any major changes made.
- Request user guidance if complex or ambiguous issues appear.
- Document all newly discovered patterns to aid future iterations.