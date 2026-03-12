#!/usr/bin/env python3
"""Script to register all existing chapters into StoryRegistry."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from novel.registry.story_registry import StoryRegistry
from novel.validators import NovelValidator


def register_existing_chapters(novel_id: str, storage_path: Path) -> dict:
    """Register all existing chapters from files into the registry.

    Args:
        novel_id: Novel identifier
        storage_path: Base storage path

    Returns:
        Dictionary with registration results
    """
    registry = StoryRegistry(novel_id, storage_path)
    chapters_dir = storage_path / novel_id / "chapters"

    if not chapters_dir.exists():
        print(f"Chapters directory not found: {chapters_dir}")
        return {"success": False, "error": "Chapters directory not found"}

    # Get all chapter files
    chapter_files = sorted(chapters_dir.glob("chapter_*.md"))

    print(f"Found {len(chapter_files)} chapter files")
    print(f"Currently registered chapters: {list(registry._chapters.keys())}")

    registered = []
    failed = []

    for chapter_file in chapter_files:
        # Extract chapter number from filename
        chapter_num = int(chapter_file.stem.split("_")[1])

        # Skip if already registered
        if registry.chapter_exists(chapter_num):
            print(f"Chapter {chapter_num} already registered, skipping...")
            continue

        # Read chapter content
        try:
            with open(chapter_file, encoding="utf-8") as f:
                content = f.read()

            # Extract title from first line
            lines = content.split("\n")
            title = lines[0] if lines else f"Chapter {chapter_num}"

            # Get word count (simple approximation)
            word_count = len(content.split())

            # Quality score (default to 8.0 for existing chapters)
            quality_score = 8.0

            # State snapshot ID (placeholder)
            state_snapshot_id = f"snap_{chapter_num:04d}"

            # Register chapter
            success = registry.register_chapter(
                number=chapter_num,
                title=title,
                content=content,
                quality_score=quality_score,
                state_snapshot_id=state_snapshot_id,
            )

            if success:
                registered.append(chapter_num)
                print(f"✓ Registered chapter {chapter_num}: {title[:50]}")
            else:
                failed.append(chapter_num)
                print(f"✗ Failed to register chapter {chapter_num}")

        except Exception as e:
            failed.append(chapter_num)
            print(f"✗ Error registering chapter {chapter_num}: {e}")

    # Get final stats
    stats = registry.get_stats()

    print("\n=== Registration Summary ===")
    print(f"Total chapters found: {len(chapter_files)}")
    print(f"Successfully registered: {len(registered)}")
    print(f"Failed: {len(failed)}")
    print(f"Now registered in total: {stats['total_chapters']}")
    print(f"Missing chapters up to 10: {registry.get_missing_chapters(10)}")

    return {"success": True, "registered": registered, "failed": failed, "stats": stats}


def main():
    """Main entry point."""
    novel_id = "user_novel_001"
    storage_path = Path("data/novels")

    print(f"Registering chapters for novel: {novel_id}")
    print(f"Storage path: {storage_path}")
    print("=" * 60)

    result = register_existing_chapters(novel_id, storage_path)

    if result["success"]:
        print("\n✓ Registration completed successfully!")

        # Now validate the novel
        print("\n" + "=" * 60)
        print("Validating novel...")
        print("=" * 60)

        validator = NovelValidator(novel_id, storage_path)
        issues = validator.validate_all_chapters()

        if issues:
            print(f"\n⚠ Found {len(issues)} validation issues:")
            for issue in issues:
                print(f"  - Chapter {issue['chapter']}: {issue['type']} ({issue['severity']})")
                print(f"    {issue['description']}")
        else:
            print("\n✓ No validation issues found!")
    else:
        print(f"\n✗ Registration failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
