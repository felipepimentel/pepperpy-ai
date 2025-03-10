# PepperPy Framework Specification

## 1. Visão Geral

O PepperPy é um framework Python para desenvolvimento de aplicações baseadas em IA, com foco em Retrieval Augmented Generation (RAG), gerenciamento de memória, streaming, segurança, armazenamento e fluxos de trabalho. O framework é projetado para ser modular, extensível e fácil de usar.

## 2. Arquitetura

### 2.1 Módulos Principais

- **Core**: Funcionalidades fundamentais do framework
- **RAG**: Retrieval Augmented Generation
- **Memory**: Gerenciamento de memória de conversas
- **Streaming**: Processamento de dados em tempo real
- **Security**: Autenticação e autorização
- **Storage**: Armazenamento de dados
- **Workflow**: Orquestração de fluxos de trabalho

### 2.2 Estrutura de Diretórios

```
pepperpy/
├── core/
│   ├── public.py
│   ├── composition.py
│   ├── assistant/
│   │   └── implementations.py
│   └── intent/
│       └── types.py
├── rag/
├── memory/
├── streaming/
├── security/
├── storage/
├── workflow/
└── apps/
    └── assistant.py
```

### 2.3 Dependências

- Python 3.9+
- Bibliotecas essenciais: numpy, pandas, requests
- Bibliotecas opcionais: torch, transformers, langchain

## 3. Interfaces Públicas

### 3.1 Core

```python
from pepperpy.core.public import (
    ContentType, Metadata, OperationType, Resource, ResourceType,
    Result, StatusCode, generate_id, load_json, save_json
)
```

### 3.2 RAG

```python
from pepperpy.rag import (
    DocumentProcessor, Retriever, Generator, RAGPipeline
)
```

### 3.3 Memory

```python
from pepperpy.memory import (
    ConversationMemory, MemoryManager, MemoryProvider
)
```

### 3.4 Streaming

```python
from pepperpy.streaming import (
    StreamProcessor, StreamHandler, StreamTransformer
)
```

### 3.5 Security

```python
from pepperpy.security import (
    Authenticator, Authorizer, SecurityManager
)
```

### 3.6 Storage

```python
from pepperpy.storage import (
    StorageProvider, LocalStorage, VectorStorage
)
```

### 3.7 Workflow

```python
from pepperpy.workflow import (
    WorkflowManager, Task, Pipeline
)
```

## 4. Padrões de Implementação

### 4.1 Providers

Todos os providers devem implementar a interface `Provider`:

```python
class Provider:
    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
```

### 4.2 Processors

Todos os processors devem implementar a interface `Processor`:

```python
class Processor:
    async def process(self, input_data):
        raise NotImplementedError
```

### 4.3 Managers

Todos os managers devem implementar as interfaces `Initializable` e `Cleanable`:

```python
class Initializable:
    async def initialize(self):
        pass

class Cleanable:
    async def cleanup(self):
        pass
```

## 5. Convenções de Codificação

### 5.1 Docstrings

Todas as classes e funções públicas devem ter docstrings no estilo Google:

```python
def function_name(param1, param2):
    """Descrição da função.
    
    Args:
        param1: Descrição do parâmetro 1
        param2: Descrição do parâmetro 2
        
    Returns:
        Descrição do retorno
        
    Raises:
        ExceptionType: Descrição da exceção
    """
```

### 5.2 Type Hints

Todas as funções e métodos devem ter type hints:

```python
def function_name(param1: str, param2: int) -> bool:
    # Implementação
```

### 5.3 Tratamento de Erros

Usar exceções específicas e documentadas:

```python
class StorageError(Exception):
    """Erro relacionado ao armazenamento."""
    pass

class AuthenticationError(Exception):
    """Erro relacionado à autenticação."""
    pass
```

## 6. Exemplos de Uso

Os exemplos do framework estão organizados em uma estrutura padronizada para facilitar a compreensão e o uso:

### 6.1 Organização dos Exemplos

1. **Exemplos Básicos**: Localizados na raiz do diretório `examples/`
   - Demonstram funcionalidades fundamentais do framework
   - São exemplos simples e autocontidos
   - Servem como ponto de entrada para novos usuários

2. **Exemplos Específicos de Domínio**: Localizados em subpastas organizadas por funcionalidade
   - Cada subpasta corresponde a um módulo ou funcionalidade específica
   - Cada subpasta contém um arquivo README.md com documentação específica
   - Os exemplos demonstram casos de uso mais avançados ou específicos

### 6.2 Categorias de Exemplos

- **Básicos**: Exemplos fundamentais do framework
- **Memória**: Gerenciamento de memória
- **RAG**: Retrieval Augmented Generation
- **Assistentes**: Assistentes virtuais
- **Core**: Funcionalidades do núcleo
- **Composição**: Composição de componentes
- **Geração de Conteúdo**: Geração de conteúdo
- **Integrações**: Integração com serviços externos
- **Multimodal**: Processamento multimodal
- **Processamento de Texto**: Processamento de texto
- **Automação de Fluxos**: Automação de fluxos de trabalho

### 6.3 Padrões de Código para Exemplos

Todos os exemplos seguem uma estrutura padronizada e convenções de codificação conforme definido em `.product/EXAMPLE_STANDARDS.md`, incluindo:

1. **Docstrings Abrangentes**: Seções de Purpose, Requirements e Usage
2. **Type Hints**: Todas as funções e métodos incluem anotações de tipo
3. **Tratamento de Erros**: Tratamento adequado de exceções com exceções específicas
4. **Imports Organizados**: Agrupados por biblioteca padrão, terceiros e framework
5. **Código Assíncrono**: Padrão async/await quando apropriado
6. **Conformidade com PEP 8**: Formatação e estilo consistentes

## 7. Conclusão

O PepperPy é um framework modular e extensível para desenvolvimento de aplicações baseadas em IA. Ele fornece uma base sólida para construir aplicações complexas, com foco em RAG, gerenciamento de memória, streaming, segurança, armazenamento e fluxos de trabalho.

A estrutura padronizada de exemplos garante que os usuários possam aprender e utilizar o framework de forma eficiente, com exemplos claros e bem documentados para cada funcionalidade. 