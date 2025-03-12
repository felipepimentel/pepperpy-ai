"""Document versioning and diff tracking system for RAG.

This module provides a system for tracking document versions and changes in the
RAG system, enabling version control, history tracking, and diff analysis for
documents.
"""

import datetime
import difflib
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pepperpy.core.telemetry import get_provider_telemetry
from pepperpy.types.common import Document, Metadata

# Set up telemetry
telemetry = get_provider_telemetry("rag_versioning")


class ChangeType(Enum):
    """Types of document changes."""

    CREATED = "created"  # Document was created
    UPDATED = "updated"  # Document was updated
    DELETED = "deleted"  # Document was deleted
    METADATA_UPDATED = "metadata_updated"  # Only metadata was updated
    CONTENT_UPDATED = "content_updated"  # Only content was updated


@dataclass
class DocumentVersion:
    """Represents a specific version of a document.

    This class stores information about a specific version of a document,
    including its content, metadata, and version information.
    """

    document_id: str  # ID of the document
    version_id: str  # Unique ID for this version
    content: str  # Document content
    metadata: Dict[str, Any]  # Document metadata
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    version_number: int = 1  # Sequential version number
    parent_version_id: Optional[str] = None  # ID of the parent version
    change_type: ChangeType = ChangeType.CREATED  # Type of change
    change_summary: Optional[str] = None  # Summary of changes
    hash: Optional[str] = None  # Content hash for integrity checking

    def __post_init__(self):
        """Initialize derived fields after creation."""
        if self.hash is None:
            self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute a hash of the document content for integrity checking.

        Returns:
            A hash string representing the document content.
        """
        content_bytes = self.content.encode("utf-8")
        return hashlib.sha256(content_bytes).hexdigest()

    def to_document(self) -> Document:
        """Convert this version to a Document object.

        Returns:
            A Document object representing this version.
        """
        # Create metadata with version information
        version_metadata = {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "timestamp": self.timestamp.isoformat(),
            "parent_version_id": self.parent_version_id,
            "change_type": self.change_type.value,
            "change_summary": self.change_summary,
            "hash": self.hash,
        }

        # Combine with original metadata
        combined_metadata = {**self.metadata, **version_metadata}

        # Create and return document
        return Document(
            id=self.document_id,
            content=self.content,
            metadata=Metadata.from_dict(combined_metadata),
        )

    @classmethod
    def from_document(
        cls,
        document: Document,
        version_id: Optional[str] = None,
        version_number: int = 1,
        parent_version_id: Optional[str] = None,
        change_type: ChangeType = ChangeType.CREATED,
        change_summary: Optional[str] = None,
    ) -> "DocumentVersion":
        """Create a DocumentVersion from a Document object.

        Args:
            document: The document to create a version from.
            version_id: Optional version ID. If not provided, a new one will be generated.
            version_number: The version number.
            parent_version_id: Optional ID of the parent version.
            change_type: The type of change this version represents.
            change_summary: Optional summary of changes.

        Returns:
            A DocumentVersion object.
        """
        # Extract metadata as dictionary
        metadata_dict = {}
        if document.metadata:
            metadata_dict = document.metadata.to_dict()

        # Generate version ID if not provided
        if version_id is None:
            timestamp = datetime.datetime.now().isoformat()
            version_id = f"{document.id}_{timestamp}"

        # Create and return version
        return cls(
            document_id=document.id,
            version_id=version_id,
            content=document.content,
            metadata=metadata_dict,
            version_number=version_number,
            parent_version_id=parent_version_id,
            change_type=change_type,
            change_summary=change_summary,
        )


@dataclass
class DocumentDiff:
    """Represents the differences between two document versions.

    This class stores information about the differences between two versions
    of a document, including content and metadata changes.
    """

    from_version_id: str  # ID of the source version
    to_version_id: str  # ID of the target version
    content_diff: List[str]  # Unified diff of content
    metadata_diff: Dict[str, Tuple[Any, Any]]  # Changes in metadata
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    change_type: ChangeType = ChangeType.UPDATED  # Type of change
    change_summary: Optional[str] = None  # Summary of changes

    def get_content_diff_html(self) -> str:
        """Get an HTML representation of the content diff.

        Returns:
            An HTML string representing the content diff.
        """
        html_parts = ["<pre class='diff'>"]

        for line in self.content_diff:
            if line.startswith("+"):
                html_parts.append(f"<span class='diff-add'>{line}</span>")
            elif line.startswith("-"):
                html_parts.append(f"<span class='diff-remove'>{line}</span>")
            elif line.startswith("@@"):
                html_parts.append(f"<span class='diff-hunk'>{line}</span>")
            else:
                html_parts.append(line)

        html_parts.append("</pre>")
        return "\n".join(html_parts)

    def get_metadata_diff_html(self) -> str:
        """Get an HTML representation of the metadata diff.

        Returns:
            An HTML string representing the metadata diff.
        """
        html_parts = ["<table class='metadata-diff'>"]
        html_parts.append("<tr><th>Key</th><th>From</th><th>To</th></tr>")

        for key, (from_value, to_value) in self.metadata_diff.items():
            html_parts.append(
                f"<tr><td>{key}</td><td>{from_value}</td><td>{to_value}</td></tr>"
            )

        html_parts.append("</table>")
        return "\n".join(html_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the diff to a dictionary.

        Returns:
            A dictionary representation of the diff.
        """
        return {
            "from_version_id": self.from_version_id,
            "to_version_id": self.to_version_id,
            "content_diff": self.content_diff,
            "metadata_diff": {
                k: {"from": v[0], "to": v[1]} for k, v in self.metadata_diff.items()
            },
            "timestamp": self.timestamp.isoformat(),
            "change_type": self.change_type.value,
            "change_summary": self.change_summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentDiff":
        """Create a DocumentDiff from a dictionary.

        Args:
            data: The dictionary to create a diff from.

        Returns:
            A DocumentDiff object.
        """
        # Convert timestamp string to datetime
        timestamp = datetime.datetime.fromisoformat(data["timestamp"])

        # Convert change type string to enum
        change_type = ChangeType(data["change_type"])

        # Convert metadata diff format
        metadata_diff = {
            k: (v["from"], v["to"]) for k, v in data["metadata_diff"].items()
        }

        # Create and return diff
        return cls(
            from_version_id=data["from_version_id"],
            to_version_id=data["to_version_id"],
            content_diff=data["content_diff"],
            metadata_diff=metadata_diff,
            timestamp=timestamp,
            change_type=change_type,
            change_summary=data["change_summary"],
        )


class VersionManager:
    """Manager for document versions.

    This class provides methods for creating, retrieving, and managing document
    versions, as well as computing diffs between versions.
    """

    def __init__(self, storage_provider=None):
        """Initialize the version manager.

        Args:
            storage_provider: Optional storage provider for persisting versions.
                If not provided, versions will only be stored in memory.
        """
        self.versions = {}  # Map of version_id to DocumentVersion
        self.document_versions = {}  # Map of document_id to list of version_ids
        self.storage_provider = storage_provider

    def create_version(
        self,
        document: Document,
        change_type: ChangeType = ChangeType.CREATED,
        change_summary: Optional[str] = None,
    ) -> DocumentVersion:
        """Create a new version of a document.

        Args:
            document: The document to create a version for.
            change_type: The type of change this version represents.
            change_summary: Optional summary of changes.

        Returns:
            The created DocumentVersion.
        """
        telemetry.info(
            "version_creation_started",
            f"Creating version for document {document.id}",
            {"document_id": document.id, "change_type": change_type.value},
        )

        # Get the latest version number for this document
        version_number = 1
        parent_version_id = None

        if (
            document.id in self.document_versions
            and self.document_versions[document.id]
        ):
            # Get the latest version
            latest_version_id = self.document_versions[document.id][-1]
            latest_version = self.versions[latest_version_id]

            # Increment version number
            version_number = latest_version.version_number + 1
            parent_version_id = latest_version.version_id

        # Generate a version ID
        timestamp = datetime.datetime.now().isoformat()
        version_id = f"{document.id}_v{version_number}_{timestamp}"

        # Create the version
        version = DocumentVersion.from_document(
            document=document,
            version_id=version_id,
            version_number=version_number,
            parent_version_id=parent_version_id,
            change_type=change_type,
            change_summary=change_summary,
        )

        # Store the version
        self.versions[version_id] = version

        if document.id not in self.document_versions:
            self.document_versions[document.id] = []

        self.document_versions[document.id].append(version_id)

        # Persist the version if a storage provider is available
        if self.storage_provider:
            self._persist_version(version)

        telemetry.info(
            "version_creation_completed",
            f"Created version {version_id} for document {document.id}",
            {
                "document_id": document.id,
                "version_id": version_id,
                "version_number": version_number,
                "change_type": change_type.value,
            },
        )

        return version

    def get_version(self, version_id: str) -> Optional[DocumentVersion]:
        """Get a specific version of a document.

        Args:
            version_id: The ID of the version to retrieve.

        Returns:
            The DocumentVersion if found, None otherwise.
        """
        # Check if the version is in memory
        if version_id in self.versions:
            return self.versions[version_id]

        # Try to load from storage if available
        if self.storage_provider:
            version = self._load_version(version_id)
            if version:
                # Cache the loaded version
                self.versions[version_id] = version

                # Update document versions mapping
                if version.document_id not in self.document_versions:
                    self.document_versions[version.document_id] = []

                if version_id not in self.document_versions[version.document_id]:
                    self.document_versions[version.document_id].append(version_id)

                return version

        return None

    def get_latest_version(self, document_id: str) -> Optional[DocumentVersion]:
        """Get the latest version of a document.

        Args:
            document_id: The ID of the document.

        Returns:
            The latest DocumentVersion if found, None otherwise.
        """
        if (
            document_id in self.document_versions
            and self.document_versions[document_id]
        ):
            latest_version_id = self.document_versions[document_id][-1]
            return self.get_version(latest_version_id)

        return None

    def get_version_history(self, document_id: str) -> List[DocumentVersion]:
        """Get the version history of a document.

        Args:
            document_id: The ID of the document.

        Returns:
            A list of DocumentVersion objects, ordered by version number.
        """
        if document_id not in self.document_versions:
            return []

        # Get all versions for this document
        versions = []
        for version_id in self.document_versions[document_id]:
            version = self.get_version(version_id)
            if version:
                versions.append(version)

        # Sort by version number
        return sorted(versions, key=lambda v: v.version_number)

    def compute_diff(
        self, from_version_id: str, to_version_id: str
    ) -> Optional[DocumentDiff]:
        """Compute the diff between two versions of a document.

        Args:
            from_version_id: The ID of the source version.
            to_version_id: The ID of the target version.

        Returns:
            A DocumentDiff object if both versions are found, None otherwise.
        """
        # Get the versions
        from_version = self.get_version(from_version_id)
        to_version = self.get_version(to_version_id)

        if not from_version or not to_version:
            return None

        telemetry.info(
            "diff_computation_started",
            f"Computing diff between versions {from_version_id} and {to_version_id}",
            {"from_version_id": from_version_id, "to_version_id": to_version_id},
        )

        # Compute content diff
        from_lines = from_version.content.splitlines(keepends=True)
        to_lines = to_version.content.splitlines(keepends=True)

        content_diff = list(
            difflib.unified_diff(
                from_lines,
                to_lines,
                fromfile=f"v{from_version.version_number}",
                tofile=f"v{to_version.version_number}",
                n=3,  # Context lines
            )
        )

        # Compute metadata diff
        metadata_diff = {}
        all_keys = set(from_version.metadata.keys()) | set(to_version.metadata.keys())

        for key in all_keys:
            from_value = from_version.metadata.get(key)
            to_value = to_version.metadata.get(key)

            if from_value != to_value:
                metadata_diff[key] = (from_value, to_value)

        # Determine change type
        change_type = to_version.change_type
        change_summary = to_version.change_summary

        # Create the diff
        diff = DocumentDiff(
            from_version_id=from_version_id,
            to_version_id=to_version_id,
            content_diff=content_diff,
            metadata_diff=metadata_diff,
            change_type=change_type,
            change_summary=change_summary,
        )

        telemetry.info(
            "diff_computation_completed",
            f"Computed diff between versions {from_version_id} and {to_version_id}",
            {
                "from_version_id": from_version_id,
                "to_version_id": to_version_id,
                "content_diff_lines": len(content_diff),
                "metadata_diff_keys": len(metadata_diff),
            },
        )

        return diff

    def _persist_version(self, version: DocumentVersion) -> bool:
        """Persist a version to storage.

        Args:
            version: The version to persist.

        Returns:
            True if successful, False otherwise.
        """
        if not self.storage_provider:
            return False

        try:
            # Convert version to a serializable format
            version_data = {
                "document_id": version.document_id,
                "version_id": version.version_id,
                "content": version.content,
                "metadata": version.metadata,
                "timestamp": version.timestamp.isoformat(),
                "version_number": version.version_number,
                "parent_version_id": version.parent_version_id,
                "change_type": version.change_type.value,
                "change_summary": version.change_summary,
                "hash": version.hash,
            }

            # Store the version
            key = f"versions/{version.version_id}"
            self.storage_provider.set(key, json.dumps(version_data))

            # Update the document versions index
            doc_key = f"document_versions/{version.document_id}"
            version_ids = self.storage_provider.get(doc_key)

            if version_ids:
                version_ids = json.loads(version_ids)
                if version.version_id not in version_ids:
                    version_ids.append(version.version_id)
            else:
                version_ids = [version.version_id]

            self.storage_provider.set(doc_key, json.dumps(version_ids))

            return True

        except Exception as e:
            telemetry.error(
                "version_persistence_error",
                f"Error persisting version {version.version_id}",
                {"version_id": version.version_id, "error": str(e)},
            )
            return False

    def _load_version(self, version_id: str) -> Optional[DocumentVersion]:
        """Load a version from storage.

        Args:
            version_id: The ID of the version to load.

        Returns:
            The DocumentVersion if found and loaded successfully, None otherwise.
        """
        if not self.storage_provider:
            return None

        try:
            # Load the version data
            key = f"versions/{version_id}"
            version_data_str = self.storage_provider.get(key)

            if not version_data_str:
                return None

            version_data = json.loads(version_data_str)

            # Convert timestamp string to datetime
            timestamp = datetime.datetime.fromisoformat(version_data["timestamp"])

            # Convert change type string to enum
            change_type = ChangeType(version_data["change_type"])

            # Create and return the version
            return DocumentVersion(
                document_id=version_data["document_id"],
                version_id=version_data["version_id"],
                content=version_data["content"],
                metadata=version_data["metadata"],
                timestamp=timestamp,
                version_number=version_data["version_number"],
                parent_version_id=version_data["parent_version_id"],
                change_type=change_type,
                change_summary=version_data["change_summary"],
                hash=version_data["hash"],
            )

        except Exception as e:
            telemetry.error(
                "version_loading_error",
                f"Error loading version {version_id}",
                {"version_id": version_id, "error": str(e)},
            )
            return None


class DocumentHistory:
    """Provides a view of a document's history.

    This class provides methods for accessing and analyzing the history of a
    document, including version history, diffs, and change tracking.
    """

    def __init__(self, document_id: str, version_manager: VersionManager):
        """Initialize the document history.

        Args:
            document_id: The ID of the document.
            version_manager: The version manager to use.
        """
        self.document_id = document_id
        self.version_manager = version_manager

    def get_versions(self) -> List[DocumentVersion]:
        """Get all versions of the document.

        Returns:
            A list of DocumentVersion objects, ordered by version number.
        """
        return self.version_manager.get_version_history(self.document_id)

    def get_version(self, version_number: int) -> Optional[DocumentVersion]:
        """Get a specific version of the document by version number.

        Args:
            version_number: The version number to retrieve.

        Returns:
            The DocumentVersion if found, None otherwise.
        """
        versions = self.get_versions()
        for version in versions:
            if version.version_number == version_number:
                return version
        return None

    def get_latest_version(self) -> Optional[DocumentVersion]:
        """Get the latest version of the document.

        Returns:
            The latest DocumentVersion if found, None otherwise.
        """
        return self.version_manager.get_latest_version(self.document_id)

    def get_diff(self, from_version: int, to_version: int) -> Optional[DocumentDiff]:
        """Get the diff between two versions of the document.

        Args:
            from_version: The source version number.
            to_version: The target version number.

        Returns:
            A DocumentDiff object if both versions are found, None otherwise.
        """
        # Get the versions
        from_version_obj = self.get_version(from_version)
        to_version_obj = self.get_version(to_version)

        if not from_version_obj or not to_version_obj:
            return None

        # Compute the diff
        return self.version_manager.compute_diff(
            from_version_obj.version_id, to_version_obj.version_id
        )

    def get_change_history(self) -> List[Dict[str, Any]]:
        """Get a summary of changes to the document.

        Returns:
            A list of change summaries, ordered by version number.
        """
        versions = self.get_versions()

        # Create change history
        history = []
        for version in versions:
            history.append({
                "version_number": version.version_number,
                "timestamp": version.timestamp,
                "change_type": version.change_type.value,
                "change_summary": version.change_summary,
            })

        return history

    def restore_version(self, version_number: int) -> Optional[Document]:
        """Restore the document to a specific version.

        This creates a new version with the content and metadata of the
        specified version.

        Args:
            version_number: The version number to restore.

        Returns:
            The restored Document if successful, None otherwise.
        """
        # Get the version to restore
        version_to_restore = self.get_version(version_number)
        if not version_to_restore:
            return None

        telemetry.info(
            "version_restoration_started",
            f"Restoring document {self.document_id} to version {version_number}",
            {"document_id": self.document_id, "version_number": version_number},
        )

        # Create a document from the version
        document = version_to_restore.to_document()

        # Create a new version
        new_version = self.version_manager.create_version(
            document=document,
            change_type=ChangeType.UPDATED,
            change_summary=f"Restored from version {version_number}",
        )

        telemetry.info(
            "version_restoration_completed",
            f"Restored document {self.document_id} to version {version_number}",
            {
                "document_id": self.document_id,
                "version_number": version_number,
                "new_version_id": new_version.version_id,
                "new_version_number": new_version.version_number,
            },
        )

        return document


# Convenience functions


def create_document_version(
    document: Document,
    storage_provider=None,
    change_type: ChangeType = ChangeType.CREATED,
    change_summary: Optional[str] = None,
) -> DocumentVersion:
    """Create a new version of a document.

    Args:
        document: The document to create a version for.
        storage_provider: Optional storage provider for persisting versions.
        change_type: The type of change this version represents.
        change_summary: Optional summary of changes.

    Returns:
        The created DocumentVersion.
    """
    version_manager = VersionManager(storage_provider)
    return version_manager.create_version(
        document=document,
        change_type=change_type,
        change_summary=change_summary,
    )


def get_document_history(document_id: str, storage_provider=None) -> DocumentHistory:
    """Get the history of a document.

    Args:
        document_id: The ID of the document.
        storage_provider: Optional storage provider for loading versions.

    Returns:
        A DocumentHistory object for the document.
    """
    version_manager = VersionManager(storage_provider)
    return DocumentHistory(document_id, version_manager)


def compute_document_diff(
    from_document: Document,
    to_document: Document,
) -> DocumentDiff:
    """Compute the diff between two documents.

    This creates temporary versions of the documents and computes the diff
    between them.

    Args:
        from_document: The source document.
        to_document: The target document.

    Returns:
        A DocumentDiff object representing the differences.
    """
    # Create temporary versions
    from_version = DocumentVersion.from_document(
        document=from_document,
        version_id=f"temp_{from_document.id}_from",
        change_type=ChangeType.CREATED,
    )

    to_version = DocumentVersion.from_document(
        document=to_document,
        version_id=f"temp_{to_document.id}_to",
        change_type=ChangeType.UPDATED,
    )

    # Compute content diff
    from_lines = from_version.content.splitlines(keepends=True)
    to_lines = to_version.content.splitlines(keepends=True)

    content_diff = list(
        difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"from_{from_document.id}",
            tofile=f"to_{to_document.id}",
            n=3,  # Context lines
        )
    )

    # Compute metadata diff
    metadata_diff = {}

    from_metadata = {}
    if from_document.metadata:
        from_metadata = from_document.metadata.to_dict()

    to_metadata = {}
    if to_document.metadata:
        to_metadata = to_document.metadata.to_dict()

    all_keys = set(from_metadata.keys()) | set(to_metadata.keys())

    for key in all_keys:
        from_value = from_metadata.get(key)
        to_value = to_metadata.get(key)

        if from_value != to_value:
            metadata_diff[key] = (from_value, to_value)

    # Create and return the diff
    return DocumentDiff(
        from_version_id=from_version.version_id,
        to_version_id=to_version.version_id,
        content_diff=content_diff,
        metadata_diff=metadata_diff,
        change_type=ChangeType.UPDATED,
        change_summary="Computed diff between documents",
    )
