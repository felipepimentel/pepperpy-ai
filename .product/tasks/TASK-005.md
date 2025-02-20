---
title: Codebase Restructuring and Alignment with Specification
priority: high
points: 13
status: 🏃 In Progress
mode: Act
created: 2024-02-19
updated: 2024-02-19
---

# Requirements

- [-] Requirement 1: Reorganize Core Module Structure  # 🏃 Started: 2024-02-19
  ## Current State
  The current `core/` module contains several components that should be at the root level according to the specification:
  - `core/workflows/` should be a root module
  - `core/hub/` should be a root module
  - `core/memory/` should be consolidated with root `memory/`
  - `core/metrics/` and `core/monitoring/` should be consolidated into root `monitoring/`
  - Core module should focus on fundamental and transversal functionalities

  ## Implementation Status
  ```python
  # Move core/workflows/ to root workflows/  # ✅ Complete
  mv pepperpy/core/workflows/* pepperpy/workflows/
  
  # Move core/hub/ to root hub/  # ✅ Complete
  mv pepperpy/core/hub/* pepperpy/hub/
  
  # Consolidate core/memory/ with root memory/  # ✅ Complete
  # Carefully merged while preserving functionality
  # - Implemented BaseMemoryStore interface
  # - Implemented InMemoryStore
  # - Implemented CompositeMemoryStore
  # - Updated memory factory
  # - Fixed all linter errors
  
  # Create monitoring/ at root and consolidate monitoring components  # ✅ Complete
  mkdir pepperpy/monitoring/
  mv pepperpy/core/metrics/* pepperpy/monitoring/metrics/
  mv pepperpy/core/monitoring/* pepperpy/monitoring/
  ```

  ## Validation Status
  ```python
  # Verify modules are in correct locations  # ✅ Complete
  assert hasattr(pepperpy, 'workflows')
  assert hasattr(pepperpy, 'hub')
  assert hasattr(pepperpy, 'monitoring')
  
  # Verify core module structure  # 🏃 In Progress
  from pepperpy.core import config, events, errors, types
  assert all(m is not None for m in [config, events, errors, types])
  
  # Verify no duplicated modules in core  # 🏃 In Progress
  from pepperpy.core import __all__
  assert 'workflows' not in __all__
  assert 'hub' not in __all__
  ```

- [ ] Requirement 2: Implement Missing Hub Components
  ## Current State
  Current `hub/` implementation is missing several key components defined in the specification:
  - Missing artifacts/ subdirectory with JSON schemas
  - Missing marketplace.py for artifact marketplace integration
  - Missing publishing.py for artifact publishing tools
  - Missing security.py for Hub security and validation
  - Missing proper storage abstraction

  ## Implementation
  1. Create complete Hub structure:
  ```python
  pepperpy/hub/
  ├── __init__.py
  ├── base.py             # HUB Protocol
  ├── manager.py          # HUB Manager
  ├── local.py            # Local HUB implementation
  ├── storage.py          # Storage abstraction
  ├── marketplace.py      # Marketplace integration
  ├── publishing.py       # Publishing tools
  ├── security.py         # Security & validation
  ├── types.py           # HUB data types
  └── artifacts/         # Schema definitions
      ├── __init__.py
      ├── agent_artifact.json
      ├── workflow_artifact.json
      ├── tool_artifact.json
      └── capability_artifact.json
  ```

  2. Implement Hub components with security focus:
  ```python
  # pepperpy/hub/security.py
  class HubSecurity:
      """Security manager for Hub artifacts with defense-in-depth approach."""
      def validate_signature(self, artifact: Artifact): ...
      def sandbox_execute(self, artifact: Artifact): ...
      def check_permissions(self, artifact: Artifact): ...
      def validate_schema(self, artifact: Artifact): ...
      def scan_code(self, artifact: Artifact): ...  # Static analysis
      
  # pepperpy/hub/storage.py
  class HubStorage(ABC):
      """Abstract storage backend for Hub."""
      @abstractmethod
      def save(self, artifact: Artifact): ...
      @abstractmethod
      def load(self, artifact_id: str): ...
      @abstractmethod
      def list(self, filter_criteria: Dict): ...
      @abstractmethod
      def delete(self, artifact_id: str): ...
  ```

  ## Validation
  ```python
  def test_hub_components():
      from pepperpy.hub import HubManager, HubSecurity, HubStorage
      
      # Test security features
      security = HubSecurity()
      assert security.validate_signature(signed_artifact)
      assert security.validate_schema(test_artifact)
      
      # Test storage abstraction
      storage = LocalHubStorage()
      artifact_id = storage.save(test_artifact)
      loaded = storage.load(artifact_id)
      assert loaded == test_artifact
  ```

- [ ] Requirement 3: Enhance CLI Module with Complete Command Set
  ## Current State
  CLI functionality is currently scattered and incomplete. Need to implement the CLI structure with all commands specified.

  ## Implementation
  1. Create complete CLI structure:
  ```python
  pepperpy/cli/
  ├── __init__.py
  ├── main.py              # CLI entry point
  ├── agent_commands.py    # Agent management
  ├── config_commands.py   # Configuration
  ├── hub_commands.py      # Hub/artifact
  ├── registry_commands.py # Registry
  ├── run_commands.py      # Execution
  ├── tool_commands.py     # Tool management
  ├── workflow_commands.py # Workflow
  ├── completion.py        # Shell completion
  ├── exceptions.py        # CLI exceptions
  └── utils.py            # CLI utilities
  ```

  2. Implement comprehensive command set:
  ```python
  # pepperpy/cli/hub_commands.py
  @click.group()
  def hub():
      """Manage PepperPy Hub artifacts."""
      
  @hub.command()
  def publish():
      """Publish an artifact to the Hub."""
      
  @hub.command()
  def install():
      """Install an artifact from the marketplace."""
      
  @hub.command()
  def list():
      """List available artifacts."""
      
  @hub.command()
  def inspect():
      """Inspect artifact details."""
  
  # Similar comprehensive command sets for other modules
  ```

  ## Validation
  ```python
  def test_cli_functionality():
      from pepperpy.cli.main import cli
      from click.testing import CliRunner
      
      runner = CliRunner()
      
      # Test hub commands
      result = runner.invoke(cli, ['hub', 'list'])
      assert result.exit_code == 0
      
      # Test workflow commands
      result = runner.invoke(cli, ['workflow', 'deploy', 'test.yaml'])
      assert result.exit_code == 0
  ```

- [ ] Requirement 4: Implement Complete Monitoring System
  ## Current State
  Current monitoring implementation needs to be enhanced with all observability features from specification.

  ## Implementation
  1. Create comprehensive monitoring structure:
  ```python
  pepperpy/monitoring/
  ├── __init__.py
  ├── metrics/           # Metrics subsystem
  │   ├── __init__.py
  │   ├── collectors.py
  │   ├── exporters.py
  │   └── types.py
  ├── tracing/          # Distributed tracing
  │   ├── __init__.py
  │   ├── providers.py
  │   └── context.py
  ├── health/           # Health checks
  │   ├── __init__.py
  │   ├── checks.py
  │   └── probes.py
  ├── logging/          # Advanced logging
  │   ├── __init__.py
  │   ├── handlers.py
  │   └── formatters.py
  └── dashboard/        # Monitoring UI
      ├── __init__.py
      └── templates/
  ```

  2. Implement monitoring with complete observability:
  ```python
  # pepperpy/monitoring/metrics/collectors.py
  class MetricsCollector:
      """Collects comprehensive metrics."""
      def collect_agent_metrics(self): ...
      def collect_workflow_metrics(self): ...
      def collect_memory_metrics(self): ...
      def collect_hub_metrics(self): ...
      def collect_system_metrics(self): ...

  # pepperpy/monitoring/health/checks.py
  class HealthChecker:
      """Comprehensive health checking."""
      def check_hub_health(self): ...
      def check_memory_stores(self): ...
      def check_providers(self): ...
      def check_system_resources(self): ...
  ```

  ## Validation
  ```python
  def test_monitoring_system():
      from pepperpy.monitoring import MetricsCollector, HealthChecker
      from pepperpy.monitoring.tracing import TracingManager
      
      # Test comprehensive metrics
      collector = MetricsCollector()
      metrics = collector.collect_system_metrics()
      assert all(key in metrics for key in [
          'agent_execution_time',
          'workflow_completion_rate',
          'memory_usage',
          'hub_artifact_count'
      ])
      
      # Test health checks
      checker = HealthChecker()
      status = checker.check_system_resources()
      assert status.is_healthy
      assert status.details['memory']['available'] > 0
  ```

- [ ] Requirement 5: Implement Event-Driven Architecture
  ## Current State
  Need to enhance the event system to fully support the asynchronous event-driven architecture specified.

  ## Implementation
  1. Create comprehensive event system:
  ```python
  pepperpy/core/events/
  ├── __init__.py
  ├── base.py
  ├── dispatcher.py
  ├── middleware.py
  ├── types.py
  └── handlers/
      ├── __init__.py
      ├── agent_events.py
      ├── workflow_events.py
      ├── memory_events.py
      └── hub_events.py
  ```

  2. Implement event system components:
  ```python
  # pepperpy/core/events/dispatcher.py
  class EventDispatcher:
      """Asynchronous event dispatcher."""
      async def dispatch(self, event: Event): ...
      async def subscribe(self, event_type: str, handler: Callable): ...
      def add_middleware(self, middleware: EventMiddleware): ...

  # pepperpy/core/events/middleware.py
  class EventMiddleware:
      """Event processing middleware."""
      async def process(self, event: Event, next_middleware: Callable): ...
      
  class AuditMiddleware(EventMiddleware):
      """Audits all events for security and monitoring."""
      
  class MetricsMiddleware(EventMiddleware):
      """Collects metrics about event processing."""
  ```

  ## Validation
  ```python
  def test_event_system():
      from pepperpy.core.events import EventDispatcher
      from pepperpy.core.events.middleware import AuditMiddleware
      
      dispatcher = EventDispatcher()
      dispatcher.add_middleware(AuditMiddleware())
      
      async def test():
          events_processed = []
          
          async def handler(event):
              events_processed.append(event)
              
          await dispatcher.subscribe("agent.started", handler)
          await dispatcher.dispatch(AgentStartedEvent())
          
          assert len(events_processed) == 1
          assert isinstance(events_processed[0], AgentStartedEvent)
  ```

- [ ] Requirement 6: Implement Zero Hardcoding and Provider Abstraction
  ## Current State
  Current codebase has hardcoded dependencies and provider-specific logic that needs to be abstracted.

  ## Implementation
  1. Create provider abstraction layer:
  ```python
  pepperpy/providers/
  ├── __init__.py
  ├── base.py             # Base provider interfaces
  ├── llm/                # LLM providers
  │   ├── base.py         # Base LLM interface
  │   ├── openai.py       # OpenAI implementation
  │   └── anthropic.py    # Anthropic implementation
  ├── storage/            # Storage providers
  │   ├── base.py         # Base storage interface
  │   ├── local.py        # Local storage
  │   └── cloud.py        # Cloud storage
  └── memory/             # Memory providers
      ├── base.py         # Base memory interface
      ├── redis.py        # Redis implementation
      └── postgres.py     # PostgreSQL implementation
  ```

  2. Implement provider registration:
  ```python
  # pepperpy/providers/base.py
  class ProviderRegistry:
      """Dynamic provider registration and management."""
      def register_provider(self, provider_type: str, provider: Type[Provider]): ...
      def get_provider(self, provider_type: str) -> Provider: ...
  ```

  ## Validation
  ```python
  def test_provider_abstraction():
      from pepperpy.providers import ProviderRegistry
      from pepperpy.providers.llm import OpenAIProvider
      
      registry = ProviderRegistry()
      registry.register_provider("llm", OpenAIProvider)
      provider = registry.get_provider("llm")
      assert isinstance(provider, OpenAIProvider)
  ```

- [ ] Requirement 7: Implement Layered Architecture and Extension Points
  ## Current State
  Need to establish clear layers and extension points for the architecture.

  ## Implementation
  1. Define architectural layers:
  ```python
  pepperpy/
  ├── core/              # Core Layer (Base)
  ├── providers/         # Provider Layer
  ├── capabilities/      # Capability Layer
  ├── agents/           # Agent Layer
  └── workflows/        # Workflow Layer
  ```

  2. Implement extension points:
  ```python
  # pepperpy/core/extensions.py
  class ExtensionPoint:
      """Base class for extension points."""
      def register_extension(self, extension: Extension): ...
      def get_extensions(self) -> List[Extension]: ...
  ```

  ## Validation
  ```python
  def test_extension_points():
      from pepperpy.core.extensions import ExtensionPoint
      
      extension_point = ExtensionPoint()
      extension_point.register_extension(CustomExtension())
      extensions = extension_point.get_extensions()
      assert len(extensions) > 0
  ```

- [ ] Requirement 8: Implement Adapter System for External Frameworks
  ## Current State
  Need to implement adapters for external frameworks as specified (Langchain, AutoGen, etc.).

  ## Implementation
  1. Create adapter module structure:
  ```python
  pepperpy/adapters/
  ├── __init__.py
  ├── base.py             # Base adapter interface
  ├── autogen.py          # Microsoft AutoGen adapter
  ├── crewai.py           # CrewAI adapter
  ├── langchain.py        # LangChain adapter
  └── semantic_kernel.py  # Microsoft Semantic Kernel adapter
  ```

  2. Implement base adapter interface:
  ```python
  # pepperpy/adapters/base.py
  class Adapter(ABC):
      """Base interface for framework adapters."""
      @abstractmethod
      def adapt_agent(self, agent: Agent) -> Any: ...
      
      @abstractmethod
      def adapt_workflow(self, workflow: Workflow) -> Any: ...
      
      @abstractmethod
      def adapt_tool(self, tool: Tool) -> Any: ...
  ```

  ## Validation
  ```python
  def test_adapters():
      from pepperpy.adapters.langchain import LangChainAdapter
      from pepperpy.agents import Agent
      
      adapter = LangChainAdapter()
      agent = Agent(name="test_agent")
      langchain_agent = adapter.adapt_agent(agent)
      assert langchain_agent is not None
  ```

- [ ] Requirement 9: Implement Content and Synthesis Modules
  ## Current State
  Missing implementation of content processing and multimodal synthesis capabilities.

  ## Implementation
  1. Create content module structure:
  ```python
  pepperpy/content/
  ├── __init__.py
  ├── base.py             # Base content processor
  ├── processors/         # Content processors
  │   ├── text.py         # Text processor
  │   ├── email.py        # Email processor
  │   └── web.py          # Web content processor
  └── providers/          # Content providers
      ├── news.py         # News API provider
      └── rss.py          # RSS feed provider
  ```

  2. Create synthesis module structure:
  ```python
  pepperpy/synthesis/
  ├── __init__.py
  ├── base.py             # Base synthesis interface
  ├── processors/         # Synthesis processors
  │   ├── tts.py          # Text-to-speech
  │   └── image.py        # Image generation
  └── providers/          # Synthesis providers
      ├── elevenlabs.py   # ElevenLabs TTS
      └── dalle.py        # DALL-E image gen
  ```

  ## Validation
  ```python
  def test_content_synthesis():
      from pepperpy.content.processors import WebProcessor
      from pepperpy.synthesis.processors import TTSProcessor
      
      # Test content processing
      web = WebProcessor()
      content = web.process("https://example.com")
      assert content.text is not None
      
      # Test synthesis
      tts = TTSProcessor()
      audio = tts.synthesize("Hello World")
      assert audio is not None
  ```

- [ ] Requirement 10: Enhance CLI with Complete Command Set
  ## Current State
  CLI needs comprehensive command set as specified in documentation.

  ## Implementation
  1. Implement complete CLI structure:
  ```python
  pepperpy/cli/
  ├── __init__.py
  ├── cli.py               # Main entry point
  ├── commands/            # Command modules
  │   ├── agent.py         # Agent commands
  │   │   ├── create.py    # pepperpy agent create
  │   │   ├── list.py      # pepperpy agent list
  │   │   └── run.py       # pepperpy agent run
  │   ├── workflow.py      # Workflow commands
  │   │   ├── deploy.py    # pepperpy workflow deploy
  │   │   ├── list.py      # pepperpy workflow list
  │   │   └── monitor.py   # pepperpy workflow monitor
  │   ├── hub.py           # Hub commands
  │   │   ├── publish.py   # pepperpy hub publish
  │   │   ├── install.py   # pepperpy hub install
  │   │   └── list.py      # pepperpy hub list
  │   └── config.py        # Config commands
  ├── utils/               # CLI utilities
  │   ├── formatting.py    # Output formatting
  │   └── validation.py    # Input validation
  └── completion/          # Shell completion
      ├── bash.py          # Bash completion
      └── zsh.py           # Zsh completion
  ```

  2. Example command implementation:
  ```python
  # pepperpy/cli/commands/workflow/deploy.py
  @click.command()
  @click.argument('workflow_path')
  @click.option('--env', '-e', help='Environment to deploy to')
  def deploy(workflow_path: str, env: str):
      """Deploy a workflow to the specified environment."""
      click.echo(f"Deploying workflow from {workflow_path} to {env}")
      # Implementation...
  ```

  ## Validation
  ```python
  def test_cli_commands():
      from click.testing import CliRunner
      from pepperpy.cli.cli import cli
      
      runner = CliRunner()
      
      # Test workflow deploy
      result = runner.invoke(cli, ['workflow', 'deploy', 'test.yaml', '-e', 'dev'])
      assert result.exit_code == 0
      
      # Test hub list
      result = runner.invoke(cli, ['hub', 'list', 'agents'])
      assert result.exit_code == 0
  ```

- [ ] Requirement 11: Implement Complete Documentation and Test Structure
  ## Current State
  Documentation and test coverage needs to be enhanced according to specification.

  ## Implementation
  1. Create complete documentation structure:
  ```
  docs/                       # Complete project documentation
  ├── source/               # Documentation source files
  │   ├── architecture/    # Architecture documentation
  │   │   ├── core.rst     # Core module architecture
  │   │   ├── hub.rst      # Hub architecture
  │   │   └── events.rst   # Event system architecture
  │   ├── api/            # API documentation
  │   │   ├── agents.rst   # Agents API
  │   │   ├── workflows.rst # Workflows API
  │   │   └── hub.rst      # Hub API
  │   ├── guides/         # User guides
  │   │   ├── quickstart.rst # Quick start guide
  │   │   ├── agents.rst    # Agent development guide
  │   │   └── workflows.rst # Workflow development guide
  │   └── examples/       # Example documentation
  ├── build/              # Documentation build output
  └── make.py            # Documentation build script
  ```

  2. Implement comprehensive test structure:
  ```python
  tests/                      # Root level tests
  ├── unit/                 # Unit tests
  │   ├── core/            # Core module tests
  │   ├── agents/          # Agents tests
  │   ├── workflows/       # Workflows tests
  │   └── hub/             # Hub tests
  ├── integration/         # Integration tests
  │   ├── agent_workflow/  # Agent-workflow integration
  │   ├── hub_security/    # Hub security integration
  │   └── monitoring/      # Monitoring integration
  ├── e2e/                # End-to-end tests
  │   ├── scenarios/      # Test scenarios
  │   └── fixtures/       # Test fixtures
  └── conftest.py         # Test configuration
  ```

  ## Validation
  ```python
  def test_documentation_build():
      from docs.make import build_docs
      assert build_docs() == 0  # Build successful
      
  def test_coverage():
      import pytest
      import coverage
      
      cov = coverage.Coverage()
      cov.start()
      pytest.main(['tests'])
      cov.stop()
      
      coverage_report = cov.report()
      assert coverage_report >= 80  # Minimum 80% coverage
  ```

- [ ] Requirement 12: Implement Project Utility Scripts
  ## Current State
  Need to implement utility scripts specified for project management and automation.

  ## Implementation
  1. Create scripts structure:
  ```
  scripts/                    # Project utility scripts
  ├── setup.py              # Development environment setup
  ├── check.sh             # Code quality checks
  ├── clean.sh             # Clean temporary files
  ├── validate_structure.py # Directory structure validation
  ├── update_imports.py    # Import statement updates
  ├── build_docs.sh        # Documentation build automation
  ├── run_tests.sh         # Test execution automation
  └── publish_hub_artifact.py # Hub artifact publishing
  ```

  2. Example script implementation:
  ```python
  # scripts/validate_structure.py
  def validate_project_structure():
      """Validates project structure against specification."""
      required_dirs = [
          'pepperpy/core',
          'pepperpy/agents',
          'pepperpy/workflows',
          'pepperpy/hub',
          'docs/source',
          'tests/unit',
          'tests/integration'
      ]
      
      for dir_path in required_dirs:
          assert os.path.isdir(dir_path), f"Missing required directory: {dir_path}"
          
  # scripts/check.sh
  #!/bin/bash
  echo "Running code quality checks..."
  
  # Run linters
  flake8 pepperpy/
  pylint pepperpy/
  mypy pepperpy/
  
  # Run formatters
  black pepperpy/
  isort pepperpy/
  ```

  ## Validation
  ```python
  def test_utility_scripts():
      from scripts.validate_structure import validate_project_structure
      
      # Test structure validation
      try:
          validate_project_structure()
          structure_valid = True
      except AssertionError:
          structure_valid = False
      
      assert structure_valid, "Project structure validation failed"
      
      # Test check script
      import subprocess
      result = subprocess.run(['./scripts/check.sh'], capture_output=True)
      assert result.returncode == 0, "Code quality checks failed"
  ```

# Progress Updates

## 2024-02-19
- Current Status: Consolidating core module structure
- Completed:
  - Moved core/workflows/ to root workflows/ ✅
  - Moved core/hub/ to root hub/ ✅
  - Created monitoring/ at root and consolidated monitoring components ✅
  - Consolidated core/memory/ with root memory/ ✅
    - Implemented BaseMemoryStore interface
    - Implemented InMemoryStore
    - Implemented CompositeMemoryStore
    - Updated memory factory
    - Fixed all linter errors
- In Progress:
  - Reorganizing remaining core module structure 🏃
    - Moving core/events/ to root events/
    - Moving core/config/ to root config/
    - Moving core/types/ to root types/
    - Moving core/protocols/ to root protocols/
- Next Steps:
  1. Complete core module reorganization
  2. Implement comprehensive event system
  3. Implement Hub components with security focus