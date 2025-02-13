---
title: Prompt Snippet Management
description: ALWAYS use when creating or managing prompt snippets to ensure consistency and effectiveness. This guide ensures prompt snippets are optimized for AI processing and user clarity.
version: 1.0
category: prompt-management
tags: [prompts, snippets, automation]
---

# Snippet Creation Context

## Pre-creation Analysis
```yaml
validate:
  existing_snippets:
    path: ".cursor/prompts/"
    check:
      - similar_prompts
      - overlapping_purposes
      - integration_points
  
  knowledge_base:
    query:
      - prompt_patterns
      - effective_formats
      - common_issues
```

# Snippet Structure

## 1. Required Header
```yaml
metadata:
  required:
    title:
      format: "Action-oriented title"
      example: "Plan Task"
    
    description:
      format: "Clear purpose and usage context"
      example: "Template for planning new tasks and analyzing requirements"
    
    version:
      format: "semantic"
      example: "1.0"
    
    category:
      values: [planning, execution, validation, maintenance]
```

## 2. Core Components
```yaml
structure:
  required:
    context:
      - clear_purpose
      - when_to_use
      - expected_outcomes
    
    validation:
      - pre_execution_checks
      - required_resources
      - integration_points
    
    process:
      - step_by_step_flow
      - decision_points
      - validation_steps
    
    examples:
      - practical_usage
      - expected_output
```

# Snippet Categories

## 1. Task Management
```yaml
task_snippets:
  types:
    - planning
    - execution
    - validation
    - continuation
  
  integration:
    - task_rules
    - knowledge_base
    - status_tracking
```

## 2. Code Management
```yaml
code_snippets:
  types:
    - implementation
    - testing
    - documentation
    - cleanup
  
  requirements:
    - follow_standards
    - maintain_quality
    - enable_automation
```

## 3. Process Management
```yaml
process_snippets:
  types:
    - workflow
    - validation
    - integration
    - maintenance
  
  focus:
    - clarity
    - automation
    - consistency
```

# Example Snippet Template
```yaml
---
title: "Action-Oriented Title"
description: |
  Clear description of purpose and when to use.
  Key points on:
  - Primary use case
  - When to apply
  - Expected outcomes
version: "1.0"
category: "snippet_category"
tags: [relevant, tags]
---

# Context
Detailed explanation of:
1. Primary purpose
2. When to use
3. Expected outcomes
4. Integration points

# Pre-execution Validation
```yaml
validate:
  requirements:
    - specific_check
    - required_resources
  
  integration:
    - reference_points
    - dependencies
```

# Process Flow
1. Clear step-by-step instructions
2. Decision points clearly marked
3. Validation checkpoints
4. Progress tracking

# Example Usage
```yaml
input:
  parameter: value
  context: details

output:
  result: expected_outcome
  next_steps: [
    "clear",
    "actionable",
    "steps"
  ]
```

# Guidelines
- Clear instructions
- Integration points
- Validation steps
- Error handling
```

# Development Guidelines

## 1. Clarity
```yaml
clarity_rules:
  content:
    - clear_purpose
    - specific_instructions
    - defined_outcomes
  
  structure:
    - logical_flow
    - clear_sections
    - consistent_format
```

## 2. AI Integration
```yaml
ai_optimization:
  requirements:
    - clear_patterns
    - structured_data
    - validation_points
    - error_handling
  
  processing:
    - context_awareness
    - decision_making
    - learning_capacity
```

## 3. User Experience
```yaml
ux_guidelines:
  focus:
    - easy_to_understand
    - practical_to_use
    - clear_outcomes
  
  format:
    - consistent_structure
    - clear_examples
    - actionable_steps
```

# Creation Process

## 1. Planning
```yaml
planning:
  steps:
    - identify_purpose
    - analyze_use_cases
    - define_structure
    - plan_integration
  
  considerations:
    - user_needs
    - ai_processing
    - automation_potential
```

## 2. Development
```yaml
development:
  steps:
    - create_structure
    - write_content
    - add_examples
    - test_effectiveness
  
  validation:
    - clarity_check
    - completeness_verify
    - integration_test
```

## 3. Testing
```yaml
testing:
  aspects:
    - practical_usage
    - ai_processing
    - integration
    - effectiveness
  
  verification:
    - expected_outcomes
    - error_handling
    - user_clarity
```

# Best Practices

## General Guidelines
- Focus on clarity and purpose
- Maintain consistent structure
- Ensure AI processability
- Include practical examples

## Integration Points
- Reference relevant rules
- Use knowledge base patterns
- Enable automation
- Support continuous improvement

## Quality Assurance
- Test thoroughly
- Validate outcomes
- Document clearly
- Update regularly

Remember: Snippets should be clear, practical, and optimize for both human understanding and AI processing.