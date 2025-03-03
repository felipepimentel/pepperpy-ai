"""Error hierarchy management.

This module provides tools for managing error hierarchies and relationships.
"""

from typing import Dict, List, Optional, Set

from pepperpy.core.common.errors.unified import PepperError


class ErrorNode:
    """Node in the error hierarchy tree."""

    def __init__(self, error_type: type[PepperError]) -> None:
        """Initialize error node.

        Args:
            error_type: The error type this node represents
        """
        self.error_type = error_type
        self.parent: ErrorNode | None = None
        self.children: list[ErrorNode] = []

    def add_child(self, child: "ErrorNode") -> None:
        """Add a child node.

        Args:
            child: The child node to add
        """
        child.parent = self
        self.children.append(child)

    def is_ancestor_of(self, other: "ErrorNode") -> bool:
        """Check if this node is an ancestor of another node.

        Args:
            other: The node to check

        Returns:
            bool: True if this node is an ancestor of other
        """
        current = other.parent
        while current is not None:
            if current == self:
                return True
            current = current.parent
        return False


class ErrorHierarchy:
    """Manages the hierarchy of error types."""

    def __init__(self) -> None:
        """Initialize error hierarchy."""
        self.root = ErrorNode(PepperError)
        self._nodes: dict[type[PepperError], ErrorNode] = {PepperError: self.root}

    def add_error(self, error_type: type[PepperError]) -> None:
        """Add an error type to the hierarchy.

        Args:
            error_type: The error type to add
        """
        if error_type in self._nodes:
            return

        node = ErrorNode(error_type)
        self._nodes[error_type] = node

        # Find parent in hierarchy
        parent_type = error_type.__bases__[0]
        while parent_type not in self._nodes and parent_type is not object:
            parent_type = parent_type.__bases__[0]

        if parent_type in self._nodes:
            self._nodes[parent_type].add_child(node)

    def get_ancestors(self, error_type: type[PepperError]) -> set[type[PepperError]]:
        """Get all ancestor error types.

        Args:
            error_type: The error type to get ancestors for

        Returns:
            Set of ancestor error types
        """
        if error_type not in self._nodes:
            return set()

        ancestors = set()
        current = self._nodes[error_type].parent
        while current is not None:
            ancestors.add(current.error_type)
            current = current.parent
        return ancestors

    def get_descendants(self, error_type: type[PepperError]) -> set[type[PepperError]]:
        """Get all descendant error types.

        Args:
            error_type: The error type to get descendants for

        Returns:
            Set of descendant error types
        """
        if error_type not in self._nodes:
            return set()

        descendants = set()
        stack = [self._nodes[error_type]]
        while stack:
            node = stack.pop()
            for child in node.children:
                descendants.add(child.error_type)
                stack.append(child)
        return descendants


__all__ = ["ErrorHierarchy", "ErrorNode"]
