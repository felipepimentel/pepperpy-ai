# Referência da API do PepperPy Framework

Este documento fornece uma referência completa da API do PepperPy Framework após a refatoração. Ele descreve os principais módulos, classes e funções disponíveis para uso.

## Módulo HTTP

O módulo HTTP fornece funcionalidades para comunicação HTTP, incluindo cliente e servidor.

### Utilitários HTTP

```python
from pepperpy.http.utils import (
    parse_json,
    check_status_code,
    get_content_type,
    is_json_content,
    format_headers,
    parse_query_params,
)
```

#### `parse_json(content: Union[str, bytes], status_code: Optional[int] = None) -> Any`

Analisa conteúdo JSON a partir de uma string ou bytes.

**Parâmetros:**
- `content`: O conteúdo JSON a ser analisado, como string ou bytes
- `status_code`: Código de status HTTP opcional para contexto de erro

**Retorna:**
- O conteúdo JSON analisado como objetos Python (dict, list, etc.)

**Exceções:**
- `ResponseError`: Se o conteúdo não puder ser analisado como JSON válido

#### `check_status_code(status_code: int) -> None`

Valida o código de status HTTP e levanta erros apropriados.

**Parâmetros:**
- `status_code`: O código de status HTTP a ser verificado

**Exceções:**
- `ResponseError`: Se o código de status indicar um erro de cliente ou servidor

#### `get_content_type(headers: Dict[str, str]) -> str`

Extrai e normaliza o tipo de conteúdo dos cabeçalhos HTTP.

**Parâmetros:**
- `headers`: Dicionário de cabeçalhos HTTP

**Retorna:**
- O tipo de conteúdo normalizado em minúsculas, sem parâmetros

#### `is_json_content(headers: Dict[str, str]) -> bool`

Determina se o tipo de conteúdo nos cabeçalhos indica JSON.

**Parâmetros:**
- `headers`: Dicionário de cabeçalhos HTTP

**Retorna:**
- `True` se o tipo de conteúdo indicar JSON, `False` caso contrário

#### `format_headers(headers: Dict[str, str]) -> Dict[str, str]`

Normaliza cabeçalhos HTTP para garantir consistência de maiúsculas/minúsculas.

**Parâmetros:**
- `headers`: Dicionário de cabeçalhos HTTP com maiúsculas/minúsculas mistas

**Retorna:**
- Dicionário com nomes de cabeçalho normalizados em minúsculas

#### `parse_query_params(query_string: str) -> Dict[str, str]`

Analisa parâmetros de consulta de URL em um dicionário.

**Parâmetros:**
- `query_string`: String de consulta URL (sem o '?' inicial)

**Retorna:**
- Dicionário de parâmetros de consulta

### Cliente HTTP

```python
from pepperpy.http.client import HTTPClient, HTTPResponse
```

#### `class HTTPClient`

Cliente HTTP para fazer requisições a servidores.

**Métodos:**
- `async get(url: str, **kwargs) -> HTTPResponse`: Faz uma requisição GET
- `async post(url: str, **kwargs) -> HTTPResponse`: Faz uma requisição POST
- `async put(url: str, **kwargs) -> HTTPResponse`: Faz uma requisição PUT
- `async delete(url: str, **kwargs) -> HTTPResponse`: Faz uma requisição DELETE
- `async request(method: str, url: str, **kwargs) -> HTTPResponse`: Faz uma requisição genérica

**Parâmetros comuns:**
- `url`: URL para a requisição
- `headers`: Cabeçalhos HTTP opcionais
- `params`: Parâmetros de consulta opcionais
- `json`: Dados JSON opcionais para enviar
- `data`: Dados de formulário opcionais para enviar
- `timeout`: Tempo limite opcional em segundos

#### `class HTTPResponse`

Resposta de uma requisição HTTP.

**Atributos:**
- `status_code`: Código de status HTTP
- `headers`: Cabeçalhos da resposta
- `content`: Conteúdo da resposta como bytes
- `text`: Conteúdo da resposta como texto
- `json()`: Método para analisar o conteúdo como JSON

### Servidor HTTP

```python
from pepperpy.http.server import HTTPServer, Request, Response
```

#### `class HTTPServer`

Servidor HTTP para lidar com requisições de clientes.

**Métodos:**
- `route(path: str, methods: List[str])`: Decorador para registrar rotas
- `async start(host: str = "0.0.0.0", port: int = 8000)`: Inicia o servidor
- `async stop()`: Para o servidor

#### `class Request`

Representa uma requisição HTTP recebida pelo servidor.

**Atributos:**
- `method`: Método HTTP (GET, POST, etc.)
- `path`: Caminho da URL
- `headers`: Cabeçalhos da requisição
- `query_params`: Parâmetros de consulta
- `json()`: Método para analisar o corpo como JSON
- `form()`: Método para analisar o corpo como dados de formulário

#### `class Response`

Representa uma resposta HTTP a ser enviada pelo servidor.

**Métodos:**
- `json(data: Any, status_code: int = 200)`: Cria uma resposta JSON
- `text(content: str, status_code: int = 200)`: Cria uma resposta de texto
- `html(content: str, status_code: int = 200)`: Cria uma resposta HTML
- `file(path: str, status_code: int = 200)`: Cria uma resposta de arquivo

## Módulo RAG

O módulo RAG (Retrieval Augmented Generation) fornece funcionalidades para processamento de documentos, recuperação e geração.

### Utilitários de Documento

```python
from pepperpy.rag.utils import (
    clean_text,
    remove_html_tags,
    clean_markdown_formatting,
    split_text,
    calculate_text_statistics,
)
```

#### `clean_text(text: str, remove_extra_whitespace: bool = True, normalize_unicode: bool = True, lowercase: bool = False) -> str`

Limpa e normaliza texto para melhor processamento.

**Parâmetros:**
- `text`: O texto de entrada a ser limpo
- `remove_extra_whitespace`: Se deve colapsar múltiplos espaços em branco em um único espaço
- `normalize_unicode`: Se deve normalizar caracteres unicode para sua forma canônica
- `lowercase`: Se deve converter todo o texto para minúsculas

**Retorna:**
- O texto limpo e normalizado

#### `remove_html_tags(text: str) -> str`

Extrai conteúdo de texto simples de texto formatado em HTML.

**Parâmetros:**
- `text`: Texto formatado em HTML para processar

**Retorna:**
- Texto simples com todos os elementos HTML removidos

#### `clean_markdown_formatting(text: str) -> str`

Remove formatação Markdown preservando o conteúdo.

**Parâmetros:**
- `text`: Texto formatado em Markdown para processar

**Retorna:**
- Texto simples com formatação Markdown removida

#### `split_text(text: str, chunk_size: int = 1000, overlap: int = 200, separator: str = "\n") -> List[str]`

Divide texto em chunks menores com sobreposição opcional.

**Parâmetros:**
- `text`: Texto a ser dividido
- `chunk_size`: Tamanho máximo de cada chunk em caracteres
- `overlap`: Número de caracteres de sobreposição entre chunks
- `separator`: Separador a ser usado para dividir o texto

**Retorna:**
- Lista de chunks de texto

#### `calculate_text_statistics(text: str) -> Dict[str, int]`

Calcula estatísticas sobre um texto.

**Parâmetros:**
- `text`: Texto para analisar

**Retorna:**
- Dicionário com estatísticas como contagem de caracteres, palavras, frases e parágrafos

### Documento e Chunks

```python
from pepperpy.rag.document.core import Document, DocumentChunk, DocumentMetadata
```

#### `class Document`

Representa um documento completo no sistema RAG.

**Atributos:**
- `id`: Identificador único do documento
- `content`: Conteúdo do documento
- `metadata`: Metadados do documento
- `chunks`: Lista de chunks do documento

**Métodos:**
- `to_chunks(chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]`: Divide o documento em chunks

#### `class DocumentChunk`

Representa um chunk de um documento.

**Atributos:**
- `id`: Identificador único do chunk
- `document_id`: Identificador do documento pai
- `content`: Conteúdo do chunk
- `metadata`: Metadados do chunk
- `embedding`: Embedding vetorial opcional do chunk

#### `class DocumentMetadata`

Metadados para documentos e chunks.

**Atributos:**
- `source`: Fonte do documento
- `created_at`: Data de criação
- `author`: Autor do documento
- `title`: Título do documento
- `tags`: Tags associadas ao documento
- `custom`: Dicionário para metadados personalizados

### Pipeline RAG

```python
from pepperpy.rag.pipeline.builder import RAGPipelineBuilder
from pepperpy.rag.pipeline.stages import RetrievalStage, RerankingStage, GenerationStage
```

#### `class RAGPipelineBuilder`

Construtor para pipelines RAG.

**Métodos:**
- `with_retrieval(stage: RetrievalStage) -> RAGPipelineBuilder`: Adiciona estágio de recuperação
- `with_reranking(stage: RerankingStage) -> RAGPipelineBuilder`: Adiciona estágio de reranking
- `with_generation(stage: GenerationStage) -> RAGPipelineBuilder`: Adiciona estágio de geração
- `build() -> RAGPipeline`: Constrói o pipeline RAG

#### `class RAGPipeline`

Pipeline completo para Retrieval Augmented Generation.

**Métodos:**
- `async process(query: str, metadata: Optional[Dict[str, Any]] = None) -> RAGPipelineOutput`: Processa uma consulta através do pipeline

#### `class RetrievalStage`

Estágio de recuperação para o pipeline RAG.

**Métodos:**
- `async process(query: str, metadata: Optional[Dict[str, Any]] = None) -> RetrievalResult`: Recupera documentos relevantes

#### `class RerankingStage`

Estágio de reranking para o pipeline RAG.

**Métodos:**
- `async process(query: str, chunks: List[DocumentChunk], metadata: Optional[Dict[str, Any]] = None) -> RerankingResult`: Reordena chunks de documento

#### `class GenerationStage`

Estágio de geração para o pipeline RAG.

**Métodos:**
- `async process(query: str, chunks: List[DocumentChunk], metadata: Optional[Dict[str, Any]] = None) -> GenerationResult`: Gera resposta baseada nos chunks

## Módulo LLM

O módulo LLM (Large Language Model) fornece funcionalidades para interagir com modelos de linguagem.

### Utilitários LLM

```python
from pepperpy.llm.utils import (
    count_tokens,
    format_prompt,
    truncate_prompt,
    parse_response,
)
```

#### `count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int`

Conta o número de tokens em um texto para um modelo específico.

**Parâmetros:**
- `text`: Texto para contar tokens
- `model`: Nome do modelo para usar para contagem de tokens

**Retorna:**
- Número de tokens no texto

#### `format_prompt(template: str, **kwargs) -> str`

Formata um template de prompt com variáveis.

**Parâmetros:**
- `template`: Template de prompt com placeholders
- `**kwargs`: Variáveis para substituir no template

**Retorna:**
- Prompt formatado

#### `truncate_prompt(prompt: str, max_tokens: int, model: str = "gpt-3.5-turbo") -> str`

Trunca um prompt para caber dentro de um limite de tokens.

**Parâmetros:**
- `prompt`: Prompt para truncar
- `max_tokens`: Número máximo de tokens permitidos
- `model`: Nome do modelo para usar para contagem de tokens

**Retorna:**
- Prompt truncado

#### `parse_response(response: str, output_format: str = "text") -> Any`

Analisa a resposta de um LLM em vários formatos.

**Parâmetros:**
- `response`: Resposta do LLM
- `output_format`: Formato de saída desejado ("text", "json", "list", etc.)

**Retorna:**
- Resposta analisada no formato especificado

### Providers LLM

```python
from pepperpy.llm.providers import LLMProvider, OpenAIProvider, AnthropicProvider
```

#### `class LLMProvider`

Classe base para providers LLM.

**Métodos:**
- `async generate(prompt: str, **kwargs) -> str`: Gera texto a partir de um prompt
- `async chat(messages: List[Dict[str, str]], **kwargs) -> str`: Gera resposta para uma conversa
- `async embed(text: str, **kwargs) -> List[float]`: Cria embeddings para um texto

#### `class OpenAIProvider`

Provider para modelos OpenAI.

**Métodos:**
- Herda todos os métodos de `LLMProvider`
- Implementações específicas para a API OpenAI

#### `class AnthropicProvider`

Provider para modelos Anthropic.

**Métodos:**
- Herda todos os métodos de `LLMProvider`
- Implementações específicas para a API Anthropic

## Módulo Core

O módulo Core fornece funcionalidades básicas usadas em todo o framework.

### Registros e Gerenciadores

```python
from pepperpy.core.base_registry import Registry
from pepperpy.core.base_manager import BaseManager
```

#### `class Registry[T]`

Registro para componentes no framework.

**Métodos:**
- `register(id: str, item: T) -> None`: Registra um item
- `unregister(id: str) -> None`: Remove um item do registro
- `get(id: str) -> Optional[T]`: Obtém um item pelo ID
- `list() -> List[str]`: Lista todos os IDs registrados

#### `class BaseManager[P]`

Classe base para gerenciadores no framework.

**Métodos:**
- `register_provider(provider_type: str, provider_class: Type[P]) -> None`: Registra um tipo de provider
- `set_default_provider(provider_type: str) -> None`: Define o provider padrão
- `async get_provider(provider_type: Optional[str] = None, **kwargs) -> P`: Obtém uma instância de provider

### Composição

```python
from pepperpy.core.composition import compose, compose_parallel, Sources, Processors, Outputs
```

#### `async compose(source: Source[T], processor: Processor[T, U], output: Output[U], metadata: Optional[Dict[str, Any]] = None) -> None`

Compõe uma fonte, processador e saída em um pipeline.

**Parâmetros:**
- `source`: Fonte de dados
- `processor`: Processador de dados
- `output`: Saída de dados
- `metadata`: Metadados opcionais

#### `async compose_parallel(sources: List[Source[T]], processor: Processor[List[T], U], output: Output[U], metadata: Optional[Dict[str, Any]] = None) -> None`

Compõe múltiplas fontes em paralelo com um processador e saída.

**Parâmetros:**
- `sources`: Lista de fontes de dados
- `processor`: Processador de dados
- `output`: Saída de dados
- `metadata`: Metadados opcionais

#### `class Sources`

Coleção de componentes de fonte.

**Métodos:**
- `from_value(value: T) -> Source[T]`: Cria uma fonte a partir de um valor estático
- `from_function(func: Any) -> Source[Any]`: Cria uma fonte a partir de uma função

#### `class Processors`

Coleção de componentes de processador.

**Métodos:**
- `from_function(func: Any) -> Processor[Any, Any]`: Cria um processador a partir de uma função

#### `class Outputs`

Coleção de componentes de saída.

**Métodos:**
- `to_list() -> Output[Any]`: Cria uma saída que coleta valores em uma lista
- `to_function(func: Any) -> Output[Any]`: Cria uma saída a partir de uma função

### Intenção

```python
from pepperpy.core.intent import Intent, IntentBuilder, IntentManager, process_intent
```

#### `class Intent`

Definição de intenção.

**Atributos:**
- `name`: Nome da intenção
- `confidence`: Pontuação de confiança
- `parameters`: Parâmetros da intenção
- `metadata`: Metadados da intenção

#### `class IntentBuilder`

Construtor para objetos de intenção.

**Métodos:**
- `with_confidence(confidence: float) -> IntentBuilder`: Define a pontuação de confiança
- `with_parameter(name: str, value: Any) -> IntentBuilder`: Adiciona um parâmetro
- `with_metadata(metadata: Dict[str, Any]) -> IntentBuilder`: Adiciona metadados
- `build() -> Intent`: Constrói a intenção

#### `class IntentManager`

Gerenciador para reconhecimento de intenção.

**Métodos:**
- `async recognize(text: str, provider_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[Intent]`: Reconhece intenções em texto
- `async train(examples: List[Dict[str, Any]], provider_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None`: Treina o reconhecedor de intenção

#### `async process_intent(text: str, manager: Optional[IntentManager] = None, provider_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[Intent]`

Processa texto para reconhecer intenções.

**Parâmetros:**
- `text`: Texto para analisar
- `manager`: Gerenciador de intenção opcional
- `provider_id`: Provider opcional para usar
- `metadata`: Metadados opcionais

**Retorna:**
- Lista de intenções reconhecidas

## Módulo Workflows

O módulo Workflows fornece funcionalidades para definir e executar fluxos de trabalho.

### Templates

```python
from pepperpy.workflows.templates import Template, TemplateManager, TemplateProvider
```

#### `class Template`

Definição de template de fluxo de trabalho.

**Atributos:**
- `name`: Nome do template
- `description`: Descrição do template
- `steps`: Lista de passos do fluxo de trabalho
- `metadata`: Metadados do template

#### `class TemplateManager`

Gerenciador para templates de fluxo de trabalho.

**Métodos:**
- `async load_template(template_id: str, provider_id: Optional[str] = None) -> Template`: Carrega um template por ID
- `async save_template(template: Template, provider_id: Optional[str] = None) -> str`: Salva um template
- `async list_templates(provider_id: Optional[str] = None) -> List[str]`: Lista IDs de templates disponíveis

#### `class TemplateProvider`

Classe base para providers de template.

**Métodos:**
- `async load_template(template_id: str) -> Template`: Carrega um template por ID
- `async save_template(template: Template) -> str`: Salva um template
- `async list_templates() -> List[str]`: Lista IDs de templates disponíveis 