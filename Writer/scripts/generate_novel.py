"""Script to generate a complete novel with continuity tracking."""

import argparse
import asyncio
import json
import os

from src.agents.writers.fantasy import FantasyWriter
from src.llm.deepseek import DeepSeekLLM
from src.novel.continuity import ContinuityManager, StoryState
from src.novel.outline_generator import OutlineGenerator
from src.novel.outline_manager import ChapterSpec, DetailedOutline


async def generate_novel(
    idea: str,
    target_chapters: int = 30,
    output_dir: str = "output",
    use_intelligent_outline: bool = True,
) -> None:
    """Generate a complete novel with continuity tracking.

    Args:
        idea: Story idea or concept
        target_chapters: Number of chapters to generate
        output_dir: Output directory for chapters
        use_intelligent_outline: Use LLM-based intelligent outline generation
    """
    print(f"Generating {target_chapters}-chapter novel for: {idea}")
    print(f"Output directory: {output_dir}")
    print(f"Intelligent outline: {use_intelligent_outline}")

    # Initialize components
    llm = DeepSeekLLM()
    writer = FantasyWriter(name="Novel Writer", llm=llm)
    continuity = ContinuityManager()

    # Step 1: Create outline
    print("Step 1: Creating outline...")

    if use_intelligent_outline:
        # Use intelligent outline generator
        outline_generator = OutlineGenerator(llm)
        detailed_chapters = await outline_generator.generate_outline(idea, target_chapters)

        if not detailed_chapters:
            print("  Warning: Intelligent outline generation failed, using simple outline")
            detailed_chapters = outline_generator._create_simple_outline(idea, target_chapters)

        # Convert DetailedChapterSpec to ChapterSpec for compatibility
        chapters = []
        for dc in detailed_chapters:
            chapter = ChapterSpec(
                number=dc.number,
                title=dc.title,
                summary=dc.summary,
                characters=dc.characters,
                location=dc.location,
                key_events=dc.key_events,
                plot_threads_resolved=dc.plot_threads_resolved,
                plot_threads_started=dc.plot_threads_started,
                character_states=dc.state_changes,
            )
            chapters.append(chapter)

        print(f"  Generated {len(chapters)} chapters with intelligent outline")
    else:
        # Use simple outline
        chapters = []
        for i in range(1, target_chapters + 1):
            chapter = ChapterSpec(
                number=i,
                title=f"Chapter {i}",
                summary=f"Events of chapter {i} in the story about: {idea}",
                characters=["Protagonist"],
                location="Various",
                key_events=[f"Event {i}"],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={"Protagonist": "alive"},
            )
            chapters.append(chapter)
        print(f"  Created {len(chapters)} chapters with simple outline")

    outline = DetailedOutline(chapters=chapters)

    # Step 2: Generate chapters with continuity
    print(f"Step 2: Generating {target_chapters} chapters...")

    current_state = None

    for chapter_spec in outline.chapters:
        print(f"  Generating Chapter {chapter_spec.number}...")

        # Apply state changes from outline before generation
        if current_state and chapter_spec.character_states:
            for char_name, new_status in chapter_spec.character_states.items():
                if char_name in current_state.character_states:
                    old_status = current_state.character_states[char_name].status
                    if old_status != new_status:
                        print(f"    Outline state change: {char_name} {old_status} -> {new_status}")
                        current_state.character_states[char_name].status = new_status

        # Generate chapter with continuity context
        previous_summary = None
        if current_state and current_state.key_events:
            previous_summary = "; ".join(current_state.key_events[-3:])

        content = await writer.write_chapter_with_context(
            chapter_spec=chapter_spec,
            story_state=current_state,
            characters=[{"name": name} for name in chapter_spec.characters],
            world_context={"setting": "fantasy"},
            previous_chapter_summary=previous_summary,
        )

        # Update state with NLP detection
        current_state = continuity.update_from_chapter(
            current_state
            or StoryState(
                chapter=0,
                location=chapter_spec.location,
                active_characters=[],
                character_states={},
                plot_threads=[],
                key_events=[],
            ),
            content,
            chapter_spec.number,
            known_characters=chapter_spec.characters,  # Use outline characters as whitelist
        )

        # Detect and report state changes from content
        detected_changes = continuity._detect_state_changes(content)
        if detected_changes:
            print(f"    Detected {len(detected_changes)} state changes from content:")
            for change in detected_changes:
                print(f"      - {change.character}: {change.old_state} -> {change.new_state}")
                # Apply detected changes to state
                if change.character in current_state.character_states:
                    if change.new_state in ["dead", "fused", "captured"]:
                        current_state.character_states[change.character].status = change.new_state

        # Save chapter
        os.makedirs(output_dir, exist_ok=True)
        chapter_file = os.path.join(output_dir, f"chapter_{chapter_spec.number:03d}.txt")
        with open(chapter_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"    Saved to {chapter_file}")

    # Save final state
    state_file = os.path.join(output_dir, "story_state.json")
    state_dict = continuity.save(current_state)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_dict, f, indent=2, ensure_ascii=False)

    print("\nNovel generation complete!")
    print(f"   Chapters: {target_chapters}")
    print(f"   Output: {output_dir}")
    print(f"   State: {state_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate a novel with continuity tracking")
    parser.add_argument("idea", help="Story idea or concept")
    parser.add_argument("chapters", nargs="?", type=int, default=30, help="Number of chapters (default: 30)")
    parser.add_argument("output_dir", nargs="?", default="output", help="Output directory (default: output)")
    parser.add_argument("--no-intelligent-outline", action="store_true", help="Disable intelligent outline generation")

    args = parser.parse_args()

    asyncio.run(
        generate_novel(
            idea=args.idea,
            target_chapters=args.chapters,
            output_dir=args.output_dir,
            use_intelligent_outline=not args.no_intelligent_outline,
        )
    )


if __name__ == "__main__":
    main()
