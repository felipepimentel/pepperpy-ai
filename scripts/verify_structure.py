#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para verificar a estrutura do projeto PepperPy.

Este script verifica se a estrutura do projeto PepperPy está de acordo
com a arquitetura definida, incluindo a presença de arquivos necessários
e a consistência entre os diferentes domínios.
"""

import os
import sys
from typing import List, Tuple


def check_file_exists(path: str) -> bool:
    """Verifica se um arquivo existe.

    Args:
        path: O caminho do arquivo.

    Returns:
        True se o arquivo existir, False caso contrário.
    """
    return os.path.isfile(path)


def check_directory_exists(path: str) -> bool:
    """Verifica se um diretório existe.

    Args:
        path: O caminho do diretório.

    Returns:
        True se o diretório existir, False caso contrário.
    """
    return os.path.isdir(path)


def check_vertical_domain(domain_path: str) -> Tuple[bool, List[str]]:
    """Verifica se um domínio vertical está completo.

    Args:
        domain_path: O caminho do domínio.

    Returns:
        Uma tupla contendo um booleano indicando se o domínio está completo
        e uma lista de arquivos faltantes.
    """
    required_files = [
        "__init__.py",
        "base.py",
        "types.py",
        "factory.py",
        "registry.py",
        "public.py",
    ]
    missing_files = []

    for file in required_files:
        file_path = os.path.join(domain_path, file)
        if not check_file_exists(file_path):
            missing_files.append(file_path)

    return len(missing_files) == 0, missing_files


def check_examples() -> Tuple[bool, List[str]]:
    """Verifica se os exemplos estão completos.

    Returns:
        Uma tupla contendo um booleano indicando se os exemplos estão completos
        e uma lista de diretórios faltantes.
    """
    required_dirs = [
        "examples/composition",
        "examples/content_processing",
        "examples/conversational",
        "examples/intent",
        "examples/workflows",
    ]
    missing_dirs = []

    for dir_path in required_dirs:
        if not check_directory_exists(dir_path):
            missing_dirs.append(dir_path)

    return len(missing_dirs) == 0, missing_dirs


def check_tests() -> Tuple[bool, List[str]]:
    """Verifica se os testes estão completos.

    Returns:
        Uma tupla contendo um booleano indicando se os testes estão completos
        e uma lista de diretórios faltantes.
    """
    required_dirs = [
        "tests/core/composition",
        "tests/core/intent",
        "tests/workflows/templates",
    ]
    missing_dirs = []

    for dir_path in required_dirs:
        if not check_directory_exists(dir_path):
            missing_dirs.append(dir_path)

    return len(missing_dirs) == 0, missing_dirs


def check_public_api() -> Tuple[bool, List[str]]:
    """Verifica se a API pública está completa.

    Returns:
        Uma tupla contendo um booleano indicando se a API pública está completa
        e uma lista de problemas encontrados.
    """
    problems = []

    # Verificar se o arquivo __init__.py existe
    if not check_file_exists("pepperpy/__init__.py"):
        problems.append("Arquivo pepperpy/__init__.py não encontrado")
        return False, problems

    # Verificar se os imports estão corretos
    # Isso é uma verificação simplificada, idealmente seria feito com AST
    with open("pepperpy/__init__.py", "r") as f:
        content = f.read()

    required_imports = [
        "compose",
        "compose_parallel",
        "recognize_intent",
        "process_intent",
        "execute_template",
    ]

    for imp in required_imports:
        if imp not in content:
            problems.append(f"Import '{imp}' não encontrado em pepperpy/__init__.py")

    return len(problems) == 0, problems


def main() -> int:
    """Função principal.

    Returns:
        0 se todos os testes passarem, 1 caso contrário.
    """
    print("Verificando a estrutura do projeto PepperPy...\n")

    all_passed = True
    vertical_domains = [
        "pepperpy/core/composition",
        "pepperpy/core/intent",
        "pepperpy/workflows/templates",
    ]

    # Verificar domínios verticais
    print("Verificando domínios verticais...")
    for domain in vertical_domains:
        passed, missing = check_vertical_domain(domain)
        if passed:
            print(f"  ✅ {domain}")
        else:
            print(f"  ❌ {domain}")
            for file in missing:
                print(f"     - {file} não encontrado")
            all_passed = False
    print()

    # Verificar exemplos
    print("Verificando exemplos...")
    passed, missing = check_examples()
    if passed:
        print("  ✅ Exemplos completos")
    else:
        print("  ❌ Exemplos incompletos")
        for dir_path in missing:
            print(f"     - {dir_path} não encontrado")
        all_passed = False
    print()

    # Verificar testes
    print("Verificando testes...")
    passed, missing = check_tests()
    if passed:
        print("  ✅ Testes completos")
    else:
        print("  ❌ Testes incompletos")
        for dir_path in missing:
            print(f"     - {dir_path} não encontrado")
        all_passed = False
    print()

    # Verificar API pública
    print("Verificando API pública...")
    passed, problems = check_public_api()
    if passed:
        print("  ✅ API pública completa")
    else:
        print("  ❌ API pública incompleta")
        for problem in problems:
            print(f"     - {problem}")
        all_passed = False
    print()

    if all_passed:
        print("✅ Todos os testes passaram!")
        return 0
    else:
        print("❌ Alguns testes falharam. Verifique os problemas acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
