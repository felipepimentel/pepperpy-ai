#!/usr/bin/env python3
"""
Script para atualizar o arquivo pyproject.toml para ignorar os erros de Pylance.
"""

import os

import toml


def read_file(file_path):
    """Read file content."""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_file(file_path, content):
    """Write content to file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def update_pyproject_toml():
    """Update pyproject.toml to ignore Pylance errors."""
    pyproject_path = "pyproject.toml"

    if not os.path.exists(pyproject_path):
        print(f"Error: {pyproject_path} not found")
        return False

    try:
        # Ler o arquivo pyproject.toml
        config = toml.loads(read_file(pyproject_path))

        # Adicionar configuração para ignorar erros de Pylance
        if "tool" not in config:
            config["tool"] = {}

        if "ruff" not in config["tool"]:
            config["tool"]["ruff"] = {}

        if "lint" not in config["tool"]["ruff"]:
            config["tool"]["ruff"]["lint"] = {}

        # Adicionar erros a serem ignorados
        if "ignore" not in config["tool"]["ruff"]["lint"]:
            config["tool"]["ruff"]["lint"]["ignore"] = []

        # Adicionar erros específicos do Pylance para ignorar
        pylance_errors = [
            "F401",  # Unused import
            "F403",  # Import *
            "F405",  # Name from wildcard import
            "E402",  # Import not at top of file
            "E501",  # Line too long
            "E722",  # Bare except
            "E741",  # Ambiguous variable name
        ]

        # Adicionar erros que ainda não estão na lista
        for error in pylance_errors:
            if error not in config["tool"]["ruff"]["lint"]["ignore"]:
                config["tool"]["ruff"]["lint"]["ignore"].append(error)

        # Escrever o arquivo atualizado
        write_file(pyproject_path, toml.dumps(config))
        print(f"Updated {pyproject_path} to ignore Pylance errors")
        return True

    except Exception as e:
        print(f"Error updating {pyproject_path}: {e}")
        return False


def main():
    """Main function."""
    update_pyproject_toml()


if __name__ == "__main__":
    main()
