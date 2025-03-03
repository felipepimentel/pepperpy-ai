#!/usr/bin/env python3
"""
Script para verificar se um domínio está em conformidade com as convenções definidas.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Arquivos obrigatórios que cada domínio deve ter
REQUIRED_FILES = ["__init__.py", "base.py", "types.py", "factory.py", "registry.py"]

# Arquivos opcionais que um domínio pode ter
OPTIONAL_FILES = ["config.py", "utils.py", "errors.py", "defaults.py", "pipeline.py"]

# Subdiretórios comuns
COMMON_SUBDIRS = ["providers", "models", "processors"]


def check_domain(domain_path: Path) -> Tuple[List[str], List[str]]:
    """
    Verifica se um domínio está em conformidade com as convenções de arquivos.

    Args:
        domain_path: Caminho para o diretório do domínio

    Returns:
        Tuple contendo a lista de arquivos obrigatórios faltantes e a lista de arquivos existentes

    """
    if not domain_path.exists() or not domain_path.is_dir():
        print(f"Erro: O diretório do domínio '{domain_path}' não existe.")
        sys.exit(1)

    # Listar todos os arquivos no diretório do domínio
    domain_files = [f.name for f in domain_path.glob("*.py")]

    # Verificar arquivos obrigatórios
    missing_files = [f for f in REQUIRED_FILES if f not in domain_files]
    existing_files = [f for f in REQUIRED_FILES if f in domain_files]

    return missing_files, existing_files


def check_all_domains(base_dir: Path) -> Dict[str, Tuple[List[str], List[str]]]:
    """
    Verifica todos os domínios no diretório base.

    Args:
        base_dir: Caminho para o diretório base dos domínios

    Returns:
        Dicionário com os resultados da verificação para cada domínio

    """
    results = {}

    # Listar todos os diretórios no diretório base
    domains = [
        d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith("__")
    ]

    for domain_path in domains:
        domain_name = domain_path.name
        missing_files, existing_files = check_domain(domain_path)
        results[domain_name] = (missing_files, existing_files)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Verifica a conformidade de um domínio com as convenções de arquivos.",
    )
    parser.add_argument("--domain", help="Nome do domínio a ser verificado")
    parser.add_argument("--all", action="store_true", help="Verifica todos os domínios")
    parser.add_argument(
        "--base-dir",
        default="pepperpy",
        help="Diretório base dos domínios (padrão: pepperpy)",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)

    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Erro: O diretório base '{base_dir}' não existe.")
        sys.exit(1)

    if args.domain:
        # Verificar um domínio específico
        domain_path = base_dir / args.domain
        print(f"Verificando o domínio: {args.domain}")
        missing_files, existing_files = check_domain(domain_path)

        if not missing_files:
            print(
                "✅ O domínio está em conformidade com todas as convenções de arquivos obrigatórios.",
            )
        else:
            print(
                "❌ O domínio não está em conformidade com as convenções de arquivos.",
            )
            print(f"Arquivos obrigatórios faltantes ({len(missing_files)}):")
            for file in missing_files:
                print(f"  - {file}")

        print(f"\nArquivos obrigatórios existentes ({len(existing_files)}):")
        for file in existing_files:
            print(f"  - {file}")

        # Verificar arquivos opcionais
        domain_files = [f.name for f in domain_path.glob("*.py")]
        optional_existing = [f for f in OPTIONAL_FILES if f in domain_files]
        if optional_existing:
            print(f"\nArquivos opcionais existentes ({len(optional_existing)}):")
            for file in optional_existing:
                print(f"  - {file}")

        # Verificar subdiretórios
        subdirs = [
            d.name
            for d in domain_path.iterdir()
            if d.is_dir() and d.name in COMMON_SUBDIRS
        ]
        if subdirs:
            print(f"\nSubdiretórios existentes ({len(subdirs)}):")
            for subdir in subdirs:
                print(f"  - {subdir}/")

    elif args.all:
        # Verificar todos os domínios
        print("Verificando todos os domínios...")
        results = check_all_domains(base_dir)

        # Contar domínios conformes e não conformes
        conforming = [domain for domain, (missing, _) in results.items() if not missing]
        non_conforming = [domain for domain, (missing, _) in results.items() if missing]

        print("\nResumo da verificação:")
        print(f"Total de domínios: {len(results)}")
        print(
            f"Domínios conformes: {len(conforming)} ({len(conforming) / len(results) * 100:.1f}%)",
        )
        print(
            f"Domínios não conformes: {len(non_conforming)} ({len(non_conforming) / len(results) * 100:.1f}%)",
        )

        if non_conforming:
            print("\nDomínios não conformes:")
            for domain in sorted(non_conforming):
                missing_files, _ = results[domain]
                print(f"  - {domain} (faltando: {', '.join(missing_files)})")

        if conforming:
            print("\nDomínios conformes:")
            for domain in sorted(conforming):
                print(f"  - {domain}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
