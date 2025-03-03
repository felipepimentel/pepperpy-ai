# Módulo Observability

O módulo `observability` fornece ferramentas para monitorar, rastrear e analisar o comportamento de aplicações PepperPy em tempo real.

## Visão Geral

O módulo Observability permite:

- Monitorar o desempenho de componentes e pipelines
- Rastrear solicitações e respostas de LLMs
- Coletar métricas de uso e latência
- Visualizar fluxos de execução
- Detectar e diagnosticar problemas

## Principais Componentes

### Telemetria

```python
from pepperpy.observability import (
    Telemetry,
    MetricsCollector,
    Counter,
    Gauge,
    Histogram
)

# Inicializar telemetria
telemetry = Telemetry(
    service_name="my-pepperpy-app",
    environment="production"
)

# Coletor de métricas
metrics = MetricsCollector()

# Definir métricas
request_counter = metrics.create_counter(
    name="llm_requests_total",
    description="Total number of LLM requests",
    labels=["model", "provider"]
)

token_gauge = metrics.create_gauge(
    name="token_usage_current",
    description="Current token usage",
    labels=["type"]
)

latency_histogram = metrics.create_histogram(
    name="request_latency_seconds",
    description="Request latency in seconds",
    labels=["endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Usar métricas
request_counter.inc(labels={"model": "gpt-4", "provider": "openai"})
token_gauge.set(100, labels={"type": "prompt"})
token_gauge.set(50, labels={"type": "completion"})
latency_histogram.observe(1.2, labels={"endpoint": "/generate"})

# Exportar métricas
metrics.export_prometheus("/metrics")
```

### Rastreamento (Tracing)

```python
from pepperpy.observability import (
    Tracer,
    Span,
    SpanContext,
    TraceExporter
)

# Inicializar rastreador
tracer = Tracer(
    service_name="my-pepperpy-app",
    exporter=TraceExporter.JAEGER
)

# Criar um span raiz
with tracer.start_span("process_user_query") as root_span:
    # Adicionar atributos ao span
    root_span.set_attribute("user_id", "user123")
    root_span.set_attribute("query_type", "rag")
    
    # Criar um span filho para recuperação de documentos
    with tracer.start_span("retrieve_documents", parent=root_span) as retrieve_span:
        retrieve_span.set_attribute("query", "Como funciona o RAG?")
        retrieve_span.set_attribute("top_k", 5)
        
        # Simular recuperação de documentos
        documents = ["doc1", "doc2", "doc3"]
        
        # Registrar eventos no span
        retrieve_span.add_event("documents_retrieved", {"count": len(documents)})
    
    # Criar um span filho para geração de resposta
    with tracer.start_span("generate_response", parent=root_span) as generate_span:
        generate_span.set_attribute("model", "gpt-4")
        
        # Simular geração de resposta
        response = "O RAG funciona combinando recuperação e geração..."
        
        # Registrar eventos no span
        generate_span.add_event("response_generated", {"length": len(response)})
    
    # Registrar resultado final
    root_span.set_status("OK")
```

### Logging

```python
from pepperpy.observability import (
    Logger,
    LogLevel,
    LogFormatter,
    LogHandler
)

# Configurar logger
logger = Logger(
    name="pepperpy.rag",
    level=LogLevel.INFO,
    formatter=LogFormatter.JSON,
    handlers=[LogHandler.CONSOLE, LogHandler.FILE]
)

# Configurar contexto do logger
logger.set_context({
    "service": "rag_service",
    "environment": "production"
})

# Usar logger
logger.info(
    "RAG query processed",
    extra={
        "user_id": "user123",
        "query": "Como funciona o RAG?",
        "num_docs_retrieved": 5,
        "response_length": 256,
        "processing_time_ms": 450
    }
)

# Registrar erros
try:
    # Código que pode gerar exceção
    raise ValueError("Documento não encontrado")
except Exception as e:
    logger.error(
        "Error processing RAG query",
        exc_info=e,
        extra={
            "user_id": "user123",
            "query": "Como funciona o RAG?"
        }
    )
```

### Monitoramento de Saúde

```python
from pepperpy.observability import (
    HealthMonitor,
    HealthCheck,
    HealthStatus,
    ServiceDependency
)

# Criar monitor de saúde
health_monitor = HealthMonitor(
    service_name="rag_service",
    check_interval_seconds=60
)

# Definir dependências
openai_dependency = ServiceDependency(
    name="openai",
    endpoint="https://api.openai.com/v1/chat/completions",
    timeout_seconds=5
)

database_dependency = ServiceDependency(
    name="vector_db",
    connection_string="postgresql://user:password@localhost:5432/vectors"
)

# Adicionar verificações de saúde
health_monitor.add_check(
    HealthCheck(
        name="openai_api",
        check_fn=lambda: openai_dependency.check_connection(),
        severity="critical"
    )
)

health_monitor.add_check(
    HealthCheck(
        name="vector_db_connection",
        check_fn=lambda: database_dependency.check_connection(),
        severity="critical"
    )
)

health_monitor.add_check(
    HealthCheck(
        name="disk_space",
        check_fn=lambda: check_disk_space() > 1_000_000_000,  # 1GB
        severity="warning"
    )
)

# Iniciar monitoramento
health_monitor.start()

# Verificar status atual
status = health_monitor.check_health()
print(f"Overall health: {status.overall_status}")

for check in status.checks:
    print(f"{check.name}: {check.status} - {check.message}")
```

### Dashboards e Visualizações

```python
from pepperpy.observability import (
    Dashboard,
    MetricsPanel,
    LogsPanel,
    TracesPanel,
    TimeRange
)

# Criar dashboard
dashboard = Dashboard(
    title="RAG Service Monitoring",
    description="Monitoring dashboard for RAG service",
    refresh_interval_seconds=30
)

# Adicionar painéis de métricas
dashboard.add_panel(
    MetricsPanel(
        title="Request Rate",
        query='rate(llm_requests_total{service="rag_service"}[5m])',
        panel_type="line",
        position={"x": 0, "y": 0, "w": 12, "h": 8}
    )
)

dashboard.add_panel(
    MetricsPanel(
        title="Latency",
        query='histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket{service="rag_service"}[5m])) by (le))',
        panel_type="line",
        position={"x": 12, "y": 0, "w": 12, "h": 8}
    )
)

# Adicionar painel de logs
dashboard.add_panel(
    LogsPanel(
        title="Error Logs",
        query='level="ERROR" AND service="rag_service"',
        position={"x": 0, "y": 8, "w": 24, "h": 8}
    )
)

# Adicionar painel de traces
dashboard.add_panel(
    TracesPanel(
        title="Slow Requests",
        query='service="rag_service" AND duration > 1s',
        position={"x": 0, "y": 16, "w": 24, "h": 8}
    )
)

# Exportar dashboard
dashboard.export("grafana", "rag_service_dashboard.json")
```

## Exemplo Completo

```python
from pepperpy.observability import (
    ObservabilityManager,
    Telemetry,
    Tracer,
    Logger,
    HealthMonitor,
    MetricsCollector,
    LogLevel
)
from pepperpy.llm import ChatSession, ChatOptions
from pepperpy.rag import RAGPipeline
import time
import uuid

# Configurar gerenciador de observabilidade
obs_manager = ObservabilityManager(
    service_name="pepperpy_rag_service",
    environment="production",
    version="1.0.0",
    exporters={
        "metrics": "prometheus",
        "traces": "jaeger",
        "logs": "elasticsearch"
    }
)

# Obter componentes de observabilidade
metrics = obs_manager.get_metrics_collector()
tracer = obs_manager.get_tracer()
logger = obs_manager.get_logger()
health = obs_manager.get_health_monitor()

# Configurar métricas
request_counter = metrics.create_counter(
    name="rag_requests_total",
    description="Total number of RAG requests",
    labels=["status"]
)

token_counter = metrics.create_counter(
    name="token_usage_total",
    description="Total token usage",
    labels=["type"]
)

latency_histogram = metrics.create_histogram(
    name="rag_latency_seconds",
    description="RAG request latency in seconds",
    labels=["stage"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Função para processar consulta RAG com observabilidade
def process_rag_query(query, user_id=None):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Contexto para logs e traces
    context = {
        "request_id": request_id,
        "user_id": user_id,
        "query": query
    }
    
    logger.info("Processing RAG query", extra=context)
    
    # Iniciar span raiz
    with tracer.start_span("process_rag_query") as root_span:
        for key, value in context.items():
            root_span.set_attribute(key, value)
        
        try:
            # Configurar pipeline RAG
            rag_pipeline = RAGPipeline(
                retriever_config={"top_k": 5},
                generator_config={"model": "gpt-4"}
            )
            
            # Recuperar documentos
            retrieval_start = time.time()
            with tracer.start_span("retrieve_documents", parent=root_span) as retrieve_span:
                documents = rag_pipeline.retrieve(query)
                retrieve_span.set_attribute("num_documents", len(documents))
                
                # Registrar evento no span
                retrieve_span.add_event("documents_retrieved", {
                    "count": len(documents),
                    "top_similarity": documents[0].similarity if documents else 0
                })
            
            retrieval_duration = time.time() - retrieval_start
            latency_histogram.observe(retrieval_duration, labels={"stage": "retrieval"})
            logger.debug(f"Retrieved {len(documents)} documents", extra={
                **context,
                "duration_seconds": retrieval_duration
            })
            
            # Gerar resposta
            generation_start = time.time()
            with tracer.start_span("generate_response", parent=root_span) as generate_span:
                response = rag_pipeline.generate(query, documents)
                
                # Registrar uso de tokens
                token_counter.inc(response.usage.prompt_tokens, labels={"type": "prompt"})
                token_counter.inc(response.usage.completion_tokens, labels={"type": "completion"})
                
                generate_span.set_attribute("prompt_tokens", response.usage.prompt_tokens)
                generate_span.set_attribute("completion_tokens", response.usage.completion_tokens)
                generate_span.set_attribute("response_length", len(response.content))
            
            generation_duration = time.time() - generation_start
            latency_histogram.observe(generation_duration, labels={"stage": "generation"})
            
            # Calcular duração total
            total_duration = time.time() - start_time
            latency_histogram.observe(total_duration, labels={"stage": "total"})
            
            # Incrementar contador de solicitações bem-sucedidas
            request_counter.inc(labels={"status": "success"})
            
            # Registrar sucesso
            logger.info("RAG query processed successfully", extra={
                **context,
                "duration_seconds": total_duration,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "response_length": len(response.content)
            })
            
            return {
                "response": response.content,
                "documents": [doc.metadata for doc in documents],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "request_id": request_id
            }
            
        except Exception as e:
            # Incrementar contador de solicitações com falha
            request_counter.inc(labels={"status": "error"})
            
            # Registrar erro
            logger.error("Error processing RAG query", exc_info=e, extra=context)
            
            # Marcar span como erro
            root_span.set_status("ERROR", str(e))
            
            # Retornar erro
            return {
                "error": str(e),
                "request_id": request_id
            }

# Exemplo de uso
if __name__ == "__main__":
    # Iniciar monitoramento de saúde
    health.start()
    
    # Processar consulta
    result = process_rag_query(
        query="Como funciona o RAG no PepperPy?",
        user_id="user123"
    )
    
    print(f"Response: {result['response']}")
    
    # Exportar métricas
    metrics.export_prometheus("./metrics")
    
    # Parar monitoramento de saúde
    health.stop()
```

## Configuração Avançada

```python
from pepperpy.observability import (
    ObservabilityConfig,
    MetricsConfig,
    TracingConfig,
    LoggingConfig,
    HealthConfig,
    SamplingStrategy
)

# Configuração avançada de observabilidade
observability_config = ObservabilityConfig(
    service_name="pepperpy_advanced_service",
    environment="production",
    version="1.0.0",
    
    # Configuração de métricas
    metrics=MetricsConfig(
        enabled=True,
        export_interval_seconds=15,
        exporters=["prometheus", "datadog"],
        endpoint="http://prometheus:9090/metrics",
        default_labels={
            "service": "pepperpy_advanced_service",
            "environment": "production"
        },
        histogram_buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
    ),
    
    # Configuração de rastreamento
    tracing=TracingConfig(
        enabled=True,
        exporter="jaeger",
        endpoint="http://jaeger:14268/api/traces",
        sampling_strategy=SamplingStrategy.RATE_LIMITING,
        sampling_rate=0.1,  # 10% das solicitações
        max_attributes_per_span=64,
        max_events_per_span=128,
        max_links_per_span=32,
        propagation_format="w3c"
    ),
    
    # Configuração de logging
    logging=LoggingConfig(
        enabled=True,
        level="INFO",
        format="json",
        exporters=["console", "file", "elasticsearch"],
        file_path="./logs/pepperpy.log",
        max_file_size_mb=100,
        backup_count=5,
        elasticsearch_url="http://elasticsearch:9200",
        elasticsearch_index="pepperpy-logs",
        include_trace_context=True
    ),
    
    # Configuração de monitoramento de saúde
    health=HealthConfig(
        enabled=True,
        check_interval_seconds=30,
        endpoint="/health",
        include_details=True,
        critical_dependencies=[
            "openai_api",
            "vector_db"
        ]
    )
)

# Inicializar gerenciador de observabilidade com configuração avançada
from pepperpy.observability import ObservabilityManager
obs_manager = ObservabilityManager(config=observability_config)
```

## Melhores Práticas

1. **Implemente Observabilidade desde o Início**: Integre métricas, logs e rastreamento desde o início do desenvolvimento, não como uma reflexão tardia.

2. **Use Contexto Consistente**: Mantenha identificadores consistentes (como request_id, user_id) em logs, métricas e spans para correlacionar dados.

3. **Monitore o que Importa**: Foque em métricas que realmente importam para o desempenho e a experiência do usuário, como latência, taxa de sucesso e uso de recursos.

4. **Estabeleça Linhas de Base**: Defina métricas de linha de base para entender o comportamento normal e detectar anomalias.

5. **Automatize Alertas**: Configure alertas para notificar sobre problemas antes que afetem os usuários, mas evite alertas excessivos que possam levar à fadiga. 