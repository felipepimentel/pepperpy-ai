"""Memory system migrations."""

from typing import Dict, Any, cast
from datetime import datetime

from .migrations import Migration


class MemoryEntryMigration_1_0_0_to_2_0_0(Migration[Dict[str, Any]]):
    """Migration for memory entries from 1.0.0 to 2.0.0."""

    def __init__(self):
        """Initialize the migration."""
        super().__init__("memory_entry")

    @property
    def source_version(self) -> str:
        """Get the source version string."""
        return "1.0.0"

    @property
    def target_version(self) -> str:
        """Get the target version string."""
        return "2.0.0"

    async def migrate_forward(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data forward from 1.0.0 to 2.0.0.
        
        Changes:
        - Moves type and scope into metadata
        - Renames timestamp to created_at
        - Adds version to metadata
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
        """
        return {
            "key": data["key"],
            "value": data["value"],
            "metadata": {
                "type": data.get("type"),
                "scope": data.get("scope"),
                "created_at": data.get("timestamp"),
                "version": "2.0.0",
            },
        }

    async def migrate_backward(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data backward from 2.0.0 to 1.0.0.
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
        """
        metadata = data.get("metadata", {})
        return {
            "key": data["key"],
            "value": data["value"],
            "type": metadata.get("type"),
            "scope": metadata.get("scope"),
            "timestamp": metadata.get("created_at"),
        }


class MemoryEntryMigration_2_0_0_to_3_0_0(Migration[Dict[str, Any]]):
    """Migration for memory entries from 2.0.0 to 3.0.0."""

    def __init__(self):
        """Initialize the migration."""
        super().__init__("memory_entry")

    @property
    def source_version(self) -> str:
        """Get the source version string."""
        return "2.0.0"

    @property
    def target_version(self) -> str:
        """Get the target version string."""
        return "3.0.0"

    async def migrate_forward(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data forward from 2.0.0 to 3.0.0.
        
        Changes:
        - Adds updated_at timestamp
        - Adds tags list
        - Adds checksum for value
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
        """
        metadata = data.get("metadata", {})
        now = datetime.utcnow().isoformat()
        
        return {
            "key": data["key"],
            "value": data["value"],
            "metadata": {
                **metadata,
                "updated_at": now,
                "tags": [],
                "checksum": self._calculate_checksum(data["value"]),
                "version": "3.0.0",
            },
        }

    async def migrate_backward(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data backward from 3.0.0 to 2.0.0.
        
        Args:
            data: Data to migrate
            
        Returns:
            Migrated data
        """
        metadata = data.get("metadata", {})
        filtered_metadata = {
            k: v
            for k, v in metadata.items()
            if k in {"type", "scope", "created_at", "version"}
        }
        filtered_metadata["version"] = "2.0.0"
        
        return {
            "key": data["key"],
            "value": data["value"],
            "metadata": filtered_metadata,
        }

    def _calculate_checksum(self, value: Any) -> str:
        """Calculate checksum for a value.
        
        Args:
            value: Value to calculate checksum for
            
        Returns:
            Checksum string
        """
        import hashlib
        import json
        
        # Convert value to JSON string
        value_str = json.dumps(value, sort_keys=True)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(value_str.encode()).hexdigest() 