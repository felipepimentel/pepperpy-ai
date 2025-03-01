#!/usr/bin/env python3
"""
Script para padronizar um domínio existente, adicionando os arquivos obrigatórios que estão faltando.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple

# Arquivos obrigatórios que cada domínio deve ter
REQUIRED_FILES = ["__init__.py", "base.py", "types.py", "factory.py", "registry.py"]

# Templates para os arquivos
TEMPLATE_BASE = '''from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Base{domain_upper}:
    """
    Classe base para componentes do domínio {domain}.
    """
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """
        Processa os dados de entrada.
        
        Args:
            input_data: Dados de entrada para processamento
            
        Returns:
            Resultado do processamento
        """
        pass
'''

TEMPLATE_TYPES = '''from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

class {domain_upper}Mode(Enum):
    """
    Modos de operação para o domínio {domain}.
    """
    STANDARD = "standard"
    ADVANCED = "advanced"

@dataclass
class {domain_upper}Config:
    """
    Configuração para componentes do domínio {domain}.
    """
    name: str
    mode: {domain_upper}Mode
    parameters: Dict[str, Any]
    options: Optional[List[str]] = None
'''

TEMPLATE_FACTORY = '''from typing import Any, Dict, Type
from .base import Base{domain_upper}
from .registry import get_component_class

def create_component(component_type: str, **kwargs) -> Base{domain_upper}:
    """
    Cria uma instância de componente do tipo especificado.
    
    Args:
        component_type: Tipo de componente a ser criado
        **kwargs: Argumentos para inicialização do componente
        
    Returns:
        Instância do componente
    """
    component_class = get_component_class(component_type)
    return component_class(**kwargs)
'''

TEMPLATE_REGISTRY = '''from typing import Dict, Type
from .base import Base{domain_upper}

_COMPONENT_REGISTRY: Dict[str, Type[Base{domain_upper}]] = {{}}

def register_component(name: str, component_class: Type[Base{domain_upper}]):
    """
    Registra uma implementação de componente.
    
    Args:
        name: Nome do componente
        component_class: Classe do componente
    """
    _COMPONENT_REGISTRY[name] = component_class

def get_component_class(name: str) -> Type[Base{domain_upper}]:
    """
    Obtém uma classe de componente pelo nome.
    
    Args:
        name: Nome do componente
        
    Returns:
        Classe do componente
        
    Raises:
        ValueError: Se o componente não for encontrado no registro
    """
    if name not in _COMPONENT_REGISTRY:
        raise ValueError(f"Component '{{name}}' not found in registry")
    return _COMPONENT_REGISTRY[name]

def list_components() -> Dict[str, Type[Base{domain_upper}]]:
    """
    Lista todos os componentes registrados.
    
    Returns:
        Dicionário com os componentes registrados
    """
    return _COMPONENT_REGISTRY.copy()
'''


def create_file_if_missing(
    domain_path: Path, file_name: str, template: str, domain: str
) -> bool:
    """
    Cria um arquivo se ele não existir.

    Args:
        domain_path: Caminho para o diretório do domínio
        file_name: Nome do arquivo a ser criado
        template: Template para o conteúdo do arquivo
        domain: Nome do domínio

    Returns:
        True se o arquivo foi criado, False se já existia
    """
    file_path = domain_path / file_name

    if file_path.exists():
        print(f"⏭️ Arquivo {file_name} já existe, pulando.")
        return False

    print(f"Criando arquivo {file_name} para o domínio {domain}...")

    # Substituir variáveis no template
    domain_upper = domain.title().replace("_", "")
    content = template.format(domain=domain, domain_upper=domain_upper)

    # Criar o arquivo
    with open(file_path, "w") as f:
        f.write(content)

    print(f"✅ Arquivo {file_name} criado com sucesso.")
    return True


def standardize_domain(domain_path: Path, domain: str) -> Tuple[int, int]:
    """
    Padroniza um domínio existente, adicionando os arquivos obrigatórios que estão faltando.

    Args:
        domain_path: Caminho para o diretório do domínio
        domain: Nome do domínio

    Returns:
        Tuple contendo o número de arquivos criados e o número de arquivos já existentes
    """
    if not domain_path.exists():
        print(f"Erro: O diretório do domínio '{domain_path}' não existe.")
        sys.exit(1)

    if not domain_path.is_dir():
        print(f"Erro: '{domain_path}' não é um diretório.")
        sys.exit(1)

    # Listar todos os arquivos no diretório do domínio
    domain_files = [f.name for f in domain_path.glob("*.py")]

    # Verificar e criar arquivos obrigatórios
    created_files = 0
    existing_files = 0

    for file_name in REQUIRED_FILES:
        if file_name in domain_files:
            existing_files += 1
            continue

        if file_name == "base.py":
            if create_file_if_missing(domain_path, file_name, TEMPLATE_BASE, domain):
                created_files += 1
        elif file_name == "types.py":
            if create_file_if_missing(domain_path, file_name, TEMPLATE_TYPES, domain):
                created_files += 1
        elif file_name == "factory.py":
            if create_file_if_missing(domain_path, file_name, TEMPLATE_FACTORY, domain):
                created_files += 1
        elif file_name == "registry.py":
            if create_file_if_missing(
                domain_path, file_name, TEMPLATE_REGISTRY, domain
            ):
                created_files += 1
        elif file_name == "__init__.py":
            # Não substituímos o __init__.py se já existir
            if not (domain_path / file_name).exists():
                print(f"Criando arquivo {file_name} para o domínio {domain}...")
                with open(domain_path / file_name, "w") as f:
                    f.write(f"# Domínio {domain}\n")
                print(f"✅ Arquivo {file_name} criado com sucesso.")
                created_files += 1

    return created_files, existing_files


def main():
    parser = argparse.ArgumentParser(
        description="Padroniza um domínio existente, adicionando os arquivos obrigatórios que estão faltando."
    )
    parser.add_argument(
        "--domain", required=True, help="Nome do domínio a ser padronizado"
    )
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

    domain_path = base_dir / args.domain

    print(f"Padronizando o domínio: {args.domain}")
    created_files, existing_files = standardize_domain(domain_path, args.domain)

    print("\nResumo da padronização:")
    print(f"Arquivos criados: {created_files}")
    print(f"Arquivos já existentes: {existing_files}")

    if created_files > 0:
        print(f"\n✅ Domínio {args.domain} padronizado com sucesso.")
    else:
        print(f"\n✅ Domínio {args.domain} já estava padronizado.")


if __name__ == "__main__":
    main()
