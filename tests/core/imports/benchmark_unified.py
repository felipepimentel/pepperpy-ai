"""Benchmarks for the unified import system.

This module provides benchmarks for:
- Import performance
- Cache efficiency
- Memory usage
- Dependency resolution
"""

import sys
import time
from pathlib import Path

import pytest

from pepperpy.core.imports.unified import (
    ImportCache,
    ImportManager,
    ImportMetadata,
    ImportType,
    get_import_manager,
)


@pytest.fixture
def large_module_list() -> list[str]:
    """Create a list of modules for benchmarking."""
    return [
        "os", "sys", "time", "json", "csv", "random",
        "hashlib", "base64", "datetime", "calendar",
        "math", "statistics", "decimal", "fractions",
        "pathlib", "glob", "fnmatch", "linecache",
        "shutil", "fileinput", "stat", "filecmp",
        "tempfile", "wave", "chunk", "colorsys",
        "shelve", "marshal", "dbm", "sqlite3",
        "zlib", "gzip", "bz2", "lzma",
        "zipfile", "tarfile", "csv", "configparser",
        "netrc", "xdrlib", "plistlib", "hashlib",
    ]


def benchmark_import_performance(benchmark, large_module_list):
    """Benchmark import performance."""
    manager = get_import_manager()

    def import_modules():
        for module_name in large_module_list:
            manager.register_module(module_name)

    benchmark(import_modules)


def benchmark_cache_performance(benchmark, large_module_list):
    """Benchmark cache performance."""
    cache = ImportCache(
        max_size=1024 * 1024 * 10,  # 10MB
        max_entries=1000,
        ttl=3600,
    )

    # Pre-fill cache
    for module_name in large_module_list:
        metadata = ImportMetadata(name=module_name)
        cache.set(module_name, sys.modules[module_name], metadata)

    def access_cache():
        for module_name in large_module_list:
            cache.get(module_name)

    benchmark(access_cache)


def benchmark_memory_usage(benchmark, large_module_list):
    """Benchmark memory usage."""
    manager = get_import_manager()

    def measure_memory():
        initial_size = manager.get_all_stats()["total_size"]
        for module_name in large_module_list:
            manager.register_module(module_name)
        final_size = manager.get_all_stats()["total_size"]
        return final_size - initial_size

    benchmark(measure_memory)


def benchmark_lazy_imports(benchmark, large_module_list):
    """Benchmark lazy import performance."""
    manager = get_import_manager()

    def lazy_import_modules():
        modules = []
        for module_name in large_module_list:
            modules.append(manager.lazy_import(module_name))
        return modules

    benchmark(lazy_import_modules)


def benchmark_cache_cleanup(benchmark, large_module_list):
    """Benchmark cache cleanup performance."""
    cache = ImportCache(
        max_size=1024 * 1024,  # 1MB (small to force cleanup)
        max_entries=10,  # Small to force cleanup
        ttl=1,  # 1 second to force expiration
    )

    def cache_cleanup_cycle():
        # Fill cache
        for module_name in large_module_list:
            metadata = ImportMetadata(name=module_name)
            cache.set(module_name, sys.modules[module_name], metadata)

        # Wait for expiration
        time.sleep(1.1)

        # Access cache to trigger cleanup
        for module_name in large_module_list:
            cache.get(module_name)

    benchmark(cache_cleanup_cycle)


def benchmark_dependency_resolution(benchmark, large_module_list):
    """Benchmark dependency resolution performance."""
    manager = get_import_manager()

    def resolve_dependencies():
        deps = set()
        for module_name in large_module_list:
            deps.update(manager.get_dependencies(module_name))
        return deps

    benchmark(resolve_dependencies)


def benchmark_validation(benchmark, large_module_list):
    """Benchmark import validation performance."""
    manager = get_import_manager()

    def validate_modules():
        results = []
        for module_name in large_module_list:
            results.append(manager.validate_imports(module_name))
        return results

    benchmark(validate_modules)