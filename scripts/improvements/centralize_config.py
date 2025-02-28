"""
Módulo para implementar a centralização de configuração no projeto PepperPy.

Este módulo:
1. Cria um diretório centralizado para configurações (pepperpy/config)
2. Move configurações dispersas para o diretório central
3. Atualiza referências a configurações em todo o projeto
4. Implementa validação de variáveis de ambiente e flags de recursos
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Set


def find_config_files(project_root: Path) -> List[Path]:
    """
    Encontra arquivos de configuração dispersos no projeto.

    Args:
        project_root: Diretório raiz do projeto

    Returns:
        Lista de caminhos para arquivos de configuração
    """
    config_files = []
    config_patterns = ["default*.py", "config*.py", "settings*.py", "constants*.py"]

    # Diretórios a ignorar
    ignore_dirs = {".git", ".venv", "__pycache__", "backup", "scripts"}

    for root, dirs, files in os.walk(project_root / "pepperpy"):
        # Remover diretórios ignorados
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        # Verificar cada arquivo
        for pattern in config_patterns:
            for file in Path(root).glob(pattern):
                # Não incluir arquivos já no diretório centralizado
                if "pepperpy/config" not in str(file):
                    config_files.append(file)

    return config_files


def create_config_module(project_root: Path) -> Path:
    """
    Cria o módulo de configuração centralizado.

    Args:
        project_root: Diretório raiz do projeto

    Returns:
        Caminho para o módulo de configuração
    """
    config_dir = project_root / "pepperpy" / "config"
    config_dir.mkdir(exist_ok=True)

    # Criar __init__.py
    init_path = config_dir / "__init__.py"
    with open(init_path, "w") as f:
        f.write('"""\nCentralized configuration module for PepperPy.\n\n')
        f.write(
            "This module provides centralized access to all configuration settings,\n"
        )
        f.write(
            "environment variables, and feature flags used in the PepperPy framework.\n"
        )
        f.write('"""\n\n')
        f.write("from .settings import *  # noqa\n")
        f.write("from .feature_flags import *  # noqa\n")
        f.write("from .environment import *  # noqa\n")

    # Criar arquivo de configurações gerais
    settings_path = config_dir / "settings.py"
    with open(settings_path, "w") as f:
        f.write('"""\nGeneral settings for PepperPy.\n\n')
        f.write("This module contains general configuration settings that are used\n")
        f.write("throughout the PepperPy framework.\n")
        f.write('"""\n\n')
        f.write("# Default settings\n")
        f.write("DEFAULT_TIMEOUT = 60  # seconds\n")
        f.write("DEFAULT_CACHE_SIZE = 1000\n")
        f.write("DEFAULT_BATCH_SIZE = 100\n\n")

    # Criar arquivo de feature flags
    flags_path = config_dir / "feature_flags.py"
    with open(flags_path, "w") as f:
        f.write('"""\nFeature flags for PepperPy.\n\n')
        f.write("This module defines feature flags that control the behavior of\n")
        f.write("various components of the PepperPy framework.\n")
        f.write('"""\n\n')
        f.write("# Feature flags\n")
        f.write("ENABLE_CACHING = True\n")
        f.write("ENABLE_DISTRIBUTED_MODE = False\n")
        f.write("ENABLE_DEBUG_LOGGING = False\n\n")

    # Criar arquivo de variáveis de ambiente
    env_path = config_dir / "environment.py"
    with open(env_path, "w") as f:
        f.write('"""\nEnvironment variables for PepperPy.\n\n')
        f.write(
            "This module handles environment variables used by the PepperPy framework.\n"
        )
        f.write('"""\n\n')
        f.write("import os\n")
        f.write("from typing import Any, Dict, Optional\n\n")
        f.write("# Environment variables\n")
        f.write("def get_env(name: str, default: Any = None) -> Any:\n")
        f.write('    """Get environment variable or return default value."""\n')
        f.write("    return os.environ.get(name, default)\n\n")
        f.write("# Common environment variables\n")
        f.write('API_KEY = get_env("PEPPERPY_API_KEY")\n')
        f.write(
            'DEBUG = get_env("PEPPERPY_DEBUG", "False").lower() in ("true", "1", "yes")\n'
        )
        f.write(
            'CACHE_DIR = get_env("PEPPERPY_CACHE_DIR", os.path.expanduser("~/.pepperpy/cache"))\n\n'
        )

    # Criar arquivo de validação de configuração
    validation_path = config_dir / "validation.py"
    with open(validation_path, "w") as f:
        f.write('"""\nConfiguration validation for PepperPy.\n\n')
        f.write("This module provides utilities to validate configuration settings\n")
        f.write("and environment variables.\n")
        f.write('"""\n\n')
        f.write("import os\n")
        f.write("from typing import Dict, List, Optional, Tuple\n\n")
        f.write("def validate_config() -> Tuple[bool, List[str]]:\n")
        f.write('    """Validate configuration settings and environment variables.\n\n')
        f.write("    Returns:\n")
        f.write("        Tuple containing a boolean indicating if validation passed\n")
        f.write("        and a list of validation error messages.\n")
        f.write('    """\n')
        f.write("    errors = []\n\n")
        f.write("    # Check required environment variables\n")
        f.write('    required_env_vars = ["PEPPERPY_API_KEY"]\n')
        f.write("    for var in required_env_vars:\n")
        f.write("        if not os.environ.get(var):\n")
        f.write(
            '            errors.append(f"Missing required environment variable: {var}")\n\n'
        )
        f.write("    # Check for deprecated settings\n")
        f.write('    if "PEPPERPY_OLD_SETTING" in os.environ:\n')
        f.write(
            '        errors.append("PEPPERPY_OLD_SETTING is deprecated, use PEPPERPY_NEW_SETTING instead")\n\n'
        )
        f.write("    return len(errors) == 0, errors\n")

    return config_dir


def extract_settings_from_file(file_path: Path) -> Dict[str, str]:
    """
    Extrai configurações de um arquivo.

    Args:
        file_path: Caminho para o arquivo

    Returns:
        Dicionário de configurações extraídas
    """
    settings = {}

    with open(file_path, "r") as f:
        content = f.read()

    # Padrão para encontrar constantes
    pattern = r"^([A-Z][A-Z0-9_]*)\s*=\s*(.+)$"

    for line in content.split("\n"):
        line = line.strip()
        if (
            line
            and not line.startswith("#")
            and not line.startswith('"""')
            and not line.startswith("'''")
        ):
            match = re.match(pattern, line)
            if match:
                name = match.group(1)
                value = match.group(2)
                settings[name] = value

    return settings


def migrate_settings(
    config_files: List[Path], config_dir: Path, backup_dir: Path
) -> Dict[str, Set[str]]:
    """
    Migra configurações para o diretório centralizado.

    Args:
        config_files: Lista de arquivos de configuração
        config_dir: Diretório de configuração centralizado
        backup_dir: Diretório para backup

    Returns:
        Dicionário de configurações migradas por categoria
    """
    migrated_settings = {"general": set(), "feature_flags": set(), "environment": set()}

    # Arquivos de destino
    settings_file = config_dir / "settings.py"
    flags_file = config_dir / "feature_flags.py"
    env_file = config_dir / "environment.py"

    # Ler conteúdo dos arquivos de destino existentes
    with open(settings_file, "r") as f:
        settings_content = f.read()

    with open(flags_file, "r") as f:
        flags_content = f.read()

    with open(env_file, "r") as f:
        env_content = f.read()

    # Migrar configurações de cada arquivo
    for file_path in config_files:
        # Criar backup
        rel_path = file_path.relative_to(file_path.parent.parent.parent)
        backup_path = backup_dir / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)

        # Extrair configurações
        settings = extract_settings_from_file(file_path)

        # Categorizar e migrar configurações
        for name, value in settings.items():
            # Feature flags (nomes que começam com ENABLE_ ou USE_)
            if name.startswith("ENABLE_") or name.startswith("USE_"):
                if f"{name} = " not in flags_content:
                    with open(flags_file, "a") as f:
                        f.write(f"{name} = {value}\n")
                    migrated_settings["feature_flags"].add(name)

            # Variáveis de ambiente (nomes que terminam com _ENV ou _VAR)
            elif name.endswith("_ENV") or name.endswith("_VAR") or "ENV_" in name:
                if f"{name} = " not in env_content:
                    with open(env_file, "a") as f:
                        f.write(
                            f'{name} = get_env("{name.replace("_", ".")}", {value})\n'
                        )
                    migrated_settings["environment"].add(name)

            # Configurações gerais (outras constantes)
            else:
                if f"{name} = " not in settings_content:
                    with open(settings_file, "a") as f:
                        f.write(f"{name} = {value}\n")
                    migrated_settings["general"].add(name)

    return migrated_settings


def update_imports(project_root: Path, config_dir: Path) -> int:
    """
    Atualiza importações em todo o projeto para usar o novo módulo de configuração centralizado.

    Args:
        project_root: Diretório raiz do projeto
        config_dir: Diretório de configuração centralizado

    Returns:
        Número de arquivos atualizados
    """
    files_updated = 0

    # Diretórios a ignorar
    ignore_dirs = {".git", ".venv", "__pycache__", "backup", "scripts"}

    # Padrões de importação a atualizar
    import_patterns = [
        (
            r"from pepperpy\.(\w+)\.defaults import (.+)",
            r"from pepperpy.config.settings import \2",
        ),
        (
            r"from pepperpy\.(\w+)\.config import (.+)",
            r"from pepperpy.config import \2",
        ),
        (r"import pepperpy\.(\w+)\.defaults", r"import pepperpy.config.settings"),
        (r"import pepperpy\.(\w+)\.config", r"import pepperpy.config"),
    ]

    for root, dirs, files in os.walk(project_root / "pepperpy"):
        # Remover diretórios ignorados
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        # Verificar cada arquivo Python
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file

                # Não atualizar arquivos no diretório de configuração
                if config_dir in file_path.parents:
                    continue

                with open(file_path, "r") as f:
                    content = f.read()

                # Aplicar cada padrão de substituição
                modified = False
                for pattern, replacement in import_patterns:
                    new_content = re.sub(pattern, replacement, content)
                    if new_content != content:
                        content = new_content
                        modified = True

                # Se modificado, salvar o arquivo
                if modified:
                    with open(file_path, "w") as f:
                        f.write(content)
                    files_updated += 1

    return files_updated


def implement_config_centralization(project_root: Path, backup_dir: Path) -> None:
    """
    Implementa a centralização de configuração no projeto.

    Args:
        project_root: Diretório raiz do projeto
        backup_dir: Diretório para backup
    """
    print("Implementando centralização de configuração...")

    # 1. Encontrar arquivos de configuração
    config_files = find_config_files(project_root)
    print(f"Encontrados {len(config_files)} arquivos de configuração:")
    for file in config_files:
        rel_path = file.relative_to(project_root)
        print(f"  - {rel_path}")

    # 2. Criar módulo de configuração centralizado
    config_dir = create_config_module(project_root)
    print(f"Criado módulo de configuração centralizado em {config_dir}")

    # 3. Migrar configurações
    migrated_settings = migrate_settings(config_files, config_dir, backup_dir)
    print("Migradas configurações:")
    print(f"  - Configurações gerais: {len(migrated_settings['general'])}")
    print(f"  - Feature flags: {len(migrated_settings['feature_flags'])}")
    print(f"  - Variáveis de ambiente: {len(migrated_settings['environment'])}")

    # 4. Atualizar importações
    files_updated = update_imports(project_root, config_dir)
    print(f"Atualizadas importações em {files_updated} arquivos")

    print("Centralização de configuração concluída!")
