---
title: Code Organization and Structure Improvements
priority: high
points: 8
status: 📋 To Do
mode: Plan
created: 2024-02-14
updated: 2024-02-14
---

# Overview

This task focuses on improving code organization and structure through systematic refactoring and consolidation. The changes will be implemented in a sequence that minimizes disruption while maximizing code quality and maintainability.

# Requirements

- [ ] Standardize Component Lifecycle
  ## Current State
  ```python
  # Different initialization patterns
  # Inconsistent cleanup
  # Manual resource management

  class Agent:
      def initialize(self):
          pass

  class Provider:
      def setup(self):
          pass

  class Store:
      def connect(self):
          pass
  ```

  ## Implementation
  ```python
  # core/lifecycle.py
  from abc import ABC, abstractmethod
  from typing import Optional, Any, Dict
  from enum import Enum
  import logging

  logger = logging.getLogger(__name__)

  class ComponentState(Enum):
      CREATED = "created"
      INITIALIZING = "initializing"
      READY = "ready"
      ERROR = "error"
      SHUTTING_DOWN = "shutting_down"
      TERMINATED = "terminated"

  class Lifecycle(ABC):
      """Base interface for components with lifecycle."""
      def __init__(self):
          self._state = ComponentState.CREATED
          self._error: Optional[Exception] = None
          self._metadata: Dict[str, Any] = {}

      @property
      def state(self) -> ComponentState:
          return self._state

      @property
      def error(self) -> Optional[Exception]:
          return self._error

      @abstractmethod
      async def initialize(self) -> None:
          """Initialize the component."""
          pass

      @abstractmethod
      async def cleanup(self) -> None:
          """Clean up component resources."""
          pass

  class LifecycleManager:
      """Central lifecycle manager."""
      def __init__(self):
          self._components: Dict[str, Lifecycle] = {}

      async def register(self, name: str, component: Lifecycle) -> None:
          """Register and initialize a component."""
          if name in self._components:
              raise ValueError(f"Component {name} already registered")
          
          try:
              self._components[name] = component
              await component.initialize()
          except Exception as e:
              component._error = e
              component._state = ComponentState.ERROR
              raise

      async def shutdown(self) -> None:
          """Shutdown all components in reverse order."""
          for name in reversed(list(self._components)):
              component = self._components[name]
              try:
                  component._state = ComponentState.SHUTTING_DOWN
                  await component.cleanup()
                  component._state = ComponentState.TERMINATED
              except Exception as e:
                  component._error = e
                  component._state = ComponentState.ERROR
                  logger.error(f"Error shutting down {name}: {e}")
  ```

  ## Validation
  ```python
  import pytest
  from unittest.mock import AsyncMock, Mock

  class TestComponent(Lifecycle):
      async def initialize(self):
          self._state = ComponentState.READY
      
      async def cleanup(self):
          self._state = ComponentState.TERMINATED

  async def test_lifecycle():
      # Test component lifecycle
      component = TestComponent()
      assert component.state == ComponentState.CREATED
      assert component.error is None
      
      await component.initialize()
      assert component.state == ComponentState.READY
      
      await component.cleanup()
      assert component.state == ComponentState.TERMINATED

      # Test lifecycle manager
      manager = LifecycleManager()
      await manager.register("test", component)
      assert "test" in manager._components
      
      # Test duplicate registration
      with pytest.raises(ValueError):
          await manager.register("test", TestComponent())
      
      # Test error handling
      error_component = TestComponent()
      error_component.initialize = AsyncMock(side_effect=RuntimeError("Test error"))
      
      with pytest.raises(RuntimeError):
          await manager.register("error", error_component)
      assert error_component.state == ComponentState.ERROR
      assert isinstance(error_component.error, RuntimeError)
      
      await manager.shutdown()
      assert all(c.state == ComponentState.TERMINATED 
                for c in manager._components.values())
  ```

  ## Cleanup Required
  After implementation and validation, remove:
  ```
  - pepperpy/agents/lifecycle.py
  - pepperpy/providers/lifecycle.py
  - pepperpy/store/lifecycle.py
  ```

- [ ] Unify Configuration System
  ## Current State
  ```python
  # Multiple configuration classes in core/config.py
  # Overlapping AutoConfig and PepperpyConfig
  # Configuration scattered across modules

  class PepperpyConfig(BaseModel):
      pass

  class AutoConfig:
      @classmethod
      def from_env(cls):
          pass

  class ConfigManager:
      def load(self):
          pass
  ```

  ## Implementation
  ```python
  # core/config/base.py
  from typing import TypeVar, Generic
  from pydantic import BaseModel

  T = TypeVar("T", bound=BaseModel)

  class ConfigurationManager(Generic[T]):
      """Unified configuration manager."""
      def __init__(self, config_class: Type[T]):
          self.config_class = config_class
          self._config: Optional[T] = None
          self._watchers: Set[ConfigWatcher] = set()

      async def load(self, sources: List[ConfigSource]) -> T:
          """Load configuration from multiple sources."""
          config_data = {}
          for source in sources:
              data = await source.load()
              config_data.update(data)
          
          self._config = self.config_class(**config_data)
          await self._notify_watchers()
          return self._config

  # core/config/sources.py
  class ConfigSource(Protocol):
      """Configuration source."""
      async def load(self) -> Dict[str, Any]:
          pass

  class EnvSource(ConfigSource):
      """Environment variable configuration."""
      def __init__(self, prefix: str = "PEPPERPY_"):
          self.prefix = prefix

      async def load(self) -> Dict[str, Any]:
          return {k[len(self.prefix):].lower(): v 
                 for k, v in os.environ.items() 
                 if k.startswith(self.prefix)}

  # core/config/watchers.py
  class ConfigWatcher(Protocol):
      """Configuration change observer."""
      async def on_config_change(self, old: BaseModel, new: BaseModel) -> None:
          pass
  ```

  ## Validation
  ```python
  async def test_config_manager():
      manager = ConfigurationManager(PepperpyConfig)
      config = await manager.load([
          EnvSource(prefix="TEST_"),
          FileSource("config.yml")
      ])
      assert isinstance(config, PepperpyConfig)
      
      # Test watcher
      watcher = MockConfigWatcher()
      manager.add_watcher(watcher)
      await manager.reload()
      assert watcher.called
  ```

  ## Cleanup Required
  After implementation and validation, remove:
  ```
  - pepperpy/core/config.py
  - pepperpy/core/auto_config.py
  - pepperpy/agents/config.py
  - pepperpy/providers/config.py
  ```

- [ ] Flatten Capabilities Structure
  ## Current State
  ```python
  # capabilities/learning/errors.py
  class LearningError(Exception):
      pass

  # capabilities/planning/errors.py
  class PlanningError(Exception):
      pass

  # capabilities/reasoning/errors.py
  class ReasoningError(Exception):
      pass
  ```

  ## Implementation
  ```python
  # capabilities/errors.py
  from enum import Enum

  class CapabilityType(Enum):
      LEARNING = "learning"
      PLANNING = "planning"
      REASONING = "reasoning"

  class CapabilityError(Exception):
      def __init__(self, type: CapabilityType, message: str):
          self.type = type
          self.message = message
          super().__init__(f"{type.value}: {message}")

  # capabilities/__init__.py
  from .errors import CapabilityError, CapabilityType
  ```

  ## Validation
  ```python
  def test_capability_errors():
      error = CapabilityError(CapabilityType.LEARNING, "test error")
      assert error.type == CapabilityType.LEARNING
      assert str(error) == "learning: test error"

      with pytest.raises(CapabilityError) as exc:
          raise CapabilityError(CapabilityType.PLANNING, "test")
      assert str(exc.value) == "planning: test"
  ```

  ## Cleanup Required
  After implementation and validation, remove:
  ```
  - pepperpy/capabilities/learning/errors.py
  - pepperpy/capabilities/planning/errors.py
  - pepperpy/capabilities/reasoning/errors.py
  - pepperpy/capabilities/learning/exceptions/
  - pepperpy/capabilities/planning/exceptions/
  - pepperpy/capabilities/reasoning/exceptions/
  ```

- [ ] Improve Monitoring System
  ## Current State
  ```python
  # Mixed logging and metrics in monitoring/monitoring.py
  # Scattered logging configuration
  # Lack of tracing structure

  root_logger = logging.getLogger("pepperpy")
  metrics_enabled = True
  tracing_enabled = True
  ```

  ## Implementation
  ```python
  # monitoring/logging.py
  from structlog import BoundLogger, get_logger
  from typing import Optional, Any

  class LoggerFactory:
      """Centralized logger factory."""
      @classmethod
      def get_logger(cls, 
                    module: str, 
                    context: Optional[Dict[str, Any]] = None) -> BoundLogger:
          logger = get_logger()
          if context:
              logger = logger.bind(**context)
          return logger.bind(module=module)

  # monitoring/metrics.py
  from dataclasses import dataclass
  from enum import Enum
  from typing import Dict, Any

  class MetricType(Enum):
      COUNTER = "counter"
      GAUGE = "gauge"
      HISTOGRAM = "histogram"

  @dataclass
  class Metric:
      name: str
      type: MetricType
      value: float
      labels: Dict[str, str]

  class MetricsManager:
      """Central metrics manager."""
      def __init__(self):
          self._metrics: Dict[str, Metric] = {}
          self._exporters: List[MetricExporter] = []

      async def record(self, metric: Metric) -> None:
          self._metrics[metric.name] = metric
          await self._export(metric)

  # monitoring/tracing.py
  from opentelemetry import trace
  from contextlib import asynccontextmanager

  class TracingManager:
      """Central tracing manager."""
      def __init__(self):
          self.tracer = trace.get_tracer(__name__)

      @asynccontextmanager
      async def span(self, name: str, attributes: Dict[str, str]):
          with self.tracer.start_as_current_span(name) as span:
              for key, value in attributes.items():
                  span.set_attribute(key, value)
              yield span
  ```

  ## Validation
  ```python
  async def test_monitoring():
      # Test logging
      logger = LoggerFactory.get_logger("test", {"env": "test"})
      assert "env" in logger._context
      assert logger._context["module"] == "test"

      # Test metrics
      manager = MetricsManager()
      metric = Metric("requests", MetricType.COUNTER, 1.0, {"endpoint": "/test"})
      await manager.record(metric)
      assert "requests" in manager._metrics

      # Test tracing
      tracer = TracingManager()
      async with tracer.span("test_op", {"service": "api"}) as span:
          assert span.is_recording()
          assert span.attributes["service"] == "api"
  ```

  ## Cleanup Required
  After implementation and validation, remove:
  ```
  - pepperpy/monitoring/monitoring.py
  - pepperpy/core/logging.py
  - pepperpy/core/metrics.py
  - pepperpy/agents/logging.py
  - pepperpy/providers/logging.py
  ```

- [ ] Integrate Resource Management
  ## Current State
  ```python
  # Mixed resource management in resources/resources.py
  # Scattered resource configuration
  # Lack of management structure

  class Resource:
      def __init__(self, name: str, type: str, config: dict):
          self.name = name
          self.type = type
          self.config = config

  class ResourceManager:
      def __init__(self):
          self._resources: Dict[str, Resource] = {}

      def add_resource(self, resource: Resource) -> None:
          self._resources[resource.name] = resource

      def get_resource(self, name: str) -> Resource:
          return self._resources.get(name)

      def remove_resource(self, name: str) -> None:
          self._resources.pop(name, None)
  ```

  ## Implementation
  ```python
  # core/resources/manager.py
  from typing import Dict, Any, Optional
  from enum import Enum
  from dataclasses import dataclass

  class ResourceType(Enum):
      STORAGE = "storage"
      COMPUTE = "compute"
      NETWORK = "network"

  @dataclass
  class ResourceConfig:
      type: ResourceType
      settings: Dict[str, Any]
      metadata: Optional[Dict[str, str]] = None

  class Resource:
      def __init__(self, name: str, config: ResourceConfig):
          self.name = name
          self.config = config
          self._state = ResourceState.CREATED

  class ResourceManager:
      """Unified resource manager."""
      def __init__(self):
          self._resources: Dict[str, Resource] = {}
          self._lifecycle = LifecycleManager()

      async def register(self, resource: Resource) -> None:
          """Register and initialize a resource."""
          await self._lifecycle.register(resource.name, resource)
          self._resources[resource.name] = resource

      async def get(self, name: str) -> Optional[Resource]:
          """Get a registered resource."""
          return self._resources.get(name)

      async def cleanup(self) -> None:
          """Clean up all resources."""
          await self._lifecycle.shutdown()
  ```

  ## Validation
  ```python
  async def test_resource_manager():
      manager = ResourceManager()
      
      config = ResourceConfig(
          type=ResourceType.STORAGE,
          settings={"path": "/tmp/test"},
          metadata={"env": "test"}
      )
      
      resource = Resource("test_storage", config)
      await manager.register(resource)
      
      retrieved = await manager.get("test_storage")
      assert retrieved.name == "test_storage"
      assert retrieved.config.type == ResourceType.STORAGE
      
      await manager.cleanup()
      assert all(r.state == ResourceState.TERMINATED 
                for r in manager._resources.values())
  ```

  ## Cleanup Required
  After implementation and validation, remove:
  ```
  - pepperpy/resources/resources.py
  - pepperpy/resources/manager.py
  - pepperpy/core/resources.py
  - pepperpy/agents/resources/
  - pepperpy/providers/resources/
  ```

- [ ] Consolidate Workflow System
  ## Current State
  ```python
  # Mixed workflow management in workflows/workflows.py
  # Scattered workflow configuration
  # Lack of execution structure

  class Workflow:
      def __init__(self, name: str, steps: List[str]):
          self.name = name
          self.steps = steps

  class WorkflowManager:
      def __init__(self):
          self._workflows: Dict[str, Workflow] = {}
  ```

  ## Implementation
  ```python
  # core/workflows/engine.py
  from typing import Dict, List, Any, Optional
  from enum import Enum
  from dataclasses import dataclass

  class WorkflowState(Enum):
      CREATED = "created"
      RUNNING = "running"
      COMPLETED = "completed"
      FAILED = "failed"

  @dataclass
  class WorkflowStep:
      name: str
      action: str
      inputs: Dict[str, Any]
      outputs: Optional[List[str]] = None
      
  class WorkflowContext:
      def __init__(self):
          self.variables: Dict[str, Any] = {}
          self.state = WorkflowState.CREATED
          self._history: List[Dict[str, Any]] = []

  class WorkflowEngine:
      """Unified workflow engine."""
      def __init__(self):
          self._workflows: Dict[str, List[WorkflowStep]] = {}
          self._contexts: Dict[str, WorkflowContext] = {}

      async def register(self, name: str, steps: List[WorkflowStep]) -> None:
          """Register a new workflow."""
          self._workflows[name] = steps
          self._contexts[name] = WorkflowContext()

      async def execute(self, name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
          """Execute a workflow with given inputs."""
          context = self._contexts[name]
          context.variables.update(inputs)
          context.state = WorkflowState.RUNNING

          try:
              for step in self._workflows[name]:
                  result = await self._execute_step(step, context)
                  if step.outputs:
                      for output in step.outputs:
                          context.variables[output] = result[output]
              
              context.state = WorkflowState.COMPLETED
              return context.variables
          except Exception as e:
              context.state = WorkflowState.FAILED
              raise WorkflowError(f"Workflow {name} failed: {str(e)}")
  ```

  ## Validation
  ```python
  async def test_workflow_engine():
      engine = WorkflowEngine()
      
      steps = [
          WorkflowStep(
              name="step1",
              action="test_action",
              inputs={"input1": "value1"},
              outputs=["result1"]
          )
      ]
      
      await engine.register("test_workflow", steps)
      
      result = await engine.execute("test_workflow", {"initial": "value"})
      assert "result1" in result
      
      context = engine._contexts["test_workflow"]
      assert context.state == WorkflowState.COMPLETED
  ```

  ## Cleanup Required
  After implementation and validation, remove:
  ```
  - pepperpy/workflows/workflows.py
  - pepperpy/workflows/manager.py
  - pepperpy/workflows/executor.py
  - pepperpy/agents/workflows/
  - pepperpy/providers/workflows/
  ```

- [ ] Reorganize Hub Structure
  ## Current State
  ```python
  # Mixed hub management in hub/hub.py
  # Scattered hub configuration
  # Lack of integration structure

  class Hub:
      def __init__(self, name: str, resources: List[str], workflows: List[str]):
          self.name = name
          self.resources = resources
          self.workflows = workflows
  ```

  ## Implementation
  ```python
  # core/hub/manager.py
  from typing import Dict, List, Optional
  from dataclasses import dataclass
  from enum import Enum

  class HubType(Enum):
      LOCAL = "local"
      REMOTE = "remote"
      HYBRID = "hybrid"

  @dataclass
  class HubConfig:
      type: HubType
      resources: List[str]
      workflows: List[str]
      metadata: Optional[Dict[str, str]] = None

  class Hub:
      """Unified hub representation."""
      def __init__(self, name: str, config: HubConfig):
          self.name = name
          self.config = config
          self._resource_manager = ResourceManager()
          self._workflow_engine = WorkflowEngine()

      async def initialize(self) -> None:
          """Initialize hub resources and workflows."""
          for resource in self.config.resources:
              await self._resource_manager.register(resource)
          
          for workflow in self.config.workflows:
              await self._workflow_engine.register(workflow)

  class HubManager:
      """Central hub manager."""
      def __init__(self):
          self._hubs: Dict[str, Hub] = {}
          self._lifecycle = LifecycleManager()

      async def register(self, name: str, config: HubConfig) -> None:
          """Register and initialize a new hub."""
          hub = Hub(name, config)
          await self._lifecycle.register(name, hub)
          self._hubs[name] = hub

      async def get(self, name: str) -> Optional[Hub]:
          """Get a registered hub."""
          return self._hubs.get(name)

      async def cleanup(self) -> None:
          """Clean up all hubs."""
          await self._lifecycle.shutdown()
  ```

  ## Validation
  ```python
  async def test_hub_manager():
      manager = HubManager()
      
      config = HubConfig(
          type=HubType.LOCAL,
          resources=["resource1"],
          workflows=["workflow1"],
          metadata={"env": "test"}
      )
      
      await manager.register("test_hub", config)
      
      hub = await manager.get("test_hub")
      assert hub.name == "test_hub"
      assert hub.config.type == HubType.LOCAL
      
      await manager.cleanup()
      assert all(h._state == ComponentState.TERMINATED 
                for h in manager._hubs.values())
  ```

  ## Cleanup Required
  After implementation and validation, remove:
  ```
  - pepperpy/hub/hub.py
  - pepperpy/hub/manager.py
  - pepperpy/hub/executor.py
  - pepperpy/agents/hub/
  - pepperpy/providers/hub/
  ```

# Dependencies

Component dependencies in order of implementation:

1. **Component Lifecycle**
   - No external dependencies
   - Required by: All other components

2. **Configuration System**
   - Depends on: Component Lifecycle
   - Required by: All other components

3. **Capabilities Structure**
   - Depends on: Component Lifecycle
   - Required by: Monitoring, Resources

4. **Monitoring System**
   - Depends on: Component Lifecycle, Configuration
   - Required by: Resources, Workflows, Hub

5. **Resource Management**
   - Depends on: Component Lifecycle, Configuration, Monitoring
   - Required by: Workflows, Hub

6. **Workflow System**
   - Depends on: Component Lifecycle, Configuration, Monitoring, Resources
   - Required by: Hub

7. **Hub Structure**
   - Depends on: All other components

# Implementation Strategy

1. **Phase 1: Core Infrastructure**
   - Implement Component Lifecycle
   - Implement Configuration System
   - Migrate core components to new structure

2. **Phase 2: System Components**
   - Implement Capabilities Structure
   - Implement Monitoring System
   - Implement Resource Management

3. **Phase 3: Integration Layer**
   - Implement Workflow System
   - Implement Hub Structure
   - Finalize component integration

# Migration Guidelines

1. **Code Migration**
   ```
   Before:                     After:
   pepperpy/                   pepperpy/
   ├── agents/                 ├── core/
   ├── providers/             │   ├── lifecycle/
   ├── store/                 │   ├── config/
   ├── capabilities/          │   ├── capabilities/
   ├── monitoring/            │   ├── monitoring/
   ├── resources/             │   ├── resources/
   ├── workflows/             │   ├── workflows/
   └── hub/                   │   └── hub/
                             └── legacy/  # Temporary
   ```

2. **Testing Strategy**
   - Unit tests for each component
   - Integration tests between components
   - Migration tests for backward compatibility
   - Performance benchmarks before/after

3. **Documentation Updates**
   - Update API documentation
   - Add migration guides
   - Update example code
   - Document breaking changes

# Validation Checklist

For each component:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] No import errors
- [ ] Documentation updated
- [ ] Examples working
- [ ] Performance verified
- [ ] Breaking changes documented
- [ ] Deprecation warnings added
- [ ] Backup created
- [ ] Old files removed

# Important Notes

1. **File Cleanup Process**:
   - Only remove files after the new implementation is tested and validated
   - Keep a backup of removed files until the entire task is completed
   - Update all import statements in dependent files
   - Run the full test suite after each cleanup
   - Document all removed files in the migration log

2. **Directory Structure Changes**:
   - All new implementations go into the `core/` directory
   - Existing implementations are gradually migrated
   - Old directories are removed only after all dependencies are updated
   - Each module follows the new structure pattern:
     ```
     core/
     ├── module_name/
     │   ├── __init__.py
     │   ├── base.py
     │   ├── manager.py
     │   └── types.py
     ```

3. **Validation Steps**:
   - Ensure all tests pass before removing old files
   - Verify no imports reference removed files
   - Check for any runtime dependencies
   - Validate documentation is updated
   - Run integration tests after each major change
   - Verify backward compatibility where needed

4. **Migration Strategy**:
   - Implement new functionality in `core/`
   - Update dependent modules to use new implementations
   - Add deprecation warnings to old implementations
   - Remove old implementations after grace period
   - Document all breaking changes

# Progress Updates

## 2024-02-14
- Current Status: Planning phase
- Completed:
  - Initial analysis
  - Requirements gathering
  - Architecture review
  - Additional structural improvements identified
  - Hub consolidation opportunities mapped
  - Added cleanup instructions for each requirement
  - Finalized implementation details
  - Enhanced test coverage
  - Added migration strategy
  - Added dependency mapping
  - Enhanced implementation strategy
  - Added validation checklist
- Next Steps:
  1. Implement standardized lifecycle
  2. Unify configuration system
  3. Consolidate capabilities
  4. Improve monitoring
  5. Integrate resources
  6. Consolidate workflows
  7. Reorganize hub 