# src/novel/glossary.py
"""Glossary system for terminology consistency across novels.

Maintains consistent definitions for:
- Character names and titles
- Place names and locations
- Magic/technology terms
- Cultural concepts
- Specialized vocabulary
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.memory.base import BaseMemory, MemoryEntry
from src.memory.memsearch_adapter import MemSearchAdapter

logger = logging.getLogger(__name__)


class TermType(str, Enum):
    """Type of glossary term."""

    CHARACTER = "character"
    LOCATION = "location"
    OBJECT = "object"
    CONCEPT = "concept"
    MAGIC = "magic"
    TECHNOLOGY = "technology"
    CULTURE = "culture"
    TITLE = "title"
    ORGANIZATION = "organization"
    OTHER = "other"


class TermStatus(str, Enum):
    """Status of a glossary term."""

    DRAFT = "draft"  # Preliminary, may change
    APPROVED = "approved"  # Finalized, should not change
    DEPRECATED = "deprecated"  # No longer used
    ALIAS = "alias"  # Alternative name for another term


@dataclass
class GlossaryTerm:
    """A single glossary term with metadata."""

    term: str  # The term itself (e.g., "Aethelgard")
    type: TermType  # Type of term
    definition: str  # Detailed definition
    status: TermStatus = TermStatus.APPROVED
    aliases: list[str] = field(default_factory=list)  # Alternative names
    related_terms: list[str] = field(default_factory=list)  # Related term references
    notes: str = ""  # Additional notes
    metadata: dict[str, Any] = field(default_factory=dict)  # Custom metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "term": self.term,
            "type": self.type.value,
            "definition": self.definition,
            "status": self.status.value,
            "aliases": self.aliases,
            "related_terms": self.related_terms,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GlossaryTerm":
        """Create from dictionary."""
        return cls(
            term=data["term"],
            type=TermType(data["type"]),
            definition=data["definition"],
            status=TermStatus(data.get("status", "approved")),
            aliases=data.get("aliases", []),
            related_terms=data.get("related_terms", []),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {}),
        )


class GlossaryManager(BaseMemory):
    """Manages glossary terms with semantic search."""

    DEFAULT_GLOSSARY_DIR = "/memory/glossary"

    def __init__(
        self,
        base_path: str | None = None,
        namespace: str = "default",
        embedding_provider: str | None = None,
        milvus_uri: str | None = None,
        collection: str = "glossary_memory",
    ) -> None:
        super().__init__(namespace=namespace)
        self._adapter = MemSearchAdapter(
            base_path=base_path,
            namespace=namespace,
            embedding_provider=embedding_provider,
            milvus_uri=milvus_uri,
            collection=collection,
        )
        logger.info(f"GlossaryManager initialized for namespace '{namespace}'")

    # BaseMemory abstract method implementations
    async def store(self, key: str, value: Any, metadata: dict[str, Any] | None = None) -> None:
        """Store a glossary term.

        Args:
            key: Term identifier (e.g., 'aethelgard')
            value: GlossaryTerm or dictionary
            metadata: Optional metadata
        """
        if not key.startswith(self.DEFAULT_GLOSSARY_DIR):
            key = f"{self.DEFAULT_GLOSSARY_DIR}/{key}"

        # Convert GlossaryTerm to dict if needed
        if isinstance(value, GlossaryTerm):
            value = value.to_dict()
            if metadata is None:
                metadata = {}
            metadata["_type"] = "GlossaryTerm"

        await self._adapter.store(key, value, metadata)

    async def retrieve(self, key: str) -> MemoryEntry | None:
        """Retrieve a glossary term.

        Args:
            key: Term identifier

        Returns:
            MemoryEntry if found, None otherwise
        """
        if not key.startswith(self.DEFAULT_GLOSSARY_DIR):
            key = f"{self.DEFAULT_GLOSSARY_DIR}/{key}"
        return await self._adapter.retrieve(key)

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        """Search for glossary terms by semantic similarity.

        Args:
            query: Natural language query
            limit: Maximum results

        Returns:
            List of matching glossary entries
        """
        return await self._adapter.search(query, limit)

    async def delete(self, key: str) -> bool:
        """Delete a glossary term.

        Args:
            key: Term identifier

        Returns:
            True if deleted, False if not found
        """
        if not key.startswith(self.DEFAULT_GLOSSARY_DIR):
            key = f"{self.DEFAULT_GLOSSARY_DIR}/{key}"
        return await self._adapter.delete(key)

    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all glossary keys.

        Args:
            prefix: Optional prefix filter

        Returns:
            List of keys
        """
        full_prefix = (
            f"{self.DEFAULT_GLOSSARY_DIR}/{prefix}" if prefix else self.DEFAULT_GLOSSARY_DIR
        )
        keys = await self._adapter.list_keys(full_prefix)
        # Strip the base path from keys
        stripped_keys = []
        for key in keys:
            if key.startswith(self.DEFAULT_GLOSSARY_DIR):
                stripped_keys.append(key[len(self.DEFAULT_GLOSSARY_DIR) + 1 :])
            else:
                stripped_keys.append(key)
        return stripped_keys

    # Domain-specific methods
    async def store_term(self, term: GlossaryTerm) -> None:
        """Store a glossary term.

        Args:
            term: GlossaryTerm instance
        """
        key = f"terms/{term.term.lower().replace(' ', '_')}"
        metadata = {
            "type": term.type.value,
            "status": term.status.value,
            "aliases": term.aliases,
        }
        await self.store(key, term, metadata)

    async def retrieve_term(self, term: str) -> GlossaryTerm | None:
        """Retrieve a glossary term by name.

        Args:
            term: Term name

        Returns:
            GlossaryTerm if found, None otherwise
        """
        key = f"terms/{term.lower().replace(' ', '_')}"
        entry = await self.retrieve(key)
        if entry and entry.value:
            try:
                if isinstance(entry.value, dict) and entry.value.get("term"):
                    return GlossaryTerm.from_dict(entry.value)
                elif isinstance(entry.value, GlossaryTerm):
                    return entry.value
            except Exception as e:
                logger.warning(f"Failed to parse glossary term {term}: {e}")
        return None

    async def search_terms(
        self,
        query: str,
        term_type: TermType | None = None,
        status: TermStatus | None = None,
        limit: int = 20,
    ) -> list[GlossaryTerm]:
        """Search glossary terms with filters.

        Args:
            query: Search query
            term_type: Optional type filter
            status: Optional status filter
            limit: Maximum results

        Returns:
            List of matching GlossaryTerm instances
        """
        entries = await self.search(query, limit=limit)
        terms = []
        for entry in entries:
            if "terms/" in entry.key:
                try:
                    if isinstance(entry.value, dict) and entry.value.get("term"):
                        term = GlossaryTerm.from_dict(entry.value)
                        # Apply filters
                        if term_type and term.type != term_type:
                            continue
                        if status and term.status != status:
                            continue
                        terms.append(term)
                    elif isinstance(entry.value, GlossaryTerm):
                        term = entry.value
                        if term_type and term.type != term_type:
                            continue
                        if status and term.status != status:
                            continue
                        terms.append(term)
                except Exception as e:
                    logger.warning(f"Failed to parse glossary entry {entry.key}: {e}")
        return terms

    async def get_all_terms(
        self,
        term_type: TermType | None = None,
        status: TermStatus | None = None,
    ) -> list[GlossaryTerm]:
        """Get all glossary terms with optional filters.

        Args:
            term_type: Optional type filter
            status: Optional status filter

        Returns:
            List of GlossaryTerm instances
        """
        keys = await self.list_keys("terms/")
        terms = []
        for key in keys:
            entry = await self.retrieve(key)
            if entry and entry.value:
                try:
                    if isinstance(entry.value, dict) and entry.value.get("term"):
                        term = GlossaryTerm.from_dict(entry.value)
                        if term_type and term.type != term_type:
                            continue
                        if status and term.status != status:
                            continue
                        terms.append(term)
                    elif isinstance(entry.value, GlossaryTerm):
                        term = entry.value
                        if term_type and term.type != term_type:
                            continue
                        if status and term.status != status:
                            continue
                        terms.append(term)
                except Exception as e:
                    logger.warning(f"Failed to parse glossary term {key}: {e}")
        return terms

    async def create_alias(self, main_term: str, alias: str) -> bool:
        """Create an alias for an existing term.

        Args:
            main_term: Main term name
            alias: Alias name

        Returns:
            True if successful, False if main term not found
        """
        term = await self.retrieve_term(main_term)
        if not term:
            return False

        # Add alias to main term
        if alias not in term.aliases:
            term.aliases.append(alias)
            await self.store_term(term)

        # Create alias entry
        alias_term = GlossaryTerm(
            term=alias,
            type=term.type,
            definition=f"Alias for {main_term}. See {main_term} for full definition.",
            status=TermStatus.ALIAS,
            aliases=[main_term],
            related_terms=[main_term],
            notes=f"Primary term: {main_term}",
            metadata={"is_alias": True, "primary_term": main_term},
        )
        await self.store_term(alias_term)

        return True

    async def get_term_by_alias(self, alias: str) -> GlossaryTerm | None:
        """Get the primary term for an alias.

        Args:
            alias: Alias name

        Returns:
            Primary GlossaryTerm if found, None otherwise
        """
        # First try to retrieve as a regular term
        term = await self.retrieve_term(alias)
        if term:
            # If it's an alias, find the primary term
            if term.status == TermStatus.ALIAS:
                primary_name = term.metadata.get("primary_term")
                if primary_name:
                    return await self.retrieve_term(primary_name)
            return term

        # Search for terms where this is an alias
        entries = await self.search(alias, limit=10)
        for entry in entries:
            if "terms/" in entry.key:
                try:
                    if isinstance(entry.value, dict) and entry.value.get("term"):
                        potential_term = GlossaryTerm.from_dict(entry.value)
                        if alias in potential_term.aliases:
                            return potential_term
                except Exception:
                    continue

        return None

    async def validate_consistency(self, text: str) -> list[tuple[str, str]]:
        """Validate text for glossary consistency.

        Args:
            text: Text to validate

        Returns:
            List of (term, issue) tuples where issues were found
        """
        # Simple implementation: check for undefined terms
        # This could be enhanced with NLP
        issues = []

        # Get all approved terms
        all_terms = await self.get_all_terms(status=TermStatus.APPROVED)


        # For each word in text (simplistic)
        words = text.lower().split()
        for word in words:
            # Clean word (remove punctuation)
            clean_word = "".join(c for c in word if c.isalnum())
            if clean_word and len(clean_word) > 2:  # Ignore short words
                # Check if word matches a term
                for term in all_terms:
                    if clean_word == term.term.lower():
                        # Term is defined, no issue
                        break
                    elif clean_word in (a.lower() for a in term.aliases):
                        # Alias is defined, no issue
                        break
                else:
                    # Word not found in glossary
                    # This is just a warning, not necessarily an issue
                    pass

        return issues

    # Synchronous wrappers
    def store_term_sync(self, term: GlossaryTerm) -> None:
        """Synchronous wrapper for store_term."""
        import asyncio

        asyncio.run(self.store_term(term))

    def retrieve_term_sync(self, term: str) -> GlossaryTerm | None:
        """Synchronous wrapper for retrieve_term."""
        import asyncio

        return asyncio.run(self.retrieve_term(term))

    def close(self) -> None:
        """Close underlying adapter."""
        self._adapter.close()


# Default glossary instance
def get_default_glossary(
    base_path: str | None = None,
    namespace: str = "default",
) -> GlossaryManager:
    """Get default glossary instance.

    Args:
        base_path: Optional base path
        namespace: Namespace

    Returns:
        GlossaryManager instance
    """
    return GlossaryManager(base_path=base_path, namespace=namespace)
