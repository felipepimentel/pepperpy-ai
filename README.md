# PepperPy

Um framework moderno e flexível para aplicações de IA em Python.

## Visão Geral

PepperPy é um framework Python projetado para simplificar o desenvolvimento de aplicações de IA, oferecendo uma API intuitiva e flexível que permite aos desenvolvedores criar soluções poderosas com poucas linhas de código.

## Características Principais

- **Composição Universal**: API de baixo nível para compor componentes em pipelines
- **Abstração por Intenção**: API de médio nível para expressar intenções de forma natural
- **Templates**: API de alto nível com soluções pré-configuradas
- **Extensibilidade**: Fácil integração com bibliotecas e serviços existentes
- **Observabilidade**: Suporte integrado para logging, métricas e rastreamento

## Instalação

```bash
pip install pepperpy
```

## Exemplos de Uso

### Composição Universal

```python
from pepperpy import compose, compose_parallel

# Gerar um podcast a partir de um feed RSS (pipeline sequencial)
podcast_path = await (
    compose("podcast_pipeline")
    .source(RSSFeedSource({"url": "https://news.google.com/rss", "max_items": 5}))
    .process(SummarizationProcessor({"max_length": 150}))
    .output(PodcastOutputComponent({"voice": "en", "output_path": "news_podcast.mp3"}))
    .execute()
)

# Processamento paralelo para análise de dados (pipeline paralelo)
results = await (
    compose_parallel("data_analysis_pipeline")
    .source(WebAPISource({"endpoint": "https://api.example.com/data"}))
    .process(DataEnricherProcessor({"enrichment_type": "sentiment"}))
    .process(DataEnricherProcessor({"enrichment_type": "entities"}))
    .output(AnalysisOutputComponent({"format": "json"}))
    .execute()
)
```

### Abstração por Intenção

```python
from pepperpy import recognize_intent, process_intent

# Reconhecer e processar uma intenção do usuário
text = "gere um podcast com as últimas notícias sobre tecnologia"
intent = await recognize_intent(text)
result = await process_intent(intent)
```

### Templates

```python
from pepperpy import execute_template

# Gerar um podcast a partir de um feed RSS usando um template
podcast_path = await execute_template(
    "news_podcast",
    {
        "source_url": "https://news.google.com/rss",
        "output_path": "news_podcast.mp3",
        "voice": "en",
        "max_articles": 5,
        "summary_length": 150,
    }
)
```

## Arquitetura

PepperPy é organizado em domínios verticais e camadas horizontais:

### Domínios Verticais

- **LLM**: Integração com modelos de linguagem
- **Embedding**: Geração e manipulação de embeddings
- **RAG**: Retrieval Augmented Generation
- **Multimodal**: Processamento de áudio, imagem e vídeo
- **Agents**: Agentes autônomos e assistentes
- **Workflows**: Orquestração de fluxos de trabalho

### Camadas Horizontais

- **Composição Universal**: API de baixo nível para compor componentes
- **Abstração por Intenção**: API de médio nível para expressar intenções
- **Templates**: API de alto nível com soluções pré-configuradas

## Fronteiras de Responsabilidade e Integração entre Sistemas

O PepperPy oferece três níveis de abstração que se integram de forma coesa para proporcionar uma experiência de desenvolvimento flexível e poderosa. Cada nível tem responsabilidades bem definidas e interfaces claras para integração.

### Quando Usar Cada Nível de Abstração

1. **Composição Universal (Baixo Nível)**
   - **Quando usar**: Para casos que exigem controle granular sobre o fluxo de dados e processamento
   - **Casos de uso**: Pipelines personalizados, integração com componentes externos, processamento de dados complexo
   - **Vantagens**: Máxima flexibilidade, controle total sobre o comportamento
   - **Desvantagens**: Requer mais código, conhecimento detalhado dos componentes

2. **Abstração por Intenção (Médio Nível)**
   - **Quando usar**: Para aplicações que precisam interpretar comandos em linguagem natural
   - **Casos de uso**: Chatbots, assistentes virtuais, interfaces conversacionais
   - **Vantagens**: Interface natural, mapeamento automático para funcionalidades
   - **Desvantagens**: Menos controle sobre o processamento específico

3. **Templates (Alto Nível)**
   - **Quando usar**: Para implementar rapidamente padrões comuns e casos de uso estabelecidos
   - **Casos de uso**: Geração de podcasts, resumos, análise de dados, tradução
   - **Vantagens**: Implementação rápida, configuração mínima, boas práticas incorporadas
   - **Desvantagens**: Menos flexibilidade para casos muito específicos

### Fluxo de Dados entre os Sistemas

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Templates    │◄────┤    Intenção     │◄────┤   Composição    │
│   (Alto Nível)  │     │  (Médio Nível)  │     │  (Baixo Nível)  │
│                 │     │                 │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Configuração   │     │ Reconhecimento  │     │   Componentes   │
│  Pré-definida   │     │   de Intenção   │     │    Básicos      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Composição → Intenção**: Os manipuladores de intenção usam pipelines de composição para implementar o processamento específico para cada intenção reconhecida.

2. **Intenção → Templates**: Os manipuladores de intenção podem executar templates para casos de uso comuns, simplificando a implementação.

3. **Templates → Composição**: Os templates são implementados usando pipelines de composição, encapsulando padrões comuns em interfaces de alto nível.

### Exemplos de Integração

Veja a pasta `examples/integration/` para exemplos completos de integração entre os sistemas:

- `intent_to_composition_example.py`: Demonstra como o sistema de intenção usa o sistema de composição
- `template_to_intent_example.py`: Demonstra como o sistema de templates se integra com o sistema de intenção
- `complete_flow_example.py`: Demonstra o fluxo completo de integração entre os três sistemas

### Sistema de Composição

O sistema de composição é o núcleo do PepperPy, permitindo a criação de pipelines flexíveis e reutilizáveis. Ele é baseado em três tipos de componentes:

1. **Componentes de Fonte (Source)**: Responsáveis por obter dados de fontes externas
   - Implementam a interface `SourceComponent[T]`
   - Método principal: `fetch() -> T`
   - Exemplos: `RSSFeedSource`, `WebAPISource`, `FileSource`

2. **Componentes de Processamento (Processor)**: Transformam ou enriquecem os dados
   - Implementam a interface `ProcessorComponent[T, U]`
   - Método principal: `transform(data: T) -> U`
   - Exemplos: `SummarizationProcessor`, `TranslationProcessor`, `EnrichmentProcessor`

3. **Componentes de Saída (Output)**: Formatam e enviam os dados processados
   - Implementam a interface `OutputComponent[T]`
   - Método principal: `output(data: T) -> Any`
   - Exemplos: `PodcastOutputComponent`, `FileOutputComponent`, `APIOutputComponent`

O sistema de composição oferece duas abordagens principais:

- **Pipelines Sequenciais**: Executam componentes em sequência
  ```python
  result = await (
      compose("sequential_pipeline")
      .source(source_component)
      .process(processor_component)
      .output(output_component)
      .execute()
  )
  ```

- **Pipelines Paralelos**: Executam componentes em paralelo para melhor desempenho
  ```python
  result = await (
      compose_parallel("parallel_pipeline")
      .source(source_component)
      .process(processor1)
      .process(processor2)  # Executado em paralelo com processor1
      .output(output_component)
      .execute()
  )
  ```

### Extensão do Sistema de Composição

Para criar novos componentes, basta implementar as interfaces apropriadas:

```python
from pepperpy.core.composition.base import SourceComponentBase
from typing import Dict, List

class CustomSource(SourceComponentBase[List[Dict[str, str]]]):
    """Componente de fonte personalizado."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url")
        self.max_items = config.get("max_items", 10)

    async def fetch(self) -> List[Dict[str, str]]:
        """Busca dados da fonte."""
        # Implementação específica
        return [{"title": "Item 1", "content": "Conteúdo 1"}, ...]
```

## Exemplos

Veja a pasta `examples/` para exemplos completos de uso do PepperPy:

- `composition/`: Exemplos de uso da API de composição universal
- `intent/`: Exemplos de reconhecimento e processamento de intenções
- `workflows/`: Exemplos de definição e execução de workflows
- `content_processing/`: Exemplos de processamento de conteúdo
- `conversational/`: Exemplos de agentes conversacionais
- `integration/`: Exemplos de integração entre os diferentes sistemas

## Contribuição

Contribuições são bem-vindas! Por favor, leia o arquivo `CONTRIBUTING.md` para mais informações.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo `LICENSE` para mais detalhes. 