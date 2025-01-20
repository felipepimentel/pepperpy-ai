"""Configuration for monitoring."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from .base import BaseConfig, ConfigError
from .validation import ValidationMixin


@dataclass
class MetricsConfig(ValidationMixin):
    """Configuration for metrics collection."""
    
    output_path: Optional[Path] = None
    buffer_size: int = 100
    
    def validate(self) -> None:
        """Validate metrics configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_positive("buffer_size", self.buffer_size)


@dataclass
class LoggingConfig(ValidationMixin):
    """Configuration for logging."""
    
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    output_path: Optional[Path] = None
    
    def validate(self) -> None:
        """Validate logging configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.validate_string(
            "level",
            self.level,
            choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        )
        self.validate_string("format", self.format, min_length=1)


@dataclass
class MonitoringConfig(BaseConfig, ValidationMixin):
    """Configuration for monitoring."""
    
    metrics: MetricsConfig = MetricsConfig()
    logging: LoggingConfig = LoggingConfig()
    
    def validate(self) -> None:
        """Validate monitoring configuration.
        
        Raises:
            ConfigError: If validation fails.
        """
        self.metrics.validate()
        self.logging.validate() 