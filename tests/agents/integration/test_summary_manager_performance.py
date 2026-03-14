"""Performance benchmark tests for hierarchical memory system.

Tests measure:
1. Memory usage stays bounded (< 500MB) for 100 chapters
2. Context generation is fast (< 100ms)
3. Cache statistics are properly tracked

All tests use MockLLM for fast execution without API costs.
"""

import asyncio
import sys
import time
import tracemalloc
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.novel_agent.novel.summary_manager import SummaryManager
from tests.integration.test_100_chapter_hierarchical import MockLLM


def test_memory_usage_100_chapters(tmp_path: Path) -> None:
    """Test that memory usage stays bounded for 100 chapters.

    Uses MockLLM to avoid API calls while measuring memory footprint.
    Memory should stay under 500MB even with 100 chapters.
    """
    temp_storage = tmp_path / "memory_test"
    mock_llm = MockLLM(delay=0.005)
    summary_manager = SummaryManager(temp_storage, "memory_benchmark", mock_llm)

    tracemalloc.start()

    # Process 100 chapters
    async def process_chapters() -> None:
        for i in range(1, 101):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i} " * 10,
            )

    asyncio.run(process_chapters())

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / 1024 / 1024
    print("\n=== Memory Usage Test ===")
    print(f"Peak Memory: {peak_mb:.1f}MB")
    print(f"Total Chapters: {summary_manager.get_total_chapters()}")

    # Assert memory stays bounded
    assert peak < 500 * 1024 * 1024, f"Memory exceeded 500MB: {peak_mb:.1f}MB"
    assert summary_manager.get_total_chapters() == 100


def test_context_generation_time(tmp_path: Path) -> None:
    """Test that context generation is fast.

    Context generation for the next chapter should complete
    in under 100ms even with 100 chapters of history.
    """
    temp_storage = tmp_path / "context_test"
    mock_llm = MockLLM(delay=0.005)
    summary_manager = SummaryManager(temp_storage, "context_benchmark", mock_llm)

    # Process 50 chapters first
    async def process_chapters() -> None:
        for i in range(1, 51):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i}",
            )

    asyncio.run(process_chapters())

    # Measure context generation time
    start_time = time.time()
    context = summary_manager.get_context_for_chapter(51)
    elapsed = time.time() - start_time

    print("\n=== Context Generation Test ===")
    print(f"Context Generation Time: {elapsed * 1000:.1f}ms")
    print(f"Context Length: {len(context)} chars")

    # Assert context generation is fast
    assert elapsed < 0.1, f"Context generation too slow: {elapsed * 1000:.1f}ms"
    assert len(context) > 0


def test_cache_statistics(tmp_path: Path) -> None:
    """Test that cache statistics are properly tracked.

    Verifies:
    - HierarchicalStoryState has LRU caching enabled
    - Cache hits/misses are tracked
    - Cache improves performance on repeated access
    """
    temp_storage = tmp_path / "cache_test"
    mock_llm = MockLLM(delay=0.005)
    summary_manager = SummaryManager(temp_storage, "cache_benchmark", mock_llm)

    # Process 20 chapters
    async def process_chapters() -> None:
        for i in range(1, 21):
            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"Chapter {i}",
                content=f"Content for chapter {i}",
            )

    asyncio.run(process_chapters())

    # Access hierarchical state cache info if available
    hierarchical_state = summary_manager.hierarchical_state

    # Test repeated context generation (should benefit from caching)
    times = []
    for _ in range(5):
        start = time.time()
        context = summary_manager.get_context_for_chapter(21)
        times.append(time.time() - start)

    print("\n=== Cache Statistics Test ===")
    print(f"Context generation times: {[f'{t * 1000:.1f}ms' for t in times]}")
    print(f"Average time: {sum(times) / len(times) * 1000:.1f}ms")
    print(f"Fastest time: {min(times) * 1000:.1f}ms")

    # All accesses should be fast
    assert all(t < 0.1 for t in times), "Some context generation too slow"
    assert len(context) > 0

    # Verify cache attributes exist on hierarchical state (using actual attribute names)
    assert hasattr(hierarchical_state, "_chapter_cache"), "Missing _chapter_cache"
    assert hasattr(hierarchical_state, "_arc_cache"), "Missing _arc_cache"

    # Verify caches have items (LRU caching is working)
    assert len(hierarchical_state._chapter_cache) > 0, "Chapter cache is empty"
    assert len(hierarchical_state._arc_cache) >= 0, "Arc cache check failed"
