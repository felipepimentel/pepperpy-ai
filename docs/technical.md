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

#### **3. Provider Factory Pattern + Registry**
- Use a central **Registry** to dynamically manage providers and frameworks.
- Implement a **Factory Pattern** to configure and build components at runtime.
- Example of provider registration:
  ```python
  from typing import Type, Dict, Any

  # Centralized Registry for Providers
  class ProviderRegistry:
      _registry: Dict[str, Type] = {}

      @classmethod
      def register(cls, name: str):
          def decorator(provider_cls: Type):
              cls._registry[name] = provider_cls
              return provider_cls
          return decorator

      @classmethod
      def get(cls, name: str) -> Type:
          if name not in cls._registry:
              raise ValueError(f"Provider '{name}' not registered.")
          return cls._registry[name]

  # Base Adapter for LLMs
  class BaseLLMAdapter:
      def __init__(self, config: Dict[str, Any]):
          self.config = config

      async def generate(self, prompt: str) -> str:
          raise NotImplementedError("Specific implementation required.")

  # Registering the Gemini Adapter
  @ProviderRegistry.register("gemini")
  class GeminiAdapter(BaseLLMAdapter):
      async def generate(self, prompt: str) -> str:
          # Specific implementation for Gemini
          return f"Gemini response to: {prompt}"
  ```

- Example of dynamic Agent construction:
  ```python
  class AgentBuilder:
      def __init__(self):
          self.llm = None
          self.reasoning = None

      def with_llm(self, name: str, config: Dict[str, Any]):
          adapter_cls = ProviderRegistry.get(name)
          self.llm = adapter_cls(config)
          return self

      def with_reasoning(self, name: str, config: Dict[str, Any]):
          framework_cls = ProviderRegistry.get(name)
          self.reasoning = framework_cls(config)
          return self

      def build(self):
          return Agent(self.llm, self.reasoning)
  ```

---

#### **4. Dependency Management**
- Use optional dependencies (extras) to minimize mandatory installations.
- Declare optional groups in `pyproject.toml`:
  ```toml
  [tool.poetry.extras]
  rag = ["faiss-cpu", "numpy"]
  llms = ["openai", "transformers"]
  ```
- Avoid hard dependencies on large libraries unless strictly necessary.

---

#### **5. Adherence to Standards**
- Follow **PEP 8** for code style and use **Google-style docstrings**.
- Include type annotations in all functions and classes.
- Use `mypy` for static type checking.

---

#### **6. Test Coverage**
- Write unit tests for all new features or changes.
- Store tests in the `tests/` directory, mirroring the project structure.
- Validate all changes using:
  ```bash
  ./scripts/check.sh
  ```
- Ensure that tests cover edge cases and performance constraints.

---

#### **7. Documentation**
- Each module must include a `README.md` file explaining its purpose, usage, and examples.
- For public functions and classes, include docstrings with:
  - Function purpose.
  - Parameter descriptions.
  - Return type explanations.
- Update `/docs` for new contracts, modules, or functionalities.

---

#### **8. Code Reuse**
- Before adding new features, evaluate existing libraries (`pepperpy-core`, `pepperpy-console`) for reuse opportunities.
- Consult library documentation to align with their interfaces.

---

#### **9. Semantic Git Workflow**
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

#### **10. AI-Driven Code Review**
- Use AI tools to periodically review `/pepperpy_ai` for:
  - Unused or duplicate code.
  - Performance optimizations.
  - Alignment with core principles.

---

#### **11. Focus on Core Objectives**
- Pepperpy's core capabilities include chunking, embedding, RAG, and multi-LLM orchestration.
- Features must prioritize:
  - Flexibility.
  - Scalability.
  - Building block design (allowing selective feature usage).

---

#### **12. Scalability**
- New features must integrate seamlessly without disrupting existing functionality.
- Avoid breaking public APIs unless absolutely necessary.
- All functionality must align with the **building block principle**, enabling consumers to declare and use only the features they need.

---

#### **13. Workflow Integration**
- All changes must be synchronized with GitHub:
  1. Stage changes: `git add .`
  2. Commit with semantic messages: `git commit -m "<message>"`
  3. Pull updates to avoid conflicts: `git pull`
  4. Push changes to remote: `git push`

---

#### **14. Building Block Design**
- Pepperpy is designed for composability and modular usage.
- Avoid tightly coupled logic or hardcoded dependencies.
- Use extras to allow users to install only the necessary features.

---

#### **15. Maintenance and Refactoring**
- Regularly evaluate the codebase for:
  - Dead or unused code.
  - Opportunities for optimization or consolidation.
  - Compliance with the guidelines.

- Update existing tests and documentation after refactoring.

---

#### **16. Python Guidelines**
- Follow PEP 8 guidelines.
- Use `black` for code formatting with a line length of 88.
- Use double quotes for strings.
- Use type hints for all function parameters and return types.
- Prefer `async`/`await` for I/O operations.
- Follow the principle of least privilege.

#### **17. Testing**
- Write unit tests for all new features.
- Maintain test coverage above 80%.
- Use `pytest` for testing.
- Write async tests using `pytest-asyncio`.
- Mock external dependencies.

---

#### **18. Error Handling**
- Define custom exceptions in `exceptions.py`.
- Include context in error messages.
- Log errors appropriately with structured logging.
- Handle edge cases explicitly.

---

#### **19. Security**
- Never store sensitive data in code.
- Use environment variables for configuration.
- Follow secure coding practices.
- Validate all inputs and sanitize where appropriate.
- Handle errors gracefully.

---

#### **20. Monitoring and Metrics**
- Use structured logging with context information.
- Implement proper log levels and telemetry for performance metrics.
- Track error rates and monitor for anomalies.

---

#### **21. Dependency Management**
- Use Poetry for dependency management.
- Pin dependency versions.
- Keep dependencies up-to-date.
- Separate optional dependencies in `pyproject.toml`.

---

#### **22. Quality Checks**
- Run `./scripts/check.sh` for type checking and linting.
- Maintain a clean build status.

