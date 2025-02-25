"""Benchmarks for the import optimization system."""

import sys
import time
from pathlib import Path
from typing import List

import pytest

from pepperpy.core.import_system import ImportCache, ImportOptimizer


def get_test_modules() -> List[str]:
    """Get list of test modules for benchmarking."""
    return [
        "os",
        "sys",
        "time",
        "json",
        "csv",
        "random",
        "hashlib",
        "base64",
        "datetime",
        "calendar",
        "math",
        "statistics",
        "decimal",
        "fractions",
        "pathlib",
        "glob",
        "fnmatch",
        "linecache",
        "shutil",
        "fileinput",
        "stat",
        "filecmp",
        "tempfile",
        "wave",
        "chunk",
        "colorsys",
        "shelve",
        "marshal",
        "dbm",
        "sqlite3",
        "zlib",
        "gzip",
        "bz2",
        "lzma",
        "zipfile",
        "tarfile",
        "csv",
        "configparser",
        "netrc",
        "xdrlib",
    ]


@pytest.mark.benchmark
def test_import_performance(benchmark) -> None:
    """Benchmark import performance."""
    optimizer = ImportOptimizer()
    modules = get_test_modules()

    def import_modules():
        """Import test modules."""
        for module_name in modules:
            if module_name not in sys.modules:
                __import__(module_name)

    # Benchmark without optimizer
    benchmark.pedantic(
        import_modules,
        iterations=10,
        rounds=100,
        warmup_rounds=3,
    )


@pytest.mark.benchmark
def test_import_performance_with_optimizer(benchmark) -> None:
    """Benchmark import performance with optimizer."""
    optimizer = ImportOptimizer()
    modules = get_test_modules()

    def import_modules_with_optimizer():
        """Import test modules with optimizer."""
        for module_name in modules:
            if module_name not in sys.modules:
                module = __import__(module_name)
                optimizer.exec_module(module)

    # Benchmark with optimizer
    benchmark.pedantic(
        import_modules_with_optimizer,
        iterations=10,
        rounds=100,
        warmup_rounds=3,
    )


@pytest.mark.benchmark
def test_cache_performance(benchmark) -> None:
    """Benchmark cache performance."""
    cache = ImportCache(
        max_size=1024 * 1024 * 10,  # 10MB
        max_entries=1000,
        ttl=3600,
    )

    # Pre-fill cache with test modules
    modules = get_test_modules()
    for module_name in modules:
        if module_name not in sys.modules:
            module = __import__(module_name)
            cache.set(module_name, module)

    def access_cache():
        """Access cached modules."""
        for module_name in modules:
            cache.get(module_name)

    # Benchmark cache access
    benchmark.pedantic(
        access_cache,
        iterations=100,
        rounds=1000,
        warmup_rounds=5,
    )


@pytest.mark.benchmark
def test_memory_usage(benchmark) -> None:
    """Benchmark memory usage."""
    import psutil
    import os

    optimizer = ImportOptimizer()
    modules = get_test_modules()
    process = psutil.Process(os.getpid())

    def measure_memory():
        """Measure memory usage during imports."""
        initial_memory = process.memory_info().rss
        
        # Import modules
        for module_name in modules:
            if module_name not in sys.modules:
                module = __import__(module_name)
                optimizer.exec_module(module)
        
        final_memory = process.memory_info().rss
        memory_delta = final_memory - initial_memory
        
        # Memory usage should be reasonable (< 50MB for test modules)
        assert memory_delta < 50 * 1024 * 1024
        return memory_delta

    # Benchmark memory usage
    benchmark.pedantic(
        measure_memory,
        iterations=5,
        rounds=10,
        warmup_rounds=2,
    ) 