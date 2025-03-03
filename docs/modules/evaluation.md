# Módulo Evaluation

O módulo `evaluation` fornece ferramentas para avaliar o desempenho de modelos, componentes e pipelines do PepperPy.

## Visão Geral

O módulo Evaluation permite:

- Avaliar a qualidade de respostas de modelos de linguagem
- Medir o desempenho de componentes e pipelines
- Comparar diferentes abordagens e configurações
- Gerar relatórios de avaliação detalhados
- Implementar métricas personalizadas

## Principais Componentes

### Avaliação de Modelos

```python
from pepperpy.evaluation import (
    ModelEvaluator,
    EvaluationMetric,
    EvaluationDataset,
    EvaluationResult
)

# Criar um avaliador de modelos
evaluator = ModelEvaluator()

# Definir métricas de avaliação
metrics = [
    EvaluationMetric.ACCURACY,
    EvaluationMetric.PRECISION,
    EvaluationMetric.RECALL,
    EvaluationMetric.F1_SCORE,
    EvaluationMetric.LATENCY
]

# Carregar conjunto de dados de avaliação
dataset = EvaluationDataset.from_csv("test_data.csv")

# Avaliar um modelo
result = evaluator.evaluate(
    model="gpt-4",
    dataset=dataset,
    metrics=metrics,
    task="text_classification"
)

# Acessar resultados
print(f"Accuracy: {result.get_metric('accuracy')}")
print(f"F1 Score: {result.get_metric('f1_score')}")
print(f"Average latency: {result.get_metric('latency')} ms")

# Gerar relatório
report = result.generate_report()
report.save("evaluation_report.pdf")
```

### Avaliação de Respostas

```python
from pepperpy.evaluation.llm import (
    ResponseEvaluator,
    ResponseCriteria,
    ResponseMetric
)

# Criar um avaliador de respostas
response_evaluator = ResponseEvaluator()

# Definir critérios de avaliação
criteria = [
    ResponseCriteria.RELEVANCE,
    ResponseCriteria.ACCURACY,
    ResponseCriteria.COMPLETENESS,
    ResponseCriteria.COHERENCE,
    ResponseCriteria.HELPFULNESS
]

# Avaliar uma resposta
evaluation = response_evaluator.evaluate(
    question="Como funciona o RAG no PepperPy?",
    response="O RAG (Retrieval Augmented Generation) no PepperPy é uma técnica que combina recuperação de informações e geração de texto. Primeiro, o sistema recupera documentos relevantes de uma base de conhecimento usando embeddings e similaridade semântica. Em seguida, esses documentos são usados como contexto para um modelo de linguagem gerar respostas mais precisas e fundamentadas.",
    reference="O RAG no PepperPy funciona em três etapas: indexação de documentos, recuperação semântica e geração contextual.",
    criteria=criteria
)

# Acessar pontuações
for criterion in criteria:
    print(f"{criterion.name}: {evaluation.get_score(criterion)}/5")

# Obter pontuação geral
print(f"Overall score: {evaluation.overall_score}/5")

# Obter feedback detalhado
print(f"Feedback: {evaluation.feedback}")
```

### Avaliação de Pipelines

```python
from pepperpy.evaluation.pipeline import (
    PipelineEvaluator,
    PipelineMetric,
    ComponentMetric
)

# Criar um avaliador de pipeline
pipeline_evaluator = PipelineEvaluator()

# Definir métricas para o pipeline
pipeline_metrics = [
    PipelineMetric.END_TO_END_LATENCY,
    PipelineMetric.THROUGHPUT,
    PipelineMetric.SUCCESS_RATE,
    PipelineMetric.RESOURCE_USAGE
]

# Definir métricas para componentes específicos
component_metrics = {
    "document_loader": [ComponentMetric.LATENCY, ComponentMetric.ERROR_RATE],
    "text_embedder": [ComponentMetric.LATENCY, ComponentMetric.EMBEDDING_QUALITY],
    "retriever": [ComponentMetric.RECALL, ComponentMetric.PRECISION],
    "generator": [ComponentMetric.RESPONSE_QUALITY, ComponentMetric.LATENCY]
}

# Avaliar um pipeline
result = pipeline_evaluator.evaluate(
    pipeline="rag_pipeline",
    test_cases="rag_test_cases.json",
    pipeline_metrics=pipeline_metrics,
    component_metrics=component_metrics,
    iterations=100
)

# Acessar resultados do pipeline
print(f"End-to-end latency: {result.get_pipeline_metric('end_to_end_latency')} ms")
print(f"Throughput: {result.get_pipeline_metric('throughput')} requests/sec")
print(f"Success rate: {result.get_pipeline_metric('success_rate')}%")

# Acessar resultados de componentes
for component in result.components:
    print(f"\nComponent: {component}")
    for metric in result.get_component_metrics(component):
        print(f"  {metric.name}: {metric.value} {metric.unit}")
```

### Métricas Personalizadas

```python
from pepperpy.evaluation import (
    CustomMetric,
    MetricRegistry,
    EvaluationContext
)

# Definir uma métrica personalizada
class FactualConsistencyMetric(CustomMetric):
    def __init__(self):
        super().__init__(
            id="factual_consistency",
            name="Factual Consistency",
            description="Measures the factual consistency of a response with a reference",
            min_value=0.0,
            max_value=1.0
        )
    
    def compute(self, response: str, reference: str, context: EvaluationContext = None) -> float:
        # Implementação simplificada
        # Em um caso real, usaria um modelo para verificar consistência factual
        reference_facts = set(reference.split("."))
        response_facts = set(response.split("."))
        
        if not reference_facts:
            return 1.0
        
        consistent_facts = 0
        for fact in response_facts:
            if any(self._is_consistent(fact, ref_fact) for ref_fact in reference_facts):
                consistent_facts += 1
        
        return consistent_facts / len(response_facts) if response_facts else 0.0
    
    def _is_consistent(self, fact1: str, fact2: str) -> bool:
        # Implementação simplificada de verificação de consistência
        common_words = set(fact1.lower().split()) & set(fact2.lower().split())
        return len(common_words) >= 2  # Pelo menos duas palavras em comum

# Registrar a métrica personalizada
registry = MetricRegistry.get_instance()
registry.register(FactualConsistencyMetric())

# Usar a métrica personalizada
evaluator = ResponseEvaluator()
evaluation = evaluator.evaluate(
    question="Quais são os principais componentes do RAG no PepperPy?",
    response="Os principais componentes do RAG no PepperPy são o indexador de documentos, o recuperador semântico e o gerador contextual.",
    reference="O RAG no PepperPy é composto por três componentes principais: indexador de documentos, recuperador semântico e gerador contextual.",
    criteria=[ResponseCriteria.FACTUAL_CONSISTENCY]
)

print(f"Factual consistency: {evaluation.get_score(ResponseCriteria.FACTUAL_CONSISTENCY)}")
```

## Exemplo Completo

```python
from pepperpy.evaluation import ModelEvaluator, EvaluationDataset
from pepperpy.evaluation.llm import ResponseEvaluator, ResponseCriteria
from pepperpy.llm import ChatSession, ChatOptions
import pandas as pd
import matplotlib.pyplot as plt

# Função para avaliar diferentes modelos de LLM em um conjunto de perguntas
def evaluate_llm_models(models, questions_file, reference_file):
    # Carregar perguntas e respostas de referência
    questions_df = pd.read_csv(questions_file)
    references_df = pd.read_csv(reference_file)
    
    # Criar avaliadores
    model_evaluator = ModelEvaluator()
    response_evaluator = ResponseEvaluator()
    
    # Critérios de avaliação
    criteria = [
        ResponseCriteria.RELEVANCE,
        ResponseCriteria.ACCURACY,
        ResponseCriteria.COMPLETENESS,
        ResponseCriteria.COHERENCE,
        ResponseCriteria.HELPFULNESS
    ]
    
    # Resultados por modelo
    results = {}
    
    # Avaliar cada modelo
    for model_name in models:
        print(f"\nEvaluating model: {model_name}")
        
        # Configurar sessão de chat
        session = ChatSession(
            provider="openai" if "gpt" in model_name else "anthropic",
            options=ChatOptions(
                model=model_name,
                temperature=0.0  # Usar temperatura 0 para respostas determinísticas
            )
        )
        
        # Resultados para este modelo
        model_results = {
            "overall_score": 0.0,
            "criteria_scores": {criterion.name.lower(): 0.0 for criterion in criteria},
            "questions": []
        }
        
        # Processar cada pergunta
        for i, row in questions_df.iterrows():
            question = row["question"]
            category = row["category"]
            reference = references_df[references_df["question_id"] == row["id"]]["reference"].iloc[0]
            
            print(f"  Processing question {i+1}/{len(questions_df)}: {question[:50]}...")
            
            # Gerar resposta
            session.add_system_message("You are a helpful assistant that provides accurate and concise information.")
            session.add_user_message(question)
            response = session.generate()
            
            # Avaliar resposta
            evaluation = response_evaluator.evaluate(
                question=question,
                response=response.content,
                reference=reference,
                criteria=criteria
            )
            
            # Armazenar resultados
            question_result = {
                "question": question,
                "category": category,
                "response": response.content,
                "reference": reference,
                "overall_score": evaluation.overall_score,
                "criteria_scores": {criterion.name.lower(): evaluation.get_score(criterion) for criterion in criteria}
            }
            
            model_results["questions"].append(question_result)
            model_results["overall_score"] += evaluation.overall_score
            
            for criterion in criteria:
                model_results["criteria_scores"][criterion.name.lower()] += evaluation.get_score(criterion)
        
        # Calcular médias
        num_questions = len(questions_df)
        model_results["overall_score"] /= num_questions
        
        for criterion in criteria:
            model_results["criteria_scores"][criterion.name.lower()] /= num_questions
        
        # Armazenar resultados do modelo
        results[model_name] = model_results
        
        print(f"  Average score: {model_results['overall_score']:.2f}/5")
    
    # Gerar visualizações comparativas
    plot_model_comparison(results)
    
    return results

# Função para plotar comparação de modelos
def plot_model_comparison(results):
    models = list(results.keys())
    overall_scores = [results[model]["overall_score"] for model in models]
    
    # Plotar pontuações gerais
    plt.figure(figsize=(10, 6))
    plt.bar(models, overall_scores)
    plt.ylim(0, 5)
    plt.title("Overall Model Performance")
    plt.xlabel("Model")
    plt.ylabel("Average Score (0-5)")
    plt.savefig("model_comparison_overall.png")
    
    # Plotar pontuações por critério
    criteria = list(results[models[0]]["criteria_scores"].keys())
    
    plt.figure(figsize=(12, 8))
    x = range(len(models))
    width = 0.15
    offsets = [i * width for i in range(len(criteria))]
    
    for i, criterion in enumerate(criteria):
        scores = [results[model]["criteria_scores"][criterion] for model in models]
        plt.bar([pos + offsets[i] for pos in x], scores, width=width, label=criterion.capitalize())
    
    plt.ylim(0, 5)
    plt.title("Model Performance by Criteria")
    plt.xlabel("Model")
    plt.ylabel("Average Score (0-5)")
    plt.xticks([pos + width * 2 for pos in x], models)
    plt.legend()
    plt.savefig("model_comparison_criteria.png")

# Exemplo de uso
models_to_evaluate = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]
results = evaluate_llm_models(
    models=models_to_evaluate,
    questions_file="evaluation_questions.csv",
    reference_file="evaluation_references.csv"
)

# Imprimir resultados resumidos
print("\nEvaluation Summary:")
for model, result in results.items():
    print(f"\n{model}:")
    print(f"  Overall Score: {result['overall_score']:.2f}/5")
    print("  Criteria Scores:")
    for criterion, score in result["criteria_scores"].items():
        print(f"    - {criterion.capitalize()}: {score:.2f}/5")
```

## Configuração Avançada

```python
from pepperpy.evaluation import ModelEvaluator
from pepperpy.evaluation.config import EvaluationConfig

# Configuração avançada para avaliação
config = EvaluationConfig(
    metrics=[
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "latency",
        "memory_usage",
        "factual_consistency"
    ],
    weights={
        "accuracy": 0.3,
        "precision": 0.15,
        "recall": 0.15,
        "f1_score": 0.2,
        "latency": 0.1,
        "memory_usage": 0.05,
        "factual_consistency": 0.05
    },
    thresholds={
        "accuracy": 0.8,
        "precision": 0.75,
        "recall": 0.75,
        "f1_score": 0.8,
        "latency": 500,  # ms
        "memory_usage": 1024,  # MB
        "factual_consistency": 0.9
    },
    num_iterations=5,
    confidence_level=0.95,
    report_format="html",
    save_responses=True,
    cache_results=True,
    parallel_evaluation=True,
    max_workers=4
)

# Criar avaliador com configuração personalizada
evaluator = ModelEvaluator(config=config)

# Avaliar modelo com configuração avançada
result = evaluator.evaluate(
    model="gpt-4",
    dataset="test_data.csv",
    task="question_answering"
)
```

## Melhores Práticas

1. **Use Conjuntos de Dados Representativos**: Certifique-se de que seus conjuntos de dados de avaliação representam casos de uso reais.

2. **Defina Métricas Claras**: Escolha métricas que sejam relevantes para seu caso de uso e defina claramente como elas são calculadas.

3. **Compare Múltiplos Modelos**: Avalie vários modelos ou configurações para identificar a melhor opção para seu caso de uso.

4. **Considere Múltiplos Aspectos**: Avalie não apenas a qualidade das respostas, mas também desempenho, latência e uso de recursos.

5. **Automatize Avaliações**: Implemente avaliações automatizadas como parte de seu pipeline de desenvolvimento para monitorar o desempenho ao longo do tempo. 