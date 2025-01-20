"""Model constants for Pepperpy."""

from enum import Enum
from typing import Final

# Model providers
class ModelProvider(str, Enum):
    """Model providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"

# Model types
class ModelType(str, Enum):
    """Model types."""
    
    TEXT = "text"
    EMBEDDING = "embedding"
    CHAT = "chat"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"

# Default model settings
DEFAULT_MAX_TOKENS: Final[int] = 2048
DEFAULT_TEMPERATURE: Final[float] = 0.7
DEFAULT_TOP_P: Final[float] = 1.0
DEFAULT_FREQUENCY_PENALTY: Final[float] = 0.0
DEFAULT_PRESENCE_PENALTY: Final[float] = 0.0

# OpenAI models
class OpenAIModel(str, Enum):
    """OpenAI model names."""
    
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT35_TURBO = "gpt-3.5-turbo"
    GPT35_TURBO_16K = "gpt-3.5-turbo-16k"
    TEXT_EMBEDDING_3 = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"

# Anthropic models
class AnthropicModel(str, Enum):
    """Anthropic model names."""
    
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_2_1 = "claude-2.1"
    CLAUDE_2 = "claude-2"
    CLAUDE_INSTANT = "claude-instant-1.2"

# Model capabilities
class ModelCapability(str, Enum):
    """Model capabilities."""
    
    COMPLETION = "completion"
    CHAT = "chat"
    EMBEDDING = "embedding"
    FINE_TUNING = "fine_tuning"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    AUDIO = "audio"

# Token limits
MAX_TOKENS_BY_MODEL = {
    OpenAIModel.GPT4: 8192,
    OpenAIModel.GPT4_TURBO: 128000,
    OpenAIModel.GPT35_TURBO: 4096,
    OpenAIModel.GPT35_TURBO_16K: 16384,
    AnthropicModel.CLAUDE_3_OPUS: 200000,
    AnthropicModel.CLAUDE_3_SONNET: 200000,
    AnthropicModel.CLAUDE_3_HAIKU: 200000,
    AnthropicModel.CLAUDE_2_1: 100000,
    AnthropicModel.CLAUDE_2: 100000,
    AnthropicModel.CLAUDE_INSTANT: 100000,
}

# Embedding dimensions
EMBEDDING_DIMENSIONS = {
    OpenAIModel.TEXT_EMBEDDING_3: 1536,
    OpenAIModel.TEXT_EMBEDDING_3_LARGE: 3072,
}

# Model roles
class ModelRole(str, Enum):
    """Model roles in conversations."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function" 