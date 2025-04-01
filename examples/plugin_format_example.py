"""Exemplo de uso do sistema de descoberta de plugins com ambos formatos de plugins.

Este exemplo demonstra como usar o sistema de descoberta de plugins aprimorado para criar providers
utilizando tanto o formato tradicional (category_service) quanto o
formato hierárquico (category/service).
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar a biblioteca
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Importar o sistema de descoberta de plugins aprimorado
    # Importar plugin_manager para compatibilidade com versões anteriores
    from pepperpy.plugins import PluginManager
    from pepperpy.plugins.discovery import (
        PluginInfo,
        PluginLoadError,
        PluginRegistry,
        PluginValidationError,
        create_provider_instance,
        discover_plugins,
        get_plugin,
        get_plugin_by_provider,
        get_plugin_registry,
    )
except ImportError as e:
    print(f"Erro ao importar o sistema de descoberta de plugins: {e}")
    sys.exit(1)


def list_available_plugins():
    """Lista todos os plugins disponíveis e seus formatos."""
    print("\n===== Plugins Disponíveis =====")

    # Usar o sistema de descoberta de plugins aprimorado
    plugin_registry = get_plugin_registry()

    # Descobrir plugins (garante que o registro está atualizado)
    plugin_registry.discover_plugins()

    # Listar categorias de plugins
    categories = plugin_registry.list_categories()

    for category in categories:
        plugins = plugin_registry.get_plugins_by_category(category)
        if not plugins:
            continue

        print(f"\nCategoria: {category}")

        # Listar todos os providers desta categoria
        providers = plugin_registry.list_providers(category)
        for provider_name in providers:
            # Obter informações detalhadas do plugin
            plugin_info = get_plugin_by_provider(category, provider_name)
            if plugin_info:
                is_hierarchical = "/" in plugin_info.name
                format_type = "hierarchical" if is_hierarchical else "flat"
                print(f"  - {provider_name} ({format_type})")
                print(f"    Descrição: {plugin_info.description}")

    # Também mostrar usando o plugin_manager para compatibilidade
    print("\n----- Usando o plugin_manager (legado) -----")
    plugins = plugin_manager.list_plugins()
    for category, providers in plugins.items():
        if not providers:
            continue

        print(f"\nCategoria: {category}")
        for provider_name, info in providers.items():
            format_type = info.get("format", "flat")
            print(f"  - {provider_name} ({format_type})")
            print(
                f"    Descrição: {info.get('metadata', {}).get('description', 'N/A')}"
            )


def use_traditional_plugin():
    """Demonstra a criação de um provider usando o formato tradicional."""
    print("\n===== Formato Tradicional (category_service) =====")

    try:
        # Criar provider no formato tradicional usando o sistema de descoberta de plugins aprimorado
        print("# Criando provider com formato tradicional usando o sistema aprimorado:")
        print("provider = create_provider_instance('llm', 'openai')")

        # Verificar se existe informação sobre o plugin
        plugin_info = get_plugin_by_provider("llm", "openai")
        if plugin_info:
            print("\n✅ Plugin encontrado no formato tradicional")
            print("  Metadados:")
            is_hierarchical = "/" in plugin_info.name
            format_type = "hierarchical" if is_hierarchical else "flat"
            print(f"    Formato: {format_type}")
            print(f"    Path: {plugin_info.path}")
            print(f"    Descrição: {plugin_info.description}")
            print(f"    Versão: {plugin_info.version}")
        else:
            print(
                "\n❌ Plugin não encontrado no formato tradicional no sistema aprimorado"
            )

            # Tentar com o plugin_manager para compatibilidade
            print("\n# Tentando com o plugin_manager (legado):")
            info = plugin_manager.get_provider_info("llm", "openai")
            if info:
                print("✅ Plugin encontrado no formato tradicional via plugin_manager")
                print("  Metadados:")
                print(f"    Formato: {info.get('format', 'flat')}")
                print(f"    Path: {info.get('path', 'N/A')}")
                print(
                    f"    Descrição: {info.get('metadata', {}).get('description', 'N/A')}"
                )
            else:
                print("❌ Plugin não encontrado no formato tradicional")
    except Exception as e:
        print(f"\n❌ Erro ao usar plugin no formato tradicional: {e}")


def use_hierarchical_plugin():
    """Demonstra a criação de um provider usando o formato hierárquico."""
    print("\n===== Formato Hierárquico (category/service) =====")

    try:
        # Criar provider no formato hierárquico usando o sistema de descoberta de plugins aprimorado
        print("# Criando provider com formato hierárquico usando o sistema aprimorado:")
        print("provider = create_provider_instance('embeddings', 'openai')")

        # Nota: O sistema de descoberta de plugins aprimorado usa o formato
        # de categoria e provider separadamente, não o formato hierárquico com /

        # Verificar se existe informação sobre o plugin
        plugin_info = get_plugin_by_provider("embeddings", "openai")
        if plugin_info:
            print("\n✅ Plugin encontrado no formato aprimorado")
            print("  Metadados:")
            is_hierarchical = "/" in plugin_info.name
            format_type = "hierarchical" if is_hierarchical else "flat"
            print(f"    Formato interno: {format_type}")
            print(f"    Path: {plugin_info.path}")
            print(f"    Descrição: {plugin_info.description}")
            print(f"    Versão: {plugin_info.version}")
        else:
            print("\n❌ Plugin não encontrado no sistema aprimorado")

        # Também verificar usando o plugin_manager para compatibilidade
        print("\n# Verificando também com o plugin_manager (legado):")
        info = plugin_manager.get_provider_info("embeddings/openai")
        if info:
            print("✅ Plugin encontrado no formato hierárquico via plugin_manager")
            print("  Metadados:")
            print(f"    Formato: {info.get('format', 'hierarchical')}")
            print(f"    Path: {info.get('path', 'N/A')}")
            print(
                f"    Descrição: {info.get('metadata', {}).get('description', 'N/A')}"
            )
        else:
            print("❌ Plugin não encontrado no formato hierárquico via plugin_manager")
    except Exception as e:
        print(f"\n❌ Erro ao usar plugin no formato hierárquico: {e}")


def main():
    """Função principal do exemplo."""
    print("===== Exemplo de Uso de Plugins em Ambos Formatos =====")

    # Listar plugins disponíveis
    list_available_plugins()

    # Demonstrar uso de formato tradicional
    use_traditional_plugin()

    # Demonstrar uso de formato hierárquico
    use_hierarchical_plugin()

    print("\n===== Como Usar Plugins em Seu Código =====")
    print(
        """
# Usando o sistema de descoberta de plugins aprimorado:
from pepperpy import create_provider_instance

# Criar provider com categoria e tipo separados
llm = create_provider_instance("llm", "openai")

# Criar provider de embeddings
embeddings = create_provider_instance("embeddings", "openai")

# Criar providers em outro estilo:
# llm = create_provider_instance(category="llm", provider_name="openai")
# embeddings = create_provider_instance(category="embeddings", provider_name="openai")
    """
    )


if __name__ == "__main__":
    main()
