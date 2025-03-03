# Módulo RAG (Retrieval Augmented Generation)

O módulo `rag` fornece um framework modular para construir aplicações de Retrieval Augmented Generation (RAG) com clara separação entre componentes de indexação, recuperação e geração.

## Visão Geral

O RAG (Retrieval Augmented Generation) é uma técnica que melhora a geração de texto por modelos de linguagem, fornecendo contexto relevante recuperado de uma base de conhecimento. O módulo RAG do PepperPy oferece:

- Pipeline completo de RAG com componentes modulares
- Indexação de documentos com suporte a diferentes estratégias de chunking
- Geração de embeddings para busca semântica
- Recuperação de informações relevantes
- Geração de respostas baseadas no contexto recuperado

## Principais Componentes

### Pipeline RAG

O pipeline RAG é o componente central que orquestra o fluxo de trabalho:

```python
from pepperpy.rag import RAGPipeline, RAGConfig, RAGFactory

# Configuração do pipeline RAG
config = RAGConfig(
    embedding_model="text-embedding-ada-002",
    llm_model="gpt-4",
    chunk_size=1000,
    chunk_overlap=200,
    similarity_top_k=3
)

# Criação do pipeline
pipeline = RAGFactory.create_pipeline(config)

# Uso do pipeline
response = pipeline.query(
    query="Como funciona o RAG no PepperPy?",
    documents=["doc1.pdf", "doc2.txt"]
)
print(response.answer)
```

### Documentos e Chunks

O módulo RAG trabalha com documentos e chunks:

```python
from pepperpy.rag import Document

# Criando documentos
documents = [
    Document(
        id="doc1",
        content="Este é o conteúdo do primeiro documento...",
        metadata={"source": "manual.pdf", "page": 1}
    ),
    Document(
        id="doc2",
        content="Este é o conteúdo do segundo documento...",
        metadata={"source": "faq.txt", "category": "introdução"}
    )
]

# Processando documentos no pipeline
pipeline.index_documents(documents)
```

### Indexação

O processo de indexação divide documentos em chunks e gera embeddings:

```python
from pepperpy.rag.indexing import Chunker, Embedder, IndexingManager
from pepperpy.rag.config import ChunkingConfig, EmbeddingConfig

# Configuração de chunking
chunking_config = ChunkingConfig(
    chunk_size=1000,
    chunk_overlap=200,
    chunking_strategy="sentence"
)

# Configuração de embedding
embedding_config = EmbeddingConfig(
    model="text-embedding-ada-002",
    dimensions=1536,
    normalize=True
)

# Criando componentes de indexação
chunker = Chunker(config=chunking_config)
embedder = Embedder(config=embedding_config)

# Indexando documentos
chunks = chunker.chunk_documents(documents)
indexed_chunks = embedder.embed_chunks(chunks)

# Ou usando o gerenciador de indexação
indexing_manager = IndexingManager(
    chunking_config=chunking_config,
    embedding_config=embedding_config
)
indexed_documents = indexing_manager.process_documents(documents)
```

### Recuperação

A recuperação busca chunks relevantes para uma consulta:

```python
from pepperpy.rag.retrieval import SimilarityRetriever, RetrievalManager
from pepperpy.rag.config import RetrievalConfig
from pepperpy.rag import SearchQuery

# Configuração de recuperação
retrieval_config = RetrievalConfig(
    similarity_top_k=3,
    similarity_threshold=0.7,
    reranking_enabled=True
)

# Criando um recuperador
retriever = SimilarityRetriever(config=retrieval_config)

# Criando uma consulta
query = SearchQuery(
    text="Como funciona o RAG no PepperPy?",
    filters={"category": "introdução"}
)

# Recuperando chunks relevantes
results = retriever.retrieve(query, indexed_chunks)

# Ou usando o gerenciador de recuperação
retrieval_manager = RetrievalManager(config=retrieval_config)
results = retrieval_manager.retrieve(query, indexed_documents)
```

### Geração

A geração produz respostas baseadas no contexto recuperado:

```python
from pepperpy.rag.generation import ContextAwareGenerator, GenerationManager
from pepperpy.rag.config import GenerationConfig

# Configuração de geração
generation_config = GenerationConfig(
    model="gpt-4",
    temperature=0.7,
    max_tokens=500,
    prompt_template="Responda à pergunta com base no contexto fornecido.\n\nContexto: {context}\n\nPergunta: {query}\n\nResposta:"
)

# Criando um gerador
generator = ContextAwareGenerator(config=generation_config)

# Gerando resposta
response = generator.generate(query, results)

# Ou usando o gerenciador de geração
generation_manager = GenerationManager(config=generation_config)
response = generation_manager.generate(query, results)
```

## Exemplo Completo

```python
from pepperpy.rag import (
    RAGPipeline, 
    RAGConfig, 
    Document, 
    SearchQuery
)

# Configuração do pipeline
config = RAGConfig(
    embedding_model="text-embedding-ada-002",
    llm_model="gpt-4",
    chunk_size=1000,
    chunk_overlap=200,
    similarity_top_k=3,
    prompt_template="Responda à pergunta com base no contexto fornecido.\n\nContexto: {context}\n\nPergunta: {query}\n\nResposta:"
)

# Criação do pipeline
pipeline = RAGPipeline.from_config(config)

# Documentos de exemplo
documents = [
    Document(
        id="doc1",
        content="O PepperPy é um framework Python para construir aplicações de IA. "
                "Ele fornece módulos para trabalhar com LLMs, RAG, agentes e muito mais.",
        metadata={"source": "docs", "category": "overview"}
    ),
    Document(
        id="doc2",
        content="O módulo RAG do PepperPy permite criar pipelines de Retrieval Augmented Generation. "
                "Ele suporta indexação de documentos, recuperação semântica e geração contextual.",
        metadata={"source": "docs", "category": "rag"}
    )
]

# Indexar documentos
pipeline.index_documents(documents)

# Consultar o pipeline
query = SearchQuery(
    text="Como o PepperPy implementa RAG?",
    filters={"category": "rag"}
)

# Obter resposta
response = pipeline.query(query)

print("Pergunta:", query.text)
print("Resposta:", response.answer)
print("Fontes:", [source.metadata for source in response.sources])
```

## Configuração Avançada

O módulo RAG permite configuração avançada para cada componente:

```python
from pepperpy.rag.config import (
    RagConfig,
    ChunkingConfig,
    EmbeddingConfig,
    IndexConfig,
    RetrievalConfig,
    GenerationConfig
)

# Configuração detalhada
config = RagConfig(
    chunking=ChunkingConfig(
        chunk_size=1000,
        chunk_overlap=200,
        chunking_strategy="sentence",
        split_by_heading=True
    ),
    embedding=EmbeddingConfig(
        model="text-embedding-ada-002",
        dimensions=1536,
        normalize=True,
        batch_size=32
    ),
    index=IndexConfig(
        index_type="faiss",
        metric="cosine",
        index_path="./rag_index"
    ),
    retrieval=RetrievalConfig(
        similarity_top_k=5,
        similarity_threshold=0.7,
        reranking_enabled=True,
        reranking_model="cross-encoder/ms-marco-MiniLM-L-6-v2"
    ),
    generation=GenerationConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=500,
        prompt_template="Responda à pergunta com base no contexto fornecido.\n\nContexto: {context}\n\nPergunta: {query}\n\nResposta:",
        include_sources=True
    )
)

# Criação do pipeline com configuração avançada
pipeline = RAGPipeline.from_config(config)
```

## Melhores Práticas

1. **Ajuste o Tamanho dos Chunks**: Experimente diferentes tamanhos de chunk para encontrar o equilíbrio entre contexto e precisão.

2. **Escolha o Modelo de Embedding Adequado**: Modelos de embedding mais avançados geralmente fornecem melhores resultados de recuperação.

3. **Personalize os Prompts**: Adapte os templates de prompt para sua aplicação específica.

4. **Filtre Resultados**: Use filtros de metadados para limitar a recuperação a documentos relevantes.

5. **Avalie o Desempenho**: Monitore e avalie regularmente o desempenho do seu pipeline RAG para identificar áreas de melhoria. 