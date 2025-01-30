#!/usr/bin/env python3
"""
@file: check_duplicates.py
@purpose: Check for potential duplicate files based on purpose and content
@component: Development Tools
@created: 2024-03-20
@task: TASK-000
@status: active
"""

from collections import defaultdict
from difflib import SequenceMatcher
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple

from validate_headers import parse_header, should_check_file


def get_file_hash(path: Path) -> str:
    """Get SHA256 hash of file content."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_purpose(path: Path) -> str:
    """Extract purpose from file header."""
    try:
        with open(path, "r") as f:
            content = f.read()
        fields = parse_header(content)
        return fields.get("purpose", "").lower()
    except Exception:
        return ""


def similar(a: str, b: str, threshold: float = 0.8) -> bool:
    """Check if two strings are similar."""
    return SequenceMatcher(None, a, b).ratio() > threshold


def find_exact_duplicates(files: List[Path]) -> List[Set[Path]]:
    """Find files with identical content."""
    hash_groups = defaultdict(set)

    for path in files:
        file_hash = get_file_hash(path)
        hash_groups[file_hash].add(path)

    return [group for group in hash_groups.values() if len(group) > 1]


def find_similar_purposes(
    files: List[Path], threshold: float = 0.8
) -> List[Tuple[Path, Path, float]]:
    """Find files with similar purposes."""
    similar_files = []
    file_purposes = {path: get_file_purpose(path) for path in files}

    checked_pairs = set()
    for i, path1 in enumerate(files):
        purpose1 = file_purposes[path1]
        if not purpose1:
            continue

        for path2 in files[i + 1 :]:
            if (path1, path2) in checked_pairs:
                continue

            purpose2 = file_purposes[path2]
            if not purpose2:
                continue

            similarity = SequenceMatcher(None, purpose1, purpose2).ratio()
            if similarity > threshold:
                similar_files.append((path1, path2, similarity))

            checked_pairs.add((path1, path2))
            checked_pairs.add((path2, path1))

    return similar_files


def find_similar_names(
    files: List[Path], threshold: float = 0.8
) -> List[Tuple[Path, Path, float]]:
    """Find files with similar names."""
    similar_names = []
    checked_pairs = set()

    for i, path1 in enumerate(files):
        name1 = path1.stem

        for path2 in files[i + 1 :]:
            if (path1, path2) in checked_pairs:
                continue

            name2 = path2.stem
            similarity = SequenceMatcher(None, name1, name2).ratio()

            if similarity > threshold:
                similar_names.append((path1, path2, similarity))

            checked_pairs.add((path1, path2))
            checked_pairs.add((path2, path1))

    return similar_names


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent.parent
    python_files = [
        path for path in project_root.rglob("*.py") if should_check_file(path)
    ]

    # Find exact duplicates
    print("\nChecking for exact duplicates...")
    exact_dupes = find_exact_duplicates(python_files)
    if exact_dupes:
        print("\n❌ Found exact duplicates:")
        for group in exact_dupes:
            print("\nDuplicate group:")
            for path in group:
                print(f"  - {path}")
    else:
        print("✅ No exact duplicates found")

    # Find similar purposes
    print("\nChecking for similar purposes...")
    similar_purposes = find_similar_purposes(python_files)
    if similar_purposes:
        print("\n⚠️  Found files with similar purposes:")
        for path1, path2, similarity in similar_purposes:
            print(f"\nSimilarity: {similarity:.2%}")
            print(f"  - {path1}")
            print(f"  - {path2}")
    else:
        print("✅ No similar purposes found")

    # Find similar names
    print("\nChecking for similar names...")
    similar_names = find_similar_names(python_files)
    if similar_names:
        print("\n⚠️  Found files with similar names:")
        for path1, path2, similarity in similar_names:
            print(f"\nSimilarity: {similarity:.2%}")
            print(f"  - {path1}")
            print(f"  - {path2}")
    else:
        print("✅ No similar names found")


if __name__ == "__main__":
    main()
