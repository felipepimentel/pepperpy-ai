"""Configuration management for the research assistant example."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration settings for the research assistant."""

    pepperpy_api_key: str
    pepperpy_provider: str
    pepperpy_model: str
    pepperpy_env: str
    pepperpy_debug: bool
    memory_importance_threshold: float
    max_short_term_memories: int
    text_chunk_size: int
    text_overlap: int

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()

        return cls(
            pepperpy_api_key=os.getenv("PEPPERPY_API_KEY", ""),
            pepperpy_provider=os.getenv("PEPPERPY_PROVIDER", "openrouter"),
            pepperpy_model=os.getenv("PEPPERPY_MODEL", "openai/gpt-4o-mini"),
            pepperpy_env=os.getenv("PEPPERPY_ENV", "development"),
            pepperpy_debug=os.getenv("PEPPERPY_DEBUG", "true").lower() == "true",
            memory_importance_threshold=float(
                os.getenv("PEPPERPY_MEMORY_IMPORTANCE_THRESHOLD", "0.5")
            ),
            max_short_term_memories=int(
                os.getenv("PEPPERPY_MAX_SHORT_TERM_MEMORIES", "100")
            ),
            text_chunk_size=int(os.getenv("PEPPERPY_TEXT_CHUNK_SIZE", "1000")),
            text_overlap=int(os.getenv("PEPPERPY_TEXT_OVERLAP", "100")),
        )
