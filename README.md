# Pepperpy

A framework for building AI-powered applications with capabilities for LLM, content processing, speech synthesis, and memory management.

## 🚀 Quick Start (News-to-Podcast Example)
```bash
# Install Pepperpy
pip install pepperpy

# Run the news-to-podcast example
python examples/news_podcast.py --topic "technology"
```

## Features

- 🤖 LLM Integration (OpenAI, LangChain)
- 📰 Content Processing
- 🎙️ Speech Synthesis
- 🧠 Memory Management
- 🔄 Agent Orchestration

## Project Structure

```
pepperpy/
├── core/          - Core abstractions and utilities
├── llm/           - LLM integration and providers
├── content/       - Content processing and providers
├── synthesis/     - Speech synthesis capabilities
├── memory/        - Memory and storage management
└── agents/        - Agent orchestration system

examples/
├── news_podcast.py  - News-to-Podcast generator
├── story_creation.py - Story creation example
└── README.md        - Examples documentation
```

## Installation

```bash
# Install with Poetry
poetry install

# Or with pip
pip install pepperpy
```

## Documentation

### News-to-Podcast Example

```python
from pepperpy import Pepperpy
from pepperpy.content import NewsProvider
from pepperpy.synthesis import TTSProvider

async def create_podcast(topic: str) -> str:
    # Initialize Pepperpy
    pepper = await Pepperpy.create()
    
    # Get news content
    news = await pepper.content.get_provider("news")
    articles = await news.fetch(topic=topic)
    
    # Generate script
    llm = await pepper.llm.get_provider("openai")
    script = await llm.generate(
        prompt="Create a podcast script from these articles",
        context=articles
    )
    
    # Convert to speech
    tts = await pepper.synthesis.get_provider("gtts")
    audio_path = await tts.synthesize(script)
    
    return audio_path

if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="technology")
    args = parser.parse_args()
    
    audio_path = asyncio.run(create_podcast(args.topic))
    print(f"Podcast created: {audio_path}")
```

### Story Creation Example

```python
from pepperpy import Pepperpy
from pepperpy.agents import Chain

async def create_story() -> dict:
    pepper = await Pepperpy.create()
    
    # Create agent chain
    chain = Chain([
        "story_planner",
        "story_writer",
        "story_editor",
        "narrator"
    ])
    
    # Run the chain
    result = await chain.run()
    
    return {
        "text": result.story,
        "audio_path": result.audio
    }
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
