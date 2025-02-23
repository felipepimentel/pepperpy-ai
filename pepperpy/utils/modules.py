"""Module management utilities.

This module provides utilities for managing Python modules and their dependencies.
"""

import logging
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Dict, List, Optional, Set

from pepperpy.utils.imports import (
    check_circular_imports,
    get_module_attributes,
    get_module_dependencies,
    get_module_doc,
    get_module_path,
    get_module_version,
    safe_import,
    validate_imports,
)

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Module information."""

    name: str
    path: Optional[str] = None
    version: Optional[str] = None
    doc: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModuleError(Exception):
    """Module error."""

    def __init__(
        self, message: str, module: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            module: Module name
            details: Optional error details
        """
        super().__init__(message)
        self.module = module
        self.details = details or {}


class ModuleManager:
    """Module manager.

    This class provides functionality for managing Python modules and their dependencies.
    """

    def __init__(self) -> None:
        """Initialize manager."""
        self._modules: Dict[str, ModuleInfo] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._reverse_dependencies: Dict[str, Set[str]] = {}

    def register_module(
        self, module: ModuleType, metadata: Optional[Dict[str, Any]] = None
    ) -> ModuleInfo:
        """Register module.

        Args:
            module: Module to register
            metadata: Optional module metadata

        Returns:
            Module information

        Raises:
            ModuleError: If module registration fails
        """
        try:
            name = module.__name__

            # Create module info
            info = ModuleInfo(
                name=name,
                path=get_module_path(name),
                version=get_module_version(name),
                doc=get_module_doc(name),
                dependencies=get_module_dependencies(module),
                attributes=get_module_attributes(name),
                metadata=metadata or {},
            )

            # Update dependencies
            self._dependencies[name] = info.dependencies
            for dep in info.dependencies:
                if dep not in self._reverse_dependencies:
                    self._reverse_dependencies[dep] = set()
                self._reverse_dependencies[dep].add(name)

            # Store module info
            self._modules[name] = info

            logger.info(
                f"Registered module: {name}",
                extra={
                    "module": name,
                    "version": info.version,
                    "dependencies": len(info.dependencies),
                },
            )

            return info

        except Exception as e:
            logger.error(
                f"Module registration failed: {e}",
                extra={"module": module.__name__},
                exc_info=True,
            )
            raise ModuleError(
                f"Failed to register module: {e}",
                module.__name__,
                {"error": str(e)},
            )

    def unregister_module(self, name: str) -> None:
        """Unregister module.

        Args:
            name: Module name

        Raises:
            ModuleError: If module unregistration fails
        """
        try:
            if name not in self._modules:
                raise ModuleError(f"Module not found: {name}", name)

            # Remove dependencies
            deps = self._dependencies.pop(name, set())
            for dep in deps:
                if dep in self._reverse_dependencies:
                    self._reverse_dependencies[dep].discard(name)
                    if not self._reverse_dependencies[dep]:
                        del self._reverse_dependencies[dep]

            # Remove module info
            del self._modules[name]

            logger.info(f"Unregistered module: {name}")

        except Exception as e:
            logger.error(
                f"Module unregistration failed: {e}",
                extra={"module": name},
                exc_info=True,
            )
            raise ModuleError(
                f"Failed to unregister module: {e}",
                name,
                {"error": str(e)},
            )

    def get_module_info(self, name: str) -> Optional[ModuleInfo]:
        """Get module information.

        Args:
            name: Module name

        Returns:
            Module information or None if not found
        """
        return self._modules.get(name)

    def get_dependencies(self, name: str) -> Set[str]:
        """Get module dependencies.

        Args:
            name: Module name

        Returns:
            Set of module dependencies

        Raises:
            ModuleError: If module not found
        """
        if name not in self._modules:
            raise ModuleError(f"Module not found: {name}", name)
        return self._dependencies.get(name, set())

    def get_reverse_dependencies(self, name: str) -> Set[str]:
        """Get modules that depend on this module.

        Args:
            name: Module name

        Returns:
            Set of dependent module names

        Raises:
            ModuleError: If module not found
        """
        if name not in self._modules:
            raise ModuleError(f"Module not found: {name}", name)
        return self._reverse_dependencies.get(name, set())

    def get_all_dependencies(self, name: str) -> Set[str]:
        """Get all module dependencies recursively.

        Args:
            name: Module name

        Returns:
            Set of all module dependencies

        Raises:
            ModuleError: If module not found
        """
        if name not in self._modules:
            raise ModuleError(f"Module not found: {name}", name)

        all_deps = set()
        visited = set()

        def visit(module: str) -> None:
            """Visit module and its dependencies.

            Args:
                module: Module name
            """
            if module in visited:
                return

            visited.add(module)
            deps = self._dependencies.get(module, set())
            all_deps.update(deps)

            for dep in deps:
                visit(dep)

        visit(name)
        return all_deps

    def get_dependency_order(self, modules: Optional[List[str]] = None) -> List[str]:
        """Get modules in dependency order.

        Args:
            modules: Optional list of modules to order

        Returns:
            List of modules in dependency order

        Raises:
            ModuleError: If circular dependency detected
        """
        if modules is None:
            modules = list(self._modules.keys())

        # Check for unknown modules
        unknown = set(modules) - set(self._modules.keys())
        if unknown:
            raise ModuleError(
                f"Unknown modules: {', '.join(unknown)}",
                next(iter(unknown)),
            )

        # Topological sort
        order = []
        visited = set()
        temp = set()

        def visit(module: str) -> None:
            """Visit module and its dependencies.

            Args:
                module: Module name

            Raises:
                ModuleError: If circular dependency detected
            """
            if module in temp:
                raise ModuleError(
                    "Circular dependency detected",
                    module,
                    {"cycle": list(temp)},
                )

            if module in visited:
                return

            temp.add(module)
            deps = self._dependencies.get(module, set())

            for dep in deps:
                if dep in modules:
                    visit(dep)

            temp.remove(module)
            visited.add(module)
            order.append(module)

        for module in modules:
            if module not in visited:
                visit(module)

        return list(reversed(order))

    def check_dependencies(self, name: str) -> bool:
        """Check if all module dependencies are available.

        Args:
            name: Module name

        Returns:
            True if all dependencies are available

        Raises:
            ModuleError: If module not found
        """
        if name not in self._modules:
            raise ModuleError(f"Module not found: {name}", name)

        deps = self._dependencies.get(name, set())
        for dep in deps:
            if not safe_import(dep):
                logger.warning(
                    "Missing dependency",
                    extra={"module": name, "dependency": dep},
                )
                return False

        return True

    def validate_module(self, name: str) -> bool:
        """Validate module.

        Args:
            name: Module name

        Returns:
            True if module is valid

        Raises:
            ModuleError: If module not found
        """
        if name not in self._modules:
            raise ModuleError(f"Module not found: {name}", name)

        module = safe_import(name)
        if not module:
            return False

        return validate_imports(module)

    def check_circular_imports(self, name: str) -> List[tuple[str, str]]:
        """Check for circular imports.

        Args:
            name: Module name

        Returns:
            List of circular import pairs

        Raises:
            ModuleError: If module not found
        """
        if name not in self._modules:
            raise ModuleError(f"Module not found: {name}", name)

        module = safe_import(name)
        if not module:
            return []

        return check_circular_imports(module)

    def list_modules(self) -> List[str]:
        """List registered modules.

        Returns:
            List of module names
        """
        return list(self._modules.keys())

    def get_module_graph(self) -> Dict[str, Set[str]]:
        """Get module dependency graph.

        Returns:
            Dictionary mapping module names to their dependencies
        """
        return self._dependencies.copy()

    def get_reverse_graph(self) -> Dict[str, Set[str]]:
        """Get reverse dependency graph.

        Returns:
            Dictionary mapping module names to modules that depend on them
        """
        return self._reverse_dependencies.copy()

    def clear(self) -> None:
        """Clear all registered modules."""
        self._modules.clear()
        self._dependencies.clear()
        self._reverse_dependencies.clear()
        logger.info("Cleared all registered modules")
