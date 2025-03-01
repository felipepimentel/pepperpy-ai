# Padronização Manual de Domínios

Este documento descreve como padronizar manualmente os domínios do projeto PepperPy para garantir que todos sigam as convenções de arquivos definidas.

## Verificação de Conformidade

Para verificar se um domínio está em conformidade com as convenções de arquivos, você pode usar o seguinte comando:

```bash
# Verificar um domínio específico
find pepperpy/nome_do_dominio -type f -name "*.py" | sort

# Comparar com a lista de arquivos obrigatórios
echo "Arquivos obrigatórios:"
echo "- __init__.py"
echo "- base.py"
echo "- types.py"
echo "- factory.py"
echo "- registry.py"
```

## Padronização Manual

Para padronizar um domínio manualmente, siga os passos abaixo:

1. Verifique quais arquivos obrigatórios estão faltando:
   ```bash
   find pepperpy/nome_do_dominio -type f -name "*.py" | sort
   ```

2. Crie os arquivos faltantes com o conteúdo apropriado:

### base.py

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseDomainName:
    """
    Classe base para componentes do domínio.
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
```

### types.py

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

class DomainNameMode(Enum):
    """
    Modos de operação para o domínio.
    """
    STANDARD = "standard"
    ADVANCED = "advanced"

@dataclass
class DomainNameConfig:
    """
    Configuração para componentes do domínio.
    """
    name: str
    mode: DomainNameMode
    parameters: Dict[str, Any]
    options: Optional[List[str]] = None
```

### factory.py

```python
from typing import Any, Dict, Type
from .base import BaseDomainName
from .registry import get_component_class

def create_component(component_type: str, **kwargs) -> BaseDomainName:
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
```

### registry.py

```python
from typing import Dict, Type
from .base import BaseDomainName

_COMPONENT_REGISTRY: Dict[str, Type[BaseDomainName]] = {}

def register_component(name: str, component_class: Type[BaseDomainName]):
    """
    Registra uma implementação de componente.
    
    Args:
        name: Nome do componente
        component_class: Classe do componente
    """
    _COMPONENT_REGISTRY[name] = component_class

def get_component_class(name: str) -> Type[BaseDomainName]:
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

def list_components() -> Dict[str, Type[BaseDomainName]]:
    """
    Lista todos os componentes registrados.
    
    Returns:
        Dicionário com os componentes registrados
    """
    return _COMPONENT_REGISTRY.copy()
```

## Exemplo de Padronização

Para padronizar o domínio `embedding`, por exemplo, você pode fazer:

```bash
# Verificar quais arquivos estão faltando
find pepperpy/embedding -type f -name "*.py" | sort

# Criar os arquivos faltantes
touch pepperpy/embedding/types.py
touch pepperpy/embedding/factory.py
touch pepperpy/embedding/registry.py

# Editar os arquivos com o conteúdo apropriado
# (use os templates acima, substituindo DomainName por Embedding)
```

## Verificação Após Padronização

Após padronizar um domínio, verifique novamente se ele está em conformidade com as convenções:

```bash
find pepperpy/nome_do_dominio -type f -name "*.py" | sort
```

Certifique-se de que todos os arquivos obrigatórios estão presentes e têm o conteúdo apropriado.

## Adaptação dos Templates

Ao criar os arquivos para um domínio específico, lembre-se de adaptar os templates:

1. Substitua `DomainName` pelo nome do domínio (com a primeira letra maiúscula)
2. Substitua `BaseDomainName` por `Base` + nome do domínio (com a primeira letra maiúscula)
3. Adapte as docstrings para refletir o propósito específico do domínio
4. Se necessário, adicione métodos ou atributos específicos do domínio

Por exemplo, para o domínio `embedding`:
- `DomainNameMode` se torna `EmbeddingMode`
- `BaseDomainName` se torna `BaseEmbedding`
- `DomainNameConfig` se torna `EmbeddingConfig`

