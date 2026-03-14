"""Entry point for running NovelWriter LSP server as a module.

Usage:
    python -m novelwriter_lsp [--help] [--version]

Or start the server:
    python -m novelwriter_lsp
"""

import argparse
import logging
import sys

from novelwriter_lsp import __version__


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the LSP server."""
    # Configure logging level
    level = logging.DEBUG if debug else logging.INFO

    # Configure logger with stderr output (LSP stdout reserved for protocol communication)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # Use stderr for logging, stdout reserved for LSP protocol
    )

    # Reduce log noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("pygls").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured (level={logging.getLevelName(level)})")


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
  python -m novelwriter_lsp --debug     Enable debug logging
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

    _ = parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show version information and exit",
    )

    _ = parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    setup_logging(debug=bool(args.debug))
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Starting NovelWriter LSP Server v{__version__}")

        # Import the server instance that has all feature handlers registered
        from novelwriter_lsp.server import server

        logger.info("Server ready, waiting for client connections...")
        server.start_io()

        logger.info("Server shutdown complete")
        return 0

    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        return 0

    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
