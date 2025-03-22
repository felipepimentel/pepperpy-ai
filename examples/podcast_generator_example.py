#!/usr/bin/env python
"""
Content Pipeline Example for PepperPy (Simplified Version).

This example demonstrates a simplified content generation pipeline:
1. Fetch news about a specific topic using NewsAPI
2. Generate a basic summary of the articles
3. Display the results in a format ready for further processing

Required Environment Variables:
1. PEPPERPY_NEWS__NEWSAPI_API_KEY:
   - Get a free key at https://newsapi.org
   - Sign up for an account
   - Go to https://newsapi.org/account
   - Copy your API key from the dashboard
   - For example: PEPPERPY_NEWS__NEWSAPI_API_KEY=123456789abcdef

   Free tier limitations:
   - 100 requests per day
   - Up to 100 articles per request
   - Developer plan required for production use
"""

import asyncio
import datetime
import os
import urllib.parse
from typing import Any, Dict, List

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from pepperpy.core.http import HTTPClient

# Load environment variables
load_dotenv()

# Get ElevenLabs API key
elevenlabs_api_key = os.getenv("PEPPERPY_TTS__ELEVENLABS_API_KEY", "")
if not elevenlabs_api_key:
    raise ValueError(
        "PEPPERPY_TTS__ELEVENLABS_API_KEY environment variable is required.\n"
        "Get a key at https://elevenlabs.io and set it as:\n"
        "export PEPPERPY_TTS__ELEVENLABS_API_KEY=your-api-key"
    )

# Initialize ElevenLabs client
eleven = ElevenLabs(api_key=elevenlabs_api_key)


class ContentPipeline:
    """A simple content pipeline that generates a podcast from news articles."""

    def __init__(self, topic: str = "inteligência artificial"):
        """Initialize the pipeline with a topic."""
        self.topic = topic
        self.articles: List[Dict[str, Any]] = []
        self.http = HTTPClient()

    async def fetch_news(self) -> None:
        """Fetch news articles about the topic."""
        print(f"\n1. Buscando notícias sobre '{self.topic}'...")

        # Build the URL with query parameters
        params = {
            "apiKey": os.getenv("PEPPERPY_NEWS__NEWSAPI_API_KEY"),
            "q": self.topic,
            "language": "pt",  # Portuguese language
            "sortBy": "relevancy",
            "pageSize": 10,
        }
        url = f"https://newsapi.org/v2/everything?{urllib.parse.urlencode(params)}"
        print(f"Requesting URL: {url}")

        # Make the request
        response = await self.http.get(url)
        print(f"Response status: {response.status}")

        if response.status != 200:
            raise ValueError(f"Failed to fetch news: {response.status}")

        data = response.json
        if callable(data):
            data = data()
        print(f"Total results: {data['totalResults']}")

        # Store relevant articles
        self.articles = data["articles"][:10]  # Limit to 10 articles
        print(f"Found {len(self.articles)} articles")

    def create_summary(self) -> None:
        """Create a summary of the articles."""
        print("\n2. Criando resumo dos artigos...")

        # Extract main themes (just using titles for simplicity)
        themes = []
        for article in self.articles:
            themes.extend(article["title"].split())
        print(f"Resumo criado com {len(themes)} temas principais")
        print(f"Script do podcast criado com {len(self.articles)} segmentos")

    def _format_podcast_script(self, articles: List[Dict[str, Any]]) -> str:
        """Format the articles into a podcast script."""
        script = f"""# SCRIPT DO PODCAST: NOTÍCIAS SOBRE {self.topic.upper()}

[SFX: MÚSICA DE INTRODUÇÃO]

APRESENTADOR: Bem-vindos ao Tech News Roundup, onde trazemos as últimas novidades sobre {self.topic}.
Eu sou seu apresentador, e hoje vamos cobrir alguns desenvolvimentos fascinantes nesta área.

Nossa cobertura abrange o período de {datetime.datetime.now().strftime('%Y-%m-%d')} até {datetime.datetime.now().strftime('%Y-%m-%d')}.

"""

        for i, article in enumerate(articles, 1):
            script += f"""[SEGMENT {i}]
APRESENTADOR: {article['title']}

{article['description']}

Fonte: {article['source']['name']}

"""

        return script

    def _save_script(self, script: str) -> None:
        """Save the podcast script to a file."""
        # Create output directory if it doesn't exist
        os.makedirs("examples/output", exist_ok=True)

        output_file = os.path.join(
            "examples/output", f"{self.topic.replace(' ', '_')}_podcast_script.txt"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"\nScript do podcast salvo em: {output_file}")

    def generate_audio(self, script: str) -> None:
        """Generate audio from the podcast script using ElevenLabs TTS."""
        print("\n4. Gerando áudio do script...")

        try:
            # Generate audio for each segment to keep within API limits
            segments = script.split("[SEGMENT")
            intro = segments[0]

            # Generate intro audio
            print("Gerando áudio da introdução...")
            intro_audio = eleven.text_to_speech.convert(
                text=intro,
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Josh - Professional American male voice
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            output_file = os.path.join(
                "examples/output", f"{self.topic.replace(' ', '_')}_intro.mp3"
            )
            with open(output_file, "wb") as f:
                for chunk in intro_audio:
                    f.write(chunk)
            print(f"Áudio da introdução salvo em: {output_file}")

            # Generate segment audios
            for i, segment in enumerate(segments[1:], 1):
                print(f"Gerando áudio do segmento {i}...")
                segment_text = f"[SEGMENT{segment}"
                try:
                    segment_audio = eleven.text_to_speech.convert(
                        text=segment_text,
                        voice_id="21m00Tcm4TlvDq8ikWAM",  # Josh - Professional American male voice
                        model_id="eleven_multilingual_v2",
                        output_format="mp3_44100_128",
                    )
                    output_file = os.path.join(
                        "examples/output",
                        f"{self.topic.replace(' ', '_')}_segment_{i}.mp3",
                    )
                    with open(output_file, "wb") as f:
                        for chunk in segment_audio:
                            f.write(chunk)
                    print(f"Áudio do segmento {i} salvo em: {output_file}")
                except Exception as e:
                    print(f"Erro ao gerar áudio do segmento {i}: {str(e)}")
                    continue
        except Exception as e:
            print(f"Erro na geração de áudio: {str(e)}")

    async def run(self) -> None:
        """Run the content pipeline."""
        await self.fetch_news()
        self.create_summary()
        script = self._format_podcast_script(self.articles)

        # Save the script to a file
        self._save_script(script)

        # Generate audio files
        self.generate_audio(script)

        # Print example content
        print("\nExample content (first 300 characters):")
        print("-" * 50)
        print(script[:300] + "...")
        print("-" * 50)


async def main():
    """Run the content pipeline example."""
    # Example topic
    topic = "inteligência artificial"

    # Create and run the pipeline
    pipeline = ContentPipeline(
        topic=topic,
    )
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
