# Guia de Migração de Providers

Este documento fornece orientações sobre como migrar providers existentes para usar a nova classe `BaseProvider` consolidada no módulo `pepperpy.core.base_provider`.

## Visão Geral

A classe `BaseProvider` foi consolidada na pasta `core` para eliminar duplicação e fornecer uma implementação consistente. Todos os providers existentes devem ser migrados para usar esta nova classe base.

## Passos para Migração

### 1. Atualize as Importações

Em cada arquivo de provider, substitua a importação da classe base antiga pela nova:

```python
# Antes
from pepperpy.providers.base import BaseProvider

# Depois
from pepperpy.core.base_provider import BaseProvider
```

### 2. Atualize a Inicialização

A nova classe `BaseProvider` requer parâmetros específicos no construtor:

```python
# Antes
class MyProvider(BaseProvider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ...
        
# Depois
class MyProvider(BaseProvider):
    def __init__(self, provider_name=None, model_name=None, **kwargs):
        super().__init__(
            provider_type="my_provider_type",
            provider_name=provider_name,
            model_name=model_name,
            **kwargs
        )
        # ...
```

### 3. Atualize o Gerenciamento de Capacidades

A nova classe `BaseProvider` utiliza strings diretas para capacidades, em vez de objetos `ProviderCapability`:

```python
# Antes
from pepperpy.core.interfaces import ProviderCapability
capability = ProviderCapability("text_processing", "Process text", {})
self.add_capability(capability)
        
# Depois
self.add_capability("text_processing")
```

### 4. Substitua Exceções `ValueError` por `ProviderError`

A nova classe `BaseProvider` usa `ProviderError` em vez de `ValueError`:

```python
# Antes
from pepperpy.errors.core import ValueError
raise ValueError("Erro de configuração")
        
# Depois
from pepperpy.errors.core import ProviderError
raise ProviderError("Erro de configuração")
```

### 5. Atualize Métodos de Validação e Inicialização

A nova classe `BaseProvider` fornece métodos `initialize()` e `close()`:

```python
async def validate(self) -> None:
    """Validar configuração do provider."""
    if "api_key" not in self.config:
        raise ProviderError("API key is required")
    
async def initialize(self) -> None:
    """Inicializar recursos do provider."""
    # Estabelecer conexões, carregar modelos, etc.
    
async def close(self) -> None:
    """Liberar recursos do provider."""
    # Fechar conexões, liberar memória, etc.
```

### 6. Atualize o Registro de Providers

Substitua o uso do registro de providers:

```python
# Antes
from pepperpy.providers.base import provider_registry
provider_registry.register("my_type", MyProvider)
        
# Depois
from pepperpy.core.base_provider import provider_registry
provider_registry.register("my_type", MyProvider)
```

## Exemplo: Provider de LLM

Exemplo de um provider de LLM migrado:

```python
from pepperpy.core.base_provider import BaseProvider
from pepperpy.errors.core import ProviderError

class OpenAIProvider(BaseProvider):
    """Provider para modelos OpenAI."""
    
    def __init__(self, provider_name=None, model_name="gpt-4", api_key=None, **kwargs):
        super().__init__(
            provider_type="llm",
            provider_name=provider_name,
            model_name=model_name,
            api_key=api_key,
            **kwargs
        )
        # Adicionar capacidades
        self.add_capability("text_generation")
        self.add_capability("embeddings")
        
    async def validate(self) -> None:
        """Validar configuração do provider."""
        if "api_key" not in self.config:
            raise ProviderError("API key is required")
            
    async def initialize(self) -> None:
        """Inicializar o provider."""
        try:
            # Inicializar cliente OpenAI
            pass
        except Exception as e:
            raise ProviderError(f"Failed to initialize OpenAI provider: {str(e)}")
            
    async def close(self) -> None:
        """Liberar recursos do provider."""
        # Fechar conexões ou liberar recursos
        pass
```

## Benefícios da Migração

1. **Consistência**: Interface unificada para todos os providers
2. **Menos Duplicação**: Eliminação de código duplicado
3. **Melhor Tipagem**: Uso consistente de generics e tipagem
4. **Gerenciamento de Recursos**: Ciclo de vida consistente com initialize/close
5. **Logging Melhorado**: Logging consistente de eventos

## Lista de Verificação de Migração

- [ ] Atualizar importações
- [ ] Atualizar construtor com os novos parâmetros
- [ ] Atualizar gerenciamento de capacidades
- [ ] Atualizar exceções para usar ProviderError
- [ ] Implementar métodos initialize() e close()
- [ ] Atualizar registro de providers
- [ ] Testar provider migrado 