---
title: Continue Execution Prompt
version: "1.0"
scope: "Pepperpy Project"
description: |
  A structured prompt for resuming tasks that were interrupted due to execution limits.
  Use this prompt when:
  - The agent reaches its execution limit and halts
  - Continuation of the task is required without starting over
  - Ensuring the context of the previous task remains intact

  This prompt is designed to help the agent pick up where it left off and complete the remaining steps without altering the original context or restarting the process.
---

Continue executing the previous task with these steps:
1. Resume from where the task was interrupted, without restarting or deviating from the original focus.
2. Maintain the context and objectives established in the previous execution.
3. Complete the remaining steps methodically and concisely.
