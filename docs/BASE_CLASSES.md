# Classes Base do PepperPy

Este documento descreve as principais classes base do framework PepperPy após a consolidação, e como elas devem ser usadas em módulos novos ou existentes.

## Classes Base Principais

### `BaseProvider`

A classe `BaseProvider` é a base para todos os provedores no framework. Provedores são componentes que implementam serviços específicos, como modelos LLM, backends de armazenamento ou integrações com APIs externas.

**Localização:** `pepperpy.core.BaseProvider`

**Características principais:**
- Gestão de capacidades (capabilities)
- Validação de configuração
- Métodos de inicialização e fechamento
- Configuração via parâmetros nomeados

**Exemplo de uso:**

```python
from pepperpy.core import BaseProvider

class MyCustomProvider(BaseProvider):
    def __init__(self, provider_name=None, model_name=None, **kwargs):
        super().__init__(
            provider_type="my_custom_type", 
            provider_name=provider_name,
            model_name=model_name,
            **kwargs
        )
        # Adicionar capacidades específicas
        self.add_capability("text_analysis")
        self.add_capability("data_extraction")
        
    async def validate(self):
        # Validação específica do provedor
        if "api_key" not in self.config:
            raise ProviderError("API key is required")
            
    async def initialize(self):
        # Inicialização de recursos
        # ...
        
    async def close(self):
        # Liberação de recursos
        # ...
```

### `Registry` e `TypeRegistry`

As classes `Registry` e `TypeRegistry` são usadas para gerenciar e organizar componentes, provedores, esquemas e outros objetos do framework.

**Localização:** `pepperpy.core.Registry`, `pepperpy.core.TypeRegistry`

**Características principais:**
- Registro e recuperação de componentes por chave
- Tipagem genérica para garantir consistência
- Métodos para listar componentes registrados
- Tratamento unificado de erros

**Exemplo de uso:**

```python
from pepperpy.core import Registry, TypeRegistry
from typing import Dict

# Registro para objetos arbitrários
data_registry = Registry[Dict](registry_name="data_registry", registry_type="data")

# Registro para classes (que podem ser instanciadas)
provider_registry = TypeRegistry[BaseProvider](
    registry_name="provider_registry", 
    registry_type="provider"
)

# Registrar um item
data_registry.register("my_data", {"key": "value"})

# Registrar uma classe
provider_registry.register("my_provider", MyCustomProvider)

# Criar uma instância de uma classe registrada
provider = provider_registry.create("my_provider", api_key="123456")
```

### `BaseManager`

A classe `BaseManager` é usada para coordenar componentes e provedores, fornecendo uma interface unificada para trabalhar com esses componentes.

**Localização:** `pepperpy.core.BaseManager`

**Características principais:**
- Gerenciamento de provedores
- Cache de instâncias de provedores
- Configuração de provedor padrão
- Tratamento unificado de erros

**Exemplo de uso:**

```python
from pepperpy.core import BaseManager
from my_module.providers import MyProvider, AnotherProvider

class MyManager(BaseManager[MyProvider]):
    def __init__(self):
        super().__init__(
            manager_name="my_manager",
            manager_type="my_type"
        )
        
        # Registrar provedores
        self.register_provider("default", MyProvider)
        self.register_provider("alternative", AnotherProvider)
        
        # Definir provedor padrão
        self.set_default_provider("default")
    
    async def process_data(self, data, provider_type=None):
        # Obter um provedor (usando o padrão se não especificado)
        provider = self.get_provider(provider_type)
        
        # Usar o provedor
        result = await provider.process(data)
        return result
```

## Migração de Código Existente

Ao migrar módulos existentes para usar as novas classes base, siga estas diretrizes:

1. **Substitua implementações de Providers existentes** por subclasses de `BaseProvider`
2. **Substitua implementações de Registry existentes** por instâncias de `Registry` ou `TypeRegistry`
3. **Substitua implementações de Manager existentes** por subclasses de `BaseManager`
4. **Verifique as APIs públicas** para garantir compatibilidade com código existente
5. **Atualize a documentação** para refletir as novas implementações

## Benefícios da Consolidação

- **Código Consistente**: Interface unificada para componentes similares
- **Menos Duplicação**: Funcionalidade comum implementada uma única vez
- **Melhor Tipagem**: Uso consistente de generics para garantir segurança de tipos
- **Mais Fácil de Entender**: Padrões consistentes em todo o framework
- **Manutenção Simplificada**: Correções e melhorias aplicadas em um único lugar

## Erros Específicos

As classes base definem erros específicos para cada tipo de componente:

- `ProviderError`: Erro relacionado a provedores
- `RegistryError`: Erro relacionado a registros
- `ManagerError`: Erro relacionado a gerenciadores

Esses erros devem ser usados em vez de exceções genéricas para facilitar o tratamento de erros específicos. 