# Base de Conhecimento - PepperPy Framework

## Arquitetura Principal

O PepperPy é um framework Python para desenvolvimento de aplicações baseadas em IA com uma arquitetura modular e extensível. O framework implementa:

- **Design Assíncrono**: Baseado em `asyncio` para operações não-bloqueantes
- **Interfaces Fluentes**: Padrão de method chaining para uma API intuitiva
- **Plugins**: Sistema extensível para adicionar novas funcionalidades
- **Memória Hierárquica**: Sistema sofisticado para gerenciamento de conhecimento

## Estrutura do Projeto

O projeto PepperPy segue uma arquitetura modular com clara separação de responsabilidades:

### Diretórios Principais

- **`pepperpy/`**: Código principal do framework
  - **`core/`**: Componentes fundamentais do framework
  - **`agents/`**: Agentes inteligentes e orquestradores
  - **`rag/`**: Implementações de Retrieval Augmented Generation
  - **`plugins/`**: Sistema de plugins interno
  - **`content/`**: Processamento e geração de conteúdo
  - **`workflow/`**: Orquestração de fluxos de trabalho
  - **`cache/`**: Sistemas de cache para otimização
  - **`tts/`**: Text-to-Speech e processamento de áudio
  - **`tools/`**: Ferramentas utilitárias

- **`plugins/`**: Plugins de extensão (externa à pasta principal)
  - **`llm/`**: Integrações com LLMs (OpenAI, Anthropic, etc.)
  - **`rag/`**: Implementações de RAG (Pinecone, Chroma, etc.)
  - **`embeddings/`**: Geradores de embeddings
  - **`storage/`**: Sistemas de armazenamento
  - **`content/`**: Processadores de conteúdo
  - **`tts/`**: Integrações para text-to-speech

- **`examples/`**: Exemplos de uso para diferentes funcionalidades
- **`docs/`**: Documentação

### Arquivos Principais

- **`pepperpy.py`**: Implementação principal com as classes centrais
- **`llm.py`**: Abstrações para modelos de linguagem
- **`embeddings.py`**: Gerenciamento de embeddings de texto
- **`storage.py`**: Sistemas de armazenamento e persistência

## Módulos Core

O diretório `core/` contém componentes fundamentais para o funcionamento do framework:

- **`base.py`**: Classes base e abstrações
- **`config.py`**: Gerenciamento de configurações
- **`di.py`**: Sistema de injeção de dependências
- **`errors.py`**: Gestão de erros e exceções
- **`events.py`**: Sistema de eventos e mensagens
- **`logging.py`**: Configuração de logging
- **`memory.py`**: Gerenciamento básico de memória
- **`metrics.py`**: Coleta e análise de métricas
- **`validation.py`**: Validação de dados e esquemas

## Sistema de Memória

O coração do PepperPy é seu sistema de memória hierárquica que categoriza o conhecimento em três tipos principais:

### 1. Memória Semântica (Knowledge)
Armazena fatos, informações e conhecimento declarativo:
```python
await repo.store_knowledge(
    "Python é uma linguagem interpretada de alto nível",
    category="programming",
    tags=["python", "language"]
)
```

### 2. Memória Procedural (Procedures)
Armazena conhecimento sobre como realizar tarefas:
```python
await repo.store_procedure(
    "Função para formatação de código removendo espaços em branco",
    language="python",
    type="formatter"
)
```

### 3. Memória Episódica (Experiences)
Armazena experiências e interações passadas:
```python
await repo.store_experience(
    '"U'suário perguntou sobre dicionários Python",
    topic="python",
    subtopic="dictionaries"
)
```

## Sistema de Agentes

O módulo `agents/` fornece implementações para criar e gerenciar agentes inteligentes:

- **`base.py`**: Interfaces base para todos os agentes
- **`hierarchical_memory.py`**: Agentes com memória hierárquica avançada
- **`intent.py`**: Detecção e processamento de intenções
- **`memory.py`**: Agentes especializados em gerenciamento de memória
- **`orchestrator.py`**: Coordenação entre múltiplos agentes

### Exemplo de Uso de Agente
```python
# Criar um agente com memória hierárquica
agent = HierarchicalMemoryAgent()
await agent.initialize()

# Configurar memória e conhecimento
await agent.learn("Python usa indentação para delimitar blocos")

# Processar uma consulta
result = await agent.process("Como funcionam blocos em Python?")
```

## Sistema RAG (Retrieval Augmented Generation)

O módulo `rag/` implementa um sistema completo de RAG:

- **`base.py`**: Interfaces base para componentes RAG
- **`chunking/`**: Estratégias para divisão de documentos
- **`pipeline/`**: Pipeline de processamento RAG
- **`memory_optimization.py`**: Otimização de consultas e contexto

### Exemplo de RAG
```python
# Criar o sistema RAG
rag_system = RagSystem()
await rag_system.initialize()

# Adicionar documentos
await rag_system.add_document("documento.pdf")

# Consultar
results = await rag_system.query("Qual a principal ideia do documento?")
```

## Componentes Principais

### PepperPy
Classe principal que serve como ponto de entrada para o framework:
```python
pepper = PepperPy()
await pepper.initialize()

# Configuração de provedores
pepper.with_llm(llm_provider)
pepper.with_rag(rag_provider)
pepper.with_embeddings(embeddings_provider)

# Criação de repositório de memória
repo = pepper.create_memory_repository()
```

### MemoryRepository
Gerencia o armazenamento e recuperação de conhecimento:
```python
# Busca em todos os tipos de memória
results = await repo.search("Python")

# Recuperação por tipo de memória
knowledge = await repo.get_knowledge()
procedures = await repo.get_procedures()
experiences = await repo.get_experiences()

# Exportação de memória
memory_file = await repo.export_memory("memory_data.json")

# Limpeza de memória
repo.clear()
```

### ChatInterface
Interface para interações baseadas em chat com suporte a memória:
```python
# Configuração do chat
pepper.chat.with_message(
    MessageRole.SYSTEM,
    "Você é um assistente útil."
)

# Geração de resposta com contexto de memória
response = (
    await pepper.chat.with_message(
        MessageRole.USER, 
        "Fale sobre dicionários Python"
    )
    .with_memory(repo)
    .generate()
)
```

## Sistema de Plugins

O PepperPy implementa um sistema robusto de plugins que permite estender suas funcionalidades:

### Tipos de Plugins
- **LLM Providers**: Integrações com diferentes modelos de linguagem
- **RAG Providers**: Sistemas de recuperação e geração aumentada
- **Embedding Providers**: Geradores de embeddings para textos
- **Storage Providers**: Soluções de armazenamento e persistência
- **Content Processors**: Processadores de conteúdo especializado
- **TTS Providers**: Serviços de síntese de voz

### Exemplo de Criação de Plugin
```python
from pepperpy.plugin.plugin import ProviderPlugin
from pepperpy.llm import LLMProvider

class CustomLLMProvider(LLMProvider, ProviderPlugin):
    """Provider personalizado para LLM."""
    
    async def initialize(self) -> None:
        """Inicializar o provider."""
        self.client = CustomClient(api_key=self.api_key)
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Gerar uma resposta para o prompt."""
        response = await self.client.generate(prompt)
        return response.text
```

### Registro de Plugins
```python
# Registrar o plugin no sistema
pepper.plugins.register("llm", "custom", CustomLLMProvider)

# Usar o plugin
pepper.with_llm(pepper.plugins.create("llm", "custom", api_key="key"))
```

## Workflows

O módulo `workflow/` implementa um sistema para criar fluxos de trabalho complexos:

### Componentes de Workflow
- **Nodes**: Unidades de processamento individual
- **Pipelines**: Sequências de nodes conectados
- **Processors**: Executores de pipelines
- **Triggers**: Gatilhos para iniciar workflows

### Exemplo de Workflow
```python
# Criar nós de processamento
extract = TextExtractorNode()
analyze = SentimentAnalysisNode()
summarize = TextSummarizerNode()

# Construir pipeline
pipeline = (
    Pipeline()
    .add_node(extract)
    .add_node(analyze)
    .add_node(summarize)
    .connect(extract, analyze)
    .connect(analyze, summarize)
)

# Executar workflow
processor = WorkflowProcessor(pipeline)
result = await processor.process({"document": "documento.pdf"})
```

## Padrões de Design

### Method Chaining
O framework usa extensivamente encadeamento de métodos para uma API fluente:
```python
repo = (
    pepper.create_memory_repository()
    .clear()
)

response = (
    await pepper.chat
    .with_message(MessageRole.USER, "Pergunta")
    .with_memory(repo)
    .generate()
)
```

### Gerenciamento de Recursos
Implementa protocolos de contexto assíncrono para gerenciamento de recursos:
```python
async with PepperPy() as pepper:
    # Recursos são inicializados automaticamente
    repo = pepper.create_memory_repository()
    # Recursos são liberados ao sair do contexto
```

### Configuração Fluente
Estilo fluente de configuração que melhora a legibilidade:
```python
pepper = (
    PepperPy()
    .with_llm(openai_provider)
    .with_rag(pinecone_provider)
    .with_embeddings(sentence_transformer_provider)
)
```

## Casos de Uso Avançados

A pasta `examples/` contém implementações de referência para diversos casos de uso:

### 1. Análise de Repositórios de Código
O exemplo `repo_analysis_assistant_example.py` demonstra como analisar repositórios:
```python
repo = await GitRepository.from_url("https://github.com/exemplo/repo")
analysis = await repo.analyze()
report = await analysis.generate_report()
```

### 2. Processamento de Documentos
O exemplo `document_processing_example.py` mostra como processar documentos:
```python
processor = DocumentProcessor()
result = await processor.process("documento.pdf")
summary = await result.generate_summary()
```

### 3. Workflows de Processamento de Texto
O exemplo `text_processing_workflow_example.py` implementa um fluxo de processamento:
```python
workflow = TextProcessingWorkflow()
result = await workflow.process("texto_para_processar.txt")
```

### 4. Assistentes de BI
O exemplo `bi_assistant_example.py` demonstra como criar assistentes para análise de dados:
```python
assistant = BIAssistant()
insight = await assistant.analyze_data("dados.csv", "Qual a tendência de vendas?")
```

### 5. Geração de Podcasts
O exemplo `podcast_generator_example.py` mostra como gerar podcasts automaticamente:
```python
generator = PodcastGenerator()
podcast = await generator.create("Tema do podcast", duration_minutes=10)
```

### 6. Assistentes de Aprendizado
O exemplo `ai_learning_assistant_example.py` implementa um assistente de aprendizado:
```python
assistant = LearningAssistant()
lesson = await assistant.create_lesson("Python para iniciantes")
```

## Implementação da Memória

A implementação da memória usa uma estrutura de dicionário com arrays para cada tipo:
```python
self._memories = {
    "knowledge": [],  # Memória semântica (fatos)
    "procedures": [], # Memória procedural (how-to)
    "experiences": [], # Memória episódica (eventos)
}
```

Cada item armazenado inclui:
- **Texto**: O conteúdo principal
- **Metadados**: Informações adicionais como categorias e tags
- **Timestamp**: Data e hora de criação

## Fluxo de Execução Típico

1. **Inicialização**:
   ```python
   pepper = PepperPy()
   await pepper.initialize()
   ```

2. **Criação de Repositório**:
   ```python
   repo = pepper.create_memory_repository()
   ```

3. **Armazenamento de Conhecimento**:
   ```python
   await repo.store_knowledge("Informação importante", category="categoria")
   ```

4. **Recuperação e Busca**:
   ```python
   results = await repo.search("termo de busca")
   ```

5. **Integração com LLM**:
   ```python
   response = await pepper.execute("Query", context={"memory": await repo.get_context()})
   ```

6. **Limpeza de Recursos**:
   ```python
   await pepper.cleanup()
   ```

## Contexto de Memória

O método `get_context()` formata a memória para uso em prompts de LLM:
```python
context = await repo.get_context()
# Resulta em:
# {
#    "knowledge": "- Fato 1\n- Fato 2\n...",
#    "procedures": "- Procedimento 1\n- Procedimento 2\n...",
#    "experiences": "- Experiência 1\n- Experiência 2\n..."
# }
```

## Persistência

O repositório salva a memória automaticamente em arquivos JSON:
```python
# Salvar memória
await repo.save()  # Salva em memory_data/{nome}_memory.json

# Exportar memória para arquivo específico
path = await repo.export_memory("arquivo.json")
```

## Configuração e Ambiente

O PepperPy suporta configuração por diferentes métodos:

### Arquivo .env
```
PEPPERPY_LLM_PROVIDER=openai
PEPPERPY_LLM_MODEL=gpt-4-turbo
PEPPERPY_API_KEY=sk-********
```

### Arquivo config.yaml
```yaml
pepperpy:
  llm:
    provider: openai
    model: gpt-4-turbo
    temperature: 0.7
  rag:
    provider: chroma
    chunk_size: 1000
  plugins:
    enabled:
      - llm.openai
      - rag.chroma
```

### Configuração Programática
```python
pepper = PepperPy(
    llm={
        "provider": "openai",
        "model": "gpt-4-turbo",
        "temperature": 0.7
    },
    rag={
        "provider": "chroma",
        "chunk_size": 1000
    }
)
```

## Métodos de Integração

### Integração com Chat
```python
# Integração simples
response = (
    await pepper.chat.with_message(MessageRole.USER, "Query")
    .with_memory(repo)
    .generate()
)

# Armazenamento automático da conversa
# A resposta é automaticamente armazenada como experiência
```

### Execução de Consultas
```python
# Execução direta com contexto de memória
result = await pepper.execute(
    query="Gerar resposta",
    context={"memory": await repo.get_context()}
)
```

## Boas Práticas

1. **Categorização Eficiente**:
   - Use categorias e tags consistentes para cada tipo de memória
   - Crie uma taxonomia bem definida para facilitar a recuperação

2. **Gerenciamento de Memória**:
   - Limpe a memória (`repo.clear()`) quando iniciar novos contextos
   - Exporte memórias importantes para persistência de longo prazo

3. **Integração com LLMs**:
   - Forneça contexto específico para a consulta
   - Use o contexto hierárquico para diferentes tipos de conhecimento

4. **Organização do Código**:
   - Separe a lógica de armazenamento da lógica de processamento
   - Use async/await consistentemente
   - Documente todos os métodos com docstrings completas

5. **Error Handling**:
   - Capture exceções específicas com try/except
   - Propague erros como exceções do domínio
   - Use logging para diagnóstico
   
6. **Gerenciamento de Recursos**:
   - Sempre utilize o método `cleanup()` para liberar recursos
   - Prefira o uso de contextos async (`async with`)
   - Verifique vazamentos de recursos

7. **Extensibilidade**:
   - Crie plugins em vez de modificar código existente
   - Siga interfaces e protocolos ao integrar novos sistemas
   - Mantenha retrocompatibilidade

## Usos Práticos

1. **Assistentes com Memória**:
   ```python
   # Assistente que lembra interações anteriores
   await repo.store_knowledge("Preferência do usuário: Python")
   response = await chat.with_memory(repo).generate()
   ```

2. **Sistemas RAG Avançados**:
   ```python
   # Recuperação com contexto de documento
   result = await pepper.execute(
       query="Explique este código",
       context={"memory": await repo.get_context(), "code": code_snippet}
   )
   ```

3. **Análise Técnica com Conhecimento Persistente**:
   ```python
   # Armazenar análises prévias
   await repo.store_knowledge(
       "Sistema usa arquitetura MVVM",
       category="architecture",
       tags=["pattern", "MVVM"]
   )
   ```
