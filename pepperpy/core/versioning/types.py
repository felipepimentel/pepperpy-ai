"""Type definitions for the versioning system.

This module defines the type system used by the versioning components:

- VersionNumber: Type for individual version components (major, minor, patch)
- VersionString: Type for string representation of versions
- VersionDict: Type for dictionary representation of versions
- VersionRange: Type for representing version ranges
- VersionRequirement: Type for version requirements
- VersionIdentifier: Type for unique version identifiers

These types provide a consistent foundation for version handling throughout
the framework, ensuring type safety and clear interfaces.
"""

from typing import Dict, List, NewType, Tuple, Union

# Basic version types
VersionNumber = NewType("VersionNumber", int)
VersionString = NewType("VersionString", str)
VersionDict = NewType("VersionDict", Dict[str, Union[int, str]])

# Version range types
VersionRange = NewType("VersionRange", Tuple[VersionString, VersionString])
VersionRequirement = NewType("VersionRequirement", str)

# Version identification
VersionIdentifier = NewType("VersionIdentifier", str)

# Version comparison results
VersionComparisonResult = NewType("VersionComparisonResult", int)

# Version metadata
VersionMetadata = NewType("VersionMetadata", Dict[str, str])

# Version constraints
VersionConstraintType = NewType("VersionConstraintType", str)
VersionConstraintDict = NewType(
    "VersionConstraintDict", Dict[str, Union[str, List[str]]],
)

# Export all types
__all__ = [
    "VersionComparisonResult",
    "VersionConstraintDict",
    "VersionConstraintType",
    "VersionDict",
    "VersionIdentifier",
    "VersionMetadata",
    "VersionNumber",
    "VersionRange",
    "VersionRequirement",
    "VersionString",
]
