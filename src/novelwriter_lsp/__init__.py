"""NovelWriter LSP Server - A Language Server Protocol implementation for AI writing systems.

This package provides LSP features for novel writing including:
- Symbol definitions (Character, Location, Item, Lore, PlotPoint, etc.)
- Go to definition
- Find references
- Document symbols
- Rename symbols
- Diagnostics and validation

Usage:
    python -m novelwriter_lsp

Or install and run:
    pip install -e .
    novelwriter-lsp
"""

__version__ = "0.1.0"
__author__ = "NovelWriter Team"

from novelwriter_lsp.server import NovelWriterLSP

__all__ = ["NovelWriterLSP", "__version__"]
