import time
import pytest

from novelwriter_lsp.index import AliasIndex, SymbolIndex
from novelwriter_lsp.parser import parse_document
from novelwriter_lsp.types import CharacterSymbol


class TestAliasPerformance:
    @pytest.mark.slow
    @pytest.mark.performance
    def test_alias_index_lookup_performance(self) -> None:
        """Test alias lookup performance (O(1)) - 200 lookups should be < 10ms."""
        idx = AliasIndex()

        for i in range(1000):
            idx.add_alias(f"alias_{i}", f"symbol_{i}")

        start = time.time()
        for i in range(200):
            result = idx.get_symbol_name(f"alias_{i}")
        duration = time.time() - start

        assert duration < 0.01, f"Alias lookup took {duration}s, expected < 0.01s"

    @pytest.mark.slow
    @pytest.mark.performance
    def test_parser_1000_lines_performance(self) -> None:
        """Test parser performance with 1000 lines of content - should be < 200ms."""
        lines = []
        for i in range(1000):
            lines.append(f'@Character: Character {i} {{ aliases: ["C{i}"] }}')

        content = "\n".join(lines)

        start = time.time()
        symbols = parse_document(content, "file:///test.md")
        duration = time.time() - start

        assert duration < 0.2, f"Parsing took {duration}s, expected < 0.2s"
        assert len(symbols) == 1000

    @pytest.mark.slow
    @pytest.mark.performance
    def test_index_update_with_aliases_performance(self) -> None:
        """Test index update with 100 symbols containing aliases - should be < 100ms."""
        idx = SymbolIndex()

        symbols = []
        for i in range(100):
            symbol = CharacterSymbol(
                id=f"char_{i}",
                name=f"Character {i}",
                novel_id="novel_1",
                definition_uri=f"file:///test{i}.md",
                definition_range={"start_line": i, "end_line": i, "start_character": 0, "end_character": 10},
                aliases=[f"C{i}", f"Char{i}"],
            )
            symbols.append(symbol)

        start = time.time()
        for symbol in symbols:
            idx.update(symbol)
        duration = time.time() - start

        assert duration < 0.1, f"Index update took {duration}s, expected < 0.1s"

    @pytest.mark.slow
    @pytest.mark.performance
    def test_definition_lookup_performance(self) -> None:
        """Test definition lookup performance with 100 lookups - should be < 1s."""
        idx = SymbolIndex()

        content_lines = []
        for i in range(100):
            content_lines.append(f'@Character: Character {i} {{ aliases: ["C{i}"] }}')

        content_lines.append("")
        content_lines.append("C50 walked in.")

        content = "\n".join(content_lines)

        symbols = parse_document(content, "file:///test.md")

        for symbol in symbols:
            idx.update(symbol)

        start = time.time()
        result = None
        for _ in range(100):
            result = idx.get_symbol_by_alias("C50")
        duration = time.time() - start

        assert result is not None, "Definition lookup returned None"
        assert result.name == "Character 50"

        assert duration < 1.0, f"100 lookups took {duration}s, expected < 1.0s"
