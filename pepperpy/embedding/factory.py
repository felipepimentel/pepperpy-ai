from typing import Any, Dict, Type
from .base import BaseEmbedding
from .registry import get_component_class

def create_component(component_type: str, **kwargs) -> BaseEmbedding:
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
