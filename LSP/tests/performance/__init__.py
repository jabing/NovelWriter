import pytest
import time

from novelwriter_lsp.index import AliasIndex, SymbolIndex
from novelwriter_lsp.parser import parse_document
from novelwriter_lsp.types import CharacterSymbol


@pytest.fixture
def performance_index() -> SymbolIndex:
    return SymbolIndex(max_size=10000)


def pytest_configure(config):
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
