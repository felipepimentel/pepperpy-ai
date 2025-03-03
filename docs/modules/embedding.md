# Módulo Embedding

O módulo `embedding` fornece capacidades para gerar e manipular embeddings de texto e documentos.

## Visão Geral

Embeddings são representações vetoriais de texto que capturam significado semântico, permitindo operações como busca semântica, agrupamento e classificação. O módulo Embedding do PepperPy oferece:

- Geração de embeddings para textos, frases e documentos
- Suporte a múltiplos provedores de embedding
- Cache de embeddings para melhorar o desempenho
- Utilitários para manipulação de embeddings

## Principais Componentes

### Embedders

O PepperPy fornece diferentes tipos de embedders:

```python
from pepperpy.embedding import (
    Embedder,
    TextEmbedder,
    DocumentEmbedder,
    SentenceEmbedder
)

# Embedder genérico
embedder = Embedder(provider="openai", model="text-embedding-ada-002")
embedding = embedder.embed("Este é um texto de exemplo.")

# Embedder específico para textos
text_embedder = TextEmbedder(provider="openai", model="text-embedding-ada-002")
text_embedding = text_embedder.embed("Este é um texto de exemplo.")

# Embedder para documentos
document_embedder = DocumentEmbedder(provider="openai", model="text-embedding-ada-002")
document_embedding = document_embedder.embed_document({
    "title": "Exemplo de Documento",
    "content": "Este é o conteúdo do documento de exemplo.",
    "metadata": {"author": "PepperPy", "date": "2023-01-01"}
})

# Embedder para sentenças
sentence_embedder = SentenceEmbedder(provider="sentence-transformers", model="all-MiniLM-L6-v2")
sentences = ["Esta é a primeira frase.", "Esta é a segunda frase."]
sentence_embeddings = sentence_embedder.embed_batch(sentences)
```

### Provedores de Embedding

O PepperPy suporta vários provedores de embedding:

```python
from pepperpy.embedding import EmbeddingProvider
from pepperpy.embedding.providers import (
    OpenAIEmbeddingProvider,
    HuggingFaceEmbeddingProvider,
    SentenceTransformersProvider,
    AzureOpenAIEmbeddingProvider
)

# Provedor OpenAI
openai_provider = OpenAIEmbeddingProvider(
    api_key="your-openai-api-key",
    model="text-embedding-ada-002"
)

# Provedor HuggingFace
huggingface_provider = HuggingFaceEmbeddingProvider(
    model="sentence-transformers/all-MiniLM-L6-v2",
    api_key="your-huggingface-api-key"  # Opcional para modelos públicos
)

# Provedor SentenceTransformers (local)
sentence_provider = SentenceTransformersProvider(
    model="all-MiniLM-L6-v2"
)

# Provedor Azure OpenAI
azure_provider = AzureOpenAIEmbeddingProvider(
    api_key="your-azure-api-key",
    api_base="https://your-resource.openai.azure.com",
    deployment_name="your-embedding-deployment",
    api_version="2023-05-15"
)

# Usar um provedor
embedding = openai_provider.embed("Este é um texto de exemplo.")
```

### Cache de Embeddings

O cache de embeddings melhora o desempenho evitando recalcular embeddings:

```python
from pepperpy.embedding import CachedEmbedder
from pepperpy.caching.providers import InMemoryCacheProvider

# Criar um provedor de cache
cache_provider = InMemoryCacheProvider()

# Criar um embedder com cache
cached_embedder = CachedEmbedder(
    embedder=TextEmbedder(provider="openai", model="text-embedding-ada-002"),
    cache_provider=cache_provider,
    ttl=3600  # Tempo de vida do cache em segundos
)

# Usar o embedder com cache
# A primeira chamada gera o embedding
embedding1 = cached_embedder.embed("Este é um texto de exemplo.")

# A segunda chamada retorna do cache
embedding2 = cached_embedder.embed("Este é um texto de exemplo.")
```

### Fábrica de Embeddings

A fábrica de embeddings simplifica a criação de embedders:

```python
from pepperpy.embedding import create_embedding

# Criar um embedder usando a fábrica
embedder = create_embedding(
    provider="openai",
    model="text-embedding-ada-002",
    api_key="your-openai-api-key",
    dimensions=1536,
    use_cache=True
)

# Usar o embedder
embedding = embedder.embed("Este é um texto de exemplo.")
```

### Tipos de Embedding

O módulo define tipos de embedding:

```python
from pepperpy.embedding.types import EmbeddingType

# Tipos disponíveis
# EmbeddingType.TEXT - Embedding de texto
# EmbeddingType.DOCUMENT - Embedding de documento
# EmbeddingType.SENTENCE - Embedding de sentença
# EmbeddingType.IMAGE - Embedding de imagem
# EmbeddingType.AUDIO - Embedding de áudio
```

## Exemplo Completo

```python
from pepperpy.embedding import (
    TextEmbedder,
    CachedEmbedder,
    create_embedding
)
from pepperpy.embedding.providers import OpenAIEmbeddingProvider
from pepperpy.caching.providers import InMemoryCacheProvider
import numpy as np

# Configurar o provedor
provider = OpenAIEmbeddingProvider(
    api_key="your-openai-api-key",
    model="text-embedding-ada-002"
)

# Criar um embedder básico
embedder = TextEmbedder(provider=provider)

# Adicionar cache
cache_provider = InMemoryCacheProvider()
cached_embedder = CachedEmbedder(
    embedder=embedder,
    cache_provider=cache_provider,
    ttl=3600
)

# Gerar embeddings para alguns textos
texts = [
    "O PepperPy é um framework para construir aplicações de IA.",
    "Embeddings são representações vetoriais de texto.",
    "A busca semântica permite encontrar textos similares."
]

embeddings = []
for text in texts:
    embedding = cached_embedder.embed(text)
    embeddings.append(embedding)

# Calcular similaridade entre embeddings
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Comparar o primeiro texto com os outros
for i, embedding in enumerate(embeddings[1:], 1):
    similarity = cosine_similarity(embeddings[0], embedding)
    print(f"Similaridade entre texto 1 e texto {i+1}: {similarity:.4f}")

# Buscar o texto mais similar a uma consulta
query = "Como o PepperPy ajuda no desenvolvimento de IA?"
query_embedding = cached_embedder.embed(query)

similarities = []
for i, embedding in enumerate(embeddings):
    similarity = cosine_similarity(query_embedding, embedding)
    similarities.append((i, similarity))

# Ordenar por similaridade
similarities.sort(key=lambda x: x[1], reverse=True)

print("\nResultados da busca para:", query)
for i, similarity in similarities:
    print(f"Texto {i+1}: {texts[i]} (Similaridade: {similarity:.4f})")
```

## Configuração Avançada

```python
from pepperpy.embedding import TextEmbedder
from pepperpy.embedding.providers import OpenAIEmbeddingProvider

# Configuração avançada do provedor
provider = OpenAIEmbeddingProvider(
    api_key="your-openai-api-key",
    model="text-embedding-ada-002",
    dimensions=1536,
    normalize=True,
    batch_size=32,
    request_timeout=30.0,
    max_retries=3,
    retry_delay=1.0
)

# Configuração avançada do embedder
embedder = TextEmbedder(
    provider=provider,
    preprocessing_pipeline=[
        "remove_html_tags",
        "normalize_whitespace",
        "lowercase"
    ],
    max_input_length=8192
)

# Usar o embedder configurado
embedding = embedder.embed("Este é um texto de exemplo.")
```

## Melhores Práticas

1. **Use Cache**: Implemente cache de embeddings para textos frequentemente usados para melhorar o desempenho.

2. **Escolha o Modelo Adequado**: Modelos maiores geralmente fornecem embeddings de melhor qualidade, mas são mais caros e lentos.

3. **Normalize Embeddings**: Normalize embeddings para facilitar comparações de similaridade.

4. **Processe em Lote**: Use `embed_batch` para processar múltiplos textos de uma vez, melhorando a eficiência.

5. **Pré-processe Textos**: Aplique pré-processamento consistente aos textos antes de gerar embeddings. 