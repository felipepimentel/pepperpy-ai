"""Performance tests for the news podcast example.

Tests performance characteristics:
1. Response times
2. Memory usage
3. Concurrent operations
4. Resource cleanup
"""

import asyncio
import logging
import time

import psutil
import pytest

from examples.news_podcast import NewsPodcastGenerator

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def test_output_dir(tmp_path):
    """Provide test output directory."""
    output_dir = tmp_path / "podcasts"
    output_dir.mkdir()
    return output_dir


@pytest.mark.performance
@pytest.mark.asyncio
async def test_fetch_news_performance(test_output_dir):
    """Test news fetching performance."""
    generator = NewsPodcastGenerator(output_dir=test_output_dir)
    await generator.initialize()
    try:
        # Measure fetch time
        start_time = time.time()
        articles = await generator.fetch_news(limit=5)
        duration = time.time() - start_time

        # Verify performance
        assert duration < 5.0, f"Fetch took too long: {duration:.2f}s"
        assert len(articles) > 0

    finally:
        await generator.cleanup()


@pytest.mark.performance
@pytest.mark.asyncio
async def test_script_generation_performance(test_output_dir):
    """Test script generation performance."""
    generator = NewsPodcastGenerator(output_dir=test_output_dir)
    await generator.initialize()
    try:
        # Get test articles
        articles = await generator.fetch_news(limit=3)

        # Measure generation time
        start_time = time.time()
        script = await generator.generate_script(articles)
        duration = time.time() - start_time

        # Verify performance
        assert duration < 10.0, f"Generation took too long: {duration:.2f}s"
        assert script is not None

    finally:
        await generator.cleanup()


@pytest.mark.performance
@pytest.mark.asyncio
async def test_audio_synthesis_performance(test_output_dir):
    """Test audio synthesis performance."""
    generator = NewsPodcastGenerator(output_dir=test_output_dir)
    await generator.initialize()
    try:
        # Get test script
        articles = await generator.fetch_news(limit=2)
        script = await generator.generate_script(articles)

        # Measure synthesis time
        start_time = time.time()
        output_path = await generator.create_podcast(script)
        duration = time.time() - start_time

        # Verify performance
        assert duration < 30.0, f"Synthesis took too long: {duration:.2f}s"
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    finally:
        await generator.cleanup()


@pytest.mark.performance
@pytest.mark.asyncio
async def test_memory_usage_under_load(test_output_dir):
    """Test memory usage under load."""
    process = psutil.Process()
    generator = NewsPodcastGenerator(output_dir=test_output_dir)
    await generator.initialize()
    try:
        # Measure initial memory
        initial_memory = process.memory_info().rss

        # Generate multiple podcasts
        for _ in range(3):
            await generator.generate()

        # Measure final memory
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # Verify memory usage
        assert memory_increase < 500, f"Memory increase too high: {memory_increase}MB"

    finally:
        await generator.cleanup()


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_operations(test_output_dir):
    """Test performance of concurrent operations."""

    async def generate_podcast(index: int):
        output_dir = test_output_dir / f"gen{index}"
        output_dir.mkdir()
        generator = NewsPodcastGenerator(output_dir=output_dir)
        await generator.initialize()
        try:
            start_time = time.time()
            path = await generator.generate()
            duration = time.time() - start_time
            return path, duration
        finally:
            await generator.cleanup()

    # Run concurrent generations
    start_time = time.time()
    results = await asyncio.gather(*[generate_podcast(i) for i in range(3)])
    total_duration = time.time() - start_time

    # Verify performance
    assert total_duration < 90.0, f"Total time too high: {total_duration:.2f}s"
    for path, duration in results:
        assert duration < 60.0, f"Individual generation too slow: {duration:.2f}s"
        assert path.exists()


@pytest.mark.performance
@pytest.mark.asyncio
async def test_cache_performance(test_output_dir):
    """Test caching performance."""
    generator = NewsPodcastGenerator(output_dir=test_output_dir)
    await generator.initialize()
    try:
        # First run - no cache
        start_time = time.time()
        articles1 = await generator.fetch_news()
        uncached_duration = time.time() - start_time

        # Second run - with cache
        start_time = time.time()
        articles2 = await generator.fetch_news()
        cached_duration = time.time() - start_time

        # Verify cache improves performance
        assert cached_duration < uncached_duration * 0.5, (
            f"Cache not effective: uncached={uncached_duration:.2f}s, "
            f"cached={cached_duration:.2f}s"
        )
        assert articles1 == articles2

    finally:
        await generator.cleanup()


@pytest.mark.performance
@pytest.mark.asyncio
async def test_resource_cleanup_performance(test_output_dir):
    """Test resource cleanup performance."""
    generator = NewsPodcastGenerator(output_dir=test_output_dir)
    await generator.initialize()

    # Generate some data
    await generator.generate()

    # Measure cleanup time
    start_time = time.time()
    await generator.cleanup()
    duration = time.time() - start_time

    # Verify cleanup performance
    assert duration < 2.0, f"Cleanup took too long: {duration:.2f}s"


@pytest.mark.performance
@pytest.mark.asyncio
async def test_initialization_performance(test_output_dir):
    """Test initialization performance."""
    generator = NewsPodcastGenerator(output_dir=test_output_dir)

    # Measure initialization time
    start_time = time.time()
    await generator.initialize()
    duration = time.time() - start_time

    try:
        # Verify initialization performance
        assert duration < 3.0, f"Initialization took too long: {duration:.2f}s"
    finally:
        await generator.cleanup()
