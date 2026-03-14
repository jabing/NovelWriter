"""PostgreSQL database client with async support.

This module provides an async client for PostgreSQL database operations
using SQLAlchemy 2.0 async engine and asyncpg driver.
Features:
    - Connection pooling
    - Async CRUD operations
    - Transaction support
    - Query helpers
    - Error handling
"""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

from src.novel_agent.db.postgres_models import (
    Base,
    CharacterProfile,
    CharacterStatus,
    Contradiction,
    ImportanceLevel,
    SeverityLevel,
    StoryFact,
    TimelineEvent,
)
from src.novel_agent.utils.config import Settings, get_settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """Async PostgreSQL client for novel agent system.
    Provides high-level async interface for database operations
    with connection pooling, transaction support, and error handling.
    Attributes:
        engine: SQLAlchemy async engine
        async_session: Async session factory
        settings: Application settings
    Example:
        >>> client = PostgresClient()
        >>> await client.initialize()
        >>> character = await client.create_character("Alice")
        >>> events = await client.get_character_timeline(character.id)
        >>> await client.close()
    """

    def __init__(self, database_url: str | None = None, settings: Settings | None = None):
        """Initialize PostgreSQL client.
        Args:
            database_url: Optional database URL (defaults to settings.postgres_url)
            settings: Optional settings instance (defaults to get_settings())
        """
        self.settings = settings or get_settings()
        self.database_url = database_url or self.settings.postgres_url
        if not self.database_url:
            raise ValueError(
                "Database URL must be provided via parameter or settings.postgres_url"
            )
        # Convert postgres:// to postgresql+asyncpg://
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        # Create engine with connection pooling
        # Only apply pooling for PostgreSQL, not SQLite
        engine_kwargs = {
            "echo": self.settings.log_level == "DEBUG",
        }
        if "postgresql" in self.database_url:
            engine_kwargs.update({
                "pool_size": 5,
                "max_overflow": 10,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            })
        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            **engine_kwargs
        )
        # Create async session factory
        self.async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info(f"PostgreSQL client initialized: {self.database_url.split('@')[-1]}")
    async def initialize(self) -> None:
        """Initialize database tables.
        Creates all tables defined in postgres_models if they don't exist.
        For production, use Alembic migrations instead.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")
    async def close(self) -> None:
        """Close database connection pool."""
        await self.engine.dispose()
        logger.info("Database connection closed")
    @asynccontextmanager
    async def session(self):
        """Provide async session context manager.
        Yields:
            AsyncSession: Database session
        Example:
            >>> async with client.session() as session:
            ...     result = await session.execute(select(CharacterProfile))
        """
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    # ============================================================
    # Character Profile Operations
    # ============================================================
    async def create_character(
        self,
        name: str,
        status: str = CharacterStatus.ACTIVE.value,
        birth_chapter: int | None = None,
        death_chapter: int | None = None,
        aliases: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CharacterProfile:
        """Create a new character profile.
        Args:
            name: Character name
            status: Character status (active/deceased/unknown/missing)
            birth_chapter: Chapter where character was born
            death_chapter: Chapter where character died
            aliases: List of character aliases
            metadata: Additional metadata
        Returns:
            Created CharacterProfile instance
        Raises:
            ValueError: If validation fails
        """
        # Validate chapter consistency
        if birth_chapter is not None and death_chapter is not None:
            if death_chapter < birth_chapter:
                raise ValueError(
                    f"Death chapter ({death_chapter}) cannot be before "
                    f"birth chapter ({birth_chapter})"
                )
        async with self.session() as session:
            character = CharacterProfile(
                name=name,
                status=status,
                birth_chapter=birth_chapter,
                death_chapter=death_chapter,
                aliases=json.dumps(aliases) if aliases else None,
                meta_data=json.dumps(metadata) if metadata else None,
            )
            session.add(character)
            await session.flush()
            await session.refresh(character)
            logger.info(f"Created character: {character.name} (ID: {character.id})")
            return character
    async def get_character(self, character_id: int) -> CharacterProfile | None:
        """Get character by ID.
        Args:
            character_id: Character ID
        Returns:
            CharacterProfile if found, None otherwise
        """
        async with self.session() as session:
            result = await session.execute(
                select(CharacterProfile)
                .options(selectinload(CharacterProfile.timeline_events))
                .where(CharacterProfile.id == character_id)
            )
            return result.scalar_one_or_none()
    async def get_character_by_name(self, name: str) -> CharacterProfile | None:
        """Get character by name.
        Args:
            name: Character name
        Returns:
            CharacterProfile if found, None otherwise
        """
        async with self.session() as session:
            result = await session.execute(
                select(CharacterProfile).where(CharacterProfile.name == name)
            )
            return result.scalar_one_or_none()
    async def list_characters(
        self,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CharacterProfile]:
        """List characters with optional filtering.
        Args:
            status: Filter by status
            limit: Maximum number of results
            offset: Result offset
        Returns:
            List of CharacterProfile instances
        """
        async with self.session() as session:
            query = select(CharacterProfile)
            if status:
                query = query.where(CharacterProfile.status == status)
            query = query.limit(limit).offset(offset).order_by(CharacterProfile.id)
            result = await session.execute(query)
            return list(result.scalars().all())
    async def update_character(
        self,
        character_id: int,
        **updates: Any,
    ) -> CharacterProfile | None:
        """Update character profile.
        Args:
            character_id: Character ID
            **updates: Fields to update
        Returns:
            Updated CharacterProfile if found, None otherwise
        Raises:
            ValueError: If validation fails
        """
        # Validate chapter consistency
        birth_chapter = updates.get("birth_chapter")
        death_chapter = updates.get("death_chapter")
        if birth_chapter is not None and death_chapter is not None:
            if death_chapter < birth_chapter:
                raise ValueError(
                    f"Death chapter ({death_chapter}) cannot be before "
                    f"birth chapter ({birth_chapter})"
                )
        # Serialize JSON fields
        if "aliases" in updates and isinstance(updates["aliases"], list):
            updates["aliases"] = json.dumps(updates["aliases"])
        if "meta_data" in updates and isinstance(updates["meta_data"], dict):
            updates["meta_data"] = json.dumps(updates["meta_data"])
        async with self.session() as session:
            result = await session.execute(
                update(CharacterProfile)
                .where(CharacterProfile.id == character_id)
                .values(**updates)
                .returning(CharacterProfile)
            )
            character = result.scalar_one_or_none()
            if character:
                logger.info(f"Updated character: {character.name} (ID: {character.id})")
            return character
    async def delete_character(self, character_id: int) -> bool:
        """Delete character and all related data.
        Args:
            character_id: Character ID
        Returns:
            True if deleted, False if not found
        """
        async with self.session() as session:
            character = await session.get(CharacterProfile, character_id)
            if not character:
                return False
            await session.delete(character)
            logger.info(f"Deleted character ID: {character_id}")
            return True
    # ============================================================
    # Timeline Event Operations
    # ============================================================
    async def create_timeline_event(
        self,
        chapter: int,
        event_type: str,
        description: str,
        character_id: int | None = None,
        importance: str = ImportanceLevel.MEDIUM.value,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        """Create a timeline event.
        Args:
            chapter: Chapter number
            event_type: Type of event
            description: Event description
            character_id: Related character ID
            importance: Importance level
            metadata: Additional metadata
        Returns:
            Created TimelineEvent instance
        """
        async with self.session() as session:
            event = TimelineEvent(
                character_id=character_id,
                chapter=chapter,
                event_type=event_type,
                description=description,
                importance=importance,
                meta_data=json.dumps(metadata) if metadata else None,
            )
            session.add(event)
            await session.flush()
            await session.refresh(event)
            logger.debug(f"Created timeline event: {event_type} at chapter {chapter}")
            return event
    async def get_character_timeline(
        self,
        character_id: int,
        start_chapter: int | None = None,
        end_chapter: int | None = None,
    ) -> list[TimelineEvent]:
        """Get timeline events for a character.
        Args:
            character_id: Character ID
            start_chapter: Optional start chapter filter
            end_chapter: Optional end chapter filter
        Returns:
            List of TimelineEvent instances
        """
        async with self.session() as session:
            query = (
                select(TimelineEvent)
                .where(TimelineEvent.character_id == character_id)
                .order_by(TimelineEvent.chapter)
            )
            if start_chapter is not None:
                query = query.where(TimelineEvent.chapter >= start_chapter)
            if end_chapter is not None:
                query = query.where(TimelineEvent.chapter <= end_chapter)
            result = await session.execute(query)
            return list(result.scalars().all())
    async def get_chapter_events(
        self,
        chapter: int,
        event_type: str | None = None,
    ) -> list[TimelineEvent]:
        """Get all events for a chapter.
        Args:
            chapter: Chapter number
            event_type: Optional event type filter
        Returns:
            List of TimelineEvent instances
        """
        async with self.session() as session:
            query = (
                select(TimelineEvent)
                .where(TimelineEvent.chapter == chapter)
                .order_by(TimelineEvent.id)
            )
            if event_type:
                query = query.where(TimelineEvent.event_type == event_type)
            result = await session.execute(query)
            return list(result.scalars().all())
    # ============================================================
    # Story Fact Operations
    # ============================================================
    async def create_story_fact(
        self,
        entity_type: str,
        category: str,
        attribute: str,
        value: str,
        source_chapter: int,
        entity_id: int | None = None,
        confidence: float = 1.0,
        is_immutable: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> StoryFact:
        """Create a story fact.
        Args:
            entity_type: Type of entity
            category: Fact category
            attribute: Attribute name
            value: Attribute value
            source_chapter: Source chapter
            entity_id: Related entity ID
            confidence: Confidence score (0.0-1.0)
            is_immutable: Whether fact is immutable
            metadata: Additional metadata
        Returns:
            Created StoryFact instance
        Raises:
            ValueError: If confidence is out of range
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")
        async with self.session() as session:
            fact = StoryFact(
                entity_type=entity_type,
                entity_id=entity_id,
                category=category,
                attribute=attribute,
                value=value,
                source_chapter=source_chapter,
                confidence=confidence,
                is_immutable=is_immutable,
                meta_data=json.dumps(metadata) if metadata else None,
            )
            session.add(fact)
            await session.flush()
            await session.refresh(fact)
            logger.debug(
                f"Created story fact: {entity_type}.{attribute} = {value[:50]}"
            )
            return fact
    async def get_entity_facts(
        self,
        entity_type: str,
        entity_id: int | None = None,
        category: str | None = None,
    ) -> list[StoryFact]:
        """Get facts for an entity.
        Args:
            entity_type: Entity type
            entity_id: Optional entity ID
            category: Optional category filter
        Returns:
            List of StoryFact instances
        """
        async with self.session() as session:
            query = select(StoryFact).where(StoryFact.entity_type == entity_type)
            if entity_id is not None:
                query = query.where(StoryFact.entity_id == entity_id)
            if category:
                query = query.where(StoryFact.category == category)
            result = await session.execute(query.order_by(StoryFact.id))
            return list(result.scalars().all())
    async def get_chapter_facts(self, chapter: int) -> list[StoryFact]:
        """Get all facts from a chapter.
        Args:
            chapter: Chapter number
        Returns:
            List of StoryFact instances
        """
        async with self.session() as session:
            result = await session.execute(
                select(StoryFact)
                .where(StoryFact.source_chapter == chapter)
                .order_by(StoryFact.id)
            )
            return list(result.scalars().all())
    async def search_facts(
        self,
        query_text: str,
        entity_type: str | None = None,
        limit: int = 50,
    ) -> list[StoryFact]:
        """Search facts by text.
        Args:
            query_text: Search query
            entity_type: Optional entity type filter
            limit: Maximum results
        Returns:
            List of matching StoryFact instances
        """
        async with self.session() as session:
            query = select(StoryFact).where(
                StoryFact.value.ilike(f"%{query_text}%")
            )
            if entity_type:
                query = query.where(StoryFact.entity_type == entity_type)
            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    # ============================================================
    # Contradiction Operations
    # ============================================================
    async def create_contradiction(
        self,
        fact1_id: int,
        fact2_id: int,
        contradiction_type: str,
        severity: str = SeverityLevel.MEDIUM.value,
        description: str | None = None,
    ) -> Contradiction:
        """Create a contradiction record.
        Args:
            fact1_id: First conflicting fact ID
            fact2_id: Second conflicting fact ID
            contradiction_type: Type of contradiction
            severity: Severity level
            description: Human-readable description
        Returns:
            Created Contradiction instance
        """
        async with self.session() as session:
            contradiction = Contradiction(
                fact1_id=fact1_id,
                fact2_id=fact2_id,
                contradiction_type=contradiction_type,
                severity=severity,
                description=description,
            )
            session.add(contradiction)
            await session.flush()
            await session.refresh(contradiction)
            logger.info(
                f"Created contradiction: {contradiction_type} "
                f"(facts {fact1_id} vs {fact2_id})"
            )
            return contradiction
    async def get_unresolved_contradictions(
        self,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[Contradiction]:
        """Get unresolved contradictions.
        Args:
            severity: Optional severity filter
            limit: Maximum results
        Returns:
            List of unresolved Contradiction instances
        """
        async with self.session() as session:
            query = (
                select(Contradiction)
                .where(Contradiction.resolved == False)  # noqa: E712
                .order_by(Contradiction.severity, Contradiction.detected_at)
            )
            if severity:
                query = query.where(Contradiction.severity == severity)
            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    async def resolve_contradiction(
        self,
        contradiction_id: int,
        resolution_notes: str | None = None,
    ) -> Contradiction | None:
        """Mark contradiction as resolved.
        Args:
            contradiction_id: Contradiction ID
            resolution_notes: Notes on resolution
        Returns:
            Updated Contradiction if found, None otherwise
        """
        async with self.session() as session:
            result = await session.execute(
                update(Contradiction)
                .where(Contradiction.id == contradiction_id)
                .values(
                    resolved=True,
                    resolution_notes=resolution_notes,
                    resolved_at=datetime.utcnow(),
                )
                .returning(Contradiction)
            )
            contradiction = result.scalar_one_or_none()
            if contradiction:
                logger.info(f"Resolved contradiction ID: {contradiction_id}")
            return contradiction
    # ============================================================
    # Utility Methods
    # ============================================================
    async def get_statistics(self) -> dict[str, Any]:
        """Get database statistics.
        Returns:
            Dictionary with counts and statistics
        """
        async with self.session() as session:
            char_count = await session.scalar(
                select(func.count(CharacterProfile.id))
            )
            event_count = await session.scalar(
                select(func.count(TimelineEvent.id))
            )
            fact_count = await session.scalar(select(func.count(StoryFact.id)))
            contradiction_count = await session.scalar(
                select(func.count(Contradiction.id))
            )
            unresolved_count = await session.scalar(
                select(func.count(Contradiction.id)).where(
                    Contradiction.resolved == False  # noqa: E712
                )
            )
            return {
                "characters": char_count,
                "timeline_events": event_count,
                "story_facts": fact_count,
                "contradictions": contradiction_count,
                "unresolved_contradictions": unresolved_count,
            }
    async def clear_all_data(self) -> None:
        """Clear all data from tables (for testing).
        WARNING: This will delete all data! Use only in tests.
        """
        async with self.session() as session:
            await session.execute(delete(Contradiction))
            await session.execute(delete(StoryFact))
            await session.execute(delete(TimelineEvent))
            await session.execute(delete(CharacterProfile))
        logger.warning("Cleared all data from database")
