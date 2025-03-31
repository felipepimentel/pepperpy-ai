"""Exemplo de uso do plugin_manager com ambos formatos de plugins.

Este exemplo demonstra como usar o plugin_manager para criar providers
utilizando tanto o formato tradicional (category_service) quanto o 
formato hierárquico (category/service).
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar a biblioteca
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Importar o plugin_manager
    from pepperpy.plugin_manager import plugin_manager
except ImportError as e:
    print(f"Erro ao importar o plugin_manager: {e}")
    sys.exit(1)


def list_available_plugins():
    """Lista todos os plugins disponíveis e seus formatos."""
    print("\n===== Plugins Disponíveis =====")

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
        # Criar provider no formato tradicional
        # Exemplo: plugin_manager.create_provider("llm", "openai")
        print("# Criando provider com formato tradicional:")
        print("provider = plugin_manager.create_provider('llm', 'openai')")

        # Verificar se existe informação sobre o plugin
        info = plugin_manager.get_provider_info("llm", "openai")
        if info:
            print("\n✅ Plugin encontrado no formato tradicional")
            print("  Metadados:")
            print(f"    Formato: {info.get('format', 'flat')}")
            print(f"    Path: {info.get('path', 'N/A')}")
            print(
                f"    Descrição: {info.get('metadata', {}).get('description', 'N/A')}"
            )
        else:
            print("\n❌ Plugin não encontrado no formato tradicional")
    except Exception as e:
        print(f"\n❌ Erro ao usar plugin no formato tradicional: {e}")


def use_hierarchical_plugin():
    """Demonstra a criação de um provider usando o formato hierárquico."""
    print("\n===== Formato Hierárquico (category/service) =====")

    try:
        # Criar provider no formato hierárquico
        # Exemplo: plugin_manager.create_provider("embeddings/openai")
        print("# Criando provider com formato hierárquico:")
        print("provider = plugin_manager.create_provider('embeddings/openai')")

        # Verificar se existe informação sobre o plugin
        info = plugin_manager.get_provider_info("embeddings/openai")
        if info:
            print("\n✅ Plugin encontrado no formato hierárquico")
            print("  Metadados:")
            print(f"    Formato: {info.get('format', 'hierarchical')}")
            print(f"    Path: {info.get('path', 'N/A')}")
            print(
                f"    Descrição: {info.get('metadata', {}).get('description', 'N/A')}"
            )
        else:
            print("\n❌ Plugin não encontrado no formato hierárquico")
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
# Formato tradicional (category_service):
from pepperpy import plugin_manager

# Criar provider com categoria e tipo separados
llm = plugin_manager.create_provider("llm", "openai")

# Formato hierárquico (category/service):
from pepperpy import plugin_manager

# Criar provider com path unificado
embeddings = plugin_manager.create_provider("embeddings/openai")
    """
    )


if __name__ == "__main__":
    main()
