#!/usr/bin/env python
"""
Script para gerar um relatório atualizado da reestruturação do PepperPy.
"""

import os
from datetime import datetime
from pathlib import Path


def count_files_by_type():
    """
    Conta os arquivos por tipo no projeto.

    Returns:
        dict: Dicionário com contagem de arquivos por tipo
    """
    pepperpy_dir = Path("pepperpy")

    # Inicializa contadores
    counts = {
        "python_files": 0,
        "directories": 0,
        "init_files": 0,
        "stub_files": 0,
        "total_modules": 0,
    }

    # Percorre o diretório recursivamente
    for root, dirs, files in os.walk(pepperpy_dir):
        root_path = Path(root)

        # Conta diretórios
        counts["directories"] += len(dirs)

        # Conta módulos (diretórios com __init__.py)
        if "__init__.py" in files:
            counts["total_modules"] += 1

        # Conta arquivos por tipo
        for file in files:
            if file.endswith(".py"):
                counts["python_files"] += 1

                if file == "__init__.py":
                    counts["init_files"] += 1

                    # Verifica se é um stub
                    init_path = root_path / file
                    with open(init_path, "r") as f:
                        content = f.read()
                        if "Compatibility stub" in content and "import *" in content:
                            counts["stub_files"] += 1

    return counts


def generate_module_tree():
    """
    Gera uma representação em árvore dos módulos principais.

    Returns:
        str: Representação em árvore dos módulos
    """
    pepperpy_dir = Path("pepperpy")

    # Lista de módulos de primeiro nível a incluir
    main_modules = [
        "capabilities",
        "providers",
        "workflows",
        "core",
        "common",
        "agents",
        "rag",
        "llm",
    ]

    tree = ["pepperpy/"]

    # Adiciona módulos de primeiro nível
    for module in sorted(main_modules):
        module_path = pepperpy_dir / module
        if module_path.exists() and module_path.is_dir():
            tree.append(f"├── {module}/")

            # Adiciona submódulos (apenas um nível)
            submodules = [p for p in module_path.glob("*") if p.is_dir()]
            for i, submodule in enumerate(sorted(submodules)):
                if i == len(submodules) - 1:
                    tree.append(f"│   └── {submodule.name}/")
                else:
                    tree.append(f"│   ├── {submodule.name}/")

    return "\n".join(tree)


def generate_report():
    """
    Gera um relatório atualizado da reestruturação.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    counts = count_files_by_type()
    module_tree = generate_module_tree()

    report_path = Path("restructuring_report_updated.md")

    with open(report_path, "w") as f:
        f.write("# Relatório Atualizado de Reestruturação PepperPy\n\n")
        f.write(f"**Data**: {timestamp}\n\n")

        f.write("## Estatísticas do Projeto\n\n")
        f.write(f"- Arquivos Python: {counts['python_files']}\n")
        f.write(f"- Diretórios: {counts['directories']}\n")
        f.write(f"- Módulos (diretórios com __init__.py): {counts['total_modules']}\n")
        f.write(f"- Arquivos __init__.py: {counts['init_files']}\n")
        f.write(f"- Stubs de compatibilidade: {counts['stub_files']}\n\n")

        f.write("## Estrutura de Módulos\n\n")
        f.write(f"```\n{module_tree}\n```\n\n")

        f.write("## Alterações Realizadas\n\n")
        f.write("### 1. Padronização de Idioma\n")
        f.write(
            "Descrições de módulos padronizadas para o inglês para maior consistência.\n\n"
        )

        f.write("### 2. Sistemas de Erro Consolidados\n")
        f.write(
            "Os sistemas de erro duplicados em `common/errors` e `core/errors` foram consolidados em `core/errors`.\n\n"
        )

        f.write("### 3. Sistema de Provedores Unificado\n")
        f.write(
            "Os provedores espalhados pelo código foram centralizados em um único módulo `providers`.\n\n"
        )

        f.write("### 4. Workflows Reorganizados\n")
        f.write(
            "O sistema de workflows foi movido de `agents/workflows` para um módulo separado `workflows`.\n\n"
        )

        f.write("### 5. Implementações Consolidadas\n")
        f.write(
            "Arquivos de implementação redundantes foram consolidados em suas respectivas pastas.\n\n"
        )

        f.write("### 6. Fronteiras entre Common e Core\n")
        f.write(
            "Redefinição clara das responsabilidades entre os módulos `common` e `core`.\n\n"
        )

        f.write("### 7. Sistemas de Plugins Unificados\n")
        f.write(
            "Os plugins da CLI foram integrados ao sistema principal de plugins.\n\n"
        )

        f.write("### 8. Sistema de Cache Consolidado\n")
        f.write("As implementações redundantes de cache foram unificadas.\n\n")

        f.write("### 9. Organização de Módulos Padronizada\n")
        f.write(
            "Os módulos foram reorganizados por domínio funcional em vez de tipo técnico.\n\n"
        )

        f.write("## Compatibilidade\n\n")
        f.write(
            f"A reestruturação mantém compatibilidade com código existente através de stubs que redirecionam importações antigas para as novas localizações. Foram criados {counts['stub_files']} stubs de compatibilidade para garantir que projetos que dependem do PepperPy continuem funcionando sem alterações.\n\n"
        )

        f.write("## Próximos Passos\n\n")
        f.write(
            "1. **Atualizar Documentação**: Atualizar a documentação para refletir a nova estrutura do projeto.\n"
        )
        f.write(
            "2. **Atualizar Testes**: Verificar e atualizar os testes para garantir que funcionem com a nova estrutura.\n"
        )
        f.write(
            "3. **Remover Stubs Gradualmente**: Planejar a remoção gradual dos stubs de compatibilidade em versões futuras.\n"
        )
        f.write(
            "4. **Revisar Dependências Circulares**: Continuar monitorando e eliminando dependências circulares.\n"
        )

    print(f"Relatório atualizado gerado em: {report_path}")


if __name__ == "__main__":
    generate_report()
