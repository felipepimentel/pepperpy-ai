# PepperPy Framework

Um framework moderno e flexível para aplicações de IA em Python, com foco em composição, reutilização e extensibilidade.

## Visão Geral

O PepperPy Framework é uma biblioteca Python projetada para simplificar o desenvolvimento de aplicações de IA, fornecendo componentes modulares e reutilizáveis para tarefas comuns como:

- Processamento de documentos e texto
- Integração com modelos de linguagem (LLMs)
- Construção de pipelines RAG (Retrieval Augmented Generation)
- Comunicação HTTP cliente/servidor
- Reconhecimento de intenção
- Composição de fluxos de trabalho

## Instalação

```bash
pip install pepperpy
```

Ou usando Poetry:

```bash
poetry add pepperpy
```

## Recursos Principais

### Módulo HTTP

Funcionalidades para comunicação HTTP, incluindo cliente e servidor:

```python
from pepperpy.http.utils import parse_json, format_headers
from pepperpy.http.client import HTTPClient
from pepperpy.http.server import HTTPServer, Request, Response

# Cliente HTTP
client = HTTPClient()
response = await client.get("https://api.example.com/data")
data = response.json()

# Servidor HTTP
server = HTTPServer()

@server.route("/api/data", methods=["GET"])
async def get_data(request: Request) -> Response:
    return Response.json({"message": "Hello, world!"})

await server.start(host="0.0.0.0", port=8000)
```

### Módulo RAG

Funcionalidades para processamento de documentos, recuperação e geração:

```python
from pepperpy.rag.document.utils import clean_text, remove_html_tags
from pepperpy.rag.document.loaders import TextLoader
from pepperpy.rag.pipeline.builder import RAGPipelineBuilder
from pepperpy.rag.pipeline.stages import RetrievalStage, GenerationStage

# Processamento de documento
text = "<p>Este é um <b>exemplo</b> de texto.</p>"
clean = remove_html_tags(text)  # "Este é um exemplo de texto."

# Pipeline RAG
pipeline = (
    RAGPipelineBuilder()
    .with_retrieval(RetrievalStage(retrieval_config))
    .with_generation(GenerationStage(generation_config))
    .build()
)

result = await pipeline.process("Qual é a capital do Brasil?")
```

### Módulo LLM

Funcionalidades para interagir com modelos de linguagem:

```python
from pepperpy.llm.utils import count_tokens, format_prompt
from pepperpy.llm.providers import OpenAIProvider

# Utilitários LLM
tokens = count_tokens("Este é um exemplo de texto.")
prompt = format_prompt("Olá, {name}!", name="Mundo")

# Provider LLM
provider = OpenAIProvider(api_key="sk-...")
response = await provider.generate("Qual é a capital do Brasil?")
```

### Módulo Core

Funcionalidades básicas usadas em todo o framework:

```python
from pepperpy.core.composition import compose, Sources, Processors, Outputs
from pepperpy.core.intent import IntentBuilder, process_intent

# Composição
source = Sources.from_value("Olá, mundo!")
processor = Processors.from_function(lambda text: text.upper())
output = Outputs.to_list()

await compose(source, processor, output)

# Intenção
intent = (
    IntentBuilder("greeting")
    .with_confidence(0.95)
    .with_parameter("name", "mundo")
    .build()
)

intents = await process_intent("Olá, como vai?")
```

## Estrutura do Framework

```
pepperpy/
├── cache/           # Gerenciamento de cache
├── cli/             # Interface de linha de comando
├── config/          # Gerenciamento de configuração
├── core/            # Funcionalidades básicas
├── data/            # Manipulação de dados
├── errors/          # Definições de erros
├── events/          # Sistema de eventos
├── http/            # Cliente e servidor HTTP
├── interfaces/      # Interfaces comuns
├── llm/             # Integração com LLMs
├── memory/          # Gerenciamento de memória
├── plugins/         # Sistema de plugins
├── providers/       # Base para provedores
├── rag/             # Sistema RAG
├── registry/        # Sistema de registro
├── storage/         # Armazenamento persistente
├── streaming/       # Processamento de streams
├── types/           # Definições de tipos
├── utils/           # Utilitários gerais
└── workflows/       # Gerenciamento de fluxos
```

## Exemplos

Consulte a pasta `examples/` para exemplos completos de uso do framework:

- `examples/http_utils_example.py`: Demonstração de utilitários HTTP
- `examples/rag_document_utils_example.py`: Demonstração de utilitários de documento RAG
- `examples/llm_integration_example.py`: Demonstração de integração com LLMs
- `examples/rag_pipeline_example.py`: Demonstração de pipeline RAG completo

## Documentação

Para documentação completa, consulte:

- [Referência da API](docs/api_reference.md)
- [Guia de Migração](docs/migration_guide.md)
- [Guia de Arquitetura](docs/architecture_guide.md)
- [Exemplos](examples/)

## Contribuindo

Contribuições são bem-vindas! Por favor, leia o [guia de contribuição](CONTRIBUTING.md) para mais informações.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 

