# Briefing Document: Cursor AI and Configuration Rules (.cursorrules, .cursor/rules/*.mdc)

This document provides a detailed summary of key themes, important ideas, and relevant facts extracted from the provided documentation on Cursor, an AI-powered code editor. The focus is on its configuration rules (Cursor Rules), offering a concise overview to assist in understanding and effectively utilizing Cursor's rule system.

## Key Themes

### Transition from .cursorrules to .cursor/rules/*.mdc
The original system, based on a single `.cursorrules` file, is being phased out in favor of a more flexible approach using a `.cursor/rules` directory containing multiple `.mdc` files. This change aims to provide greater granularity and control over AI behavior across different parts of a project.

> "It is now .cursor/rules/*.mdc (.cursorrules still works but will be removed)."
>
> "We will eventually remove .cursorrules in the future, so we recommend migrating to the new Project Rules system for better flexibility and control."

### Structure and Format of .mdc Files
`.mdc` (Markdown Cursor) files are the new standard for defining project-specific rules. They combine a frontmatter section (typically in YAML) for metadata with the rule definition itself, which can be written in XML, Markdown, or plain text. There is ongoing discussion about the most suitable format for rule definitions.

> "The Rules files in Cursor are special files in Cursor with the .mdc extension. Basically, it's markdown."
>
> "Each rule is defined in a .mdc file format that combines frontmatter configuration with XML-based rule definitions."

### Granularity and Context
The new system allows for more specific and contextual rules, tailored to different file types, directories, or situations. This improves the accuracy and relevance of AI suggestions and actions.

> "Project rules offer a powerful and flexible system with path-specific configurations."
>
> "Users can write several repository-level rules to disk in the .cursor/rules directory. The Agent will automatically choose which rule to follow."

### Organization and Naming of Files
Organizing `.mdc` files within the `.cursor/rules` directory is crucial for clarity and maintainability. A numbering scheme and descriptive kebab-case naming conventions are recommended.

> "I use a three-digit format and group rules like this: Core Rules: 001-099, Integration Rules: 100-199, Pattern/Role Rules: 200-299."

### Creating and Managing Rules
#### Choosing the Appropriate File Format
- **YAML:** Recommended for its clean syntax and readability, making complex rules easier to organize. It also supports comments for in-file documentation.
- **XML:** Provides strict schema validation, ensuring a consistent structure and rich metadata support.
- **Markdown or Plain Text:** Suitable for simpler rules where structure and validation are less critical.
- **.mdc Format:** Essential for files to be recognized as rules by Cursor.

#### Directory Structure
- Since version 0.45, Cursor uses the `.cursor/rules` directory to store project-specific rules.
- Within this directory, create separate `.mdc` files for different rule types (e.g., `.ts`, `.js`, `.md`, or entire subfolders).

#### Naming Conventions
- Use **kebab-case** for filenames with relevant keywords to clarify the rule's purpose.
- Implement a numbering system to categorize rules (e.g., `001-core-security.mdc`, `100-api-integration.mdc`).

#### Defining Rules
- **Clear Description:** Use concise action-oriented phrasing like "ALWAYS," "NEVER," or "USE" to clarify application contexts.
- **Glob Patterns:** Define specific file and folder targets for rule application.
- **Examples:** Provide correct and incorrect usage scenarios to help the AI understand application scope.

#### Modular and Specific Rules
- Avoid overly broad rules, as they may overload the AI context and be ignored.
- Keep rules separate and tailored to specific spaces or contexts.
- Define rules for distinct file types or subfolders.

#### Using File References (@)
- Use `@` symbols to reference files and include their content dynamically when applying rules.
- Chain multiple rules together for better reuse and maintainability.

### Automating Rule Creation and Maintenance
- Utilize AI to generate and update rules based on evolving project needs.
- Leverage tools like `airul`, a CLI tool that generates `.cursorrules` files from multiple documents.

### Testing and Validating Rules
- Continuously test rules to ensure correct application and avoid unintended side effects.
- Use chat mode for rule review and refinement by instructing AI to analyze and describe rule files.

### Managing Rule Changes
- Implement version control to track modifications and allow rollbacks if necessary.
- Be aware of a known issue where `.mdc` file changes may disappear. To mitigate, close Cursor completely and select **"Override"** in the "Unsaved Changes" prompt when reopening.

### Optimizing Rules for AI
- Use **clear and actionable** descriptions.
- Include relevant **trigger keywords**.
- Specify **precise file patterns** in glob expressions.

### Common Mistakes to Avoid
- **Incorrect directory placement:** Ensure rules reside inside `.cursor/rules/`.
- **Mismatched descriptions:** Ensure consistency between frontmatter and metadata.
- **Vague descriptions:** Avoid unclear rule definitions.
- **Incomplete XML structure:** If using XML, include all required sections.
- **Lack of examples:** Provide clear correct/incorrect usage samples.

### Exploring Structured Formats (XML)
For strict validation and organization, consider using XML. The `cursor-xml-rules-trial` GitHub repository provides a structured system for managing Cursor AI rules using XML, emphasizing schema validation, clear hierarchy, and metadata support.

By following these steps, you can optimize rule creation, ensuring effectiveness, maintainability, and a consistent development environment.

