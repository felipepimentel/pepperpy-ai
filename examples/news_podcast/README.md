# Gerador de Podcast de Notícias

Este exemplo demonstra como criar um gerador de podcast de notícias usando a biblioteca PepperPy.

## Funcionalidades

1. Busca artigos de notícias de um feed RSS usando o processador RSS do PepperPy
2. Resume os artigos usando o módulo LLM do PepperPy
3. Converte os resumos em áudio usando o módulo multimodal do PepperPy
4. Combina os arquivos de áudio em um podcast

## Requisitos

- Python 3.10+
- Biblioteca PepperPy
- Dependências adicionais:
  - pydub (para processamento de áudio)
  - feedparser (para processamento de RSS)
  - gtts (para síntese de voz, usado pelo PepperPy)

## Instalação

1. Certifique-se de que a biblioteca PepperPy está instalada:

```bash
pip install pepperpy
```

2. Instale as dependências adicionais:

```bash
pip install pydub feedparser gtts
```

## Configuração

O exemplo pode ser configurado através de variáveis de ambiente ou argumentos de linha de comando. As seguintes configurações estão disponíveis:

| Configuração | Variável de Ambiente | Descrição | Valor Padrão |
|--------------|----------------------|-----------|--------------|
| URL do Feed | NEWS_PODCAST_FEED_URL | URL do feed RSS | https://news.google.com/rss |
| Caminho de Saída | NEWS_PODCAST_OUTPUT_PATH | Caminho para salvar o podcast | example_output/news_podcast.mp3 |
| Máximo de Artigos | NEWS_PODCAST_MAX_ARTICLES | Número máximo de artigos a incluir | 5 |
| Voz | NEWS_PODCAST_VOICE_NAME | Nome da voz a ser usada (código de idioma para gTTS) | en |
| Chave API OpenAI | OPENAI_API_KEY | Chave de API do OpenAI para resumo de artigos | - |
| Chave API ElevenLabs | ELEVENLABS_API_KEY | Chave de API do ElevenLabs para síntese de voz | - |

## Uso

### Linha de Comando

Para executar o exemplo a partir da linha de comando:

```bash
python -m examples.news_podcast.news_podcast_workflow --feed https://news.google.com/rss --output example_output/podcast.mp3 --max-articles 3 --voice pt
```

### Como Módulo

Para usar o exemplo como um módulo em seu código:

```python
import asyncio
from examples.news_podcast.config import load_config
from examples.news_podcast.news_podcast_workflow import NewsPodcastWorkflow

async def generate_podcast():
    # Carregar configuração com valores personalizados
    config = load_config(
        feed_url="https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        output_path="example_output/nytimes_podcast.mp3",
        max_articles=3,
        voice_name="en",
    )
    
    # Criar e executar o fluxo de trabalho
    workflow = NewsPodcastWorkflow(config)
    podcast_path = await workflow.run()
    
    if podcast_path:
        print(f"Podcast gerado com sucesso: {podcast_path}")
    else:
        print("Falha ao gerar o podcast")

# Executar a função assíncrona
asyncio.run(generate_podcast())
```

## Exemplo Pronto

Um exemplo pronto para uso está disponível em `examples/news_podcast/example.py`:

```bash
python -m examples.news_podcast.example
```

## Estrutura do Código

- `news_podcast_workflow.py`: Implementa o fluxo de trabalho completo
- `config.py`: Gerencia a configuração do gerador de podcast
- `example.py`: Exemplo de uso do gerador de podcast
- `README.md`: Documentação do exemplo

## Personalização

O exemplo pode ser personalizado de várias maneiras:

1. **Feeds RSS**: Altere o feed RSS para obter notícias de diferentes fontes
2. **Idioma**: Altere o código de idioma para gerar podcasts em diferentes idiomas
3. **Número de Artigos**: Ajuste o número máximo de artigos para controlar a duração do podcast
4. **Modelo LLM**: Modifique o modelo usado para resumir os artigos

## Solução de Problemas

### Erros de API

Se você encontrar erros relacionados às APIs, verifique se as chaves de API estão configuradas corretamente:

```bash
export OPENAI_API_KEY=sua_chave_aqui
export ELEVENLABS_API_KEY=sua_chave_aqui
```

### Erros de Dependência

Se você encontrar erros relacionados a dependências ausentes, certifique-se de que todas as dependências estão instaladas:

```bash
pip install -r requirements.txt
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests. 