# Sistema de Registro Unificado do PepperPy

Este pacote fornece um sistema de registro unificado para componentes do PepperPy. Ele implementa um mecanismo de registro central que pode ser usado por todos os módulos para registrar e descobrir componentes de forma consistente.

## Visão Geral

O sistema de registro unificado permite:

- Registrar e descobrir componentes em todo o framework
- Gerenciar metadados de componentes
- Criar instâncias de componentes a partir de tipos registrados
- Fornecer um ponto central para acessar todos os registros específicos

## Estrutura

O sistema de registro é composto por:

- `Registry`: Classe base para todos os registros
- `RegistryComponent`: Interface para componentes registráveis
- `RegistryManager`: Gerenciador central de registros
- Utilitários para auto-registro e descoberta de componentes

## Uso Básico

### Registrar um Componente

```python
from pepperpy.core.registry import ComponentMetadata, Registry, RegistryComponent

# Criar um componente
class MyComponent(RegistryComponent):
    @property
    def name(self) -> str:
        return "my_component"
    
    @property
    def metadata(self) -> ComponentMetadata:
        return ComponentMetadata(
            name=self.name,
            description="Meu componente personalizado",
            tags={"example"},
            properties={"type": "example"},
        )

# Criar um registro
registry = Registry(MyComponent)

# Registrar o componente
component = MyComponent()
registry.register(component)

# Obter o componente
retrieved = registry.get("my_component")
```

### Registrar um Tipo de Componente

```python
from pepperpy.core.registry import ComponentMetadata, Registry, RegistryComponent

# Definir uma classe de componente
class MyComponent(RegistryComponent):
    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def metadata(self) -> ComponentMetadata:
        return ComponentMetadata(
            name=self.name,
            description=self._description,
            tags={"example"},
            properties={"type": "example"},
        )

# Criar um registro
registry = Registry(MyComponent)

# Registrar o tipo de componente
registry.register_type(
    "MyComponentType",
    MyComponent,
    ComponentMetadata(
        name="MyComponentType",
        description="Tipo de componente personalizado",
        tags={"type", "example"},
    ),
)

# Criar uma instância a partir do tipo
component = registry.create("MyComponentType", "instance1", "Instância criada a partir do tipo")
registry.register(component)
```

### Usar o Gerenciador de Registros

```python
from pepperpy.core.registry import get_registry

# Obter o gerenciador de registros
registry_manager = get_registry()

# Registrar um registro específico
registry_manager.register_registry("my_registry", my_registry)

# Obter um registro específico
my_registry = registry_manager.get_registry("my_registry")
```

### Auto-Registro de Componentes

```python
from pepperpy.core.registry.auto import register_component

@register_component("my_registry", "MyComponent")
class MyComponent(RegistryComponent):
    # Implementação do componente
    pass
```

## Registros Específicos

O framework PepperPy inclui vários registros específicos que usam o sistema de registro unificado:

- `AgentRegistry`: Registro para agentes
- `WorkflowRegistry`: Registro para fluxos de trabalho
- `ComponentRegistry`: Registro para componentes RAG
- `AdapterRegistry`: Registro para adaptadores
- `CommandRegistry`: Registro para comandos CLI

Cada registro específico fornece funcionalidades adicionais específicas para seu domínio, mas todos usam a infraestrutura de registro unificada.

## Boas Práticas

1. Use a interface `RegistryComponent` para componentes registráveis
2. Forneça metadados úteis para componentes
3. Use o gerenciador de registros para acessar registros específicos
4. Considere usar o auto-registro para componentes que devem ser descobertos automaticamente
5. Documente os componentes registrados com descrições claras

## Referência da API

Consulte a documentação das classes e funções em:

- `pepperpy.core.registry.__init__`
- `pepperpy.core.registry.base`
- `pepperpy.core.registry.auto` 