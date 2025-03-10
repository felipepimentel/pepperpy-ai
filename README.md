# PepperPy: Framework Moderno para Aplicações de IA em Python

PepperPy é um framework flexível e poderoso para construir aplicações de IA em Python, oferecendo múltiplos níveis de abstração para atender a diferentes necessidades e perfis de usuários.

## Visão Geral

O PepperPy oferece três níveis de abstração:

1. **Composição Universal**: API de baixo nível para compor componentes em pipelines
2. **Abstração por Intenção**: API de médio nível para expressar intenções de forma natural
3. **Templates**: API de alto nível com soluções pré-configuradas

## Recursos Principais

### Composição Funcional

Crie pipelines de processamento combinando componentes de forma flexível:

```python
import pepperpy as pp

# Criar um pipeline de processamento de texto
pipeline = (
    pp.Pipeline.builder()
    .add(pp.sources.text.from_string("Olá, mundo!"))
    .add(pp.processors.text.tokenize())
    .add(pp.processors.text.remove_stopwords())
    .add(pp.outputs.console())
    .build()
)

# Executar o pipeline
result = pipeline.run()
```

### Abstração por Intenção

Expresse suas intenções em linguagem natural e deixe o PepperPy configurar o pipeline adequado:

```python
import pepperpy as pp

# Criar um pipeline a partir de uma intenção
pipeline = pp.create_pipeline_from_intent(
    "Extrair entidades de um texto e gerar um resumo"
)

# Processar um documento
result = pipeline.process("caminho/para/documento.txt")
```

### Templates Pré-configurados

Use soluções prontas para casos de uso comuns:

```python
import pepperpy as pp

# Criar uma aplicação de perguntas e respostas
app = pp.create_app("question_answering")

# Indexar documentos
app.index("caminho/para/documentos/")

# Fazer uma pergunta
resposta = app.query("Qual é a capital da França?")
```

### Assistência ao Desenvolvedor (Zero-to-Hero)

Assistentes interativos para guiar a criação de componentes e pipelines:

```python
import pepperpy as pp

# Criar um assistente para construção de pipelines
assistant = pp.create_assistant("pipeline_builder")

# Criar um pipeline com assistência
pipeline = assistant.create("um pipeline para análise de sentimentos")
```

### Diagnóstico Inteligente

Ferramentas para analisar, diagnosticar e otimizar pipelines:

```python
import pepperpy as pp

# Analisar um pipeline
analysis = pp.analyze_pipeline(pipeline)
print(analysis.summary())

# Perfilar a execução
profiler = pp.profile_execution(pipeline, {"text": "Exemplo de texto"})
print(profiler.summary())

# Visualizar o pipeline
svg = pp.visualize_pipeline(pipeline)
with open("pipeline.svg", "w") as f:
    f.write(svg)

# Sugerir otimizações
suggestions = pp.suggest_optimizations(pipeline)
for suggestion in suggestions:
    print(f"{suggestion['name']}: {suggestion['description']}")
```

### Integração Multimodal

Processamento unificado de diferentes modalidades (texto, imagem, áudio, vídeo):

```python
import pepperpy as pp

# Criar dados de diferentes modalidades
text_data = pp.ModalityData(modality="text", content="Descrição de uma imagem")
image_data = pp.ModalityData(modality="image", content="caminho/para/imagem.jpg")

# Converter entre modalidades
image_from_text = await pp.convert_between_modalities(
    text_data, 
    target_modality="image"
)

text_from_image = await pp.convert_between_modalities(
    image_data, 
    target_modality="text"
)
```

### Workflows Adaptativos

Workflows que aprendem e se adaptam com base em feedback:

```python
import pepperpy as pp

# Criar um workflow adaptativo
workflow = pp.create_adaptive_workflow("summarization")

# Processar um documento
result = await workflow.process("Este é um texto longo que precisa ser resumido.")

# Fornecer feedback para aprendizado
await workflow.learn_from_feedback(user_rating=4, comments="Bom resumo, mas muito técnico")
```

## Arquitetura

PepperPy is built with a modular architecture that allows for easy extension and customization:

```
pepperpy/
├── types/                # Fundamental types
├── errors/               # Error hierarchy
├── utils/                # General utilities
├── config/               # Framework configuration
├── cli/                  # Command-line interface
├── registry/             # Component registry
├── interfaces/           # Base interfaces
├── memory/               # Memory management
├── cache/                # Caching system
├── storage/              # Persistent storage
├── workflows/            # Workflow system
├── events/               # Event system
├── plugins/              # Plugin system
├── streaming/            # Streaming functionality
├── llm/                  # LLM integration
├── rag/                  # RAG system
├── http/                 # HTTP client/server
├── data/                 # Data handling
└── docs/                 # Documentation
```

### Core Modules

- **Types**: Centralized type definitions for consistent typing across the framework
- **Errors**: Comprehensive error hierarchy with detailed error information
- **Utils**: Common utilities for logging, async operations, and validation
- **Config**: Flexible configuration system with environment variable support

### Framework Base

- **CLI**: Command-line interface for interacting with the framework
- **Registry**: Component registry for discovering and managing components
- **Interfaces**: Base interfaces for framework components

### State Management

- **Memory**: Memory management for storing and retrieving data
- **Cache**: Caching system for improving performance
- **Storage**: Persistent storage for data

### Flow Control

- **Workflows**: Workflow system for defining and executing complex processes
- **Events**: Event system for communication between components
- **Plugins**: Plugin system for extending functionality

### I/O & Communication

- **Streaming**: Streaming functionality for real-time data processing
- **HTTP**: HTTP client and server for web communication

### AI & Machine Learning

- **LLM**: Integration with large language models
- **RAG**: Retrieval-augmented generation system

### Data & Integration

- **Data**: Data handling with schema validation and transformation

## Instalação

```bash
pip install pepperpy
```

## Documentação

Para documentação completa, visite [docs.pepperpy.ai](https://docs.pepperpy.ai).

## Contribuindo

Contribuições são bem-vindas! Por favor, leia nosso [guia de contribuição](CONTRIBUTING.md) para mais informações.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. 