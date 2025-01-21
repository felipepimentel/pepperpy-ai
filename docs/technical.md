---
type: "technical-guidelines"
scope: "Pepperpy Project"
version: "1.2"
dependencies:
  - "docs/architecture.mermaid"
  - "docs/project_structure.md"
---

# Technical Guidelines

## **0. Pre-Modification Review**
- Always review the [Project Structure](docs/project_structure.md) document before making any changes to ensure alignment with the architecture and modularity principles.
- Confirm compliance with directory and file responsibilities as outlined in the project structure.
- Validate changes against the [Architecture Overview](docs/architecture.mermaid) to ensure they align with the system's modular and scalable design.

---

## **1. Modular Structure**
- Each directory and subdirectory represents a single responsibility.
- Avoid mixing concerns between directories or files.
- Subdirectories, such as `algorithms` or `strategies`, allow easy extension without modifying the base functionality.
- Example of directory structure:
  ```plaintext
  pepperpy/
  ├── core/        # Core utilities and shared logic
  ├── algorithms/  # Algorithm implementations
  ├── providers/   # Provider modules (e.g., LLM, Vector Stores)
  ├── services/    # High-level services orchestrating providers
  └── tests/       # Unit and integration tests
  ```
- Each module within a directory should be self-contained and provide clear interfaces via `__init__.py` files:
  ```python
  # Example: providers/__init__.py
  from .llm_provider import LLMProvider
  from .vector_store_provider import VectorStoreProvider

  __all__ = ["LLMProvider", "VectorStoreProvider"]
  ```

---

## **2. Unified Interfaces**
- Use `__init__.py` files as single points of entry for each module, ensuring abstraction and encapsulation.
- Maintain clean, well-documented APIs within each module.

---

## **3. Provider Factory Pattern + Registry**
- Use a central **Registry** to dynamically manage providers and frameworks.
- Implement a **Factory Pattern** for runtime configuration and component construction.
- Ensure all registered providers include appropriate validation mechanisms for runtime consistency.

---

## **4. Provider System**

### Overview
- The Pepperpy project uses a modular provider system for managing different components:
  - **LLM Providers**: Handle interactions with language models.
  - **Vector Store Providers**: Manage vector storage and retrieval.
  - **Embedding Providers**: Generate embeddings from text.
  - **Memory Providers**: Handle conversation history and state.

### Provider Configuration
All providers use a standardized configuration structure:
```python
@dataclass
class ProviderConfig:
    type: str                              # Provider type identifier
    parameters: Dict[str, Any] = {}        # Provider-specific parameters
    metadata: Dict[str, Any] = {}          # Additional metadata
```

### Agent Configuration
Agents are configured using a comprehensive configuration structure:
```python
@dataclass
class AgentConfig:
    name: str                              # Agent name
    description: str                       # Agent description
    llm_provider: ProviderConfig           # Required LLM provider
    vector_store_provider: Optional[ProviderConfig] = None  # Optional vector store
    embedding_provider: Optional[ProviderConfig] = None     # Optional embeddings
    memory_provider: Optional[ProviderConfig] = None        # Optional memory
    parameters: Dict[str, Any] = {}        # Agent parameters
    metadata: Dict[str, Any] = {}          # Additional metadata
```

---

## **5. Dependency Management**
- Use optional dependencies (extras) to minimize mandatory installations.
- Declare optional groups in `pyproject.toml` to allow selective feature usage.

---

## **6. Testing Standards**
- Maintain test coverage above 80%.
- Use `pytest` for testing and `pytest-asyncio` for async tests.
- Mock external dependencies to isolate unit tests.
- Always write tests for:
  - Edge cases.
  - Performance-critical components.
  - Newly added or refactored modules.

---

## **7. Documentation Standards**
- All public APIs must include Google-style docstrings.
- Provide examples for complex or non-intuitive functions.
- Update `/docs` for all changes that affect functionality or architecture.
- Include architecture or workflow diagrams in `docs/` as necessary.

---

## **8. Error Handling**
- Define custom exceptions in `exceptions.py`.
- Ensure error messages include context and are logged appropriately.
- Handle edge cases explicitly.
- Implement fallback mechanisms for critical failures.

---

## **9. Scalability and Building Block Design**
- Follow the **building block principle**, ensuring features can be used independently.
- Avoid tightly coupled logic or hardcoded dependencies.
- Design for horizontal scaling and modular extension.

---

## **10. Security**
- Never store sensitive data in code.
- Use environment variables for all configuration.
- Validate all user inputs and sanitize where necessary.
- Regularly audit dependencies for security vulnerabilities.

---

## **11. Quality Checks**
- Run `./scripts/check.sh` for linting and type checking.
- Ensure compliance with PEP 8 and Google-style docstrings.
- Use `mypy` for static type checks.

---

## **12. AI-Driven Code Review**
- Periodically evaluate `/pepperpy` for:
  - Unused or duplicate code.
  - Alignment with core principles.
  - Performance optimizations.
- Use AI tools to review refactor opportunities and dead code.

---

## **13. Semantic Git Workflow**
- Use semantic versioning and meaningful commit messages.
- Example commit types:
  - `feat`: New feature additions.
  - `fix`: Bug fixes.
  - `docs`: Documentation updates.

---

## **14. Workflow Integration**
- All changes must follow the GitHub workflow outlined in `.cursorrules`.
- Include testing, documentation, and architectural validation as part of every PR.

---

## **15. Maintenance and Refactoring**
- Regularly review code for optimization opportunities and compliance with standards.
- Update documentation and tests post-refactoring.
- Remove deprecated code responsibly, with clear versioning and migration guidelines.

---

## **16. Agent Service**

### Overview
- The agent service manages the lifecycle of agents:
  - Creation and initialization.
  - Registration and tracking.
  - Process execution.
  - Cleanup and resource management.

### Usage Example
```python
# Create service
service = AgentService("my_service")

# Create agent
config = {
    "name": "my_agent",
    "description": "Example agent",
    "llm_provider": {
        "type": "openrouter",
        "parameters": {"model": "gpt-3.5-turbo"}
    }
}
agent = await service.create_agent("chat", config)

# Process input
result = await service.process("my_agent", "Hello!")

# Cleanup
await service.cleanup()
```

---

## **17. Resource Management**

### Initialization
- Providers must implement `initialize()` method.
- Validate configuration before initialization.
- Set up required resources and connections.
- Handle initialization failures gracefully.

### Cleanup
- Providers must implement `cleanup()` method.
- Release all acquired resources.
- Close connections and handles.
- Log cleanup status and errors.
