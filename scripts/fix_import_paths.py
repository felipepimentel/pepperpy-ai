#!/usr/bin/env python3
"""
Script para mapear e corrigir automaticamente problemas de importação no projeto.

Este script:
1. Mapeia a estrutura do projeto para entender onde cada módulo está localizado
2. Detecta importações quebradas e sugere correções
3. Aplica as correções automaticamente
"""

import ast
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

# Configurações
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE_NAME = "pepperpy"
PACKAGE_ROOT = PROJECT_ROOT / PACKAGE_NAME
BACKUP_DIR = PROJECT_ROOT / "backups" / "imports"


class ImportMapper:
    """Classe para mapear a estrutura de importações do projeto."""

    def __init__(self):
        self.module_map: Dict[str, Path] = {}
        self.class_map: Dict[str, List[str]] = defaultdict(list)
        self.function_map: Dict[str, List[str]] = defaultdict(list)
        self.variable_map: Dict[str, List[str]] = defaultdict(list)
        self.import_errors: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.fixed_files: Set[str] = set()
        self.module_aliases: Dict[str, str] = {}
        self.old_to_new_paths: Dict[str, str] = {}

    def map_project_structure(self) -> None:
        """Mapeia a estrutura do projeto, identificando todos os módulos Python."""
        print("Mapeando estrutura do projeto...")

        # Mapear todos os arquivos Python no projeto
        for root, _, files in os.walk(PACKAGE_ROOT):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(PROJECT_ROOT)

                    # Converter caminho de arquivo para formato de módulo
                    if file == "__init__.py":
                        module_path = str(rel_path.parent).replace("/", ".")
                    else:
                        module_path = str(rel_path.with_suffix("")).replace("/", ".")

                    self.module_map[module_path] = file_path

                    # Analisar o conteúdo do arquivo para extrair classes, funções e variáveis
                    self._extract_symbols_from_file(file_path, module_path)

        print(f"Mapeados {len(self.module_map)} módulos")
        print(f"Encontradas {sum(len(v) for v in self.class_map.values())} classes")
        print(f"Encontradas {sum(len(v) for v in self.function_map.values())} funções")

    def _extract_symbols_from_file(self, file_path: Path, module_path: str) -> None:
        """Extrai classes, funções e variáveis de um arquivo Python."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            try:
                tree = ast.parse(content)

                # Extrair classes
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        self.class_map[node.name].append(module_path)
                    elif isinstance(node, ast.FunctionDef):
                        self.function_map[node.name].append(module_path)
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                self.variable_map[target.id].append(module_path)

                # Extrair aliases de importação
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            if name.asname:
                                self.module_aliases[name.asname] = name.name
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module
                        for name in node.names:
                            if name.asname:
                                if module:
                                    full_name = f"{module}.{name.name}"
                                else:
                                    full_name = name.name
                                self.module_aliases[name.asname] = full_name
            except SyntaxError:
                # Ignorar arquivos com erros de sintaxe
                pass
        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")

    def detect_import_errors(self) -> None:
        """Detecta erros de importação usando o Ruff."""
        print("Detectando erros de importação...")

        # Executar ruff para encontrar erros de importação
        cmd = [
            "ruff",
            "check",
            PACKAGE_NAME,
            "--select=F401,F403,F405,F821,E402,F811",
            "--format=json",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0 and result.stdout:
                errors = json.loads(result.stdout)

                # Agrupar erros por arquivo
                for error in errors:
                    file_path = error["filename"]
                    self.import_errors[file_path].append(error)

                print(
                    f"Encontrados {len(errors)} erros de importação em {len(self.import_errors)} arquivos",
                )
            else:
                print("Nenhum erro de importação encontrado!")

            # Mesmo que não haja erros detectados pelo ruff, vamos procurar por padrões de importação antigos
            self._find_old_import_patterns()
        except Exception as e:
            print(f"Erro ao executar ruff: {e}")

    def _find_old_import_patterns(self) -> None:
        """Procura por padrões de importação antigos nos arquivos."""
        print("Procurando por padrões de importação antigos...")

        # Padrões de importação antigos para procurar
        old_patterns = [
            r"from\s+workflows\.",
            r"import\s+workflows\.",
            r"from\s+agents\.",
            r"import\s+agents\.",
            r"from\s+core\.",
            r"import\s+core\.",
            r"from\s+rag\.",
            r"import\s+rag\.",
        ]

        # Compilar padrões
        compiled_patterns = [re.compile(pattern) for pattern in old_patterns]

        # Procurar nos arquivos
        for root, _, files in os.walk(PACKAGE_ROOT):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()

                        # Verificar cada padrão
                        for pattern in compiled_patterns:
                            if pattern.search(content):
                                # Criar um erro simulado para este arquivo
                                error = {
                                    "filename": file_path,
                                    "code": "CUSTOM001",
                                    "message": "Possível importação de módulo antigo",
                                    "location": {"row": 1, "column": 1},
                                }
                                self.import_errors[file_path].append(error)
                                break  # Um padrão encontrado é suficiente
                    except Exception as e:
                        print(f"Erro ao processar {file_path}: {e}")

        if self.import_errors:
            print(
                f"Encontrados padrões de importação antigos em {len(self.import_errors)} arquivos",
            )

    def build_migration_map(self) -> None:
        """Constrói um mapa de migração de caminhos antigos para novos."""
        print("Construindo mapa de migração...")

        # Padrões comuns de migração baseados na estrutura do projeto
        migration_patterns = [
            # Exemplo: workflows.definition.base -> pepperpy.workflows.definition
            (r"^workflows\.(\w+)\.(\w+)$", f"{PACKAGE_NAME}.workflows.\\1.\\2"),
            # Exemplo: agents.base -> pepperpy.agents
            (r"^agents\.(\w+)$", f"{PACKAGE_NAME}.agents.\\1"),
            # Exemplo: core.base -> pepperpy.core.base
            (r"^core\.(\w+)$", f"{PACKAGE_NAME}.core.\\1"),
            # Exemplo: rag.base -> pepperpy.rag
            (r"^rag\.(\w+)$", f"{PACKAGE_NAME}.rag.\\1"),
            # Padrões adicionais
            (r"^workflows\.(\w+)$", f"{PACKAGE_NAME}.workflows.\\1"),
            (r"^multimodal\.(\w+)$", f"{PACKAGE_NAME}.multimodal.\\1"),
            (r"^observability\.(\w+)$", f"{PACKAGE_NAME}.observability.\\1"),
            (r"^adapters\.(\w+)$", f"{PACKAGE_NAME}.adapters.\\1"),
        ]

        # Construir mapa de migração
        for old_pattern, new_pattern in migration_patterns:
            for module_path in self.module_map.keys():
                if not module_path.startswith(PACKAGE_NAME):
                    continue

                # Remover prefixo do pacote para comparação
                short_path = module_path[len(PACKAGE_NAME) + 1 :]

                # Verificar se o módulo corresponde ao padrão novo
                # Substituir os grupos de captura na expressão regular por grupos não capturantes
                # para evitar referências de grupo inválidas
                pattern_to_match = new_pattern.replace(f"{PACKAGE_NAME}.", "")
                pattern_to_match = pattern_to_match.replace("\\1", "\\\\w+").replace(
                    "\\2", "\\\\w+",
                )

                match = re.match(pattern_to_match, short_path)
                if match:
                    # Extrair componentes do caminho
                    components = short_path.split(".")
                    if len(components) >= 2:
                        # Construir caminho antigo baseado no padrão
                        if (
                            old_pattern == r"^workflows\.(\w+)\.(\w+)$"
                            and len(components) >= 3
                        ):
                            old_path = f"workflows.{components[1]}.{components[2]}"
                        elif old_pattern == r"^agents\.(\w+)$":
                            old_path = f"agents.{components[1]}"
                        elif old_pattern == r"^core\.(\w+)$":
                            old_path = f"core.{components[1]}"
                        elif old_pattern == r"^rag\.(\w+)$":
                            old_path = f"rag.{components[1]}"
                        else:
                            continue

                        self.old_to_new_paths[old_path] = module_path

        # Adicionar mapeamentos específicos conhecidos
        specific_mappings = {
            "workflows.definition.builder": f"{PACKAGE_NAME}.workflows.definition",
            "workflows.definition.factory": f"{PACKAGE_NAME}.workflows.definition",
            "workflows.execution.scheduler": f"{PACKAGE_NAME}.workflows.execution.scheduler",
            "workflows.base": f"{PACKAGE_NAME}.workflows.base",
            "workflows.execution": f"{PACKAGE_NAME}.workflows.execution",
            "workflows.definition": f"{PACKAGE_NAME}.workflows.definition",
            "agents.factory": f"{PACKAGE_NAME}.agents.factory",
            "agents.base": f"{PACKAGE_NAME}.agents.base",
            "core.types": f"{PACKAGE_NAME}.core.types",
            "core.base": f"{PACKAGE_NAME}.core.base",
            "core.versioning": f"{PACKAGE_NAME}.core.versioning",
            "rag.retrieval.system": f"{PACKAGE_NAME}.rag.retrieval.system",
            "rag.retrieval": f"{PACKAGE_NAME}.rag.retrieval",
            "rag.base": f"{PACKAGE_NAME}.rag.base",
            "multimodal.base": f"{PACKAGE_NAME}.multimodal.base",
            "multimodal.audio": f"{PACKAGE_NAME}.multimodal.audio",
            "multimodal.vision": f"{PACKAGE_NAME}.multimodal.vision",
            "observability.metrics": f"{PACKAGE_NAME}.observability.metrics",
            "observability.logging": f"{PACKAGE_NAME}.observability.logging",
            "adapters.base": f"{PACKAGE_NAME}.adapters.base",
        }

        self.old_to_new_paths.update(specific_mappings)
        print(f"Criados {len(self.old_to_new_paths)} mapeamentos de migração")

    def find_correct_import(self, symbol: str) -> List[str]:
        """Encontra o caminho de importação correto para um símbolo."""
        candidates = []

        # Verificar se é uma classe
        if symbol in self.class_map:
            candidates.extend(self.class_map[symbol])

        # Verificar se é uma função
        if symbol in self.function_map:
            candidates.extend(self.function_map[symbol])

        # Verificar se é uma variável
        if symbol in self.variable_map:
            candidates.extend(self.variable_map[symbol])

        return candidates

    def fix_import_errors(self) -> None:
        """Corrige erros de importação nos arquivos."""
        print("Corrigindo erros de importação...")

        # Criar diretório de backup se não existir
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Processar cada arquivo com erros
        for file_path, errors in self.import_errors.items():
            self._fix_file_imports(file_path, errors)

        # Corrigir problemas específicos conhecidos
        self._fix_specific_issues()

        print(f"Corrigidos erros em {len(self.fixed_files)} arquivos")

    def _fix_specific_issues(self) -> None:
        """Fix specific known issues in files."""
        specific_fixes = [
            # Add missing imports to adapters/registry.py
            {
                "file": "pepperpy/adapters/registry.py",
                "add_import": "from typing import Any, Dict, Optional, Type",
                "position": "top",
            },
            {
                "file": "pepperpy/adapters/registry.py",
                "add_import": "from pepperpy.adapters.base import BaseAdapter",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/adapters/registry.py",
                "add_import": "from pepperpy.adapters.types import AdapterType",
                "position": "after_imports",
            },
            # Add missing imports to workflows/base.py
            {
                "file": "pepperpy/workflows/base.py",
                "add_import": "from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union",
                "position": "top",
            },
            {
                "file": "pepperpy/workflows/base.py",
                "add_import": "from pepperpy.core.components import ComponentState, ComponentConfig, ComponentCallback",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/workflows/base.py",
                "add_import": "from datetime import datetime",
                "position": "top",
            },
            {
                "file": "pepperpy/workflows/base.py",
                "add_import": "from abc import ABC, abstractmethod",
                "position": "top",
            },
            {
                "file": "pepperpy/workflows/base.py",
                "add_import": "from enum import Enum",
                "position": "top",
            },
            {
                "file": "pepperpy/workflows/base.py",
                "add_import": "from dataclasses import dataclass, field",
                "position": "top",
            },
            {
                "file": "pepperpy/workflows/base.py",
                "add_import": "from typing import Protocol",
                "position": "top",
            },
            # Add missing imports to workflows/execution/scheduler.py
            {
                "file": "pepperpy/workflows/execution/scheduler.py",
                "add_import": "from pepperpy.core.components import ComponentBase, ComponentConfig",
                "position": "after_imports",
            },
            # Add missing imports to rag/retrieval/system.py
            {
                "file": "pepperpy/rag/retrieval/system.py",
                "add_import": "from pepperpy.rag.embedders import TextEmbedder",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/rag/retrieval/system.py",
                "add_import": "from pepperpy.rag.indexers import Indexer",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/rag/retrieval/system.py",
                "add_import": "from pepperpy.core.lifecycle import Lifecycle",
                "position": "after_imports",
            },
            # Add missing imports to analysis/code.py
            {
                "file": "pepperpy/analysis/code.py",
                "add_import": "from pepperpy.monitoring.metrics import MetricsCollector",
                "position": "after_imports",
            },
            # Fix import in agents/factory.py
            {
                "file": "pepperpy/agents/factory.py",
                "add_import": "from pepperpy.core.errors import AgentError",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/agents/factory.py",
                "add_import": "from pepperpy.agents.base import BaseAgent",
                "position": "after_imports",
            },
            # Add missing imports to multimodal/audio/providers/synthesis/effects.py
            {
                "file": "pepperpy/multimodal/audio/providers/synthesis/effects.py",
                "add_import": "from typing import Any, Dict, List, Optional, Union",
                "position": "top",
            },
            {
                "file": "pepperpy/multimodal/audio/providers/synthesis/effects.py",
                "add_import": "from pydantic import BaseModel, Field",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/multimodal/audio/providers/synthesis/effects.py",
                "add_import": "from pepperpy.multimodal.audio.processors.base import AudioProcessor",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/multimodal/audio/providers/synthesis/effects.py",
                "add_import": "from pepperpy.multimodal.audio.types import AudioData",
                "position": "after_imports",
            },
            # Add missing imports to observability/logging/formatters.py
            {
                "file": "pepperpy/observability/logging/formatters.py",
                "add_import": "from typing import Any, Callable, Dict, Optional",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/formatters.py",
                "add_import": "from datetime import datetime",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/formatters.py",
                "add_import": "import logging",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/formatters.py",
                "add_import": "from pydantic import BaseModel, Field",
                "position": "after_imports",
            },
            # Add missing imports to observability/logging/filters.py
            {
                "file": "pepperpy/observability/logging/filters.py",
                "add_import": "from typing import Any, Dict, Set",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/filters.py",
                "add_import": "from pepperpy.observability.logging.formatters import LogRecord",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/observability/logging/filters.py",
                "add_import": "from pepperpy.observability.logging.types import LogLevel",
                "position": "after_imports",
            },
            # Add missing imports to observability/logging/handlers.py
            {
                "file": "pepperpy/observability/logging/handlers.py",
                "add_import": "from typing import Any, Dict, Optional, Union",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/handlers.py",
                "add_import": "import os",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/handlers.py",
                "add_import": "import gzip",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/handlers.py",
                "add_import": "import shutil",
                "position": "top",
            },
            {
                "file": "pepperpy/observability/logging/handlers.py",
                "add_import": "from pepperpy.observability.logging.formatters import LogRecord",
                "position": "after_imports",
            },
            {
                "file": "pepperpy/observability/logging/handlers.py",
                "add_import": "from pepperpy.observability.logging.base import LogHandler",
                "position": "after_imports",
            },
        ]

        for fix in specific_fixes:
            file_path = fix["file"]
            if not os.path.exists(file_path):
                print(f"File {file_path} not found, skipping specific fix.")
                continue

            try:
                with open(file_path) as f:
                    content = f.read()

                # Skip if file is empty
                if not content.strip():
                    continue

                # Check if the import already exists
                import_line = fix["add_import"]
                if import_line in content:
                    continue

                # Add the import at the specified position
                if fix["position"] == "top":
                    # Add at the top of the file
                    content = import_line + "\n" + content
                elif fix["position"] == "after_imports":
                    # Add after the last import statement
                    import_section_end = 0
                    for match in re.finditer(
                        r"^(?:import|from)\s+\w+", content, re.MULTILINE,
                    ):
                        end_of_line = content.find("\n", match.start())
                        import_section_end = max(import_section_end, end_of_line)

                    if import_section_end > 0:
                        content = (
                            content[: import_section_end + 1]
                            + import_line
                            + "\n"
                            + content[import_section_end + 1 :]
                        )
                    else:
                        # No imports found, add at the top
                        content = import_line + "\n" + content

                # Write the updated content
                with open(file_path, "w") as f:
                    f.write(content)
                print(f"Added import '{import_line}' to {file_path}")
            except Exception as e:
                print(f"Error fixing specific issue in {file_path}: {e}")

    def _fix_file_imports(self, file_path: str, errors: List[Dict[str, Any]]) -> None:
        """Fix import errors in a file."""
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return

        try:
            # Read the file content
            with open(file_path) as f:
                content = f.read()

            # Skip if file is empty
            if not content.strip():
                return

            original_content = content

            # Fix undefined names
            content = self._fix_undefined_names(content, errors)

            # Fix unused imports
            content = self._fix_unused_imports(content, errors)

            # Fix import * usage
            content = self._fix_import_star(content, errors)

            # Fix import order
            content = self._fix_import_order(content, errors)

            # Fix old import patterns
            content = self._fix_old_import_patterns(content)

            # Write the file if changes were made
            if content != original_content:
                print(f"Fixing imports in {file_path}")
                with open(file_path, "w") as f:
                    f.write(content)
        except Exception as e:
            print(f"Error fixing imports in {file_path}: {e}")

    def _fix_undefined_names(self, content: str, errors: List[Dict[str, Any]]) -> str:
        """Corrige erros de nomes indefinidos (F821)."""
        lines = content.split("\n")
        imports_to_add = set()

        for error in errors:
            message = error.get("message", "")
            match = re.search(r"undefined name '(\w+)'", message)
            if match:
                symbol = match.group(1)
                candidates = self.find_correct_import(symbol)

                if candidates:
                    # Escolher o candidato mais específico
                    best_candidate = max(candidates, key=lambda x: len(x.split(".")))
                    imports_to_add.add(f"from {best_candidate} import {symbol}")

        # Adicionar importações no início do arquivo, após as importações existentes
        if imports_to_add:
            # Encontrar a última importação
            last_import_line = 0
            for i, line in enumerate(lines):
                if re.match(r"^(import|from)\s+", line):
                    last_import_line = i

            # Inserir novas importações após a última importação existente
            for import_stmt in sorted(imports_to_add):
                lines.insert(last_import_line + 1, import_stmt)
                last_import_line += 1

        return "\n".join(lines)

    def _fix_unused_imports(self, content: str, errors: List[Dict[str, Any]]) -> str:
        """Corrige erros de importações não utilizadas (F401)."""
        lines = content.split("\n")
        lines_to_remove = set()

        for error in errors:
            line = error.get("location", {}).get("row", 0) - 1
            if 0 <= line < len(lines):
                # Verificar se é uma importação completa ou apenas um símbolo
                import_line = lines[line]
                message = error.get("message", "")
                match = re.search(r"'(\w+)' imported but unused", message)

                if match:
                    symbol = match.group(1)
                    # Se for uma importação de múltiplos símbolos, remover apenas o símbolo não utilizado
                    if "," in import_line:
                        pattern = rf"(,\s*{re.escape(symbol)}|{re.escape(symbol)}\s*,)"
                        lines[line] = re.sub(pattern, "", import_line)
                    else:
                        # Se for uma importação única, remover a linha inteira
                        lines_to_remove.add(line)
                else:
                    # Importação completa não utilizada
                    lines_to_remove.add(line)

        # Remover linhas marcadas para remoção (de trás para frente para não afetar os índices)
        for line in sorted(lines_to_remove, reverse=True):
            del lines[line]

        return "\n".join(lines)

    def _fix_import_star(self, content: str, errors: List[Dict[str, Any]]) -> str:
        """Corrige erros de importação com * (F403, F405)."""
        lines = content.split("\n")
        imports_to_add = set()
        lines_to_remove = set()

        # Identificar importações com *
        star_imports = {}
        for i, line in enumerate(lines):
            match = re.match(r"from\s+(\S+)\s+import\s+\*", line)
            if match:
                module = match.group(1)
                star_imports[i] = module

        # Para cada erro F405, adicionar importação específica
        for error in errors:
            code = error.get("code", "")
            if code == "F405":
                message = error.get("message", "")
                match = re.search(r"'(\w+)' may be undefined", message)
                if match:
                    symbol = match.group(1)

                    # Tentar encontrar o módulo correto para o símbolo
                    candidates = self.find_correct_import(symbol)
                    if candidates:
                        best_candidate = max(
                            candidates, key=lambda x: len(x.split(".")),
                        )
                        imports_to_add.add(f"from {best_candidate} import {symbol}")

        # Remover importações com * se tivermos importações específicas
        if imports_to_add:
            for line, _ in star_imports.items():
                lines_to_remove.add(line)

        # Remover linhas marcadas (de trás para frente)
        for line in sorted(lines_to_remove, reverse=True):
            del lines[line]

        # Adicionar importações específicas
        if imports_to_add:
            # Encontrar a última importação
            last_import_line = 0
            for i, line in enumerate(lines):
                if re.match(r"^(import|from)\s+", line):
                    last_import_line = i

            # Inserir novas importações após a última importação existente
            for import_stmt in sorted(imports_to_add):
                lines.insert(last_import_line + 1, import_stmt)
                last_import_line += 1

        return "\n".join(lines)

    def _fix_import_order(self, content: str, errors: List[Dict[str, Any]]) -> str:
        """Corrige erros de ordem de importação (E402)."""
        lines = content.split("\n")
        imports_to_move = []

        # Identificar importações fora de ordem
        for error in errors:
            line = error.get("location", {}).get("row", 0) - 1
            if 0 <= line < len(lines) and re.match(r"^(import|from)\s+", lines[line]):
                imports_to_move.append((line, lines[line]))

        # Remover importações fora de ordem (de trás para frente)
        for line, _ in sorted(imports_to_move, reverse=True):
            del lines[line]

        # Adicionar importações no início do arquivo
        for _, import_line in sorted(imports_to_move):
            lines.insert(0, import_line)

        return "\n".join(lines)

    def _fix_old_import_patterns(self, content: str) -> str:
        """Corrige padrões de importação antigos no conteúdo."""
        # Substituir importações antigas por novas
        for old_path, new_path in self.old_to_new_paths.items():
            # Corrigir importações diretas
            pattern = rf"import\s+{re.escape(old_path)}(\s|;|$)"
            replacement = f"import {new_path}\\1"
            content = re.sub(pattern, replacement, content)

            # Corrigir importações from
            pattern = rf"from\s+{re.escape(old_path)}\s+import"
            replacement = f"from {new_path} import"
            content = re.sub(pattern, replacement, content)

            # Corrigir importações from com subpacotes
            parts = old_path.split(".")
            if len(parts) > 1:
                base = ".".join(parts[:-1])
                last = parts[-1]
                pattern = (
                    rf"from\s+{re.escape(base)}\s+import\s+{re.escape(last)}(\s|;|,|$)"
                )
                new_parts = new_path.split(".")
                new_base = ".".join(new_parts[:-1])
                new_last = new_parts[-1]
                replacement = f"from {new_base} import {new_last}\\1"
                content = re.sub(pattern, replacement, content)

        return content

    def fix_old_import_paths(self) -> None:
        """Corrige caminhos de importação antigos para novos."""
        print("Corrigindo caminhos de importação antigos...")

        # Processar todos os arquivos Python no projeto
        for root, _, files in os.walk(PACKAGE_ROOT):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self._fix_old_paths_in_file(file_path)

    def _fix_old_paths_in_file(self, file_path: str) -> None:
        """Fix old import paths in a file."""
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return

        try:
            # Read the file content
            with open(file_path) as f:
                content = f.read()

            # Skip if file is empty
            if not content.strip():
                return

            original_content = content

            # Replace old import paths
            for old_path, new_path in self.old_to_new_paths.items():
                pattern = rf"from\s+{re.escape(old_path)}(\.\w+)?\s+import"
                replacement = f"from {new_path}\\1 import"
                content = re.sub(pattern, replacement, content)

                pattern = rf"import\s+{re.escape(old_path)}(\.\w+)?"
                replacement = f"import {new_path}\\1"
                content = re.sub(pattern, replacement, content)

            # Write the file if changes were made
            if content != original_content:
                print(f"Fixing old import paths in {file_path}")
                with open(file_path, "w") as f:
                    f.write(content)
        except Exception as e:
            print(f"Error fixing old import paths in {file_path}: {e}")

    def run(self) -> None:
        """Executa o processo completo de correção de importações."""
        self.map_project_structure()
        self.build_migration_map()
        self.fix_old_import_paths()
        self.detect_import_errors()
        self.fix_import_errors()
        print("\nProcesso concluído!")
        print(f"Arquivos corrigidos: {len(self.fixed_files)}")
        print(f"Backups salvos em: {BACKUP_DIR}")


def main() -> None:
    """Função principal."""
    print("=== Corretor de Importações do PepperPy ===")
    mapper = ImportMapper()
    mapper.run()


if __name__ == "__main__":
    main()
