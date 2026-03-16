# tests/test_agents/test_writers.py
"""Tests for Writer Agents."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.novel_agent.agents.writers.fantasy import FantasyWriter
from src.novel_agent.agents.writers.history import HistoryWriter
from src.novel_agent.agents.writers.military import MilitaryWriter
from src.novel_agent.agents.writers.romance import RomanceWriter
from src.novel_agent.agents.writers.scifi import SciFiWriter
from src.novel_agent.agents.writers.writer_factory import get_available_genres, get_writer


class TestWriterFactory:
    """Tests for writer factory."""

    def test_get_scifi_writer(self) -> None:
        """Test getting sci-fi writer."""
        mock_llm = MagicMock()
        writer = get_writer("scifi", mock_llm)
        assert isinstance(writer, SciFiWriter)
        assert writer.GENRE == "scifi"

    def test_get_fantasy_writer(self) -> None:
        """Test getting fantasy writer."""
        mock_llm = MagicMock()
        writer = get_writer("fantasy", mock_llm)
        assert isinstance(writer, FantasyWriter)

    def test_get_romance_writer(self) -> None:
        """Test getting romance writer."""
        mock_llm = MagicMock()
        writer = get_writer("romance", mock_llm)
        assert isinstance(writer, RomanceWriter)

    def test_get_history_writer(self) -> None:
        """Test getting history writer."""
        mock_llm = MagicMock()
        writer = get_writer("history", mock_llm)
        assert isinstance(writer, HistoryWriter)

    def test_get_military_writer(self) -> None:
        """Test getting military writer."""
        mock_llm = MagicMock()
        writer = get_writer("military", mock_llm)
        assert isinstance(writer, MilitaryWriter)

    def test_get_writer_case_insensitive(self) -> None:
        """Test that genre is case insensitive."""
        mock_llm = MagicMock()
        writer = get_writer("SCI-FI", mock_llm)
        assert writer.GENRE == "scifi"

    def test_get_writer_unknown_genre(self) -> None:
        """Test error for unknown genre."""
        mock_llm = MagicMock()
        with pytest.raises(ValueError, match="Unknown genre"):
            get_writer("unknown", mock_llm)

    def test_get_available_genres(self) -> None:
        """Test getting available genres."""
        genres = get_available_genres()
        assert "scifi" in genres
        assert "fantasy" in genres
        assert "romance" in genres
        assert "history" in genres
        assert "military" in genres


class TestSciFiWriter:
    """Tests for Sci-Fi Writer."""

    @pytest.fixture
    def writer(self) -> SciFiWriter:
        """Create Sci-Fi writer with mock LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(
            return_value=MagicMock(content="Test chapter content")
        )
        return SciFiWriter(name="Test Sci-Fi Writer", llm=mock_llm)

    def test_genre(self, writer: SciFiWriter) -> None:
        """Test genre is set correctly."""
        assert writer.GENRE == "scifi"

    def test_domain_knowledge(self, writer: SciFiWriter) -> None:
        """Test domain knowledge is defined."""
        assert "physics" in writer.DOMAIN_KNOWLEDGE.lower()

    @pytest.mark.asyncio
    async def test_write_chapter(self, writer: SciFiWriter) -> None:
        """Test chapter writing."""
        content = await writer.write_chapter(
            chapter_number=1,
            chapter_outline="Test outline",
            characters=[{"name": "Alice", "role": "protagonist"}],
            world_context={"rules": {"name": "Test World"}},
        )

        assert content == "Test chapter content"

    @pytest.mark.asyncio
    async def test_execute(self, writer: SciFiWriter) -> None:
        """Test execute method."""
        result = await writer.execute(
            {
                "chapter_number": 1,
                "chapter_outline": "Test",
                "characters": [],
                "world_context": {},
            }
        )

        assert result.success is True
        assert "content" in result.data


class TestFantasyWriter:
    """Tests for Fantasy Writer."""

    @pytest.fixture
    def writer(self) -> FantasyWriter:
        """Create Fantasy writer."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(return_value=MagicMock(content="Fantasy chapter"))
        return FantasyWriter(name="Test Fantasy Writer", llm=mock_llm)

    def test_genre(self, writer: FantasyWriter) -> None:
        """Test genre is set correctly."""
        assert writer.GENRE == "fantasy"

    def test_domain_knowledge(self, writer: FantasyWriter) -> None:
        """Test domain knowledge includes magic."""
        assert "magic" in writer.DOMAIN_KNOWLEDGE.lower()

    @pytest.mark.asyncio
    async def test_write_chapter(self, writer: FantasyWriter) -> None:
        """Test chapter writing."""
        content = await writer.write_chapter(
            chapter_number=1,
            chapter_outline="A hero discovers magic",
            characters=[],
            world_context={},
        )

        assert content == "Fantasy chapter"


class TestRomanceWriter:
    """Tests for Romance Writer."""

    @pytest.fixture
    def writer(self) -> RomanceWriter:
        """Create Romance writer."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(return_value=MagicMock(content="Romance chapter"))
        return RomanceWriter(name="Test Romance Writer", llm=mock_llm)

    def test_genre(self, writer: RomanceWriter) -> None:
        """Test genre is set correctly."""
        assert writer.GENRE == "romance"

    def test_domain_knowledge(self, writer: RomanceWriter) -> None:
        """Test domain knowledge includes emotion."""
        assert "emotion" in writer.DOMAIN_KNOWLEDGE.lower()


class TestHistoryWriter:
    """Tests for History Writer."""

    @pytest.fixture
    def writer(self) -> HistoryWriter:
        """Create History writer."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(
            return_value=MagicMock(content="Historical chapter")
        )
        return HistoryWriter(name="Test History Writer", llm=mock_llm)

    def test_genre(self, writer: HistoryWriter) -> None:
        """Test genre is set correctly."""
        assert writer.GENRE == "history"

    def test_domain_knowledge(self, writer: HistoryWriter) -> None:
        """Test domain knowledge includes period details."""
        assert "period" in writer.DOMAIN_KNOWLEDGE.lower()


class TestMilitaryWriter:
    """Tests for Military Writer."""

    @pytest.fixture
    def writer(self) -> MilitaryWriter:
        """Create Military writer."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(
            return_value=MagicMock(content="Military chapter")
        )
        return MilitaryWriter(name="Test Military Writer", llm=mock_llm)

    def test_genre(self, writer: MilitaryWriter) -> None:
        """Test genre is set correctly."""
        assert writer.GENRE == "military"

    def test_domain_knowledge(self, writer: MilitaryWriter) -> None:
        """Test domain knowledge includes tactics."""
        assert "tactical" in writer.DOMAIN_KNOWLEDGE.lower()


class TestWriterWithWorldContext:
    """Tests for writers with various world context structures."""

    @pytest.fixture
    def writer(self) -> SciFiWriter:
        """Create writer with mock LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(return_value=MagicMock(content="Chapter content"))
        return SciFiWriter(name="Test Writer", llm=mock_llm)

    @pytest.mark.asyncio
    async def test_with_full_world_context(self, writer: SciFiWriter) -> None:
        """Test writing with full world context."""
        content = await writer.write_chapter(
            chapter_number=5,
            chapter_outline="The crew discovers an anomaly",
            characters=[
                {
                    "name": "Captain Jane",
                    "role": "protagonist",
                    "personality": {"traits": ["brave"]},
                },
            ],
            world_context={
                "rules": {
                    "name": "Andromeda Station",
                    "technology_level": "FTL capable",
                    "core_rules": [{"rule": "No FTL near gravity wells"}],
                },
                "locations": [{"name": "Bridge", "description": "The command center of the ship"}],
            },
            style_guide="Use technical jargon sparingly",
        )

        assert content == "Chapter content"


class TestWriterContextParams:
    """Test new context parameters in writers (relationships, full_outline, world_settings)."""

    @pytest.fixture
    def writer(self) -> SciFiWriter:
        """Create Sci-Fi writer with mock LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(
            return_value=MagicMock(content="Test chapter with context")
        )
        return SciFiWriter(name="Test Writer", llm=mock_llm)

    @pytest.mark.asyncio
    async def test_write_chapter_accepts_relationships(self, writer: SciFiWriter) -> None:
        """Test that write_chapter accepts relationships parameter."""
        relationships = [
            {
                "character1_name": "Alice",
                "character2_name": "Bob",
                "relationship_type": "friend",
            }
        ]
        content = await writer.write_chapter(
            chapter_number=1,
            chapter_outline="Test outline",
            characters=[{"name": "Alice", "role": "protagonist"}],
            world_context={},
            relationships=relationships,
        )

        assert content == "Test chapter with context"

    @pytest.mark.asyncio
    async def test_write_chapter_accepts_full_outline(self, writer: SciFiWriter) -> None:
        """Test that write_chapter accepts full_outline parameter."""
        full_outline = {
            "main_plot": "The hero saves the world",
            "chapters": [
                {"number": 1, "summary": "Introduction"},
                {"number": 2, "summary": "Rising action"},
            ],
        }
        content = await writer.write_chapter(
            chapter_number=1,
            chapter_outline="Test outline",
            characters=[],
            world_context={},
            full_outline=full_outline,
        )

        assert content == "Test chapter with context"

    @pytest.mark.asyncio
    async def test_write_chapter_accepts_world_settings(self, writer: SciFiWriter) -> None:
        """Test that write_chapter accepts world_settings parameter."""
        world_settings = {
            "rules": ["Magic requires mana", "Night lasts 10 hours"],
            "forbidden_elements": ["teleportation"],
        }
        content = await writer.write_chapter(
            chapter_number=1,
            chapter_outline="Test outline",
            characters=[],
            world_context={},
            world_settings=world_settings,
        )

        assert content == "Test chapter with context"

    @pytest.mark.asyncio
    async def test_write_chapter_accepts_all_new_params(self, writer: SciFiWriter) -> None:
        """Test that write_chapter accepts all new parameters together."""
        relationships = [
            {"character1_name": "Alice", "character2_name": "Bob", "relationship_type": "friend"}
        ]
        full_outline = {"main_plot": "Test plot", "chapters": []}
        world_settings = {"rules": ["Rule 1"], "forbidden_elements": []}

        content = await writer.write_chapter(
            chapter_number=1,
            chapter_outline="Test outline",
            characters=[{"name": "Alice", "role": "protagonist"}],
            world_context={},
            relationships=relationships,
            full_outline=full_outline,
            world_settings=world_settings,
        )

        assert content == "Test chapter with context"

    @pytest.mark.asyncio
    async def test_execute_passes_relationships(self, writer: SciFiWriter) -> None:
        """Test that execute method passes relationships parameter."""
        result = await writer.execute(
            {
                "chapter_number": 1,
                "chapter_outline": "Test",
                "characters": [],
                "world_context": {},
                "relationships": [
                    {"character1_name": "A", "character2_name": "B", "relationship_type": "enemy"}
                ],
            }
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_passes_full_outline(self, writer: SciFiWriter) -> None:
        """Test that execute method passes full_outline parameter."""
        result = await writer.execute(
            {
                "chapter_number": 1,
                "chapter_outline": "Test",
                "characters": [],
                "world_context": {},
                "full_outline": {"main_plot": "Plot", "chapters": []},
            }
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_passes_world_settings(self, writer: SciFiWriter) -> None:
        """Test that execute method passes world_settings parameter."""
        result = await writer.execute(
            {
                "chapter_number": 1,
                "chapter_outline": "Test",
                "characters": [],
                "world_context": {},
                "world_settings": {"rules": ["Rule"], "forbidden_elements": []},
            }
        )

        assert result.success is True
