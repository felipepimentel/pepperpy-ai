# PepperPy Code Quality and Maintenance Rules

This directory contains new rules for the PepperPy framework focusing on code quality, maintenance, and AI-assisted development. These rules are designed to address common issues in AI-generated code, prevent duplication, maintain structural consistency, and ensure safe evolution of the codebase.

## Rules Overview

### 180-code-duplication-prevention.mdc

This rule provides strategies and tools to detect and prevent code duplication. It includes:
- Techniques for identifying duplicate code patterns
- Refactoring strategies to extract and consolidate duplicated code
- Workflows for safely refactoring duplicate code
- Design patterns to reduce duplication
- Implementation examples showing good and bad practices

### 185-file-organization.mdc

This rule defines standards for file organization and project structure consistency:
- Guidelines for proper file placement within the project structure
- Techniques to prevent file duplication
- Standard module structure patterns
- Naming conventions for files and directories
- Tools for validating and maintaining structure consistency

### 190-api-evolution.mdc

This rule focuses on safe API evolution with backward compatibility:
- Versioning strategy using Semantic Versioning
- Backward compatibility requirements
- Deprecation workflows
- Safe API evolution patterns
- Examples of breaking vs. backward-compatible changes
- Testing strategies for API compatibility

### 195-ai-response-validation.mdc

This rule addresses AI hallucinations and ensures accuracy in AI-generated code:
- Techniques for recognizing and preventing AI hallucinations
- Validation processes for AI-generated code
- Verification checklists for AI responses
- Progressive implementation approaches
- Guard rails for preventing framework inconsistencies
- Common hallucination scenarios and solutions

### 200-refactoring-validation.mdc

This rule provides guidance on using PepperPy refactoring tools effectively:
- Overview of refactoring tool capabilities
- Pre-refactoring analysis techniques
- Safe refactoring workflows for various scenarios
- Best practices for using refactoring tools
- Common pitfalls and their solutions
- Integration with development workflows

### 205-rule-evolution.mdc

This rule defines processes for continuous improvement of the rules system:
- Principles of unified tooling (single tool approach)
- Processes for capturing and analyzing AI failures
- Guidelines for rule updates and corrections
- Implementation of rule management in refactor.py
- Validation and verification of rule improvements
- Audit processes for measuring rule effectiveness

## Integration with Existing Rules

These new rules complement the existing core rules framework:

- **Core Framework Rules (000-099)**: Foundation rules that define the framework architecture and coding standards
- **Domain-Specific Rules (100-199)**: Rules for specific functional domains
- **Meta Rules (200-299)**: Rules about managing and updating rules

The new code quality rules (180-205) fill gaps in the existing rule set, providing concrete guidance on code maintenance, preventing common AI-generated code issues, and leveraging the refactoring tools.

## Single Tool Approach

Following PepperPy's principle of unified tooling, all rule management and code refactoring operations are performed through the **single `scripts/refactor.py` script**:

```bash
# Main refactoring operations
python scripts/refactor.py detect-smells --directory pepperpy
python scripts/refactor.py validate

# Rule management operations (new functionality)
python scripts/refactor.py rule-management --validate
python scripts/refactor.py rule-management --generate --name "New Rule" --category 210
```

This approach ensures consistency, eliminates tool fragmentation, and simplifies the developer experience.

## Using These Rules

1. Initialize the rules system:
   ```bash
   ./scripts/initialize-rules.sh
   ```

2. Reference specific rules when performing code maintenance:
   ```bash
   # For example, when refactoring duplicate code
   python scripts/refactor.py detect-smells --directory pepperpy
   # Then follow the guidelines in 180-code-duplication-prevention.mdc
   ```

3. Validate your changes:
   ```bash
   python scripts/refactor.py validate
   ```

4. When AI tools make mistakes, update rules to prevent recurrence:
   ```bash
   python scripts/refactor.py rule-management --register-issue --rule 195 --description "Issue description"
   python scripts/refactor.py rule-management --update --rule 195 --section "Common Scenarios" --add-example "example"
   ```

## Maintenance

Keep these rules updated as the codebase evolves:

```bash
python scripts/refactor.py rule-management --version
```

Run periodic audits to measure rule effectiveness:

```bash
python scripts/refactor.py rule-management --audit --period "last-3-months"
``` 