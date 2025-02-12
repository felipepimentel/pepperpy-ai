---
title: Task Continuation Protocol
description: Safe resumption of in-progress tasks with context recovery and momentum maintenance
version: 2.1
language: en
yolo: true
---

# CORE PRINCIPLES
1. **Context First**: Always reconstruct full task state before acting
2. **Change Safety**: Verify all previous work before new changes
3. **Progress Preservation**: Maintain detailed continuation records

# CONTEXT RECOVERY WORKFLOW

## 1. STATE RECONSTRUCTION
```
Required Checks:
1. Task ID Validation:
   - Pattern: TASK-\d{3}
   - File Exists: .workflow/tasks/{ID}.md
2. Status Verification:
   - Current Status: 🏃 in_progress OR ⏳ blocked
3. Git Context:
   - Correct Branch: task/{ID}
   - Clean Working Tree

Steps:
- Load last 3 progress entries
- Verify requirement completion consistency
- Cross-reference with knowledge base
```

## 2. PROGRESS ANALYSIS
```
Key Elements to Assess:
✓ Last Active Requirement (marked [-])
✓ Open Blockers (if status=⏳ blocked)
✓ Time Since Last Update
✓ Related Code Changes

Output Format:
## Continuation Plan
**Current Focus**: [Requirement Title]
**Next Steps**:
1. [Immediate action]
2. [Secondary action]
3. [Validation needed]
```

# CONTINUATION PROTOCOL

## 1. SAFE RESUMPTION
```
When: Resuming 🏃 in_progress tasks
Steps:
1. Update status marker: 
   - From: ⏳ blocked → 🏃 in_progress (if applicable)
2. Add continuation header:
```markdown
### ➡️ Continued: YYYY-MM-DD HH:MM
- Previous Progress: [Brief summary]
- Current Focus: [Requirement]
- Environment Verified: [Yes/No]
```
3. Commit: "[TASK-XXX] Resumed: [Focus item]"
```

## 2. BLOCKER RESOLUTION
```
When: Clearing ⏳ blocked status
Requirements:
1. Update blocker section:
```markdown
#### RESOLVED: [Blocker Title]
- Resolution Date: YYYY-MM-DD
- Solution: [Method used]
- Remaining Risks: [If any]
```
2. Maintain original blocker log for history
3. Commit: "[TASK-XXX] Unblocked: [Blocker ID]"
```

## 3. PROGRESS DOCUMENTATION
```
Mandatory Fields:
- Changed Files: [File paths]
- Time Invested: [HH:MM]
- Completion Estimate: [Updated %]
- Knowledge Used:
  ```markdown
  - Pattern: [KB Reference]
  - Lesson: [Key insight]
  ```

Example Entry:
### 2025-03-01 14:30 Progress
- Completed: Auth middleware integration
- Time: 1h45m
- Remaining: 2h estimated
- Used Patterns: API_SECURITY_003
```

# VALIDATION CHECKS

## STATUS TRANSITIONS
```
Allowed Resumption Paths:
1. ⏳ blocked → 🏃 in_progress:
   - Require resolved blocker documentation
2. 🏃 in_progress → 🏃 in_progress:
   - Require progress evidence
   
Rejection Conditions:
- Attempt to resume ✅ done tasks
- Missing continuation header
- Unaddressed blockers
```

# EXAMPLE USAGE

## Basic Continuation
```
@task-continue TASK-042 
Context:
- Last State: 🏃 in_progress
- Current Focus: "Rate limit configuration"
Progress:
- Adjusted threshold values
- Added environment variables
```

## Post-Blocker Resumption
```
@task-continue TASK-042 
Resolution:
- Blocker: "DB Connection Pool Exhausted"
- Solution: "Increased pool size + monitoring"
Next Steps:
- Verify connection stability
- Run load tests
```

## Multi-Session Continuation
```
@task-continue TASK-042
Session Report:
- Morning: Implemented core logic (3h)
- Afternoon: Debugged race conditions (2h)
Knowledge Updates:
- Identified new concurrency pattern
- Updated error handling guide
```

# ERROR PREVENTION

## Continuation Safeguards
```
1. Time Gap Check:
   - Warn if resuming >7d old task
   - Require re-validation checklist

2. Requirement Locking:
   - Prevent marking complete without 
     implementation evidence

3. Pattern Verification:
   - Cross-check with knowledge base
   - Flag deprecated methods
```

Remember: Reference testing_standards rule for guidelines and ai_knowledge_base_management for pattern learning and sharing.