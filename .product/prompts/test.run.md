---
title: Continuous Test Resolution
description: ALWAYS use when resolving test issues to ensure systematic and continuous problem solving. This prompt guides continuous test execution and issue resolution.
version: 1.2
category: testing
tags: [testing, quality, continuous, automation]
yolo: true
---

# Context
Guides the continuous process of testing, issue resolution, and quality improvement while maintaining project standards and learning patterns.

# Continuous Execution Loop

## 1. Initial Validation
```yaml
setup:
  environment:
    validate:
      - python_version
      - dependencies
      - virtual_env
  
  knowledge_base:
    query:
      - common_patterns
      - recent_solutions
      - known_issues
```

## 2. Test Execution
```yaml
execute:
  primary:
    command: "python ./scripts/check.py"
    flags: ["--verbose"]
  
  secondary:
    command: ".venv/bin/pytest"
    options:
      - "-v"
      - "--cov=pepperpy"
      - "--cov-report=term-missing"

  monitoring:
    capture:
      - stdout
      - stderr
      - exit_code
```

## 3. Issue Analysis
```yaml
analyze:
  output:
    parse:
      - test_failures
      - warnings
      - coverage
      - linting
    
    classify:
      priority:
        critical:
          - test_failures
          - import_errors
        high:
          - type_errors
          - attribute_errors
        medium:
          - warnings
          - coverage
        low:
          - linting
          - style
```

## 4. Resolution Pipeline
```yaml
resolution:
  strategy:
    quick_wins:
      - linting_fixes: "--fix"
      - import_corrections
      - format_fixes
    
    systematic:
      - test_failures:
          analyze: "stack_trace"
          patterns: "known_issues"
          fix: "targeted_solution"
      
      - type_errors:
          analyze: "signature"
          check: "type_hints"
          fix: "type_correction"
      
      - coverage:
          analyze: "missing_paths"
          generate: "test_cases"
          verify: "coverage_increase"
```

## 5. Verification
```yaml
verify:
  changes:
    run: "test_suite"
    expect:
      - tests: "passing"
      - warnings: "none"
      - coverage: ">=80%"
      - linting: "clean"
  
  improvement:
    check:
      - progress_made: true
      - no_regressions: true
```

## 6. Learning Integration
```yaml
learn:
  patterns:
    success:
      record:
        - issue_type
        - solution
        - verification
    
    failure:
      analyze:
        - attempted_fixes
        - roadblocks
        - user_guidance
```

# Common Patterns Library

## 1. Quick Fixes
```yaml
fixes:
  imports:
    - verify_path
    - check_installation
    - fix_circular
  
  types:
    - add_hints
    - fix_signatures
    - update_protocols
  
  async:
    - add_awaits
    - fix_event_loop
    - handle_timeouts
```

## 2. Test Improvements
```yaml
patterns:
  coverage:
    - edge_cases
    - error_paths
    - async_flows
  
  assertions:
    - type_checks
    - value_validation
    - exception_handling
  
  mocking:
    - external_services
    - time_sensitive
    - file_operations
```

# Continuous Loop

## Process Flow
```yaml
continuous_execution:
  while: not all_checks_passing
    steps:
      - run_validation
      - analyze_issues
      - apply_fixes
      - verify_changes
      - learn_patterns
    
    monitoring:
      - track_progress
      - detect_loops
      - identify_blockers
    
    exit_conditions:
      - all_tests_pass
      - coverage_met
      - no_warnings
      - clean_lint
```

# Communication Protocol

## Progress Updates
```yaml
updates:
  frequency: after_each_iteration
  include:
    - current_status
    - fixed_issues
    - remaining_issues
    - success_rate
  
  blocking:
    when:
      - no_progress_made
      - unknown_issue
      - needs_guidance
    action:
      - document_attempts
      - request_help
      - suggest_solutions
```

# Guidelines

## Execution Strategy
- Execute tests continuously
- Prioritize critical issues
- Group similar problems
- Track progress constantly

## Resolution Approach
- Start with quick wins
- Apply systematic fixes
- Verify each change
- Learn from patterns

## Quality Standards
- Maintain test integrity
- Follow project structure
- Update documentation
- Keep code clean

## Knowledge Management
- Document new patterns
- Share successful fixes
- Learn from failures
- Update strategies

Remember: Reference testing_standards rule for guidelines and ai_knowledge_base_management for pattern learning and sharing.