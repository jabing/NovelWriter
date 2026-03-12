"""Tests for the AliasIndex class."""

import pytest
from novelwriter_lsp.index import AliasIndex


@pytest.fixture
def alias_index() -> AliasIndex:
    """Create a fresh AliasIndex for each test."""
    return AliasIndex()


class TestAliasIndex:
    """Test suite for AliasIndex basic operations."""

    def test_add_single_alias(self, alias_index: AliasIndex) -> None:
        """Test adding a single alias mapping."""
        alias_index.add_alias("John", "John Doe")

        assert alias_index.get_symbol_name("John") == "John Doe"

    def test_add_multiple_aliases_for_same_symbol(self, alias_index: AliasIndex) -> None:
        """Test adding multiple aliases for the same symbol."""
        alias_index.add_alias("John", "John Doe")
        alias_index.add_alias("Johnny", "John Doe")

        assert alias_index.get_symbol_name("John") == "John Doe"
        assert alias_index.get_symbol_name("Johnny") == "John Doe"

    def test_get_nonexistent_alias(self, alias_index: AliasIndex) -> None:
        """Test getting a symbol name for a nonexistent alias."""
        result = alias_index.get_symbol_name("Nonexistent")

        assert result is None

    def test_remove_symbol_clears_all_aliases(self, alias_index: AliasIndex) -> None:
        """Test that removing a symbol clears all its aliases."""
        alias_index.add_alias("John", "John Doe")
        alias_index.add_alias("Johnny", "John Doe")
        alias_index.add_alias("Mr. Doe", "John Doe")

        assert alias_index.get_symbol_name("John") == "John Doe"
        assert alias_index.get_symbol_name("Johnny") == "John Doe"
        assert alias_index.get_symbol_name("Mr. Doe") == "John Doe"

        alias_index.remove_symbol("John Doe")

        assert alias_index.get_symbol_name("John") is None
        assert alias_index.get_symbol_name("Johnny") is None
        assert alias_index.get_symbol_name("Mr. Doe") is None

    def test_clear_all_aliases(self, alias_index: AliasIndex) -> None:
        """Test clearing all alias mappings."""
        alias_index.add_alias("John", "John Doe")
        alias_index.add_alias("Mary", "Mary Smith")
        alias_index.add_alias("Bob", "Bob Johnson")

        assert alias_index.get_symbol_name("John") == "John Doe"
        assert alias_index.get_symbol_name("Mary") == "Mary Smith"
        assert alias_index.get_symbol_name("Bob") == "Bob Johnson"

        alias_index.clear()

        assert alias_index.get_symbol_name("John") is None
        assert alias_index.get_symbol_name("Mary") is None
        assert alias_index.get_symbol_name("Bob") is None

    def test_alias_overwrite(self, alias_index: AliasIndex) -> None:
        """Test that adding the same alias overwrites the previous mapping."""
        alias_index.add_alias("John", "John Doe")

        assert alias_index.get_symbol_name("John") == "John Doe"

        alias_index.add_alias("John", "John Smith")

        assert alias_index.get_symbol_name("John") == "John Smith"

    def test_concurrent_aliases_for_different_symbols(self, alias_index: AliasIndex) -> None:
        """Test that different symbols can have different aliases concurrently."""
        alias_index.add_alias("John", "John Doe")
        alias_index.add_alias("Johnny", "John Doe")
        alias_index.add_alias("Mary", "Mary Smith")
        alias_index.add_alias("Bob", "Bob Johnson")

        assert alias_index.get_symbol_name("John") == "John Doe"
        assert alias_index.get_symbol_name("Johnny") == "John Doe"
        assert alias_index.get_symbol_name("Mary") == "Mary Smith"
        assert alias_index.get_symbol_name("Bob") == "Bob Johnson"

    def test_remove_nonexistent_symbol(self, alias_index: AliasIndex) -> None:
        """Test that removing a nonexistent symbol doesn't raise an error."""
        alias_index.add_alias("John", "John Doe")

        alias_index.remove_symbol("Nonexistent Symbol")

        assert alias_index.get_symbol_name("John") == "John Doe"

    def test_remove_partial_aliases(self, alias_index: AliasIndex) -> None:
        """Test that removing one symbol doesn't affect other symbols' aliases."""
        alias_index.add_alias("John", "John Doe")
        alias_index.add_alias("Johnny", "John Doe")
        alias_index.add_alias("Mary", "Mary Smith")
        alias_index.add_alias("Bob", "Bob Johnson")

        alias_index.remove_symbol("John Doe")

        assert alias_index.get_symbol_name("John") is None
        assert alias_index.get_symbol_name("Johnny") is None
        assert alias_index.get_symbol_name("Mary") == "Mary Smith"
        assert alias_index.get_symbol_name("Bob") == "Bob Johnson"

    def test_empty_index_operations(self, alias_index: AliasIndex) -> None:
        """Test operations on an empty AliasIndex."""
        alias_index.clear()

        alias_index.remove_symbol("Any Symbol")

        assert alias_index.get_symbol_name("Any Alias") is None

    def test_alias_with_empty_string(self, alias_index: AliasIndex) -> None:
        """Test handling of empty strings as aliases or symbol names."""
        alias_index.add_alias("", "Empty Alias Symbol")
        alias_index.add_alias("Valid", "")

        assert alias_index.get_symbol_name("") == "Empty Alias Symbol"
        assert alias_index.get_symbol_name("Valid") == ""

    def test_case_sensitive_aliases(self, alias_index: AliasIndex) -> None:
        """Test that aliases are case-sensitive."""
        alias_index.add_alias("john", "John Doe")
        alias_index.add_alias("John", "John Smith")
        alias_index.add_alias("JOHN", "John Johnson")

        assert alias_index.get_symbol_name("john") == "John Doe"
        assert alias_index.get_symbol_name("John") == "John Smith"
        assert alias_index.get_symbol_name("JOHN") == "John Johnson"

    def test_special_characters_in_aliases(self, alias_index: AliasIndex) -> None:
        """Test handling of special characters in aliases."""
        alias_index.add_alias("John-Doe", "John Doe")
        alias_index.add_alias("John_Doe", "John Doe")
        alias_index.add_alias("John.Doe", "John Doe")

        assert alias_index.get_symbol_name("John-Doe") == "John Doe"
        assert alias_index.get_symbol_name("John_Doe") == "John Doe"
        assert alias_index.get_symbol_name("John.Doe") == "John Doe"
