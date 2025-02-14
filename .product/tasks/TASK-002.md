---
title: Code Organization and Structure Improvements
priority: high
points: 8
status: 📋 To Do
mode: Plan
created: 2024-02-14
updated: 2024-02-14
---

# Requirements

- [ ] Flatten capabilities structure
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

- [ ] Unificar sistema de configuração
  ## Current State
  ```python
  # core/config.py tem múltiplas classes de configuração
  # AutoConfig e PepperpyConfig com sobreposição
  # Configuração espalhada em vários módulos

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
      """Gerenciador unificado de configuração."""
      def __init__(self, config_class: Type[T]):
          self.config_class = config_class
          self._config: Optional[T] = None
          self._watchers: Set[ConfigWatcher] = set()

      async def load(self, sources: List[ConfigSource]) -> T:
          """Carrega configuração de múltiplas fontes."""
          config_data = {}
          for source in sources:
              data = await source.load()
              config_data.update(data)
          
          self._config = self.config_class(**config_data)
          await self._notify_watchers()
          return self._config

  # core/config/sources.py
  class ConfigSource(Protocol):
      """Fonte de configuração."""
      async def load(self) -> Dict[str, Any]:
          pass

  class EnvSource(ConfigSource):
      """Configuração via variáveis de ambiente."""
      def __init__(self, prefix: str = "PEPPERPY_"):
          self.prefix = prefix

      async def load(self) -> Dict[str, Any]:
          return {k[len(self.prefix):].lower(): v 
                 for k, v in os.environ.items() 
                 if k.startswith(self.prefix)}

  # core/config/watchers.py
  class ConfigWatcher(Protocol):
      """Observador de mudanças na configuração."""
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

- [ ] Melhorar sistema de monitoramento
  ## Current State
  ```python
  # monitoring/monitoring.py mistura logging e métricas
  # Configuração de logging espalhada
  # Falta estrutura para tracing

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
      """Fábrica centralizada de loggers."""
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
      """Gerenciador central de métricas."""
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
      """Gerenciador central de tracing."""
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

- [ ] Padronizar ciclo de vida dos componentes
  ## Current State
  ```python
  # Diferentes padrões de inicialização
  # Falta consistência no cleanup
  # Gestão manual de recursos

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
  from typing import Optional, Any
  from enum import Enum

  class ComponentState(Enum):
      CREATED = "created"
      INITIALIZING = "initializing"
      READY = "ready"
      ERROR = "error"
      SHUTTING_DOWN = "shutting_down"
      TERMINATED = "terminated"

  class Lifecycle(ABC):
      """Interface base para componentes com ciclo de vida."""
      def __init__(self):
          self._state = ComponentState.CREATED
          self._error: Optional[Exception] = None
          self._metadata: Dict[str, Any] = {}

      @property
      def state(self) -> ComponentState:
          return self._state

      @abstractmethod
      async def initialize(self) -> None:
          """Inicializa o componente."""
          pass

      @abstractmethod
      async def cleanup(self) -> None:
          """Limpa recursos do componente."""
          pass

  class LifecycleManager:
      """Gerenciador central de ciclo de vida."""
      def __init__(self):
          self._components: Dict[str, Lifecycle] = {}

      async def register(self, name: str, component: Lifecycle) -> None:
          self._components[name] = component
          await component.initialize()

      async def shutdown(self) -> None:
          """Desliga todos os componentes em ordem reversa."""
          for name in reversed(list(self._components)):
              component = self._components[name]
              try:
                  await component.cleanup()
              except Exception as e:
                  logger.error(f"Error shutting down {name}: {e}")
  ```

  ## Validation
  ```python
  async def test_lifecycle():
      # Test component lifecycle
      component = TestComponent()
      assert component.state == ComponentState.CREATED
      
      await component.initialize()
      assert component.state == ComponentState.READY
      
      await component.cleanup()
      assert component.state == ComponentState.TERMINATED

      # Test lifecycle manager
      manager = LifecycleManager()
      await manager.register("test", component)
      assert "test" in manager._components
      
      await manager.shutdown()
      assert all(c.state == ComponentState.TERMINATED 
                for c in manager._components.values())
  ```

# Progress Updates

## 2024-02-14
- Current Status: Planning phase
- Completed:
  - Initial analysis
  - Requirements gathering
  - Architecture review
  - Additional structural improvements identified
- Next Steps:
  1. Start dependency analysis (TASK-002.1)
  2. Setup test environment (TASK-002.2)
  3. Begin capabilities restructure
  4. Implement unified configuration system
  5. Enhance monitoring infrastructure
  6. Standardize component lifecycles 