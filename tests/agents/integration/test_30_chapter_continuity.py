"""Integration test for 30-chapter novel generation with continuity tracking.

This script tests the continuity system by:
1. Creating a detailed 30-chapter outline with character state changes
2. Generating chapters with continuity context
3. Validating each chapter for continuity issues
4. Reporting any problems found

Test scenarios:
- Sylas dies in Chapter 4 (should not appear alive after)
- Aurelion fuses with Kael in Chapter 5 (should not have physical form after)
- Character relationship progression
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.novel_agent.agents.writers.fantasy import FantasyWriter
from src.novel_agent.llm.deepseek import DeepSeekLLM
from src.novel_agent.novel.continuity import CharacterState, ContinuityManager, PlotThread, StoryState
from src.novel_agent.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel_agent.novel.validators import ContinuityValidator


def create_test_outline() -> DetailedOutline:
    """Create a detailed 30-chapter outline with continuity events."""
    chapters = []

    # Chapters 1-4: Aurelion has physical form, Sylas is alive
    for i in range(1, 5):
        chapters.append(
            ChapterSpec(
                number=i,
                title=f"Chapter {i}: {'The Beginning' if i == 1 else 'The Journey Continues' if i == 2 else 'Growing Power' if i == 3 else 'Sacrifice'}",
                summary=f"""
            Chapter {i} events:
            - Kael and Lyra continue their training at the Academy
            - Aurelion guides them with his ancient wisdom
            - Sylas teaches combat techniques
            {"- Sylas sacrifices himself to save Kael from the dark mage" if i == 4 else ""}
            """,
                characters=["Kael", "Lyra", "Aurelion"] + (["Sylas"] if i < 4 else []),
                location="Academy",
                key_events=[
                    f"Training session {i}",
                    "Aurelion shares dragon lore" if i < 5 else "",
                    "Sylas's final stand" if i == 4 else "",
                ],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={
                    "Kael": "alive",
                    "Lyra": "alive",
                    "Aurelion": "alive" if i < 5 else "fused",
                    **({"Sylas": "alive"} if i < 4 else {"Sylas": "dead"}),
                },
            )
        )

    # Chapter 5: Aurelion fuses with Kael, Sylas is dead
    chapters.append(
        ChapterSpec(
            number=5,
            title="Chapter 5: The Fusion",
            summary="""
        Chapter 5 events:
        - Aurelion sacrifices his physical form to save Kael
        - Aurelion's spirit merges with Kael's body
        - Kael gains dragon-like abilities
        - The group mourns Sylas's death
        """,
            characters=["Kael", "Lyra"],  # Aurelion is now fused, Sylas is dead
            location="Inner Sanctum",
            key_events=[
                "Aurelion fuses with Kael",
                "Kael transforms",
                "Mourning Sylas",
            ],
            plot_threads_resolved=["Dragon awakening"],
            plot_threads_started=["Kael's new power"],
            character_states={
                "Kael": "alive",
                "Lyra": "alive",
                "Aurelion": "fused",
                "Sylas": "dead",
            },
        )
    )

    # Chapters 6-30: Aurelion is fused, Sylas is dead
    for i in range(6, 31):
        # Vary the story progression
        if i <= 10:
            stage = "Training with new powers"
            location = "Academy"
        elif i <= 15:
            stage = "First adventures"
            location = "Enchanted Forest"
        elif i <= 20:
            stage = "Growing conflict"
            location = "Kingdom of Eldoria"
        elif i <= 25:
            stage = "Dark times"
            location = "Shadow Lands"
        else:
            stage = "Final confrontation"
            location = "Dragon's Peak"

        chapters.append(
            ChapterSpec(
                number=i,
                title=f"Chapter {i}: {stage}",
                summary=f"""
            Chapter {i} events:
            - Kael uses his fused powers with Aurelion's guidance
            - Lyra supports Kael through challenges
            - {stage} continues
            - No mention of Sylas (he's dead) or Aurelion's physical form (fused)
            """,
                characters=["Kael", "Lyra"],  # Only these two should appear
                location=location,
                key_events=[
                    "Kael uses dragon powers",
                    f"Progress in {stage.lower()}",
                ],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={
                    "Kael": "alive",
                    "Lyra": "alive",
                    "Aurelion": "fused",
                    "Sylas": "dead",
                },
            )
        )

    return DetailedOutline(chapters=chapters)


async def test_30_chapter_novel():
    """Run a 30-chapter novel generation test with continuity validation."""
    print("=" * 60)
    print("30-Chapter Novel Generation Test with Continuity Tracking")
    print("=" * 60)
    print()

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/continuity_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # Initialize components
    print("Initializing components...")
    llm = DeepSeekLLM()
    writer = FantasyWriter(name="Test Fantasy Writer", llm=llm)
    continuity = ContinuityManager()
    validator = ContinuityValidator()
    print("✓ Components initialized")
    print()

    # Create test outline
    print("Creating 30-chapter test outline...")
    outline = create_test_outline()
    print(f"✓ Outline created with {len(outline.chapters)} chapters")

    # Validate outline itself
    outline_errors = outline.validate()
    if outline_errors:
        print("⚠ Outline validation errors:")
        for error in outline_errors:
            print(f"  - {error}")
    else:
        print("✓ Outline validation passed")
    print()

    # Initialize story state
    current_state = StoryState(
        chapter=0,
        location="Academy",
        active_characters=["Kael", "Lyra", "Aurelion", "Sylas"],
        character_states={
            "Kael": CharacterState(
                name="Kael",
                status="alive",
                location="Academy",
                physical_form="human",
                relationships={"Lyra": "friend", "Aurelion": "mentor", "Sylas": "teacher"},
            ),
            "Lyra": CharacterState(
                name="Lyra",
                status="alive",
                location="Academy",
                physical_form="human",
                relationships={"Kael": "friend"},
            ),
            "Aurelion": CharacterState(
                name="Aurelion",
                status="alive",
                location="Academy",
                physical_form="dragon",
                relationships={"Kael": "student"},
            ),
            "Sylas": CharacterState(
                name="Sylas",
                status="alive",
                location="Academy",
                physical_form="human",
                relationships={"Kael": "student"},
            ),
        },
        plot_threads=[
            PlotThread(name="Dragon awakening", status="active"),
        ],
        key_events=[],
    )

    # Track validation results
    all_validation_results = []
    continuity_errors = []

    # Generate chapters
    print("Generating chapters...")
    print("-" * 60)

    for chapter_spec in outline.chapters:
        chapter_num = chapter_spec.number
        print(f"\nChapter {chapter_num}: {chapter_spec.title}")

        # Build previous summary
        previous_summary = None
        if current_state.key_events:
            previous_summary = "; ".join(current_state.key_events[-3:])

        # Validate state before generation
        pre_validation = validator.validate_chapter(
            chapter_content="",  # Will be generated
            chapter_number=chapter_num,
            story_state=current_state,
            chapter_spec=chapter_spec,
        )

        # Check for state mismatches with outline
        for char_name, expected_status in chapter_spec.character_states.items():
            current_char = current_state.get_character_state(char_name)
            if current_char and current_char.status != expected_status:
                # Update state to match outline
                current_char.status = expected_status
                if expected_status == "dead":
                    if char_name in current_state.active_characters:
                        current_state.active_characters.remove(char_name)
                elif expected_status == "fused":
                    if char_name in current_state.active_characters:
                        current_state.active_characters.remove(char_name)

        try:
            # Generate chapter content
            content = await writer.write_chapter_with_context(
                chapter_spec=chapter_spec,
                story_state=current_state,
                characters=[
                    {"name": c, "status": chapter_spec.character_states.get(c, "alive")}
                    for c in chapter_spec.characters
                ],
                world_context={"setting": "fantasy academy", "genre": "fantasy"},
                previous_chapter_summary=previous_summary,
            )

            # Validate generated content
            post_validation = validator.validate_chapter(
                chapter_content=content,
                chapter_number=chapter_num,
                story_state=current_state,
                chapter_spec=chapter_spec,
            )

            all_validation_results.append(
                {
                    "chapter": chapter_num,
                    "pre_errors": len(pre_validation.errors),
                    "post_errors": len(post_validation.errors),
                    "post_warnings": len(post_validation.warnings),
                    "content_length": len(content),
                }
            )

            # Report validation issues
            if post_validation.errors:
                print("  ⚠ Validation errors:")
                for error in post_validation.errors:
                    print(f"    - {error.message}")
                    continuity_errors.append(
                        {
                            "chapter": chapter_num,
                            "type": "error",
                            "message": error.message,
                        }
                    )

            if post_validation.warnings:
                print("  ⚡ Warnings:")
                for warning in post_validation.warnings:
                    print(f"    - {warning.message}")

            # Update state from content
            current_state = continuity.update_from_chapter(
                current_state,
                content,
                chapter_num,
            )

            # Save chapter
            chapter_file = output_dir / f"chapter_{chapter_num:03d}.txt"
            with open(chapter_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"  ✓ Generated {len(content)} characters")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            continuity_errors.append(
                {
                    "chapter": chapter_num,
                    "type": "generation_error",
                    "message": str(e),
                }
            )

    # Save final state and results
    print("\n" + "=" * 60)
    print("Saving results...")

    # Save story state
    state_file = output_dir / "story_state.json"
    state_dict = continuity.save(current_state)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_dict, f, indent=2)
    print(f"✓ Story state saved to {state_file}")

    # Save validation results
    results_file = output_dir / "validation_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "validation_results": all_validation_results,
                "continuity_errors": continuity_errors,
            },
            f,
            indent=2,
        )
    print(f"✓ Validation results saved to {results_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total chapters generated: {len(outline.chapters)}")
    print(f"Total validation errors: {len(continuity_errors)}")

    # Analyze by chapter range
    early_errors = [e for e in continuity_errors if e["chapter"] <= 5]
    mid_errors = [e for e in continuity_errors if 5 < e["chapter"] <= 20]
    late_errors = [e for e in continuity_errors if e["chapter"] > 20]

    print("\nErrors by chapter range:")
    print(f"  Chapters 1-5:   {len(early_errors)} errors")
    print(f"  Chapters 6-20:  {len(mid_errors)} errors")
    print(f"  Chapters 21-30: {len(late_errors)} errors")

    # Check for specific continuity issues
    dead_character_appearances = [
        e
        for e in continuity_errors
        if "dead" in e["message"].lower() and "appears" in e["message"].lower()
    ]
    fused_character_issues = [
        e
        for e in continuity_errors
        if "fused" in e["message"].lower() and "physical" in e["message"].lower()
    ]

    print("\nSpecific issue detection:")
    print(f"  Dead character appearances: {len(dead_character_appearances)}")
    print(f"  Fused character physical form issues: {len(fused_character_issues)}")

    if continuity_errors:
        print("\n⚠ CONTINUITY ISSUES FOUND - System needs improvement")
    else:
        print("\n✓ NO CONTINUITY ISSUES - System working correctly!")

    print(f"\nOutput directory: {output_dir}")

    return len(continuity_errors) == 0


if __name__ == "__main__":
    success = asyncio.run(test_30_chapter_novel())
    sys.exit(0 if success else 1)
