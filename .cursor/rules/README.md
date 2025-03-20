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
├── 200-rules-management.mdc          # Meta: Rules management
├── 201-self-update-system.mdc        # Meta: Self-updating mechanisms
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

3. **200-299**: Meta rules
   - Rules about rules
   - Self-management and update mechanisms

4. **300-399**: Documentation rules
   - Standards for documentation
   - API documentation patterns

5. **400-499**: Tooling rules
   - CI/CD pipelines
   - Development tools integration

6. **500-599**: Extension rules
   - Plugin development
   - Extension patterns

7. **auto-generated/**: Auto-generated rules
   - Rules created by automated processes
   - Updated when the codebase changes

## Rule Structure

Each rule file follows this structure:

```markdown
<!--
@title: Rule Title
@description: Brief description of the rule
@glob: Pattern matching files this rule applies to
@priority: Numeric priority (higher values = higher priority)
-->

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

The PepperPy framework includes tools to manage rules:

### Rules Updater Script

The `scripts/rules-updater.py` script provides functionality for:

- Scanning the codebase and updating module maps
- Validating rules for syntax and completeness
- Generating new rules from templates
- Updating rule metadata (versions and timestamps)
- Analyzing APIs and generating documentation

Usage:
```bash
python scripts/rules-updater.py [command]
```

Commands:
- `scan`: Scan codebase and update module maps
- `validate`: Validate all rules for syntax and completeness
- `generate`: Generate new rules from templates
- `version`: Update version numbers and timestamps
- `analyze-api`: Analyze APIs and update documentation
- `help`: Show help information

### Rules Initialization Script

The `scripts/initialize-rules.sh` script initializes the rules system by:

1. Backing up existing rules
2. Moving new rules into place
3. Setting up the auto-generated directory
4. Running the initial rule scan

Usage:
```bash
./scripts/initialize-rules.sh
```

## Self-Updating Mechanism

The rules system includes self-updating capabilities:

1. **Module Scanner**: Updates module structure information
   - Auto-generates module maps based on the current codebase

2. **API Analyzer**: Updates interface documentation
   - Generates API docs from module exports

3. **Rule Validator**: Ensures rules are properly formatted
   - Validates rule structure and required sections

## Creating New Rules

To create a new rule:

1. Identify the appropriate category
2. Use the generator:
   ```bash
   python scripts/rules-updater.py generate --name "My Rule Name" --category 100
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

To update all rule metadata (versions and timestamps):
```bash
python scripts/rules-updater.py version
```

## Contributing

When contributing to the rules system:

1. Follow the established rule structure
2. Validate your rules before committing:
   ```bash
   python scripts/rules-updater.py validate
   ```
3. Update auto-generated content:
   ```bash
   python scripts/rules-updater.py scan
   ```
4. Document your changes in the rule's metadata 