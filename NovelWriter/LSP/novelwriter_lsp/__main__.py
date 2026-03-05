"""Entry point for running NovelWriter LSP server as a module.

Usage:
    python -m novelwriter_lsp [--help] [--version]

Or start the server:
    python -m novelwriter_lsp
"""

import argparse
import sys

from novelwriter_lsp import __version__
from novelwriter_lsp.server import NovelWriterLSP


def main() -> int:
    """Main entry point for the NovelWriter LSP server.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = argparse.ArgumentParser(
        prog="novelwriter_lsp",
        description="NovelWriter LSP Server - Language Server Protocol for AI writing systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m novelwriter_lsp              Start the LSP server
  python -m novelwriter_lsp --version    Show version information
  python -m novelwriter_lsp --help       Show this help message

Features:
  - Symbol definitions (Character, Location, Item, Lore, PlotPoint, etc.)
  - Go to definition
  - Find references
  - Document symbols
  - Rename symbols
  - Diagnostics and validation
        """,
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version information and exit",
    )
    
    args = parser.parse_args()
    
    # Start the LSP server
    # In production, this would use stdio transport
    # For now, we just show the help to verify the entry point works
    if len(sys.argv) == 1:
        # No arguments provided, start server mode
        # This will be implemented in later tasks
        print("NovelWriter LSP Server starting...")
        print("Server mode will be implemented in Phase 1 Task 1")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
