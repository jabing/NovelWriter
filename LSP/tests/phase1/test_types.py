"""
Tests for NovelWriter LSP type definitions.

This module tests the symbol types defined in novelwriter_lsp.types.
"""

import pytest
from novelwriter_lsp.types import (
    SymbolType,
    OutlineLevel,
    BaseSymbol,
    CharacterSymbol,
    LocationSymbol,
    ItemSymbol,
    LoreSymbol,
    PlotPointSymbol,
    OutlineSymbol,
    EventSymbol,
    RelationshipSymbol,
    ChapterSymbol,
)


class TestSymbolType:
    """Tests for SymbolType enum."""
    
    def test_symbol_type_count(self):
        """Test that all 9 symbol types are defined."""
        assert len(SymbolType) == 9
    
    def test_symbol_type_values(self):
        """Test that all expected symbol types exist."""
        expected_types = [
            "CHARACTER",
            "LOCATION",
            "ITEM",
            "LORE",
            "PLOTPOINT",
            "OUTLINE",
            "EVENT",
            "RELATIONSHIP",
            "CHAPTER",
        ]
        for type_name in expected_types:
            assert hasattr(SymbolType, type_name)
    
    def test_symbol_type_string_values(self):
        """Test that enum string values are correct."""
        assert SymbolType.CHARACTER.value == "character"
        assert SymbolType.LOCATION.value == "location"
        assert SymbolType.ITEM.value == "item"
        assert SymbolType.LORE.value == "lore"
        assert SymbolType.PLOTPOINT.value == "plotpoint"
        assert SymbolType.OUTLINE.value == "outline"
        assert SymbolType.EVENT.value == "event"
        assert SymbolType.RELATIONSHIP.value == "relationship"
        assert SymbolType.CHAPTER.value == "chapter"


class TestOutlineLevel:
    """Tests for OutlineLevel enum."""
    
    def test_outline_level_count(self):
        """Test that all 3 outline levels are defined."""
        assert len(OutlineLevel) == 3
    
    def test_outline_level_values(self):
        """Test that all expected outline levels exist."""
        assert hasattr(OutlineLevel, "MASTER")
        assert hasattr(OutlineLevel, "VOLUME")
        assert hasattr(OutlineLevel, "CHAPTER")
    
    def test_outline_level_string_values(self):
        """Test that enum string values are correct."""
        assert OutlineLevel.MASTER.value == "master"
        assert OutlineLevel.VOLUME.value == "volume"
        assert OutlineLevel.CHAPTER.value == "chapter"


class TestBaseSymbol:
    """Tests for BaseSymbol dataclass."""
    
    def test_base_symbol_creation(self):
        """Test creating a basic BaseSymbol instance."""
        symbol = BaseSymbol(
            id="test-1",
            type=SymbolType.CHARACTER,
            name="Test Character",
            novel_id="novel-1",
            definition_uri="file:///test.md",
            definition_range={"start_line": 0, "end_line": 5},
        )
        
        assert symbol.id == "test-1"
        assert symbol.type == SymbolType.CHARACTER
        assert symbol.name == "Test Character"
        assert symbol.novel_id == "novel-1"
        assert symbol.definition_uri == "file:///test.md"
        assert symbol.definition_range == {"start_line": 0, "end_line": 5}
        assert symbol.references == []
        assert symbol.metadata == {}
    
    def test_base_symbol_with_optional_fields(self):
        """Test creating BaseSymbol with optional fields."""
        symbol = BaseSymbol(
            id="test-2",
            type=SymbolType.LOCATION,
            name="Test Location",
            novel_id="novel-1",
            definition_uri="file:///test.md",
            definition_range={"start_line": 10, "end_line": 15},
            references=[{"uri": "file:///ref1.md", "line": 5}],
            metadata={"key": "value"},
        )
        
        assert len(symbol.references) == 1
        assert symbol.metadata == {"key": "value"}


class TestCharacterSymbol:
    """Tests for CharacterSymbol dataclass."""
    
    def test_character_symbol_creation(self):
        """Test creating a CharacterSymbol instance."""
        symbol = CharacterSymbol(
            id="char-1",
            name="John Doe",
            novel_id="novel-1",
            definition_uri="file:///characters.md",
            definition_range={"start_line": 0, "end_line": 10},
            age=42,
            status="alive",
            occupation="Detective",
            description="A rugged detective with a troubled past",
        )
        
        assert symbol.type == SymbolType.CHARACTER
        assert symbol.age == 42
        assert symbol.status == "alive"
        assert symbol.occupation == "Detective"
        assert "rugged" in symbol.description
    
    def test_character_symbol_defaults(self):
        """Test CharacterSymbol default values."""
        symbol = CharacterSymbol(
            id="char-2",
            name="Jane Doe",
            novel_id="novel-1",
            definition_uri="file:///characters.md",
            definition_range={"start_line": 0, "end_line": 5},
        )
        
        assert symbol.status == "alive"
        assert symbol.age is None
        assert symbol.personality == []
        assert symbol.goals == []
        assert symbol.relationships == []
        assert symbol.inventory == []
    
    def test_character_symbol_with_lists(self):
        """Test CharacterSymbol with list fields."""
        symbol = CharacterSymbol(
            id="char-3",
            name="Bob Smith",
            novel_id="novel-1",
            definition_uri="file:///characters.md",
            definition_range={"start_line": 0, "end_line": 5},
            personality=["brave", "loyal", "impulsive"],
            goals=["Solve the mystery", "Protect his family"],
            inventory=["Badge", "Gun", "Notebook"],
        )
        
        assert len(symbol.personality) == 3
        assert "brave" in symbol.personality
        assert len(symbol.goals) == 2
        assert len(symbol.inventory) == 3


class TestLocationSymbol:
    """Tests for LocationSymbol dataclass."""
    
    def test_location_symbol_creation(self):
        """Test creating a LocationSymbol instance."""
        symbol = LocationSymbol(
            id="loc-1",
            name="The Rusty Anchor Pub",
            novel_id="novel-1",
            definition_uri="file:///locations.md",
            definition_range={"start_line": 0, "end_line": 8},
            location_type="Building",
            description="A dimly lit pub in Boston's waterfront",
            region="Boston",
        )
        
        assert symbol.type == SymbolType.LOCATION
        assert symbol.location_type == "Building"
        assert "dimly lit" in symbol.description
        assert symbol.region == "Boston"
    
    def test_location_symbol_defaults(self):
        """Test LocationSymbol default values."""
        symbol = LocationSymbol(
            id="loc-2",
            name="Empty Location",
            novel_id="novel-1",
            definition_uri="file:///locations.md",
            definition_range={"start_line": 0, "end_line": 3},
        )
        
        assert symbol.visited_by == []
        assert symbol.events == []
        assert symbol.location_type is None


class TestItemSymbol:
    """Tests for ItemSymbol dataclass."""
    
    def test_item_symbol_creation(self):
        """Test creating an ItemSymbol instance."""
        symbol = ItemSymbol(
            id="item-1",
            name="The Ancient Sword",
            novel_id="novel-1",
            definition_uri="file:///items.md",
            definition_range={"start_line": 0, "end_line": 6},
            item_type="Weapon",
            description="A legendary sword with glowing runes",
            owner="John Doe",
            abilities=["Glows in darkness", "Cuts through steel"],
        )
        
        assert symbol.type == SymbolType.ITEM
        assert symbol.item_type == "Weapon"
        assert symbol.owner == "John Doe"
        assert len(symbol.abilities) == 2
    
    def test_item_symbol_defaults(self):
        """Test ItemSymbol default values."""
        symbol = ItemSymbol(
            id="item-2",
            name="Generic Item",
            novel_id="novel-1",
            definition_uri="file:///items.md",
            definition_range={"start_line": 0, "end_line": 3},
        )
        
        assert symbol.abilities == []
        assert symbol.owner is None


class TestLoreSymbol:
    """Tests for LoreSymbol dataclass."""
    
    def test_lore_symbol_creation(self):
        """Test creating a LoreSymbol instance."""
        symbol = LoreSymbol(
            id="lore-1",
            name="Magic System Basics",
            novel_id="novel-1",
            definition_uri="file:///lore.md",
            definition_range={"start_line": 0, "end_line": 15},
            lore_type="Magic System",
            description="The fundamental rules of magic in this world",
            category="Magic",
            rules=["Magic requires mana", "Cannot resurrect the dead"],
        )
        
        assert symbol.type == SymbolType.LORE
        assert symbol.lore_type == "Magic System"
        assert len(symbol.rules) == 2
    
    def test_lore_symbol_defaults(self):
        """Test LoreSymbol default values."""
        symbol = LoreSymbol(
            id="lore-2",
            name="Basic Lore",
            novel_id="novel-1",
            definition_uri="file:///lore.md",
            definition_range={"start_line": 0, "end_line": 3},
        )
        
        assert symbol.rules == []
        assert symbol.related_lore == []


class TestPlotPointSymbol:
    """Tests for PlotPointSymbol dataclass."""
    
    def test_plotpoint_symbol_creation(self):
        """Test creating a PlotPointSymbol instance."""
        symbol = PlotPointSymbol(
            id="plot-1",
            name="The Discovery",
            novel_id="novel-1",
            definition_uri="file:///plot.md",
            definition_range={"start_line": 0, "end_line": 8},
            plot_type="Inciting Incident",
            description="John discovers the mysterious artifact",
            chapter=1,
            volume=1,
            involved_characters=["John Doe", "Jane Smith"],
        )
        
        assert symbol.type == SymbolType.PLOTPOINT
        assert symbol.plot_type == "Inciting Incident"
        assert symbol.chapter == 1
        assert len(symbol.involved_characters) == 2
    
    def test_plotpoint_symbol_defaults(self):
        """Test PlotPointSymbol default values."""
        symbol = PlotPointSymbol(
            id="plot-2",
            name="Basic Plot Point",
            novel_id="novel-1",
            definition_uri="file:///plot.md",
            definition_range={"start_line": 0, "end_line": 3},
        )
        
        assert symbol.foreshadows == []
        assert symbol.callbacks == []
        assert symbol.chapter is None


class TestOutlineSymbol:
    """Tests for OutlineSymbol dataclass."""
    
    def test_outline_symbol_master_level(self):
        """Test creating a master outline symbol."""
        symbol = OutlineSymbol(
            id="outline-1",
            name="Master Outline",
            novel_id="novel-1",
            definition_uri="file:///outline.md",
            definition_range={"start_line": 0, "end_line": 50},
            level=OutlineLevel.MASTER,
        )
        
        assert symbol.type == SymbolType.OUTLINE
        assert symbol.level == OutlineLevel.MASTER
        assert symbol.volume_number is None
        assert symbol.chapter_number is None
    
    def test_outline_symbol_volume_level(self):
        """Test creating a volume outline symbol."""
        symbol = OutlineSymbol(
            id="outline-2",
            name="Volume 1 Outline",
            novel_id="novel-1",
            definition_uri="file:///outline.md",
            definition_range={"start_line": 0, "end_line": 20},
            level=OutlineLevel.VOLUME,
            volume_number=1,
        )
        
        assert symbol.level == OutlineLevel.VOLUME
        assert symbol.volume_number == 1
    
    def test_outline_symbol_chapter_level(self):
        """Test creating a chapter outline symbol."""
        symbol = OutlineSymbol(
            id="outline-3",
            name="Chapter 1 Outline",
            novel_id="novel-1",
            definition_uri="file:///outline.md",
            definition_range={"start_line": 0, "end_line": 5},
            level=OutlineLevel.CHAPTER,
            volume_number=1,
            chapter_number=1,
        )
        
        assert symbol.level == OutlineLevel.CHAPTER
        assert symbol.volume_number == 1
        assert symbol.chapter_number == 1
    
    def test_outline_symbol_with_children(self):
        """Test outline symbol with parent-child relationships."""
        symbol = OutlineSymbol(
            id="outline-4",
            name="Parent Outline",
            novel_id="novel-1",
            definition_uri="file:///outline.md",
            definition_range={"start_line": 0, "end_line": 10},
            level=OutlineLevel.VOLUME,
            volume_number=1,
            children=["outline-5", "outline-6"],
        )
        
        assert len(symbol.children) == 2
        assert symbol.parent is None


class TestEventSymbol:
    """Tests for EventSymbol dataclass."""
    
    def test_event_symbol_creation(self):
        """Test creating an EventSymbol instance."""
        symbol = EventSymbol(
            id="event-1",
            name="The First Meeting",
            novel_id="novel-1",
            definition_uri="file:///events.md",
            definition_range={"start_line": 0, "end_line": 10},
            event_id="evt-001",
            chapter=1,
            volume=1,
            time="Morning",
            location="The Rusty Anchor Pub",
            participants=["John Doe", "Jane Smith"],
            description="John meets Jane for the first time",
            importance="major",
        )
        
        assert symbol.type == SymbolType.EVENT
        assert symbol.event_id == "evt-001"
        assert symbol.chapter == 1
        assert len(symbol.participants) == 2
        assert symbol.importance == "major"
    
    def test_event_symbol_defaults(self):
        """Test EventSymbol default values."""
        symbol = EventSymbol(
            id="event-2",
            name="Basic Event",
            novel_id="novel-1",
            definition_uri="file:///events.md",
            definition_range={"start_line": 0, "end_line": 5},
        )
        
        assert symbol.importance == "minor"
        assert symbol.chapter == 0
        assert symbol.participants == []
        assert symbol.evidence == []
        assert symbol.impact == []


class TestRelationshipSymbol:
    """Tests for RelationshipSymbol dataclass."""
    
    def test_relationship_symbol_creation(self):
        """Test creating a RelationshipSymbol instance."""
        symbol = RelationshipSymbol(
            id="rel-1",
            name="John-Jane Relationship",
            novel_id="novel-1",
            definition_uri="file:///relationships.md",
            definition_range={"start_line": 0, "end_line": 8},
            from_character="John Doe",
            to_character="Jane Smith",
            relation_type="Friends",
            since_volume=1,
            since_chapter=1,
        )
        
        assert symbol.type == SymbolType.RELATIONSHIP
        assert symbol.from_character == "John Doe"
        assert symbol.to_character == "Jane Smith"
        assert symbol.relation_type == "Friends"
        assert symbol.since_volume == 1
        assert symbol.since_chapter == 1
    
    def test_relationship_symbol_defaults(self):
        """Test RelationshipSymbol default values."""
        symbol = RelationshipSymbol(
            id="rel-2",
            name="Basic Relationship",
            novel_id="novel-1",
            definition_uri="file:///relationships.md",
            definition_range={"start_line": 0, "end_line": 3},
        )
        
        assert symbol.history == []
        assert symbol.since_volume is None
        assert symbol.since_chapter is None


class TestChapterSymbol:
    """Tests for ChapterSymbol dataclass."""
    
    def test_chapter_symbol_creation(self):
        """Test creating a ChapterSymbol instance."""
        symbol = ChapterSymbol(
            id="chapter-1",
            name="Chapter 1: The Beginning",
            novel_id="novel-1",
            definition_uri="file:///chapters/chapter1.md",
            definition_range={"start_line": 0, "end_line": 100},
            chapter_number=1,
            volume_number=1,
            title="The Beginning",
            word_count=5000,
            summary="John discovers the mystery",
            status="final",
        )
        
        assert symbol.type == SymbolType.CHAPTER
        assert symbol.chapter_number == 1
        assert symbol.volume_number == 1
        assert symbol.title == "The Beginning"
        assert symbol.word_count == 5000
        assert symbol.status == "final"
    
    def test_chapter_symbol_defaults(self):
        """Test ChapterSymbol default values."""
        symbol = ChapterSymbol(
            id="chapter-2",
            name="Chapter 2",
            novel_id="novel-1",
            definition_uri="file:///chapters/chapter2.md",
            definition_range={"start_line": 0, "end_line": 50},
            chapter_number=2,
        )
        
        assert symbol.status == "draft"
        assert symbol.word_count == 0
        assert symbol.events == []
        assert symbol.characters_appearing == []
        assert symbol.outline_id is None


class TestSymbolTypeInheritance:
    """Tests to verify symbol types correctly inherit from BaseSymbol."""
    
    def test_character_symbol_inherits_base_fields(self):
        """Test that CharacterSymbol inherits BaseSymbol fields."""
        symbol = CharacterSymbol(
            id="char-1",
            name="Test",
            novel_id="novel-1",
            definition_uri="file:///test.md",
            definition_range={"start_line": 0, "end_line": 5},
        )
        
        # Check base fields exist
        assert hasattr(symbol, "id")
        assert hasattr(symbol, "type")
        assert hasattr(symbol, "name")
        assert hasattr(symbol, "novel_id")
        assert hasattr(symbol, "definition_uri")
        assert hasattr(symbol, "definition_range")
        assert hasattr(symbol, "references")
        assert hasattr(symbol, "metadata")
    
    def test_all_symbols_inherit_base_fields(self):
        """Test that all symbol types inherit BaseSymbol fields."""
        symbol_classes = [
            CharacterSymbol,
            LocationSymbol,
            ItemSymbol,
            LoreSymbol,
            PlotPointSymbol,
            OutlineSymbol,
            EventSymbol,
            RelationshipSymbol,
            ChapterSymbol,
        ]
        
        base_fields = ["id", "name", "novel_id", "definition_uri", "definition_range"]
        
        for symbol_class in symbol_classes:
            # Create instance with minimal required fields
            if symbol_class == OutlineSymbol:
                symbol = symbol_class(
                    id="test",
                    name="Test",
                    novel_id="novel-1",
                    definition_uri="file:///test.md",
                    definition_range={"start_line": 0, "end_line": 5},
                )
            elif symbol_class == RelationshipSymbol:
                symbol = symbol_class(
                    id="test",
                    name="Test",
                    novel_id="novel-1",
                    definition_uri="file:///test.md",
                    definition_range={"start_line": 0, "end_line": 5},
                )
            elif symbol_class == ChapterSymbol:
                symbol = symbol_class(
                    id="test",
                    name="Test",
                    novel_id="novel-1",
                    definition_uri="file:///test.md",
                    definition_range={"start_line": 0, "end_line": 5},
                    chapter_number=1,
                )
            else:
                symbol = symbol_class(
                    id="test",
                    name="Test",
                    novel_id="novel-1",
                    definition_uri="file:///test.md",
                    definition_range={"start_line": 0, "end_line": 5},
                )
            
            for field_name in base_fields:
                assert hasattr(symbol, field_name), f"{symbol_class.__name__} missing {field_name}"
