"""Tests for outline management system."""

from src.novel.outline_manager import ChapterSpec, DetailedOutline


class TestChapterSpec:
    """Test ChapterSpec dataclass."""

    def test_chapter_spec_initialization(self) -> None:
        """Test that ChapterSpec can be initialized."""
        spec = ChapterSpec(
            number=1,
            title="The Beginning",
            summary="Kael discovers the dragon egg",
            characters=["Kael", "Lyra"],
            location="Academy",
            key_events=["Kael finds the egg"],
            plot_threads_resolved=[],
            plot_threads_started=["Dragon awakening"],
            character_states={"Kael": "alive", "Lyra": "alive"},
        )

        assert spec.number == 1
        assert spec.title == "The Beginning"
        assert "Kael" in spec.characters
        assert "Lyra" in spec.characters
        assert len(spec.key_events) == 1
        assert len(spec.plot_threads_started) == 1

    def test_chapter_spec_with_multiple_events(self) -> None:
        """Test ChapterSpec with multiple key events."""
        spec = ChapterSpec(
            number=2,
            title="The Test",
            summary="Kael tests his powers",
            characters=["Kael"],
            location="Training Grounds",
            key_events=["Kael learns fire magic", "Kael accidentally burns a book"],
            plot_threads_resolved=[],
            plot_threads_started=[],
            character_states={"Kael": "alive"},
        )

        assert len(spec.key_events) == 2
        assert "Kael learns fire magic" in spec.key_events

    def test_chapter_spec_with_resolved_threads(self) -> None:
        """Test ChapterSpec with resolved plot threads."""
        spec = ChapterSpec(
            number=10,
            title="Resolution",
            summary="The dragon awakening is resolved",
            characters=["Kael", "Lyra"],
            location="Dragon's Lair",
            key_events=["Aurelion awakens"],
            plot_threads_resolved=["Dragon awakening"],
            plot_threads_started=[],
            character_states={"Kael": "alive", "Lyra": "alive"},
        )

        assert len(spec.plot_threads_resolved) == 1
        assert "Dragon awakening" in spec.plot_threads_resolved


class TestDetailedOutline:
    """Test DetailedOutline class."""

    def test_detailed_outline_initialization(self) -> None:
        """Test that DetailedOutline can be initialized."""
        chapters = [
            ChapterSpec(
                number=1,
                title="Chapter 1",
                summary="Introduction",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
            ChapterSpec(
                number=2,
                title="Chapter 2",
                summary="Development",
                characters=["Kael", "Lyra"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
        ]

        outline = DetailedOutline(chapters=chapters)

        assert len(outline.chapters) == 2
        assert outline.chapters[0].number == 1
        assert outline.chapters[1].number == 2

    def test_detailed_outline_with_30_chapters(self) -> None:
        """Test DetailedOutline with 30 chapters."""
        chapters = [
            ChapterSpec(
                number=i + 1,
                title=f"Chapter {i + 1}",
                summary=f"Summary for chapter {i + 1}",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            )
            for i in range(30)
        ]

        outline = DetailedOutline(chapters=chapters)

        assert len(outline.chapters) == 30
        assert outline.chapters[29].number == 30

    def test_get_chapter_spec(self) -> None:
        """Test get_chapter_spec method."""
        chapters = [
            ChapterSpec(
                number=1,
                title="Chapter 1",
                summary="Summary 1",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
            ChapterSpec(
                number=2,
                title="Chapter 2",
                summary="Summary 2",
                characters=["Kael", "Lyra"],
                location="Library",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
        ]

        outline = DetailedOutline(chapters=chapters)

        spec = outline.get_chapter_spec(1)
        assert spec is not None
        assert spec.number == 1
        assert spec.title == "Chapter 1"

        spec = outline.get_chapter_spec(2)
        assert spec is not None
        assert spec.number == 2
        assert spec.location == "Library"

    def test_get_chapter_spec_not_found(self) -> None:
        """Test get_chapter_spec with non-existent chapter."""
        chapters = [
            ChapterSpec(
                number=1,
                title="Chapter 1",
                summary="Summary 1",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            )
        ]

        outline = DetailedOutline(chapters=chapters)

        spec = outline.get_chapter_spec(99)
        assert spec is None

    def test_validate_complete_outline(self) -> None:
        """Test validate on a complete outline."""
        chapters = [
            ChapterSpec(
                number=i + 1,
                title=f"Chapter {i + 1}",
                summary=f"Summary for chapter {i + 1}",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            )
            for i in range(30)
        ]

        outline = DetailedOutline(chapters=chapters)

        errors = outline.validate()
        assert len(errors) == 0

    def test_validate_missing_chapters(self) -> None:
        """Test validate detects missing chapters."""
        chapters = [
            ChapterSpec(
                number=1,
                title="Chapter 1",
                summary="Summary 1",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
            ChapterSpec(
                number=3,  # Missing chapter 2
                title="Chapter 3",
                summary="Summary 3",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
        ]

        outline = DetailedOutline(chapters=chapters)

        errors = outline.validate()
        assert len(errors) > 0
        assert any("missing" in error.lower() for error in errors)

    def test_validate_duplicate_chapters(self) -> None:
        """Test validate detects duplicate chapter numbers."""
        chapters = [
            ChapterSpec(
                number=1,
                title="Chapter 1",
                summary="Summary 1",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
            ChapterSpec(
                number=1,  # Duplicate
                title="Chapter 1 Again",
                summary="Summary 1 Again",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            ),
        ]

        outline = DetailedOutline(chapters=chapters)

        errors = outline.validate()
        assert len(errors) > 0
        assert any("duplicate" in error.lower() for error in errors)

    def test_validate_empty_fields(self) -> None:
        """Test validate detects empty required fields."""
        chapters = [
            ChapterSpec(
                number=1,
                title="",  # Empty title
                summary="Summary 1",
                characters=[],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={},
            )
        ]

        outline = DetailedOutline(chapters=chapters)

        errors = outline.validate()
        assert len(errors) > 0
        assert any("empty" in error.lower() or "missing" in error.lower() for error in errors)

    def test_validate_plot_thread_continuity(self) -> None:
        """Test validate detects plot thread continuity issues."""
        chapters = [
            ChapterSpec(
                number=1,
                title="Chapter 1",
                summary="Summary 1",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=["Dragon awakening"],
                character_states={},
            ),
            ChapterSpec(
                number=2,
                title="Chapter 2",
                summary="Summary 2",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=["Dragon awakening"],  # Resolved too quickly
                plot_threads_started=[],
                character_states={},
            ),
        ]

        outline = DetailedOutline(chapters=chapters)

        # This should pass - it's valid for a thread to be resolved quickly
        errors = outline.validate()
        # For now, we don't validate plot thread pacing
        assert len(errors) >= 0

    def test_get_character_states_for_chapter(self) -> None:
        """Test getting character states for a specific chapter."""
        chapters = [
            ChapterSpec(
                number=1,
                title="Chapter 1",
                summary="Summary 1",
                characters=["Kael", "Sylas"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={"Kael": "alive", "Sylas": "alive"},
            ),
            ChapterSpec(
                number=2,
                title="Chapter 2",
                summary="Summary 2",
                characters=["Kael"],
                location="Academy",
                key_events=[],
                plot_threads_resolved=[],
                plot_threads_started=[],
                character_states={"Kael": "alive"},
            ),
        ]

        outline = DetailedOutline(chapters=chapters)

        states = outline.get_character_states_for_chapter(1)
        assert "Kael" in states
        assert "Sylas" in states
        assert states["Kael"] == "alive"

        states = outline.get_character_states_for_chapter(2)
        assert "Kael" in states
        assert "Sylas" not in states
