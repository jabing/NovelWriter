#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""quick_status.py - Quick chapter status checker"""

from pathlib import Path
import sys


def get_chapter_status(novel_name: str = "gilded_cage") -> None:
    """Check chapter status for a novel."""
    chapters_dir = Path(f"data/openviking/memory/novels/{novel_name}/chapters")

    if not chapters_dir.exists():
        print(f"Project not found: {novel_name}")
        return

    cn_chapters = sorted([f for f in chapters_dir.glob("chapter_*.md") if "_en" not in f.name])
    en_chapters = sorted([f for f in chapters_dir.glob("chapter_*_en.md")])

    print()
    print("=" * 50)
    print(f"Project: {novel_name}")
    print("=" * 50)
    print(f"Chinese chapters: {len(cn_chapters)}")
    print(f"English chapters: {len(en_chapters)}")
    print()

    if cn_chapters:
        print("Chinese chapters:")
        for ch in cn_chapters:
            size = ch.stat().st_size
            words = size // 3
            print(f"  {ch.stem}: ~{words} chars")

    if en_chapters:
        print()
        print("English chapters:")
        for ch in en_chapters:
            size = ch.stat().st_size
            words = size // 4
            print(f"  {ch.stem}: ~{words} words")

    print()
    total = 350
    print(f"Progress: {len(cn_chapters)}/{total} chapters ({len(cn_chapters)/total*100:.1f}%)") 


def read_chapter(novel_name: str, chapter_num: int, max_lines: int = 50) -> None:
    """Read a chapter content."""
    chapter_file = Path(f"data/openviking/memory/novels/{novel_name}/chapters/chapter_{chapter_num:03d}.md")

    if not chapter_file.exists():
        print(f"Chapter {chapter_num} not found")
        return

    with open(chapter_file, "r", encoding="utf-8") as f:
        content = f.read()
        content_lines = content.split("
")

    print()
    print("=" * 50)
    print(f"Chapter {chapter_num}: {novel_name}")
    print("=" * 50)

    for i, line in enumerate(content_lines[:max_lines], 1):
        print(f"{i:3}: {line}")

    if len(content_lines) > max_lines:
        print()
        print(f"... ({len(content_lines) - max_lines} more lines)")
        print(f"Total: {len(content)} characters")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        get_chapter_status("gilded_cage")
    elif sys.argv[1] == "read":
        chapter = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        read_chapter("gilded_cage", chapter)
    else:
        get_chapter_status(sys.argv[1])
