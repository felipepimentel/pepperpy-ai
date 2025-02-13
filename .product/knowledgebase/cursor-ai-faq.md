# Briefing Document: Cursor AI, Configuration Rules, and Python Code Style Guide

This document provides a detailed summary of key themes, important ideas, and relevant facts extracted from the provided documentation on Cursor, an AI-powered code editor. The focus is on its configuration rules (Cursor Rules), Python code style guidelines, and best practices for effectively leveraging Cursor AI.

## Key Themes

### What Are "Cursor Rules" and Why Are They Necessary?
Cursor Rules are a set of customized instructions that guide the AI’s behavior in the Cursor code editor. They function as a "manual" for the AI, helping it understand coding conventions, project architecture, and best practices specific to each project. These rules ensure consistency in generated code, prevent common errors, and optimize the workflow with AI assistance. Without clear instructions, AI-generated code can become inconsistent or fail to adhere to project standards.

### Transition from .cursorrules to .cursor/rules/*.mdc
The `.cursorrules` file is a legacy system for defining global project rules. It is being deprecated, and users are encouraged to migrate to the `.cursor/rules/` directory, which supports multiple `.mdc` rule files. This approach offers:
- Greater flexibility and control over AI behavior in different parts of the project.
- The ability to apply specific rules per file type or directory.
- More efficient use of AI context memory.

> "It is now .cursor/rules/*.mdc (.cursorrules still works but will be removed)."
>
> "We will eventually remove .cursorrules in the future, so we recommend migrating to the new Project Rules system for better flexibility and control."

### Organizing and Naming Rule Files in .cursor/rules/
- All rule files must have the `.mdc` extension.
- Use a numbering system to categorize rules:
  - **001-099:** Core rules (e.g., security, logging)
  - **100-199:** Integration rules (e.g., API, CLI)
  - **200-299:** Pattern and function rules (e.g., data validation, naming conventions)
- Use **kebab-case** for file names (e.g., `001-core-security.mdc`).

### Recommended Format for .mdc Rule Files
Cursor supports multiple formats (`YAML`, `XML`, `JSON`, `Markdown`), but `YAML` and `XML` are preferred:
- **YAML:** Offers readability, supports comments, and allows for structured rule definitions.
- **XML:** Ensures a strict schema structure and integrates well with Cursor’s JSX-like rule parsing.

A `.mdc` rule file consists of:
1. **Frontmatter (YAML)**: Contains metadata (e.g., `description`, `globs`).
2. **Rule Definition (XML)**: Defines the actual rule structure.

### How to Reference Rule Files in Cursor
Cursor allows referencing rule files directly within prompts using the `@` symbol, such as `@instructions` or `@specific_file`. This ensures AI adherence to predefined rules without needing to repeat them in prompts.

### Best Practices for Writing Effective Cursor Rules
- **Clear, Actionable Descriptions:** Start with verbs like `ALWAYS`, `NEVER`, or `USE`.
- **Specific Scopes (`globs`)**: Define precise file patterns (e.g., `*.ts`, `src/**/*.py`).
- **Examples:** Provide correct and incorrect usage examples.
- **Prioritization:** Define priority levels to resolve conflicts.
- **Modular Approach:** Keep rules separate for clarity and maintainability.

### Handling .mdc File Save Issues
A known issue may cause `.mdc` file changes to disappear. A workaround is to close Cursor, select **"Override"** in the "Unsaved Changes" prompt, and reopen the editor.

## Python Code Style Guide
To ensure readability, maintainability, and code quality, follow these Python coding standards in the **Pepperpy** project:

### Pythonic Philosophy
- **Readability First:** Prefer clear, concise solutions over excessive complexity.
- **Consistent Naming:** Use `snake_case` for functions and variables, `CamelCase` for classes, and uppercase letters for constants.
- **Docstrings & Type Hints:** Provide clear docstrings using Google or reStructuredText style, along with type hints.
- **Single Responsibility:** Functions and classes should have a clear, focused purpose.
- **EAFP (Easier to Ask for Forgiveness than Permission):** Use Pythonic error handling idioms.

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

### Automating Code Quality
- Configure **CI/CD pipelines** (e.g., GitHub Actions) to run **Ruff, Black, and MyPy** automatically.
- Automate commits using **conventional commit** messages.

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

Furthermore, **optimizing Cursor AI usage** involves:
- **Building a library of reusable rules** (`stdlib`).
- **Automating tasks** like code formatting, commits, and deployment.
- **Using AI to generate and refine rules** based on project requirements.
- **Implementing self-learning mechanisms** for AI-driven rule optimization.
- **Enhancing security** by enforcing OWASP Top 10 mitigations and strict validation protocols.

Following these detailed guidelines will equip your team to produce Python code that is easy to read, maintain, and collaborate on.