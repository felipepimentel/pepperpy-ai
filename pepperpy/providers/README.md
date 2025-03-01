# Estratégia de Providers no PepperPy

Este documento descreve a estratégia de providers no framework PepperPy, incluindo a organização, diretrizes de implementação e melhores práticas.

## Organização dos Providers

### Providers Genéricos Centralizados

Os providers genéricos são centralizados no módulo `pepperpy/providers/`. Esta centralização oferece várias vantagens:

- **Descoberta**: Facilita a localização de implementações disponíveis
- **Consistência**: Promove padrões de implementação uniformes
- **Manutenção**: Permite que atualizações e correções sejam aplicadas de forma centralizada
- **Documentação**: Possibilita uma documentação unificada para todos os providers genéricos

Exemplos de providers genéricos incluem:

- `providers/llm/`: Providers para modelos de linguagem (OpenAI, Anthropic, etc.)
- `providers/cloud/`: Providers para serviços de nuvem (AWS, GCP, etc.)
- `providers/storage/`: Providers para armazenamento (local, cloud, SQL, etc.)
- `providers/vision/`: Providers para processamento de visão computacional
- `providers/audio/`: Providers para processamento de áudio

### Providers Específicos de Domínio

Providers específicos de domínio devem ficar junto aos módulos que os utilizam. Isso é apropriado quando:

- O provider é altamente especializado para um domínio específico
- A implementação depende fortemente de detalhes internos do módulo
- O provider não tem utilidade fora do contexto do módulo específico

Exemplos incluem:

- `embedding/providers/`: Providers específicos para embeddings vetoriais
- `memory/providers/`: Providers específicos para sistemas de memória
- `rag/providers/`: Providers específicos para sistemas RAG (Retrieval Augmented Generation)

## Diretrizes para Implementação de Novos Providers

### 1. Determinando a Localização

Para decidir onde implementar um novo provider, considere:

- **É um provider genérico?** Se pode ser usado por múltiplos módulos, deve estar em `providers/`
- **É específico de domínio?** Se é altamente especializado para um único módulo, deve estar em `[módulo]/providers/`

### 2. Estrutura de Arquivos

Todo provider deve seguir esta estrutura básica:

```
providers/[categoria]/
  ├── __init__.py       # Exporta as classes públicas
  ├── base.py           # Define interfaces e classes base
  ├── [implementação].py  # Implementação específica (ex: openai.py)
```

### 3. Implementação

Ao implementar um novo provider:

1. **Herdar da classe base**: Todo provider deve herdar da classe base apropriada
   ```python
   from pepperpy.providers.[categoria].base import BaseProvider
   
   class MyProvider(BaseProvider):
       ...
   ```

2. **Implementar métodos obrigatórios**: Todos os métodos abstratos devem ser implementados

3. **Documentar requisitos**: Documentar dependências, configurações e credenciais necessárias

4. **Incluir testes**: Fornecer testes unitários e de integração (quando possível)

### 4. Registro de Providers

Todos os providers devem ser registrados no sistema de registro apropriado:

```python
from pepperpy.core.registry import registry

@registry.register("my_provider")
class MyProvider(BaseProvider):
    ...
```

### 5. Configuração

Providers devem aceitar configuração via:

- Parâmetros no construtor
- Variáveis de ambiente (via `pepperpy.core.config`)
- Arquivos de configuração

### 6. Tratamento de Erros

Providers devem:

- Converter erros específicos da implementação para exceções do PepperPy
- Fornecer mensagens de erro claras e acionáveis
- Implementar estratégias de retry quando apropriado

## Exemplos

### Exemplo de Provider Genérico

```python
# pepperpy/providers/llm/my_llm.py
from pepperpy.providers.llm.base import BaseLLMProvider

class MyLLMProvider(BaseLLMProvider):
    def __init__(self, api_key=None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or self._get_api_key_from_config()
        
    def generate(self, prompt, **kwargs):
        # Implementação específica
        ...
```

### Exemplo de Provider Específico de Domínio

```python
# pepperpy/embedding/providers/my_embedding.py
from pepperpy.embedding.providers.base import BaseEmbeddingProvider

class MyEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_name, **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name
        
    def embed(self, text, **kwargs):
        # Implementação específica
        ...
```

## Melhores Práticas

1. **Desacoplamento**: Minimize dependências entre providers e o código principal
2. **Configuração flexível**: Permita múltiplas formas de configuração
3. **Documentação clara**: Documente requisitos, limitações e exemplos de uso
4. **Tratamento de erros robusto**: Converta erros específicos para exceções do framework
5. **Testes abrangentes**: Teste tanto o comportamento normal quanto casos de erro
6. **Métricas e observabilidade**: Integre com o sistema de métricas do PepperPy

# Provider Migration Notice

## Important: Providers Have Been Moved

The providers in this directory have been moved to their respective domain directories for better modularity and maintainability.

### New Provider Locations

- `providers/audio/` → `multimodal/audio/providers/`
- `providers/vision/` → `multimodal/vision/providers/`
- `providers/agent/` → `agents/providers/`
- `providers/storage/` → `storage/providers/`
- `providers/cloud/` → `cloud/providers/`
- `providers/config/` → `core/config/providers/`

### Why This Change?

This reorganization follows the principle of high cohesion, keeping implementations close to their abstractions. Benefits include:

- **Domain-Specific Organization**: All components related to a domain are in one place
- **Better Maintainability**: Developers working on a domain have access to all its implementation
- **Consistency**: Follows the pattern already established with `embedding/providers/` and `llm/providers/`
- **Modern Framework Design**: Aligns with practices in contemporary frameworks

### How to Update Your Code

If you were importing from the old locations, update your imports as follows:

```python
# Old import
from pepperpy.providers.audio import SomeAudioProvider

# New import
from pepperpy.multimodal.audio.providers import SomeAudioProvider
```

### Backward Compatibility

For backward compatibility, the main `pepperpy` package still re-exports all providers, so code that imports directly from `pepperpy` will continue to work:

```python
# This still works
from pepperpy import SomeAudioProvider
```

However, direct imports from `pepperpy.providers.*` are deprecated and will be removed in a future version.
