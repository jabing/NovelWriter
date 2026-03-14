"""Tests for summary data structures."""

from datetime import datetime

from src.novel.summaries import ArcSummary, ChapterSummary


class TestChapterSummary:
    """Test ChapterSummary data structure."""

    def test_create_chapter_summary(self):
        """Test creating a chapter summary."""
        summary = ChapterSummary(
            chapter_number=1,
            title="The Beginning",
            summary="Hero starts journey",
            key_events=["Event 1"],
        )
        assert summary.chapter_number == 1
        assert summary.title == "The Beginning"
        assert summary.summary == "Hero starts journey"
        assert summary.key_events == ["Event 1"]
        assert summary.sentiment == "neutral"
        assert summary.word_count == 0

    def test_create_with_all_fields(self):
        """Test creating with all fields populated."""
        summary = ChapterSummary(
            chapter_number=5,
            title="Midpoint",
            summary="The story reaches its midpoint",
            key_events=["Battle won", "Ally joined"],
            character_changes={"Hero": "grew stronger", "Villain": "revealed plan"},
            location="Castle",
            plot_threads_advanced=["Main quest", "Romance"],
            plot_threads_resolved=["Initial conflict"],
            sentiment="hopeful",
            word_count=3000,
        )
        assert summary.chapter_number == 5
        assert len(summary.key_events) == 2
        assert len(summary.character_changes) == 2
        assert summary.location == "Castle"
        assert len(summary.plot_threads_advanced) == 2
        assert len(summary.plot_threads_resolved) == 1
        assert summary.sentiment == "hopeful"
        assert summary.word_count == 3000

    def test_serialization(self):
        """Test to_dict and from_dict."""
        summary = ChapterSummary(
            chapter_number=10,
            title="Climax",
            summary="The final battle",
            key_events=["Hero defeats villain"],
            character_changes={"Hero": "became leader"},
            location="Battlefield",
            sentiment="triumphant",
            word_count=5000,
        )
        data = summary.to_dict()

        # Check all fields are present
        assert data["chapter_number"] == 10
        assert data["title"] == "Climax"
        assert data["summary"] == "The final battle"
        assert data["key_events"] == ["Hero defeats villain"]
        assert data["character_changes"] == {"Hero": "became leader"}
        assert data["location"] == "Battlefield"
        assert data["sentiment"] == "triumphant"
        assert data["word_count"] == 5000
        assert "created_at" in data

    def test_deserialization(self):
        """Test from_dict with datetime handling."""
        data = {
            "chapter_number": 15,
            "title": "Resolution",
            "summary": "Everything is resolved",
            "key_events": ["Peace restored"],
            "character_changes": {},
            "location": "Kingdom",
            "plot_threads_advanced": [],
            "plot_threads_resolved": ["Main plot"],
            "sentiment": "satisfying",
            "word_count": 4000,
            "created_at": "2026-03-02T12:00:00",
        }
        summary = ChapterSummary.from_dict(data)
        assert summary.chapter_number == 15
        assert isinstance(summary.created_at, datetime)
        assert summary.created_at.year == 2026

    def test_roundtrip_serialization(self):
        """Test that roundtrip preserves all data."""
        original = ChapterSummary(
            chapter_number=20,
            title="New Beginning",
            summary="A new adventure starts",
            key_events=["Call received", "Party formed"],
            character_changes={"Hero": "ready for more", "Sidekick": "promoted"},
            location="Tavern",
            plot_threads_advanced=["Sequel hook"],
            plot_threads_resolved=[],
            sentiment="exciting",
            word_count=3500,
        )
        data = original.to_dict()
        restored = ChapterSummary.from_dict(data)

        assert restored.chapter_number == original.chapter_number
        assert restored.title == original.title
        assert restored.summary == original.summary
        assert restored.key_events == original.key_events
        assert restored.character_changes == original.character_changes
        assert restored.location == original.location
        assert restored.sentiment == original.sentiment
        assert restored.word_count == original.word_count

    def test_context_string_basic(self):
        """Test context string generation with basic data."""
        summary = ChapterSummary(
            chapter_number=1,
            title="Start",
            summary="Beginning of story",
        )
        ctx = summary.get_context_string()
        assert "第1章" in ctx
        assert "Start" in ctx
        assert "摘要" in ctx
        assert "Beginning of story" in ctx

    def test_context_string_with_events(self):
        """Test context string includes key events."""
        summary = ChapterSummary(
            chapter_number=5,
            title="Battle",
            summary="Epic battle scene",
            key_events=["Enemy appears", "Hero fights", "Victory"],
        )
        ctx = summary.get_context_string()
        assert "关键事件" in ctx
        assert "Enemy appears" in ctx
        assert "Hero fights" in ctx

    def test_context_string_with_changes(self):
        """Test context string includes character changes."""
        summary = ChapterSummary(
            chapter_number=10,
            title="Growth",
            summary="Character development",
            character_changes={"Hero": "gained power", "Villain": "lost ally"},
        )
        ctx = summary.get_context_string()
        assert "角色变化" in ctx
        assert "Hero" in ctx
        assert "gained power" in ctx

    def test_context_string_truncation(self):
        """Test that context string truncates long lists."""
        summary = ChapterSummary(
            chapter_number=15,
            title="Complex",
            summary="Many things happened",
            key_events=[f"Event {i}" for i in range(20)],  # 20 events
            character_changes={f"Char{i}": f"Change {i}" for i in range(10)},  # 10 chars
        )
        ctx = summary.get_context_string()
        # Should only include first 5 key events
        assert "Event 0" in ctx
        assert "Event 4" in ctx
        assert "Event 5" not in ctx or ctx.count("Event") <= 5


class TestArcSummary:
    """Test ArcSummary data structure."""

    def test_create_arc_summary(self):
        """Test creating an arc summary."""
        arc = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Introduction",
            summary="The story begins",
        )
        assert arc.arc_number == 1
        assert arc.start_chapter == 1
        assert arc.end_chapter == 10
        assert arc.title == "Introduction"
        assert arc.summary == "The story begins"

    def test_chapter_range(self):
        """Test chapter_range property."""
        arc = ArcSummary(
            arc_number=2,
            start_chapter=11,
            end_chapter=20,
            title="Rising Action",
            summary="Story develops",
        )
        assert 15 in arc.chapter_range
        assert 11 in arc.chapter_range
        assert 20 in arc.chapter_range
        assert 10 not in arc.chapter_range
        assert 21 not in arc.chapter_range
        assert len(list(arc.chapter_range)) == 10

    def test_contains_chapter(self):
        """Test contains_chapter method."""
        arc = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Test",
            summary="Test",
        )
        assert arc.contains_chapter(5)
        assert arc.contains_chapter(1)
        assert arc.contains_chapter(10)
        assert not arc.contains_chapter(0)
        assert not arc.contains_chapter(11)

    def test_serialization(self):
        """Test to_dict and from_dict."""
        arc = ArcSummary(
            arc_number=3,
            start_chapter=21,
            end_chapter=30,
            title="Climax",
            summary="The climax arc",
            major_events=["Event A", "Event B"],
            character_arcs={"Hero": "completed training"},
            world_changes=["Kingdom fell"],
            plot_threads_status={"Main": "active", "Romance": "resolved"},
            themes=["Sacrifice", "Redemption"],
        )
        data = arc.to_dict()

        assert data["arc_number"] == 3
        assert data["major_events"] == ["Event A", "Event B"]
        assert data["character_arcs"] == {"Hero": "completed training"}
        assert data["world_changes"] == ["Kingdom fell"]
        assert data["plot_threads_status"] == {"Main": "active", "Romance": "resolved"}
        assert data["themes"] == ["Sacrifice", "Redemption"]

    def test_deserialization(self):
        """Test from_dict with datetime."""
        data = {
            "arc_number": 5,
            "start_chapter": 41,
            "end_chapter": 50,
            "title": "Resolution",
            "summary": "Everything ends",
            "major_events": [],
            "character_arcs": {},
            "world_changes": [],
            "plot_threads_status": {},
            "themes": [],
            "created_at": "2026-03-02T12:00:00",
        }
        arc = ArcSummary.from_dict(data)
        assert arc.arc_number == 5
        assert isinstance(arc.created_at, datetime)

    def test_context_string_basic(self):
        """Test context string generation."""
        arc = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Beginning",
            summary="The hero's journey starts",
        )
        ctx = arc.get_context_string()
        assert "第1卷" in ctx
        assert "Beginning" in ctx
        assert "1-10" in ctx
        assert "概要" in ctx

    def test_context_string_with_events(self):
        """Test context string includes major events."""
        arc = ArcSummary(
            arc_number=2,
            start_chapter=11,
            end_chapter=20,
            title="Development",
            summary="Story develops",
            major_events=[f"Event {i}" for i in range(15)],  # 15 events
        )
        ctx = arc.get_context_string()
        assert "重大事件" in ctx
        # Should only include first 10
        assert "Event 0" in ctx
        assert "Event 9" in ctx

    def test_context_string_with_character_arcs(self):
        """Test context string includes character arcs."""
        arc = ArcSummary(
            arc_number=1,
            start_chapter=1,
            end_chapter=10,
            title="Growth",
            summary="Characters develop",
            character_arcs={
                "Hero": "became stronger",
                "Sidekick": "gained confidence",
                "Mentor": "revealed secret",
            },
        )
        ctx = arc.get_context_string()
        assert "角色成长" in ctx
        assert "Hero" in ctx
        assert "became stronger" in ctx

    def test_context_string_with_plot_threads(self):
        """Test context string includes plot thread status."""
        arc = ArcSummary(
            arc_number=3,
            start_chapter=21,
            end_chapter=30,
            title="Conflict",
            summary="Multiple plots converge",
            plot_threads_status={
                "Main Quest": "active",
                "Romance": "resolved",
                "Betrayal": "active",
            },
        )
        ctx = arc.get_context_string()
        assert "剧情线" in ctx
        assert "Main Quest(active)" in ctx
        assert "Romance(resolved)" in ctx
