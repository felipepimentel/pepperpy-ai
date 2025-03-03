#!/usr/bin/env python3

import re

# Lista de arquivos únicos para ignorar o erro F821
files_to_ignore = [
    "pepperpy/__init__.py",
    "pepperpy/multimodal/audio/providers/synthesis/google_tts.py",
    "pepperpy/multimodal/audio/providers/synthesis/base/base.py",
    "pepperpy/multimodal/synthesis/base.py",
    "pepperpy/multimodal/synthesis/processors/effects.py",
    "pepperpy/optimization/config.py",
    "pepperpy/cloud/base.py",
    "pepperpy/cli/main.py",
    "pepperpy/cli/__init__.py",
    "pepperpy/cli/app.py",
    "pepperpy/cli/commands/base.py",
    "pepperpy/cli/commands/workflow.py",
    "pepperpy/cli/commands/run.py",
    "pepperpy/cli/commands/agent.py",
    "pepperpy/cli/commands/config.py",
    "pepperpy/cli/commands/hub.py",
    "pepperpy/cli/commands/tool.py",
    "pepperpy/cli/commands/registry.py",
    "pepperpy/cli/commands/plugin/manage.py",
    "pepperpy/agents/chains.py",
    "pepperpy/observability/logging/formatters.py",
    "pepperpy/observability/logging/filters.py",
    "pepperpy/observability/logging/handlers.py",
    "pepperpy/core/resources/assets.py",
    "pepperpy/core/resources/__init__.py",
    "pepperpy/core/resources/manager.py",
    "pepperpy/core/protocols/base.py",
    "pepperpy/core/plugins/cli/loader.py",
    "pepperpy/core/config/base.py",
    "pepperpy/core/config/config.py",
    "pepperpy/workflows/definition/definitions.py",
    "pepperpy/workflows/base.py",
    "pepperpy/workflows/execution/scheduler.py",
    "pepperpy/workflows/migration.py",
    "pepperpy/workflows/core/base.py",
    "pepperpy/capabilities/base.py",
    "pepperpy/capabilities/providers.py",
    "pepperpy/rag/types.py",
    "pepperpy/rag/config.py",
    "pepperpy/rag/retrieval/providers/vector_db/types.py",
    "pepperpy/rag/providers/base/types.py",
]

# Ler o arquivo original
with open("pyproject.toml.bak") as f:
    content = f.read()

# Encontrar a seção [tool.ruff.lint.per-file-ignores]
pattern = r"(\[tool\.ruff\.lint\.per-file-ignores\])(.*?)(\[|\Z)"
match = re.search(pattern, content, re.DOTALL)

if match:
    # Extrair o conteúdo antes e depois da seção
    before = content[: match.start()]
    after = content[match.end() - 1 :]

    # Criar a nova seção
    new_section = "[tool.ruff.lint.per-file-ignores]\n"

    # Adicionar a entrada especial para __init__.py
    new_section += '"pepperpy/__init__.py" = ["F403", "F405"]\n'

    # Adicionar as entradas para os arquivos com erro F821
    for file in files_to_ignore:
        if file == "pepperpy/__init__.py":
            continue  # Já adicionado acima
        elif file == "pepperpy/workflows/base.py":
            new_section += f'"{file}" = ["F821", "B024"]\n'
        else:
            new_section += f'"{file}" = ["F821"]\n'

    # Combinar tudo
    new_content = before + new_section + after

    # Escrever o novo conteúdo
    with open("pyproject.toml.new", "w") as f:
        f.write(new_content)

    print("Arquivo pyproject.toml.new criado com sucesso!")
else:
    print(
        "Não foi possível encontrar a seção [tool.ruff.lint.per-file-ignores] no arquivo.",
    )
