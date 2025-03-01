#!/bin/bash
# Script para padronizar um domínio existente, adicionando os arquivos obrigatórios que estão faltando
BASE_DIR="pepperpy"
REQUIRED_FILES=("__init__.py" "base.py" "types.py" "factory.py" "registry.py")

# Função para criar um arquivo base.py
create_base_file() {
    local domain=$1
    local file_path="$BASE_DIR/$domain/base.py"
    
    if [ -f "$file_path" ]; then
        echo "⏭️ Arquivo base.py já existe, pulando."
        return 0
    fi
    
    echo "Criando arquivo base.py para o domínio $domain..."
    
    # Criar o arquivo com conteúdo básico
    cat > "$file_path" << EOF
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g'):
    """
    Classe base para componentes do domínio $domain.
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
EOF
    
    echo "✅ Arquivo base.py criado com sucesso."
    return 0
}

# Função para criar um arquivo types.py
create_types_file() {
    local domain=$1
    local file_path="$BASE_DIR/$domain/types.py"
    
    if [ -f "$file_path" ]; then
        echo "⏭️ Arquivo types.py já existe, pulando."
        return 0
    fi
    
    echo "Criando arquivo types.py para o domínio $domain..."
    
    # Criar o arquivo com conteúdo básico
    cat > "$file_path" << EOF
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

class $(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')Mode(Enum):
    """
    Modos de operação para o domínio $domain.
    """
    STANDARD = "standard"
    ADVANCED = "advanced"

@dataclass
class $(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')Config:
    """
    Configuração para componentes do domínio $domain.
    """
    name: str
    mode: $(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')Mode
    parameters: Dict[str, Any]
    options: Optional[List[str]] = None
EOF
    
    echo "✅ Arquivo types.py criado com sucesso."
    return 0
}

# Função para criar um arquivo factory.py
create_factory_file() {
    local domain=$1
    local file_path="$BASE_DIR/$domain/factory.py"
    
    if [ -f "$file_path" ]; then
        echo "⏭️ Arquivo factory.py já existe, pulando."
        return 0
    fi
    
    echo "Criando arquivo factory.py para o domínio $domain..."
    
    # Criar o arquivo com conteúdo básico
    cat > "$file_path" << EOF
from typing import Any, Dict, Type
from .base import Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')
from .registry import get_component_class

def create_component(component_type: str, **kwargs) -> Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g'):
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
EOF
    
    echo "✅ Arquivo factory.py criado com sucesso."
    return 0
}

# Função para criar um arquivo registry.py
create_registry_file() {
    local domain=$1
    local file_path="$BASE_DIR/$domain/registry.py"
    
    if [ -f "$file_path" ]; then
        echo "⏭️ Arquivo registry.py já existe, pulando."
        return 0
    fi
    
    echo "Criando arquivo registry.py para o domínio $domain..."
    
    # Criar o arquivo com conteúdo básico
    cat > "$file_path" << EOF
from typing import Dict, Type
from .base import Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')

_COMPONENT_REGISTRY: Dict[str, Type[Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')]] = {}

def register_component(name: str, component_class: Type[Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')]):
    """
    Registra uma implementação de componente.
    
    Args:
        name: Nome do componente
        component_class: Classe do componente
    """
    _COMPONENT_REGISTRY[name] = component_class

def get_component_class(name: str) -> Type[Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')]:
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
        raise ValueError(f"Component '{name}' not found in registry")
    return _COMPONENT_REGISTRY[name]

def list_components() -> Dict[str, Type[Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')]]:
    """
    Lista todos os componentes registrados.
    
    Returns:
        Dicionário com os componentes registrados
    """
    return _COMPONENT_REGISTRY.copy()
EOF
    
    echo "✅ Arquivo registry.py criado com sucesso."
    return 0
}

# Função para criar um arquivo __init__.py
create_init_file() {
    local domain=$1
    local file_path="$BASE_DIR/$domain/__init__.py"
    
    if [ -f "$file_path" ]; then
        echo "⏭️ Arquivo __init__.py já existe, pulando."
        return 0
    fi
    
    echo "Criando arquivo __init__.py para o domínio $domain..."
    
    # Criar o arquivo com conteúdo básico
    cat > "$file_path" << EOF
# Domínio $domain
from .base import Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')
from .factory import create_component

__all__ = ["Base$(echo "$domain" | sed -r 's/(^|_)([a-z])/\U\2/g')", "create_component"]
EOF
    
    echo "✅ Arquivo __init__.py criado com sucesso."
    return 0
}

# Função para padronizar um domínio
standardize_domain() {
    local domain=$1
    local domain_path="$BASE_DIR/$domain"
    
    echo "Padronizando o domínio: $domain"
    
    if [ ! -d "$domain_path" ]; then
        echo "Erro: O diretório do domínio '$domain_path' não existe."
        return 1
    fi
    
    # Verificar e criar arquivos obrigatórios
    local created_files=0
    local existing_files=0
    
    # Criar __init__.py
    if [ ! -f "$domain_path/__init__.py" ]; then
        create_init_file "$domain"
        ((created_files++))
    else
        ((existing_files++))
    fi
    
    # Criar base.py
    if [ ! -f "$domain_path/base.py" ]; then
        create_base_file "$domain"
        ((created_files++))
    else
        ((existing_files++))
    fi
    
    # Criar types.py
    if [ ! -f "$domain_path/types.py" ]; then
        create_types_file "$domain"
        ((created_files++))
    else
        ((existing_files++))
    fi
    
    # Criar factory.py
    if [ ! -f "$domain_path/factory.py" ]; then
        create_factory_file "$domain"
        ((created_files++))
    else
        ((existing_files++))
    fi
    
    # Criar registry.py
    if [ ! -f "$domain_path/registry.py" ]; then
        create_registry_file "$domain"
        ((created_files++))
    else
        ((existing_files++))
    fi
    
    echo ""
    echo "Resumo da padronização:"
    echo "Arquivos criados: $created_files"
    echo "Arquivos já existentes: $existing_files"
    
    if [ $created_files -gt 0 ]; then
        echo "✅ Domínio $domain padronizado com sucesso."
    else
        echo "✅ Domínio $domain já estava padronizado."
    fi
    
    return 0
}

# Função para mostrar a ajuda
show_help() {
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --domain NOME    Padroniza um domínio específico"
    echo "  --help           Mostra esta mensagem de ajuda"
}

# Processar argumentos da linha de comando
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

case "$1" in
    --domain)
        if [ -z "$2" ]; then
            echo "Erro: Nome do domínio não especificado."
            show_help
            exit 1
        fi
        standardize_domain "$2"
        ;;
    --help)
        show_help
        ;;
    *)
        echo "Opção desconhecida: $1"
        show_help
        exit 1
        ;;
esac
