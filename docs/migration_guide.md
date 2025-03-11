# Guia de Migração do PepperPy Framework

Este guia fornece instruções para migrar de versões anteriores do PepperPy Framework para a nova estrutura refatorada. A refatoração teve como objetivo simplificar a estrutura do framework, reduzir a duplicação de código e melhorar a manutenibilidade.

## Visão Geral das Mudanças

A refatoração incluiu as seguintes mudanças principais:

1. **Consolidação de Módulos**: Redução do número de diretórios e arquivos
2. **Padronização de APIs**: Interfaces consistentes em todo o framework
3. **Centralização de Utilitários**: Funções comuns movidas para módulos de utilidades
4. **Melhoria na Documentação**: Documentação mais completa e exemplos atualizados

## Mudanças de Importação

### Módulo HTTP

**Antes:**
```python
from pepperpy.http.client.utils import parse_json
from pepperpy.http.server.utils import format_headers
```

**Depois:**
```python
from pepperpy.http.utils import parse_json, format_headers
```

### Módulo RAG

**Antes:**
```python
from pepperpy.rag.document.loaders.text import TextLoader
from pepperpy.rag.document.processors.text import TextProcessor
from pepperpy.rag.pipeline.stages.retrieval import RetrievalStage
from pepperpy.rag.pipeline.stages.reranking import RerankingStage
from pepperpy.rag.pipeline.stages.generation import GenerationStage
```

**Depois:**
```python
from pepperpy.rag.document.loaders import TextLoader
from pepperpy.rag.document.processors import TextProcessor
from pepperpy.rag.pipeline.stages import RetrievalStage, RerankingStage, GenerationStage
```

### Módulo LLM

**Antes:**
```python
from pepperpy.llm.providers.openai import OpenAIProvider
from pepperpy.llm.utils.tokens import count_tokens
from pepperpy.llm.utils.prompts import format_prompt
```

**Depois:**
```python
from pepperpy.llm.providers import OpenAIProvider
from pepperpy.llm.utils import count_tokens, format_prompt
```

## Mudanças na API

### Registros e Gerenciadores

**Antes:**
```python
# Criação de registros específicos para cada tipo
document_registry = DocumentRegistry()
provider_registry = ProviderRegistry()

# Gerenciadores com diferentes assinaturas
document_manager = DocumentManager(document_registry)
provider_manager = ProviderManager("provider", provider_registry)
```

**Depois:**
```python
# Uso consistente de Registry para todos os tipos
document_registry = Registry[Type[Document]]("document_registry", "document")
provider_registry = Registry[Type[Provider]]("provider_registry", "provider")

# Assinatura consistente para todos os gerenciadores
document_manager = DocumentManager("document_manager", "document", document_registry)
provider_manager = ProviderManager("provider_manager", "provider", provider_registry)
```

### Utilitários de Documento

**Antes:**
```python
# Funções espalhadas em diferentes módulos
from pepperpy.rag.document.loaders.utils import clean_text
from pepperpy.rag.document.processors.utils import remove_html_tags
from pepperpy.rag.document.formatters.utils import clean_markdown
```

**Depois:**
```python
# Funções consolidadas em um único módulo de utilidades
from pepperpy.rag.document.utils import (
    clean_text,
    remove_html_tags,
    clean_markdown_formatting,
)
```

## Migração de Configurações

### Formato de Configuração

**Antes:**
```python
config = {
    "llm": {
        "provider": "openai",
        "model": "gpt-4",
    },
    "rag": {
        "document": {
            "loader": "text",
        },
        "pipeline": {
            "retrieval": {
                "provider": "faiss",
            },
        },
    },
}
```

**Depois:**
```python
config = {
    "llm": {
        "provider": {
            "type": "openai",
            "model": "gpt-4",
        },
    },
    "rag": {
        "document": {
            "loader": {
                "type": "text",
            },
        },
        "pipeline": {
            "stages": {
                "retrieval": {
                    "provider": {
                        "type": "faiss",
                    },
                },
            },
        },
    },
}
```

## Exemplos de Migração

### Exemplo 1: Processamento de Documento

**Antes:**
```python
from pepperpy.rag.document.loaders.text import TextLoader
from pepperpy.rag.document.processors.text import TextProcessor
from pepperpy.rag.document.formatters.markdown import MarkdownFormatter

loader = TextLoader()
processor = TextProcessor()
formatter = MarkdownFormatter()

document = loader.load("document.txt")
processed = processor.process(document)
formatted = formatter.format(processed)
```

**Depois:**
```python
from pepperpy.rag.document.loaders import TextLoader
from pepperpy.rag.document.processors import TextProcessor
from pepperpy.rag.document.utils import clean_markdown_formatting

loader = TextLoader()
processor = TextProcessor()

document = loader.load("document.txt")
processed = processor.process(document)
formatted_text = clean_markdown_formatting(processed.content)
```

### Exemplo 2: Pipeline RAG

**Antes:**
```python
from pepperpy.rag.pipeline.builder import PipelineBuilder
from pepperpy.rag.pipeline.stages.retrieval import RetrievalStage
from pepperpy.rag.pipeline.stages.reranking import RerankingStage
from pepperpy.rag.pipeline.stages.generation import GenerationStage

pipeline = (
    PipelineBuilder()
    .add_stage("retrieval", RetrievalStage(retrieval_config))
    .add_stage("reranking", RerankingStage(reranking_config))
    .add_stage("generation", GenerationStage(generation_config))
    .build()
)
```

**Depois:**
```python
from pepperpy.rag.pipeline.builder import RAGPipelineBuilder
from pepperpy.rag.pipeline.stages import RetrievalStage, RerankingStage, GenerationStage

pipeline = (
    RAGPipelineBuilder()
    .with_retrieval(RetrievalStage(retrieval_config))
    .with_reranking(RerankingStage(reranking_config))
    .with_generation(GenerationStage(generation_config))
    .build()
)
```

## Funcionalidades Descontinuadas

As seguintes funcionalidades foram descontinuadas na nova versão:

1. **Formatadores de Documento**: Substituídos por funções utilitárias em `pepperpy.rag.document.utils`
2. **Registros Específicos**: Substituídos pelo `Registry` genérico
3. **Utilitários Duplicados**: Consolidados em módulos centralizados

## Funcionalidades Novas

As seguintes funcionalidades foram adicionadas na nova versão:

1. **Utilitários HTTP**: Funções para manipulação de requisições e respostas HTTP
2. **Utilitários de Documento**: Funções para processamento de texto e documentos
3. **Utilitários LLM**: Funções para manipulação de tokens, prompts e respostas
4. **Pipeline RAG Simplificado**: API mais intuitiva para construção de pipelines RAG

## Próximos Passos

1. Atualize suas importações conforme as instruções acima
2. Adapte suas configurações para o novo formato
3. Substitua o uso de classes descontinuadas pelas novas funções utilitárias
4. Consulte os exemplos atualizados em `examples/` para ver as melhores práticas

## Suporte

Se você encontrar problemas durante a migração, entre em contato com a equipe de suporte ou abra uma issue no repositório do projeto. 