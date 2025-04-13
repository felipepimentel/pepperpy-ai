# PepperPy Cursor Rules

This directory contains rules that define architecture, coding standards, and best practices for the PepperPy project. 

## Available Rules

| Rule Name | Description | When to Use |
|-----------|-------------|-------------|
| 000-architecture-principles | Core design principles and architectural vision | When designing or implementing any component |
| 001-coding-standards | Mandatory style, patterns and type hints | When writing any Python code |
| 002-core-architecture | Core framework component design | When modifying core framework components or creating new modules |
| 003-plugin-architecture | Plugin system structure and patterns | When working with plugins |
| 004-web-ui-architecture | Web UI patterns and best practices | When working with web UI components |
| 005-api-architecture | API server patterns and implementation | When working with API server components |
| 006-workflow-plugin-system | Workflow plugin requirements | When implementing workflow plugins |
| 999-mdc-format | MDC file format guide | When creating or updating *.mdc files |

## How to Apply Rules

Rules are automatically applied based on the following:

1. **File matching** - When working with files that match the glob patterns specified in a rule
2. **Explicit references** - When you explicitly refer to a rule in a prompt
3. **Always apply** - Some rules may be flagged to always apply to all conversations

## Rule Structure

Each rule contains:

- **Frontmatter** - Metadata including description and file patterns (globs)
- **Content** - Detailed guidance written in Markdown, including:
  - Overview of the concept
  - Code examples and patterns
  - Anti-patterns to avoid
  - Best practices

## Requesting Rule Updates

If you need to update or add rules, specify the rule name and the changes needed. Rule changes should be considered carefully as they affect the entire codebase. 