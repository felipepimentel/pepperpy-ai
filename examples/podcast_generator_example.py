#!/usr/bin/env python
"""
Content Pipeline Example for PepperPy (Simplified Version).

This example demonstrates a simplified content generation pipeline:
1. Fetch news about a specific topic using NewsAPI
2. Generate a basic summary of the articles
3. Create a podcast script from the summary
4. Generate audio for the podcast using TTS

Required Environment Variables:
1. PEPPERPY_NEWS__NEWSAPI_API_KEY:
   - Get a free key at https://newsapi.org
   - Sign up for an account
   - Go to https://newsapi.org/account
   - Copy your API key from the dashboard

2. PEPPERPY_TTS__PROVIDER:
   - Set to your preferred TTS provider (e.g., "murf")

3. Provider-specific API keys:
   - For Murf: PEPPERPY_TTS_MURF__API_KEY
   - Get a key at https://murf.ai/api

Free tier limitations may apply depending on the provider.
"""

import asyncio
import datetime
import os
import urllib.parse
from typing import Any, Dict, List

from dotenv import load_dotenv

from pepperpy.core.http import HTTPClient
from pepperpy.tts import convert_text, save_audio

# Load environment variables
load_dotenv()


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

    async def generate_audio(self, script: str) -> None:
        """Generate audio from the script using TTS."""
        try:
            # Split the script into chunks of 2500 characters (leaving room for safety)
            chunks = []
            max_chunk_size = 2500
            while script:
                # Find the last complete sentence within the chunk size
                chunk_end = min(max_chunk_size, len(script))
                while chunk_end > 0 and script[chunk_end - 1] not in ".!?\n":
                    chunk_end -= 1
                if chunk_end == 0:  # No sentence break found, force split at max size
                    chunk_end = min(max_chunk_size, len(script))

                chunks.append(script[:chunk_end])
                script = script[chunk_end:].lstrip()

            print(f"\nSplit script into {len(chunks)} chunks for processing...")

            # Process each chunk and combine the audio
            all_audio = bytearray()
            for i, chunk in enumerate(chunks, 1):
                print(f"Processing chunk {i}/{len(chunks)}...")
                audio_data = await convert_text(
                    chunk,
                    voice_id="pt-BR-heitor",  # Using Heitor's voice (middle-aged male) for Brazilian Portuguese
                    output_format="mp3",
                )
                all_audio.extend(audio_data)

            # Save the combined audio file
            save_audio(bytes(all_audio), "examples/output/podcast_audio.mp3")
            print("Audio file saved successfully!")
        except Exception as e:
            print(f"Error generating audio: {e}")

    async def run(self) -> None:
        """Run the content pipeline."""
        await self.fetch_news()
        self.create_summary()
        script = self._format_podcast_script(self.articles)

        # Save the script to a file
        self._save_script(script)

        # Generate audio files
        await self.generate_audio(script)

        # Print example content for reference
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
