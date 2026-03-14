# src/utils/logger.py
"""Logging configuration."""

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a configured logger with Rich formatting.

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Console handler with Rich formatting
    console = Console(stderr=True)
    handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        rich_tracebacks=True,
    )
    handler.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def setup_file_logging(log_file: str, level: str = "INFO") -> None:
    """Set up file logging in addition to console.

    Args:
        log_file: Path to log file
        level: Log level
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Add file handler to root logger
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
