# PepperPy Cursor Rules System

This document provides instructions for setting up and using the PepperPy Cursor Rules system, which helps guide AI-assisted development and ensures consistent, high-quality code.

## Quick Start

### Initialize Rules System

The rules system can be initialized with the following commands:

```bash
# Make the initialization script executable
chmod +x scripts/initialize-rules.sh

# Run the initialization script
./scripts/initialize-rules.sh
```

This process:
1. Backs up any existing rules
2. Sets up the new rules structure
3. Creates the auto-generated rules directory
4. Performs an initial rule scan

## Working with Rules

### Rules Organization

Rules are organized into a hierarchical numbering system:

1. **000-099**: Core framework rules
   - Architecture, standards, and general principles

2. **100-199**: Domain-specific rules
   - Rules for specific domains (RAG, workflows, etc.)

3. **180-205**: Code quality and maintenance rules
   - Rules for preventing duplication, maintaining structure, and ensuring proper API evolution
   - Tools for validating AI-generated code and preventing hallucinations
   - Processes for rules evolution and self-correction

4. **200-299**: Meta rules
   - Rules about rules management
   - Self-updating mechanisms

5. **300-399**: Documentation rules
   - Standards for documentation
   - API documentation patterns

6. **400-499**: Tooling rules
   - CI/CD pipelines
   - Development tools integration

7. **500-599**: Extension rules
   - Plugin development
   - Extension patterns

8. **auto-generated/**: Auto-generated rules
   - Rules created by automated processes
   - Updated when the codebase changes

### Preventing Common AI Code Issues

The code quality rules (180-205) specifically address common issues in AI-generated code:

1. **Code Duplication Prevention (180)**
   - Strategies for detecting and eliminating duplicated code
   - Commands:
     ```bash
     python scripts/refactor.py detect-smells --directory pepperpy
     python scripts/refactor.py find-small-dirs --directory pepperpy
     ```

2. **File Organization (185)**
   - Guidelines for maintaining consistent project structure
   - Commands:
     ```bash
     python scripts/refactor.py validate
     ```

3. **API Evolution (190)**
   - Patterns for safely evolving APIs with backward compatibility
   - Commands:
     ```bash
     python scripts/refactor.py extract-api --module pepperpy/module_name
     ```

4. **AI Response Validation (195)**
   - Techniques for preventing AI hallucinations and ensuring accurate code
   - Verification checklists and validation processes

5. **Refactoring Tools Usage (200)**
   - Guidelines for effectively using the PepperPy refactoring tools
   - Workflow examples for common refactoring scenarios

6. **Rule Evolution (205)**
   - Processes for updating rules when AI errors are identified
   - Self-improvement mechanisms for the rules system

## Single Tool Approach

PepperPy follows the principle of unified tooling - using a single tool (`refactor.py`) for all code maintenance and rule management operations:

```bash
# All operations are performed through the refactor.py script
python scripts/refactor.py [command] [options]
```

This approach:
- Eliminates tool fragmentation
- Simplifies the developer experience
- Ensures consistent operations
- Makes the system easier to maintain

## Managing Rules

### View Rules

To view rules, simply open the rule files in the `.cursor/rules/` directory.

### Create New Rules

To create a new rule:

```bash
python scripts/refactor.py rule-management --generate --name "Rule Name" --category XXX
```

Where `XXX` is the category number (e.g., 100 for domain-specific rules).

### Validate Rules

To validate all rules for correct formatting:

```bash
python scripts/refactor.py rule-management --validate
```

### Update Auto-Generated Rules

To update auto-generated rules based on the current codebase:

```bash
python scripts/refactor.py rule-management --scan
```

### Update Rule Metadata

To update version numbers and timestamps:

```bash
python scripts/refactor.py rule-management --version
```

### Handling AI Errors

When the AI makes mistakes, update the rules to prevent recurrence:

```bash
# Register an issue with a specific rule
python scripts/refactor.py rule-management --register-issue --rule 195 --description "Description" --example "Bad example"

# Update the rule with a new example or guidance
python scripts/refactor.py rule-management --update --rule 195 --section "Common Scenarios" --add-example "example"

# Verify the rule prevents the issue
python scripts/refactor.py rule-management --verify --rule 195 --test-case "test_case"
```

## Using Rules with Refactoring Tools

The PepperPy framework includes powerful refactoring tools that work alongside the rules system:

```bash
# Overview of all commands
python scripts/refactor.py --help

# Code analysis
python scripts/refactor.py detect-circular --directory pepperpy
python scripts/refactor.py find-unused --directory pepperpy

# Code consolidation
python scripts/refactor.py auto-consolidate --directory pepperpy --max-files 2

# Impact analysis
python scripts/refactor.py analyze-impact --operation files --mapping changes.json
```

Follow the guidelines in the code quality rules (180-205) when using these tools to ensure safe and effective refactoring.

## How Rules Are Used

When using Cursor AI with the PepperPy framework:

1. **Ask AI to consult relevant rules** before generating code
2. **Reference specific rule numbers** for guidance (e.g., "Please follow rule 180 for code duplication prevention")
3. **Verify AI-generated code** using the validation techniques in rule 195
4. **Update rules when AI makes mistakes** following the process in rule 205

The rules ensure that AI-generated code:
- Follows project architecture and standards
- Avoids duplication
- Maintains consistent structure
- Evolves APIs safely
- Integrates properly with the framework

## Continuous Integration

The rules system integrates with CI through GitHub Actions:

- Rules are validated on pull requests
- Auto-generated rules are updated regularly
- Code quality checks use the standards defined in the rules

## Further Information

For more information about the rules system:

- See the README in `.cursor/rules/README.md`
- Explore the refactoring tools with `python scripts/refactor.py --help`
- View the rule management guidelines in `.cursor/rules/205-rule-evolution.mdc` 