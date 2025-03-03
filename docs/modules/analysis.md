# Módulo Analysis

O módulo `analysis` fornece ferramentas para analisar dados e conteúdo, extrair informações e gerar insights.

## Visão Geral

O módulo Analysis permite:

- Analisar texto e extrair entidades, sentimentos e tópicos
- Processar dados estruturados e não estruturados
- Gerar estatísticas e métricas
- Visualizar resultados de análise
- Comparar e avaliar diferentes modelos e abordagens

## Principais Componentes

### Análise de Texto

Ferramentas para análise de conteúdo textual:

```python
from pepperpy.analysis.text import (
    TextAnalyzer,
    EntityExtractor,
    SentimentAnalyzer,
    TopicExtractor,
    KeywordExtractor
)

# Analisador de texto básico
text_analyzer = TextAnalyzer()
analysis = text_analyzer.analyze(
    "O PepperPy é um framework Python para construir aplicações de IA.",
    features=["entities", "sentiment", "keywords"]
)
print(f"Entities: {analysis.entities}")
print(f"Sentiment: {analysis.sentiment}")
print(f"Keywords: {analysis.keywords}")

# Extração de entidades
entity_extractor = EntityExtractor(model="spacy")
entities = entity_extractor.extract(
    "A Microsoft anunciou uma parceria com a OpenAI para desenvolver novos produtos baseados em GPT-4."
)
for entity in entities:
    print(f"Entity: {entity.text}, Type: {entity.type}, Confidence: {entity.confidence}")

# Análise de sentimento
sentiment_analyzer = SentimentAnalyzer(provider="openai")
sentiment = sentiment_analyzer.analyze(
    "Estou muito satisfeito com os resultados obtidos usando o PepperPy!"
)
print(f"Sentiment: {sentiment.label}, Score: {sentiment.score}")

# Extração de tópicos
topic_extractor = TopicExtractor()
topics = topic_extractor.extract([
    "O Python é uma linguagem de programação versátil.",
    "JavaScript é usado principalmente para desenvolvimento web.",
    "O TensorFlow é uma biblioteca popular para machine learning."
])
for topic in topics:
    print(f"Topic: {topic.name}, Keywords: {topic.keywords}")

# Extração de palavras-chave
keyword_extractor = KeywordExtractor()
keywords = keyword_extractor.extract(
    "A inteligência artificial está transformando diversos setores da economia global."
)
for keyword in keywords:
    print(f"Keyword: {keyword.text}, Relevance: {keyword.relevance}")
```

### Análise de Dados

Ferramentas para análise de dados estruturados:

```python
from pepperpy.analysis.data import (
    DataAnalyzer,
    StatisticalAnalyzer,
    CorrelationAnalyzer,
    AnomalyDetector
)
import pandas as pd

# Carregar dados
data = pd.read_csv("sales_data.csv")

# Analisador de dados básico
data_analyzer = DataAnalyzer()
summary = data_analyzer.analyze(data)
print(f"Shape: {summary.shape}")
print(f"Missing values: {summary.missing_values}")
print(f"Data types: {summary.dtypes}")

# Análise estatística
stat_analyzer = StatisticalAnalyzer()
stats = stat_analyzer.analyze(data["sales"])
print(f"Mean: {stats.mean}")
print(f"Median: {stats.median}")
print(f"Std Dev: {stats.std}")
print(f"Quantiles: {stats.quantiles}")

# Análise de correlação
corr_analyzer = CorrelationAnalyzer()
correlations = corr_analyzer.analyze(
    data, 
    columns=["sales", "marketing_spend", "customer_count"]
)
print(f"Correlation matrix:\n{correlations.matrix}")
print(f"Strongest correlation: {correlations.strongest}")

# Detecção de anomalias
anomaly_detector = AnomalyDetector(method="isolation_forest")
anomalies = anomaly_detector.detect(data["sales"])
print(f"Anomalies detected: {len(anomalies)}")
for i, anomaly in enumerate(anomalies[:5]):
    print(f"Anomaly {i+1}: Index {anomaly.index}, Value {anomaly.value}, Score {anomaly.score}")
```

### Visualização

Ferramentas para visualizar resultados de análise:

```python
from pepperpy.analysis.visualization import (
    DataVisualizer,
    TextVisualizer,
    ChartGenerator
)

# Visualizador de dados
data_visualizer = DataVisualizer()

# Gerar visualizações básicas
data_visualizer.histogram(data["sales"], title="Sales Distribution")
data_visualizer.boxplot(data[["sales", "marketing_spend"]], title="Sales and Marketing")
data_visualizer.scatter(data, x="marketing_spend", y="sales", title="Marketing vs Sales")

# Visualizador de texto
text_visualizer = TextVisualizer()

# Visualizar análise de texto
text_visualizer.word_cloud(
    "O PepperPy é um framework Python para construir aplicações de IA com recursos avançados de processamento de linguagem natural e aprendizado de máquina.",
    title="PepperPy Description"
)

text_visualizer.entity_highlights(
    "A Microsoft anunciou uma parceria com a OpenAI para desenvolver novos produtos baseados em GPT-4.",
    entities=entities
)

# Gerador de gráficos
chart_generator = ChartGenerator(format="plotly")

# Gerar gráficos interativos
chart = chart_generator.line_chart(
    data, 
    x="date", 
    y="sales", 
    title="Sales Over Time",
    color="region"
)
chart.show()

dashboard = chart_generator.create_dashboard([
    {"type": "line", "data": data, "x": "date", "y": "sales", "title": "Sales Trend"},
    {"type": "bar", "data": data, "x": "region", "y": "sales", "title": "Sales by Region"},
    {"type": "pie", "data": data, "names": "product", "values": "sales", "title": "Sales by Product"}
])
dashboard.save("sales_dashboard.html")
```

### Comparação e Avaliação

Ferramentas para comparar e avaliar modelos e abordagens:

```python
from pepperpy.analysis.evaluation import (
    ModelEvaluator,
    ModelComparator,
    PerformanceAnalyzer
)

# Avaliar um modelo
evaluator = ModelEvaluator()
evaluation = evaluator.evaluate(
    model="sentiment_analyzer",
    dataset="reviews.csv",
    metrics=["accuracy", "precision", "recall", "f1"]
)
print(f"Evaluation results: {evaluation.metrics}")
print(f"Confusion matrix:\n{evaluation.confusion_matrix}")

# Comparar múltiplos modelos
comparator = ModelComparator()
comparison = comparator.compare(
    models=["model_a", "model_b", "model_c"],
    dataset="test_data.csv",
    metrics=["accuracy", "latency", "memory_usage"]
)
print(f"Comparison results:\n{comparison.summary}")
comparator.plot_comparison(comparison, metric="accuracy")

# Analisar desempenho
performance_analyzer = PerformanceAnalyzer()
performance = performance_analyzer.analyze(
    model="text_classifier",
    inputs=["short_text", "medium_text", "long_text"],
    metrics=["latency", "memory_usage", "accuracy"]
)
print(f"Performance analysis:\n{performance.summary}")
performance_analyzer.plot_performance(performance)
```

## Exemplo Completo

```python
from pepperpy.analysis.text import TextAnalyzer, EntityExtractor, SentimentAnalyzer
from pepperpy.analysis.visualization import TextVisualizer
import pandas as pd

# Função para analisar feedback de usuários
def analyze_user_feedback(feedback_file):
    # Carregar dados
    feedback_data = pd.read_csv(feedback_file)
    
    # Inicializar analisadores
    text_analyzer = TextAnalyzer()
    entity_extractor = EntityExtractor()
    sentiment_analyzer = SentimentAnalyzer()
    visualizer = TextVisualizer()
    
    # Resultados agregados
    results = {
        "total_feedback": len(feedback_data),
        "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
        "top_entities": {},
        "top_keywords": {}
    }
    
    # Processar cada feedback
    for i, row in feedback_data.iterrows():
        feedback_text = row["feedback"]
        
        # Análise básica
        analysis = text_analyzer.analyze(
            feedback_text,
            features=["sentiment", "keywords"]
        )
        
        # Extrair entidades
        entities = entity_extractor.extract(feedback_text)
        
        # Análise de sentimento detalhada
        sentiment = sentiment_analyzer.analyze(feedback_text)
        
        # Atualizar distribuição de sentimento
        results["sentiment_distribution"][sentiment.label] += 1
        
        # Atualizar contagem de entidades
        for entity in entities:
            if entity.type in ["PRODUCT", "FEATURE", "ISSUE"]:
                if entity.text not in results["top_entities"]:
                    results["top_entities"][entity.text] = 0
                results["top_entities"][entity.text] += 1
        
        # Atualizar contagem de palavras-chave
        for keyword in analysis.keywords:
            if keyword.text not in results["top_keywords"]:
                results["top_keywords"][keyword.text] = 0
            results["top_keywords"][keyword.text] += 1
    
    # Ordenar entidades e palavras-chave por frequência
    results["top_entities"] = dict(sorted(
        results["top_entities"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10])
    
    results["top_keywords"] = dict(sorted(
        results["top_keywords"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10])
    
    # Gerar visualizações
    visualizer.sentiment_distribution(
        results["sentiment_distribution"],
        title="Sentiment Distribution in User Feedback"
    )
    
    visualizer.entity_frequency(
        results["top_entities"],
        title="Top Mentioned Entities in Feedback"
    )
    
    visualizer.word_cloud(
        " ".join(feedback_data["feedback"]),
        title="User Feedback Word Cloud"
    )
    
    return results

# Exemplo de uso
feedback_analysis = analyze_user_feedback("user_feedback.csv")
print("Feedback Analysis Results:")
print(f"Total feedback: {feedback_analysis['total_feedback']}")
print(f"Sentiment distribution: {feedback_analysis['sentiment_distribution']}")
print("Top mentioned entities:")
for entity, count in feedback_analysis["top_entities"].items():
    print(f"  - {entity}: {count}")
print("Top keywords:")
for keyword, count in feedback_analysis["top_keywords"].items():
    print(f"  - {keyword}: {count}")
```

## Configuração Avançada

```python
from pepperpy.analysis.text import TextAnalyzer
from pepperpy.analysis.config import TextAnalysisConfig

# Configuração avançada para análise de texto
config = TextAnalysisConfig(
    language="pt-br",
    models={
        "entities": "spacy_lg",
        "sentiment": "openai",
        "keywords": "custom_model"
    },
    entity_types=["PERSON", "ORG", "PRODUCT", "FEATURE"],
    sentiment_labels=["VERY_NEGATIVE", "NEGATIVE", "NEUTRAL", "POSITIVE", "VERY_POSITIVE"],
    min_keyword_relevance=0.3,
    max_keywords=15,
    custom_stopwords=["exemplo", "etc", "coisa"],
    cache_results=True,
    batch_size=32
)

# Criar analisador com configuração personalizada
analyzer = TextAnalyzer(config=config)

# Analisar texto com configuração avançada
analysis = analyzer.analyze(
    "O novo recurso de análise de texto do PepperPy é extremamente útil para processar grandes volumes de feedback de usuários.",
    features=["entities", "sentiment", "keywords", "topics"]
)
```

## Melhores Práticas

1. **Pré-processe os Dados**: Limpe e normalize os dados antes da análise para obter resultados mais precisos.

2. **Combine Múltiplas Análises**: Utilize diferentes tipos de análise para obter insights mais completos.

3. **Visualize os Resultados**: Use visualizações para comunicar os resultados de forma mais eficaz.

4. **Avalie a Qualidade**: Valide os resultados da análise com métricas de qualidade e comparações.

5. **Otimize para Escala**: Para grandes volumes de dados, utilize processamento em lote e cache para melhorar o desempenho. 