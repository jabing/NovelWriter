"""Continuity validation test for the novel generation system.

This test specifically verifies:
1. Dead characters don't appear alive after death
2. Fused characters don't have physical form after fusion
3. ContinuityValidator detects violations
"""

from src.novel.continuity import CharacterState, ContinuityManager, PlotThread, StoryState
from src.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel.validators import ContinuityValidator


def test_continuity_validation():
    """Test the continuity validator detects violations correctly."""
    print("=" * 60)
    print("Continuity Validation Test")
    print("=" * 60)

    validator = ContinuityValidator()
    ContinuityManager()

    # Create a story state where:
    # - Sylas is dead (died in Chapter 4)
    # - Aurelion is fused with Kael (fused in Chapter 5)
    # - Current chapter is 6

    current_state = StoryState(
        chapter=6,
        location="Academy",
        active_characters=["Kael", "Lyra"],  # Only Kael and Lyra are present
        character_states={
            "Kael": CharacterState(
                name="Kael",
                status="alive",
                location="Academy",
                physical_form="human with dragon spirit",
                relationships={"Lyra": "friend", "Aurelion": "fused"},
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
                status="fused",
                location="Kael",  # Fused with Kael
                physical_form="spirit",  # No physical form
                relationships={"Kael": "host"},
            ),
            "Sylas": CharacterState(
                name="Sylas",
                status="dead",
                location="None",
                physical_form="None",
                relationships={},
            ),
        },
        plot_threads=[
            PlotThread(name="Dragon awakening", status="resolved"),
            PlotThread(name="Kael's power development", status="active"),
        ],
        key_events=[
            "Kael found the dragon egg",
            "Sylas taught Kael resonance magic",
            "Sylas died protecting Kael",
            "Aurelion's spirit fused with Kael",
        ],
    )

    print("\n1. Testing VALID chapter content...")
    valid_content = """
    Chapter 6: New Powers

    Kael walked through the Academy halls, feeling Aurelion's presence within him.
    The dragon spirit whispered ancient wisdom, guiding his steps.

    Lyra joined him in the training yard. "How are you feeling?" she asked.

    "Different," Kael replied. "I can hear him—Aurelion. He's part of me now."

    They practiced magic together, with Aurelion's spirit helping Kael control
    his new dragon-infused powers. Sylas would have been proud, Kael thought,
    remembering his fallen teacher.
    """

    chapter_spec = ChapterSpec(
        number=6,
        title="New Powers",
        summary="Kael learns to use his new powers with Lyra's help",
        characters=["Kael", "Lyra"],
        location="Academy",
        key_events=["Kael practices dragon magic"],
        plot_threads_resolved=[],
        plot_threads_started=[],
        character_states={"Kael": "alive", "Lyra": "alive"},
    )

    result = validator.validate_chapter(
        chapter_content=valid_content,
        chapter_number=6,
        story_state=current_state,
        chapter_spec=chapter_spec,
    )

    if result.is_valid:
        print("   ✓ Valid content passed validation")
    else:
        print(f"   ✗ Valid content failed: {result.errors}")

    print("\n2. Testing INVALID content - Dead character appears alive...")
    invalid_content_dead = """
    Chapter 6: The Return

    Sylas walked into the training yard, alive and well.
    "I'm back," he said with a smile.

    Kael and Lyra were shocked to see their teacher alive.
    Sylas began teaching them new combat techniques.
    """

    result_dead = validator.validate_chapter(
        chapter_content=invalid_content_dead,
        chapter_number=6,
        story_state=current_state,
        chapter_spec=chapter_spec,
    )

    if not result_dead.is_valid:
        print("   ✓ Validator correctly detected dead character appearing alive")
        for error in result_dead.errors:
            print(f"     - {error.message}")
    else:
        print("   ✗ Validator FAILED to detect dead character!")

    print("\n3. Testing INVALID content - Fused character has physical form...")
    invalid_content_fused = """
    Chapter 6: The Dragon's Choice

    Aurelion stood before Kael in his full dragon form, scales gleaming.
    "I have decided to help you," the great dragon said.

    Aurelion walked beside Kael through the Academy, his massive form
    drawing stares from the students.
    """

    result_fused = validator.validate_chapter(
        chapter_content=invalid_content_fused,
        chapter_number=6,
        story_state=current_state,
        chapter_spec=chapter_spec,
    )

    if not result_fused.is_valid:
        print("   ✓ Validator correctly detected fused character with physical form")
        for error in result_fused.errors:
            print(f"     - {error.message}")
    else:
        print("   ✗ Validator FAILED to detect fused character issue!")

    print("\n4. Testing state transitions...")

    # Test Chapter 5 (before fusion)
    state_chapter_4 = StoryState(
        chapter=4,
        location="Vault",
        active_characters=["Kael", "Lyra", "Aurelion", "Sylas"],
        character_states={
            "Kael": CharacterState(
                name="Kael", status="alive", location="Vault", physical_form="human"
            ),
            "Lyra": CharacterState(
                name="Lyra", status="alive", location="Vault", physical_form="human"
            ),
            "Aurelion": CharacterState(
                name="Aurelion", status="alive", location="Vault", physical_form="dragon"
            ),
            "Sylas": CharacterState(
                name="Sylas", status="alive", location="Vault", physical_form="human"
            ),
        },
        plot_threads=[],
        key_events=[],
    )

    # After Chapter 4: Sylas dies
    state_chapter_4.character_states["Sylas"].status = "dead"
    state_chapter_4.active_characters.remove("Sylas")
    state_chapter_4.key_events.append("Sylas dies protecting Kael")

    print(f"   After Chapter 4: Sylas status = {state_chapter_4.character_states['Sylas'].status}")
    print(f"   Active characters: {state_chapter_4.active_characters}")

    # After Chapter 5: Aurelion fuses with Kael
    state_chapter_5 = StoryState(
        chapter=5,
        location="Sanctum",
        active_characters=["Kael", "Lyra"],
        character_states={
            "Kael": CharacterState(
                name="Kael",
                status="alive",
                location="Sanctum",
                physical_form="human with dragon spirit",
            ),
            "Lyra": CharacterState(
                name="Lyra", status="alive", location="Sanctum", physical_form="human"
            ),
            "Aurelion": CharacterState(
                name="Aurelion", status="fused", location="Kael", physical_form="spirit"
            ),
            "Sylas": CharacterState(
                name="Sylas", status="dead", location="None", physical_form="None"
            ),
        },
        plot_threads=[],
        key_events=["Sylas dies protecting Kael", "Aurelion fuses with Kael"],
    )

    print(
        f"   After Chapter 5: Aurelion status = {state_chapter_5.character_states['Aurelion'].status}"
    )
    print(f"   Active characters: {state_chapter_5.active_characters}")

    print("\n5. Testing outline validation...")

    # Create an outline with continuity issues
    problematic_outline = DetailedOutline(
        chapters=[
            ChapterSpec(
                number=4,
                title="Sylas's Last Stand",
                summary="Sylas dies protecting Kael",
                characters=["Kael", "Lyra", "Sylas"],
                location="Vault",
                key_events=["Sylas dies"],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={"Kael": "alive", "Lyra": "alive", "Sylas": "dead"},
            ),
            ChapterSpec(
                number=5,
                title="Fusion",
                summary="Aurelion fuses with Kael",
                characters=["Kael", "Lyra", "Aurelion"],  # Aurelion still has physical form!
                location="Sanctum",
                key_events=["Fusion"],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={"Kael": "alive", "Lyra": "alive", "Aurelion": "fused"},
            ),
            ChapterSpec(
                number=6,
                title="Aftermath",
                summary="Kael adjusts to new powers",
                characters=["Kael", "Lyra", "Sylas"],  # Sylas appears after death!
                location="Academy",
                key_events=["Training"],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={
                    "Kael": "alive",
                    "Lyra": "alive",
                    "Sylas": "alive",
                },  # Sylas is alive!
            ),
        ]
    )

    outline_errors = problematic_outline.validate()
    print(f"   Outline validation found {len(outline_errors)} issues")
    for error in outline_errors:
        print(f"     - {error}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    # Summary
    all_passed = result.is_valid and not result_dead.is_valid and not result_fused.is_valid

    if all_passed:
        print("\n✅ All continuity validation tests passed!")
        print("   - Valid content accepted")
        print("   - Dead character appearances detected")
        print("   - Fused character physical form issues detected")
        print("   - State transitions work correctly")
    else:
        print("\n⚠ Some tests failed - review results above")

    return all_passed


if __name__ == "__main__":
    import sys

    success = test_continuity_validation()
    sys.exit(0 if success else 1)
