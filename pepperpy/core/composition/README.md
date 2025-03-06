# Arquitetura de Composição Universal

A arquitetura de composição universal do PepperPy permite a criação de pipelines de processamento flexíveis e reutilizáveis, combinando componentes de diferentes domínios.

## Visão Geral

A arquitetura de composição é baseada em três tipos principais de componentes:

1. **Fontes (Sources)**: Componentes que fornecem dados para o pipeline.
2. **Processadores (Processors)**: Componentes que transformam os dados.
3. **Saídas (Outputs)**: Componentes que escrevem os dados processados em algum destino.

Esses componentes são combinados em pipelines que podem ser executados para processar dados de forma sequencial ou paralela.

## Estrutura do Módulo

O módulo de composição está organizado da seguinte forma:

- `__init__.py`: Exporta a API pública do módulo.
- `public.py`: Define a API pública para criação de pipelines.
- `factory.py`: Implementa fábricas para criação de componentes e pipelines.
- `registry.py`: Gerencia o registro de componentes disponíveis.
- `implementation.py`: Implementa os tipos de pipeline (standard e parallel).

## Uso Básico

### Pipeline Sequencial

```python
from pepperpy.core.composition import compose, Sources, Processors, Outputs

# Criar um pipeline para gerar um podcast a partir de um feed RSS
pipeline = (
    compose("podcast_pipeline")
    .source(Sources.rss("https://news.google.com/rss", max_items=3))
    .process(Processors.summarize(max_length=150))
    .output(Outputs.podcast("podcast.mp3", voice="pt"))
)

# Executar o pipeline
podcast_path = await pipeline.execute()
```

### Pipeline Paralelo

```python
from pepperpy.core.composition import compose_parallel, Sources, Processors, Outputs

# Criar um pipeline paralelo para processar um feed RSS
pipeline = (
    compose_parallel("parallel_rss_pipeline")
    .source(Sources.rss("https://news.google.com/rss", max_items=3))
    .process(Processors.summarize(max_length=150))
    .process(Processors.extract_keywords(max_keywords=5))
    .output(Outputs.file("result.txt"))
)

# Executar o pipeline
result_path = await pipeline.execute()
```

## Extensibilidade

A arquitetura de composição é extensível, permitindo a adição de novos tipos de componentes:

1. **Adicionar uma nova fonte**:
   - Implemente uma classe que herda de `SourceComponent`.
   - Registre a fonte usando `register_source_component`.

2. **Adicionar um novo processador**:
   - Implemente uma classe que herda de `ProcessorComponent`.
   - Registre o processador usando `register_processor_component`.

3. **Adicionar uma nova saída**:
   - Implemente uma classe que herda de `OutputComponent`.
   - Registre a saída usando `register_output_component`.

## Benefícios

- **Flexibilidade**: Combine componentes de diferentes domínios em um único pipeline.
- **Reutilização**: Use os mesmos componentes em diferentes pipelines.
- **Extensibilidade**: Adicione novos componentes sem modificar o código existente.
- **Paralelismo**: Execute processadores em paralelo para melhorar o desempenho.
- **Simplicidade**: API fluente e intuitiva para criação de pipelines.

## Exemplo Completo

Veja o arquivo `examples/composition_example.py` para um exemplo completo de uso da arquitetura de composição. 