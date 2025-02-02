---
title: Manage Rules
description: Create, update, or validate cursor rules
version: 1.0
category: rules
tags: [rules, management, documentation]
---

# Context
This prompt helps manage .cursor/rules, which define implementation standards,
validation rules, and best practices for different components of the system.

# Input Format
```yaml
action: create|update|validate
rule:
  name: string  # Rule name (e.g., providers-rules)
  description: string  # Brief description
  scope: string  # Component/module scope
  globs: list[string]  # File patterns this rule applies to
```

# Output Format
```yaml
result:
  rule:
    path: string  # Path to the rule file
    content: string  # Rule content or changes
  validation:
    status: pass|fail
    issues: list[string]
  next_steps: list[string]
```

# Example Usage
```yaml
input:
  action: create
  rule:
    name: providers-rules
    description: Standards for provider implementations
    scope: pepperpy.providers
    globs: ["pepperpy/providers/**/*.py"]

output:
  result:
    rule:
      path: .cursor/rules/providers-rules.mdc
      content: |
        ---
        title: Provider Implementation Rules
        description: Standards for implementing providers
        version: 1.0
        scope: pepperpy.providers
        globs: ["pepperpy/providers/**/*.py"]
        ---
        
        # Provider Implementation
        
        ## Interface Requirements
        - All providers must implement BaseProvider
        - All methods must be async
        - Standard error handling required
        
        ## Configuration
        - Use environment variables for credentials
        - Support dynamic configuration
        - Validate all inputs
        
        ## Security
        - No hardcoded credentials
        - Implement rate limiting
        - Sanitize all inputs/outputs
        
        ## Testing
        - Provide mock implementations
        - Test all error scenarios
        - Validate configuration handling
    validation:
      status: pass
      issues: []
    next_steps:
      - "Update project_structure.yml"
      - "Create provider base interface"
      - "Add rule to documentation"
```

# Usage
1. Create new rules for components
2. Update existing rules
3. Validate rule compliance

# Common Rules
1. providers-rules: Provider implementation standards
2. agents-rules: Agent behavior and interaction
3. memory-rules: Memory management
4. security-rules: Security practices
5. testing-rules: Testing requirements 