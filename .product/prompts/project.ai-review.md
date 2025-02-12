---
title: "AI Review"
version: "1.1"
scope: "Pepperpy Project"
description: |
  An AI-driven code review and optimization guide.
  Use this prompt when:
    - Conducting periodic code reviews
    - Looking for optimization opportunities
    - Identifying technical debt
    - Planning refactoring efforts
    - Improving code quality
  
  This prompt leverages AI capabilities to systematically analyze
  and enhance the codebase while upholding project standards and 
  adopting a visionary approach for future maintainability.
---

1. **Initial Assessment**
   - Perform an AI-driven scan of the entire codebase to identify:
     - Dead or unused code blocks.
     - Potential performance bottlenecks.
     - Redundant or repetitive functions.
   - Note any **immediate** issues in `.product/kanban.md` for further review.

2. **Identify Technical Debt**
   - List any code sections that appear overly complex, outdated, or prone to bugs.
   - Document **why** these areas present technical debt (e.g., legacy design patterns, insufficient test coverage).

3. **Look for Optimization Opportunities**
   - Recommend performance improvements, such as:
     - More efficient data structures or algorithms.
     - Caching or lazy-loading where beneficial.
   - Evaluate the feasibility and potential impact of each optimization.

4. **Refactoring and Modularization**
   - Suggest ways to **refactor** large or monolithic modules into smaller, more reusable components.
   - Propose **modularization** opportunities that align with the project's architecture and best practices, referencing `.product/project_structure.yml` where relevant.

5. **Code Quality and Readability**
   - Check for coding style inconsistencies, deprecated functions, or poorly named variables.
   - Flag any debugging statements or commented-out code that should be removed or updated.
   - Recommend updates to maintain a clean, readable, and maintainable codebase.

6. **Documentation and Tests**
   - Assess the documentation for accuracy and completeness. Suggest improvements where needed.
   - Review test coverage to confirm critical code paths are tested. Propose added or improved tests if coverage is lacking.

7. **Visionary Enhancements**
   - Encourage forward-thinking improvements that help **future-proof** the code.
   - Identify emerging industry best practices or design patterns that could keep the project modern and scalable.

8. **Log Findings and Recommendations**
   - Compile all identified issues, suggested optimizations, and refactoring plans into `.product/kanban.md`.
   - Prioritize or categorize items by **impact**, **complexity**, and **urgency** to guide future development efforts.

9. **Follow-up and Implementation**
   - Optionally, coordinate with maintainers or a dedicated development team to plan and implement the recommended changes.
   - After each change, re-run applicable tests and confirm the project remains stable and aligned with best practices.