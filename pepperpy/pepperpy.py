"""
PepperPy Framework Core.

Framework declarativo para construção de agentes e processamento de texto,
com uma API fluida, orientada a domínio e baseada em tarefas.
"""

import asyncio
import os
import re
from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import (
    Any,
    Protocol,
    TypeVar,
    runtime_checkable,
)

# Versão do framework
__version__ = "0.3.0"


# Core enums
class DependencyType(str, Enum):
    """Tipos de dependências entre plugins."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    CONFLICTS = "conflicts"


class EventPriority(int, Enum):
    """Prioridades para eventos."""

    HIGHEST = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    LOWEST = 0


class ServiceScope(str, Enum):
    """Escopo de visibilidade para serviços."""

    PUBLIC = "public"
    PRIVATE = "private"
    LIMITED = "limited"


class ResourceType(str, Enum):
    """Tipos de recursos."""

    MEMORY = "memory"
    PERSISTENT = "persistent"
    SHARED = "shared"


class AgentCapability(str, Enum):
    """Capacidades dos agentes."""

    TEXT_PROCESSING = "text_processing"
    CODE_ANALYSIS = "code_analysis"
    REPOSITORY_NAVIGATION = "repository_navigation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    DOCUMENT_ANALYSIS = "document_analysis"
    QA = "question_answering"
    ARCHITECTURE = "architecture_analysis"
    REFACTORING = "refactoring"
    TESTING = "testing"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"


class TaskType(str, Enum):
    """Tipos de tarefas para agentes."""

    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    INDEX = "index"
    SEARCH = "search"
    GENERATE = "generate"
    EXTRACT = "extract"
    CONVERT = "convert"
    COMPARE = "compare"
    REFACTOR = "refactor"
    TEST = "test"
    AUDIT = "audit"
    OPTIMIZE = "optimize"


class AnalysisType(str, Enum):
    """Tipos de análise para repositórios."""

    ARCHITECTURE = "architecture"
    DEPENDENCIES = "dependencies"
    COMPLEXITY = "complexity"
    PATTERNS = "patterns"
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    DOCUMENTATION = "documentation"
    TESTS = "tests"


class AnalysisScope(str, Enum):
    """Escopo da análise."""

    FILE = "file"
    MODULE = "module"
    PACKAGE = "package"
    REPOSITORY = "repository"


class AnalysisLevel(int, Enum):
    """Nível de detalhe da análise."""

    BASIC = 1
    STANDARD = 2
    DETAILED = 3
    COMPREHENSIVE = 4


# Type variables for generics
T = TypeVar("T")
P = TypeVar("P", bound="Plugin")
R = TypeVar("R")
TResult = TypeVar("TResult")
TEvent = TypeVar("TEvent", bound="Event")


# Sistema de eventos e handlers
_event_handlers: dict[str, list[dict[str, Any]]] = defaultdict(list)
_analysis_hooks: dict[str, list[Callable[..., Any]]] = defaultdict(list)
_task_hooks: dict[TaskType, list[Callable[..., Any]]] = defaultdict(list)
_plugin_registry: dict[str, dict[str, Any]] = defaultdict(dict)


# Decoradores expressivos para DSL


def repository_task(
    capabilities: list[AgentCapability] | None = None,
    requires: list[str] | None = None,
    scope: AnalysisScope = AnalysisScope.REPOSITORY,
    level: AnalysisLevel = AnalysisLevel.STANDARD,
):
    """Decorador para definir uma tarefa de análise de repositório.

    Args:
        capabilities: Capacidades necessárias para executar a tarefa
        requires: Plugins ou recursos necessários
        scope: Escopo da análise (arquivo, módulo, pacote, repositório)
        level: Nível de detalhe da análise

    Returns:
        Decorador configurado
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(repo, *args, **kwargs):
            # Registro para rastreamento
            task_name = func.__name__
            task_doc = func.__doc__ or "Repository task"

            # Iniciar rastreamento
            _start_task_tracking(task_name, task_doc, scope, level)

            # Verificar requisitos
            if requires:
                for req in requires:
                    if not await _check_requirement(repo, req):
                        raise ValueError(f"Requisito não atendido: {req}")

            # Executar hooks pré-tarefa
            await _run_pre_task_hooks(repo, task_name, scope, level)

            # Executar a tarefa
            result = await func(repo, *args, **kwargs)

            # Executar hooks pós-tarefa
            await _run_post_task_hooks(repo, task_name, result, scope, level)

            # Finalizar rastreamento
            _end_task_tracking(task_name, scope, level)

            return result

        # Metadados para introspection
        wrapper._is_repository_task = True
        wrapper._task_capabilities = capabilities or []
        wrapper._task_requires = requires or []
        wrapper._task_scope = scope
        wrapper._task_level = level

        return wrapper

    return decorator


def code_analysis(
    language: str | None = None,
    patterns: list[str] | None = None,
    metrics: list[str] | None = None,
):
    """Decorador para análise específica de código.

    Args:
        language: Linguagem para análise específica
        patterns: Padrões a serem buscados
        metrics: Métricas a serem coletadas

    Returns:
        Decorador configurado
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(target, *args, **kwargs):
            # Metadados para logging
            analysis_name = func.__name__
            analysis_doc = func.__doc__ or "Code analysis"

            # Iniciar rastreamento
            _start_analysis_tracking(analysis_name, language, patterns, metrics)

            # Executar hooks pré-análise
            await _run_pre_analysis_hooks(target, analysis_name, language)

            # Executar a análise
            result = await func(target, *args, **kwargs)

            # Executar hooks pós-análise
            await _run_post_analysis_hooks(target, analysis_name, result, language)

            # Finalizar rastreamento
            _end_analysis_tracking(analysis_name, language)

            return result

        # Metadados para introspection
        wrapper._is_code_analysis = True
        wrapper._analysis_language = language
        wrapper._analysis_patterns = patterns or []
        wrapper._analysis_metrics = metrics or []

        return wrapper

    return decorator


def on_analysis_complete(analysis_type: str | None = None):
    """Decorador para registrar handler para conclusão de análise.

    Args:
        analysis_type: Tipo específico de análise ou None para todas

    Returns:
        Decorador configurado
    """

    def decorator(func):
        # Registrar o handler para o tipo de análise
        analysis_key = analysis_type or "all"
        _analysis_hooks[analysis_key].append(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Metadados
        wrapper._is_analysis_handler = True
        wrapper._analysis_type = analysis_type

        return wrapper

    return decorator


def on_task_complete(task_type: TaskType | None = None):
    """Decorador para registrar handler para conclusão de tarefa.

    Args:
        task_type: Tipo específico de tarefa ou None para todas

    Returns:
        Decorador configurado
    """

    def decorator(func):
        # Registrar o handler para o tipo de tarefa
        task_key = task_type or "all"
        if isinstance(task_key, TaskType):
            _task_hooks[task_key].append(func)
        else:
            _task_hooks[task_key].append(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        # Metadados
        wrapper._is_task_handler = True
        wrapper._task_type = task_type

        return wrapper

    return decorator


# Funções auxiliares para o sistema de handlers


async def _run_pre_task_hooks(repo, task_name, scope, level):
    """Executar hooks antes da tarefa."""
    # Implementação real aqui
    pass


async def _run_post_task_hooks(repo, task_name, result, scope, level):
    """Executar hooks após tarefa."""
    # Executar handlers genéricos
    for handler in _task_hooks.get("all", []):
        try:
            await handler(repo, task_name, result, scope=scope, level=level)
        except Exception as e:
            # Log error but continue
            print(f"Erro no handler pós-tarefa: {e}")

    # Executar handlers específicos para o tipo de tarefa
    for task_type, handlers in _task_hooks.items():
        if task_type != "all" and task_name.startswith(task_type.value):
            for handler in handlers:
                try:
                    await handler(repo, task_name, result, scope=scope, level=level)
                except Exception as e:
                    # Log error but continue
                    print(f"Erro no handler específico {task_type}: {e}")


def _start_task_tracking(task_name, task_doc, scope, level):
    """Iniciar rastreamento de tarefa."""
    # Implementação real aqui
    pass


def _end_task_tracking(task_name, scope, level):
    """Finalizar rastreamento de tarefa."""
    # Implementação real aqui
    pass


async def _check_requirement(repo, requirement):
    """Verificar se um requisito é atendido."""
    # Implementação real aqui
    return True


async def _run_pre_analysis_hooks(target, analysis_name, language):
    """Executar hooks antes da análise."""
    # Implementação real aqui
    pass


async def _run_post_analysis_hooks(target, analysis_name, result, language):
    """Executar hooks após análise."""
    # Executar handlers genéricos
    for handler in _analysis_hooks.get("all", []):
        try:
            await handler(target, analysis_name, result, language=language)
        except Exception as e:
            # Log error but continue
            print(f"Erro no handler pós-análise: {e}")

    # Executar handlers específicos
    for analysis_type, handlers in _analysis_hooks.items():
        if analysis_type != "all" and analysis_name.startswith(analysis_type):
            for handler in handlers:
                try:
                    await handler(target, analysis_name, result, language=language)
                except Exception as e:
                    # Log error but continue
                    print(f"Erro no handler específico {analysis_type}: {e}")


def _start_analysis_tracking(analysis_name, language, patterns, metrics):
    """Iniciar rastreamento de análise."""
    # Implementação real aqui
    pass


def _end_analysis_tracking(analysis_name, language):
    """Finalizar rastreamento de análise."""
    # Implementação real aqui
    pass


# Classe base para eventos
class Event:
    """Classe base para eventos no framework."""

    def __init__(self, event_type: str, data: Any = None):
        self.event_type = event_type
        self.data = data
        self.cancelled = False
        self.results: list[Any] = []

    def cancel(self) -> None:
        """Cancelar processamento do evento."""
        self.cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Verificar se evento está cancelado."""
        return self.cancelled

    def add_result(self, result: Any) -> None:
        """Adicionar resultado ao evento."""
        self.results.append(result)

    def get_results(self) -> list[Any]:
        """Obter resultados do evento."""
        return self.results.copy()


# Classes específicas de eventos
class AnalysisStartEvent(Event):
    """Evento disparado ao iniciar uma análise."""

    def __init__(self, analysis_type: str, target: Any, options: dict[str, Any] = None):
        super().__init__(
            "analysis.start",
            {
                "analysis_type": analysis_type,
                "target": target,
                "options": options or {},
            },
        )


class AnalysisCompleteEvent(Event):
    """Evento disparado ao concluir uma análise."""

    def __init__(self, analysis_type: str, target: Any, result: Any):
        super().__init__(
            "analysis.complete",
            {"analysis_type": analysis_type, "target": target, "result": result},
        )


class RepositoryActionEvent(Event):
    """Evento para ações em repositório."""

    def __init__(self, action: str, repository: Any, details: dict[str, Any] = None):
        super().__init__(
            f"repository.{action}", {"repository": repository, "details": details or {}}
        )


# Sistema de publicação de eventos
async def publish_event(event: Event) -> Event:
    """Publicar um evento para os handlers registrados.

    Args:
        event: Evento a ser publicado

    Returns:
        O evento processado com resultados
    """
    # Obter handlers para este tipo de evento
    handlers = _event_handlers.get(event.event_type, [])

    # Ordenar por prioridade
    handlers.sort(key=lambda h: h.get("priority", EventPriority.NORMAL), reverse=True)

    # Processar o evento
    for handler_info in handlers:
        if event.is_cancelled:
            break

        handler = handler_info.get("handler")
        priority = handler_info.get("priority", EventPriority.NORMAL)

        if handler:
            try:
                # Chamar o handler
                result = handler(event)

                # Se for corotina, aguardar resultado
                if asyncio.iscoroutine(result):
                    result = await result

                # Adicionar resultado se não for None
                if result is not None:
                    event.add_result(result)
            except Exception as e:
                # Logar erro, mas continuar processamento
                print(f"Erro no handler de evento {event.event_type}: {e}")

    return event


# Registrar um handler para eventos
def register_event_handler(
    event_type: str,
    handler: Callable[[Event], Any],
    priority: EventPriority = EventPriority.NORMAL,
) -> None:
    """Registrar um handler para eventos.

    Args:
        event_type: Tipo de evento
        handler: Função de handler
        priority: Prioridade do handler
    """
    _event_handlers[event_type].append({"handler": handler, "priority": priority})


# Decorador para eventos
def event_handler(event_type: str, priority: EventPriority = EventPriority.NORMAL):
    """Decorador para registrar handlers de eventos.

    Args:
        event_type: Tipo de evento
        priority: Prioridade do handler

    Returns:
        Decorador configurado
    """

    def decorator(func):
        # Registrar o handler
        register_event_handler(event_type, func, priority)

        @wraps(func)
        async def wrapper(event: Event):
            return await func(event)

        # Metadados
        wrapper._is_event_handler = True
        wrapper._event_type = event_type
        wrapper._event_priority = priority

        return wrapper

    return decorator


# ---------- PROTOCOLS ----------


@runtime_checkable
class Initializable(Protocol):
    """Protocol for objects that can be initialized."""

    async def initialize(self) -> None:
        """Initialize the object."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...


@runtime_checkable
class TextProcessor(Protocol):
    """Protocol for text processors."""

    async def process(self, text: str, **options: Any) -> str:
        """Process text."""
        ...


@runtime_checkable
class Agent(Protocol):
    """Protocol for agent implementations."""

    async def execute(self, task: "Task") -> Any:
        """Execute a task."""
        ...

    async def ask(self, question: str, **context: Any) -> str:
        """Ask the agent a question."""
        ...


@runtime_checkable
class Repository(Protocol):
    """Protocol for repository interfaces."""

    async def index_files(
        self, files: list[str | Path], **options: Any
    ) -> "IndexResult":
        """Index repository files."""
        ...

    async def analyze(self) -> "RepositoryAnalysis":
        """Analyze repository."""
        ...


# ---------- RESULT CLASSES ----------


class Result:
    """Base class for operation results."""

    def __init__(self, **data: Any):
        """Initialize with result data."""
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    async def save(self, path: str | Path, format: str = "txt") -> Path:
        """Save result to file."""
        path = Path(path)
        os.makedirs(path.parent, exist_ok=True)

        # Determine content based on format
        if format == "txt":
            content = self.to_text()
        elif format == "md" or format == "markdown":
            content = self.to_markdown()
        elif format == "json":
            import json

            content = json.dumps(self.to_dict(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Write to file
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    def to_text(self) -> str:
        """Convert result to text format."""
        lines = ["Result:"]
        for key, value in self._data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Convert result to markdown format."""
        lines = ["# Result"]
        for key, value in self._data.items():
            lines.append(f"## {key.replace('_', ' ').title()}")
            lines.append(f"{value}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return dict(self._data)

    async def export(
        self, format: str = "md", path: str | Path | None = None
    ) -> str | Path:
        """Export result to specified format."""
        if path:
            return await self.save(path, format)

        if format in ("txt", "md", "markdown"):
            return (
                self.to_markdown()
                if format == "md" or format == "markdown"
                else self.to_text()
            )
        elif format == "json":
            import json

            return json.dumps(self.to_dict(), indent=2)
        elif format == "dict":
            return self.to_dict()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def __repr__(self) -> str:
        """String representation."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"{self.__class__.__name__}({attrs})"


class TextResult(Result):
    """Result of text processing operations."""

    @property
    def text(self) -> str:
        """Get processed text."""
        return self._data.get("text", "")


class IndexResult(Result):
    """Result of indexing operations."""

    @property
    def indexed_files(self) -> list[str]:
        """Get list of indexed files."""
        return self._data.get("indexed_files", [])

    @property
    def failed_files(self) -> list[tuple[str, str]]:
        """Get list of files that failed to index with reasons."""
        return self._data.get("failed_files", [])


class RepositoryAnalysis(Result):
    """Result of repository analysis."""

    def __init__(self, repository: "Repository", **data: Any):
        """Initialize with repository and data."""
        super().__init__(**data)
        self._repository = repository

    async def summarize(self) -> str:
        """Generate repository summary."""
        if "summary" in self._data:
            return self._data["summary"]

        # Generate summary if not available
        summary = await self._repository.ask("Summarize this repository")
        self._data["summary"] = summary
        return summary

    async def describe_architecture(self) -> str:
        """Describe repository architecture."""
        if "architecture" in self._data:
            return self._data["architecture"]

        # Generate architecture description if not available
        arch = await self._repository.ask(
            "Describe the architecture of this repository"
        )
        self._data["architecture"] = arch
        return arch

    async def list_dependencies(self) -> list[str]:
        """List repository dependencies."""
        if "dependencies" in self._data:
            return self._data["dependencies"]

        # Find dependencies if not available
        deps = await self._repository.ask("List all dependencies in this repository")
        deps_list = [d.strip() for d in deps.split("\n") if d.strip()]
        self._data["dependencies"] = deps_list
        return deps_list

    async def generate_report(self) -> "Report":
        """Generate comprehensive repository report."""
        # Ensure we have all the data
        summary = await self.summarize()
        architecture = await self.describe_architecture()
        dependencies = await self.list_dependencies()

        # Create report
        return Report(
            title=f"Analysis of {self._repository}",
            sections=[
                {"title": "Summary", "content": summary},
                {"title": "Architecture", "content": architecture},
                {
                    "title": "Dependencies",
                    "content": "\n".join(f"- {d}" for d in dependencies),
                },
            ],
        )


class Report(Result):
    """Formatted report with sections."""

    def __init__(self, title: str, sections: list[dict[str, str]]):
        """Initialize report with title and sections."""
        super().__init__(title=title, sections=sections)

    def to_markdown(self) -> str:
        """Convert report to markdown format."""
        lines = [f"# {self._data['title']}", ""]

        for section in self._data["sections"]:
            lines.append(f"## {section['title']}")
            lines.append("")
            lines.append(section["content"])
            lines.append("")

        return "\n".join(lines)

    def to_text(self) -> str:
        """Convert report to text format."""
        lines = [f"{self._data['title']}", "=" * len(self._data["title"]), ""]

        for section in self._data["sections"]:
            lines.append(f"{section['title']}")
            lines.append("-" * len(section["title"]))
            lines.append("")
            lines.append(section["content"])
            lines.append("")

        return "\n".join(lines)


# ---------- BASE CLASSES ----------


class Plugin:
    """Base class for all plugins."""

    def __init__(self, **config: Any):
        """Initialize plugin with configuration."""
        self.plugin_id = self.__class__.__name__
        self.config = config

        # Map config directly to attributes for easier access
        for key, value in config.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    async def initialize(self) -> None:
        """Initialize plugin resources."""
        pass

    async def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(plugin_id={self.plugin_id})"


class ProviderPlugin(Plugin):
    """Base class for provider plugins."""

    provider_type: str = ""


class Task:
    """Task to be executed by an agent."""

    def __init__(
        self, type: TaskType, target: Any, parameters: dict[str, Any] | None = None
    ):
        """Initialize task with type, target and parameters."""
        self.type = type
        self.target = target
        self.parameters = parameters or {}

    @classmethod
    def analyze(cls, target: Any, **params: Any) -> "Task":
        """Create analysis task."""
        return cls(TaskType.ANALYZE, target, params)

    @classmethod
    def summarize(cls, target: Any, **params: Any) -> "Task":
        """Create summarization task."""
        return cls(TaskType.SUMMARIZE, target, params)

    @classmethod
    def translate(cls, target: Any, to_language: str, **params: Any) -> "Task":
        """Create translation task."""
        params["to_language"] = to_language
        return cls(TaskType.TRANSLATE, target, params)

    @classmethod
    def index(cls, target: Any, **params: Any) -> "Task":
        """Create indexing task."""
        return cls(TaskType.INDEX, target, params)

    @classmethod
    def search(cls, target: Any, query: str, **params: Any) -> "Task":
        """Create search task."""
        params["query"] = query
        return cls(TaskType.SEARCH, target, params)

    @classmethod
    def generate(cls, target: Any, **params: Any) -> "Task":
        """Create generation task."""
        return cls(TaskType.GENERATE, target, params)

    @classmethod
    def extract(cls, target: Any, what: str, **params: Any) -> "Task":
        """Create extraction task."""
        params["what"] = what
        return cls(TaskType.EXTRACT, target, params)

    @classmethod
    def convert(cls, target: Any, to_format: str, **params: Any) -> "Task":
        """Create conversion task."""
        params["to_format"] = to_format
        return cls(TaskType.CONVERT, target, params)

    def __repr__(self) -> str:
        """String representation."""
        return f"Task(type={self.type}, target={self.target})"


# ---------- MAIN IMPLEMENTATIONS ----------


class AgentImpl(Plugin):
    """Agent implementation that can execute tasks."""

    def __init__(
        self, capabilities: list[AgentCapability] | None = None, **config: Any
    ):
        """Initialize agent with capabilities and config."""
        super().__init__(**config)
        self.capabilities = capabilities or []
        self._initialized = False
        self._pepper = None

    async def __aenter__(self) -> "AgentImpl":
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize agent."""
        if self._initialized:
            return

        # Initialize PepperPy core if needed
        if not self._pepper:
            self._pepper = PepperPy()
            await self._pepper.initialize()

        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        if not self._initialized:
            return

        if self._pepper:
            await self._pepper.cleanup()

        self._initialized = False

    async def execute(self, task: Task) -> Any:
        """Execute a task."""
        await self.initialize()

        # Map task to appropriate handler
        if task.type == TaskType.ANALYZE:
            return await self._analyze(task.target, **task.parameters)
        elif task.type == TaskType.SUMMARIZE:
            return await self._summarize(task.target, **task.parameters)
        elif task.type == TaskType.TRANSLATE:
            return await self._translate(task.target, **task.parameters)
        elif task.type == TaskType.INDEX:
            return await self._index(task.target, **task.parameters)
        elif task.type == TaskType.SEARCH:
            return await self._search(task.target, **task.parameters)
        elif task.type == TaskType.GENERATE:
            return await self._generate(task.target, **task.parameters)
        elif task.type == TaskType.EXTRACT:
            return await self._extract(task.target, **task.parameters)
        elif task.type == TaskType.CONVERT:
            return await self._convert(task.target, **task.parameters)
        else:
            raise ValueError(f"Unsupported task type: {task.type}")

    async def ask(self, question: str, **context: Any) -> str:
        """Ask the agent a question."""
        await self.initialize()

        # Execute the query
        result = await self._pepper.execute(query=question, context=context)
        return result

    # Task handler implementations
    async def _analyze(self, target: Any, **params: Any) -> Any:
        """Analyze a target."""
        # For repositories, delegate to repository analysis
        if isinstance(target, GitRepository):
            return await target.analyze()

        # For text, perform analysis
        if isinstance(target, str):
            # Basic text analysis
            query = f"Analyze the following text: {target[:1000]}..."
            return await self.ask(query)

        # For other types, return generic analysis
        return Result(
            type="analysis", target=str(target), analysis=f"Analysis of {target}"
        )

    async def _summarize(self, target: Any, **params: Any) -> str:
        """Summarize a target."""
        if isinstance(target, str):
            max_length = params.get("max_length", 200)
            query = f"Summarize the following text in {max_length} words or less: {target[:2000]}..."
            return await self.ask(query)

        return f"Summary of {target}"

    async def _translate(self, target: Any, **params: Any) -> str:
        """Translate a target."""
        if isinstance(target, str):
            to_language = params.get("to_language", "en")
            query = f"Translate the following text to {to_language}: {target}"
            return await self.ask(query)

        return f"Translation of {target} to {params.get('to_language', 'en')}"

    async def _index(self, target: Any, **params: Any) -> IndexResult:
        """Index a target."""
        if isinstance(target, GitRepository):
            return await target.index_all(**params)

        return IndexResult(indexed_files=[], failed_files=[])

    async def _search(self, target: Any, **params: Any) -> Any:
        """Search in a target."""
        query = params.get("query", "")
        if not query:
            raise ValueError("Search query is required")

        if isinstance(target, GitRepository):
            return await target.search(query, **params)

        return Result(query=query, results=[])

    async def _generate(self, target: Any, **params: Any) -> str:
        """Generate content based on target."""
        if isinstance(target, str):
            # Target is a prompt
            return await self.ask(target, **params)

        return f"Generated content for {target}"

    async def _extract(self, target: Any, **params: Any) -> Any:
        """Extract information from target."""
        what = params.get("what", "")
        if not what:
            raise ValueError("Extraction target (what) is required")

        if isinstance(target, str):
            query = f"Extract {what} from the following: {target}"
            return await self.ask(query)

        return Result(what=what, extracted="")

    async def _convert(self, target: Any, **params: Any) -> Any:
        """Convert target to another format."""
        to_format = params.get("to_format", "")
        if not to_format:
            raise ValueError("Target format (to_format) is required")

        if isinstance(target, str):
            query = f"Convert the following to {to_format} format: {target}"
            return await self.ask(query)

        return Result(to_format=to_format, converted="")


class GitRepository:
    """Interface avançada para repositórios Git."""

    def __init__(self, url: str, local_path: str | Path | None = None):
        """Initialize repository with URL and optional local path."""
        self.url = url
        self.local_path = Path(local_path) if local_path else None
        self._cloned = False
        self._agent = None
        self._files = []
        self._branches = []
        self._current_branch = None
        self._commits = []
        self._context = {}
        self._analysis_cache = {}
        self._filters = {}

    async def __aenter__(self) -> "GitRepository":
        """Context manager entry."""
        await self.ensure_cloned()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        await self.cleanup()

    async def ensure_cloned(self) -> Path:
        """Ensure repository is cloned locally."""
        if self._cloned and self.local_path and self.local_path.exists():
            return self.local_path

        if not self.local_path:
            # Create temporary directory
            import tempfile

            self.local_path = Path(tempfile.mkdtemp())

        # Clone repository
        import subprocess

        clone_process = subprocess.run(
            ["git", "clone", self.url, str(self.local_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._cloned = True

        # Discover branches
        await self._discover_branches()

        # Find all files
        await self._index_files()

        # Publish event for repository clone
        event = RepositoryActionEvent(
            "cloned",
            self,
            {
                "url": self.url,
                "path": str(self.local_path),
                "files_count": len(self._files),
            },
        )
        await publish_event(event)

        return self.local_path

    async def _discover_branches(self) -> list[str]:
        """Discover all branches in the repository."""
        import subprocess

        result = subprocess.run(
            ["git", "-C", str(self.local_path), "branch", "-a"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Parse branches
        branches = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line:
                # Remove leading * and whitespace
                if line.startswith("*"):
                    line = line[1:].strip()
                    self._current_branch = line
                branches.append(line)

        self._branches = branches
        return branches

    async def _index_files(self) -> list[Path]:
        """Index all files in the repository."""
        self._files = []
        for path in self.local_path.rglob("*"):
            if path.is_file() and not path.name.startswith(".git"):
                self._files.append(path)
        return self._files

    async def checkout(self, branch: str) -> bool:
        """Checkout a specific branch."""
        import subprocess

        try:
            subprocess.run(
                ["git", "-C", str(self.local_path), "checkout", branch],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._current_branch = branch

            # Reindex files as they may have changed
            await self._index_files()

            # Publish event
            event = RepositoryActionEvent("branch_checkout", self, {"branch": branch})
            await publish_event(event)

            return True
        except subprocess.CalledProcessError:
            return False

    async def cleanup(self) -> None:
        """Clean up repository resources."""
        if self._agent:
            await self._agent.cleanup()

        # If using temporary directory, clean it up
        if self._cloned and self.local_path and self.local_path.parent == Path("/tmp"):
            import shutil

            shutil.rmtree(self.local_path)

    async def get_agent(self) -> "AgentImpl":
        """Get or create agent for this repository."""
        if not self._agent:
            self._agent = AgentImpl(
                capabilities=[
                    AgentCapability.CODE_ANALYSIS,
                    AgentCapability.REPOSITORY_NAVIGATION,
                ]
            )
            await self._agent.initialize()

        return self._agent

    async def index_files(
        self, files: list[str | Path], **options: Any
    ) -> "IndexResult":
        """Index specified repository files."""
        await self.ensure_cloned()
        agent = await self.get_agent()

        indexed_files = []
        failed_files = []

        # Process each file
        for file_path in files:
            file_path = Path(file_path) if isinstance(file_path, str) else file_path

            # Get absolute path if relative
            if not file_path.is_absolute() and self.local_path:
                file_path = self.local_path / file_path

            try:
                # Read file content
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Index file
                relative_path = (
                    file_path.relative_to(self.local_path)
                    if self.local_path
                    else file_path
                )
                await agent._pepper.execute(
                    query="Index repository file",
                    context={
                        "file_path": str(relative_path),
                        "content": content[:5000],  # Limit content size
                        "metadata": {"repository": self.url},
                    },
                )

                indexed_files.append(str(relative_path))

            except Exception as e:
                failed_files.append((str(file_path), str(e)))

        # Publish indexing completed event
        event = RepositoryActionEvent(
            "files_indexed",
            self,
            {"indexed_count": len(indexed_files), "failed_count": len(failed_files)},
        )
        await publish_event(event)

        return IndexResult(indexed_files=indexed_files, failed_files=failed_files)

    async def index_all(
        self, exclude: list[str] | None = None, **options: Any
    ) -> "IndexResult":
        """Index all repository files with optional exclusion patterns."""
        await self.ensure_cloned()

        # Apply exclusion patterns
        exclude_patterns = exclude or []
        files_to_index = []

        for file_path in self._files:
            # Check if file matches any exclusion pattern
            excluded = False
            for pattern in exclude_patterns:
                if file_path.match(pattern):
                    excluded = True
                    break

            if not excluded:
                files_to_index.append(file_path)

        # Index files
        return await self.index_files(files_to_index, **options)

    def code_files(self) -> "RepoFileFilter":
        """Fluent API para filtrar arquivos do repositório.

        Returns:
            Interface de filtragem de arquivos
        """
        return RepoFileFilter(self)

    async def analyze(
        self, analyses: list[AnalysisType] | None = None
    ) -> "RepositoryAnalysis":
        """Analyze repository and return comprehensive analysis."""
        await self.ensure_cloned()
        agent = await self.get_agent()

        # Publish analysis starting event
        start_event = AnalysisStartEvent(
            "repository", self, {"analyses": analyses, "branch": self._current_branch}
        )
        await publish_event(start_event)

        # If analysis was cancelled by an event handler
        if start_event.is_cancelled:
            return RepositoryAnalysis(repository=self, cancelled=True)

        # Determine which analyses to run
        analyses_to_run = analyses or [
            AnalysisType.ARCHITECTURE,
            AnalysisType.DEPENDENCIES,
        ]

        # Run the specified analyses
        results = {}

        if AnalysisType.ARCHITECTURE in analyses_to_run:
            results["architecture"] = await agent.ask(
                "How is the code structured?", repo_url=self.url
            )

        if AnalysisType.DEPENDENCIES in analyses_to_run:
            results["dependencies"] = await self._analyze_dependencies()

        if AnalysisType.COMPLEXITY in analyses_to_run:
            results["complexity"] = await self._analyze_complexity()

        if AnalysisType.PATTERNS in analyses_to_run:
            results["patterns"] = await self._analyze_patterns()

        if AnalysisType.SECURITY in analyses_to_run:
            results["security"] = await self._analyze_security()

        # Always get the purpose
        results["purpose"] = await agent.ask(
            "What is the purpose of this repository?", repo_url=self.url
        )

        # Get main files
        results["main_files"] = await agent.ask(
            "What are the main files in this project?", repo_url=self.url
        )

        # Create repository analysis result
        analysis = RepositoryAnalysis(repository=self, **results)

        # Publish analysis completed event
        complete_event = AnalysisCompleteEvent("repository", self, analysis)
        await publish_event(complete_event)

        return analysis

    async def _analyze_dependencies(self) -> dict[str, Any]:
        """Analyze repository dependencies."""
        # Specialized dependency analysis implementation
        agent = await self.get_agent()

        # Get direct dependencies
        direct_deps = await agent.ask(
            "List all direct dependencies in this repository with versions",
            repo_url=self.url,
        )

        # Parse and structure the results
        dependencies = {"direct": direct_deps}

        return dependencies

    async def _analyze_complexity(self) -> dict[str, Any]:
        """Analyze code complexity."""
        # Example implementation
        import subprocess

        # Find Python files to analyze
        python_files = [f for f in self._files if f.suffix == ".py"]
        complexity_data = {}

        if python_files:
            try:
                # Try to use radon for complexity analysis if available
                import importlib.util

                if importlib.util.find_spec("radon"):
                    for py_file in python_files[:10]:  # Limit to 10 files for example
                        rel_path = py_file.relative_to(self.local_path)
                        proc = subprocess.run(
                            ["radon", "cc", "-s", str(py_file)],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        complexity_data[str(rel_path)] = proc.stdout
            except (ImportError, subprocess.SubprocessError):
                # Fallback to simpler analysis
                for py_file in python_files[:10]:
                    rel_path = py_file.relative_to(self.local_path)
                    with open(py_file, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        loc = len(content.splitlines())
                        # Simple complexity heuristic based on line count
                        complexity_data[str(rel_path)] = {
                            "loc": loc,
                            "complexity": "high"
                            if loc > 500
                            else "medium"
                            if loc > 200
                            else "low",
                        }

        return {
            "metrics": complexity_data,
            "summary": "Complexity analysis summary would go here",
        }

    async def _analyze_patterns(self) -> dict[str, Any]:
        """Analyze design patterns used in the code."""
        # Example implementation
        agent = await self.get_agent()

        patterns = await agent.ask(
            "Identify common design patterns used in this codebase", repo_url=self.url
        )

        return {
            "identified_patterns": patterns,
            "suggestions": "Potential pattern applications would go here",
        }

    async def _analyze_security(self) -> dict[str, Any]:
        """Analyze code for security issues."""
        # Example implementation
        security_issues = []

        # Very basic check for hard-coded secrets/keys
        for file_path in self._files:
            if file_path.suffix in [
                ".py",
                ".js",
                ".ts",
                ".java",
                ".xml",
                ".yml",
                ".yaml",
            ]:
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # Basic check for API keys, passwords, etc.
                        secret_patterns = [
                            r'api[_-]?key\s*=\s*[\'"]([\w\d]{16,})[\'"]',
                            r'password\s*=\s*[\'"]([\w\d]{8,})[\'"]',
                            r'secret\s*=\s*[\'"]([\w\d]{16,})[\'"]',
                        ]

                        for pattern in secret_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                security_issues.append(
                                    {
                                        "file": str(
                                            file_path.relative_to(self.local_path)
                                        ),
                                        "issue": "Potential hardcoded secret",
                                        "pattern": pattern,
                                        "line": content[: match.start()].count("\n")
                                        + 1,
                                    }
                                )
                except Exception:
                    continue

        return {
            "issues": security_issues,
            "count": len(security_issues),
            "risk_level": "high"
            if len(security_issues) > 5
            else "medium"
            if security_issues
            else "low",
        }

    async def ask(self, question: str, **context: Any) -> str:
        """Ask a question about the repository."""
        agent = await self.get_agent()
        return await agent.ask(question, repo_url=self.url, **context)

    async def search(self, query: str, **options: Any) -> "Result":
        """Search in the repository."""
        await self.ensure_cloned()
        agent = await self.get_agent()

        result = await agent.ask(
            f"Search for '{query}' in the repository", repo_url=self.url, **options
        )

        return Result(query=query, result=result)

    async def compare_branches(self, branch1: str, branch2: str) -> "Result":
        """Compare duas branches do repositório.

        Args:
            branch1: Nome da primeira branch
            branch2: Nome da segunda branch

        Returns:
            Resultado da comparação
        """
        await self.ensure_cloned()

        # Verificar se as branches existem
        if branch1 not in self._branches or branch2 not in self._branches:
            missing = []
            if branch1 not in self._branches:
                missing.append(branch1)
            if branch2 not in self._branches:
                missing.append(branch2)
            return Result(
                error=f"Branch(es) não encontrada(s): {', '.join(missing)}",
                branches_found=self._branches,
            )

        # Executar diff
        import subprocess

        result = subprocess.run(
            [
                "git",
                "-C",
                str(self.local_path),
                "diff",
                f"{branch1}..{branch2}",
                "--stat",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Obter detalhes mais profundos
        agent = await self.get_agent()
        current_branch = self._current_branch

        # Checkout branch1 para analisar
        await self.checkout(branch1)
        branch1_analysis = await self.ask("Summarize the code and architecture")

        # Checkout branch2 para analisar
        await self.checkout(branch2)
        branch2_analysis = await self.ask("Summarize the code and architecture")

        # Restaurar branch original
        if current_branch:
            await self.checkout(current_branch)

        # Analisar diferenças
        differences_analysis = await agent.ask(
            f"Analyze the differences between branches {branch1} and {branch2}",
            branch1_summary=branch1_analysis,
            branch2_summary=branch2_analysis,
            diff_stats=result.stdout,
        )

        return Result(
            branch1=branch1,
            branch2=branch2,
            diff_stats=result.stdout,
            branch1_analysis=branch1_analysis,
            branch2_analysis=branch2_analysis,
            differences_analysis=differences_analysis,
        )

    async def changes_since(self, reference: str) -> "Result":
        """Analisa mudanças desde uma referência (tag, commit, etc).

        Args:
            reference: Referência para comparação (commit, tag)

        Returns:
            Resultado da análise de mudanças
        """
        await self.ensure_cloned()

        # Verificar se a referência existe
        import subprocess

        try:
            ref_check = subprocess.run(
                ["git", "-C", str(self.local_path), "rev-parse", reference],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return Result(error=f"Referência não encontrada: {reference}")

        # Obter mudanças
        result = subprocess.run(
            [
                "git",
                "-C",
                str(self.local_path),
                "log",
                f"{reference}..HEAD",
                "--stat",
                "--oneline",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Obter resumo das mudanças
        agent = await self.get_agent()
        changes_summary = await agent.ask(
            f"Summarize the changes since {reference}",
            repo_url=self.url,
            changes_log=result.stdout,
        )

        return Result(
            reference=reference,
            changes_log=result.stdout,
            changes_summary=changes_summary,
            commit_count=result.stdout.count("\n"),
        )

    async def analyze_and_report(
        self, include: list[AnalysisType] | None = None
    ) -> "Report":
        """Analisa o repositório e gera relatório completo.

        Args:
            include: Tipos de análise a incluir

        Returns:
            Relatório completo
        """
        # Executar análise
        analysis = await self.analyze(analyses=include)

        # Gerar relatório
        report = await analysis.generate_report()

        return report

    async def apply_pattern(
        self, pattern: str, target: str | Path | None = None
    ) -> "Result":
        """Aplicar um padrão de design ao código.

        Args:
            pattern: Nome do padrão a aplicar
            target: Arquivo ou pasta alvo (opcional)

        Returns:
            Resultado da aplicação do padrão
        """
        await self.ensure_cloned()

        # Verificar se temos capacidade de refatoração
        agent = await self.get_agent()
        if AgentCapability.REFACTORING not in agent.capabilities:
            return Result(
                error="Capacidade de refatoração não disponível",
                pattern=pattern,
                target=str(target) if target else "entire repo",
            )

        # Determinar o alvo
        target_path = None
        if target:
            target_path = self.local_path / Path(target)
            if not target_path.exists():
                return Result(error=f"Alvo não encontrado: {target}", pattern=pattern)

        # Aplicar o padrão
        refactor_task = Task(
            type=TaskType.REFACTOR,
            target=target_path or self.local_path,
            parameters={"pattern": pattern, "repo": self},
        )

        result = await agent.execute(refactor_task)

        return Result(
            pattern=pattern,
            target=str(target) if target else "entire repo",
            changes=result,
        )

    async def suggest_design_patterns(self) -> "Result":
        """Sugere padrões de design aplicáveis ao código.

        Returns:
            Sugestões de padrões de design
        """
        agent = await self.get_agent()
        suggestions = await agent.ask(
            "Suggest design patterns that would improve this codebase",
            repo_url=self.url,
        )

        # Estruturar as sugestões
        analysis = await self.ask(
            "Identify specific files or modules where these design patterns could be applied"
        )

        return Result(suggestions=suggestions, application_analysis=analysis)

    def with_context(self, **context: Any) -> "GitRepository":
        """Define contexto para análise.

        Args:
            **context: Variáveis de contexto

        Returns:
            Self para encadeamento
        """
        self._context.update(context)
        return self

    def find_files(self, pattern: str) -> list[Path]:
        """Encontrar arquivos por padrão glob.

        Args:
            pattern: Padrão glob

        Returns:
            Lista de arquivos encontrados
        """
        import fnmatch

        matches = []
        for file in self._files:
            if fnmatch.fnmatch(str(file), pattern):
                matches.append(file)
        return matches

    def __repr__(self) -> str:
        """String representation."""
        branch = f", branch={self._current_branch}" if self._current_branch else ""
        return f"GitRepository(url={self.url}{branch})"


class RepoFileFilter:
    """Fluent interface para filtrar arquivos do repositório."""

    def __init__(self, repo: GitRepository):
        """Inicializar filtro.

        Args:
            repo: Repositório
        """
        self.repo = repo
        self._filters = []
        self._exclusions = []

    def by_language(self, language: str) -> "RepoFileFilter":
        """Filtrar por linguagem.

        Args:
            language: Extensão ou nome da linguagem

        Returns:
            Self para encadeamento
        """
        # Mapear nomes comuns para extensões
        language_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "c++": [".cpp", ".hpp", ".h"],
            "c#": ".cs",
            "ruby": ".rb",
            "go": ".go",
            "rust": ".rs",
            "php": ".php",
            "html": ".html",
            "css": ".css",
        }

        # Se for uma linguagem conhecida, usar extensão
        if language.lower() in language_map:
            extensions = language_map[language.lower()]
            if isinstance(extensions, list):
                for ext in extensions:
                    self._filters.append(lambda f, ext=ext: f.suffix == ext)
            else:
                self._filters.append(lambda f, ext=extensions: f.suffix == ext)
        else:
            # Assumir que é uma extensão
            self._filters.append(
                lambda f, lang=language: f.suffix == lang
                if lang.startswith(".")
                else f.suffix == f".{lang}"
            )

        return self

    def excluding(self, pattern: str) -> "RepoFileFilter":
        """Excluir arquivos por padrão.

        Args:
            pattern: Padrão de exclusão

        Returns:
            Self para encadeamento
        """
        import fnmatch

        self._exclusions.append(lambda f, pat=pattern: fnmatch.fnmatch(str(f), pat))
        return self

    def in_directory(self, directory: str) -> "RepoFileFilter":
        """Filtrar arquivos em diretório.

        Args:
            directory: Nome do diretório

        Returns:
            Self para encadeamento
        """
        self._filters.append(
            lambda f, d=directory: str(f).startswith(str(self.repo.local_path / d))
        )
        return self

    def matching(self, pattern: str) -> "RepoFileFilter":
        """Filtrar arquivos por padrão glob.

        Args:
            pattern: Padrão glob

        Returns:
            Self para encadeamento
        """
        import fnmatch

        self._filters.append(lambda f, pat=pattern: fnmatch.fnmatch(str(f), pat))
        return self

    async def analyze(self, **options: Any) -> "Result":
        """Analisar arquivos filtrados.

        Args:
            **options: Opções de análise

        Returns:
            Resultado da análise
        """
        # Aplicar filtros
        files = self._apply_filters()

        if not files:
            return Result(
                error="No files match the specified filters",
                filters_applied=len(self._filters),
                exclusions_applied=len(self._exclusions),
            )

        # Analisar arquivos
        agent = await self.repo.get_agent()

        # Prepare sample code from files (limit to avoid overloading)
        code_samples = []
        for file in files[:5]:  # Limit to 5 files
            try:
                with open(file, encoding="utf-8", errors="ignore") as f:
                    rel_path = file.relative_to(self.repo.local_path)
                    content = f.read()
                    code_samples.append(f"File: {rel_path}\n\n{content[:1000]}...")
            except Exception:
                continue

        # Perform analysis
        file_count = len(files)
        file_types = set(f.suffix for f in files)

        # Generate analysis based on file contents
        code_analysis = ""
        if code_samples:
            code_analysis = await agent.ask(
                "Analyze these code files and provide insights",
                code_samples="\n\n---\n\n".join(code_samples),
                file_count=file_count,
            )

        return Result(
            file_count=file_count,
            file_types=list(file_types),
            file_paths=[str(f.relative_to(self.repo.local_path)) for f in files[:20]],
            analysis=code_analysis,
            has_more_files=file_count > 20,
        )

    def _apply_filters(self) -> list[Path]:
        """Aplicar filtros aos arquivos.

        Returns:
            Arquivos filtrados
        """
        # Começar com todos os arquivos
        files = self.repo._files

        # Aplicar filtros de inclusão
        for filter_func in self._filters:
            files = [f for f in files if filter_func(f)]

        # Aplicar filtros de exclusão
        for exclude_func in self._exclusions:
            files = [f for f in files if not exclude_func(f)]

        return files

    async def count(self) -> int:
        """Contar arquivos filtrados.

        Returns:
            Número de arquivos
        """
        return len(self._apply_filters())


class PepperPy:
    """
    Classe principal do framework PepperPy.

    Fornece métodos fluidos para inicialização, configuração e uso do framework.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Inicializa o framework.

        Args:
            config: Configuração opcional
        """
        self.config = config or {}
        self._initialized = False
        self._plugins: dict[str, Plugin] = {}
        self._current_plugin_type: str | None = None
        self._current_plugin_id: str | None = None
        self._current_config: dict[str, Any] = {}
        self._context: dict[str, Any] = {}
        self._events: list[Event] = []
        self._providers: dict[str, dict[str, Any]] = {}

    async def __aenter__(self) -> Self:
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        await self.cleanup()

    async def initialize(self) -> Self:
        """Inicializa o framework e seus componentes."""
        if self._initialized:
            return self

        # Initialize plugins
        await self._initialize_plugins()

        self._initialized = True
        return self

    async def cleanup(self) -> None:
        """Limpa o framework e todos os plugins."""
        if not self._initialized:
            return

        # Clean up plugins
        for plugin in self._plugins.values():
            await plugin.cleanup()

        self._initialized = False

    async def _initialize_plugins(self) -> None:
        """Inicializa todos os plugins registrados."""
        for plugin_id, plugin in self._plugins.items():
            try:
                await plugin.initialize()
            except Exception as e:
                print(f"Erro ao inicializar plugin {plugin_id}: {e}")

    def with_plugin(self, plugin_type: str, plugin_id: str) -> Self:
        """
        Configura o plugin atual para operações encadeadas.

        Args:
            plugin_type: Tipo de plugin
            plugin_id: ID do plugin

        Returns:
            Self para encadeamento
        """
        self._current_plugin_type = plugin_type
        self._current_plugin_id = plugin_id
        self._current_config = {}
        return self

    def with_config(self, **config: Any) -> Self:
        """
        Define configuração para o plugin atual.

        Args:
            **config: Opções de configuração

        Returns:
            Self para encadeamento
        """
        self._current_config.update(config)
        return self

    def with_context(self, **context: Any) -> Self:
        """
        Define contexto para a próxima operação.

        Args:
            **context: Variáveis de contexto

        Returns:
            Self para encadeamento
        """
        self._context.update(context)
        return self

    def reset_context(self) -> Self:
        """
        Limpa o contexto atual.

        Returns:
            Self para encadeamento
        """
        self._context = {}
        return self

    async def execute(self, query: str, context: dict[str, Any] | None = None) -> Any:
        """
        Executa uma query com contexto.

        Args:
            query: Query do usuário
            context: Informações de contexto

        Returns:
            Resultado da execução da query
        """
        # Verificar se o framework está inicializado
        if not self._initialized:
            await self.initialize()

        # Criar contexto completo
        full_context = self._context.copy()
        if context:
            full_context.update(context)

        # Publicar evento de início de execução
        event = Event("execute.start", {"query": query, "context": full_context})
        await publish_event(event)

        # Processar a query
        result = await self._process_query(query, full_context)

        # Publicar evento de conclusão
        end_event = Event(
            "execute.complete",
            {"query": query, "context": full_context, "result": result},
        )
        await publish_event(end_event)

        return result

    async def _process_query(self, query: str, context: dict[str, Any]) -> Any:
        """
        Processa uma query usando o contexto.

        Args:
            query: Query do usuário
            context: Contexto da execução

        Returns:
            Resultado do processamento
        """
        # Aqui você implementaria a lógica real de processamento
        # Por enquanto, retorna um texto de exemplo com base na query
        if "texto" in context:
            texto = context["texto"]
            if "normalizar" in query.lower():
                return self._normalize_text_example(texto, context.get("opcoes", {}))
            elif "resumir" in query.lower():
                return self._summarize_text_example(texto)
            elif "traduzir" in query.lower():
                return self._translate_text_example(texto)

        return f"PepperPy processou: {query}"

    # Exemplos de métodos de processamento
    def _normalize_text_example(self, texto: str, opcoes: dict[str, Any]) -> str:
        """Exemplo de normalização de texto."""
        result = texto

        if opcoes.get("minusculas", False):
            result = result.lower()

        if opcoes.get("remover_pontuacao", False):
            result = re.sub(r"[^\w\s]", "", result)

        return result

    def _summarize_text_example(self, texto: str) -> str:
        """Exemplo de resumo de texto."""
        words = texto.split()
        if len(words) <= 5:
            return texto
        return " ".join(words[:5]) + "..."

    def _translate_text_example(self, texto: str) -> str:
        """Exemplo de tradução de texto."""
        return f"[Tradução] {texto}"

    async def normalize(self, text: str, **options: Any) -> str:
        """
        Normaliza um texto com as opções especificadas.

        Args:
            text: Texto a ser normalizado
            **options: Opções de normalização

        Returns:
            Texto normalizado
        """
        context = {"texto": text, "opcoes": options}
        result = await self.execute("Normalizar este texto", context)
        return result

    async def summarize(self, text: str, length: str = "medium") -> str:
        """
        Resume um texto.

        Args:
            text: Texto a ser resumido
            length: Tamanho do resumo (short, medium, long)

        Returns:
            Texto resumido
        """
        context = {"texto": text, "tamanho": length}
        result = await self.execute("Resumir este texto", context)
        return result

    async def translate(self, text: str, target_language: str) -> str:
        """
        Traduz um texto.

        Args:
            text: Texto a ser traduzido
            target_language: Idioma alvo

        Returns:
            Texto traduzido
        """
        context = {"texto": text, "idioma": target_language}
        result = await self.execute(
            f"Traduzir este texto para {target_language}", context
        )
        return result

    async def process_file(
        self,
        input_path: str | Path,
        output_path: str | Path | None = None,
        operation: str = "normalize",
        **options: Any,
    ) -> str | None:
        """
        Processa um arquivo de texto.

        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída (opcional)
            operation: Operação a ser realizada (normalize, summarize, translate)
            **options: Opções adicionais

        Returns:
            Conteúdo processado se output_path for None, caso contrário None
        """
        # Normalizar caminhos
        input_path = Path(input_path)
        output_path = Path(output_path) if output_path else None

        # Verificar se o arquivo existe
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

        # Ler o arquivo
        with open(input_path, encoding="utf-8") as f:
            content = f.read()

        # Processar o conteúdo
        if operation == "normalize":
            processed = await self.normalize(content, **options)
        elif operation == "summarize":
            processed = await self.summarize(content, **options.get("length", "medium"))
        elif operation == "translate":
            processed = await self.translate(
                content, options.get("target_language", "en")
            )
        else:
            raise ValueError(f"Operação desconhecida: {operation}")

        # Salvar ou retornar o resultado
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(processed)
            return None
        else:
            return processed

    def register_plugin(self, plugin: Plugin) -> Plugin:
        """
        Registra um plugin no framework.

        Args:
            plugin: Instância do plugin

        Returns:
            O plugin registrado
        """
        self._plugins[plugin.plugin_id] = plugin
        return plugin

    def create_repository(
        self, url: str, local_path: str | Path | None = None
    ) -> GitRepository:
        """
        Cria uma interface para um repositório git.

        Args:
            url: URL do repositório
            local_path: Caminho local opcional

        Returns:
            Interface do repositório
        """
        return GitRepository(url=url, local_path=local_path)

    # Métodos factory integrados do factory.py
    def create_plugin(
        self, plugin_type: str, provider_type: str | None = None, **config: Any
    ) -> Plugin:
        """
        Cria uma instância de plugin.

        Args:
            plugin_type: Tipo de plugin (llm, tts, rag, etc.)
            provider_type: Tipo de provedor (opcional)
            **config: Configuração adicional

        Returns:
            Instância do plugin
        """
        if not provider_type:
            # Obter provedor padrão
            provider_type = config.pop("provider_type", "default")

        # Criação e registro fictício do plugin
        plugin = Plugin()
        plugin.plugin_id = f"{plugin_type}.{provider_type}"
        for key, value in config.items():
            setattr(plugin, key, value)

        # Registrar o plugin
        self._plugins[plugin.plugin_id] = plugin
        return plugin

    def create_agent(self, **config: Any) -> AgentImpl:
        """
        Cria um agente.

        Args:
            **config: Configuração do agente

        Returns:
            Instância do agente
        """
        capabilities = config.pop("capabilities", None)
        return AgentImpl(capabilities=capabilities, **config)


# Instância singleton
_instance: PepperPy | None = None

# Funções de factory globais


def get_instance() -> PepperPy:
    """Obtém ou cria a instância singleton do PepperPy."""
    global _instance
    if _instance is None:
        _instance = PepperPy()
    return _instance


async def create(**config: Any) -> PepperPy:
    """
    Cria uma nova instância do framework.

    Args:
        **config: Configuração opcional

    Returns:
        Nova instância do framework
    """
    instance = PepperPy(config)
    await instance.initialize()
    return instance


def Repository(url: str, local_path: str | Path | None = None) -> GitRepository:
    """
    Cria uma interface para um repositório git.

    Args:
        url: URL do repositório
        local_path: Caminho local opcional

    Returns:
        Interface do repositório
    """
    return GitRepository(url=url, local_path=local_path)


async def normalize(text: str, **options: Any) -> str:
    """
    Normaliza um texto com as opções especificadas.

    Args:
        text: Texto a ser normalizado
        **options: Opções de normalização

    Returns:
        Texto normalizado
    """
    instance = get_instance()
    return await instance.normalize(text, **options)


async def summarize(text: str, length: str = "medium") -> str:
    """
    Resume um texto.

    Args:
        text: Texto a ser resumido
        length: Tamanho do resumo (short, medium, long)

    Returns:
        Texto resumido
    """
    instance = get_instance()
    return await instance.summarize(text, length=length)


async def translate(text: str, target_language: str) -> str:
    """
    Traduz um texto.

    Args:
        text: Texto a ser traduzido
        target_language: Idioma alvo

    Returns:
        Texto traduzido
    """
    instance = get_instance()
    return await instance.translate(text, target_language=target_language)


async def process_file(
    input_path: str | Path,
    output_path: str | Path | None = None,
    operation: str = "normalize",
    **options: Any,
) -> str | None:
    """
    Processa um arquivo de texto.

    Args:
        input_path: Caminho do arquivo de entrada
        output_path: Caminho do arquivo de saída (opcional)
        operation: Operação a ser realizada (normalize, summarize, translate)
        **options: Opções adicionais

    Returns:
        Conteúdo processado se output_path for None, caso contrário None
    """
    instance = get_instance()
    return await instance.process_file(input_path, output_path, operation, **options)


async def analyze(
    url: str, objectives: list[str] | None = None, **options: Any
) -> Result:
    """
    Analisa um URL (repositório, documento, etc.) com objetivos específicos.

    Args:
        url: URL a ser analisado
        objectives: Lista de objetivos de análise
        **options: Opções adicionais

    Returns:
        Resultado da análise
    """
    # Determinar tipo de URL e criar handler apropriado
    if url.endswith(".git") or "github.com" in url:
        # Git repository
        repo = Repository(url)

        # Se especificou análises específicas, mapear para AnalysisType
        analyses = None
        if objectives:
            analyses = []
            for obj in objectives:
                if obj == "understand_purpose":
                    # Propósito já é sempre incluído
                    pass
                elif obj == "identify_structure":
                    analyses.append(AnalysisType.ARCHITECTURE)
                elif obj == "summarize_code":
                    analyses.append(AnalysisType.COMPLEXITY)
                elif obj == "check_security":
                    analyses.append(AnalysisType.SECURITY)
                elif obj == "identify_patterns":
                    analyses.append(AnalysisType.PATTERNS)

        # Executar análise
        analysis = await repo.analyze(analyses=analyses)

        return analysis

    # Default para resultado genérico
    return Result(url=url, analysis=f"Análise de {url}")


# Alias task factory para métodos da classe Task
analyze_task = Task.analyze
summarize_task = Task.summarize
translate_task = Task.translate
index_task = Task.index
search_task = Task.search
generate_task = Task.generate
extract_task = Task.extract
convert_task = Task.convert

# Export public API
__all__ = [
    # Classes principais
    "PepperPy",
    "Plugin",
    "ProviderPlugin",
    "Event",
    "Task",
    "Result",
    "TextResult",
    "Report",
    "RepositoryAnalysis",
    "IndexResult",
    "GitRepository",
    "RepoFileFilter",
    # Enums
    "TaskType",
    "AgentCapability",
    "DependencyType",
    "EventPriority",
    "ServiceScope",
    "ResourceType",
    "AnalysisType",
    "AnalysisScope",
    "AnalysisLevel",
    # Protocols
    "Initializable",
    "TextProcessor",
    "Agent",
    "Repository",
    # Decoradores do DSL
    "repository_task",
    "code_analysis",
    "on_analysis_complete",
    "on_task_complete",
    "event_handler",
    # Eventos
    "Event",
    "AnalysisStartEvent",
    "AnalysisCompleteEvent",
    "RepositoryActionEvent",
    "publish_event",
    # Funções factory
    "get_instance",
    "create",
    "Repository",
    "normalize",
    "summarize",
    "translate",
    "process_file",
    "analyze",
    # Aliases de factory para Task
    "analyze_task",
    "summarize_task",
    "translate_task",
    "index_task",
    "search_task",
    "generate_task",
    "extract_task",
    "convert_task",
]
