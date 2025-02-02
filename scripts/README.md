# Development Scripts

This directory contains utility scripts for development and maintenance of the Pepperpy project.

## Check Script

The `check.py` script is a unified validation tool that runs all necessary checks on the codebase:

- Code formatting (black)
- Import sorting (isort)
- Linting (ruff)
- Type checking (mypy)
- Unit tests (pytest)
- Coverage validation
- Project structure validation

### Usage

To run all checks:
```bash
./scripts/check.py
```

To automatically fix issues when possible:
```bash
./scripts/check.py --fix
```

### Exit Codes

- 0: All checks passed
- Non-zero: One or more checks failed

### Requirements

All required dependencies are listed in `requirements-dev.txt`. Install them with:
```bash
pip install -r requirements-dev.txt
```

## Best Practices

1. Run the check script before committing changes
2. Use the `--fix` option to automatically resolve formatting issues
3. Address any remaining linting or type errors manually
4. Ensure test coverage meets requirements (minimum 80%)
5. Keep the project structure valid according to `.product/project_structure.yml` 