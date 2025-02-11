---
title: Validate Project Structure
version: "1.1"
scope: "Pepperpy Project"
description: |
  A tool for validating and maintaining project structure integrity.
  Use this prompt to:
  - Validate compliance with `.product/project_structure.yml`.
  - Propose and log changes to the architecture.
  - Prevent unapproved structural drift.
  - Maintain a consistent and scalable project organization.
---

### **Workflow**
1. **Run Validation Script**  
   Execute `./scripts/validate_structure.py` to verify compliance with `.product/project_structure.yml`.

2. **Handle Discrepancies**  
   If the validation script detects issues:
   - Log unexpected items or missing paths.
   - Analyze the issue and provide a detailed proposal:
     - Justify the need for any new files, directories, or modifications.
     - Suggest alternatives if applicable.
   - Wait for user approval before making any changes.

3. **Log Changes**  
   - Record all proposed and approved changes in `.product/status.md` under the relevant task.
   - Example log entry:
     ```markdown
     ## In Progress
     - TASK-012: Address discrepancies in project structure validation
       - Detected: Missing `pepperpy/providers/vector_store/implementations/milvus.py`.
       - Proposed Action: Create the file with base implementation.
       - Status: Awaiting user approval.
     ```

4. **Prohibited Actions**  
   Avoid the following unless explicitly directed:
   - Creating redundant directories (e.g., `data` vs. `data_store`).
   - Modifying the architecture to bypass validation rules.
   - Introducing structural changes that conflict with the existing design.

5. **Rerun Validation**  
   After user-approved modifications, rerun `./scripts/validate_structure.py` to ensure full compliance.

---

### **Example Workflow**
- Validation Script Output:
- Unexpected item in pepperpy: data
- Missing optional path: pepperpy/providers/vector_store/implementations/milvus.py

- Suggested Actions:
1. Remove the redundant `data` directory (log the action and reasoning).
2. Add `milvus.py` under `pepperpy/providers/vector_store/implementations/` (log justification).

- User Confirmation Required:
- Await explicit approval for all proposed actions.

