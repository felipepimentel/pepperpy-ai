# Briefing Document: Cursor AI and Python Code Style Guide

This document provides a detailed summary of key themes, important ideas, and relevant facts extracted from the provided documentation on Cursor, an AI-powered code editor. The focus is on its configuration rules (Cursor Rules) and Python code style guidelines, offering a concise overview to assist in understanding and effectively utilizing Cursor’s rule system while ensuring high-quality Python code.

## Key Themes

### Transition from .cursorrules to .cursor/rules/*.mdc
The original system, based on a single `.cursorrules` file, is being phased out in favor of a more flexible approach using a `.cursor/rules` directory containing multiple `.mdc` files. This change aims to provide greater granularity and control over AI behavior across different parts of a project.

> "It is now .cursor/rules/*.mdc (.cursorrules still works but will be removed)."
>
> "We will eventually remove .cursorrules in the future, so we recommend migrating to the new Project Rules system for better flexibility and control."

### Structure and Format of .mdc Files
`.mdc` (Markdown Cursor) files are the new standard for defining project-specific rules. They combine a frontmatter section (typically in YAML) for metadata with the rule definition itself, which can be written in XML, Markdown, or plain text. 

> "Each rule is defined in a .mdc file format that combines frontmatter configuration with XML-based rule definitions."

### Python Code Style Guide
To ensure readability, maintainability, and code quality, follow these Python coding standards in the **Pepperpy** project:

#### Pythonic Philosophy
- **Readability First:** Prefer clear, concise solutions over excessive complexity.
- **Consistent Naming:** Use `snake_case` for functions and variables, `CamelCase` for classes, and uppercase letters for constants.
- **Docstrings & Type Hints:** Provide clear docstrings using Google or reStructuredText style, along with type hints.
- **Single Responsibility:** Functions and classes should have a clear, focused purpose.
- **EAFP (Easier to Ask for Forgiveness than Permission):** Use Pythonic error handling idioms.

### File Naming and Organization
- Store `.mdc` rule files in the `.cursor/rules/` directory.
- Use **kebab-case** for filenames with descriptive keywords (e.g., `001-core-security.mdc`).
- Number rules logically to improve maintainability (e.g., `100-api-integration.mdc`).

### Python Project Configuration (pyproject.toml)
All tool configurations should be centralized in `pyproject.toml`:

#### Linting with Ruff
- Enforce **PEP 8**, `pycodestyle`, `pyflakes`, and `isort`.
- Detect unused variables, imports, and syntax errors.

#### Formatting with Black
- Enforce consistent formatting.
- Set a **max line length** (e.g., **120 characters**) for better readability.

#### Import Sorting with isort
- Organize imports alphabetically and by category (standard library, third-party, local).

#### Type Checking with MyPy
- Enable strict type checking for improved code reliability.

### Best Coding Practices

#### Naming Conventions
- **Variables:** `snake_case` (e.g., `user_name`).
- **Functions:** `snake_case` (e.g., `calculate_total()`).
- **Classes:** `CamelCase` (e.g., `UserClass`).
- **Constants:** `UPPER_CASE` (e.g., `MAX_USERS`).

#### Writing Effective Docstrings
- Follow Google or reStructuredText style.
- Clearly describe function purpose, arguments, and return values.

#### Exception Handling
- Use `try...except` to gracefully handle errors.
- Catch specific exceptions instead of using `except Exception`.

#### Meaningful Comments
- Keep comments concise and relevant.
- Avoid redundant comments that merely repeat code logic.

#### Code Formatting
- **Indentation:** Use 4 spaces per indentation level.
- **Max Line Length:** 120 characters.
- **Blank Lines:** Use them to separate logical sections of code.

### Key Software Design Principles
- **SOLID Principles:** Write modular, maintainable code.
- **DRY (Don't Repeat Yourself):** Extract reusable logic into functions.
- **YAGNI (You Ain’t Gonna Need It):** Avoid premature optimizations or unnecessary features.

### Automating Code Quality
- Configure **CI/CD pipelines** (e.g., GitHub Actions) to run **Ruff, Black, and MyPy** automatically.
- Automate commits using **conventional commit** messages.

### Workflow for Creating New Rules
1. **Create a new `.mdc` file** in `.cursor/rules/`.
2. **Define a clear description** and apply glob patterns.
3. **Include examples** of correct and incorrect code.
4. **Validate the rule** before deployment.
5. **Automate rule enforcement**, such as auto-formatting with Black.

### Example of a `.mdc` Rule File
```yaml
---
description: "ALWAYS use 'snake_case' for variable names in Python."
globs: "**/*.py"
---
```

### Example XML Rule
```xml
<rule>
    <metadata>
        <description>ALWAYS use 'snake_case' for variable names in Python.</description>
        <priority>high</priority>
        <version>1.0</version>
    </metadata>
    <filters>
        <content type="regex">
            ^(?!(.*def|.*class)\s+\w+\s*\(.*\):\s*$)(?!\s*$).*[^_\W]([a-z][a-z0-9_]*)[^_\W].*$
        </content>
    </filters>
    <actions>
        <type>suggest</type>
        <message>Use 'snake_case' for variable names in Python. Example: `my_variable`.</message>
    </actions>
    <examples>
        <correct>
            my_variable = 10
        </correct>
        <incorrect>
            myVariable = 10
        </incorrect>
    </examples>
</rule>
```

### Final Considerations
By following this guide, your team will maintain a **consistent, readable, and high-quality Python codebase**. Leveraging AI for rule creation ensures an evolving, adaptable coding standard that aligns with project needs. 

Following these detailed guidelines will equip your team to produce Python code that is easy to read, maintain, and collaborate on.