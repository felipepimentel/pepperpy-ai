# News Podcast Generator

Este exemplo demonstra como criar um gerador de podcast de notícias usando a biblioteca PepperPy.

## Funcionalidades

O exemplo:

1. Busca artigos de notícias de um feed RSS
2. Resume os artigos usando um modelo de linguagem (LLM)
3. Converte os resumos em áudio usando síntese de voz
4. Combina os arquivos de áudio em um podcast

## Arquitetura

Este exemplo utiliza a arquitetura de agentes da biblioteca PepperPy para criar um fluxo de trabalho completo:

- `NewsFetcherAgent`: Agente responsável por buscar artigos de notícias de um feed RSS
- `NewsSummarizerAgent`: Agente que utiliza LLM para resumir os artigos
- `PodcastGeneratorAgent`: Agente que converte os resumos em áudio e gera o podcast final

Cada agente implementa a interface `BaseAgent` da biblioteca PepperPy, aproveitando o ciclo de vida e a gestão de estado fornecidos pela biblioteca.

## Como Usar

Para executar o exemplo, use o seguinte comando:

```bash
poetry run python -m examples.news_podcast.news_podcast --feed <feed_url> --output <output_file>
```

Parâmetros disponíveis:

- `--feed`: URL do feed RSS (obrigatório)
- `--output`: Caminho para salvar o podcast (obrigatório)
- `--max-articles`: Número máximo de artigos a incluir (padrão: 5)
- `--llm-provider`: Nome do provedor de LLM (padrão: openai)
- `--llm-model`: Nome do modelo a ser usado (padrão: gpt-3.5-turbo)
- `--voice`: Nome da voz a ser usada (padrão: en-US-Neural2-F)

## Exemplo de Uso

```bash
poetry run python -m examples.news_podcast.news_podcast --feed https://news.google.com/rss --output podcast.mp3 --max-articles 3
```

Este comando irá:
1. Buscar os 3 artigos mais recentes do feed de notícias do Google
2. Gerar resumos para cada artigo usando o modelo gpt-3.5-turbo
3. Converter os resumos em áudio usando a voz en-US-Neural2-F
4. Combinar os arquivos de áudio em um podcast chamado `podcast.mp3`

## Requisitos

Para executar este exemplo, você precisará:

- Python 3.10+
- Poetry
- API keys para:
  - OpenAI (ou outro provedor de LLM)
  - Google Cloud (para Text-to-Speech)

## Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto com suas chaves de API:

```
OPENAI_API_KEY=sua_chave_api_openai
GOOGLE_APPLICATION_CREDENTIALS=caminho/para/suas/credenciais-google.json
``` 