# PepperPy Cursor Rules

This directory contains the Cursor rules for the PepperPy framework. These rules provide guidance to AI tools, ensuring consistent code generation, architectural adherence, and best practices.

## Rules System Architecture

The rules are organized into a hierarchical numbering system:

```
.cursor/rules/
├── 000-framework-architecture.mdc    # Core framework architecture (highest priority)
├── 001-coding-standards.mdc          # General coding standards 
├── 002-file-management.mdc           # File organization and structure
├── ...
├── 100-rag-system.mdc                # Domain-specific: RAG
├── 101-workflow-system.mdc           # Domain-specific: Workflows
├── ...
├── 180-code-duplication-prevention.mdc # Code quality: Duplication prevention
├── 185-file-organization.mdc         # Code quality: File organization
├── 190-api-evolution.mdc             # Code quality: API evolution
├── 195-ai-response-validation.mdc    # Code quality: AI response validation
├── 200-refactoring-validation.mdc    # Code quality: Refactoring tools usage
├── 200-rules-management.mdc          # Meta: Rules management
├── 205-rule-evolution.mdc            # Meta: Rules evolution and self-correction
├── ...
├── auto-generated/                   # Auto-generated rules
│   ├── module-map.mdc                # Generated module map
│   ├── class-hierarchy.mdc           # Generated class hierarchy
│   └── ...
```

### Rule Categories

1. **000-099**: Core framework rules
   - Architecture, standards, and general principles
   - Highest priority and broadest application

2. **100-199**: Domain-specific rules
   - Rules for specific domains (RAG, workflows, etc.)
   - Applied to specific subsets of the codebase

3. **180-205**: Code quality and maintenance rules
   - Rules for preventing duplication, maintaining structure
   - Validation of AI-generated code
   - API evolution and backward compatibility
   - Self-correction of rules

4. **200-299**: Meta rules
   - Rules about rules
   - Self-management and update mechanisms

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

## Rule Structure

Each rule file follows this structure:

```markdown
---
description: Brief description of the rule
globs:
  - "**/*.py"  # Pattern matching files this rule applies to
alwaysApply: true
---

# Rule Title

## Overview

Brief description of the rule's purpose and scope.

## Section 1

Content for section 1...

## Section 2

Content for section 2...

...

## Conclusion

Summary of the rule.
```

## Rule Management Tools

The PepperPy framework includes tools to manage rules using the single unified `refactor.py` script:

### Rule Management Commands

The `scripts/refactor.py rule-management` command provides functionality for:

- Scanning the codebase and updating module maps
- Validating rules for syntax and completeness
- Generating new rules from templates
- Updating rule metadata (versions and timestamps)
- Analyzing APIs and generating documentation
- Registering and fixing AI hallucinations and errors

Usage:
```bash
python scripts/refactor.py rule-management [command]
```

Commands:
- `--scan`: Scan codebase and update module maps
- `--validate`: Validate all rules for syntax and completeness
- `--validate-frontmatter`: Verify YAML frontmatter format
- `--generate`: Generate new rules from templates
- `--update`: Update existing rules with new examples
- `--version`: Update version numbers and timestamps
- `--register-issue`: Register issues with AI-generated code
- `--verify`: Test if rules prevent known issues
- `--audit`: Audit rule effectiveness

## Self-Updating Mechanism

The rules system includes self-updating capabilities:

1. **Module Scanner**: Updates module structure information
   - Auto-generates module maps based on the current codebase

2. **API Analyzer**: Updates interface documentation
   - Generates API docs from module exports

3. **Rule Validator**: Ensures rules are properly formatted
   - Validates rule structure and required sections

4. **Rule Evolution**: Updates rules based on AI errors
   - Captures and analyzes AI hallucinations
   - Updates rules to prevent recurrence

## Creating New Rules

To create a new rule:

1. Identify the appropriate category
2. Use the generator:
   ```bash
   python scripts/refactor.py rule-management --generate --name "My Rule Name" --category 100
   ```
3. Edit the generated file with domain-specific content
4. Test the rule for compatibility

## Maintaining Rules

Rules should be updated when:

1. Framework architecture changes
2. New modules or domains are added
3. Coding standards evolve
4. Implementation patterns change
5. Dependencies are updated
6. Significant bugs are fixed
7. AI makes errors or hallucinations

To update all rule metadata (versions and timestamps):
```bash
python scripts/refactor.py rule-management --version
```

## Contributing

When contributing to the rules system:

1. Follow the established rule structure
2. Use proper YAML frontmatter format
3. Validate your rules before committing:
   ```bash
   python scripts/refactor.py rule-management --validate
   ```
4. Update auto-generated content:
   ```bash
   python scripts/refactor.py rule-management --scan
   ```
5. Document your changes in the rule's metadata 