---
title: Rule Management Guide
description: ALWAYS use when creating or managing rules to ensure consistency and effectiveness. This prompt guides the creation and maintenance of cursor rules.
version: 1.1
category: rules-management
tags: [rules, standards, automation]
---

# Rule Creation Context

## Pre-creation Analysis
```yaml
validate:
  existing_rules:
    path: ".cursor/rules/"
    check:
      - similar_rules
      - overlapping_scopes
      - dependencies
  
  knowledge_base:
    query:
      - rule_patterns
      - effective_structures
      - common_pitfalls
```

# Rule Structure

## 1. Frontmatter (Required)
```yaml
frontmatter:
  required:
    description:
      format: "ACTION_WORD when TRIGGER_SCENARIO to ensure OUTCOME. BRIEF_EXPLANATION."
      requirements:
        - Start with ALWAYS/NEVER/USE
        - Clear trigger conditions
        - Specific outcome
        - Concise explanation
    
    globs:
      format: "file pattern(s)"
      example: "**/*.{ts,tsx}"
    
    version:
      format: "semantic"
      example: "1.0"
    
    priority:
      values: [critical, high, medium, low]
```

## 2. XML Structure
```yaml
xml:
  required_sections:
    metadata:
      - name
      - description
      - priority
      - version
      - tags
    
    filters:
      - type
      - pattern
      - description
    
    actions:
      - type
      - conditions
      - guidelines
    
    examples:
      - incorrect
      - correct
```

# Rule Types

## 1. Validation Rules
```yaml
validation_rule:
  purpose: "Ensure code/structure compliance"
  sections:
    - file_patterns
    - validation_criteria
    - error_messages
    - recovery_actions
```

## 2. Implementation Rules
```yaml
implementation_rule:
  purpose: "Define coding standards"
  sections:
    - patterns
    - requirements
    - best_practices
    - examples
```

## 3. Process Rules
```yaml
process_rule:
  purpose: "Define workflows"
  sections:
    - steps
    - validations
    - integrations
    - documentation
```

# Rule Writing Guidelines

## 1. Clarity
```yaml
clarity:
  requirements:
    - Unambiguous descriptions
    - Clear trigger conditions
    - Specific outcomes
    - Practical examples
  
  format:
    - Use consistent terminology
    - Structure content logically
    - Provide complete context
```

## 2. AI Processing
```yaml
ai_optimization:
  elements:
    - Clear patterns
    - Structured data
    - Explicit validations
    - Error recovery
  
  context:
    - Provide complete information
    - Define clear boundaries
    - Specify validation criteria
```

## 3. Knowledge Integration
```yaml
knowledge_base:
  integration:
    - Pattern recognition
    - Learning capabilities
    - Error handling
    - Continuous improvement
```

# Example Rule Template
```yaml
---
description: ALWAYS use when [SCENARIO] to ensure [OUTCOME]. [EXPLANATION]
globs: "pattern/**/*.ext"
version: "1.0"
priority: high
---
<?xml version="1.0" encoding="UTF-8"?>
<rule>
  <metadata>
    <name>rule_name</name>
    <description>Same as frontmatter description</description>
    <priority>high</priority>
    <version>1.0</version>
    <tags>
      <tag>category</tag>
    </tags>
  </metadata>

  <filters>
    <filter>
      <type>file_path|content|event</type>
      <pattern>regex_pattern</pattern>
      <description>What this matches</description>
    </filter>
  </filters>

  <actions>
    <action>
      <type>validate|reject|suggest</type>
      <conditions>
        <condition>
          <pattern>condition_pattern</pattern>
          <message>Clear error message</message>
        </condition>
      </conditions>
    </action>
  </actions>

  <examples>
    <example>
      <incorrect>
        <case type="error_type">
          <description>What's wrong</description>
          <content>Wrong example</content>
          <error>Error explanation</error>
        </case>
      </incorrect>
      <correct>
        <case type="correct_type">
          <description>What's right</description>
          <content>Correct example</content>
        </case>
      </correct>
    </example>
  </examples>
</rule>
```

# Rule Creation Process

## 1. Initial Planning
```yaml
planning:
  analyze:
    - purpose
    - scope
    - impact
    - dependencies
  
  research:
    - existing_rules
    - similar_patterns
    - best_practices
```

## 2. Content Development
```yaml
development:
  structure:
    - frontmatter
    - metadata
    - filters
    - actions
    - examples
  
  review:
    - clarity
    - completeness
    - effectiveness
    - ai_processability
```

## 3. Validation
```yaml
validation:
  checks:
    - format_compliance
    - content_completeness
    - example_coverage
    - integration_points
  
  testing:
    - rule_application
    - error_handling
    - ai_processing
```

# Guidelines

## Rule Writing
- Be explicit and clear
- Include complete context
- Provide practical examples
- Define clear validations

## AI Optimization
- Use consistent patterns
- Structure data clearly
- Define explicit validations
- Include error recovery

## Integration
- Reference other rules
- Use knowledge base
- Maintain consistency
- Enable automation

## Quality Assurance
- Validate thoroughly
- Test with examples
- Document clearly
- Update regularly

Remember: Rules are the foundation of automated processing and should be clear, unambiguous, and complete.