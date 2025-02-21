---
title: Library Usability and Example Improvements
priority: high
points: 8
status: 📋 To Do
mode: Plan
created: 2024-02-21
updated: 2024-02-21
---

# Requirements

- [ ] Requirement 1: Simplify Agent Creation and Configuration
  ## Current State
  ```python
  # Current example shows verbose initialization and configuration
  class TaskAssistant(BaseComponent):
      def __init__(self, config: Optional[TaskAssistantConfig] = None) -> None:
          self.config = config or TaskAssistantConfig()
          self.memory: Optional[SimpleMemory] = None
          self._logger = logging.getLogger(__name__)
          self._initialized = False
  ```

  ## Implementation
  ```python
  # Hub-based agent configuration
  # .pepper_hub/agents/task_assistant/v1.0.0.yaml
  """
  name: task_assistant
  version: 1.0.0
  type: agent
  config:
    memory:
      enabled: true
      type: simple
    capabilities:
      - name: search
        config:
          max_results: 5
    logging:
      level: INFO
  """

  # Simple agent creation using Hub configuration
  from pepperpy.agents import Agent
  from pepperpy.hub import HubManager

  class TaskAssistant(Agent):
      """Task Assistant Agent.
      
      Automatically configured from Hub artifact: task_assistant/v1.0.0
      """
      async def process(self, input: str) -> str:
          return await self._process_task(input)

  # Usage - clean and simple
  agent = TaskAssistant.from_hub("task_assistant")  # version defaults to latest
  # or with specific version
  agent = TaskAssistant.from_hub("task_assistant", version="1.0.0")
  ```

  ## Validation
  ```python
  async def test_agent_creation():
      # Test default creation
      agent = TaskAssistant.from_hub("task_assistant")
      assert agent.has_memory()
      assert agent.has_capability("search")
      
      # Test version specific creation
      agent_v1 = TaskAssistant.from_hub("task_assistant", version="1.0.0")
      assert agent_v1.config.memory.enabled
  ```

- [ ] Requirement 2: Standardize Error Handling and Logging
  ## Current State
  ```python
  # Current examples show inconsistent error handling
  try:
      await self.memory.store(key, value)
  except Exception as e:
      self._logger.error("Failed to store", extra={"error": str(e)})
      raise MemoryError(f"Failed to store memory entry: {e}")
  ```

  ## Implementation
  ```python
  # Hub-based error configuration
  # .pepper_hub/errors/memory/v1.0.0.yaml
  """
  name: memory_errors
  version: 1.0.0
  type: error_definitions
  errors:
    store_failed:
      code: MEM001
      message: "Failed to store memory entry: {error}"
      level: ERROR
    retrieve_failed:
      code: MEM002
      message: "Failed to retrieve memory entry: {error}"
      level: ERROR
  """

  from pepperpy.core.errors import error_handler
  from pepperpy.hub import ErrorManager

  class MemoryComponent:
      def __init__(self):
          self.errors = ErrorManager.load("memory_errors")

      @error_handler("memory.store")
      async def store(self, key: str, value: Any) -> None:
          try:
              await self._store.set(key, value)
          except Exception as e:
              raise self.errors.store_failed.with_context(error=str(e))
  ```

  ## Validation
  ```python
  async def test_error_handling():
      memory = MemoryComponent()
      with pytest.raises(MemoryError) as exc:
          await memory.store("key", "value")
      assert exc.value.code == "MEM001"
      assert "Failed to store" in str(exc.value)
  ```

- [ ] Requirement 3: Improve Resource Management and Cleanup
  ## Current State
  ```python
  # Current examples require manual resource management
  async def initialize(self) -> None:
      if self._initialized:
          return
      self.memory = SimpleMemory()
      await self.memory.initialize()
      self._initialized = True
  ```

  ## Implementation
  ```python
  # Hub-based resource configuration
  # .pepper_hub/resources/memory/v1.0.0.yaml
  """
  name: memory_resources
  version: 1.0.0
  type: resource_config
  config:
    auto_cleanup: true
    session_timeout: 3600
    retry_policy:
      max_attempts: 3
      backoff: exponential
  """

  from pepperpy.core.resources import Resource, resource_session
  from pepperpy.hub import ResourceManager

  class MemoryResource(Resource):
      def __init__(self):
          self.config = ResourceManager.load("memory_resources")
          super().__init__(auto_cleanup=self.config.auto_cleanup)

  class TaskAssistant(Agent):
      async def process(self, input: str) -> str:
          async with resource_session(MemoryResource()) as memory:
              return await self._process_with_memory(input, memory)
  ```

  ## Validation
  ```python
  async def test_resource_management():
      async with resource_session(MemoryResource()) as memory:
          assert memory.is_initialized
          await memory.store("test", "value")
      # Resources automatically cleaned up
  ```

- [ ] Requirement 4: Enhance Example Documentation and Structure
  ## Current State
  ```python
  """Quickstart example for the Pepperpy framework."""
  ```

  ## Implementation
  ```python
  """Quickstart Example: Task Management Assistant

  This example demonstrates building a task management assistant using PepperPy.
  All configurations are loaded from the Hub, making the code clean and maintainable.

  Hub Artifacts Used:
  - task_assistant/v1.0.0 (agent configuration)
  - memory_resources/v1.0.0 (resource management)
  - research_prompts/v1.0.0 (string templates)

  Prerequisites:
    - Python 3.12+
    - pip install pepperpy[all]
  
  Quick Start:
    ```bash
    # Install and run
    pip install pepperpy[all]
    python examples/quickstart.py
    ```
  
  Code Overview:
    ```python
    # 1. Create agent from Hub config
    agent = TaskAssistant.from_hub("task_assistant")
    
    # 2. Process tasks with automatic resource management
    async with agent.session() as session:
        result = await session.process("Create a new task")
    ```
  """
  ```

  ## Validation
  ```python
  def test_example_documentation():
      import quickstart
      assert "Hub Artifacts Used" in quickstart.__doc__
      assert "Code Overview" in quickstart.__doc__
  ```

- [ ] Requirement 5: Hub-Centric Resource Management
  ## Current State
  ```python
  # Resources scattered across code
  TEST_PROMPTS = {...}
  ERROR_MESSAGES = {...}
  CONFIG = {...}
  ```

  ## Implementation
  ```python
  # All resources centralized in Hub with clear organization
  # .pepper_hub/
  #   ├── agents/
  #   │   └── task_assistant/
  #   │       └── v1.0.0.yaml    # Agent configuration
  #   ├── resources/
  #   │   └── memory/
  #   │       └── v1.0.0.yaml    # Resource management config
  #   ├── prompts/
  #   │   └── research/
  #   │       └── v1.0.0.yaml    # String templates
  #   └── errors/
  #       └── memory/
  #           └── v1.0.0.yaml    # Error definitions

  from pepperpy.hub import HubManager

  class Application:
      def __init__(self):
          # Single entry point for all Hub resources
          self.hub = HubManager()
          
      async def setup(self):
          # Load all required resources
          self.agent = await self.hub.load_agent("task_assistant")
          self.prompts = await self.hub.load_prompts("research")
          self.errors = await self.hub.load_errors("memory")
  ```

  ## Validation
  ```python
  async def test_hub_integration():
      app = Application()
      await app.setup()
      
      assert app.agent.config == app.hub.get_config("task_assistant")
      assert app.prompts.templates == app.hub.get_prompts("research")
      assert app.errors.definitions == app.hub.get_errors("memory")
  ```

- [ ] Requirement 6: Comprehensive Example Validation
  ## Current State
  ```python
  # Current examples may have inconsistencies or outdated patterns
  # Need to ensure all examples work with the new Hub-centric design
  ```

  ## Implementation
  ```python
  # test_examples.py
  import pytest
  from pathlib import Path
  from typing import List, Dict
  import importlib.util
  import asyncio
  import yaml

  class ExampleValidator:
      """Validates all examples in the examples directory."""
      
      def __init__(self):
          self.examples_dir = Path("examples")
          self.hub_dir = Path(".pepper_hub")
          self.results: Dict[str, bool] = {}

      async def validate_example(self, example_path: Path) -> bool:
          """Validates a single example file."""
          try:
              # 1. Check Hub dependencies
              hub_deps = self._get_hub_dependencies(example_path)
              assert all(self._validate_hub_artifact(dep) for dep in hub_deps)

              # 2. Load and run example
              spec = importlib.util.spec_from_file_location(
                  example_path.stem, example_path
              )
              module = importlib.util.module_from_spec(spec)
              spec.loader.exec_module(module)

              # 3. Run example's main function
              if hasattr(module, "main"):
                  if asyncio.iscoroutinefunction(module.main):
                      await module.main()
                  else:
                      module.main()

              # 4. Validate example's output
              assert self._validate_example_output(example_path)

              return True
          except Exception as e:
              print(f"Failed to validate {example_path}: {e}")
              return False

      def _get_hub_dependencies(self, example_path: Path) -> List[str]:
          """Extracts Hub artifact dependencies from example docstring."""
          with open(example_path) as f:
              content = f.read()
              # Parse docstring to find "Hub Artifacts Used" section
              if "Hub Artifacts Used:" in content:
                  # Extract artifact references
                  return [
                      line.strip("- ").split(" ")[0]
                      for line in content.split("Hub Artifacts Used:")[1].split("\n")
                      if line.strip().startswith("-")
                  ]
          return []

      def _validate_hub_artifact(self, artifact_ref: str) -> bool:
          """Validates that a Hub artifact exists and is valid."""
          name, version = artifact_ref.split("/")
          artifact_path = self.hub_dir / name.split("_")[0] / name / f"{version}.yaml"
          
          if not artifact_path.exists():
              return False

          # Validate YAML structure
          with open(artifact_path) as f:
              try:
                  config = yaml.safe_load(f)
                  assert "name" in config
                  assert "version" in config
                  assert "type" in config
                  return True
              except:
                  return False

      def _validate_example_output(self, example_path: Path) -> bool:
          """Validates example output matches expected results."""
          # Implementation specific to each example
          # Could check for specific files created, API calls made, etc.
          return True

      async def validate_all(self) -> Dict[str, bool]:
          """Validates all examples in the examples directory."""
          for example_path in self.examples_dir.glob("*.py"):
              if example_path.name != "__init__.py":
                  self.results[example_path.name] = await self.validate_example(example_path)
          return self.results

  ```

  ## Validation
  ```python
  async def test_example_validation():
      validator = ExampleValidator()
      results = await validator.validate_all()
      
      # All examples should pass validation
      assert all(results.values()), f"Failed examples: {[k for k,v in results.items() if not v]}"
      
      # Check specific examples
      assert results["quickstart.py"]
      assert results["research_agent.py"]
      assert results["news_podcast.py"]
      
      # Validate Hub artifacts were used
      example_path = Path("examples/quickstart.py")
      deps = validator._get_hub_dependencies(example_path)
      assert "task_assistant/v1.0.0" in deps
      assert "memory_resources/v1.0.0" in deps
  ```

# Progress Updates

## 2024-02-21
- Current Status: Planning phase finalizada
- Completed: 
  - Análise inicial dos exemplos e especificação
  - Revisão focando em simplicidade e coerência
  - Adição de validação completa dos exemplos
- Next Steps: 
  1. Implementar estrutura base do Hub
  2. Criar templates YAML para recursos
  3. Desenvolver HubManager como ponto central
  4. Atualizar exemplos com novo padrão Hub-centric
  5. Documentar padrões de uso do Hub
  6. Implementar sistema de validação de exemplos
  7. Executar e validar todos os exemplos 