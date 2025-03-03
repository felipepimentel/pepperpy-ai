# Módulo Optimization

O módulo `optimization` fornece ferramentas para otimizar o desempenho, eficiência e custo de aplicações baseadas em LLMs no framework PepperPy.

## Visão Geral

O módulo Optimization permite:

- Otimizar o desempenho de modelos e pipelines
- Reduzir custos de operação com LLMs
- Melhorar a eficiência de processamento
- Implementar técnicas de quantização e compressão
- Balancear qualidade e velocidade
- Realizar benchmarks e testes comparativos

## Principais Componentes

### Otimização de Prompts

```python
from pepperpy.optimization.prompt import (
    PromptOptimizer,
    PromptCompressor,
    PromptDistiller,
    PromptAnalyzer
)

# Analisar um prompt para identificar oportunidades de otimização
prompt = """
Você é um assistente útil e informativo. Por favor, responda à seguinte pergunta 
com detalhes e explicações claras, fornecendo exemplos quando apropriado.
Pergunta: Quais são as principais técnicas de otimização para sistemas baseados em LLM?
"""

analyzer = PromptAnalyzer()
analysis = analyzer.analyze(prompt)

print(f"Tamanho do prompt: {analysis.token_count} tokens")
print(f"Complexidade: {analysis.complexity_score}/10")
print(f"Redundância: {analysis.redundancy_score}/10")
print(f"Clareza: {analysis.clarity_score}/10")
print(f"Sugestões de otimização: {analysis.optimization_suggestions}")

# Comprimir um prompt para reduzir tokens
compressor = PromptCompressor()
compressed_prompt = compressor.compress(prompt)

print(f"Prompt original: {len(prompt)} caracteres, {analyzer.count_tokens(prompt)} tokens")
print(f"Prompt comprimido: {len(compressed_prompt)} caracteres, {analyzer.count_tokens(compressed_prompt)} tokens")
print(f"Redução: {100 * (1 - len(compressed_prompt) / len(prompt)):.2f}%")
print(f"Prompt comprimido: {compressed_prompt}")

# Destilar um prompt para manter a essência com menos tokens
distiller = PromptDistiller()
distilled_prompt = distiller.distill(prompt)

print(f"Prompt destilado: {distilled_prompt}")

# Otimizar um prompt para melhor desempenho
optimizer = PromptOptimizer()
optimized_prompt = optimizer.optimize(
    prompt,
    target="quality",  # Alternativas: "efficiency", "balanced"
    max_tokens=100
)

print(f"Prompt otimizado: {optimized_prompt}")
```

### Otimização de Modelos

```python
from pepperpy.optimization.model import (
    ModelOptimizer,
    ModelQuantizer,
    ModelPruner,
    ModelCompressor
)

# Quantizar um modelo para reduzir tamanho e melhorar velocidade
quantizer = ModelQuantizer()
quantized_model = quantizer.quantize(
    model_path="./models/llm-model",
    bits=8,  # Opções: 8, 4, 3, 2
    quantization_type="int",  # Alternativas: "float", "dynamic"
    device="cuda"
)

print(f"Modelo quantizado salvo em: {quantized_model.path}")
print(f"Tamanho original: {quantized_model.original_size} MB")
print(f"Tamanho após quantização: {quantized_model.quantized_size} MB")
print(f"Redução: {quantized_model.size_reduction_percent}%")
print(f"Speedup estimado: {quantized_model.estimated_speedup}x")

# Podar um modelo para remover pesos menos importantes
pruner = ModelPruner()
pruned_model = pruner.prune(
    model_path="./models/llm-model",
    sparsity=0.3,  # 30% dos pesos serão removidos
    method="magnitude",  # Alternativas: "random", "structured"
    fine_tune=True,
    fine_tune_dataset="./data/fine_tune_data.jsonl",
    fine_tune_epochs=1
)

print(f"Modelo podado salvo em: {pruned_model.path}")
print(f"Tamanho original: {pruned_model.original_size} MB")
print(f"Tamanho após poda: {pruned_model.pruned_size} MB")
print(f"Redução: {pruned_model.size_reduction_percent}%")
print(f"Perda de performance estimada: {pruned_model.estimated_performance_loss}%")

# Comprimir um modelo usando técnicas avançadas
compressor = ModelCompressor()
compressed_model = compressor.compress(
    model_path="./models/llm-model",
    method="distillation",  # Alternativas: "knowledge_distillation", "low_rank"
    teacher_model_path="./models/llm-model-large",
    student_model_config={
        "hidden_size": 768,
        "num_layers": 6,
        "num_attention_heads": 12
    },
    training_data="./data/distillation_data.jsonl",
    epochs=3
)

print(f"Modelo comprimido salvo em: {compressed_model.path}")
print(f"Tamanho original: {compressed_model.original_size} MB")
print(f"Tamanho após compressão: {compressed_model.compressed_size} MB")
print(f"Redução: {compressed_model.size_reduction_percent}%")
print(f"Perda de performance estimada: {compressed_model.estimated_performance_loss}%")

# Otimizar um modelo para um caso de uso específico
optimizer = ModelOptimizer()
optimized_model = optimizer.optimize(
    model_path="./models/llm-model",
    optimization_target="latency",  # Alternativas: "throughput", "memory", "balanced"
    device="cuda",
    batch_size=16,
    precision="fp16",  # Alternativas: "fp32", "bf16", "int8"
    compile=True,
    dynamic_shapes=True,
    enable_flash_attention=True
)

print(f"Modelo otimizado salvo em: {optimized_model.path}")
print(f"Configuração de otimização: {optimized_model.config}")
print(f"Speedup medido: {optimized_model.measured_speedup}x")
```

### Otimização de Pipelines

```python
from pepperpy.optimization.pipeline import (
    PipelineOptimizer,
    PipelineBenchmark,
    PipelineProfiler,
    PipelineCache
)

# Criar um benchmark para medir desempenho de pipeline
benchmark = PipelineBenchmark()
benchmark_results = benchmark.run(
    pipeline_config={
        "name": "rag_pipeline",
        "components": {
            "retriever": {"type": "vector_db", "top_k": 5},
            "reranker": {"type": "cross_encoder", "model": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
            "generator": {"type": "llm", "model": "gpt-3.5-turbo"}
        }
    },
    test_queries=["Como funciona RAG?", "Quais são as melhores práticas para fine-tuning?"],
    metrics=["latency", "throughput", "token_usage", "quality"],
    iterations=5,
    concurrency=2
)

print(f"Resultados do benchmark:")
print(f"Latência média: {benchmark_results.avg_latency} ms")
print(f"Throughput: {benchmark_results.throughput} consultas/s")
print(f"Uso de tokens: {benchmark_results.token_usage} tokens")
print(f"Pontuação de qualidade: {benchmark_results.quality_score}/10")

# Perfilar um pipeline para identificar gargalos
profiler = PipelineProfiler()
profile_results = profiler.profile(
    pipeline_name="rag_pipeline",
    test_queries=["Como otimizar um pipeline RAG?"],
    detailed=True
)

print(f"Resultados do profiling:")
for component, stats in profile_results.component_stats.items():
    print(f"Componente: {component}")
    print(f"  Tempo médio: {stats.avg_time} ms ({stats.percentage}% do total)")
    print(f"  Uso de memória: {stats.memory_usage} MB")
    print(f"  Gargalo: {stats.is_bottleneck}")

# Otimizar um pipeline com base em resultados de profiling
optimizer = PipelineOptimizer()
optimized_pipeline = optimizer.optimize(
    pipeline_name="rag_pipeline",
    optimization_target="latency",  # Alternativas: "throughput", "cost", "quality", "balanced"
    profile_results=profile_results,
    max_cost_per_query=0.01,
    min_quality_score=7.0
)

print(f"Pipeline otimizado:")
print(f"Configuração: {optimized_pipeline.config}")
print(f"Melhorias estimadas:")
print(f"  Latência: {optimized_pipeline.estimated_improvements.latency_reduction}%")
print(f"  Custo: {optimized_pipeline.estimated_improvements.cost_reduction}%")
print(f"  Qualidade: {optimized_pipeline.estimated_improvements.quality_change}%")

# Implementar cache para pipeline
pipeline_cache = PipelineCache(
    cache_type="redis",
    connection_string="redis://localhost:6379/0",
    ttl=3600,
    max_size_mb=1000
)

# Adicionar cache ao pipeline
optimized_pipeline.add_cache(pipeline_cache)
print(f"Cache adicionado ao pipeline")
```

### Otimização de Custos

```python
from pepperpy.optimization.cost import (
    CostOptimizer,
    CostEstimator,
    CostMonitor,
    ModelSelector
)

# Estimar custos de operação
estimator = CostEstimator()
cost_estimate = estimator.estimate(
    model="gpt-4o",
    avg_input_tokens=500,
    avg_output_tokens=300,
    queries_per_day=1000,
    days=30
)

print(f"Estimativa de custo mensal:")
print(f"  Custo total: ${cost_estimate.total_cost}")
print(f"  Custo de entrada: ${cost_estimate.input_cost}")
print(f"  Custo de saída: ${cost_estimate.output_cost}")
print(f"  Tokens totais: {cost_estimate.total_tokens}")

# Monitorar custos em tempo real
monitor = CostMonitor()
monitor.start(
    models=["gpt-4o", "gpt-3.5-turbo", "claude-3-opus-20240229"],
    alert_threshold=100.0,  # Alerta quando custo diário ultrapassar $100
    alert_email="admin@example.com"
)

# Verificar custos atuais
current_costs = monitor.get_current_costs()
print(f"Custos atuais:")
for model, cost in current_costs.items():
    print(f"  {model}: ${cost}")

# Selecionar modelo com melhor custo-benefício
selector = ModelSelector()
best_model = selector.select(
    task="summarization",
    quality_threshold=0.8,  # Qualidade mínima aceitável (0-1)
    max_cost_per_1k_tokens=0.01,
    max_latency_ms=500
)

print(f"Modelo recomendado: {best_model.name}")
print(f"  Custo por 1k tokens: ${best_model.cost_per_1k_tokens}")
print(f"  Pontuação de qualidade: {best_model.quality_score}")
print(f"  Latência média: {best_model.avg_latency} ms")

# Otimizar custos de operação
optimizer = CostOptimizer()
optimization_plan = optimizer.optimize(
    current_setup={
        "models": {
            "summarization": "gpt-4o",
            "classification": "gpt-4o",
            "qa": "gpt-4o",
            "chat": "gpt-4o"
        },
        "avg_usage": {
            "summarization": {"queries_per_day": 500, "avg_tokens": 800},
            "classification": {"queries_per_day": 1000, "avg_tokens": 300},
            "qa": {"queries_per_day": 800, "avg_tokens": 600},
            "chat": {"queries_per_day": 2000, "avg_tokens": 1000}
        }
    },
    max_quality_reduction=0.1,  # Máxima redução aceitável na qualidade
    target_cost_reduction=0.3  # Alvo de redução de custos (30%)
)

print(f"Plano de otimização de custos:")
print(f"  Redução estimada: {optimization_plan.estimated_savings_percent}%")
print(f"  Economia mensal estimada: ${optimization_plan.estimated_monthly_savings}")
print(f"  Recomendações:")
for task, recommendation in optimization_plan.recommendations.items():
    print(f"    {task}: Mudar de {recommendation.current_model} para {recommendation.recommended_model}")
    print(f"      Economia: ${recommendation.monthly_savings}")
    print(f"      Impacto na qualidade: {recommendation.quality_impact}%")
```

### Benchmarking e Testes

```python
from pepperpy.optimization.benchmark import (
    Benchmark,
    ModelBenchmark,
    RAGBenchmark,
    LatencyBenchmark,
    QualityBenchmark
)

# Benchmark de modelos
model_benchmark = ModelBenchmark()
model_results = model_benchmark.run(
    models=["gpt-4o", "gpt-3.5-turbo", "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
    tasks=["summarization", "qa", "classification"],
    datasets={
        "summarization": "./data/benchmark/summarization_dataset.jsonl",
        "qa": "./data/benchmark/qa_dataset.jsonl",
        "classification": "./data/benchmark/classification_dataset.jsonl"
    },
    metrics=["accuracy", "f1", "rouge", "latency", "cost"]
)

print(f"Resultados do benchmark de modelos:")
for model, results in model_results.items():
    print(f"  {model}:")
    for task, metrics in results.items():
        print(f"    {task}:")
        for metric, value in metrics.items():
            print(f"      {metric}: {value}")

# Benchmark de sistemas RAG
rag_benchmark = RAGBenchmark()
rag_results = rag_benchmark.run(
    rag_pipelines={
        "basic_rag": {
            "retriever": {"type": "bm25"},
            "generator": {"model": "gpt-3.5-turbo"}
        },
        "advanced_rag": {
            "retriever": {"type": "vector_db", "model": "text-embedding-3-large"},
            "reranker": {"type": "cross_encoder", "model": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
            "generator": {"model": "gpt-4o"}
        }
    },
    dataset="./data/benchmark/rag_dataset.jsonl",
    metrics=["relevance", "faithfulness", "answer_correctness", "latency", "cost"]
)

print(f"Resultados do benchmark RAG:")
for pipeline, metrics in rag_results.items():
    print(f"  {pipeline}:")
    for metric, value in metrics.items():
        print(f"    {metric}: {value}")

# Benchmark de latência
latency_benchmark = LatencyBenchmark()
latency_results = latency_benchmark.run(
    models=["gpt-4o", "gpt-3.5-turbo", "claude-3-opus-20240229"],
    input_lengths=[100, 500, 1000, 2000],
    output_lengths=[100, 500, 1000],
    batch_sizes=[1, 4, 8],
    iterations=10,
    warmup_iterations=2
)

print(f"Resultados do benchmark de latência:")
for model, results in latency_results.items():
    print(f"  {model}:")
    for input_length, output_results in results.items():
        print(f"    Input tokens: {input_length}")
        for output_length, batch_results in output_results.items():
            print(f"      Output tokens: {output_length}")
            for batch_size, latency in batch_results.items():
                print(f"        Batch size {batch_size}: {latency} ms")

# Benchmark de qualidade
quality_benchmark = QualityBenchmark()
quality_results = quality_benchmark.run(
    models=["gpt-4o", "gpt-3.5-turbo", "claude-3-opus-20240229"],
    evaluation_datasets={
        "reasoning": "./data/benchmark/reasoning_dataset.jsonl",
        "knowledge": "./data/benchmark/knowledge_dataset.jsonl",
        "creativity": "./data/benchmark/creativity_dataset.jsonl",
        "instruction_following": "./data/benchmark/instruction_dataset.jsonl"
    },
    evaluator_model="gpt-4o",
    metrics=["correctness", "relevance", "coherence", "fluency"]
)

print(f"Resultados do benchmark de qualidade:")
for model, results in quality_results.items():
    print(f"  {model}:")
    for dataset, metrics in results.items():
        print(f"    {dataset}:")
        for metric, value in metrics.items():
            print(f"      {metric}: {value}")
```

## Exemplo Completo

```python
from pepperpy.optimization import (
    ModelOptimizer, PromptOptimizer, PipelineOptimizer, 
    CostOptimizer, Benchmark
)
from pepperpy.llm import LLMProvider
from pepperpy.rag import RAGPipeline
import json
import os

def optimize_rag_system():
    """Exemplo completo de otimização de um sistema RAG."""
    
    print("Iniciando otimização do sistema RAG...")
    
    # 1. Configuração inicial do sistema RAG
    print("\n1. Configurando sistema RAG inicial...")
    
    # Carregar configuração do pipeline
    with open("./config/rag_pipeline.json", "r") as f:
        pipeline_config = json.load(f)
    
    # Criar pipeline RAG
    rag_pipeline = RAGPipeline.from_config(pipeline_config)
    
    # 2. Benchmark do sistema atual
    print("\n2. Realizando benchmark do sistema atual...")
    
    benchmark = Benchmark()
    benchmark_results = benchmark.run(
        pipeline=rag_pipeline,
        test_dataset="./data/benchmark/rag_test_queries.jsonl",
        metrics=["latency", "quality", "token_usage", "cost"]
    )
    
    print(f"Resultados do benchmark inicial:")
    print(f"  Latência média: {benchmark_results.avg_latency} ms")
    print(f"  Pontuação de qualidade: {benchmark_results.quality_score}/10")
    print(f"  Uso médio de tokens: {benchmark_results.avg_token_usage}")
    print(f"  Custo médio por consulta: ${benchmark_results.avg_cost_per_query}")
    
    # 3. Otimização de prompts
    print("\n3. Otimizando prompts...")
    
    prompt_optimizer = PromptOptimizer()
    
    # Obter prompts atuais
    system_prompt = pipeline_config["llm"]["system_prompt"]
    query_prompt_template = pipeline_config["llm"]["query_prompt_template"]
    
    # Otimizar prompts
    optimized_system_prompt = prompt_optimizer.optimize(
        system_prompt,
        target="balanced",
        max_tokens=int(len(system_prompt) * 0.7)  # Reduzir em 30%
    )
    
    optimized_query_prompt = prompt_optimizer.optimize(
        query_prompt_template,
        target="balanced",
        max_tokens=int(len(query_prompt_template) * 0.7)  # Reduzir em 30%
    )
    
    print(f"Prompt do sistema original ({len(system_prompt)} caracteres):")
    print(f"  {system_prompt[:100]}...")
    print(f"Prompt do sistema otimizado ({len(optimized_system_prompt)} caracteres):")
    print(f"  {optimized_system_prompt[:100]}...")
    
    # Atualizar prompts no pipeline
    pipeline_config["llm"]["system_prompt"] = optimized_system_prompt
    pipeline_config["llm"]["query_prompt_template"] = optimized_query_prompt
    
    # 4. Otimização de modelo
    print("\n4. Otimizando seleção de modelo...")
    
    cost_optimizer = CostOptimizer()
    model_recommendation = cost_optimizer.recommend_model(
        current_model=pipeline_config["llm"]["model"],
        task="rag",
        quality_threshold=0.8,  # Manter pelo menos 80% da qualidade
        max_latency_ms=500
    )
    
    print(f"Modelo atual: {pipeline_config['llm']['model']}")
    print(f"Modelo recomendado: {model_recommendation.model}")
    print(f"  Economia estimada: {model_recommendation.cost_reduction_percent}%")
    print(f"  Impacto na qualidade: {model_recommendation.quality_impact}%")
    print(f"  Impacto na latência: {model_recommendation.latency_impact}%")
    
    # Atualizar modelo no pipeline
    pipeline_config["llm"]["model"] = model_recommendation.model
    
    # 5. Otimização de pipeline
    print("\n5. Otimizando pipeline...")
    
    pipeline_optimizer = PipelineOptimizer()
    optimized_pipeline_config = pipeline_optimizer.optimize(
        pipeline_config=pipeline_config,
        optimization_target="balanced",
        benchmark_results=benchmark_results
    )
    
    print("Otimizações de pipeline aplicadas:")
    for change in optimized_pipeline_config.changes:
        print(f"  - {change}")
    
    # 6. Implementar cache
    print("\n6. Implementando estratégia de cache...")
    
    optimized_pipeline_config.config["cache"] = {
        "enabled": True,
        "type": "redis",
        "ttl": 3600,
        "namespace": "rag_cache"
    }
    
    print("Configuração de cache adicionada")
    
    # 7. Criar pipeline otimizado
    print("\n7. Criando pipeline otimizado...")
    
    optimized_rag_pipeline = RAGPipeline.from_config(optimized_pipeline_config.config)
    
    # 8. Benchmark final
    print("\n8. Realizando benchmark do sistema otimizado...")
    
    optimized_benchmark_results = benchmark.run(
        pipeline=optimized_rag_pipeline,
        test_dataset="./data/benchmark/rag_test_queries.jsonl",
        metrics=["latency", "quality", "token_usage", "cost"]
    )
    
    print(f"Resultados do benchmark após otimização:")
    print(f"  Latência média: {optimized_benchmark_results.avg_latency} ms")
    print(f"  Pontuação de qualidade: {optimized_benchmark_results.quality_score}/10")
    print(f"  Uso médio de tokens: {optimized_benchmark_results.avg_token_usage}")
    print(f"  Custo médio por consulta: ${optimized_benchmark_results.avg_cost_per_query}")
    
    # 9. Comparar resultados
    print("\n9. Comparando resultados...")
    
    latency_improvement = (benchmark_results.avg_latency - optimized_benchmark_results.avg_latency) / benchmark_results.avg_latency * 100
    quality_change = (optimized_benchmark_results.quality_score - benchmark_results.quality_score) / benchmark_results.quality_score * 100
    token_reduction = (benchmark_results.avg_token_usage - optimized_benchmark_results.avg_token_usage) / benchmark_results.avg_token_usage * 100
    cost_reduction = (benchmark_results.avg_cost_per_query - optimized_benchmark_results.avg_cost_per_query) / benchmark_results.avg_cost_per_query * 100
    
    print(f"Melhorias:")
    print(f"  Redução de latência: {latency_improvement:.2f}%")
    print(f"  Mudança na qualidade: {quality_change:.2f}%")
    print(f"  Redução no uso de tokens: {token_reduction:.2f}%")
    print(f"  Redução de custo: {cost_reduction:.2f}%")
    
    # 10. Salvar configuração otimizada
    print("\n10. Salvando configuração otimizada...")
    
    with open("./config/optimized_rag_pipeline.json", "w") as f:
        json.dump(optimized_pipeline_config.config, f, indent=2)
    
    print(f"Configuração otimizada salva em ./config/optimized_rag_pipeline.json")
    
    return {
        "original_benchmark": benchmark_results,
        "optimized_benchmark": optimized_benchmark_results,
        "improvements": {
            "latency": latency_improvement,
            "quality": quality_change,
            "token_usage": token_reduction,
            "cost": cost_reduction
        },
        "optimized_config": optimized_pipeline_config.config
    }

if __name__ == "__main__":
    optimize_rag_system()
```

## Configuração Avançada

```python
from pepperpy.optimization import OptimizationConfig
from pepperpy.optimization.model import ModelOptimizerConfig
from pepperpy.optimization.pipeline import PipelineOptimizerConfig

# Configuração avançada para otimização de modelos
model_optimizer_config = ModelOptimizerConfig(
    quantization_enabled=True,
    quantization_bits=8,
    pruning_enabled=True,
    pruning_sparsity=0.3,
    distillation_enabled=False,
    compile_enabled=True,
    flash_attention_enabled=True,
    precision="fp16",
    device_map="auto",
    optimization_level=2,  # 0-3, onde 3 é mais agressivo
    preserve_accuracy=True,
    max_accuracy_drop=0.05  # 5% de queda máxima na precisão
)

# Configuração avançada para otimização de pipeline
pipeline_optimizer_config = PipelineOptimizerConfig(
    cache_enabled=True,
    cache_ttl=3600,
    batch_processing_enabled=True,
    optimal_batch_size=16,
    parallel_processing_enabled=True,
    max_parallel_tasks=4,
    adaptive_retrieval_enabled=True,
    min_retrieval_results=3,
    max_retrieval_results=10,
    dynamic_model_selection=True,
    fallback_strategies_enabled=True,
    timeout_ms=5000,
    optimization_level=2  # 0-3, onde 3 é mais agressivo
)

# Configuração global para otimização
global_optimization_config = OptimizationConfig(
    model_optimizer_config=model_optimizer_config,
    pipeline_optimizer_config=pipeline_optimizer_config,
    cost_optimization_enabled=True,
    max_cost_per_query=0.01,
    quality_threshold=0.8,
    latency_target_ms=300,
    optimization_strategy="balanced"  # "cost", "quality", "latency", "balanced"
)

# Aplicar configuração global
from pepperpy.optimization import set_global_config
set_global_config(global_optimization_config)
```

## Melhores Práticas

1. **Comece com Benchmarks**: Antes de otimizar, estabeleça métricas de referência para entender o desempenho atual e identificar áreas para melhoria.

2. **Otimize Prompts Primeiro**: A otimização de prompts geralmente oferece o melhor retorno sobre investimento, reduzindo custos sem necessidade de mudanças na infraestrutura.

3. **Equilibre Custo e Qualidade**: Encontre o equilíbrio certo entre redução de custos e manutenção da qualidade para seu caso de uso específico.

4. **Implemente Caching Estratégico**: Use cache para consultas frequentes e respostas, mas defina TTLs apropriados para evitar dados desatualizados.

5. **Monitore Continuamente**: Implemente monitoramento contínuo de custos, desempenho e qualidade para identificar oportunidades de otimização.

6. **Teste Antes de Implantar**: Sempre teste otimizações em ambiente de desenvolvimento antes de aplicá-las em produção.

7. **Considere o Ciclo Completo**: Otimize o pipeline completo, não apenas componentes individuais, para obter os melhores resultados. 