from typing import Dict, Type
from .base import BaseEmbedding

_COMPONENT_REGISTRY: Dict[str, Type[BaseEmbedding]] = {}

def register_component(name: str, component_class: Type[BaseEmbedding]):
    """
    Registra uma implementação de componente.
    
    Args:
        name: Nome do componente
        component_class: Classe do componente
    """
    _COMPONENT_REGISTRY[name] = component_class

def get_component_class(name: str) -> Type[BaseEmbedding]:
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

def list_components() -> Dict[str, Type[BaseEmbedding]]:
    """
    Lista todos os componentes registrados.
    
    Returns:
        Dicionário com os componentes registrados
    """
    return _COMPONENT_REGISTRY.copy()
