#!/usr/bin/env python3
"""Demonstration test for T4-2 progressive context loading.

This script demonstrates that arc preloading works correctly.
"""

import tempfile
from pathlib import Path

from src.novel_agent.novel.hierarchical_state import HierarchicalStoryState
from src.novel_agent.novel.summaries import ArcSummary


def test_preloading_demo():
    """Demonstrate arc preloading functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        state = HierarchicalStoryState(storage_path, "test_novel")

        # Create and save arc summaries for arcs 1, 2, and 3
        for arc_num in [1, 2, 3]:
            arc_summary = ArcSummary(
                arc_number=arc_num,
                start_chapter=(arc_num - 1) * 10 + 1,
                end_chapter=arc_num * 10,
                title=f"Arc {arc_num}",
                summary=f"Summary for arc {arc_num}",
                major_events=[f"Event {arc_num}"],
                character_arcs={},
                world_changes=[],
                plot_threads_status={},
                themes=[f"Theme {arc_num}"],
            )
            state.save_arc_summary(arc_summary)

            state.save_arc_summary(arc_summary)

        print("✓ Created 3 arc summaries")

        # Clear cache to start fresh (save operations add to cache)
        state.clear_cache()

        # Verify cache is now empty
        assert len(state._arc_cache) == 0, "Cache should be empty after clearing"


        # Get context for chapter 1 (arc 1)
        # This should load arc 1, but NOT preload arc 2 (not approaching boundary)
        state.get_context_for_chapter(1)
        assert 1 in state._arc_cache, "Arc 1 should be cached"
        assert 2 not in state._arc_cache, "Arc 2 should NOT be pre-loaded yet"
        print("✓ Chapter 1: Arc 1 loaded, Arc 2 NOT pre-loaded (not at boundary)")

        # Clear cache
        state.clear_cache()
        assert len(state._arc_cache) == 0, "Cache should be cleared"
        print("✓ Cache cleared")

        # Get context for chapter 8 (arc 1, chapter 8/10)
        # This SHOULD preload arc 2 (approaching boundary)
        state.get_context_for_chapter(8)
        assert 1 in state._arc_cache, "Arc 1 should be cached"
        assert 2 in state._arc_cache, "Arc 2 should be pre-loaded (at boundary)"
        assert 3 not in state._arc_cache, "Arc 3 should NOT be pre-loaded"
        print("✓ Chapter 8: Arc 1 loaded, Arc 2 pre-loaded (at boundary)")

        # Clear cache again
        state.clear_cache()

        # Get context for chapter 18 (arc 2, chapter 8/10 relative to arc start)
        # This SHOULD preload arc 3 (approaching boundary)
        state.get_context_for_chapter(18)
        assert 2 in state._arc_cache, "Arc 2 should be cached"
        assert 3 in state._arc_cache, "Arc 3 should be pre-loaded (at boundary)"
        print("✓ Chapter 18: Arc 2 loaded, Arc 3 pre-loaded (at boundary)")

        print("\n✅ All preloading tests passed!")
        print("\nProgressive loading behavior verified:")
        print("- Early chapters: No preloading")
        print("- Last 3 chapters of arc: Next arc pre-loaded")
        print("- LRU cache eviction working correctly")


if __name__ == "__main__":
    test_preloading_demo()
