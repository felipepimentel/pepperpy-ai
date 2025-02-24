"""
Unified import system for managing and optimizing imports across the framework.
Provides tools for import tracking, validation, and optimization.
"""

import importlib
import inspect
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TypeVar

from pepperpy.core.errors.unified import PepperpyError
from pepperpy.core.metrics.unified import MetricsManager

T = TypeVar("T")


class ImportError(PepperpyError):
    """Base error class for import-related errors."""

    pass


class CircularImportError(ImportError):
    """Error raised when a circular import is detected."""

    pass


class ImportValidationError(ImportError):
    """Error raised when import validation fails."""

    pass


class ImportType(Enum):
    """Types of imports."""

    DIRECT = auto()
    LAZY = auto()
    CONDITIONAL = auto()


@dataclass
class ImportMetadata:
    """Metadata for an imported module."""

    name: str
    path: Path | None = None
    type: ImportType = ImportType.DIRECT
    dependencies: set[str] = field(default_factory=set)
    import_time: float = 0.0
    size: int = 0
    is_package: bool = False


class ImportValidator:
    """Validates imports and dependencies."""

    @staticmethod
    def validate_module_structure(module_name: str) -> bool:
        """Validate the structure of a module."""
        try:
            module = importlib.import_module(module_name)
            return bool(module and hasattr(module, "__file__"))
        except Exception:
            return False

    @staticmethod
    def check_circular_imports(
        module_name: str, visited: set[str] | None = None
    ) -> list[str]:
        """Check for circular imports in a module."""
        if visited is None:
            visited = set()

        if module_name in visited:
            return [module_name]

        visited.add(module_name)
        circular_deps = []

        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.ismodule(obj):
                    deps = ImportValidator.check_circular_imports(
                        obj.__name__, visited.copy()
                    )
                    if deps:
                        circular_deps.extend(deps)
        except Exception:
            pass

        return circular_deps


class ImportProfiler:
    """Profiles import performance and usage."""

    def __init__(self):
        self.metrics = MetricsManager.get_instance()
        self.import_times: dict[str, float] = {}
        self.import_counts: dict[str, int] = {}

    def start_import(self, module_name: str) -> float:
        """Start timing an import."""
        return time.time()

    def end_import(self, module_name: str, start_time: float):
        """End timing an import and record metrics."""
        duration = time.time() - start_time
        self.import_times[module_name] = duration
        self.import_counts[module_name] = self.import_counts.get(module_name, 0) + 1

        self.metrics.record_metric("import_duration", duration, {"module": module_name})
        self.metrics.record_metric("import_count", 1, {"module": module_name})


class ImportManager:
    """Manages imports and dependencies."""

    _instance = None

    def __new__(cls) -> "ImportManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self.modules: dict[str, ImportMetadata] = {}
            self.validator = ImportValidator()
            self.profiler = ImportProfiler()

    def register_module(
        self, module_name: str, import_type: ImportType = ImportType.DIRECT
    ) -> ImportMetadata:
        """Register a module with the manager."""
        if module_name in self.modules:
            return self.modules[module_name]

        start_time = self.profiler.start_import(module_name)
        try:
            module = importlib.import_module(module_name)
            path = Path(module.__file__) if hasattr(module, "__file__") else None
            size = path.stat().st_size if path else 0

            metadata = ImportMetadata(
                name=module_name,
                path=path,
                type=import_type,
                import_time=0.0,
                size=size,
                is_package=hasattr(module, "__path__"),
            )

            self.modules[module_name] = metadata
            self.profiler.end_import(module_name, start_time)
            return metadata

        except Exception as e:
            raise ImportError(f"Failed to register module {module_name}: {e!s}")

    def lazy_import(self, module_name: str) -> type[T]:
        """Lazily import a module."""
        return self.register_module(module_name, ImportType.LAZY)

    def get_dependencies(self, module_name: str) -> set[str]:
        """Get dependencies for a module."""
        if module_name not in self.modules:
            self.register_module(module_name)
        return self.modules[module_name].dependencies

    def check_circular_imports(self, module_name: str) -> list[str]:
        """Check for circular imports in a module."""
        return self.validator.check_circular_imports(module_name)

    def validate_imports(self, module_name: str) -> bool:
        """Validate imports for a module."""
        return self.validator.validate_module_structure(module_name)

    def get_import_stats(self, module_name: str) -> dict[str, float | int]:
        """Get import statistics for a module."""
        if module_name not in self.modules:
            return {}

        metadata = self.modules[module_name]
        return {
            "import_time": metadata.import_time,
            "size": metadata.size,
            "import_count": self.profiler.import_counts.get(module_name, 0),
        }


def get_import_manager() -> ImportManager:
    """Get the global ImportManager instance."""
    return ImportManager()
