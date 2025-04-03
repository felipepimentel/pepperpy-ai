"""
PepperPy Framework Core.

Este módulo fornece o ponto de entrada principal para o framework PepperPy,
com uma API simples e intuitiva para plugins, serviços e eventos.
"""

import inspect
import sys
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import (
    Any,
    TypeVar,
    Union,
    get_type_hints,
)


# Definir nossas próprias classes base e enums antes das importações
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

    async def initialize(self) -> None:
        """Inicializa o plugin."""
        pass

    async def cleanup(self) -> None:
        """Limpa recursos do plugin."""
        pass


class ProviderPlugin(PepperpyPlugin):
    """Classe base para plugins provedores."""

    pass


# Importações principais do sistema de plugins
try:
    # Usar importações renomeadas para evitar conflitos
    from pepperpy.core.config_manager import get_config
    from pepperpy.core.logging import configure_logging, get_logger
    from pepperpy.plugins.dependencies import add_dependency
    from pepperpy.plugins.events import EventContext as _EventContext
    from pepperpy.plugins.events import EventPriority as _EventPriority
    from pepperpy.plugins.events import publish as _publish
    from pepperpy.plugins.events import subscribe as _subscribe
    from pepperpy.plugins.integration import PluginManager as _PluginManager
    from pepperpy.plugins.integration import get_plugin_manager
    from pepperpy.plugins.plugin import DependencyType as _DependencyType
    from pepperpy.plugins.plugin import PepperpyPlugin as _PepperpyPlugin
    from pepperpy.plugins.plugin import ProviderPlugin as _ProviderPlugin
    from pepperpy.plugins.resources import ResourceType as _ResourceType
    from pepperpy.plugins.resources import get_resource, register_resource
    from pepperpy.plugins.services import ServiceScope as _ServiceScope
    from pepperpy.plugins.services import call_service, register_service
    from pepperpy.plugins.services import service as _service
except ImportError:
    # Para permitir uso mesmo se partes do sistema não estiverem disponíveis
    class _MockEnum:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return self.name

    class _DependencyType(_MockEnum):
        pass

    _DependencyType.REQUIRED = _DependencyType("required")

    class _EventPriority(_MockEnum):
        pass

    _EventPriority.NORMAL = _EventPriority("normal")

    class _ServiceScope(_MockEnum):
        pass

    _ServiceScope.PUBLIC = _ServiceScope("public")

    class _ResourceType(_MockEnum):
        pass

    _ResourceType.MEMORY = _ResourceType("memory")

    class _PepperpyPlugin:
        pass

    class _ProviderPlugin(_PepperpyPlugin):
        pass

    class _EventContext:
        def __init__(self, *args, **kwargs):
            self.event_id = "mock"
            self.canceled = False

    class _PluginManager:
        def __init__(self):
            pass

        def register_plugin(self, *args, **kwargs):
            pass

        def initialize_plugin(self, *args, **kwargs):
            pass

        def cleanup_plugin(self, *args, **kwargs):
            pass

    def _publish(*args, **kwargs):
        return _EventContext()

    def _subscribe(*args, **kwargs):
        pass

    def _service(*args, **kwargs):
        return lambda f: f

    def register_service(*args, **kwargs):
        pass

    def call_service(*args, **kwargs):
        return None

    def register_resource(*args, **kwargs):
        pass

    def get_resource(*args, **kwargs):
        return None

    def add_dependency(*args, **kwargs):
        pass

    def get_plugin_manager():
        return _PluginManager()

    def get_config(*args, **kwargs):
        return {}

    def configure_logging(*args, **kwargs):
        pass

    def get_logger(*args):
        return print


logger = get_logger(__name__)

# Record the Python version at startup
PYTHON_VERSION = sys.version_info
PYTHON_VERSION_STR = (
    f"{PYTHON_VERSION.major}.{PYTHON_VERSION.minor}.{PYTHON_VERSION.micro}"
)

# Armazenamento para plugins registrados
_plugins: dict[str, Any] = {}
_plugin_classes: dict[str, type] = {}
_dependencies: dict[str, dict[str, Any]] = {}
_services: dict[str, dict[str, Callable]] = {}
_event_handlers: dict[str, list[dict[str, Any]]] = {}

T = TypeVar("T")


def plugin(cls=None, **kwargs):
    """
    Decorador para definir uma classe como um plugin PepperPy.

    Args:
        cls: A classe a ser decorada
        provides: Tipo de provedor (para plugins provedores)
        depends_on: Lista de plugins dos quais este plugin depende

    Returns:
        A classe decorada como plugin
    """
    provides = kwargs.pop("provides", None)
    depends_on = kwargs.pop("depends_on", None)

    def decorator(cls):
        # Em vez de modificar __bases__, vamos criar um tipo derivado dinamicamente
        if provides:
            # Se fornece algum serviço, é um plugin provedor
            if not issubclass(cls, ProviderPlugin):
                # Criar uma nova classe que herda de ProviderPlugin e da classe original
                original_name = cls.__name__
                original_dict = dict(cls.__dict__)

                # Remover atributos especiais que não devem ser copiados
                for attr in ["__dict__", "__weakref__"]:
                    original_dict.pop(attr, None)

                # Criar nova classe
                new_cls = type(
                    original_name, (ProviderPlugin,) + cls.__bases__, original_dict
                )

                # Copiar docstring e outras propriedades importantes
                new_cls.__module__ = cls.__module__
                if hasattr(cls, "__doc__"):
                    new_cls.__doc__ = cls.__doc__

                cls = new_cls

            # Adicionar metadados de provedor como um atributo normal
            cls.provider_type = provides

        elif not issubclass(cls, PepperpyPlugin):
            # Se não é um plugin provedor nem deriva de PepperpyPlugin,
            # criar uma nova classe que herda de PepperpyPlugin
            original_name = cls.__name__
            original_dict = dict(cls.__dict__)

            # Remover atributos especiais que não devem ser copiados
            for attr in ["__dict__", "__weakref__"]:
                if attr in original_dict:
                    del original_dict[attr]

            # Criar nova classe
            new_cls = type(
                original_name, (PepperpyPlugin,) + cls.__bases__, original_dict
            )

            # Copiar docstring e outras propriedades importantes
            new_cls.__module__ = cls.__module__
            if hasattr(cls, "__doc__"):
                new_cls.__doc__ = cls.__doc__

            cls = new_cls

        # Registrar dependências como atributo normal da classe
        if depends_on:
            if not hasattr(cls, "dependencies"):
                cls.dependencies = {}

            if isinstance(depends_on, list) or isinstance(depends_on, tuple):
                for dep in depends_on:
                    if isinstance(dep, str):
                        cls.dependencies[dep] = DependencyType.REQUIRED
                    elif isinstance(dep, dict):
                        for dep_name, dep_type in dep.items():
                            cls.dependencies[dep_name] = dep_type
                    else:
                        cls.dependencies[dep] = DependencyType.REQUIRED
            else:
                cls.dependencies[depends_on] = DependencyType.REQUIRED

        # Registrar plugin na coleção
        plugin_id = cls.__name__
        _plugin_classes[plugin_id] = cls

        # Envolver o método __init__ para auto-registro
        original_init = cls.__init__

        @wraps(original_init)
        def init_wrapper(self, *args, **kwargs):
            # Chamar o inicializador original
            original_init(self, *args, **kwargs)

            # Definir plugin_id se não existir
            if not hasattr(self, "plugin_id"):
                self.plugin_id = self.__class__.__name__

            # Auto-registrar
            _plugins[self.plugin_id] = self

            # Adicionar serviços se definidos com decorador @service
            for name in dir(self):
                attr = getattr(self, name)
                if callable(attr) and hasattr(attr, "service_info"):
                    register_service(
                        self.plugin_id,
                        attr.service_info["name"],
                        attr,
                        attr.service_info["scope"],
                    )

        cls.__init__ = init_wrapper

        # Interceptar chamadas de métodos para injetar dependências automaticamente
        original_getattribute = cls.__getattribute__

        def getattribute_wrapper(self, name):
            # Obter o atributo normalmente
            attr = original_getattribute(self, name)

            # Apenas processar chamadas de métodos
            if callable(attr) and hasattr(attr, "inject_deps") and attr.inject_deps:
                # Obter as anotações de tipo do método
                sig = inspect.signature(attr)
                annotations = get_type_hints(attr)

                @wraps(attr)
                def method_wrapper(*args, **kwargs):
                    # Injetar dependências com base nos tipos
                    for param_name, param in sig.parameters.items():
                        if param_name == "self" or param_name in kwargs:
                            continue

                        if param_name in annotations:
                            param_type = annotations[param_name]
                            type_name = getattr(param_type, "__name__", str(param_type))

                            # Verificar se este tipo corresponde a um plugin
                            if type_name in _plugin_classes:
                                # Injetar a instância do plugin
                                plugin_instance = get_plugin(type_name)
                                if plugin_instance:
                                    kwargs[param_name] = plugin_instance

                    # Chamar o método original com as dependências injetadas
                    return attr(*args, **kwargs)

                return method_wrapper

            return attr

        cls.__getattribute__ = getattribute_wrapper

        return cls

    # Permitir uso como @plugin ou @plugin()
    if cls is None:
        return decorator
    return decorator(cls)


def service(name_or_func=None, **kwargs):
    """
    Decorador para marcar um método como serviço disponível para outros plugins.

    Args:
        name_or_func: Nome do serviço ou a função a ser decorada
        name: Nome do serviço (alternativa ao primeiro argumento)
        scope: Escopo de visibilidade do serviço

    Returns:
        O método decorado
    """
    name = kwargs.pop("name", None)
    scope = kwargs.pop("scope", ServiceScope.PUBLIC)

    def decorator(func):
        # Determinar o nome do serviço
        service_name = name or (
            name_or_func if isinstance(name_or_func, str) else func.__name__
        )

        # Armazenar informações do serviço como atributo normal
        func.service_info = {"name": service_name, "scope": scope}

        # Marcar para injeção de dependência
        func.inject_deps = True

        return func

    # Permitir uso como @service, @service() ou @service("nome")
    if callable(name_or_func) and not isinstance(name_or_func, str):
        return decorator(name_or_func)
    return decorator


def event(event_type, priority=EventPriority.NORMAL):
    """
    Decorador para inscrever um método como manipulador de eventos.

    Args:
        event_type: Tipo de evento a ser manipulado
        priority: Prioridade do manipulador

    Returns:
        O método decorado
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Permitir manipuladores com assinaturas flexíveis
            if len(args) == 3:  # Compatível com (event_type, context, data)
                return func(self, *args)
            elif len(args) == 1:  # Simplificado (data)
                return func(self, args[0])
            elif not args:  # Sem argumentos
                return func(self)
            else:
                return func(self, *args, **kwargs)

        # Armazenar metadados como atributos normais
        wrapper.event_handler = True
        wrapper.event_type = event_type
        wrapper.event_priority = priority

        # Marcar para injeção de dependência
        wrapper.inject_deps = True

        return wrapper

    return decorator


def inject(cls_or_func=None):
    """
    Decorador para marcar um método para injeção automática de dependências.

    Args:
        cls_or_func: A classe ou função a ser decorada

    Returns:
        A classe ou função decorada
    """

    def decorator(cls_or_func):
        if inspect.isclass(cls_or_func):
            # Para classes, decoramos todos os métodos
            for name, method in inspect.getmembers(cls_or_func, inspect.isfunction):
                setattr(cls_or_func, name, inject(method))
            return cls_or_func
        else:
            # Para funções/métodos, marcamos para injeção
            cls_or_func.inject_deps = True
            return cls_or_func

    # Permitir uso como @inject ou @inject()
    if cls_or_func is None:
        return decorator
    return decorator(cls_or_func)


def get_plugin(plugin_id: str) -> Any:
    """
    Obtém uma instância de plugin pelo ID.

    Args:
        plugin_id: ID do plugin

    Returns:
        Instância do plugin ou None se não encontrado
    """
    return _plugins.get(plugin_id)


def initialize_plugins() -> None:
    """Inicializa todos os plugins registrados na ordem correta."""
    # Obter gerenciador de plugins
    plugin_manager = get_plugin_manager()

    # Inicializar plugins em ordem de dependência
    for plugin_id, plugin in _plugins.items():
        try:
            if hasattr(plugin, "initialize"):
                plugin.initialize()
            else:
                plugin_manager.initialize_plugin(plugin_id)
        except Exception as e:
            logger.error(f"Erro ao inicializar plugin {plugin_id}: {e}")


async def cleanup_plugins() -> None:
    """Limpa todos os plugins registrados na ordem inversa."""
    # Obter gerenciador de plugins
    plugin_manager = get_plugin_manager()

    # Lista de plugins em ordem reversa
    plugin_ids = list(_plugins.keys())
    plugin_ids.reverse()

    # Limpar plugins
    for plugin_id in plugin_ids:
        plugin = _plugins.get(plugin_id)
        if not plugin:
            continue

        try:
            # Tentar async_cleanup primeiro
            if hasattr(plugin, "async_cleanup") and callable(plugin.async_cleanup):
                await plugin.async_cleanup()
            # Depois tentar cleanup normal
            elif hasattr(plugin, "cleanup") and callable(plugin.cleanup):
                plugin.cleanup()
            else:
                # Usar o gerenciador como fallback
                await plugin_manager.cleanup_plugin(plugin_id)
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
    # Criar contexto local
    context = EventContext(event_type, data)

    try:
        # Chamar o sistema de eventos subjacente
        internal_context = await _publish(event_type, "pepperpy", data)

        # Se chamada bem-sucedida, atualizar nosso contexto
        if hasattr(internal_context, "canceled"):
            context.cancelled = internal_context.canceled

        # Tentar extrair resultados
        if hasattr(internal_context, "results"):
            for result in internal_context.results.values():
                context.add_result(result)
    except Exception as e:
        logger.error(f"Erro ao publicar evento {event_type}: {e}")

    return context


class PepperPy:
    """
    Classe principal do framework PepperPy.

    Fornece métodos simplificados para inicialização, configuração e uso do framework.
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

    async def initialize(self) -> None:
        """Inicializa o framework e seus componentes."""
        if self._initialized:
            return

        logger.info(f"Inicializando framework PepperPy (Python {PYTHON_VERSION_STR})")

        # Inicializar plugins
        initialize_plugins()

        self._initialized = True
        logger.info("Framework PepperPy inicializado")

    async def execute(self, query: str, context: dict[str, Any] | None = None) -> Any:
        """
        Executa uma query com contexto.

        Args:
            query: Query do usuário
            context: Informações de contexto

        Returns:
            Resultado da execução da query
        """
        logger.info(f"Executando query: {query}")
        return f"PepperPy processou: {query}"

    async def cleanup(self) -> None:
        """Limpa o framework e todos os plugins."""
        if not self._initialized:
            return

        logger.info("Limpando framework PepperPy")

        # Limpar plugins
        await cleanup_plugins()

        self._initialized = False

    def get_plugin_instance(self, plugin_type: str, name: str) -> Any:
        """Get a plugin instance by type and name.

        Args:
            plugin_type: Type of plugin
            name: Name of plugin instance

        Returns:
            Plugin instance if found, None otherwise
        """
        registry_key = f"{plugin_type}.{name}"
        return self._plugins.get(registry_key)

    def register_plugin(
        self, plugin: Union["PepperpyPlugin", type["PepperpyPlugin"]]
    ) -> None:
        """Register a plugin with the framework.

        Args:
            plugin: Plugin instance or class to register
        """
        # Implement plugin registration logic here
        pass


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


# Exportar decoradores e funções principais da API
__all__ = [
    "DependencyType",
    "EventPriority",
    "PepperPy",
    "ResourceType",
    "ServiceScope",
    "cleanup_plugins",
    "event",
    "get_pepperpy",
    "get_plugin",
    "init_framework",
    "initialize_plugins",
    "inject",
    "plugin",
    "publish_event",
    "service",
]
