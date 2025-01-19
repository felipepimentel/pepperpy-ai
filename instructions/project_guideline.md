

### **Pepperpy Project Guidelines**

---

#### **1. Modular Structure**
- Each directory and subdirectory represents a single responsibility.
- Avoid mixing concerns between directories or files.
- Subdirectories, such as `algorithms` or `strategies`, allow easy extension without modifying the base functionality.

---

#### **2. Unified Interfaces**
- Use `__init__.py` files as single points of entry for each module, ensuring abstraction and encapsulation.
- Example:
  ```python
  # tools/extensions/__init__.py
  from .registry import Registry
  from .discovery import Discovery

  __all__ = ["Registry", "Discovery"]
  ```

- Example for dynamic factory logic:
  ```python
  # data/dynamic_sources/__init__.py
  import os
  from .algorithms import AlgorithmA, AlgorithmB

  def get_algorithm():
      algo = os.getenv("ALGORITHM", "AlgorithmA")
      if algo == "AlgorithmA":
          return AlgorithmA()
      elif algo == "AlgorithmB":
          return AlgorithmB()
      else:
          raise ValueError("Unknown algorithm")
  ```

---

#### **3. Dependency Management**
- Use optional dependencies (extras) to minimize mandatory installations.
- Declare optional groups in `pyproject.toml`:
  ```toml
  [tool.poetry.extras]
  rag = ["faiss-cpu", "numpy"]
  llms = ["openai", "transformers"]
  ```
- Avoid hard dependencies on large libraries unless strictly necessary.

---

#### **4. Adherence to Standards**
- Follow **PEP 8** for code style and use **Google-style docstrings**.
- Include type annotations in all functions and classes.
- Use `mypy` for static type checking.

---

#### **5. Test Coverage**
- Write unit tests for all new features or changes.
- Store tests in the `tests/` directory, mirroring the project structure.
- Validate all changes using:
  ```bash
  ./scripts/check.sh
  ```
- Ensure that tests cover edge cases and performance constraints.

---

#### **6. Documentation**
- Each module must include a `README.md` file explaining its purpose, usage, and examples.
- For public functions and classes, include docstrings with:
  - Function purpose.
  - Parameter descriptions.
  - Return type explanations.
- Update `/docs` for new contracts, modules, or functionalities.

---

#### **7. Code Reuse**
- Before adding new features, evaluate existing libraries (`pepperpy-core`, `pepperpy-console`) for reuse opportunities.
- Consult library documentation to align with their interfaces.

---

#### **8. Semantic Git Workflow**
- Use semantic versioning and meaningful commit messages:
  - `feat: add support for multi-LLM orchestration`
  - `fix: resolve memory manager bug in long-term storage`
  - `docs: update usage examples for memory module`

- Workflow:
  1. Stage changes: `git add .`
  2. Commit changes: `git commit -m "<message>"`
  3. Pull updates: `git pull`
  4. Push changes: `git push`

---

#### **9. AI-Driven Code Review**
- Use AI tools to periodically review `/pepperpy_ai` for:
  - Unused or duplicate code.
  - Performance optimizations.
  - Alignment with core principles.

---

#### **10. Focus on Core Objectives**
- Pepperpy's core capabilities include chunking, embedding, RAG, and multi-LLM orchestration.
- Features must prioritize:
  - Flexibility.
  - Scalability.
  - Building block design (allowing selective feature usage).

---

#### **11. Scalability**
- New features must integrate seamlessly without disrupting existing functionality.
- Avoid breaking public APIs unless absolutely necessary.
- All functionality must align with the **building block principle**, enabling consumers to declare and use only the features they need.

---

#### **12. Workflow Integration**
- All changes must be synchronized with GitHub:
  1. Stage changes: `git add .`
  2. Commit with semantic messages: `git commit -m "<message>"`
  3. Pull updates to avoid conflicts: `git pull`
  4. Push changes to remote: `git push`

---

#### **13. Building Block Design**
- Pepperpy is designed for composability and modular usage.
- Avoid tightly coupled logic or hardcoded dependencies.
- Use extras to allow users to install only the necessary features.

---

#### **14. Maintenance and Refactoring**
- Regularly evaluate the codebase for:
  - Dead or unused code.
  - Opportunities for optimization or consolidation.
  - Compliance with the guidelines.

- Update existing tests and documentation after refactoring.