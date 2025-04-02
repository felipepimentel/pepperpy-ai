import importlib
import importlib.util
import inspect
import os
import sys
from typing import Any, Dict, List, Optional, Set, Type

from pepperpy.core.errors import ValidationError
from pepperpy.core.logging import get_logger
from pepperpy.plugins.base import PepperpyPlugin

logger = get_logger(__name__)

# Cache de módulos carregados com tempos de modificação
_module_cache: Dict[str, Dict[str, Any]] = {}
_plugin_dependencies: Dict[str, Set[str]] = {}
_hot_reload_enabled = False
_autodiscovery_enabled = True


def enable_hot_reload(enabled: bool = True) -> None:
    """Habilita ou desabilita o hot-reload de plugins.

    Quando habilitado, os plugins são recarregados automaticamente
    quando seus arquivos fonte são modificados.

    Args:
        enabled: Se o hot-reload deve ser habilitado
    """
    global _hot_reload_enabled
    _hot_reload_enabled = enabled
    logger.info(f"Hot-reload de plugins {'habilitado' if enabled else 'desabilitado'}")


def set_autodiscovery(enabled: bool = True) -> None:
    """Habilita ou desabilita a descoberta automática de plugins.

    Args:
        enabled: Se a descoberta automática deve ser habilitada
    """
    global _autodiscovery_enabled
    _autodiscovery_enabled = enabled
    logger.info(
        f"Autodiscovery de plugins {'habilitado' if enabled else 'desabilitado'}"
    )


def is_plugin_module(module_name: str) -> bool:
    """Verifica se um módulo é um possível módulo de plugin.

    Args:
        module_name: Nome do módulo a verificar

    Returns:
        True se for um possível módulo de plugin
    """
    return (
        not module_name.startswith("_")
        and not module_name.startswith("test")
        and not module_name.startswith("setup")
    )


def get_file_modified_time(file_path: str) -> float:
    """Obtém o tempo de modificação de um arquivo.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        Timestamp da última modificação
    """
    if not os.path.exists(file_path):
        return 0
    return os.path.getmtime(file_path)


def needs_reload(module_path: str) -> bool:
    """Verifica se um módulo precisa ser recarregado.

    Args:
        module_path: Caminho do módulo

    Returns:
        True se o módulo precisa ser recarregado
    """
    if not _hot_reload_enabled or module_path not in _module_cache:
        return True

    cached_info = _module_cache[module_path]
    current_mtime = get_file_modified_time(cached_info["file"])

    # Recarregar se o arquivo foi modificado
    if current_mtime > cached_info["mtime"]:
        return True

    # Verificar também as dependências
    if module_path in _plugin_dependencies:
        for dep_path in _plugin_dependencies[module_path]:
            if dep_path in _module_cache:
                dep_info = _module_cache[dep_path]
                dep_mtime = get_file_modified_time(dep_info["file"])
                if dep_mtime > dep_info["mtime"]:
                    return True

    return False


def load_module(module_path: str, reload: bool = False) -> Optional[Any]:
    """Carrega um módulo Python pelo caminho do arquivo.

    Args:
        module_path: Caminho para o arquivo do módulo
        reload: Se deve forçar o recarregamento

    Returns:
        Módulo carregado ou None se falhar
    """
    if not os.path.exists(module_path):
        logger.warning(f"Módulo não encontrado: {module_path}")
        return None

    # Verificar se precisamos recarregar
    if not reload and module_path in _module_cache and not needs_reload(module_path):
        return _module_cache[module_path]["module"]

    # Obter nome e especificação do módulo
    module_name = os.path.basename(module_path)
    if module_name.endswith(".py"):
        module_name = module_name[:-3]

    # Usar caminho absoluto para evitar conflitos
    abs_path = os.path.abspath(module_path)

    try:
        # Carregar a especificação do módulo
        spec = importlib.util.spec_from_file_location(module_name, abs_path)
        if spec is None or spec.loader is None:
            logger.warning(f"Não foi possível carregar spec para: {module_path}")
            return None

        # Criar e carregar o módulo
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Armazenar no cache
        _module_cache[module_path] = {
            "module": module,
            "file": abs_path,
            "mtime": get_file_modified_time(abs_path),
            "name": module_name,
        }

        # Registrar dependências
        _update_module_dependencies(module_path, module)

        return module
    except Exception as e:
        logger.error(f"Erro ao carregar módulo {module_path}: {e}")
        return None


def _update_module_dependencies(module_path: str, module: Any) -> None:
    """Atualiza o registro de dependências de um módulo.

    Args:
        module_path: Caminho do módulo
        module: Módulo carregado
    """
    dependencies = set()

    # Registrar módulos importados como dependências
    for name, obj in inspect.getmembers(module):
        if inspect.ismodule(obj):
            mod_file = getattr(obj, "__file__", None)
            if mod_file:
                dependencies.add(mod_file)

    _plugin_dependencies[module_path] = dependencies


def discover_plugin_files(
    directory: str, plugin_type: Optional[str] = None
) -> List[str]:
    """Descobre arquivos de plugin em um diretório.

    Args:
        directory: Diretório para procurar
        plugin_type: Tipo opcional de plugin para filtrar

    Returns:
        Lista de caminhos para arquivos de plugin
    """
    plugin_files = []

    if not os.path.exists(directory) or not os.path.isdir(directory):
        return plugin_files

    # Se temos um tipo específico de plugin, procurar nessa subpasta
    search_dir = directory
    if plugin_type:
        type_dir = os.path.join(directory, plugin_type)
        if os.path.exists(type_dir) and os.path.isdir(type_dir):
            search_dir = type_dir

    # Procurar arquivos de plugin
    for root, dirs, files in os.walk(search_dir):
        # Ignorar diretórios ocultos e de testes
        dirs[:] = [d for d in dirs if not d.startswith((".", "_", "test"))]

        for file in files:
            if file == "provider.py":
                plugin_files.append(os.path.join(root, file))
            elif file.endswith(".py") and not file.startswith((".", "_", "test")):
                # Arquivos que podem conter plugins
                if "plugin" in file.lower() or "provider" in file.lower():
                    plugin_files.append(os.path.join(root, file))

    return plugin_files


def find_plugin_class(module: Any) -> Optional[Type[PepperpyPlugin]]:
    """Encontra a classe de plugin em um módulo.

    Args:
        module: Módulo a ser analisado

    Returns:
        Classe de plugin ou None se não encontrada
    """
    # Procurar por classes que herdam de PepperpyPlugin
    plugin_classes = []

    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and issubclass(obj, PepperpyPlugin)
            and obj != PepperpyPlugin
        ):
            # Verificar se é uma classe concreta
            if not inspect.isabstract(obj):
                plugin_classes.append(obj)

    # Se houver apenas uma classe de plugin, retorná-la
    if len(plugin_classes) == 1:
        return plugin_classes[0]

    # Se houver múltiplas, priorizar as que têm Provider ou Plugin no nome
    for cls in plugin_classes:
        if "Provider" in cls.__name__ or "Plugin" in cls.__name__:
            return cls

    # Se ainda não encontrou, retornar a primeira
    if plugin_classes:
        return plugin_classes[0]

    return None


def validate_plugin_config(
    plugin_class: Type[PepperpyPlugin], config: Dict[str, Any]
) -> Dict[str, Any]:
    """Valida a configuração de um plugin.

    Args:
        plugin_class: Classe do plugin
        config: Configuração a ser validada

    Returns:
        Configuração validada

    Raises:
        ValidationError: Se a configuração for inválida
    """
    # Se o plugin tem um método de validação, usá-lo
    if hasattr(plugin_class, "validate_config") and callable(
        plugin_class.validate_config
    ):
        try:
            return plugin_class.validate_config(config)
        except Exception as e:
            raise ValidationError(f"Erro validando configuração: {e}")

    # Verificar parâmetros obrigatórios baseado no __init__
    try:
        init_params = inspect.signature(plugin_class.__init__).parameters
        required_params = {
            name
            for name, param in init_params.items()
            if param.default == inspect.Parameter.empty and name != "self"
        }

        # Verificar se todos os parâmetros obrigatórios existem
        for param in required_params:
            if param not in config and param != "kwargs":
                raise ValidationError(f"Parâmetro obrigatório ausente: {param}")

        return config
    except Exception as e:
        if not isinstance(e, ValidationError):
            raise ValidationError(f"Erro validando configuração: {e}")
        raise


def load_plugin_from_file(
    file_path: str,
    plugin_type: str,
    provider_type: str,
    config: Optional[Dict[str, Any]] = None,
) -> Optional[Type[PepperpyPlugin]]:
    """Carrega um plugin de um arquivo.

    Args:
        file_path: Caminho do arquivo de plugin
        plugin_type: Tipo de plugin
        provider_type: Tipo de provedor
        config: Configuração opcional

    Returns:
        Classe de plugin ou None se falhar
    """
    # Carregar o módulo
    module = load_module(file_path, reload=needs_reload(file_path))
    if not module:
        return None

    # Encontrar a classe de plugin
    plugin_class = find_plugin_class(module)
    if not plugin_class:
        logger.warning(f"Nenhuma classe de plugin encontrada em {file_path}")
        return None

    # Validar configuração se fornecida
    if config:
        config = validate_plugin_config(plugin_class, config)

    # Registrar metadados no plugin
    plugin_class.plugin_type = plugin_type
    plugin_class.provider_type = provider_type
    plugin_class.plugin_file = file_path

    return plugin_class


def scan_plugin_directory(directory: str) -> Dict[str, Dict[str, List[str]]]:
    """Escaneia um diretório em busca de plugins disponíveis.

    Args:
        directory: Diretório para escanear

    Returns:
        Dicionário de tipos de plugin -> tipos de provedor -> caminhos
    """
    plugins = {}

    if not os.path.exists(directory) or not os.path.isdir(directory):
        return plugins

    # Buscar em subdiretórios de primeiro nível (plugin_type)
    for plugin_type in os.listdir(directory):
        type_dir = os.path.join(directory, plugin_type)
        if not os.path.isdir(type_dir) or plugin_type.startswith((".", "_", "test")):
            continue

        plugins[plugin_type] = {}

        # Buscar em subdiretórios de segundo nível (provider_type)
        for provider_type in os.listdir(type_dir):
            provider_dir = os.path.join(type_dir, provider_type)
            if not os.path.isdir(provider_dir) or provider_type.startswith(
                (".", "_", "test")
            ):
                continue

            # Procurar pelo arquivo provider.py
            provider_file = os.path.join(provider_dir, "provider.py")
            if os.path.exists(provider_file):
                if plugin_type not in plugins:
                    plugins[plugin_type] = {}
                if provider_type not in plugins[plugin_type]:
                    plugins[plugin_type][provider_type] = []
                plugins[plugin_type][provider_type].append(provider_file)

    return plugins


def check_dependencies(plugin_class: Type[PepperpyPlugin]) -> bool:
    """Verifica se as dependências de um plugin estão instaladas.

    Args:
        plugin_class: Classe de plugin

    Returns:
        True se todas as dependências estão disponíveis
    """
    # Se o plugin define as dependências
    if hasattr(plugin_class, "dependencies") and plugin_class.dependencies:
        missing = []

        for dependency in plugin_class.dependencies:
            try:
                importlib.import_module(dependency)
            except ImportError:
                missing.append(dependency)

        if missing:
            logger.warning(
                f"Plugin {plugin_class.__name__} tem dependências não instaladas: {', '.join(missing)}"
            )
            return False

    return True


def get_plugin_metadata(plugin_class: Type[PepperpyPlugin]) -> Dict[str, Any]:
    """Obtém metadados de um plugin.

    Args:
        plugin_class: Classe de plugin

    Returns:
        Dicionário com metadados do plugin
    """
    return {
        "name": getattr(plugin_class, "plugin_name", plugin_class.__name__),
        "type": getattr(plugin_class, "plugin_type", "unknown"),
        "provider_type": getattr(plugin_class, "provider_type", "unknown"),
        "description": getattr(plugin_class, "__doc__", ""),
        "version": getattr(plugin_class, "version", "0.1.0"),
        "author": getattr(plugin_class, "author", "Unknown"),
        "dependencies": getattr(plugin_class, "dependencies", []),
        "file": getattr(plugin_class, "plugin_file", None),
    }
