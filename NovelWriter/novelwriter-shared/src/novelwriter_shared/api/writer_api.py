"""Writer API interface definitions.

This module defines the abstract interface for Writer operations,
allowing LSP and other components to interact with Writer functionality.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from novelwriter_shared.models.character import CharacterProfile
from novelwriter_shared.models.fact import Fact


class WriterAPI(ABC):
    """Abstract interface for Writer operations.

    This interface defines the contract for interacting with the Writer
    component, allowing LSP and other tools to access shared data.
    """

    @abstractmethod
    async def get_character(self, name: str) -> CharacterProfile | None:
        """Get a character profile by name.

        Args:
            name: Character name

        Returns:
            CharacterProfile if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_characters(self, status: str | None = None) -> list[CharacterProfile]:
        """List all character profiles.

        Args:
            status: Optional status filter

        Returns:
            List of matching character profiles
        """
        pass

    @abstractmethod
    async def create_character(
        self,
        name: str,
        aliases: list[str] | None = None,
        birth_chapter: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CharacterProfile:
        """Create a new character profile.

        Args:
            name: Character name
            aliases: Alternative names
            birth_chapter: Chapter where character was introduced
            metadata: Additional metadata

        Returns:
            Created CharacterProfile
        """
        pass

    @abstractmethod
    async def update_character(self, profile: CharacterProfile) -> bool:
        """Update an existing character profile.

        Args:
            profile: Profile to update

        Returns:
            True if updated successfully
        """
        pass

    @abstractmethod
    async def delete_character(self, name: str) -> bool:
        """Delete a character profile.

        Args:
            name: Character name to delete

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def get_fact(self, fact_id: str) -> Fact | None:
        """Get a fact by ID.

        Args:
            fact_id: Fact identifier

        Returns:
            Fact if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_facts(
        self,
        fact_type: str | None = None,
        entity: str | None = None,
        chapter: int | None = None,
    ) -> list[Fact]:
        """List facts with optional filters.

        Args:
            fact_type: Filter by fact type
            entity: Filter by entity name
            chapter: Filter by chapter number

        Returns:
            List of matching facts
        """
        pass

    @abstractmethod
    async def create_fact(
        self,
        fact_type: str,
        content: str,
        chapter_origin: int,
        importance: float = 0.5,
        entities: list[str] | None = None,
    ) -> Fact:
        """Create a new fact.

        Args:
            fact_type: Type of fact
            content: Fact content
            chapter_origin: Chapter where fact originated
            importance: Importance score (0.0-1.0)
            entities: Related entity names

        Returns:
            Created Fact
        """
        pass

    @abstractmethod
    async def get_chapter(self, chapter_number: int) -> dict[str, Any] | None:
        """Get chapter content and metadata.

        Args:
            chapter_number: Chapter number

        Returns:
            Chapter data if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_chapters(self) -> list[dict[str, Any]]:
        """List all chapters.

        Returns:
            List of chapter metadata
        """
        pass
