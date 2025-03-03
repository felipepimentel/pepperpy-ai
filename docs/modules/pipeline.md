# Módulo Pipeline

O módulo `pipeline` fornece ferramentas para criar, configurar e executar pipelines de processamento de dados e tarefas de IA no framework PepperPy.

## Visão Geral

O módulo Pipeline permite:
- Criar fluxos de processamento compostos por múltiplos componentes
- Conectar diferentes módulos do PepperPy em sequências lógicas
- Definir pipelines declarativamente ou programaticamente
- Monitorar e depurar a execução de pipelines
- Reutilizar e compartilhar pipelines pré-configurados
- Otimizar o desempenho de fluxos de trabalho complexos

## Principais Componentes

### Criação de Pipelines

```python
from pepperpy.pipeline import (
    Pipeline,
    PipelineBuilder,
    PipelineStep,
    PipelineConfig
)

# Criar um pipeline usando o builder
builder = PipelineBuilder()
pipeline = (
    builder
    .add_step("load_data", "DataLoader", {"source": "csv", "path": "data.csv"})
    .add_step("preprocess", "TextPreprocessor", {"clean": True, "lowercase": True})
    .add_step("embed", "TextEmbedder", {"model": "text-embedding-3-large"})
    .add_step("store", "VectorStore", {"db_type": "chroma", "collection": "documents"})
    .build()
)

# Executar o pipeline
results = pipeline.run(
    input_data={"file_path": "data.csv"},
    options={"verbose": True}
)

print(f"Pipeline executado com sucesso. Armazenados {len(results['stored_vectors'])} vetores.")

# Criar um pipeline a partir de uma configuração
config = PipelineConfig(
    name="rag_pipeline",
    description="Pipeline para Retrieval Augmented Generation",
    steps=[
        PipelineStep(
            id="retrieve",
            component="VectorRetriever",
            config={"db_type": "chroma", "collection": "documents", "top_k": 5}
        ),
        PipelineStep(
            id="generate",
            component="LLMGenerator",
            config={"model": "gpt-4o", "temperature": 0.7}
        )
    ]
)

rag_pipeline = Pipeline.from_config(config)

# Executar o pipeline RAG
response = rag_pipeline.run(
    input_data={"query": "Como funciona o RAG?"}
)

print(f"Resposta: {response['generated_text']}")
```

### Pipelines Declarativos

```python
from pepperpy.pipeline import load_pipeline
import yaml

# Definir um pipeline em YAML
pipeline_yaml = """
name: text_classification_pipeline
description: Pipeline para classificação de texto
steps:
  - id: load
    component: TextLoader
    config:
      source: file
      path: texts.txt
  
  - id: preprocess
    component: TextPreprocessor
    config:
      clean: true
      lowercase: true
      remove_stopwords: true
      language: pt
    input: load.output
  
  - id: embed
    component: TextEmbedder
    config:
      model: text-embedding-3-large
    input: preprocess.output
  
  - id: classify
    component: TextClassifier
    config:
      model: distilbert-base-uncased-finetuned-sst-2-english
      labels: [positivo, negativo, neutro]
    input: embed.output
"""

# Salvar a definição do pipeline
with open("text_classification_pipeline.yaml", "w") as f:
    f.write(pipeline_yaml)

# Carregar o pipeline a partir do arquivo YAML
pipeline = load_pipeline("text_classification_pipeline.yaml")

# Executar o pipeline
results = pipeline.run(
    input_data={"text": "Este produto é excelente, estou muito satisfeito!"}
)

print(f"Classificação: {results['classification']}")
print(f"Confiança: {results['confidence']}")
```

### Pipelines Compostos

```python
from pepperpy.pipeline import (
    Pipeline,
    CompositePipeline,
    ConditionalPipeline,
    ParallelPipeline
)

# Criar pipelines individuais
preprocessing_pipeline = Pipeline.from_config({
    "name": "preprocessing",
    "steps": [
        {"id": "clean", "component": "TextCleaner", "config": {"remove_html": True}},
        {"id": "normalize", "component": "TextNormalizer", "config": {"lowercase": True}}
    ]
})

embedding_pipeline = Pipeline.from_config({
    "name": "embedding",
    "steps": [
        {"id": "tokenize", "component": "Tokenizer", "config": {"model": "cl100k_base"}},
        {"id": "embed", "component": "Embedder", "config": {"model": "text-embedding-3-large"}}
    ]
})

generation_pipeline = Pipeline.from_config({
    "name": "generation",
    "steps": [
        {"id": "prompt", "component": "PromptFormatter", "config": {"template": "system_template"}},
        {"id": "generate", "component": "LLMGenerator", "config": {"model": "gpt-4o"}}
    ]
})

# Criar um pipeline composto sequencial
sequential_pipeline = CompositePipeline(
    name="sequential_rag",
    pipelines=[preprocessing_pipeline, embedding_pipeline, generation_pipeline],
    mode="sequential"
)

# Criar um pipeline condicional
def language_detector(input_data):
    # Lógica para detectar o idioma
    text = input_data.get("text", "")
    if "hello" in text.lower() or "hi" in text.lower():
        return "english"
    elif "olá" in text.lower() or "oi" in text.lower():
        return "portuguese"
    else:
        return "unknown"

conditional_pipeline = ConditionalPipeline(
    name="multilingual_pipeline",
    condition_fn=language_detector,
    pipeline_map={
        "english": Pipeline.from_config({"name": "english_pipeline", "steps": [
            {"id": "process_en", "component": "EnglishProcessor", "config": {}}
        ]}),
        "portuguese": Pipeline.from_config({"name": "portuguese_pipeline", "steps": [
            {"id": "process_pt", "component": "PortugueseProcessor", "config": {}}
        ]}),
        "unknown": Pipeline.from_config({"name": "default_pipeline", "steps": [
            {"id": "detect_lang", "component": "LanguageDetector", "config": {}}
        ]})
    }
)

# Criar um pipeline paralelo
parallel_pipeline = ParallelPipeline(
    name="parallel_analysis",
    pipelines=[
        Pipeline.from_config({"name": "sentiment_analysis", "steps": [
            {"id": "sentiment", "component": "SentimentAnalyzer", "config": {}}
        ]}),
        Pipeline.from_config({"name": "entity_extraction", "steps": [
            {"id": "entities", "component": "EntityExtractor", "config": {}}
        ]}),
        Pipeline.from_config({"name": "topic_modeling", "steps": [
            {"id": "topics", "component": "TopicModeler", "config": {}}
        ]})
    ],
    aggregator_fn=lambda results: {
        "sentiment": results[0]["sentiment"],
        "entities": results[1]["entities"],
        "topics": results[2]["topics"]
    }
)

# Executar os pipelines compostos
sequential_result = sequential_pipeline.run(
    input_data={"text": "Como implementar RAG em aplicações?"}
)

conditional_result = conditional_pipeline.run(
    input_data={"text": "Olá, como posso implementar RAG?"}
)

parallel_result = parallel_pipeline.run(
    input_data={"text": "A Amazon anunciou novos produtos de IA que parecem promissores."}
)

print(f"Resultado sequencial: {sequential_result['generated_text']}")
print(f"Resultado condicional: {conditional_result['response']}")
print(f"Resultado paralelo - Sentimento: {parallel_result['sentiment']}")
print(f"Resultado paralelo - Entidades: {parallel_result['entities']}")
print(f"Resultado paralelo - Tópicos: {parallel_result['topics']}")
```

### Monitoramento e Observabilidade

```python
from pepperpy.pipeline import (
    Pipeline,
    PipelineMonitor,
    PipelineTracer,
    PipelineMetrics
)

# Criar um monitor para o pipeline
monitor = PipelineMonitor()

# Criar um pipeline com monitoramento
pipeline = Pipeline.from_config({
    "name": "monitored_pipeline",
    "steps": [
        {"id": "retrieve", "component": "VectorRetriever", "config": {"top_k": 5}},
        {"id": "rerank", "component": "Reranker", "config": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2"}},
        {"id": "generate", "component": "LLMGenerator", "config": {"model": "gpt-4o"}}
    ]
})

# Adicionar monitor ao pipeline
pipeline.add_monitor(monitor)

# Executar o pipeline
result = pipeline.run(
    input_data={"query": "Quais são as melhores práticas para RAG?"},
    trace=True  # Habilitar rastreamento detalhado
)

# Obter métricas de execução
metrics = monitor.get_metrics()
print(f"Tempo total de execução: {metrics.total_execution_time} ms")
print(f"Uso de memória: {metrics.memory_usage} MB")

# Obter métricas por etapa
for step_id, step_metrics in metrics.step_metrics.items():
    print(f"Etapa: {step_id}")
    print(f"  Tempo de execução: {step_metrics.execution_time} ms")
    print(f"  Uso de memória: {step_metrics.memory_usage} MB")
    print(f"  Status: {step_metrics.status}")

# Obter rastreamento detalhado
trace = monitor.get_trace()
print(f"Rastreamento completo: {len(trace.events)} eventos")
for event in trace.events[:5]:  # Mostrar os primeiros 5 eventos
    print(f"  {event.timestamp} - {event.step_id} - {event.event_type}: {event.message}")

# Visualizar o fluxo do pipeline
monitor.visualize_flow()

# Exportar métricas para dashboard
monitor.export_metrics(format="prometheus")
```

### Gerenciamento de Erros e Recuperação

```python
from pepperpy.pipeline import (
    Pipeline,
    ErrorHandler,
    RetryStrategy,
    FallbackStrategy
)

# Definir estratégia de retry
retry_strategy = RetryStrategy(
    max_retries=3,
    retry_delay=2,
    backoff_factor=2,
    retry_on_exceptions=[TimeoutError, ConnectionError]
)

# Definir estratégia de fallback
fallback_strategy = FallbackStrategy(
    fallback_component="LLMGenerator",
    fallback_config={"model": "gpt-3.5-turbo", "temperature": 0.7}
)

# Definir manipulador de erros personalizado
class CustomErrorHandler(ErrorHandler):
    def handle_error(self, error, step_id, input_data, context):
        print(f"Erro na etapa {step_id}: {str(error)}")
        
        if isinstance(error, TimeoutError):
            # Tentar novamente com timeout maior
            return {"retry": True, "timeout": context.get("timeout", 30) * 2}
        
        elif isinstance(error, ValueError) and "token limit" in str(error).lower():
            # Reduzir entrada e tentar novamente
            return {"retry": True, "truncate_input": True}
        
        else:
            # Usar fallback para outros erros
            return {"use_fallback": True}

# Criar pipeline com tratamento de erros
pipeline = Pipeline.from_config({
    "name": "robust_pipeline",
    "steps": [
        {
            "id": "retrieve",
            "component": "VectorRetriever",
            "config": {"top_k": 5},
            "retry_strategy": retry_strategy
        },
        {
            "id": "generate",
            "component": "LLMGenerator",
            "config": {"model": "gpt-4o"},
            "retry_strategy": retry_strategy,
            "fallback_strategy": fallback_strategy
        }
    ]
})

# Adicionar manipulador de erros personalizado
pipeline.set_error_handler(CustomErrorHandler())

# Executar o pipeline com tratamento de erros
try:
    result = pipeline.run(
        input_data={"query": "Explique o conceito de RAG em detalhes"},
        options={"timeout": 30}
    )
    print(f"Resultado: {result['generated_text'][:100]}...")
except Exception as e:
    print(f"Erro não tratado: {str(e)}")
```

### Otimização de Pipelines

```python
from pepperpy.pipeline import (
    Pipeline,
    PipelineOptimizer,
    CachingStrategy,
    BatchProcessingStrategy
)

# Criar estratégia de cache
cache_strategy = CachingStrategy(
    cache_type="redis",
    ttl=3600,
    namespace="rag_pipeline",
    cache_key_fn=lambda input_data: f"query:{input_data.get('query', '')}"
)

# Criar estratégia de processamento em lote
batch_strategy = BatchProcessingStrategy(
    batch_size=16,
    max_latency_ms=100,
    process_partial_batches=True
)

# Criar pipeline
pipeline = Pipeline.from_config({
    "name": "optimized_pipeline",
    "steps": [
        {"id": "embed", "component": "TextEmbedder", "config": {"model": "text-embedding-3-large"}},
        {"id": "retrieve", "component": "VectorRetriever", "config": {"top_k": 5}},
        {"id": "generate", "component": "LLMGenerator", "config": {"model": "gpt-4o"}}
    ]
})

# Adicionar estratégias de otimização
pipeline.add_caching_strategy(cache_strategy)
pipeline.add_batch_processing_strategy(batch_strategy)

# Otimizar pipeline automaticamente
optimizer = PipelineOptimizer()
optimized_pipeline = optimizer.optimize(
    pipeline=pipeline,
    optimization_target="latency",  # Alternativas: "throughput", "cost", "balanced"
    max_cost_per_query=0.01
)

print(f"Pipeline otimizado: {optimized_pipeline.name}")
print(f"Otimizações aplicadas:")
for optimization in optimized_pipeline.applied_optimizations:
    print(f"  - {optimization}")

# Executar pipeline otimizado
results = optimized_pipeline.run_batch(
    input_data_batch=[
        {"query": "O que é RAG?"},
        {"query": "Como implementar RAG?"},
        {"query": "Quais são as limitações do RAG?"},
        {"query": "Como avaliar um sistema RAG?"}
    ]
)

for i, result in enumerate(results):
    print(f"Resultado {i+1}: {result['generated_text'][:50]}...")
```

## Exemplo Completo

```python
from pepperpy.pipeline import Pipeline, PipelineBuilder, PipelineMonitor
from pepperpy.rag import VectorRetriever, Reranker
from pepperpy.llm import LLMGenerator
from pepperpy.embedding import TextEmbedder
from pepperpy.formats import DocumentProcessor, TextSplitter
import json
import os

def create_advanced_rag_pipeline():
    """Exemplo completo de criação e uso de um pipeline RAG avançado."""
    
    # Configurar monitor
    monitor = PipelineMonitor()
    
    # Criar pipeline usando o builder
    builder = PipelineBuilder()
    pipeline = (
        builder
        .add_step(
            "process_documents",
            "DocumentProcessor",
            {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "include_metadata": True
            }
        )
        .add_step(
            "embed_documents",
            "TextEmbedder",
            {
                "model": "text-embedding-3-large",
                "dimensions": 1536,
                "normalize": True
            }
        )
        .add_step(
            "store_embeddings",
            "VectorStore",
            {
                "db_type": "chroma",
                "collection": "rag_documents",
                "persist_directory": "./data/vectordb"
            }
        )
        .add_step(
            "embed_query",
            "TextEmbedder",
            {
                "model": "text-embedding-3-large",
                "dimensions": 1536,
                "normalize": True
            }
        )
        .add_step(
            "retrieve",
            "VectorRetriever",
            {
                "db_type": "chroma",
                "collection": "rag_documents",
                "top_k": 5,
                "search_type": "similarity",
                "persist_directory": "./data/vectordb"
            }
        )
        .add_step(
            "rerank",
            "Reranker",
            {
                "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "top_k": 3
            }
        )
        .add_step(
            "generate",
            "LLMGenerator",
            {
                "model": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 1000,
                "system_prompt": """Você é um assistente de IA especializado em responder perguntas com base nos documentos fornecidos.
                Use apenas as informações dos documentos para responder. Se a informação não estiver nos documentos, diga que não sabe.""",
                "prompt_template": """Documentos:
                {context}
                
                Pergunta: {query}
                
                Resposta:"""
            }
        )
        .build()
    )
    
    # Adicionar monitor ao pipeline
    pipeline.add_monitor(monitor)
    
    # Salvar a configuração do pipeline
    pipeline_config = pipeline.to_config()
    os.makedirs("./config", exist_ok=True)
    with open("./config/advanced_rag_pipeline.json", "w") as f:
        json.dump(pipeline_config, f, indent=2)
    
    print(f"Pipeline configurado e salvo em ./config/advanced_rag_pipeline.json")
    
    # Função para indexar documentos
    def index_documents(documents_dir):
        """Indexa documentos usando o pipeline."""
        document_files = []
        for filename in os.listdir(documents_dir):
            if filename.endswith((".txt", ".md", ".pdf")):
                document_files.append(os.path.join(documents_dir, filename))
        
        print(f"Indexando {len(document_files)} documentos...")
        
        # Processar e indexar cada documento
        for file_path in document_files:
            with open(file_path, "rb") as f:
                content = f.read()
            
            # Executar apenas as etapas de processamento e armazenamento
            result = pipeline.run_steps(
                ["process_documents", "embed_documents", "store_embeddings"],
                input_data={"document": content, "metadata": {"source": file_path}}
            )
            
            print(f"Documento indexado: {file_path}")
            print(f"  Chunks: {len(result['chunks'])}")
            print(f"  Embeddings: {len(result['embeddings'])}")
        
        print("Indexação concluída.")
    
    # Função para consultar o pipeline
    def query_pipeline(query):
        """Consulta o pipeline RAG com uma pergunta."""
        print(f"\nConsulta: {query}")
        
        # Executar apenas as etapas de consulta
        result = pipeline.run_steps(
            ["embed_query", "retrieve", "rerank", "generate"],
            input_data={"query": query}
        )
        
        print("\nDocumentos recuperados:")
        for i, doc in enumerate(result["retrieved_documents"][:3]):
            print(f"  {i+1}. {doc['metadata'].get('source', 'Desconhecido')} (Score: {doc['score']:.4f})")
            print(f"     {doc['content'][:100]}...")
        
        print("\nResposta gerada:")
        print(result["generated_text"])
        
        # Obter métricas de execução
        metrics = monitor.get_metrics()
        print("\nMétricas de execução:")
        print(f"  Tempo total: {metrics.total_execution_time} ms")
        for step_id, step_metrics in metrics.step_metrics.items():
            if step_id in ["embed_query", "retrieve", "rerank", "generate"]:
                print(f"  {step_id}: {step_metrics.execution_time} ms")
        
        return result
    
    # Retornar as funções para uso
    return {
        "pipeline": pipeline,
        "index_documents": index_documents,
        "query_pipeline": query_pipeline
    }

if __name__ == "__main__":
    # Criar o pipeline e as funções auxiliares
    rag_system = create_advanced_rag_pipeline()
    
    # Indexar documentos de exemplo
    rag_system["index_documents"]("./documents")
    
    # Consultar o pipeline
    queries = [
        "O que é RAG e como funciona?",
        "Quais são as melhores práticas para implementar RAG?",
        "Como posso avaliar a qualidade de um sistema RAG?"
    ]
    
    for query in queries:
        rag_system["query_pipeline"](query)
```

## Configuração Avançada

```python
from pepperpy.pipeline import (
    PipelineConfig,
    ExecutionConfig,
    MonitoringConfig,
    OptimizationConfig
)

# Configuração avançada de execução
execution_config = ExecutionConfig(
    max_concurrency=4,
    timeout=30,
    retry_enabled=True,
    max_retries=3,
    retry_delay=2,
    backoff_factor=2,
    fail_fast=False,
    propagate_exceptions=False,
    validate_inputs=True,
    validate_outputs=True
)

# Configuração avançada de monitoramento
monitoring_config = MonitoringConfig(
    metrics_enabled=True,
    tracing_enabled=True,
    logging_level="INFO",
    log_inputs=True,
    log_outputs=True,
    performance_tracking=True,
    export_metrics=True,
    metrics_format="prometheus",
    metrics_endpoint="http://localhost:9090/metrics"
)

# Configuração avançada de otimização
optimization_config = OptimizationConfig(
    caching_enabled=True,
    cache_ttl=3600,
    batch_processing_enabled=True,
    optimal_batch_size=16,
    parallel_processing_enabled=True,
    max_parallel_tasks=4,
    dynamic_resource_allocation=True,
    memory_optimization=True,
    max_memory_usage_mb=1024
)

# Configuração completa do pipeline
pipeline_config = PipelineConfig(
    name="advanced_rag_pipeline",
    description="Pipeline RAG avançado com configurações otimizadas",
    version="1.0.0",
    execution_config=execution_config,
    monitoring_config=monitoring_config,
    optimization_config=optimization_config,
    steps=[
        # Definição das etapas do pipeline...
    ]
)

# Criar pipeline com configuração avançada
from pepperpy.pipeline import Pipeline
pipeline = Pipeline.from_config(pipeline_config)
```

## Melhores Práticas

1. **Modularize Seus Pipelines**: Divida pipelines complexos em componentes menores e reutilizáveis para melhorar a manutenção e testabilidade.

2. **Use Configurações Declarativas**: Defina pipelines usando configurações declarativas (YAML, JSON) para facilitar o versionamento, compartilhamento e modificação.

3. **Implemente Tratamento de Erros Robusto**: Configure estratégias de retry, fallback e tratamento de erros para garantir a resiliência dos pipelines em produção.

4. **Monitore o Desempenho**: Utilize as ferramentas de monitoramento para identificar gargalos e otimizar o desempenho dos pipelines.

5. **Otimize para Seu Caso de Uso**: Configure estratégias de otimização (cache, processamento em lote) com base nas características específicas do seu caso de uso.

6. **Teste Pipelines Isoladamente**: Teste cada etapa do pipeline isoladamente antes de integrá-las para facilitar a depuração.

7. **Documente Entradas e Saídas**: Documente claramente as entradas e saídas esperadas de cada etapa do pipeline para facilitar a integração e manutenção.