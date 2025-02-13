---
title: Rule Management Guide
description: ALWAYS use this guide when creating or managing rules to ensure consistency, clarity, and effectiveness. This prompt details the creation, validation, and maintenance of Cursor rules.
version: 1.1
category: rules-management
tags: [rules, standards, automation]
yolo: true
---

# Rule Creation Context

This guide is intended for creating or improving .mdc rule files for the Cursor AI environment. It outlines the required structure and best practices to ensure your rule files are clear, unambiguous, and fully aligned with the system's requirements.

---

# Rule Structure

Each .mdc rule file consists of **two main sections**: a YAML frontmatter containing metadata and an XML section defining the rule logic. Both sections must be synchronized, especially for critical fields such as description and version.

## 1. YAML Frontmatter (Required)

**Purpose:**  
Provide essential metadata that describes the rule.

**Required Fields:**

- **`description`**  
  - **Format:** "ACTION_WORD when TRIGGER_SCENARIO to ensure OUTCOME. BRIEF_EXPLANATION."  
  - **Requirements:**  
    - Must start with ALWAYS, NEVER, or USE.
    - Clearly define the trigger conditions.
    - Specify the desired outcome.
    - Provide a concise explanation.
  - **Synchronization:** This description **must be identical** to the `<description>` element in the XML section.

- **`globs`**  
  - **Format:** File pattern(s) (e.g., `"**/*.{ts,tsx}"`).
  - **Purpose:** Define which files or folders the rule applies to.

- **`version`**  
  - **Format:** Semantic versioning (e.g., `"1.0"`).
  - **Synchronization:** Must match the `<version>` in the XML.

- **`priority`** (Optional but recommended)  
  - **Values:** `critical`, `high`, `medium`, `low`

**Example:**

```yaml
---
description: ALWAYS use kebab-case for file names for new modules to ensure consistency and readability. Filenames must follow the kebab-case format.
globs: "**/*.{ts,tsx}"
version: "1.0"
priority: high
---
```

---

## 2. XML Rule Definition

**Purpose:**  
Provide a detailed, structured definition of the rule that aligns with the YAML metadata.

**Required Structure:**

1. **XML Declaration:**  
   Start with the XML declaration:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   ```

2. **Root Element `<rule>`:**  
   Enclose all rule components within this element.

3. **Subelements:**

   - **`<metadata>`**  
     Must include:
     - `<name>`: Unique rule name in kebab-case (e.g., `kebab-case-filenames`).
     - `<description>`: **Identical** to the YAML `description`.
     - `<priority>`: The rule’s priority (e.g., `high`, `medium`, `low`).
     - `<version>`: Must match the YAML version.
     - `<tags>`: (Optional) Additional categorization tags.

   - **`<filters>`**  
     Specifies conditions for applying the rule:
     - Example: `<filter>` elements with `<type>`, `<pattern>`, and `<description>`.
     - **Example Field:** `<file_name>` with a regex pattern.

   - **`<actions>`**  
     Defines the actions to be executed when the rule is triggered:
     - Action types may include `<reject>`, `<suggest>`, or `<validate>`.
     - If multiple actions are provided, clearly specify the order and strategy for handling conflicts.

   - **`<examples>`**  
     Provides practical examples:
     - Each `<example>` must include an `<incorrect>` case and a `<correct>` case.
     - Each case should include a `<description>`, `<content>`, and, if applicable, an `<error>` explanation.

**Example:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rule>
  <metadata>
    <name>kebab-case-filenames</name>  <!-- Unique name in kebab-case -->
    <description>ALWAYS use kebab-case for file names for new modules to ensure consistency and readability. Filenames must follow the kebab-case format.</description>
    <priority>high</priority>
    <version>1.0</version>
    <tags>
      <tag>naming</tag>
      <tag>standards</tag>
    </tags>
  </metadata>
  <filters>
    <filter>
      <type>file_name</type>
      <pattern>.*</pattern>  <!-- Regex pattern matching all file names -->
      <description>Matches all file names for validation</description>
    </filter>
  </filters>
  <actions>
    <action>
      <type>reject</type>
      <conditions>
        <condition>
          <pattern>[A-Z]</pattern>
          <message>File names must be in kebab-case: no uppercase letters allowed.</message>
        </condition>
      </conditions>
    </action>
    <!-- Optional: Add a <suggest> action if necessary -->
  </actions>
  <examples>
    <example>
      <incorrect>
        <case type="naming-error">
          <description>Filename contains uppercase letters.</description>
          <content>IncorrectFileName.ts</content>
          <error>Filename should be in kebab-case.</error>
        </case>
      </incorrect>
      <correct>
        <case type="naming-correct">
          <description>Proper kebab-case filename.</description>
          <content>incorrect-file-name.ts</content>
        </case>
      </correct>
    </example>
  </examples>
</rule>
```

---

# Additional Guidelines and Best Practices

### Consistency & Synchronization

- **Data Matching:**  
  Ensure that the `description` and `version` in the YAML frontmatter exactly match those in the XML `<metadata>`.
- **Integrity Check:**  
  Verify that all mandatory fields are present and properly synchronized across both sections.

### Formatting & Syntax

- **YAML Delimiters:**  
  The YAML frontmatter must be enclosed between `---` markers with no extraneous text between it and the XML section.
- **Indentation:**  
  Maintain consistent indentation in both YAML and XML (e.g., 2 or 4 spaces) for improved readability.
- **Syntax Validation:**  
  Validate both YAML and XML to ensure they are free from syntax errors and can be parsed correctly.

### Special Character Handling

- **CDATA Usage:**  
  Use CDATA sections in XML when embedding content that includes special characters to avoid parsing issues.

### Modularity & Scalability

- **Complex Rules:**  
  For rules covering multiple scenarios or requiring complex logic, consider modularizing by splitting rules into separate files or clearly defined sections.
- **Documentation:**  
  Include inline comments within both the YAML and XML sections to explain the purpose and logic behind each field, aiding future maintenance and updates.

### Order and Priority of Actions

- **Execution Order:**  
  Clearly define the order in which actions should be processed if multiple actions are defined.
- **Conflict Resolution:**  
  Specify how to resolve conflicts between actions, whether through prioritization or manual review.

---

# Rule Creation Process

## 1. Initial Planning

Define the purpose, scope, and impact of the rule. Consider dependencies and the specific conditions the rule must enforce.

```yaml
planning:
  analyze:
    - purpose: "Define what the rule should enforce or prevent."
    - scope: "Identify the files or directories affected."
    - impact: "Evaluate potential impacts on existing code."
    - dependencies: "Identify any dependencies with other rules or systems."
  
  research:
    - best_practices: "Consult effective structures and common pitfalls."
```

## 2. Content Development

Develop the rule by creating both the YAML frontmatter and XML sections.

```yaml
development:
  structure:
    - frontmatter: "YAML metadata (description, globs, version, priority)"
    - metadata: "XML metadata (name, description, priority, version, tags)"
    - filters: "XML filters (type, pattern, description)"
    - actions: "XML actions (reject, suggest, validate)"
    - examples: "XML examples (incorrect and correct cases)"
  
  review:
    - clarity: "Ensure descriptions are unambiguous and complete."
    - completeness: "Check that all required fields are included."
    - effectiveness: "Confirm that examples clearly demonstrate intended behavior."
    - ai_processability: "Optimize structure for automated processing."
```

## 3. Validation

After development, validate the rule to ensure it meets all formatting and content requirements.

```yaml
validation:
  checks:
    - format_compliance: "Ensure YAML and XML syntax are valid."
    - content_completeness: "Verify all mandatory fields are present."
    - example_coverage: "Ensure examples illustrate both incorrect and correct usage."
    - integration_points: "Confirm the rule integrates seamlessly with the Cursor environment."
  
  testing:
    - rule_application: "Test the rule against sample inputs."
    - error_handling: "Ensure clear error messages are provided."
    - ai_processing: "Verify that AI systems can process the rule without issues."
```

---

# Rule Writing Guidelines

## 1. Clarity
- Use clear, unambiguous language.
- Begin descriptions with an action word (ALWAYS, NEVER, USE).
- Define precise trigger conditions and expected outcomes.
- Include practical examples that highlight both correct and incorrect usage.

## 2. AI Optimization
- Structure data using clear, consistent patterns.
- Define explicit validations and error recovery steps.
- Provide complete context to enable robust automated processing.

## 3. Knowledge Integration
- Reference other relevant rules when applicable.
- Incorporate best practices to maintain consistency across rule definitions.
- Ensure documentation is thorough to facilitate future updates.

## 4. Quality Assurance
- Validate the rule thoroughly using multiple examples.
- Test the rule in varied scenarios to ensure effectiveness.
- Document all decisions and update the rule regularly for continuous improvement.

---

# Final Example Rule Template

Below is a complete example that encapsulates all the guidelines:

**YAML Frontmatter:**

```yaml
---
description: ALWAYS use kebab-case for file names for new modules to ensure consistency and readability. Filenames must follow the kebab-case format.
globs: "**/*.{ts,tsx}"
version: "1.0"
priority: high
---
```

**XML Rule Definition:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rule>
  <metadata>
    <name>kebab-case-filenames</name>
    <description>ALWAYS use kebab-case for file names for new modules to ensure consistency and readability. Filenames must follow the kebab-case format.</description>
    <priority>high</priority>
    <version>1.0</version>
    <tags>
      <tag>naming</tag>
      <tag>standards</tag>
    </tags>
  </metadata>
  <filters>
    <filter>
      <type>file_name</type>
      <pattern>.*</pattern>
      <description>Matches all file names for validation</description>
    </filter>
  </filters>
  <actions>
    <action>
      <type>reject</type>
      <conditions>
        <condition>
          <pattern>[A-Z]</pattern>
          <message>File names must be in kebab-case: no uppercase letters allowed.</message>
        </condition>
      </conditions>
    </action>
  </actions>
  <examples>
    <example>
      <incorrect>
        <case type="naming-error">
          <description>Filename contains uppercase letters.</description>
          <content>IncorrectFileName.ts</content>
          <error>Filename should be in kebab-case.</error>
        </case>
      </incorrect>
      <correct>
        <case type="naming-correct">
          <description>Proper kebab-case filename.</description>
          <content>incorrect-file-name.ts</content>
        </case>
      </correct>
    </example>
  </examples>
</rule>
```