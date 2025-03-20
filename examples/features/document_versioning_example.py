#!/usr/bin/env python
"""Example demonstrating the document versioning and diff tracking system.

This example demonstrates the usage of the document versioning and diff tracking
system, including creating versions, computing diffs, and tracking document
history.
"""

import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import pepperpy
sys.path.append(str(Path(__file__).parent.parent))

from pepperpy.core.telemetry import enable_telemetry, set_telemetry_level
from pepperpy.rag.versioning import (
    ChangeType,
    DocumentHistory,
    VersionManager,
    compute_document_diff,
    get_document_history,
)
from pepperpy.types.common import Document, Metadata


def setup_logging():
    """Set up logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def create_sample_document() -> Document:
    """Create a sample document for demonstration.

    Returns:
        A sample document.
    """
    content = """# Sample Document

This is a sample document for demonstrating the versioning system.

## Introduction

The versioning system allows tracking changes to documents over time.
It provides features for:

- Creating document versions
- Computing diffs between versions
- Tracking document history
- Restoring previous versions

## Usage

To use the versioning system, you need to:

1. Create a document
2. Create versions of the document
3. Track changes using the version manager
4. Compute diffs between versions

## Conclusion

The versioning system is a powerful tool for managing document changes.
"""

    metadata = {
        "title": "Sample Document",
        "author": "John Doe",
        "tags": ["sample", "versioning", "example"],
        "created_at": "2025-03-16T10:00:00",
    }

    return Document(
        id="doc1",
        content=content,
        metadata=Metadata.from_dict(metadata),
    )


def create_updated_document(original: Document) -> Document:
    """Create an updated version of the document.

    Args:
        original: The original document.

    Returns:
        An updated document.
    """
    # Update the content with some changes
    updated_content = """# Sample Document (Updated)

This is a sample document for demonstrating the versioning system.

## Introduction

The versioning system allows tracking changes to documents over time.
It provides features for:

- Creating document versions
- Computing diffs between versions
- Tracking document history
- Restoring previous versions
- Analyzing change patterns

## Usage

To use the versioning system, you need to:

1. Create a document
2. Create versions of the document
3. Track changes using the version manager
4. Compute diffs between versions
5. Analyze document history

## Advanced Features

The versioning system also supports:

- HTML diff rendering
- Metadata change tracking
- Version restoration

## Conclusion

The versioning system is a powerful tool for managing document changes.
It helps maintain document integrity and track the evolution of content.
"""

    # Update the metadata
    metadata_dict = original.metadata.to_dict() if original.metadata else {}
    updated_metadata = {
        **metadata_dict,
        "title": "Sample Document (Updated)",
        "updated_at": "2025-03-16T14:30:00",
        "tags": ["sample", "versioning", "example", "updated"],
        "version": "1.1",
    }

    return Document(
        id=original.id,
        content=updated_content,
        metadata=Metadata.from_dict(updated_metadata),
    )


def create_final_document(updated: Document) -> Document:
    """Create a final version of the document.

    Args:
        updated: The updated document.

    Returns:
        A final document.
    """
    # Update the content with some changes
    final_content = """# Sample Document (Final)

This is the final version of the sample document for demonstrating the versioning system.

## Introduction

The versioning system allows tracking changes to documents over time.
It provides features for:

- Creating document versions
- Computing diffs between versions
- Tracking document history
- Restoring previous versions
- Analyzing change patterns
- Exporting version history

## Usage

To use the versioning system, you need to:

1. Create a document
2. Create versions of the document
3. Track changes using the version manager
4. Compute diffs between versions
5. Analyze document history
6. Export version reports

## Advanced Features

The versioning system also supports:

- HTML diff rendering
- Metadata change tracking
- Version restoration
- Change summarization
- Integrity verification

## Conclusion

The versioning system is a powerful tool for managing document changes.
It helps maintain document integrity and track the evolution of content.
With the versioning system, you can confidently manage document revisions
and collaborate with others on document creation.
"""

    # Update the metadata
    metadata_dict = updated.metadata.to_dict() if updated.metadata else {}
    final_metadata = {
        **metadata_dict,
        "title": "Sample Document (Final)",
        "updated_at": "2025-03-16T18:45:00",
        "tags": ["sample", "versioning", "example", "updated", "final"],
        "version": "2.0",
        "status": "final",
    }

    return Document(
        id=updated.id,
        content=final_content,
        metadata=Metadata.from_dict(final_metadata),
    )


def demonstrate_version_creation():
    """Demonstrate creating document versions."""
    print("\n=== Demonstrating Version Creation ===\n")

    # Create sample documents
    original = create_sample_document()
    updated = create_updated_document(original)
    final = create_final_document(updated)

    # Create a version manager
    version_manager = VersionManager()

    # Create versions
    v1 = version_manager.create_version(
        document=original,
        change_type=ChangeType.CREATED,
        change_summary="Initial version",
    )

    v2 = version_manager.create_version(
        document=updated,
        change_type=ChangeType.UPDATED,
        change_summary="Updated content and metadata",
    )

    v3 = version_manager.create_version(
        document=final,
        change_type=ChangeType.UPDATED,
        change_summary="Finalized document",
    )

    # Print version information
    print(f"Created {len(version_manager.document_versions[original.id])} versions:")
    print(f"  Version 1: {v1.version_id} ({v1.change_type.value})")
    print(f"  Version 2: {v2.version_id} ({v2.change_type.value})")
    print(f"  Version 3: {v3.version_id} ({v3.change_type.value})")

    # Get the latest version
    latest = version_manager.get_latest_version(original.id)
    print(f"\nLatest version: {latest.version_number} ({latest.change_summary})")

    return version_manager, original.id


def demonstrate_diff_computation(version_manager: VersionManager, document_id: str):
    """Demonstrate computing diffs between document versions.

    Args:
        version_manager: The version manager to use.
        document_id: The ID of the document.
    """
    print("\n=== Demonstrating Diff Computation ===\n")

    # Get the versions
    versions = version_manager.get_version_history(document_id)

    if len(versions) < 2:
        print("Need at least 2 versions to compute diffs.")
        return

    # Compute diff between versions 1 and 2
    v1 = versions[0]
    v2 = versions[1]

    diff_1_2 = version_manager.compute_diff(v1.version_id, v2.version_id)

    print("Diff between versions 1 and 2:")
    print(f"  From: {v1.version_id} (Version {v1.version_number})")
    print(f"  To: {v2.version_id} (Version {v2.version_number})")
    print(f"  Content changes: {len(diff_1_2.content_diff)} lines")
    print(f"  Metadata changes: {len(diff_1_2.metadata_diff)} keys")

    # Print some of the content diff
    print("\nContent diff preview:")
    for line in diff_1_2.content_diff[:10]:
        print(f"  {line}")
    if len(diff_1_2.content_diff) > 10:
        print(f"  ... ({len(diff_1_2.content_diff) - 10} more lines)")

    # Print metadata diff
    print("\nMetadata diff:")
    for key, (from_value, to_value) in diff_1_2.metadata_diff.items():
        print(f"  {key}: {from_value} -> {to_value}")

    # If we have at least 3 versions, compute diff between versions 1 and 3
    if len(versions) >= 3:
        v3 = versions[2]
        diff_1_3 = version_manager.compute_diff(v1.version_id, v3.version_id)

        print("\nDiff between versions 1 and 3:")
        print(f"  From: {v1.version_id} (Version {v1.version_number})")
        print(f"  To: {v3.version_id} (Version {v3.version_number})")
        print(f"  Content changes: {len(diff_1_3.content_diff)} lines")
        print(f"  Metadata changes: {len(diff_1_3.metadata_diff)} keys")


def demonstrate_document_history(document_id: str):
    """Demonstrate using document history.

    Args:
        document_id: The ID of the document.
    """
    print("\n=== Demonstrating Document History ===\n")

    # Get document history
    history = get_document_history(document_id)

    # Get all versions
    versions = history.get_versions()
    print(f"Document has {len(versions)} versions:")

    for version in versions:
        print(f"  Version {version.version_number}: {version.change_summary}")
        print(f"    Created: {version.timestamp}")
        print(f"    Change type: {version.change_type.value}")
        print(f"    Content length: {len(version.content)} characters")
        print(f"    Metadata keys: {', '.join(version.metadata.keys())}")
        print()

    # Get change history
    change_history = history.get_change_history()
    print("Change history:")
    for change in change_history:
        print(
            f"  Version {change['version_number']}: {change['change_type']} - {change['change_summary']}"
        )

    # Get diff between first and last version
    if len(versions) >= 2:
        first_version = versions[0].version_number
        last_version = versions[-1].version_number

        diff = history.get_diff(first_version, last_version)
        print(f"\nDiff between versions {first_version} and {last_version}:")
        print(f"  Content changes: {len(diff.content_diff)} lines")
        print(f"  Metadata changes: {len(diff.metadata_diff)} keys")


def demonstrate_direct_diff_computation():
    """Demonstrate computing diffs directly between documents."""
    print("\n=== Demonstrating Direct Diff Computation ===\n")

    # Create sample documents
    original = create_sample_document()
    final = create_final_document(create_updated_document(original))

    # Compute diff directly
    diff = compute_document_diff(original, final)

    print("Direct diff between original and final documents:")
    print(f"  From: {original.id}")
    print(f"  To: {final.id}")
    print(f"  Content changes: {len(diff.content_diff)} lines")
    print(f"  Metadata changes: {len(diff.metadata_diff)} keys")

    # Print some of the content diff
    print("\nContent diff preview:")
    for line in diff.content_diff[:10]:
        print(f"  {line}")
    if len(diff.content_diff) > 10:
        print(f"  ... ({len(diff.content_diff) - 10} more lines)")

    # Print metadata diff
    print("\nMetadata diff:")
    for key, (from_value, to_value) in diff.metadata_diff.items():
        print(f"  {key}: {from_value} -> {to_value}")


def demonstrate_version_restoration(version_manager: VersionManager, document_id: str):
    """Demonstrate restoring a document to a previous version.

    Args:
        version_manager: The version manager to use.
        document_id: The ID of the document.
    """
    print("\n=== Demonstrating Version Restoration ===\n")

    # Get document history
    history = DocumentHistory(document_id, version_manager)

    # Get all versions
    versions = history.get_versions()
    if len(versions) < 2:
        print("Need at least 2 versions to demonstrate restoration.")
        return

    # Restore to the first version
    first_version = versions[0].version_number
    print(f"Restoring document to version {first_version}...")

    restored_doc = history.restore_version(first_version)

    # Get the latest version after restoration
    latest_version = history.get_latest_version()

    print(f"Document restored to version {first_version}")
    print(f"New version created: Version {latest_version.version_number}")
    print(f"Change summary: {latest_version.change_summary}")

    # Verify the content matches the original
    original_version = history.get_version(first_version)
    content_matches = original_version.content == restored_doc.content

    print(f"Content matches original: {content_matches}")

    # Get all versions again to show the new version
    versions = history.get_versions()
    print(f"\nDocument now has {len(versions)} versions:")

    for version in versions:
        print(f"  Version {version.version_number}: {version.change_summary}")


def main():
    """Run the document versioning example."""
    # Set up logging
    setup_logging()

    # Enable telemetry for demonstration
    enable_telemetry()
    set_telemetry_level("INFO")

    print("=== Document Versioning Example ===")
    print(
        "This example demonstrates the usage of the document versioning and diff tracking system."
    )

    # Run demonstrations
    version_manager, document_id = demonstrate_version_creation()
    demonstrate_diff_computation(version_manager, document_id)
    demonstrate_document_history(document_id)
    demonstrate_direct_diff_computation()
    demonstrate_version_restoration(version_manager, document_id)

    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
