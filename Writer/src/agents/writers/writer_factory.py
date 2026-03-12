# src/agents/writers/writer_factory.py
"""Factory for creating genre-specific writers."""

from typing import Any

from src.agents.writers.base_writer import BaseWriter
from src.agents.writers.fantasy import FantasyWriter
from src.agents.writers.history import HistoryWriter
from src.agents.writers.military import MilitaryWriter
from src.agents.writers.romance import RomanceWriter
from src.agents.writers.scifi import SciFiWriter

# Mapping of genre to writer class
WRITERS: dict[str, type[BaseWriter]] = {
    "scifi": SciFiWriter,
    "fantasy": FantasyWriter,
    "romance": RomanceWriter,
    "darkromance": RomanceWriter,  # Dark romance uses romance writer
    "history": HistoryWriter,
    "military": MilitaryWriter,
    "thriller": RomanceWriter,  # Thriller can use romance writer for now
}


def get_writer(
    genre: str,
    llm: Any,
    memory: Any = None,
) -> BaseWriter:
    """Get a writer for the specified genre.

    Args:
        genre: Genre name (scifi, fantasy, romance, history, military)
        llm: LLM instance for text generation
        memory: Optional memory system

    Returns:
        Genre-specific writer instance

    Raises:
        ValueError: If genre is not supported
    """
    genre_lower = genre.lower().replace("-", "").replace(" ", "")

    if genre_lower not in WRITERS:
        available = ", ".join(WRITERS.keys())
        raise ValueError(
            f"Unknown genre '{genre}'. Available genres: {available}"
        )

    writer_class = WRITERS[genre_lower]
    return writer_class(
        name=f"{genre.title()} Writer",
        llm=llm,
        memory=memory,
    )


def get_available_genres() -> list[str]:
    """Get list of supported genres.

    Returns:
        List of genre names
    """
    return list(WRITERS.keys())
