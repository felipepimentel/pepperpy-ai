# Guia de Migração para a Nova Estrutura de Providers

Este guia descreve como atualizar seu código para usar a nova estrutura centralizada de providers no framework PepperPy.

## Contexto

Como parte da padronização do framework, todos os providers foram centralizados no módulo `pepperpy.providers`. Isso significa que as importações de providers de módulos específicos de domínio (como `pepperpy.embedding.providers`) devem ser atualizadas para apontar para o novo local (`pepperpy.providers.embedding`).

## Mapeamento de Módulos

A tabela abaixo mostra o mapeamento entre os módulos antigos e novos:

| Módulo Antigo | Módulo Novo |
|---------------|-------------|
| `pepperpy.embedding.providers` | `pepperpy.providers.embedding` |
| `pepperpy.memory.providers` | `pepperpy.providers.memory` |
| `pepperpy.rag.providers` | `pepperpy.providers.rag` |
| `pepperpy.cloud.providers` | `pepperpy.providers.cloud` |
| `pepperpy.llm.providers` | `pepperpy.providers.llm` |

## Como Atualizar suas Importações

### Antes

```python
from pepperpy.embedding.providers import OpenAIEmbeddingProvider
from pepperpy.memory.providers import RedisMemoryProvider
from pepperpy.rag.providers import SomeRAGProvider
from pepperpy.cloud.providers import AWSProvider
from pepperpy.llm.providers import OpenAIProvider
```

### Depois

```python
from pepperpy.providers.embedding import OpenAIEmbeddingProvider
from pepperpy.providers.memory import RedisMemoryProvider
from pepperpy.providers.rag import SomeRAGProvider
from pepperpy.providers.cloud import AWSProvider
from pepperpy.providers.llm import OpenAIProvider
```

## Compatibilidade

Para garantir a compatibilidade com código existente, foram criados stubs nos locais originais dos providers, redirecionando para os novos locais. Esses stubs emitem avisos de depreciação e serão removidos em uma versão futura do framework.

Se você ver um aviso como este:

```
DeprecationWarning: The module pepperpy.embedding.providers has been moved to pepperpy.providers.embedding. 
Please update your imports. This compatibility stub will be removed in a future version.
```

Você deve atualizar suas importações conforme descrito acima.

## Usando o Módulo de Migração

O framework fornece um módulo de migração para ajudar na transição para a nova estrutura de providers:

```python
from pepperpy.migration import import_from_new_location

# Importar um provider específico
OpenAIEmbeddingProvider = import_from_new_location(
    "pepperpy.embedding.providers",
    "pepperpy.providers.embedding",
    "OpenAIEmbeddingProvider"
)

# Importar um módulo inteiro
embedding_providers = import_from_new_location(
    "pepperpy.embedding.providers",
    "pepperpy.providers.embedding"
)
```

## Cronograma de Depreciação

Os stubs de compatibilidade serão mantidos por 2 versões do framework e depois serão removidos. Recomendamos que você atualize suas importações o mais rápido possível para evitar problemas futuros. 