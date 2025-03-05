#!/usr/bin/env python3
"""News Podcast Generator

Este exemplo demonstra como criar um gerador de podcast de notícias.

Funcionalidades:
1. Busca artigos de notícias de um feed RSS
2. Resume os artigos usando um modelo de linguagem (OpenAI)
3. Converte os resumos em áudio usando síntese de voz (gTTS)
4. Combina os arquivos de áudio em um podcast

Como usar:
Para executar o exemplo, use o seguinte comando:
```bash
python -m examples.news_podcast.news_podcast --feed https://news.google.com/rss \
    --output example_output/podcast.mp3 --max-articles 3
```

Parâmetros disponíveis:
- `--feed`: URL do feed RSS (padrão: https://news.google.com/rss)
- `--output`: Caminho para salvar o podcast (padrão: example_output/news_podcast.mp3)
- `--max-articles`: Número máximo de artigos a incluir (padrão: 5)
- `--voice`: Nome da voz a ser usada (padrão: en)

Requisitos:
- Python 3.10+
- Bibliotecas: feedparser, openai, gtts, pydub, python-dotenv
- Chaves de API configuradas no arquivo .env:
  - OPENAI_API_KEY ou OPENROUTER_API_KEY para o LLM
  - ELEVENLABS_API_KEY para síntese de voz (opcional, usa gTTS como fallback)
"""

import argparse
import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import feedparser
import requests
from dotenv import load_dotenv
from gtts import gTTS
from openai import AsyncOpenAI
from pydub import AudioSegment

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default values
DEFAULT_FEED_URL = "https://news.google.com/rss"
# Define o caminho para a pasta example_output dentro do diretório do exemplo
EXAMPLE_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLE_DIR / "example_output"
DEFAULT_OUTPUT_PATH = str(OUTPUT_DIR / "news_podcast.mp3")

# Garantir que a pasta example_output exista
OUTPUT_DIR.mkdir(exist_ok=True)
DEFAULT_MAX_ARTICLES = 5
DEFAULT_VOICE_NAME = "en"  # Idioma padrão para gTTS


@dataclass
class NewsArticle:
    """Represents a news article."""

    title: str
    link: str
    summary: str
    published: Optional[datetime] = None


async def fetch_news(
    feed_url: str, max_articles: int = DEFAULT_MAX_ARTICLES
) -> List[NewsArticle]:
    """Fetch news articles from the RSS feed.

    Args:
        feed_url: URL of the RSS feed
        max_articles: Maximum number of articles to fetch

    Returns:
        List of news articles
    """
    logger.info(f"Fetching news from {feed_url}")
    try:
        # Parse the RSS feed
        feed = feedparser.parse(feed_url)

        # Extract articles
        articles = []
        for entry in feed.entries[:max_articles]:
            # Convert struct_time to datetime safely
            published_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    import time

                    published_date = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed)
                    )
                except Exception as e:
                    logger.warning(f"Error converting date: {e}")

            article = NewsArticle(
                title=entry.title,
                link=entry.link,
                summary=entry.get("summary", "No summary available"),
                published=published_date,
            )
            articles.append(article)

        logger.info(f"Fetched {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []


async def summarize_article(article: NewsArticle) -> str:
    """Summarize a news article using OpenAI.

    Args:
        article: News article to summarize

    Returns:
        Summarized article text
    """
    logger.info(f"Summarizing article: {article.title}")

    # Tentar obter a chave da API do OpenRouter primeiro, depois OpenAI
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")

    if not api_key:
        logger.warning("No API key found for OpenAI or OpenRouter")
        return f"Here's a brief news update about {article.title}."

    try:
        # Verificar se estamos usando OpenRouter ou OpenAI diretamente
        if os.environ.get("OPENROUTER_API_KEY"):
            # Usar OpenRouter
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://example.com",  # Necessário para OpenRouter
            }
            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a professional news summarizer. Create a concise "
                            "summary of the news article in a style suitable for a podcast. "
                            "Keep it under 100 words."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Title: {article.title}\n\n"
                            f"Summary: {article.summary}\n\n"
                            f"Link: {article.link}"
                        ),
                    },
                ],
            }

            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                try:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    # Garantir que o conteúdo não seja None
                    return (
                        content
                        if content is not None
                        else f"Here's a brief news update about {article.title}."
                    )
                except (KeyError, json.JSONDecodeError) as e:
                    logger.error(f"Error parsing OpenRouter response: {e}")
                    return f"Here's a brief news update about {article.title}."
            else:
                logger.error(
                    f"OpenRouter API error: {response.status_code} - {response.text}"
                )
                return f"Here's a brief news update about {article.title}."
        else:
            # Usar OpenAI diretamente
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional news summarizer. Create a concise "
                            "summary of the news article in a style suitable for a podcast. "
                            "Keep it under 100 words."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Title: {article.title}\n\n"
                            f"Summary: {article.summary}\n\n"
                            f"Link: {article.link}"
                        ),
                    },
                ],
            )
            content = response.choices[0].message.content
            # Garantir que o conteúdo não seja None
            return (
                content
                if content is not None
                else f"Here's a brief news update about {article.title}."
            )
    except Exception as e:
        logger.error(f"Error summarizing article: {e}")
        return f"Here's a brief news update about {article.title}."


async def text_to_speech_elevenlabs(text: str, output_path: Path) -> bool:
    """Convert text to speech using ElevenLabs API.

    Args:
        text: Text to convert
        output_path: Path to save the audio file

    Returns:
        True if successful, False otherwise
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.warning("No ElevenLabs API key found")
        return False

    try:
        # Usar a voz "Rachel" (ID padrão) ou outra voz configurada
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"ElevenLabs audio saved to {output_path}")
            return True
        else:
            logger.error(
                f"ElevenLabs API error: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Error in ElevenLabs text-to-speech: {e}")
        return False


async def text_to_speech(
    text: str, output_path: Path, voice_name: str = DEFAULT_VOICE_NAME
) -> Path:
    """Convert text to speech using ElevenLabs or gTTS as fallback.

    Args:
        text: Text to convert
        output_path: Path to save the audio file
        voice_name: Voice name or language code

    Returns:
        Path to the generated audio file
    """
    logger.info(f"Converting text to speech: {text[:30]}...")

    # Tentar primeiro com ElevenLabs
    success = await text_to_speech_elevenlabs(text, output_path)

    # Se falhar, usar gTTS como fallback
    if not success:
        try:
            logger.info("Using gTTS as fallback")
            tts = gTTS(text=text, lang=voice_name)
            tts.save(output_path)
            logger.info(f"gTTS audio saved to {output_path}")
        except Exception as e:
            logger.error(f"Error in gTTS: {e}")
            # Criar um arquivo de áudio silencioso como último recurso
            silent = AudioSegment.silent(duration=3000)
            silent.export(output_path, format="mp3")

    return output_path


def combine_audio_files(audio_files: List[Path], output_path: Path) -> Path:
    """Combine audio files into a single podcast.

    Args:
        audio_files: List of audio file paths
        output_path: Path to save the combined audio

    Returns:
        Path to the combined audio file
    """
    logger.info(f"Combining {len(audio_files)} audio files")

    # Create a silent intro
    podcast = AudioSegment.silent(duration=1000)

    # Add each audio file with a short pause between
    for audio_file in audio_files:
        try:
            segment = AudioSegment.from_file(audio_file)
            podcast += segment
            podcast += AudioSegment.silent(duration=1000)  # 1 second pause
        except Exception as e:
            logger.error(f"Error adding audio file {audio_file}: {e}")

    # Garantir que o diretório de saída exista
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export the combined podcast
    podcast.export(output_path, format="mp3")
    logger.info(f"Podcast saved to {output_path}")

    return output_path


async def generate_news_podcast(
    feed_url: str = DEFAULT_FEED_URL,
    output_path: str = DEFAULT_OUTPUT_PATH,
    max_articles: int = DEFAULT_MAX_ARTICLES,
    voice_name: str = DEFAULT_VOICE_NAME,
) -> Optional[Path]:
    """Generate a news podcast.

    Args:
        feed_url: URL of the RSS feed
        output_path: Path to save the podcast
        max_articles: Maximum number of articles to include
        voice_name: Name of the voice to use

    Returns:
        Path to the generated podcast or None if no articles found
    """
    logger.info("Starting news podcast generation")

    # Fetch news articles
    articles = await fetch_news(feed_url, max_articles)

    if not articles:
        logger.error("No articles found")
        return None

    # Create a temporary directory for audio files
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_files = []

        # Process each article
        for i, article in enumerate(articles):
            # Summarize the article
            summary = await summarize_article(article)

            # Convert summary to speech
            audio_path = Path(temp_dir) / f"article_{i}.mp3"
            audio_file = await text_to_speech(summary, audio_path, voice_name)
            audio_files.append(audio_file)

        # Combine audio files into a podcast
        output_file = combine_audio_files(audio_files, Path(output_path))

    logger.info(f"Podcast generation complete: {output_file}")
    return output_file


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate a news podcast")
    parser.add_argument(
        "--feed",
        type=str,
        default=DEFAULT_FEED_URL,
        help="URL of the RSS feed",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to save the podcast (default: example_output/news_podcast.mp3)",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=DEFAULT_MAX_ARTICLES,
        help="Maximum number of articles to include",
    )
    parser.add_argument(
        "--voice",
        type=str,
        default=DEFAULT_VOICE_NAME,
        help="Name of the voice to use (language code for gTTS)",
    )
    return parser.parse_args()


async def main():
    """Run the example."""
    args = parse_args()

    try:
        await generate_news_podcast(
            feed_url=args.feed,
            output_path=args.output,
            max_articles=args.max_articles,
            voice_name=args.voice,
        )
    except Exception as e:
        logger.error(f"Error generating podcast: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
