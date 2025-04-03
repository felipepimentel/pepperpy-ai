"""
PepperPy Framework Core.

Fornece o ponto de entrada principal para o framework PepperPy,
com uma API fluida e intuitiva para plugins, serviços e eventos.
"""

import asyncio
import inspect
import sys
from collections.abc import Callable
from enum import Enum
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import (
    Any,
    Protocol,
    Self,
    TypeVar,
    get_type_hints,
    runtime_checkable,
)


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


# Core typing
T = TypeVar("T")
P = TypeVar("P", bound="PepperpyPlugin")


# Core protocols
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
class AIProvider(Protocol):
    """Protocol for AI providers."""

    async def call(self, prompt: str, **options: Any) -> str:
        """Call the AI provider."""
        ...


# Core base classes
class EventContext:
    """Contexto para eventos do PepperPy."""

    def __init__(self, event_type: str, data: Any = None):
        """Inicializa o contexto do evento.

        Args:
            event_type: Tipo do evento
            data: Dados do evento
        """
        self.event_type = event_type
        self.data = data
        self.cancelled = False
        self.results: list[Any] = []

    def cancel(self) -> None:
        """Cancela o processamento do evento."""
        self.cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Verifica se o evento foi cancelado."""
        return self.cancelled

    def add_result(self, result: Any) -> None:
        """Adiciona um resultado ao contexto."""
        self.results.append(result)

    def get_results(self) -> list[Any]:
        """Obtém todos os resultados do contexto."""
        return self.results.copy()


class PepperpyPlugin:
    """Classe base para plugins do PepperPy."""

    def __init__(self, **kwargs):
        """Inicializa o plugin.

        Args:
            **kwargs: Configuração do plugin
        """
        self.plugin_id = self.__class__.__name__
        self.config = kwargs or {}
        # Allow direct attribute access to config values
        for key, value in self.config.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    async def initialize(self) -> None:
        """Inicializa o plugin."""
        pass

    async def cleanup(self) -> None:
        """Limpa recursos do plugin."""
        pass


class ProviderPlugin(PepperpyPlugin):
    """Classe base para plugins provedores."""

    provider_type: str = ""


# Core registry storage
_plugins: dict[str, PepperpyPlugin] = {}
_plugin_classes: dict[str, type[PepperpyPlugin]] = {}
_dependencies: dict[str, dict[str, DependencyType]] = {}
_services: dict[str, dict[str, Callable]] = {}
_event_handlers: dict[str, list[dict[str, Any]]] = {}


# Import core components with fallbacks for smooth initialization
try:
    from pepperpy.core.config_manager import get_config
    from pepperpy.core.logging import configure_logging, get_logger
except ImportError:
    # Fallback implementations when not running within full framework
    def get_config(section: str = "", **defaults) -> dict[str, Any]:
        """Get configuration."""
        return defaults

    def configure_logging(**kwargs) -> None:
        """Configure logging."""
        pass

    def get_logger(name: str) -> Any:
        """Get a logger."""

        class SimpleLogger:
            def debug(self, msg: str, *args, **kwargs) -> None:
                print(f"DEBUG: {msg}")

            def info(self, msg: str, *args, **kwargs) -> None:
                print(f"INFO: {msg}")

            def warning(self, msg: str, *args, **kwargs) -> None:
                print(f"WARNING: {msg}")

            def error(self, msg: str, *args, **kwargs) -> None:
                print(f"ERROR: {msg}")

        return SimpleLogger()


# Setup logger for this module
logger = get_logger(__name__)


# Record the Python version at startup
PYTHON_VERSION = sys.version_info
PYTHON_VERSION_STR = (
    f"{PYTHON_VERSION.major}.{PYTHON_VERSION.minor}.{PYTHON_VERSION.micro}"
)


# Fluent decorator implementations
def plugin(
    cls=None,
    *,
    provides: str | None = None,
    depends_on: str | list[str] | dict[str, DependencyType] | None = None,
):
    """
    Decorador para definir uma classe como um plugin PepperPy.

    Uso:
        @plugin
        class MyPlugin:
            pass

        @plugin(provides="processor")
        class TextProcessor:
            pass

        @plugin(depends_on=["OtherPlugin"])
        class DependentPlugin:
            pass

    Args:
        cls: A classe a ser decorada
        provides: Tipo de provedor (para plugins provedores)
        depends_on: Plugins dos quais este plugin depende

    Returns:
        A classe decorada como plugin
    """

    def decorator(cls):
        # Ensure the class inherits from PepperpyPlugin
        if not issubclass(cls, PepperpyPlugin):
            # Create a new class that inherits from PepperpyPlugin
            original_dict = {
                key: value
                for key, value in cls.__dict__.items()
                if key not in ("__dict__", "__weakref__")
            }

            if provides:
                # Provider plugins inherit from ProviderPlugin
                new_cls = type(
                    cls.__name__, (ProviderPlugin,) + cls.__bases__, original_dict
                )
                new_cls.provider_type = provides
            else:
                # Regular plugins inherit from PepperpyPlugin
                new_cls = type(
                    cls.__name__, (PepperpyPlugin,) + cls.__bases__, original_dict
                )

            # Copy metadata
            new_cls.__module__ = cls.__module__
            new_cls.__doc__ = cls.__doc__
            cls = new_cls
        elif provides and issubclass(cls, ProviderPlugin):
            # Add provider type to existing ProviderPlugin
            cls.provider_type = provides

        # Process dependencies
        if depends_on:
            if not hasattr(cls, "dependencies"):
                cls.dependencies = {}

            # Convert various dependency formats to dictionary
            if isinstance(depends_on, (list, tuple)):
                for dep in depends_on:
                    if isinstance(dep, str):
                        cls.dependencies[dep] = DependencyType.REQUIRED
                    elif isinstance(dep, dict):
                        cls.dependencies.update(dep)
                    else:
                        cls.dependencies[str(dep)] = DependencyType.REQUIRED
            elif isinstance(depends_on, dict):
                cls.dependencies.update(depends_on)
            else:
                cls.dependencies[str(depends_on)] = DependencyType.REQUIRED

        # Register plugin class
        _plugin_classes[cls.__name__] = cls

        # Add auto-registration to __init__
        original_init = cls.__init__

        @wraps(original_init)
        def init_wrapper(self, *args, **kwargs):
            # Call original init
            original_init(self, *args, **kwargs)

            # Ensure plugin_id exists
            if not hasattr(self, "plugin_id"):
                self.plugin_id = self.__class__.__name__

            # Register plugin instance
            _plugins[self.plugin_id] = self

            # Register services marked with @service
            for name in dir(self):
                attr = getattr(self, name)
                if callable(attr) and hasattr(attr, "_service_info"):
                    register_service(
                        self.plugin_id,
                        attr._service_info["name"],
                        attr,
                        attr._service_info["scope"],
                    )

        cls.__init__ = init_wrapper

        # Add dependency injection to method calls
        original_getattribute = cls.__getattribute__

        def getattribute_wrapper(self, name):
            attr = original_getattribute(self, name)

            # Only process methods marked for dependency injection
            if callable(attr) and hasattr(attr, "_inject_deps") and attr._inject_deps:
                sig = inspect.signature(attr)
                annotations = get_type_hints(attr)

                @wraps(attr)
                def method_wrapper(*args, **kwargs):
                    # Inject dependencies based on type annotations
                    for param_name, param in sig.parameters.items():
                        if param_name == "self" or param_name in kwargs:
                            continue

                        if param_name in annotations:
                            param_type = annotations[param_name]
                            type_name = getattr(param_type, "__name__", str(param_type))

                            # Check if this type corresponds to a plugin
                            if type_name in _plugin_classes:
                                # Inject plugin instance
                                plugin_instance = get_plugin(type_name)
                                if plugin_instance:
                                    kwargs[param_name] = plugin_instance

                    # Call original method with injected dependencies
                    return attr(*args, **kwargs)

                return method_wrapper

            return attr

        cls.__getattribute__ = getattribute_wrapper

        return cls

    # Allow usage as @plugin or @plugin()
    if cls is None:
        return decorator
    return decorator(cls)


def service(
    name_or_func=None,
    *,
    name: str | None = None,
    scope: ServiceScope = ServiceScope.PUBLIC,
):
    """
    Decorador para marcar um método como serviço disponível para outros plugins.

    Uso:
        @service
        def my_service(self):
            pass

        @service(name="custom_name")
        def another_service(self):
            pass

        @service(scope=ServiceScope.PRIVATE)
        def private_service(self):
            pass

    Args:
        name_or_func: Nome do serviço ou a função a ser decorada
        name: Nome do serviço (alternativa ao primeiro argumento)
        scope: Escopo de visibilidade do serviço

    Returns:
        O método decorado
    """

    def decorator(func):
        # Determine service name
        service_name = name or (
            name_or_func if isinstance(name_or_func, str) else func.__name__
        )

        # Store service info as attribute
        func._service_info = {"name": service_name, "scope": scope}

        # Mark for dependency injection
        func._inject_deps = True

        return func

    # Allow usage as @service, @service() or @service("name")
    if callable(name_or_func) and not isinstance(name_or_func, str):
        return decorator(name_or_func)
    return decorator


def event(event_type: str, priority: EventPriority = EventPriority.NORMAL):
    """
    Decorador para inscrever um método como manipulador de eventos.

    Uso:
        @event("user.login")
        def handle_login(self, user_data):
            pass

        @event("system.error", priority=EventPriority.HIGH)
        def handle_error(self, error_data):
            pass

    Args:
        event_type: Tipo de evento a ser manipulado
        priority: Prioridade do manipulador

    Returns:
        O método decorado
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Handle various parameter patterns
            if len(args) == 1:  # Just data
                return func(self, args[0])
            elif not args:  # No arguments
                return func(self)
            else:  # Pass everything through
                return func(self, *args, **kwargs)

        # Store metadata
        wrapper._event_handler = True
        wrapper._event_type = event_type
        wrapper._event_priority = priority

        # Mark for dependency injection
        wrapper._inject_deps = True

        return wrapper

    return decorator


def inject(cls_or_func=None):
    """
    Decorador para marcar um método para injeção automática de dependências.

    Uso:
        @inject
        def method(self, dependency: SomePlugin):
            # dependency é automaticamente injetado
            pass

        @inject
        class MyClass:
            # Todos os métodos terão injeção automática
            def method(self, dependency: SomePlugin):
                pass

    Args:
        cls_or_func: A classe ou função a ser decorada

    Returns:
        A classe ou função decorada
    """

    def decorator(cls_or_func):
        if inspect.isclass(cls_or_func):
            # For classes, decorate all methods
            for name, method in inspect.getmembers(cls_or_func, inspect.isfunction):
                setattr(cls_or_func, name, inject(method))
            return cls_or_func
        else:
            # For functions/methods, mark for injection
            cls_or_func._inject_deps = True
            return cls_or_func

    # Allow usage as @inject or @inject()
    if cls_or_func is None:
        return decorator
    return decorator(cls_or_func)


# Core utility functions
def get_plugin(plugin_id: str) -> PepperpyPlugin | None:
    """
    Obtém uma instância de plugin pelo ID.

    Args:
        plugin_id: ID do plugin

    Returns:
        Instância do plugin ou None se não encontrado
    """
    return _plugins.get(plugin_id)


async def initialize_plugins() -> None:
    """Inicializa todos os plugins registrados na ordem correta."""
    logger.info(f"Inicializando plugins ({len(_plugins)} registrados)")

    # TODO: Sort plugins by dependency order for proper initialization
    for plugin_id, plugin in _plugins.items():
        try:
            if asyncio.iscoroutinefunction(plugin.initialize):
                await plugin.initialize()
            else:
                plugin.initialize()
            logger.debug(f"Plugin inicializado: {plugin_id}")
        except Exception as e:
            logger.error(f"Erro ao inicializar plugin {plugin_id}: {e}")


async def cleanup_plugins() -> None:
    """Limpa todos os plugins registrados na ordem inversa."""
    logger.info("Limpando plugins")

    # Reverse order for cleanup
    plugin_ids = list(_plugins.keys())
    plugin_ids.reverse()

    for plugin_id in plugin_ids:
        plugin = _plugins.get(plugin_id)
        if not plugin:
            continue

        try:
            if asyncio.iscoroutinefunction(plugin.cleanup):
                await plugin.cleanup()
            else:
                plugin.cleanup()
            logger.debug(f"Plugin limpo: {plugin_id}")
        except Exception as e:
            logger.error(f"Erro ao limpar plugin {plugin_id}: {e}")


async def publish_event(event_type: str, data: Any = None) -> EventContext:
    """
    Publica um evento para todos os manipuladores registrados.

    Args:
        event_type: Tipo de evento
        data: Dados do evento

    Returns:
        Contexto do evento com resultados
    """
    logger.debug(f"Publicando evento: {event_type}")

    # Create event context
    context = EventContext(event_type, data)

    # Get handlers for this event type
    handlers = _event_handlers.get(event_type, [])

    # Sort by priority (highest first)
    handlers.sort(key=lambda h: h["priority"], reverse=True)

    # Call handlers
    for handler_info in handlers:
        if context.is_cancelled:
            break

        try:
            handler = handler_info["handler"]
            plugin = handler_info["plugin"]

            # Call handler with context
            result = handler(plugin, context, data)

            # Handle async handlers
            if asyncio.iscoroutine(result):
                result = await result

            # Add result if not None
            if result is not None:
                context.add_result(result)

        except Exception as e:
            logger.error(f"Erro no manipulador de evento {event_type}: {e}")

    return context


def register_service(
    plugin_id: str,
    service_name: str,
    handler: Callable,
    scope: ServiceScope = ServiceScope.PUBLIC,
) -> None:
    """
    Registra um serviço para um plugin.

    Args:
        plugin_id: ID do plugin
        service_name: Nome do serviço
        handler: Função do serviço
        scope: Escopo de visibilidade
    """
    if plugin_id not in _services:
        _services[plugin_id] = {}

    _services[plugin_id][service_name] = {"handler": handler, "scope": scope}

    logger.debug(f"Serviço registrado: {plugin_id}.{service_name} ({scope.value})")


async def call_service(
    plugin_id: str, service_name: str, *args: Any, **kwargs: Any
) -> Any:
    """
    Chama um serviço de um plugin.

    Args:
        plugin_id: ID do plugin
        service_name: Nome do serviço
        *args: Argumentos posicionais
        **kwargs: Argumentos nomeados

    Returns:
        Resultado do serviço

    Raises:
        ValueError: Se o serviço não for encontrado
    """
    # Check if plugin exists
    if plugin_id not in _services:
        raise ValueError(f"Plugin não encontrado: {plugin_id}")

    # Check if service exists
    if service_name not in _services[plugin_id]:
        raise ValueError(f"Serviço não encontrado: {plugin_id}.{service_name}")

    # Get service
    service_info = _services[plugin_id][service_name]
    handler = service_info["handler"]

    # Call service
    result = handler(*args, **kwargs)

    # Handle async services
    if asyncio.iscoroutine(result):
        result = await result

    return result


# Fluent PepperPy implementation
class PepperPy:
    """
    Classe principal do framework PepperPy.

    Fornece métodos fluidos para inicialização, configuração e uso do framework.

    Uso:
        # Uso básico
        app = PepperPy()
        await app.initialize()
        result = await app.execute("Normalizar texto", {"texto": "Exemplo"})
        await app.cleanup()

        # Uso com context manager
        async with PepperPy() as app:
            result = await app.execute("Normalizar texto", {"texto": "Exemplo"})

        # Uso fluido
        result = await (
            PepperPy()
            .with_plugin("text.normalizer", "basic")
            .with_config(lowercase=True)
            .normalize("Exemplo")
        )
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Inicializa o framework.

        Args:
            config: Configuração opcional
        """
        self.config = config or {}
        self._initialized = False
        self._plugins = _plugins
        self._current_plugin_type: str | None = None
        self._current_plugin_id: str | None = None
        self._current_config: dict[str, Any] = {}
        self._context: dict[str, Any] = {}

    async def __aenter__(self) -> Self:
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

    async def initialize(self) -> Self:
        """Inicializa o framework e seus componentes."""
        if self._initialized:
            return self

        logger.info(f"Inicializando framework PepperPy (Python {PYTHON_VERSION_STR})")

        # Initialize plugins
        await initialize_plugins()

        self._initialized = True
        logger.info("Framework PepperPy inicializado")
        return self

    async def cleanup(self) -> None:
        """Limpa o framework e todos os plugins."""
        if not self._initialized:
            return

        logger.info("Limpando framework PepperPy")

        # Clean up plugins
        await cleanup_plugins()

        self._initialized = False

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
        full_context = self._context.copy()
        if context:
            full_context.update(context)

        # Verificar se o framework está inicializado
        if not self._initialized:
            await self.initialize()

        logger.info(f"Executando query: {query}")

        # Aqui você implementaria a lógica real de processamento
        # Por enquanto, retorna um texto de exemplo com base na query
        if "texto" in full_context:
            texto = full_context["texto"]
            if "normalizar" in query.lower():
                return self._normalize_text_example(
                    texto, full_context.get("opcoes", {})
                )
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
            import re

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
        # Simulação de tradução
        return f"[Tradução] {texto}"

    # Métodos especializados para operações comuns
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

    def get_plugin_instance(
        self, plugin_type: str, plugin_id: str
    ) -> PepperpyPlugin | None:
        """
        Obtém uma instância de plugin.

        Args:
            plugin_type: Tipo de plugin
            plugin_id: ID do plugin

        Returns:
            Instância do plugin ou None se não encontrado
        """
        registry_key = f"{plugin_type}.{plugin_id}"
        return self._plugins.get(registry_key)

    def register_plugin(
        self, plugin: PepperpyPlugin | type[PepperpyPlugin]
    ) -> PepperpyPlugin | None:
        """
        Registra um plugin.

        Args:
            plugin: Instância ou classe do plugin

        Returns:
            Instância do plugin registrado ou None se falhar
        """
        if inspect.isclass(plugin):
            # É uma classe, instanciar
            try:
                instance = plugin()
                return instance
            except Exception as e:
                logger.error(f"Erro ao instanciar plugin {plugin.__name__}: {e}")
                return None
        else:
            # É uma instância, já registrada no __init__
            return plugin


# Instância singleton
_framework: PepperPy | None = None


def init_framework(config: dict[str, Any] | None = None) -> PepperPy:
    """
    Inicializa a instância singleton do framework.

    Args:
        config: Configuração opcional

    Returns:
        A instância do framework
    """
    global _framework

    if _framework is None:
        # Configurar logging
        configure_logging()
        _framework = PepperPy(config)

    return _framework


def get_pepperpy() -> PepperPy:
    """
    Obtém a instância singleton do framework.

    Returns:
        A instância do framework
    """
    if _framework is None:
        return init_framework()

    return _framework


# Factory functions for common operations
async def normalize(
    text: str,
    lowercase: bool = True,
    remove_punctuation: bool = False,
    remove_numbers: bool = False,
    remove_whitespace: bool = False,
) -> str:
    """
    Normaliza um texto.

    Args:
        text: Texto a ser normalizado
        lowercase: Converter para minúsculas
        remove_punctuation: Remover pontuação
        remove_numbers: Remover números
        remove_whitespace: Remover espaços extras

    Returns:
        Texto normalizado
    """
    app = get_pepperpy()
    return await app.normalize(
        text,
        lowercase=lowercase,
        remove_punctuation=remove_punctuation,
        remove_numbers=remove_numbers,
        remove_whitespace=remove_whitespace,
    )


async def summarize(text: str, length: str = "medium") -> str:
    """
    Resume um texto.

    Args:
        text: Texto a ser resumido
        length: Tamanho do resumo (short, medium, long)

    Returns:
        Texto resumido
    """
    app = get_pepperpy()
    return await app.summarize(text, length=length)


async def translate(text: str, target_language: str) -> str:
    """
    Traduz um texto.

    Args:
        text: Texto a ser traduzido
        target_language: Idioma alvo

    Returns:
        Texto traduzido
    """
    app = get_pepperpy()
    return await app.translate(text, target_language)


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
    app = get_pepperpy()
    return await app.process_file(input_path, output_path, operation, **options)


# Type export aliases for easier imports
Plugin = PepperpyPlugin
Provider = ProviderPlugin


# Função create para criar e configurar uma instância do framework
async def create(
    config: dict[str, Any] | None = None, auto_initialize: bool = True
) -> PepperPy:
    """
    Cria uma nova instância do framework.

    Args:
        config: Configuração opcional
        auto_initialize: Inicializar automaticamente

    Returns:
        Nova instância do framework
    """
    app = PepperPy(config)
    if auto_initialize:
        await app.initialize()
    return app


# Export public API
__all__ = [
    # Classes principais
    "PepperPy",
    "PepperpyPlugin",
    "ProviderPlugin",
    "EventContext",
    # Aliases de tipo
    "Plugin",
    "Provider",
    # Enums
    "DependencyType",
    "EventPriority",
    "ServiceScope",
    "ResourceType",
    # Protocolos
    "Initializable",
    "TextProcessor",
    "AIProvider",
    # Decoradores
    "plugin",
    "service",
    "event",
    "inject",
    # Funções de singleton
    "get_pepperpy",
    "init_framework",
    # Funções de criação
    "create",
    # Funções de utilidade
    "get_plugin",
    "initialize_plugins",
    "cleanup_plugins",
    "publish_event",
    "call_service",
    "register_service",
    # Funções simples
    "normalize",
    "summarize",
    "translate",
    "process_file",
]
