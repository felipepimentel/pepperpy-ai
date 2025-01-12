"""Core configuration module."""

from .base import BaseConfig


class CoreConfig(BaseConfig):
    """Configuration for core functionality.

    This class provides configuration options for core functionality,
    including logging settings, resource limits, and other fundamental
    parameters that control system behavior.
    """

    def __init__(
        self,
        name: str,
        version: str,
        enabled: bool = True,
        log_level: str = "INFO",
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        max_workers: int = 4,
        max_queue_size: int = 1000,
        max_memory: int = 1024,
        max_cpu_percent: float = 80.0,
    ) -> None:
        """Initialize core configuration.

        Args:
            name: Configuration name.
            version: Configuration version.
            enabled: Whether core functionality is enabled.
            log_level: Logging level.
            log_format: Logging format string.
            max_workers: Maximum number of worker threads.
            max_queue_size: Maximum size of task queues.
            max_memory: Maximum memory usage in MB.
            max_cpu_percent: Maximum CPU usage percentage.
        """
        super().__init__(name=name, version=version, enabled=enabled)
        self.log_level = log_level
        self.log_format = log_format
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.max_memory = max_memory
        self.max_cpu_percent = max_cpu_percent
