"""LLM configuration."""

from dataclasses import dataclass

from ..providers.config import ProviderConfig


@dataclass
class LLMConfig(ProviderConfig):
    """LLM configuration."""

    # Herdamos os campos base do ProviderConfig:
    # - name: str
    # - provider: str
    # - model: str
    # - api_key: str
    # - api_base: Optional[str] = None
    # - metadata: Dict[str, Any]
    # - settings: Dict[str, Any]

    # Campos específicos do LLM
    temperature: float = 0.7
    max_tokens: int = 1000
    stop_sequences: list[str] | None = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
