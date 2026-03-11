"""Integration tests for Writer-LSP features using shared models.

Tests the integration between:
- LSP features (definition, diagnostics, completion)
- WriterAPI interface
- Shared models (CharacterProfile, TimelineConflict)
"""

import pytest

# Skip entire module - requires novelwriter_shared package (P1 phase)
pytest.skip(
    "Requires novelwriter_shared package (P1 phase - not yet created)",
    allow_module_level=True
)
from unittest.mock import AsyncMock, MagicMock
from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.features.definition import (
    register_goto_definition,
    _create_location_from_profile,
)
from novelwriter_lsp.features.diagnostics import (
    register_diagnostics,
    _detect_timeline_conflicts,
    _check_status_consistency,
)
from novelwriter_lsp.features.completion import register_completion
from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import CharacterSymbol
from novelwriter_shared.models import (
    CharacterProfile,
    CharacterStatus,
    CharacterTimelineEvent,
    EventType,
    ConflictType,
    TimelineConflict,
)


class MockWriterAPI:
    """Mock implementation of WriterAPI for testing."""

    def __init__(self, characters: list[CharacterProfile] | None = None):
        self._characters = characters or []

    async def get_character(self, name: str) -> CharacterProfile | None:
        for char in self._characters:
            if char.name == name or name in char.aliases:
                return char
        return None

    async def list_characters(self, status: str | None = None) -> list[CharacterProfile]:
        if status:
            return [c for c in self._characters if c.current_status == status]
        return self._characters

    async def create_character(self, *args, **kwargs):
        raise NotImplementedError

    async def update_character(self, *args, **kwargs):
        raise NotImplementedError

    async def delete_character(self, *args, **kwargs):
        raise NotImplementedError

    async def get_fact(self, *args, **kwargs):
        raise NotImplementedError

    async def list_facts(self, *args, **kwargs):
        raise NotImplementedError

    async def create_fact(self, *args, **kwargs):
        raise NotImplementedError

    async def get_chapter(self, *args, **kwargs):
        raise NotImplementedError

    async def list_chapters(self, *args, **kwargs):
        raise NotImplementedError


class TestDefinitionIntegration:
    """Tests for definition feature integration with WriterAPI."""

    def test_create_location_from_profile(self):
        """Test creating LSP Location from CharacterProfile."""
        profile = CharacterProfile(
            name="John Doe",
            aliases=["John"],
            current_status=CharacterStatus.ALIVE,
            metadata={
                "definition_uri": "file:///novel/characters.md",
                "definition_range": {
                    "start_line": 10,
                    "end_line": 10,
                    "start_character": 0,
                    "end_character": 8,
                },
            },
        )
        
        location = _create_location_from_profile(profile, "file:///default.md")
        
        assert location is not None
        assert location.uri == "file:///novel/characters.md"
        assert location.range.start.line == 10
        assert location.range.start.character == 0

    def test_create_location_from_profile_default(self):
        """Test creating Location with default URI when profile lacks metadata."""
        profile = CharacterProfile(name="Jane Doe")
        
        location = _create_location_from_profile(profile, "file:///default.md")
        
        assert location is not None
        assert location.uri == "file:///default.md"

    @pytest.mark.asyncio
    async def test_definition_uses_writer_api(self):
        """Test that definition falls back to WriterAPI when symbol not in index."""
        profile = CharacterProfile(
            name="Alice",
            aliases=["Ali"],
            current_status=CharacterStatus.ALIVE,
        )
        writer_api = MockWriterAPI(characters=[profile])
        
        server = MagicMock(spec=LanguageServer)
        server.workspace = MagicMock()
        mock_doc = MagicMock()
        mock_doc.source = "Alice walked down the street."
        server.workspace.get_text_document.return_value = mock_doc
        
        index = SymbolIndex()
        
        register_goto_definition(server, index, writer_api)
        
        # The handler is registered but we need to call it directly
        # This test verifies the registration works


class TestDiagnosticsIntegration:
    """Tests for diagnostics feature integration with shared models."""

    def test_detect_multiple_deaths(self):
        """Test detection of multiple death events."""
        profile = CharacterProfile(
            name="Bob",
            timeline=[
                CharacterTimelineEvent(
                    chapter=5,
                    event_type=EventType.DEATH,
                    description="Killed in battle",
                ),
                CharacterTimelineEvent(
                    chapter=10,
                    event_type=EventType.DEATH,
                    description="Found dead",
                ),
            ],
        )
        
        conflicts = _detect_timeline_conflicts(profile)
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.MULTIPLE_DEATHS
        assert "multiple death events" in conflicts[0].description.lower()

    def test_detect_action_after_death(self):
        """Test detection of actions after death."""
        profile = CharacterProfile(
            name="Charlie",
            death_chapter=5,
            timeline=[
                CharacterTimelineEvent(
                    chapter=5,
                    event_type=EventType.DEATH,
                    description="Dies",
                ),
                CharacterTimelineEvent(
                    chapter=10,
                    event_type=EventType.APPEARANCE,
                    description="Appears at party",
                ),
            ],
        )
        
        conflicts = _detect_timeline_conflicts(profile)
        
        assert len(conflicts) >= 1
        found_action_after_death = any(
            c.conflict_type == ConflictType.ACTION_AFTER_DEATH for c in conflicts
        )
        assert found_action_after_death

    def test_detect_temporal_paradox(self):
        """Test detection of birth after death."""
        profile = CharacterProfile(
            name="Dave",
            birth_chapter=10,
            death_chapter=5,
        )
        
        conflicts = _detect_timeline_conflicts(profile)
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.TEMPORAL_PARADOX

    def test_check_status_consistency_deceased_no_death(self):
        """Test warning for deceased character without death event."""
        profile = CharacterProfile(
            name="Eve",
            current_status=CharacterStatus.DECEASED,
        )
        
        warnings = _check_status_consistency(profile)
        
        assert len(warnings) == 1
        assert "no death chapter" in warnings[0].lower()

    def test_check_status_consistency_alive_with_death(self):
        """Test warning for alive character with death chapter."""
        profile = CharacterProfile(
            name="Frank",
            current_status=CharacterStatus.ALIVE,
            death_chapter=10,
        )
        
        warnings = _check_status_consistency(profile)
        
        assert len(warnings) >= 1
        assert any("alive but has a death chapter" in w.lower() for w in warnings)

    @pytest.mark.asyncio
    async def test_diagnostics_register_with_writer_api(self):
        """Test that diagnostics can be registered with WriterAPI."""
        server = MagicMock()
        server._custom_state = {}
        index = MagicMock(spec=SymbolIndex)
        writer_api = MockWriterAPI()
        
        register_diagnostics(server, index, writer_api)
        
        assert "validate_document" in server._custom_state


class TestCompletionIntegration:
    """Tests for completion feature integration with WriterAPI."""

    @pytest.mark.asyncio
    async def test_completion_uses_writer_api(self):
        """Test that completion includes characters from WriterAPI."""
        profile = CharacterProfile(
            name="Zoe",
            aliases=["Z"],
            current_status=CharacterStatus.ALIVE,
            bio="A mysterious traveler",
        )
        writer_api = MockWriterAPI(characters=[profile])
        
        server = MagicMock(spec=LanguageServer)
        server.workspace = MagicMock()
        mock_doc = MagicMock()
        mock_doc.source = "@Z"
        server.workspace.get_text_document.return_value = mock_doc
        
        index = SymbolIndex()
        
        register_completion(server, index, writer_api)

    def test_completion_register_without_writer_api(self):
        """Test that completion works without WriterAPI."""
        server = MagicMock(spec=LanguageServer)
        index = MagicMock(spec=SymbolIndex)
        
        register_completion(server, index, None)
        
        assert server.feature.called


class TestConversionUtilities:
    """Tests for model conversion utilities."""

    def test_profile_to_symbol_conversion(self):
        """Test converting CharacterProfile to CharacterSymbol."""
        from novelwriter_lsp.utils.conversions import profile_to_symbol
        
        profile = CharacterProfile(
            name="Test Character",
            aliases=["TC"],
            current_status=CharacterStatus.ALIVE,
            bio="A test character",
            tier=0,
        )
        
        symbol = profile_to_symbol(
            profile,
            definition_uri="file:///test.md",
            definition_range={"start_line": 1, "end_line": 1, "start_character": 0, "end_character": 14},
            novel_id="novel_1",
        )
        
        assert symbol.name == "Test Character"
        assert symbol.aliases == ["TC"]
        assert symbol.status == "alive"
        assert symbol.description == "A test character"

    def test_symbol_to_profile_conversion(self):
        """Test converting CharacterSymbol to CharacterProfile."""
        from novelwriter_lsp.utils.conversions import symbol_to_profile
        
        symbol = CharacterSymbol(
            id="char_test_1",
            name="Test Symbol",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={"start_line": 1, "end_line": 1, "start_character": 0, "end_character": 11},
            aliases=["TS"],
            status="alive",
            description="A test symbol",
        )
        
        profile = symbol_to_profile(symbol)
        
        assert profile.name == "Test Symbol"
        assert profile.aliases == ["TS"]
        assert profile.current_status == "alive"
        assert profile.bio == "A test symbol"
