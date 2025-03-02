"""Version migration manager."""


class MigrationManager:
    """Manager for version migrations."""

    def __init__(self) -> None:
        """Initialize migration manager."""
        self._migrations = {}
        self._dependencies = {}
