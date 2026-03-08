"""Tests for the SymbolIndex class with LRU cache."""

import pytest
from novelwriter_lsp.index import SymbolIndex
from novelwriter_lsp.types import (
    CharacterSymbol,
    SymbolType,
)


@pytest.fixture
def index() -> SymbolIndex:
    """Create a fresh SymbolIndex for each test."""
    return SymbolIndex(max_size=100)


@pytest.fixture
def small_index() -> SymbolIndex:
    """Create a small SymbolIndex for LRU eviction tests."""
    return SymbolIndex(max_size=3)


class TestSymbolIndex:
    """Test suite for SymbolIndex basic operations."""

    def test_init(self, index: SymbolIndex) -> None:
        """Test index initialization."""
        assert len(index) == 0
        assert index.max_size == 100
        assert index.get_cache_info()["size"] == 0

    def test_update_single_symbol(self, index: SymbolIndex) -> None:
        """Test adding a single symbol to the index."""
        symbol = CharacterSymbol(
            id="char_john_1",
            name="John Doe",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 0,
                "end_line": 0,
                "start_character": 0,
                "end_character": 10,
            },
            age=42,
        )

        index.update(symbol)

        assert len(index) == 1
        assert "John Doe" in index
        retrieved = index.get_symbol("John Doe")
        assert retrieved is not None
        assert retrieved.name == "John Doe"
        assert retrieved.type == SymbolType.CHARACTER

    def test_update_multiple_symbols(self, index: SymbolIndex) -> None:
        """Test adding multiple symbols to the index."""
        symbols = [
            CharacterSymbol(
                id=f"char_{i}_{i}",
                name=f"Character {i}",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": i,
                    "end_line": i,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
            for i in range(5)
        ]

        for symbol in symbols:
            index.update(symbol)

        assert len(index) == 5
        for i in range(5):
            assert f"Character {i}" in index

    def test_get_symbol_not_found(self, index: SymbolIndex) -> None:
        """Test getting a symbol that doesn't exist."""
        result = index.get_symbol("Nonexistent")
        assert result is None

    def test_get_symbol_by_id(self, index: SymbolIndex) -> None:
        """Test retrieving a symbol by its ID."""
        symbol = CharacterSymbol(
            id="char_unique_1",
            name="Unique Character",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 0,
                "end_line": 0,
                "start_character": 0,
                "end_character": 10,
            },
        )

        index.update(symbol)

        retrieved = index.get_symbol_by_id("char_unique_1")
        assert retrieved is not None
        assert retrieved.name == "Unique Character"

    def test_get_symbol_by_id_not_found(self, index: SymbolIndex) -> None:
        """Test getting a symbol by ID that doesn't exist."""
        result = index.get_symbol_by_id("nonexistent_id")
        assert result is None

    def test_search_by_name(self, index: SymbolIndex) -> None:
        """Test searching for symbols by name."""
        symbols = [
            CharacterSymbol(
                id=f"char_{i}_{i}",
                name=f"Hero {i}",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": i,
                    "end_line": i,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
            for i in range(3)
        ]

        for symbol in symbols:
            index.update(symbol)

        results = index.search("Hero")
        assert len(results) == 3

        results = index.search("Hero 1")
        assert len(results) == 1
        assert results[0].name == "Hero 1"

    def test_search_with_type_filter(self, index: SymbolIndex) -> None:
        """Test searching with symbol type filter."""
        from novelwriter_lsp.types import LocationSymbol

        index.update(
            CharacterSymbol(
                id="char_1",
                name="John",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 0,
                    "end_line": 0,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        index.update(
            LocationSymbol(
                id="loc_1",
                name="John's House",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 1,
                    "end_line": 1,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        results = index.search("John", symbol_type=SymbolType.CHARACTER)
        assert len(results) == 1
        assert results[0].type == SymbolType.CHARACTER

    def test_get_symbols_by_uri(self, index: SymbolIndex) -> None:
        """Test getting all symbols for a specific URI."""
        uri1 = "file:///document1.md"
        uri2 = "file:///document2.md"

        index.update(
            CharacterSymbol(
                id="char_1",
                name="Character 1",
                novel_id="novel_1",
                definition_uri=uri1,
                definition_range={
                    "start_line": 0,
                    "end_line": 0,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        index.update(
            CharacterSymbol(
                id="char_2",
                name="Character 2",
                novel_id="novel_1",
                definition_uri=uri1,
                definition_range={
                    "start_line": 1,
                    "end_line": 1,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        index.update(
            CharacterSymbol(
                id="char_3",
                name="Character 3",
                novel_id="novel_1",
                definition_uri=uri2,
                definition_range={
                    "start_line": 0,
                    "end_line": 0,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        symbols = index.get_symbols_by_uri(uri1)
        assert len(symbols) == 2

        symbols = index.get_symbols_by_uri(uri2)
        assert len(symbols) == 1

    def test_remove_by_uri(self, index: SymbolIndex) -> None:
        """Test removing all symbols for a URI."""
        uri = "file:///test.md"

        index.update(
            CharacterSymbol(
                id="char_1",
                name="Character 1",
                novel_id="novel_1",
                definition_uri=uri,
                definition_range={
                    "start_line": 0,
                    "end_line": 0,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        index.update(
            CharacterSymbol(
                id="char_2",
                name="Character 2",
                novel_id="novel_1",
                definition_uri=uri,
                definition_range={
                    "start_line": 1,
                    "end_line": 1,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        removed = index.remove(uri)

        assert len(removed) == 2
        assert len(index) == 0
        assert "Character 1" not in index
        assert "Character 2" not in index

    def test_clear(self, index: SymbolIndex) -> None:
        """Test clearing all symbols from the index."""
        for i in range(5):
            index.update(
                CharacterSymbol(
                    id=f"char_{i}_{i}",
                    name=f"Character {i}",
                    novel_id="novel_1",
                    definition_uri="file:///test.md",
                    definition_range={
                        "start_line": i,
                        "end_line": i,
                        "start_character": 0,
                        "end_character": 10,
                    },
                )
            )

        assert len(index) == 5
        index.clear()
        assert len(index) == 0
        assert index.get_cache_info()["size"] == 0

    def test_update_existing_symbol(self, index: SymbolIndex) -> None:
        """Test updating an existing symbol."""
        symbol = CharacterSymbol(
            id="char_1",
            name="John Doe",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 0,
                "end_line": 0,
                "start_character": 0,
                "end_character": 10,
            },
            age=42,
        )

        index.update(symbol)

        updated_symbol = CharacterSymbol(
            id="char_1",
            name="John Doe",
            novel_id="novel_1",
            definition_uri="file:///test.md",
            definition_range={
                "start_line": 0,
                "end_line": 0,
                "start_character": 0,
                "end_character": 10,
            },
            age=43,
        )

        index.update(updated_symbol)

        assert len(index) == 1
        retrieved = index.get_symbol("John Doe")
        assert retrieved is not None
        assert isinstance(retrieved, CharacterSymbol)
        assert retrieved.age == 43


class TestLRUEviction:
    """Test suite for LRU cache eviction behavior."""

    def test_lru_eviction(self, small_index: SymbolIndex) -> None:
        """Test that LRU eviction works when max_size is exceeded."""
        for i in range(4):
            small_index.update(
                CharacterSymbol(
                    id=f"char_{i}_{i}",
                    name=f"Character {i}",
                    novel_id="novel_1",
                    definition_uri="file:///test.md",
                    definition_range={
                        "start_line": i,
                        "end_line": i,
                        "start_character": 0,
                        "end_character": 10,
                    },
                )
            )

        assert len(small_index) == 3
        assert "Character 0" not in small_index
        assert "Character 1" in small_index
        assert "Character 2" in small_index
        assert "Character 3" in small_index

    def test_lru_access_prevents_eviction(self, small_index: SymbolIndex) -> None:
        """Test that accessing a symbol prevents it from being evicted."""
        for i in range(3):
            small_index.update(
                CharacterSymbol(
                    id=f"char_{i}_{i}",
                    name=f"Character {i}",
                    novel_id="novel_1",
                    definition_uri="file:///test.md",
                    definition_range={
                        "start_line": i,
                        "end_line": i,
                        "start_character": 0,
                        "end_character": 10,
                    },
                )
            )

        small_index.get_symbol("Character 0")

        small_index.update(
            CharacterSymbol(
                id="char_3",
                name="Character 3",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 3,
                    "end_line": 3,
                    "start_character": 0,
                    "end_character": 10,
                },
            )
        )

        assert "Character 0" in small_index
        assert "Character 1" not in small_index

    def test_cache_info(self, small_index: SymbolIndex) -> None:
        """Test cache info reporting."""
        for i in range(2):
            small_index.update(
                CharacterSymbol(
                    id=f"char_{i}_{i}",
                    name=f"Character {i}",
                    novel_id="novel_1",
                    definition_uri="file:///test.md",
                    definition_range={
                        "start_line": i,
                        "end_line": i,
                        "start_character": 0,
                        "end_character": 10,
                    },
                )
            )

        info = small_index.get_cache_info()
        assert info["size"] == 2
        assert info["max_size"] == 3
        assert info["documents"] == 1
        assert info["utilization"] == 2 / 3


class TestFindSymbolAtPosition:
    """Test suite for find_symbol_at_position method."""

    def test_find_symbol_at_position_exact_match(self, index: SymbolIndex) -> None:
        """Test finding a symbol at exact definition position."""
        index.update(
            CharacterSymbol(
                id="char_1",
                name="John Doe",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 5,
                    "end_line": 5,
                    "start_character": 0,
                    "end_character": 20,
                },
            )
        )

        result = index.find_symbol_at_position("file:///test.md", 5, 10)
        assert result is not None
        assert result.name == "John Doe"

    def test_find_symbol_at_position_out_of_range(self, index: SymbolIndex) -> None:
        """Test finding a symbol when position is outside definition range."""
        index.update(
            CharacterSymbol(
                id="char_1",
                name="John Doe",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 5,
                    "end_line": 5,
                    "start_character": 0,
                    "end_character": 20,
                },
            )
        )

        result = index.find_symbol_at_position("file:///test.md", 10, 10)
        assert result is None

    def test_find_symbol_at_position_multiple_symbols(self, index: SymbolIndex) -> None:
        """Test finding correct symbol when multiple symbols exist in document."""
        index.update(
            CharacterSymbol(
                id="char_1",
                name="John Doe",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 5,
                    "end_line": 5,
                    "start_character": 0,
                    "end_character": 20,
                },
            )
        )

        index.update(
            CharacterSymbol(
                id="char_2",
                name="Jane Doe",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 10,
                    "end_line": 10,
                    "start_character": 0,
                    "end_character": 20,
                },
            )
        )

        result = index.find_symbol_at_position("file:///test.md", 10, 5)
        assert result is not None
        assert result.name == "Jane Doe"

    def test_find_symbol_at_position_uri_mismatch(self, index: SymbolIndex) -> None:
        """Test finding symbol when URI doesn't match."""
        index.update(
            CharacterSymbol(
                id="char_1",
                name="John Doe",
                novel_id="novel_1",
                definition_uri="file:///test.md",
                definition_range={
                    "start_line": 5,
                    "end_line": 5,
                    "start_character": 0,
                    "end_character": 20,
                },
            )
        )

        result = index.find_symbol_at_position("file:///other.md", 5, 10)
        assert result is None
