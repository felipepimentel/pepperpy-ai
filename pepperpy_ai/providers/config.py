"""Provider configuration."""

from dataclasses import dataclass, field
from typing import Any, Optional, ClassVar, Dict, Type
from datetime import datetime

from pepperpy_core.config import ConfigManager
from pepperpy_core.validation import validate_field

from ..config.base import BaseConfigData
from ..types import JsonDict
from ..exceptions import ValidationError

@dataclass
class ProviderSettings:
    """Base provider settings."""
    pass

@dataclass
class OpenAISettings(ProviderSettings):
    """OpenAI provider settings."""
    organization: Optional[str] = None
    request_timeout: float = 30.0
    max_retries: int = 3

@dataclass
class AnthropicSettings(ProviderSettings):
    """Anthropic provider settings."""
    request_timeout: float = 30.0
    max_retries: int = 3

@dataclass
class OpenRouterSettings(ProviderSettings):
    """OpenRouter provider settings."""
    request_timeout: float = 30.0
    max_retries: int = 3

@dataclass
class StackSpotSettings(ProviderSettings):
    """StackSpot provider settings."""
    request_timeout: float = 30.0
    max_retries: int = 3

PROVIDER_SETTINGS: Dict[str, Type[ProviderSettings]] = {
    "openai": OpenAISettings,
    "anthropic": AnthropicSettings,
    "openrouter": OpenRouterSettings,
    "stackspot": StackSpotSettings,
}

@dataclass
class ProviderConfig(BaseConfigData):
    """Provider configuration.
    
    This class defines the configuration for AI providers.
    
    Attributes:
        name: Provider name
        version: Configuration version
        description: Provider description
        provider: Provider type (e.g., openai, anthropic)
        model: Model name
        api_key: API key
        api_base: Optional API base URL
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens per request
        metadata: Additional provider metadata
        settings: Provider-specific settings
        created_at: Configuration creation timestamp
        updated_at: Configuration update timestamp
    """
    # Required fields from BaseConfigData
    name: str = field(default="")
    version: str = field(default="1.0.0")
    enabled: bool = field(default=True)
    
    # Required provider fields
    provider: str = field(default="")
    model: str = field(default="")
    api_key: str = field(default="")
    
    # Optional fields
    description: str = field(default="")
    api_base: Optional[str] = field(default=None)
    temperature: float = field(default=0.7)
    max_tokens: int = field(default=1000)
    metadata: JsonDict = field(default_factory=dict)
    settings: JsonDict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Configuration constraints
    MIN_TEMPERATURE: ClassVar[float] = 0.0
    MAX_TEMPERATURE: ClassVar[float] = 1.0
    MIN_TOKENS: ClassVar[int] = 1
    MAX_TOKENS: ClassVar[int] = 32000  # Maximum for most models
    SUPPORTED_PROVIDERS: ClassVar[set[str]] = {
        "openai",
        "anthropic",
        "stackspot",
        "openrouter"
    }

    def __post_init__(self) -> None:
        """Validate configuration."""
        super().__post_init__()
        self.validate()
        self._init_provider_settings()

    def _init_provider_settings(self) -> None:
        """Initialize provider-specific settings."""
        if self.provider in PROVIDER_SETTINGS:
            settings_class = PROVIDER_SETTINGS[self.provider]
            provider_settings = settings_class(**self.settings)
            self.settings = provider_settings.__dict__

    def validate(self) -> None:
        """Validate configuration.
        
        Raises:
            ValidationError: If configuration is invalid
        """
        # Validate required fields
        required_fields = {
            "name": str,
            "provider": str,
            "model": str,
            "api_key": str,
        }
        
        for field_name, field_type in required_fields.items():
            validate_field(
                self,
                field_name,
                field_type,
                required=True,
                error_class=ValidationError
            )

        # Validate provider type
        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise ValidationError(
                f"Unsupported provider: {self.provider}",
                field="provider",
                value=self.provider,
                constraints={"supported": list(self.SUPPORTED_PROVIDERS)}
            )

        # Validate temperature
        if not self.MIN_TEMPERATURE <= self.temperature <= self.MAX_TEMPERATURE:
            raise ValidationError(
                f"Temperature must be between {self.MIN_TEMPERATURE} and {self.MAX_TEMPERATURE}",
                field="temperature",
                value=self.temperature,
                constraints={
                    "min": self.MIN_TEMPERATURE,
                    "max": self.MAX_TEMPERATURE
                }
            )

        # Validate max_tokens
        if not self.MIN_TOKENS <= self.max_tokens <= self.MAX_TOKENS:
            raise ValidationError(
                f"max_tokens must be between {self.MIN_TOKENS} and {self.MAX_TOKENS}",
                field="max_tokens",
                value=self.max_tokens,
                constraints={
                    "min": self.MIN_TOKENS,
                    "max": self.MAX_TOKENS
                }
            )

        # Validate provider settings
        if self.provider in PROVIDER_SETTINGS:
            settings_class = PROVIDER_SETTINGS[self.provider]
            try:
                settings_class(**self.settings)
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    f"Invalid provider settings: {e}",
                    field="settings",
                    value=self.settings,
                    constraints={"provider": self.provider}
                )

    def update_settings(self, **kwargs: Any) -> None:
        """Update provider settings.
        
        Args:
            **kwargs: Settings to update
        """
        self.settings.update(kwargs)
        self.updated_at = datetime.now()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get provider setting.
        
        Args:
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            Setting value
        """
        return self.settings.get(key, default)

    def to_dict(self) -> JsonDict:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "api_key": self.api_key,
            "api_base": self.api_base,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ProviderConfig":
        """Create configuration from dictionary.
        
        Args:
            data: Configuration data
            
        Returns:
            Configuration instance
            
        Raises:
            ValidationError: If data is invalid
        """
        try:
            return cls(
                name=data["name"],
                version=data.get("version", "1.0.0"),
                enabled=data.get("enabled", True),
                provider=data["provider"],
                model=data["model"],
                api_key=data["api_key"],
                api_base=data.get("api_base"),
                temperature=data.get("temperature", 0.7),
                max_tokens=data.get("max_tokens", 1000),
                metadata=data.get("metadata", {}),
                settings=data.get("settings", {}),
                created_at=datetime.fromisoformat(
                    data.get("created_at", datetime.now().isoformat())
                ),
                updated_at=datetime.fromisoformat(
                    data.get("updated_at", datetime.now().isoformat())
                ),
            )
        except KeyError as e:
            raise ValidationError(
                f"Missing required field: {e}",
                field=str(e),
                value=None
            )
