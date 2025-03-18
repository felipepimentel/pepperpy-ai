# Framework de Pipeline do PepperPy

Este módulo implementa um framework de pipeline flexível e extensível para orquestrar sequências de operações no PepperPy.

## Visão Geral

O framework de pipeline permite criar fluxos de processamento modulares, onde a saída de cada estágio serve como entrada para o próximo. Este padrão é ideal para:

- Transformações de dados
- Fluxos de processamento RAG (Retrieval Augmented Generation)
- Composição de componentes
- Workflows complexos

## Componentes Principais

### Pipeline

A classe `Pipeline` é o contêiner principal que gerencia uma sequência de estágios. Ela oferece métodos para:

- Adicionar estágios
- Executar o pipeline com dados de entrada
- Configurar o comportamento do pipeline

### PipelineStage

`PipelineStage` é a classe base para todos os estágios de um pipeline. Estágios implementam o método `process` que:

- Recebe dados de entrada e um contexto de execução
- Executa alguma transformação nos dados
- Retorna os dados processados para o próximo estágio

### PipelineContext

`PipelineContext` armazena estado e metadados durante a execução do pipeline, permitindo:

- Compartilhar informações entre estágios
- Rastrear o progresso da execução
- Armazenar metadados sobre a execução

### PipelineRegistry

O `PipelineRegistry` permite registrar pipelines globalmente para uso posterior, facilitando:

- Centralização da configuração de pipelines
- Recuperação de pipelines por nome
- Execução de pipelines registrados

## Estágios Predefinidos

O framework inclui vários estágios comuns prontos para uso:

### FunctionStage

Aplica uma função aos dados de entrada:

```python
uppercase_stage = FunctionStage(
    name="uppercase",
    func=lambda x, context: x.upper()
)
```

### TransformStage

Usa um objeto transformador para processar os dados:

```python
class TextNormalizer:
    def transform(self, text):
        return text.strip().lower()

normalize_stage = TransformStage(
    name="normalize",
    transform=TextNormalizer()
)
```

### ConditionalStage

Executa diferentes estágios com base em uma condição:

```python
conditional_stage = ConditionalStage(
    name="length_check",
    condition=lambda x, ctx: len(x) > 100,
    if_true=summarize_stage,
    if_false=pass_through_stage
)
```

### BranchingStage

Processa os mesmos dados de entrada de várias maneiras em paralelo:

```python
branching_stage = BranchingStage(
    name="text_analysis",
    branches={
        "sentiment": sentiment_stage,
        "keywords": keyword_extraction_stage,
        "entities": entity_recognition_stage
    }
)
```

## Exemplo de Uso

Criando e executando um pipeline simples de processamento de texto:

```python
from pepperpy.core.pipeline.base import Pipeline, PipelineContext
from pepperpy.core.pipeline.stages import FunctionStage

# Criar estágios
clean_stage = FunctionStage(
    name="clean",
    func=lambda x, _: x.strip().lower()
)

tokenize_stage = FunctionStage(
    name="tokenize",
    func=lambda x, _: x.split()
)

count_stage = FunctionStage(
    name="count",
    func=lambda x, _: len(x)
)

# Criar pipeline
pipeline = Pipeline(
    name="text_processor",
    stages=[clean_stage, tokenize_stage, count_stage]
)

# Executar pipeline
context = PipelineContext()
result = pipeline.execute("  Hello World!  ", context)
print(f"Número de palavras: {result}")  # Saída: Número de palavras: 2
```

## Boas Práticas

1. **Nomeie claramente os estágios**: Use nomes descritivos para facilitar a depuração.
2. **Mantenha estágios simples e focados**: Cada estágio deve fazer apenas uma coisa.
3. **Use o contexto para compartilhar estado**: Evite variáveis globais.
4. **Trate erros nos estágios**: Garanta que os estágios lidem adequadamente com entradas inesperadas.
5. **Documente os tipos de entrada/saída**: Especifique claramente o que cada estágio espera e produz.

## Extensibilidade

O framework é projetado para ser facilmente extensível:

- Crie estágios personalizados herdando de `PipelineStage`
- Implemente lógica de execução personalizada estendendo `Pipeline`
- Adicione funcionalidades de rastreamento ou validação através do `PipelineContext`

---

Para mais informações, consulte os exemplos no módulo `pepperpy.core.pipeline.examples` e os testes no diretório `tests/core/pipeline/`. 