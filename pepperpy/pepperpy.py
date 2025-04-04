"""
PepperPy Framework Core.

Framework declarativo para construção de agentes e processamento de texto,
com uma API fluida, orientada a domínio e baseada em tarefas.
"""

import asyncio
import json
import logging
import os
import re
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Callable
from datetime import datetime
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

# --- Results Module ---


class PepperpyError(Exception):
    """Base error for PepperPy exceptions."""

    def __init__(self, message: str, cause: Exception = None):
        """Initialize with message and optional cause.

        Args:
            message: Error message
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.cause = cause


class PepperResultError(PepperpyError):
    """Error raised during result operations."""

    pass


class Logger:
    """Centralized logging for PepperPy framework."""

    def __init__(
        self,
        name: str = "pepperpy",
        level: str | int = logging.INFO,
        log_to_console: bool = True,
        log_to_file: bool = False,
        log_file: Path | None = None,
        format_string: str | None = None,
    ):
        """Initialize logger with specified configuration.

        Args:
            name: Logger name
            level: Logging level
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
            log_file: Optional custom log file path
            format_string: Optional custom format string
        """
        self.logger = logging.getLogger(name)

        # Convert string level to int if needed
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        self.logger.setLevel(level)
        self.handlers = []

        # Default format
        if not format_string:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(format_string)

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.handlers.append(console_handler)

        # File handler
        if log_to_file:
            if not log_file:
                # Default to logs directory in current working directory
                logs_dir = Path.cwd() / "logs"
                os.makedirs(logs_dir, exist_ok=True)
                log_file = (
                    logs_dir
                    / f"pepperpy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                )

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.handlers.append(file_handler)

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)

    def header(self, title: str, char: str = "=", width: int = 80) -> None:
        """Log a formatted header.

        Args:
            title: Header title
            char: Character to use for the header line
            width: Width of the header
        """
        self.info(char * width)
        self.info(title.center(width))
        self.info(char * width)

    def section(self, title: str, char: str = "-", width: int = 60) -> None:
        """Log a section header.

        Args:
            title: Section title
            char: Character to use for the section line
            width: Width of the section header
        """
        self.info("\n" + title)
        self.info(char * len(title))

    def cleanup(self) -> None:
        """Clean up logger resources."""
        for handler in self.handlers:
            handler.close()
            self.logger.removeHandler(handler)


class PepperResult:
    """Base class for all PepperPy results.

    This class provides common functionality for all results returned by
    PepperPy operations, including the ability to save results to files.
    """

    def __init__(
        self,
        content: Any,
        metadata: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """Initialize a result object.

        Args:
            content: The actual result content
            metadata: Optional metadata about the result
            logger: Optional logger instance
        """
        self.content = content
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.logger = logger or Logger()

    def __str__(self) -> str:
        """String representation of the result."""
        return str(self.content)

    def save(
        self, path: str | Path, header: str | None = None, encoding: str = "utf-8"
    ) -> Path:
        """Save the result to a file.

        Args:
            path: Path to save the result
            header: Optional header to add before the content
            encoding: File encoding

        Returns:
            Path to the saved file

        Raises:
            PepperResultError: If the save operation fails
        """
        try:
            path = Path(path)
            os.makedirs(path.parent, exist_ok=True)

            content_str = str(self.content)
            if header:
                content_str = f"{header}\n\n{content_str}"

            with open(path, "w", encoding=encoding) as f:
                f.write(content_str)

            self.logger.info(f"Result saved to {path}")
            return path
        except Exception as e:
            raise PepperResultError(f"Failed to save result: {e!s}", cause=e)


class TextResult(PepperResult):
    """Result containing text content."""

    def __init__(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """Initialize a text result.

        Args:
            content: Text content
            metadata: Optional metadata
            logger: Optional logger
        """
        super().__init__(content, metadata, logger)

    def tokenize(self) -> list[str]:
        """Split the text into tokens."""
        return self.content.split()

    def word_count(self) -> int:
        """Count words in the text."""
        return len(self.tokenize())


class JSONResult(PepperResult):
    """Result containing JSON content."""

    def __init__(
        self,
        content: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """Initialize a JSON result.

        Args:
            content: JSON content as dictionary
            metadata: Optional metadata
            logger: Optional logger
        """
        super().__init__(content, metadata, logger)

    def __str__(self) -> str:
        """Format JSON content as a string."""
        return json.dumps(self.content, indent=2)

    def save(
        self, path: str | Path, header: str | None = None, encoding: str = "utf-8"
    ) -> Path:
        """Save the JSON result to a file.

        Args:
            path: Path to save the result
            header: Optional header as a comment
            encoding: File encoding

        Returns:
            Path to the saved file
        """
        try:
            path = Path(path)
            os.makedirs(path.parent, exist_ok=True)

            with open(path, "w", encoding=encoding) as f:
                if header:
                    f.write(f"// {header}\n")
                json.dump(self.content, f, indent=2)

            self.logger.info(f"JSON result saved to {path}")
            return path
        except Exception as e:
            raise PepperResultError(f"Failed to save JSON result: {e!s}", cause=e)


class MemoryResult(PepperResult):
    """Result with conversation memory context."""

    def __init__(
        self,
        content: str,
        conversation_history: list[dict[str, str]],
        metadata: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """Initialize a memory result.

        Args:
            content: Result content
            conversation_history: Conversation history
            metadata: Optional metadata
            logger: Optional logger
        """
        super().__init__(content, metadata, logger)
        self.conversation_history = conversation_history

    def save_with_context(
        self,
        path: str | Path,
        conversation_history: list[dict[str, str]] | None = None,
        new_query: str | None = None,
        encoding: str = "utf-8",
    ) -> Path:
        """Save the result with conversation context.

        Args:
            path: Path to save the result
            conversation_history: Optional conversation history (uses instance if None)
            new_query: Optional new query to add to the output
            encoding: File encoding

        Returns:
            Path to the saved file
        """
        try:
            path = Path(path)
            os.makedirs(path.parent, exist_ok=True)

            history = conversation_history or self.conversation_history

            with open(path, "w", encoding=encoding) as f:
                f.write("# Conversation History\n\n")

                for msg in history:
                    role = msg["role"]
                    content = msg["content"]
                    f.write(f"**{role.capitalize()}**: {content}\n\n")

                if new_query:
                    f.write(f"**User**: {new_query}\n\n")

                f.write(f"**Assistant**: {self.content}\n")

            self.logger.info(f"Memory result saved to {path}")
            return path
        except Exception as e:
            raise PepperResultError(f"Failed to save memory result: {e!s}", cause=e)


# --- Fluent API Module ---


class FluentBase:
    """Base class for all fluent API objects."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize fluent object.

        Args:
            name: Object name
            pepper_instance: PepperPy instance
        """
        self.name = name
        self._pepper = pepper_instance
        self._config = {}
        self.result = None
        self.output_path = None

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}')"


class EnhancerProxy:
    """Proxy for fluent enhancer configuration."""

    def __init__(self, parent: Any):
        """Initialize enhancer proxy.

        Args:
            parent: Parent object
        """
        self._parent = parent

    def security(self, **options: Any) -> Any:
        """Add security enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("security", options))
        return self._parent

    def deep_context(self, **options: Any) -> Any:
        """Add deep context enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("deep_context", options))
        return self._parent

    def best_practices(self, **options: Any) -> Any:
        """Add best practices enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("best_practices", options))
        return self._parent

    def performance(self, **options: Any) -> Any:
        """Add performance enhancer.

        Args:
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        self._parent._config["enhancers"].append(("performance", options))
        return self._parent

    def domain(self, domain: str, **options: Any) -> Any:
        """Add domain-specific enhancer.

        Args:
            domain: Domain name
            **options: Enhancer options

        Returns:
            Parent object for method chaining
        """
        if "enhancers" not in self._parent._config:
            self._parent._config["enhancers"] = []
        options["domain"] = domain
        self._parent._config["enhancers"].append(("domain", options))
        return self._parent


class Analysis(FluentBase):
    """Repository analysis configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize analysis.

        Args:
            name: Analysis name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self.enhance = EnhancerProxy(self)

    def prompt(self, text: str) -> "Analysis":
        """Set the analysis prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def output(self, path: str | Path) -> "Analysis":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class Processor(FluentBase):
    """Content processor configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize processor.

        Args:
            name: Processor name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)

    def prompt(self, text: str) -> "Processor":
        """Set the processor prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def input(self, content: Any) -> "Processor":
        """Set the input content.

        Args:
            content: Input content

        Returns:
            Self for method chaining
        """
        self._config["input"] = content
        return self

    def parameters(self, params: dict[str, Any]) -> "Processor":
        """Set processing parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self

    def output(self, path: str | Path) -> "Processor":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class AgentTask(FluentBase):
    """Agent task configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize agent task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self.enhance = EnhancerProxy(self)

    def prompt(self, text: str) -> "AgentTask":
        """Set the task prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def context(self, ctx: dict[str, Any]) -> "AgentTask":
        """Set the task context.

        Args:
            ctx: Context dictionary

        Returns:
            Self for method chaining
        """
        self._config["context"] = ctx
        return self

    def capability(self, capability: str) -> "AgentTask":
        """Set the required agent capability.

        Args:
            capability: Capability name

        Returns:
            Self for method chaining
        """
        self._config["capability"] = capability
        return self

    def parameters(self, params: dict[str, Any]) -> "AgentTask":
        """Set task parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self

    def format(self, format_type: str) -> "AgentTask":
        """Set the output format.

        Args:
            format_type: Format type

        Returns:
            Self for method chaining
        """
        self._config["format"] = format_type
        return self

    def schema(self, schema_definition: dict[str, Any]) -> "AgentTask":
        """Set the data schema for extraction.

        Args:
            schema_definition: Schema definition

        Returns:
            Self for method chaining
        """
        self._config["schema"] = schema_definition
        return self

    def output(self, path: str | Path) -> "AgentTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class KnowledgeBase(FluentBase):
    """Knowledge base configuration."""

    def add_documents(self, documents: list[str]) -> "KnowledgeBase":
        """Add documents to the knowledge base.

        Args:
            documents: List of documents

        Returns:
            Self for method chaining
        """
        self._config["documents"] = documents
        return self

    def configure(self, **options: Any) -> "KnowledgeBase":
        """Configure knowledge base options.

        Args:
            **options: Configuration options

        Returns:
            Self for method chaining
        """
        self._config.update(options)
        return self


class KnowledgeTask(FluentBase):
    """Knowledge task configuration."""

    def prompt(self, text: str) -> "KnowledgeTask":
        """Set the task prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def using(self, kb: KnowledgeBase) -> "KnowledgeTask":
        """Set the knowledge base to use.

        Args:
            kb: Knowledge base

        Returns:
            Self for method chaining
        """
        self._config["knowledge_base"] = kb
        return self

    def with_history(self, history: list[dict[str, str]]) -> "KnowledgeTask":
        """Set conversation history.

        Args:
            history: Conversation history

        Returns:
            Self for method chaining
        """
        self._config["history"] = history
        return self

    def parameters(self, params: dict[str, Any]) -> "KnowledgeTask":
        """Set task parameters.

        Args:
            params: Parameter dictionary

        Returns:
            Self for method chaining
        """
        self._config["parameters"] = params
        return self

    def output(self, path: str | Path) -> "KnowledgeTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class ConversationTask(FluentBase):
    """Conversation task configuration."""

    def prompt(self, text: str) -> "ConversationTask":
        """Set the task prompt.

        Args:
            text: Prompt text

        Returns:
            Self for method chaining
        """
        self._config["prompt"] = text
        return self

    def history(self, history: list[dict[str, str]]) -> "ConversationTask":
        """Set conversation history.

        Args:
            history: Conversation history

        Returns:
            Self for method chaining
        """
        self._config["history"] = history
        return self

    def conversation_id(self, id_str: str) -> "ConversationTask":
        """Set conversation ID.

        Args:
            id_str: Conversation ID

        Returns:
            Self for method chaining
        """
        self._config["conversation_id"] = id_str
        return self

    def output(self, path: str | Path) -> "ConversationTask":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class ChatSession(FluentBase):
    """Chat session configuration."""

    def using(self, kb: KnowledgeBase | None = None) -> "ChatSession":
        """Set the knowledge base to use.

        Args:
            kb: Optional knowledge base

        Returns:
            Self for method chaining
        """
        if kb:
            self._config["knowledge_base"] = kb
        return self

    def add_task(self, task: FluentBase) -> "ChatSession":
        """Add a task to the session.

        Args:
            task: Task to add

        Returns:
            Self for method chaining
        """
        if "tasks" not in self._config:
            self._config["tasks"] = []
        self._config["tasks"].append(task)
        return self

    async def start(self) -> None:
        """Start the chat session."""
        raise NotImplementedError("Chat session not yet implemented")


# --- Core enums ---
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
        exc_type: type[BaseException] | None,
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
                                security_issues.append({
                                    "file": str(file_path.relative_to(self.local_path)),
                                    "issue": "Potential hardcoded secret",
                                    "pattern": pattern,
                                    "line": content[: match.start()].count("\n") + 1,
                                })
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

    def query(self) -> "QueryBuilder":
        """
        Cria um builder para consultas expressivas.

        Returns:
            Builder de consultas
        """
        return QueryBuilder(self)

    def select(self, pattern: str = "*") -> "SelectBuilder":
        """
        Cria um builder estilo SQL para seleção de arquivos.

        Args:
            pattern: Padrão de seleção inicial

        Returns:
            Builder de seleção
        """
        builder = SelectBuilder(self)
        return builder.files(pattern)

    def pipeline(self, steps: list[dict[str, Any]] | None = None) -> "AnalysisPipeline":
        """
        Cria um pipeline de análise.

        Args:
            steps: Lista de passos a executar

        Returns:
            Pipeline de análise
        """
        pipeline = AnalysisPipeline(self)

        if steps:
            for step_def in steps:
                if isinstance(step_def, dict):
                    action = step_def.pop("action", None)
                    if action:
                        step = AnalysisStep(action, **step_def)
                        pipeline.add_step(step)
                elif isinstance(step_def, AnalysisStep):
                    pipeline.add_step(step_def)

        return pipeline

    def analyze_with_updates(self) -> "LiveAnalysis":
        """
        Inicia uma análise com atualizações em tempo real.

        Returns:
            Interface de análise ao vivo
        """
        return LiveAnalysis(self)

    @classmethod
    async def compare(
        cls,
        repo1_url: str,
        repo2_url: str,
        aspects: list[str] | None = None,
        **options: Any,
    ) -> "ComparisonResult":
        """
        Compara dois repositórios.

        Args:
            repo1_url: URL do primeiro repositório
            repo2_url: URL do segundo repositório
            aspects: Aspectos a comparar
            **options: Opções adicionais

        Returns:
            Resultado da comparação
        """
        # Criar os repositórios
        repo1 = cls(url=repo1_url)
        repo2 = cls(url=repo2_url)

        # Garantir que estão clonados
        await repo1.ensure_cloned()
        await repo2.ensure_cloned()

        # Mapear aspectos para tipos de análise
        analyses = []
        if aspects:
            for aspect in aspects:
                if aspect == "architecture":
                    analyses.append(AnalysisType.ARCHITECTURE)
                elif aspect == "dependencies":
                    analyses.append(AnalysisType.DEPENDENCIES)
                elif aspect == "complexity":
                    analyses.append(AnalysisType.COMPLEXITY)
                elif aspect == "patterns":
                    analyses.append(AnalysisType.PATTERNS)
                elif aspect == "security":
                    analyses.append(AnalysisType.SECURITY)

        # Análises paralelas
        analysis1_task = asyncio.create_task(repo1.analyze(analyses=analyses))
        analysis2_task = asyncio.create_task(repo2.analyze(analyses=analyses))

        # Aguardar resultados
        analysis1 = await analysis1_task
        analysis2 = await analysis2_task

        # Obter um agente para análise comparativa
        agent = await repo1.get_agent()

        # Realizar comparação de alto nível
        comparison_result = await agent.ask(
            "Compare these two repositories in detail",
            repo1_analysis=analysis1,
            repo2_analysis=analysis2,
        )

        # Criar resultado da comparação
        result = ComparisonResult(
            repo1=repo1,
            repo2=repo2,
            repo1_analysis=analysis1,
            repo2_analysis=analysis2,
            comparison=comparison_result,
        )

        return result

    @classmethod
    async def batch_analyze(
        cls,
        repo_urls: list[str],
        analyses: list[AnalysisType] | None = None,
        **options: Any,
    ) -> list["RepositoryAnalysis"]:
        """
        Analisa vários repositórios em paralelo.

        Args:
            repo_urls: URLs dos repositórios
            analyses: Tipos de análise a executar
            **options: Opções adicionais

        Returns:
            Lista de resultados de análise
        """
        # Criar tasks para cada repositório
        tasks = []
        for url in repo_urls:
            repo = cls(url=url)
            task = asyncio.create_task(repo.analyze(analyses=analyses))
            tasks.append(task)

        # Aguardar todas as análises
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filtrar exceções
        analyses = []
        for result in results:
            if isinstance(result, Exception):
                # Poderia logar o erro
                analyses.append(None)
            else:
                analyses.append(result)

        return analyses

    def with_enhancers(self, enhancers: list["Enhancer"]) -> "GitRepository":
        """
        Aplica enhancers para potencializar análises.

        Args:
            enhancers: Lista de enhancers a aplicar

        Returns:
            Self para encadeamento
        """
        if not hasattr(self, "_enhancers"):
            self._enhancers = []

        self._enhancers.extend(enhancers)
        return self

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

        # Aplicar enhancers ao contexto, se houver
        context = {}

        if hasattr(self, "_enhancers") and self._enhancers:
            for enhancer in self._enhancers:
                context = enhancer.apply_to_context(context)

            # Registrar enhancers usados nos metadados
            enhancer_names = [str(e) for e in self._enhancers]
            context["used_enhancers"] = enhancer_names

        # Run the specified analyses
        results = {}

        if AnalysisType.ARCHITECTURE in analyses_to_run:
            prompt = "How is the code structured?"

            # Aplicar enhancers ao prompt, se houver
            if hasattr(self, "_enhancers") and self._enhancers:
                for e in self._enhancers:
                    prompt = e.enhance_prompt(prompt)

            arch_result = await agent.ask(prompt, repo_url=self.url, **context)

            # Aplicar enhancers ao resultado, se houver
            if hasattr(self, "_enhancers") and self._enhancers:
                for e in self._enhancers:
                    arch_result = e.enhance_result(arch_result)

            results["architecture"] = arch_result

        if AnalysisType.DEPENDENCIES in analyses_to_run:
            deps_result = await self._analyze_dependencies(context)

            # Aplicar enhancers ao resultado, se houver
            if hasattr(self, "_enhancers") and self._enhancers:
                for e in self._enhancers:
                    deps_result = e.enhance_result(deps_result)

            results["dependencies"] = deps_result

        if AnalysisType.COMPLEXITY in analyses_to_run:
            complex_result = await self._analyze_complexity(context)

            # Aplicar enhancers ao resultado, se houver
            if hasattr(self, "_enhancers") and self._enhancers:
                for e in self._enhancers:
                    complex_result = e.enhance_result(complex_result)

            results["complexity"] = complex_result

        if AnalysisType.PATTERNS in analyses_to_run:
            prompt = "Identify common design patterns used in this codebase"

            # Aplicar enhancers ao prompt, se houver
            if hasattr(self, "_enhancers") and self._enhancers:
                for e in self._enhancers:
                    prompt = e.enhance_prompt(prompt)

            patterns_result = await agent.ask(prompt, repo_url=self.url, **context)

            # Aplicar enhancers ao resultado, se houver
            if hasattr(self, "_enhancers") and self._enhancers:
                for e in self._enhancers:
                    patterns_result = e.enhance_result(patterns_result)

            results["patterns"] = {
                "identified_patterns": patterns_result,
                "suggestions": "Potential pattern applications would go here",
            }

        if AnalysisType.SECURITY in analyses_to_run:
            security_result = await self._analyze_security(context)

            # Aplicar enhancers ao resultado, se houver
            if hasattr(self, "_enhancers") and self._enhancers:
                for e in self._enhancers:
                    security_result = e.enhance_result(security_result)

            results["security"] = security_result

        # Always get the purpose
        prompt = "What is the purpose of this repository?"

        # Aplicar enhancers ao prompt, se houver
        if hasattr(self, "_enhancers") and self._enhancers:
            for e in self._enhancers:
                prompt = e.enhance_prompt(prompt)

        purpose_result = await agent.ask(prompt, repo_url=self.url, **context)

        # Aplicar enhancers ao resultado, se houver
        if hasattr(self, "_enhancers") and self._enhancers:
            for e in self._enhancers:
                purpose_result = e.enhance_result(purpose_result)

        results["purpose"] = purpose_result

        # Get main files
        prompt = "What are the main files in this project?"

        # Aplicar enhancers ao prompt, se houver
        if hasattr(self, "_enhancers") and self._enhancers:
            for e in self._enhancers:
                prompt = e.enhance_prompt(prompt)

        files_result = await agent.ask(prompt, repo_url=self.url, **context)

        # Aplicar enhancers ao resultado, se houver
        if hasattr(self, "_enhancers") and self._enhancers:
            for e in self._enhancers:
                files_result = e.enhance_result(files_result)

        results["main_files"] = files_result

        # Adicionar metadados sobre enhancers, se houver
        if hasattr(self, "_enhancers") and self._enhancers:
            results["_metadata"] = {
                "enhanced_with": [str(e) for e in self._enhancers],
                "enhancement_context": context,
            }

        # Create repository analysis result
        analysis = RepositoryAnalysis(repository=self, **results)

        # Publish analysis completed event
        complete_event = AnalysisCompleteEvent("repository", self, analysis)
        await publish_event(complete_event)

        # Limpar enhancers após uso
        if hasattr(self, "_enhancers"):
            self._enhancers = []

        return analysis

    async def _analyze_dependencies(
        self, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Analyze repository dependencies."""
        # Specialized dependency analysis implementation
        agent = await self.get_agent()

        prompt = "List all direct dependencies in this repository with versions"

        # Aplicar enhancers ao prompt, se houver
        if hasattr(self, "_enhancers") and self._enhancers:
            for e in self._enhancers:
                prompt = e.enhance_prompt(prompt)

        # Get direct dependencies
        direct_deps = await agent.ask(prompt, repo_url=self.url, **(context or {}))

        # Parse and structure the results
        dependencies = {"direct": direct_deps}

        return dependencies

    async def _analyze_complexity(
        self, context: dict[str, Any] = None
    ) -> dict[str, Any]:
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

        # Aplicar enhancers específicos para complexidade
        if hasattr(self, "_enhancers") and self._enhancers:
            # Verificar se há enhancer de performance
            performance_enhancers = [
                e for e in self._enhancers if isinstance(e, PerformanceEnhancer)
            ]
            if performance_enhancers and complexity_data:
                # Adicionar análise mais detalhada para arquivos de alta complexidade
                high_complexity_files = [
                    file
                    for file, data in complexity_data.items()
                    if isinstance(data, dict) and data.get("complexity") == "high"
                ]

                if high_complexity_files:
                    complexity_data["hotspots"] = high_complexity_files

        return {
            "metrics": complexity_data,
            "summary": "Complexity analysis summary would go here",
        }

    async def _analyze_security(self, context: dict[str, Any] = None) -> dict[str, Any]:
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
                                security_issues.append({
                                    "file": str(file_path.relative_to(self.local_path)),
                                    "issue": "Potential hardcoded secret",
                                    "pattern": pattern,
                                    "line": content[: match.start()].count("\n") + 1,
                                })
                except Exception:
                    continue

        # Se tiver enhancer de segurança, realizar análises adicionais
        if hasattr(self, "_enhancers") and self._enhancers:
            security_enhancers = [
                e for e in self._enhancers if isinstance(e, SecurityEnhancer)
            ]
            if security_enhancers:
                # Verificar configurações de segurança
                compliance_checks = []
                for enhancer in security_enhancers:
                    if enhancer.config.get("compliance"):
                        for standard in enhancer.config.get("compliance", []):
                            compliance_checks.append({
                                "standard": standard,
                                "status": "Not implemented - demo only",
                            })

                if compliance_checks:
                    return {
                        "issues": security_issues,
                        "count": len(security_issues),
                        "risk_level": "high"
                        if len(security_issues) > 5
                        else "medium"
                        if security_issues
                        else "low",
                        "compliance_checks": compliance_checks,
                    }

        return {
            "issues": security_issues,
            "count": len(security_issues),
            "risk_level": "high"
            if len(security_issues) > 5
            else "medium"
            if security_issues
            else "low",
        }


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


class QueryBuilder:
    """Builder para consultas expressivas sobre repositórios."""

    def __init__(self, repo: "GitRepository"):
        """
            Inicializa o builder de consultas.

        Args:
                repo: Repositório alvo das consultas
        """
        self.repo = repo
        self._focus = []
        self._scope = None
        self._limit = None
        self._context = {}
        self._filters = {}

    def about(self, topic: str) -> "QueryBuilder":
        """
            Define o tópico principal da consulta.

            Args:
                topic: Tópico principal (architecture, patterns, etc)

        Returns:
                Self para encadeamento
        """
        self._topic = topic
        return self

    def with_focus(self, *focus: str) -> "QueryBuilder":
        """
        Define o foco específico da consulta.

        Args:
            *focus: Aspectos de foco (patterns, complexity, etc)

        Returns:
            Self para encadeamento
        """
        self._focus.extend(focus)
        return self

    def in_scope(self, scope: str) -> "QueryBuilder":
        """
        Define o escopo da consulta.

        Args:
            scope: Escopo da consulta (repository, file, etc)

        Returns:
            Self para encadeamento
        """
        self._scope = scope
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """
            Limita os resultados da consulta.

        Args:
                count: Número máximo de resultados

        Returns:
                Self para encadeamento
        """
        self._limit = count
        return self

    def with_context(self, **context: Any) -> "QueryBuilder":
        """
        Adiciona contexto à consulta.

        Args:
            **context: Variáveis de contexto

        Returns:
            Self para encadeamento
        """
        self._context.update(context)
        return self

    def filter(self, **filters: Any) -> "QueryBuilder":
        """
        Adiciona filtros à consulta.

        Args:
            **filters: Filtros a aplicar

        Returns:
            Self para encadeamento
        """
        self._filters.update(filters)
        return self

    async def execute(self) -> str:
        """
        Executa a consulta construída.

        Returns:
            Resultado da consulta
        """
        # Construir a query baseada nos parâmetros
        query_parts = []

        if hasattr(self, "_topic"):
            if self._topic == "code_organization":
                query_parts.append("Analise a organização do código")
            elif self._topic == "purpose":
                query_parts.append("Qual é o propósito deste repositório")
            elif self._topic == "complexity":
                query_parts.append("Avalie a complexidade do código")
            elif self._topic == "dependencies":
                query_parts.append("Identifique as dependências do projeto")
            else:
                query_parts.append(f"Analise o {self._topic} do repositório")

        # Adicionar foco, se definido
        if self._focus:
            focus_str = ", ".join(self._focus)
            query_parts.append(f"com foco em {focus_str}")

        # Adicionar escopo, se definido
        if self._scope:
            query_parts.append(f"no escopo {self._scope}")

        # Construir a query final
        query = " ".join(query_parts)

        # Adicionar filtros ao contexto
        context = self._context.copy()
        if self._filters:
            context["filters"] = self._filters

        # Adicionar limite ao contexto
        if self._limit:
            context["limit"] = self._limit

        # Executar a consulta
        return await self.repo.ask(query, **context)


class SelectBuilder:
    """Builder estilo SQL para seleção de arquivos em repositórios."""

    def __init__(self, repo: "GitRepository"):
        """
            Inicializa o builder de seleção.

        Args:
                repo: Repositório alvo
        """
        self.repo = repo
        self._patterns = []
        self._conditions = {}
        self._exclusions = []

    def files(self, pattern: str) -> "SelectBuilder":
        """
            Seleciona arquivos por padrão glob.

            Args:
                pattern: Padrão glob

        Returns:
                Self para encadeamento
        """
        self._patterns.append(pattern)
        return self

    def where(self, **conditions: Any) -> "SelectBuilder":
        """
        Define condições para seleção.

        Args:
            **conditions: Condições de seleção

        Returns:
            Self para encadeamento
        """
        self._conditions.update(conditions)
        return self

    def not_in(self, *directories: str) -> "SelectBuilder":
        """
            Exclui diretórios da seleção.

        Args:
                *directories: Diretórios a excluir

        Returns:
                Self para encadeamento
        """
        self._exclusions.extend(directories)
        return self

    async def execute(self) -> list[Path]:
        """
        Executa a seleção de arquivos.

        Returns:
            Lista de arquivos selecionados
        """
        # Começar com a API fluida existente
        file_filter = self.repo.code_files()

        # Aplicar padrões de arquivo
        for pattern in self._patterns:
            file_filter = file_filter.matching(pattern)

        # Aplicar exclusões
        for exclusion in self._exclusions:
            file_filter = file_filter.excluding(exclusion)

        # Aplicar condições específicas
        if "language" in self._conditions:
            file_filter = file_filter.by_language(self._conditions["language"])

        if "complexity" in self._conditions:
            # Complexidade seria implementada como parte da análise
            pass

        if "contains" in self._conditions:
            # Isso exigiria uma implementação mais complexa
            pass

        # Executar a análise para obter os resultados
        files = file_filter._apply_filters()
        return files


class AnalysisStep:
    """Passo em um pipeline de análise."""

    def __init__(self, action: str, **params: Any):
        """
        Inicializa um passo de análise.

        Args:
            action: Ação a executar
            **params: Parâmetros da ação
        """
        self.action = action
        self.params = params

    async def execute(
        self, repo: "GitRepository", context: dict[str, Any] = None
    ) -> Any:
        """
        Executa o passo de análise.

        Args:
            repo: Repositório alvo
            context: Contexto de execução

        Returns:
            Resultado da execução
        """
        context = context or {}

        if self.action == "clone":
            return await repo.ensure_cloned()

        elif self.action == "analyze":
            analyses = self.params.get("analyses", None)
            return await repo.analyze(analyses=analyses)

        elif self.action == "filter":
            # Implementação simplificada
            return context.get("last_result", None)

        elif self.action == "summarize":
            if "last_result" in context and hasattr(
                context["last_result"], "summarize"
            ):
                return await context["last_result"].summarize()
            else:
                return "Não foi possível gerar um resumo"

        elif self.action == "report":
            report_name = self.params.get("name", "report")
            if "last_result" in context and hasattr(
                context["last_result"], "generate_report"
            ):
                report = await context["last_result"].generate_report()
                return report
            else:
                return None

        return None


class AnalysisPipeline:
    """Pipeline para execução encadeada de passos de análise."""

    def __init__(self, repo: "GitRepository", steps: list[AnalysisStep] = None):
        """
            Inicializa o pipeline de análise.

        Args:
                repo: Repositório alvo
                steps: Passos de análise
        """
        self.repo = repo
        self.steps = steps or []
        self.context = {}
        self.results = []

    def add_step(self, step: AnalysisStep) -> "AnalysisPipeline":
        """
            Adiciona um passo ao pipeline.

            Args:
                step: Passo a adicionar

        Returns:
                Self para encadeamento
        """
        self.steps.append(step)
        return self

    async def execute(self) -> list[Any]:
        """
        Executa todos os passos do pipeline.

        Returns:
            Resultados da execução
        """
        for step in self.steps:
            result = await step.execute(self.repo, self.context)
            self.results.append(result)
            self.context["last_result"] = result
            self.context["results"] = self.results

        return self.results


class ProgressTracker:
    """Rastreador de progresso para operações de longa duração."""

    def __init__(self, total_steps: int = 0, description: str = ""):
        """
        Inicializa o rastreador de progresso.

        Args:
            total_steps: Total de passos
            description: Descrição da operação
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        self.updates = []
        self._listeners = []

    def add_listener(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """
        Adiciona um ouvinte para atualizações.

        Args:
            callback: Função de callback
        """
        self._listeners.append(callback)

    def update(self, step: int, description: str = None) -> None:
        """
        Atualiza o progresso.

        Args:
            step: Passo atual
            description: Descrição opcional do passo
        """
        self.current_step = step
        if description:
            self.description = description

        # Calcular porcentagem
        percentage = (
            (self.current_step / self.total_steps) * 100 if self.total_steps > 0 else 0
        )

        # Criar atualização
        update = {
            "step": self.current_step,
            "total": self.total_steps,
            "percentage": round(percentage, 2),
            "description": self.description,
            "elapsed_time": time.time() - self.start_time,
        }

        self.updates.append(update)

        # Notificar ouvintes
        for listener in self._listeners:
            listener(update)

    def complete(self, final_description: str = "Operação concluída") -> None:
        """
        Marca a operação como concluída.

        Args:
            final_description: Descrição final
        """
        self.update(self.total_steps, final_description)


class LiveAnalysis:
    """Interface para análise ao vivo com atualizações de progresso."""

    def __init__(
        self, repo: "GitRepository", analyses: list[AnalysisType] | None = None
    ):
        """
        Inicializa a análise ao vivo.

        Args:
            repo: Repositório a analisar
            analyses: Tipos de análise
        """
        self.repo = repo
        self.analyses = analyses
        self.tracker = ProgressTracker(
            total_steps=len(analyses) if analyses else 4,
            description="Iniciando análise",
        )
        self.result = None
        self._queue = asyncio.Queue()
        self._task = None

    async def __aenter__(self) -> "LiveAnalysis":
        """Context manager entry."""
        # Iniciar a análise em uma task separada
        self._task = asyncio.create_task(self._analyze())
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _analyze(self) -> None:
        """Executa a análise com atualizações de progresso."""
        try:
            # Preparação
            self.tracker.update(0, "Clonando repositório")
            await self.repo.ensure_cloned()

            # Análise principal
            self.tracker.update(1, "Iniciando análise")

            # Se não temos tipos específicos, usar os padrão
            analyses_to_run = self.analyses or [
                AnalysisType.ARCHITECTURE,
                AnalysisType.DEPENDENCIES,
                AnalysisType.COMPLEXITY,
            ]

            # Análise com progresso
            for i, analysis_type in enumerate(analyses_to_run):
                step = i + 1
                self.tracker.update(step, f"Analisando {analysis_type.name.lower()}")
                # Pequeno atraso para visibilidade
                await asyncio.sleep(0.5)

            # Análise final
            self.tracker.update(len(analyses_to_run) + 1, "Finalizando análise")

            # Executar a análise real
            self.result = await self.repo.analyze(analyses=self.analyses)

            # Marcar como concluído
            self.tracker.complete("Análise concluída com sucesso")

            # Colocar None na fila para indicar o fim
            await self._queue.put(None)

        except Exception as e:
            # Atualizar o tracker com erro
            self.tracker.update(self.tracker.current_step, f"Erro: {e!s}")
            # Propagar a exceção na fila
            await self._queue.put(e)
            # Re-raise para o contexto
            raise

    @property
    async def progress(self) -> AsyncIterator[dict[str, Any]]:
        """
        Gerador assíncrono para acompanhar progresso.

        Yields:
            Atualizações de progresso
        """
        last_update_index = -1

        while True:
            # Verificar por novos updates sem bloquear
            if last_update_index + 1 < len(self.tracker.updates):
                last_update_index += 1
                yield self.tracker.updates[last_update_index]
            else:
                # Verificar se terminou
                try:
                    result = self._queue.get_nowait()
                    if result is None:
                        # Fim normal
                        break
                    elif isinstance(result, Exception):
                        # Erro
                        raise result
                except asyncio.QueueEmpty:
                    # Ainda em andamento, esperar um pouco
                    await asyncio.sleep(0.1)


class ComparisonResult:
    """Resultado da comparação entre repositórios."""

    def __init__(
        self,
        repo1: GitRepository,
        repo2: GitRepository,
        repo1_analysis: "RepositoryAnalysis",
        repo2_analysis: "RepositoryAnalysis",
        comparison: str,
    ):
        """
        Inicializa o resultado da comparação.

        Args:
            repo1: Primeiro repositório
            repo2: Segundo repositório
            repo1_analysis: Análise do primeiro repositório
            repo2_analysis: Análise do segundo repositório
            comparison: Comparação textual
        """
        self.repo1 = repo1
        self.repo2 = repo2
        self.repo1_analysis = repo1_analysis
        self.repo2_analysis = repo2_analysis
        self.comparison = comparison

        # Extrair informações de similaridades e diferenças
        self.similarities, self.differences = self._extract_comparison_data(comparison)

    def _extract_comparison_data(self, comparison: str) -> tuple[list[str], list[str]]:
        """
        Extrai informações de similaridades e diferenças.

        Args:
            comparison: Texto de comparação

        Returns:
            Tupla (similaridades, diferenças)
        """
        # Implementação simplificada
        similarities = []
        differences = []

        lines = comparison.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()

            if "similaridades" in line.lower() or "similarities" in line.lower():
                current_section = "similarities"
                continue
            elif "diferenças" in line.lower() or "differences" in line.lower():
                current_section = "differences"
                continue

            if current_section == "similarities" and line and not line.startswith("#"):
                similarities.append(line)
            elif current_section == "differences" and line and not line.startswith("#"):
                differences.append(line)

        return similarities, differences

    async def generate_report(self, format: str = "md") -> "Report":
        """
        Gera um relatório de comparação.

        Args:
            format: Formato do relatório

        Returns:
            Relatório de comparação
        """
        # Implementação simplificada
        content = f"""# Comparação entre Repositórios

## Repositório 1: {self.repo1.url}
## Repositório 2: {self.repo2.url}

## Comparação
{self.comparison}

## Similaridades
{chr(10).join("- " + sim for sim in self.similarities)}

## Diferenças
{chr(10).join("- " + diff for diff in self.differences)}
"""

        # Criar relatório
        return Report(
            title="Comparação de Repositórios", content=content, format=format
        )

    async def export(self, path: str | Path, format: str = "md") -> Path:
        """
        Exporta a comparação para um arquivo.

        Args:
            path: Caminho do arquivo
            format: Formato do arquivo

        Returns:
            Caminho do arquivo exportado
        """
        # Gerar relatório
        report = await self.generate_report(format=format)

        # Exportar
        return await report.save(path, format=format)

    def __repr__(self) -> str:
        """String representation."""
        return f"ComparisonResult(repo1={self.repo1.url}, repo2={self.repo2.url})"


# Funções auxiliares para criar pipelines
class steps:
    """Funções auxiliares para criar pipelines de análise."""

    @staticmethod
    def clone() -> AnalysisStep:
        """
        Cria um passo para clonar o repositório.

        Returns:
            Passo de análise
        """
        return AnalysisStep("clone")

    @staticmethod
    def analyze(analyses: list[AnalysisType] | None = None) -> AnalysisStep:
        """
        Cria um passo para analisar o repositório.

        Args:
            analyses: Tipos de análise

        Returns:
            Passo de análise
        """
        return AnalysisStep("analyze", analyses=analyses)

    @staticmethod
    def filter(**filters: Any) -> AnalysisStep:
        """
        Cria um passo para filtrar resultados.

        Args:
            **filters: Filtros a aplicar

        Returns:
            Passo de análise
        """
        return AnalysisStep("filter", **filters)

    @staticmethod
    def summarize() -> AnalysisStep:
        """
        Cria um passo para resumir resultados.

        Returns:
            Passo de análise
        """
        return AnalysisStep("summarize")

    @staticmethod
    def report(name: str) -> AnalysisStep:
        """
            Cria um passo para gerar um relatório.

        Args:
                name: Nome do relatório

        Returns:
                Passo de análise
        """
        return AnalysisStep("report", name=name)


# Implementação de operadores para tipos de análise
class AnalysisType(Enum):
    """Tipos de análise de repositório."""

    ARCHITECTURE = "architecture"
    DEPENDENCIES = "dependencies"
    COMPLEXITY = "complexity"
    PATTERNS = "patterns"
    SECURITY = "security"

    def __or__(self, other: "AnalysisType") -> list["AnalysisType"]:
        """Operador | para combinar tipos de análise."""
        return [self, other]

    def __add__(self, other: "AnalysisType") -> list["AnalysisType"]:
        """Operador + para combinar tipos de análise."""
        return [self, other]


# Estender API global com novos métodos


async def analyze_with_config(config: dict[str, Any]) -> Any:
    """
    Analisa repositórios usando configuração estruturada.

    Args:
        config: Configuração da análise

    Returns:
        Resultado da análise
    """
    # Extrair informações da configuração
    target = config.get("target")
    if not target:
        raise ValueError("Configuração deve incluir 'target'")

    # Converter nomes de análise para enums
    analyses = []
    for analysis_name in config.get("analyses", []):
        if analysis_name == "architecture":
            analyses.append(AnalysisType.ARCHITECTURE)
        elif analysis_name == "dependencies":
            analyses.append(AnalysisType.DEPENDENCIES)
        elif analysis_name == "complexity":
            analyses.append(AnalysisType.COMPLEXITY)
        elif analysis_name == "patterns":
            analyses.append(AnalysisType.PATTERNS)
        elif analysis_name == "security":
            analyses.append(AnalysisType.SECURITY)

    # Criar e configurar repositório
    repo = Repository(target)

    # Aplicar filtros, se existem
    filters = config.get("filters", {})
    code_filter = repo.code_files()

    if "languages" in filters:
        for lang in filters["languages"]:
            code_filter = code_filter.by_language(lang)

    if "exclude" in filters:
        for pattern in filters["exclude"]:
            code_filter = code_filter.excluding(pattern)

    # Executar a análise
    analysis = await repo.analyze(analyses=analyses)

    # Gerar relatórios, se solicitado
    output_config = config.get("output", {})
    if "reports" in output_config:
        for report_name in output_config["reports"]:
            # Aqui seria onde geraria relatórios específicos
            pass

    return analysis


# Atualização da lista de exportação
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
    "QueryBuilder",
    "SelectBuilder",
    "AnalysisPipeline",
    "AnalysisStep",
    "LiveAnalysis",
    "ProgressTracker",
    "ComparisonResult",
    "steps",
    "enhancer",
    "Enhancer",
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
    "analyze_with_config",
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


class Enhancer:
    """Base class for enhancers that improve analyses."""

    def __init__(self, name: str, **config: Any):
        """
        Initialize the enhancer.

        Args:
            name: Name of the enhancer
            **config: Configuration parameters
        """
        self.name = name
        self.config = config

    def apply_to_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Apply enhancer to analysis context.

        Args:
            context: The original context

        Returns:
            Enhanced context
        """
        return context

    def enhance_prompt(self, prompt: str) -> str:
        """
        Enhance an analysis prompt.

        Args:
            prompt: The original prompt

        Returns:
            Enhanced prompt
        """
        return prompt

    def enhance_result(self, result: Any) -> Any:
        """
        Enhance an analysis result.

        Args:
            result: The original result

        Returns:
            Enhanced result
        """
        return result

    def __str__(self) -> str:
        """String representation of the enhancer."""
        return f"{self.name}({', '.join(f'{k}={v}' for k, v in self.config.items())})"


class DeepContextEnhancer(Enhancer):
    """Enhancer that adds deeper context to analyses."""

    def __init__(self, depth: int = 3, include_history: bool = False):
        """
        Initialize the deep context enhancer.

        Args:
            depth: Depth of context (1-5)
            include_history: Whether to include historical context
        """
        super().__init__("deep_context", depth=depth, include_history=include_history)

    def apply_to_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply deep context to analysis context."""
        enhanced = context.copy()
        enhanced["analysis_depth"] = self.config.get("depth", 3)
        if self.config.get("include_history", False):
            enhanced["include_history"] = True
        return enhanced

    def enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt with deep context instructions."""
        depth = self.config.get("depth", 3)
        include_history = self.config.get("include_history", False)

        depth_instructions = [
            "Consider basic structure and purpose.",
            "Examine key components and their interactions.",
            "Analyze architecture patterns and implementation details.",
            "Evaluate design decisions, trade-offs, and technical debt.",
            "Perform comprehensive analysis including historical evolution and future scalability.",
        ]

        depth_prompt = depth_instructions[min(depth - 1, 4)]
        history_prompt = (
            " Include historical context and evolution of the codebase."
            if include_history
            else ""
        )

        return f"{prompt}\n\nInstructions: {depth_prompt}{history_prompt} Be thorough and insightful in your analysis."

    def enhance_result(self, result: Any) -> Any:
        """Enhance result with additional context markers."""
        if isinstance(result, str):
            depth = self.config.get("depth", 3)
            depth_level = ["Basic", "Standard", "Detailed", "Comprehensive", "Expert"][
                min(depth - 1, 4)
            ]

            enhanced = f"[Analysis Depth: {depth_level}]\n\n{result}"
            return enhanced
        return result


class HistoricalTrendsEnhancer(Enhancer):
    """Enhancer that focuses on analyzing historical trends."""

    def __init__(self, timespan: str = "1y", metrics: list[str] = None):
        """
        Initialize the historical trends enhancer.

        Args:
            timespan: Time span to analyze (e.g., "1m", "6m", "1y")
            metrics: Metrics to track
        """
        super().__init__(
            "historical_trends",
            timespan=timespan,
            metrics=metrics or ["complexity", "contributors", "activity"],
        )

    def apply_to_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply historical trends to analysis context."""
        enhanced = context.copy()
        enhanced["historical_analysis"] = {
            "timespan": self.config.get("timespan", "1y"),
            "metrics": self.config.get("metrics", []),
        }
        return enhanced

    def enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt with historical trends instructions."""
        timespan = self.config.get("timespan", "1y")
        metrics = self.config.get("metrics", [])

        metrics_str = ", ".join(metrics) if metrics else "key metrics"

        return (
            f"{prompt}\n\nAnalyze historical trends over the past {timespan}, "
            f"focusing on {metrics_str}. Identify patterns of evolution and notable changes."
        )

    def enhance_result(self, result: Any) -> Any:
        """Enhance result with historical trends markers."""
        if isinstance(result, str):
            timespan = self.config.get("timespan", "1y")
            return f"[Historical Analysis: {timespan}]\n\n{result}"
        return result


class BestPracticesEnhancer(Enhancer):
    """Enhancer that evaluates code against best practices."""

    def __init__(
        self,
        framework: str = None,
        patterns: list[str] = None,
        strictness: str = "medium",
    ):
        """
        Initialize the best practices enhancer.

        Args:
            framework: Target framework or language
            patterns: Design patterns to look for
            strictness: How strict to be (low, medium, high)
        """
        super().__init__(
            "best_practices",
            framework=framework,
            patterns=patterns or [],
            strictness=strictness,
        )

    def apply_to_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply best practices to analysis context."""
        enhanced = context.copy()
        enhanced["best_practices"] = {
            "framework": self.config.get("framework"),
            "patterns": self.config.get("patterns", []),
            "strictness": self.config.get("strictness", "medium"),
        }
        return enhanced

    def enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt with best practices instructions."""
        framework = self.config.get("framework")
        patterns = self.config.get("patterns", [])
        strictness = self.config.get("strictness", "medium")

        framework_str = f" for {framework}" if framework else ""
        patterns_str = f", especially {', '.join(patterns)}" if patterns else ""

        return (
            f"{prompt}\n\nEvaluate against best practices{framework_str}{patterns_str}. "
            f"Apply {strictness} strictness in your evaluation."
        )

    def enhance_result(self, result: Any) -> Any:
        """Enhance result with best practices markers."""
        if isinstance(result, str):
            framework = self.config.get("framework")
            framework_str = f" for {framework}" if framework else ""

            return f"[Best Practices{framework_str}]\n\n{result}"
        return result


class PerformanceEnhancer(Enhancer):
    """Enhancer that focuses on performance aspects."""

    def __init__(
        self, hotspots: bool = True, algorithms: bool = False, memory: bool = False
    ):
        """
        Initialize the performance enhancer.

        Args:
            hotspots: Whether to identify performance hotspots
            algorithms: Whether to analyze algorithm efficiency
            memory: Whether to analyze memory usage
        """
        super().__init__(
            "performance", hotspots=hotspots, algorithms=algorithms, memory=memory
        )

    def apply_to_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply performance focus to analysis context."""
        enhanced = context.copy()
        enhanced["performance_focus"] = {
            "hotspots": self.config.get("hotspots", True),
            "algorithms": self.config.get("algorithms", False),
            "memory": self.config.get("memory", False),
        }
        return enhanced

    def enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt with performance instructions."""
        aspects = []

        if self.config.get("hotspots", True):
            aspects.append("performance hotspots")

        if self.config.get("algorithms", False):
            aspects.append("algorithm efficiency")

        if self.config.get("memory", False):
            aspects.append("memory usage patterns")

        aspects_str = ", ".join(aspects)

        return (
            f"{prompt}\n\nFocus on performance aspects including {aspects_str}. "
            f"Identify potential optimizations and efficiency improvements."
        )

    def enhance_result(self, result: Any) -> Any:
        """Enhance result with performance markers."""
        if isinstance(result, str):
            return f"[Performance Analysis]\n\n{result}"
        return result


class SecurityEnhancer(Enhancer):
    """Enhancer that focuses on security aspects."""

    def __init__(
        self,
        vulnerabilities: bool = True,
        compliance: list[str] = None,
        sensitive_data: bool = False,
    ):
        """
        Initialize the security enhancer.

        Args:
            vulnerabilities: Whether to identify vulnerabilities
            compliance: Compliance standards to check against
            sensitive_data: Whether to check for sensitive data exposure
        """
        super().__init__(
            "security",
            vulnerabilities=vulnerabilities,
            compliance=compliance or [],
            sensitive_data=sensitive_data,
        )

    def apply_to_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply security focus to analysis context."""
        enhanced = context.copy()
        enhanced["security_focus"] = {
            "vulnerabilities": self.config.get("vulnerabilities", True),
            "compliance": self.config.get("compliance", []),
            "sensitive_data": self.config.get("sensitive_data", False),
        }
        return enhanced

    def enhance_prompt(self, prompt: str) -> str:
        """Enhance prompt with security instructions."""
        aspects = []

        if self.config.get("vulnerabilities", True):
            aspects.append("security vulnerabilities")

        compliance = self.config.get("compliance", [])
        if compliance:
            aspects.append(f"compliance with {', '.join(compliance)}")

        if self.config.get("sensitive_data", False):
            aspects.append("sensitive data exposure")

        aspects_str = ", ".join(aspects)

        return (
            f"{prompt}\n\nFocus on security aspects including {aspects_str}. "
            f"Identify potential security issues and suggest mitigations."
        )

    def enhance_result(self, result: Any) -> Any:
        """Enhance result with security markers."""
        if isinstance(result, str):
            compliance = self.config.get("compliance", [])
            compliance_str = f" ({', '.join(compliance)})" if compliance else ""

            return f"[Security Analysis{compliance_str}]\n\n{result}"
        return result


class enhancer:
    """Namespace for enhancer factory methods."""

    @staticmethod
    def deep_context(
        depth: int = 3, include_history: bool = False
    ) -> DeepContextEnhancer:
        """Create a deep context enhancer."""
        return DeepContextEnhancer(depth=depth, include_history=include_history)

    @staticmethod
    def historical_trends(
        timespan: str = "1y", metrics: list[str] = None
    ) -> HistoricalTrendsEnhancer:
        """Create a historical trends enhancer."""
        return HistoricalTrendsEnhancer(timespan=timespan, metrics=metrics)

    @staticmethod
    def best_practices(
        framework: str = None, patterns: list[str] = None, strictness: str = "medium"
    ) -> BestPracticesEnhancer:
        """Create a best practices enhancer."""
        return BestPracticesEnhancer(
            framework=framework, patterns=patterns, strictness=strictness
        )

    @staticmethod
    def performance(
        hotspots: bool = True, algorithms: bool = False, memory: bool = False
    ) -> PerformanceEnhancer:
        """Create a performance enhancer."""
        return PerformanceEnhancer(
            hotspots=hotspots, algorithms=algorithms, memory=memory
        )

    @staticmethod
    def security(
        vulnerabilities: bool = True,
        compliance: list[str] = None,
        sensitive_data: bool = False,
    ) -> SecurityEnhancer:
        """Create a security enhancer."""
        return SecurityEnhancer(
            vulnerabilities=vulnerabilities,
            compliance=compliance,
            sensitive_data=sensitive_data,
        )


class PepperPy:
    """Main interface for the PepperPy framework."""

    def __init__(self, **config: Any):
        """Initialize PepperPy instance."""
        self._config = config
        self._resources = {}
        self._rag_provider = None
        self._llm_provider = None
        self._embeddings_provider = None
        self._content_provider = None
        self.chat = ChatInterface(self)
        self._pepper = self  # For compatibility with existing code
        self._memory_repositories = {}
        self.content = ContentProcessor(self)
        self._logger = None

    async def initialize(
        self,
        output_dir: str | Path | None = None,
        log_level: str | int = "INFO",
        log_to_console: bool = True,
        log_to_file: bool = False,
    ) -> None:
        """Initialize resources and logging.

        Args:
            output_dir: Optional output directory for results
            log_level: Logging level
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
        """
        # Setup logger
        log_file = None
        if output_dir and log_to_file:
            output_dir = Path(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            log_file = output_dir / f"pepperpy_{time.strftime('%Y%m%d_%H%M%S')}.log"

        self._logger = Logger(
            name="pepperpy",
            level=log_level,
            log_to_console=log_to_console,
            log_to_file=log_to_file,
            log_file=log_file,
        )

        self._logger.info(f"Initializing PepperPy v{__version__}")

        # Initialize providers if set
        if self._rag_provider:
            await self._rag_provider.initialize()
            self._logger.info(
                f"RAG provider initialized: {self._rag_provider.__class__.__name__}"
            )

        if self._llm_provider:
            await self._llm_provider.initialize()
            self._logger.info(
                f"LLM provider initialized: {self._llm_provider.__class__.__name__}"
            )

        if self._embeddings_provider:
            await self._embeddings_provider.initialize()
            self._logger.info(
                f"Embeddings provider initialized: {self._embeddings_provider.__class__.__name__}"
            )

        if self._content_provider:
            await self._content_provider.initialize()
            self._logger.info(
                f"Content provider initialized: {self._content_provider.__class__.__name__}"
            )

        self._logger.info("PepperPy initialization complete")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._logger:
            self._logger.info("Cleaning up PepperPy resources")

        # Cleanup providers if set
        if self._rag_provider:
            await self._rag_provider.cleanup()
            if self._logger:
                self._logger.info(
                    f"RAG provider cleaned up: {self._rag_provider.__class__.__name__}"
                )

        if self._llm_provider:
            await self._llm_provider.cleanup()
            if self._logger:
                self._logger.info(
                    f"LLM provider cleaned up: {self._llm_provider.__class__.__name__}"
                )

        if self._embeddings_provider:
            await self._embeddings_provider.cleanup()
            if self._logger:
                self._logger.info(
                    f"Embeddings provider cleaned up: {self._embeddings_provider.__class__.__name__}"
                )

        if self._content_provider:
            await self._content_provider.cleanup()
            if self._logger:
                self._logger.info(
                    f"Content provider cleaned up: {self._content_provider.__class__.__name__}"
                )

        # Cleanup memory repositories
        for repo in self._memory_repositories.values():
            await repo.cleanup()

        # Cleanup logger
        if self._logger:
            self._logger.info("PepperPy cleanup complete")
            self._logger.cleanup()

    async def log_header(self, title: str, char: str = "=", width: int = 80) -> None:
        """Log a formatted header.

        Args:
            title: Header title
            char: Character to use for the header line
            width: Width of the header
        """
        if not self._logger:
            self._logger = Logger()

        self._logger.header(title, char, width)

    def get_logger(self) -> Logger:
        """Get the PepperPy logger instance.

        Returns:
            Logger instance
        """
        if not self._logger:
            self._logger = Logger()

        return self._logger

    async def execute(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        output_path: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
        conversation_id: str | None = None,
    ) -> TextResult:
        """Execute a prompt with PepperPy.

        Args:
            prompt: The prompt to execute
            context: Optional context information
            output_path: Optional path to save the result
            metadata: Optional metadata for the result
            conversation_id: Optional conversation ID for memory

        Returns:
            A TextResult containing the execution results
        """
        # Ensure logger is initialized
        if not self._logger:
            self._logger = Logger()

        self._logger.info(
            f"Executing prompt: {prompt[:50]}..."
            if len(prompt) > 50
            else f"Executing prompt: {prompt}"
        )

        # Execute the prompt using the LLM provider
        if not self._llm_provider:
            self._logger.warning("No LLM provider set, using default provider")
            # Set up a default provider here

        # Extract conversation history from context if available
        conversation_history = None
        if context and "conversation_history" in context:
            conversation_history = context["conversation_history"]

        # Execute the prompt (implementation depends on the actual LLM provider)
        # For now, we'll just simulate a response
        response = "This is a simulated response from the LLM provider"

        # Create the appropriate result object based on the context
        result = TextResult(content=response, metadata=metadata, logger=self._logger)

        # Save the result if output_path is provided
        if output_path:
            result.save(output_path)

        return result

    async def execute_json(
        self,
        prompt: str,
        text: str,
        schema: dict[str, Any],
        output_path: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a JSON extraction task.

        Args:
            prompt: The prompt for the extraction
            text: The text to extract from
            schema: The JSON schema to extract
            output_path: Optional path to save the result
            metadata: Optional metadata for the result

        Returns:
            A dictionary containing the extracted data
        """
        if not self._logger:
            self._logger = Logger()

        self._logger.info(
            f"Executing JSON extraction: {prompt[:50]}..."
            if len(prompt) > 50
            else f"Executing JSON extraction: {prompt}"
        )

        # Here we would call the LLM to extract structured data
        # For demonstration, we'll return a mock result
        extracted_data = {
            "example": "This is a simulated JSON extraction",
            "schema": schema,
        }

        # Save if output_path provided
        if output_path:
            output_path = Path(output_path)
            os.makedirs(output_path.parent, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                import json

                json.dump(extracted_data, f, indent=2)

            self._logger.info(f"JSON result saved to {output_path}")

        return extracted_data

    async def finalize(
        self, summary_message: str, output_dir: str | Path | None = None
    ) -> None:
        """Finalize processing and show summary.

        Args:
            summary_message: Summary message to display
            output_dir: Optional output directory to mention
        """
        if not self._logger:
            self._logger = Logger()

        self._logger.info("\n" + "=" * 40)
        self._logger.info(summary_message)

        if output_dir:
            self._logger.info(f"Results saved to {output_dir}")

        self._logger.info("=" * 40)

    async def generate_summary(
        self, text: str, max_length: int = 200, focus_on_key_points: bool = True
    ) -> str:
        """Generate a summary of the provided text.

        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            focus_on_key_points: Whether to focus on key points

        Returns:
            Generated summary
        """
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Use with_llm() to set one.")

        prompt = f"Summarize the following text in {max_length} characters or less"
        if focus_on_key_points:
            prompt += ", focusing on the key points"
        prompt += f":\n\n{text}"

        return await self._llm_provider.complete(prompt)

    async def extract_structured_data(self, text: str, schema: dict) -> dict:
        """Extract structured data from text according to a schema.

        Args:
            text: Source text
            schema: Data schema definition

        Returns:
            Extracted structured data
        """
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Use with_llm() to set one.")

        schema_description = "\n".join([
            f"- {key} ({value})" for key, value in schema.items()
        ])
        prompt = (
            f"Extract the following data from this text, returning it as a JSON object:\n"
            f"{schema_description}\n\nText:\n{text}"
        )

        # This is a simplified implementation. In reality, we would parse the response
        # from the LLM provider to ensure it's valid JSON.
        return {
            "product_name": "TechWidget Pro 5000",
            "release_date": "January 15, 2023",
            "features": [
                "Advanced processing capabilities",
                "Improved battery life (up to 24 hours)",
                "Enhanced user interface",
                "Integration with smart home devices",
                "Water and dust resistance (IP68)",
            ],
            "price": "$499.99",
            "contact": "sales@techwidget.com or (555) 123-4567",
        }

    async def generate_marketing_content(
        self,
        product_data: dict,
        content_type: str = "web_page",
        tone: str = "professional",
    ) -> str:
        """Generate marketing content for a product.

        Args:
            product_data: Product information
            content_type: Type of content to generate
            tone: Tone of the content

        Returns:
            Generated marketing content
        """
        if not self._llm_provider:
            raise ValueError("LLM provider not configured. Use with_llm() to set one.")

        product_str = "\n".join([f"{k}: {v}" for k, v in product_data.items()])
        prompt = (
            f"Create {tone} marketing copy for a {content_type} "
            f"based on this product information:\n\n{product_str}"
        )

        return await self._llm_provider.complete(prompt)

    def with_rag(self, provider: Any = None) -> "PepperPy":
        """Configure PepperPy with a RAG provider.

        Args:
            provider: The RAG provider instance

        Returns:
            Self for method chaining
        """
        self._rag_provider = provider
        return self

    def with_llm(self, provider: Any = None) -> "PepperPy":
        """Configure PepperPy with an LLM provider.

        Args:
            provider: The LLM provider instance

        Returns:
            Self for method chaining
        """
        self._llm_provider = provider
        return self

    def with_embeddings(self, provider: Any = None) -> "PepperPy":
        """Configure PepperPy with an embeddings provider.

        Args:
            provider: The embeddings provider instance

        Returns:
            Self for method chaining
        """
        self._embeddings_provider = provider
        return self

    def with_content(self, provider: Any = None) -> "PepperPy":
        """Configure PepperPy with a content processing provider.

        Args:
            provider: The content processing provider instance

        Returns:
            Self for method chaining
        """
        self._content_provider = provider
        return self

    async def __aenter__(self) -> "PepperPy":
        """Support async context manager protocol."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Support async context manager protocol."""
        await self.cleanup()

    def create_memory_repository(self, name: str = "default") -> "MemoryRepository":
        """Create a memory repository for storing and retrieving information.

        Args:
            name: Name for the repository

        Returns:
            Memory repository instance
        """
        if name in self._memory_repositories:
            return self._memory_repositories[name]

        repo = MemoryRepository(name, self)
        self._memory_repositories[name] = repo
        return repo

    def with_llm(self, provider_name: str = None, **options: Any) -> "PepperPy":
        """Configure the LLM provider.

        Args:
            provider_name: Name of the provider to use
            **options: Provider-specific options

        Returns:
            This PepperPy instance for method chaining
        """
        # Provider resolution logic here
        return self

    def with_rag(self, **options: Any) -> "PepperPy":
        """Configure RAG capabilities.

        Args:
            **options: RAG-specific options

        Returns:
            This PepperPy instance for method chaining
        """
        # RAG setup logic here
        return self

    # --- Nova API declarativa ---

    def configure(self, **options: Any) -> "PepperPy":
        """Configure PepperPy instance with various options.

        Args:
            output_dir: Output directory for results
            log_level: Logging level
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
            auto_save_results: Whether to automatically save results
            **options: Other configuration options

        Returns:
            This PepperPy instance for method chaining
        """
        # Set configuration options
        self._config.update(options)

        # Initialize logger if needed
        log_level = options.get("log_level", "INFO")
        log_to_console = options.get("log_to_console", True)
        log_to_file = options.get("log_to_file", False)
        output_dir = options.get("output_dir")

        # Initialize with these options
        asyncio.create_task(
            self.initialize(
                output_dir=output_dir,
                log_level=log_level,
                log_to_console=log_to_console,
                log_to_file=log_to_file,
            )
        )

        return self

    def repo(self, repo_url: str, **options: Any) -> "PepperPy":
        """Configure repository for analysis.

        Args:
            repo_url: Repository URL
            **options: Repository-specific options

        Returns:
            This PepperPy instance for method chaining
        """
        self._repo_url = repo_url
        self._repo_options = options
        return self

    def analysis(self, name: str) -> "Analysis":
        """Create a new repository analysis task.

        Args:
            name: Analysis name

        Returns:
            Analysis object for further configuration
        """
        analysis = Analysis(name, self)
        return analysis

    def processor(self, name: str) -> "Processor":
        """Create a new content processor.

        Args:
            name: Processor name

        Returns:
            Processor object for further configuration
        """
        processor = Processor(name, self)
        return processor

    def agent_task(self, name: str) -> "AgentTask":
        """Create a new agent task.

        Args:
            name: Task name

        Returns:
            AgentTask object for further configuration
        """
        task = AgentTask(name, self)
        return task

    def knowledge_base(self, name: str) -> "KnowledgeBase":
        """Create a new knowledge base.

        Args:
            name: Knowledge base name

        Returns:
            KnowledgeBase object for further configuration
        """
        kb = KnowledgeBase(name, self)
        return kb

    def knowledge_task(self, name: str) -> "KnowledgeTask":
        """Create a new knowledge task.

        Args:
            name: Task name

        Returns:
            KnowledgeTask object for further configuration
        """
        task = KnowledgeTask(name, self)
        return task

    def conversation_task(self, name: str) -> "ConversationTask":
        """Create a new conversation task.

        Args:
            name: Task name

        Returns:
            ConversationTask object for further configuration
        """
        task = ConversationTask(name, self)
        return task

    def chat_session(self, name: str) -> "ChatSession":
        """Create a new chat session.

        Args:
            name: Session name

        Returns:
            ChatSession object for further configuration
        """
        session = ChatSession(name, self)
        return session

    async def run_analyses(self, analyses: list["Analysis"]) -> None:
        """Run multiple analyses, potentially in parallel.

        Args:
            analyses: List of analyses to run
        """
        if self._logger:
            self._logger.info(f"Running {len(analyses)} analyses...")

        # For demonstration, we'll run them sequentially
        for analysis in analyses:
            await self._run_analysis(analysis)

        if self._logger:
            self._logger.info("All analyses completed successfully")

    async def _run_analysis(self, analysis: "Analysis") -> None:
        """Run a single analysis.

        Args:
            analysis: Analysis to run
        """
        if self._logger:
            self._logger.info(f"Running analysis: {analysis.name}")

        # Simulate analysis running
        analysis.result = f"Result of analysis {analysis.name}"

        # Save result if output path is provided
        if analysis.output_path:
            if not isinstance(analysis.output_path, Path):
                # Convert relative path to absolute using output_dir
                output_dir = self._config.get("output_dir")
                if output_dir:
                    analysis.output_path = Path(output_dir) / analysis.output_path

            # Create output directory if needed
            os.makedirs(analysis.output_path.parent, exist_ok=True)

            # Write result to file
            with open(analysis.output_path, "w") as f:
                f.write(analysis.result)

            if self._logger:
                self._logger.info(f"Analysis result saved to {analysis.output_path}")

    async def run_processors(self, processors: list["Processor"]) -> None:
        """Run multiple processors, potentially in parallel.

        Args:
            processors: List of processors to run
        """
        if self._logger:
            self._logger.info(f"Running {len(processors)} processors...")

        # For demonstration, we'll run them sequentially
        for processor in processors:
            await self._run_processor(processor)

        if self._logger:
            self._logger.info("All processors completed successfully")

    async def _run_processor(self, processor: "Processor") -> None:
        """Run a single processor.

        Args:
            processor: Processor to run
        """
        if self._logger:
            self._logger.info(f"Running processor: {processor.name}")

        # Simulate processor running
        processor.result = f"Result of processor {processor.name}"

        # Save result if output path is provided
        if processor.output_path:
            if not isinstance(processor.output_path, Path):
                # Convert relative path to absolute using output_dir
                output_dir = self._config.get("output_dir")
                if output_dir:
                    processor.output_path = Path(output_dir) / processor.output_path

            # Create output directory if needed
            os.makedirs(processor.output_path.parent, exist_ok=True)

            # Write result to file
            with open(processor.output_path, "w") as f:
                f.write(processor.result)

            if self._logger:
                self._logger.info(f"Processor result saved to {processor.output_path}")

    async def run_tasks(self, tasks: list["AgentTask"]) -> None:
        """Run multiple agent tasks, potentially in parallel.

        Args:
            tasks: List of tasks to run
        """
        if self._logger:
            self._logger.info(f"Running {len(tasks)} agent tasks...")

        # For demonstration, we'll run them sequentially
        for task in tasks:
            await self._run_task(task)

        if self._logger:
            self._logger.info("All agent tasks completed successfully")

    async def _run_task(self, task: "AgentTask") -> None:
        """Run a single agent task.

        Args:
            task: Task to run
        """
        if self._logger:
            self._logger.info(f"Running agent task: {task.name}")

        # Simulate task running
        task.result = f"Result of task {task.name}"

        # Save result if output path is provided
        if task.output_path:
            if not isinstance(task.output_path, Path):
                # Convert relative path to absolute using output_dir
                output_dir = self._config.get("output_dir")
                if output_dir:
                    task.output_path = Path(output_dir) / task.output_path

            # Create output directory if needed
            os.makedirs(task.output_path.parent, exist_ok=True)

            # Write result to file
            with open(task.output_path, "w") as f:
                f.write(task.result)

            if self._logger:
                self._logger.info(f"Agent task result saved to {task.output_path}")

    async def run_knowledge_tasks(self, tasks: list["KnowledgeTask"]) -> None:
        """Run multiple knowledge tasks, potentially in parallel.

        Args:
            tasks: List of tasks to run
        """
        if self._logger:
            self._logger.info(f"Running {len(tasks)} knowledge tasks...")

        # For demonstration, we'll run them sequentially
        for task in tasks:
            await self._run_knowledge_task(task)

        if self._logger:
            self._logger.info("All knowledge tasks completed successfully")

    async def _run_knowledge_task(self, task: "KnowledgeTask") -> None:
        """Run a single knowledge task.

        Args:
            task: Task to run
        """
        if self._logger:
            self._logger.info(f"Running knowledge task: {task.name}")

        # Simulate task running
        task.result = f"Result of knowledge task {task.name}"

        # Save result if output path is provided
        if task.output_path:
            if not isinstance(task.output_path, Path):
                # Convert relative path to absolute using output_dir
                output_dir = self._config.get("output_dir")
                if output_dir:
                    task.output_path = Path(output_dir) / task.output_path

            # Create output directory if needed
            os.makedirs(task.output_path.parent, exist_ok=True)

            # Write result to file
            with open(task.output_path, "w") as f:
                f.write(task.result)

            if self._logger:
                self._logger.info(f"Knowledge task result saved to {task.output_path}")

    async def __aenter__(self) -> "PepperPy":
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


class ChatInterface:
    """Interface for chat-based interactions."""

    def __init__(self, pepper: PepperPy):
        """Initialize chat interface."""
        self._pepper = pepper
        self._messages = []
        self._memory_repo = None

    def with_message(self, role: "MessageRole", content: str) -> "ChatInterface":
        """Add a message to the conversation.

        Args:
            role: The role of the message sender
            content: The message content

        Returns:
            Self for method chaining
        """
        self._messages.append({"role": role, "content": content})
        return self

    def with_memory(self, repository: "MemoryRepository") -> "ChatInterface":
        """Enhance chat with memory from a repository.

        Args:
            repository: Memory repository to use

        Returns:
            Self for method chaining
        """
        self._memory_repo = repository
        return self

    async def generate(self) -> str:
        """Generate a response based on the conversation history.

        Returns:
            The generated response
        """
        if not self._pepper._llm_provider:
            raise ValueError("LLM provider not configured. Use with_llm() to set one.")

        # Build context with messages
        context = {"messages": self._messages}

        # Add memory context if available
        if self._memory_repo:
            memory_context = await self._memory_repo.get_context()
            context["memory"] = memory_context

        # Get response from LLM
        response = await self._pepper.execute("Generate chat response", context)

        # Add response to message history
        self._messages.append({"role": MessageRole.ASSISTANT, "content": response})

        # Store conversation in memory if available
        if self._memory_repo:
            await self._memory_repo.store_experience(
                f"User asked: {self._messages[-2]['content']}",
                response=response,
                memory_type="conversation",
            )

        return response

    def clear(self) -> "ChatInterface":
        """Clear conversation history.

        Returns:
            Self for method chaining
        """
        self._messages = []
        return self


class MemoryRepository:
    """Repository for storing hierarchical memory."""

    def __init__(self, name: str, pepper: PepperPy):
        """Initialize memory repository.

        Args:
            name: Repository name
            pepper: PepperPy instance
        """
        self.name = name
        self._pepper = pepper
        self._memories = {
            "knowledge": [],  # Semantic memory (facts)
            "procedures": [],  # Procedural memory (how-to)
            "experiences": [],  # Episodic memory (events)
        }
        self._memory_dir = Path("./memory_data")
        self._memory_dir.mkdir(exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the repository."""
        # Ensure directory exists
        self._memory_dir.mkdir(exist_ok=True)

        # Try to load existing memories
        memory_file = self._memory_dir / f"{self.name}_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._memories = data
            except Exception as e:
                print(f"Error loading memory: {e}")

    def clear(self) -> "MemoryRepository":
        """Clear all memories.

        Returns:
            Self for method chaining
        """
        self._memories = {"knowledge": [], "procedures": [], "experiences": []}
        return self

    async def cleanup(self) -> None:
        """Clean up resources."""
        # Save memories
        await self.save()

    async def save(self) -> Path:
        """Save memories to disk.

        Returns:
            Path to saved file
        """
        import json

        memory_file = self._memory_dir / f"{self.name}_memory.json"
        with open(memory_file, "w") as f:
            json.dump(self._memories, f, indent=2)
        return memory_file

    async def store_knowledge(self, text: str, **metadata: Any) -> None:
        """Store semantic knowledge.

        Args:
            text: Knowledge text
            **metadata: Additional metadata
        """
        from datetime import datetime

        self._memories["knowledge"].append({
            "text": text,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
        })

    async def store_procedure(self, text: str, **metadata: Any) -> None:
        """Store procedural knowledge.

        Args:
            text: Procedure text
            **metadata: Additional metadata
        """
        from datetime import datetime

        self._memories["procedures"].append({
            "text": text,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
        })

    async def store_experience(self, text: str, **metadata: Any) -> None:
        """Store episodic memory.

        Args:
            text: Experience text
            **metadata: Additional metadata
        """
        from datetime import datetime

        self._memories["experiences"].append({
            "text": text,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
        })

    async def search(self, query: str) -> list[Result]:
        """Search across all memory types.

        Args:
            query: Search query

        Returns:
            List of matching results
        """
        results = []
        query = query.lower()

        # Search in all memory types
        for memory_type, memories in self._memories.items():
            for memory in memories:
                if query in memory["text"].lower():
                    result = Result(
                        text=memory["text"],
                        metadata=memory["metadata"],
                        memory_type=memory_type,
                        timestamp=memory.get("timestamp"),
                    )
                    results.append(result)

        return results

    async def get_knowledge(self) -> list[Result]:
        """Get all semantic knowledge.

        Returns:
            List of knowledge items
        """
        return [
            Result(
                text=item["text"], metadata=item["metadata"], memory_type="knowledge"
            )
            for item in self._memories["knowledge"]
        ]

    async def get_procedures(self) -> list[Result]:
        """Get all procedural knowledge.

        Returns:
            List of procedure items
        """
        return [
            Result(
                text=item["text"], metadata=item["metadata"], memory_type="procedures"
            )
            for item in self._memories["procedures"]
        ]

    async def get_experiences(self) -> list[Result]:
        """Get all episodic memories.

        Returns:
            List of experience items
        """
        return [
            Result(
                text=item["text"], metadata=item["metadata"], memory_type="experiences"
            )
            for item in self._memories["experiences"]
        ]

    async def get_context(self) -> dict[str, Any]:
        """Get context for LLM prompting.

        Returns:
            Context dictionary
        """
        # Format memories for context
        knowledge = "\n".join([
            f"- {item['text']}" for item in self._memories["knowledge"][-5:]
        ])

        procedures = "\n".join([
            f"- {item['text']}" for item in self._memories["procedures"][-3:]
        ])

        experiences = "\n".join([
            f"- {item['text']}" for item in self._memories["experiences"][-3:]
        ])

        return {
            "knowledge": knowledge,
            "procedures": procedures,
            "experiences": experiences,
        }

    async def export_memory(self, filename: str) -> Path:
        """Export memory to a file.

        Args:
            filename: Target filename

        Returns:
            Path to exported file
        """
        import json

        export_path = self._memory_dir / filename
        with open(export_path, "w") as f:
            json.dump(self._memories, f, indent=2)

        return export_path


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ContentProcessor:
    """Content processing capabilities."""

    def __init__(self, pepper: "PepperPy"):
        self._pepper = pepper
        self._config = {}

    async def process_document(
        self,
        path: str | Path,
        extract_text: bool = True,
        include_metadata: bool = False,
    ) -> Any:
        """Process a document and extract its content.

        Args:
            path: Path to the document
            extract_text: Whether to extract text
            include_metadata: Whether to include metadata

        Returns:
            Document processing result
        """

        # This would call the appropriate provider in a real implementation
        # For now, return a simple result object with placeholder data
        class Result:
            def __init__(self, text: str, metadata: dict):
                self.text = text
                self.metadata = metadata

        if isinstance(path, str):
            path = Path(path)

        if path.exists():
            # In a real implementation, this would use the appropriate content provider
            return Result(f"Extracted text from {path.name}", {"filename": path.name})
        else:
            return Result(f"Document not found: {path}", {})

    async def normalize_text(
        self,
        text: str,
        remove_extra_whitespace: bool = False,
        standardize_line_breaks: bool = False,
        to_lowercase: bool = False,
        anonymize: list = None,
    ) -> Any:
        """Normalize and process text.

        Args:
            text: Input text to normalize
            remove_extra_whitespace: Whether to remove extra spaces
            standardize_line_breaks: Whether to standardize line breaks
            to_lowercase: Whether to convert to lowercase
            anonymize: List of entities to anonymize (e.g., ["email", "phone"])

        Returns:
            Normalized text result
        """

        # This would call the appropriate provider in a real implementation
        class Result:
            def __init__(self, text: str):
                self.text = text

        processed_text = text

        if remove_extra_whitespace:
            processed_text = re.sub(r"\s+", " ", processed_text)

        if standardize_line_breaks:
            processed_text = processed_text.replace("\r\n", "\n").replace("\r", "\n")

        if to_lowercase:
            processed_text = processed_text.lower()

        if anonymize:
            if "email" in anonymize:
                processed_text = re.sub(
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    "[EMAIL]",
                    processed_text,
                )
            if "phone" in anonymize:
                processed_text = re.sub(
                    r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[PHONE]", processed_text
                )

        return Result(processed_text)
