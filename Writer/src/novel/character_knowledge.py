"""Character Knowledge for tracking what each character knows.

This module implements the CharacterKnowledge class which provides a character-specific
interface for managing knowledge, detecting cognitive conflicts, and tracking when
facts were learned.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.novel.cognitive_graph import CognitiveGraph

logger = logging.getLogger(__name__)


class KnowledgeSource(str, Enum):
    """How a character learned a fact."""

    DIRECT = "direct"  # Character witnessed or experienced directly
    HEARSAY = "hearsay"  # Learned from another character
    INFERENCE = "inference"  # Deduced from other facts
    DISCOVERY = "discovery"  # Found through investigation


@dataclass
class KnowledgeEntry:
    """Entry representing a character's knowledge of a fact."""

    fact_id: str
    learned_chapter: int  # Chapter when character learned this fact
    source: KnowledgeSource
    confidence: float = 1.0
    context: str = ""  # How they learned it (optional description)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "fact_id": self.fact_id,
            "learned_chapter": self.learned_chapter,
            "source": self.source.value,
            "confidence": self.confidence,
            "context": self.context,
        }


@dataclass
class CognitiveConflict:
    """Represents a detected cognitive conflict."""

    fact_id: str
    fact_content: str
    conflict_type: str  # "unknown_knowledge" or "insufficient_confidence"
    description: str
    chapter: int
    action_description: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "fact_id": self.fact_id,
            "fact_content": self.fact_content,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "chapter": self.chapter,
            "action_description": self.action_description,
        }


class CharacterKnowledge:
    """Manages what a character knows and detects cognitive conflicts.

    This class wraps CognitiveGraph to provide a character-specific interface
    for knowledge management. It tracks:
    - What facts the character knows
    - When (which chapter) they learned each fact
    - How they learned it (source)
    - Their confidence in the knowledge

    Cognitive conflicts occur when a character acts on knowledge they shouldn't
    have (either because they haven't learned it yet, or their source doesn't
    justify the action).

    Usage:
        >>> graph = CognitiveGraph()
        >>> graph.add_character_node("char1", "林晚", tier=0)
        >>> graph.add_fact_node("fact1", "secret", "丞相私通敌国", "char2", 3)
        >>>
        >>> ck = CharacterKnowledge("char1", graph)
        >>> ck.learn_fact("fact1", source="hearsay", chapter=5)
        >>> ck.knows_fact("fact1")  # True
        >>> conflicts = ck.check_cognitive_conflict("林晚质问丞相私通敌国", chapter=4)
        # Returns conflict because char1 doesn't know fact1 until chapter 5
    """

    def __init__(
        self,
        character_id: str,
        cognitive_graph: CognitiveGraph | None = None,
    ) -> None:
        """Initialize CharacterKnowledge for a specific character.

        Args:
            character_id: ID of the character whose knowledge this tracks
            cognitive_graph: Optional CognitiveGraph to use for storage.
                            If None, creates a new graph.
        """
        self.character_id = character_id
        self._graph = cognitive_graph or CognitiveGraph()

        # Internal tracking of when facts were learned
        # Maps fact_id -> KnowledgeEntry
        self._knowledge_entries: dict[str, KnowledgeEntry] = {}

        # Knowledge scope - what the character can reasonably know
        # Based on character tier and story context
        self._scope: dict[str, Any] = {
            "tier": None,  # Will be populated from graph if available
            "locations_known": [],  # Locations the character has visited
            "characters_known": [],  # Characters this character has met
            "events_witnessed": [],  # Events the character witnessed
        }

        # Try to get character tier from graph
        if self._graph:
            char_node = self._graph.get_node(character_id)
            if char_node:
                self._scope["tier"] = char_node.get("tier", 1)

    def learn_fact(
        self,
        fact_id: str,
        chapter: int = 1,
        source: str = "direct",
        confidence: float = 1.0,
        context: str = "",
    ) -> bool:
        """Record that the character has learned a fact.

        Args:
            fact_id: ID of the fact learned
            chapter: Chapter number when the character learned this fact
            source: How they learned it ("direct", "hearsay", "inference", "discovery")
            confidence: Confidence level (0.0-1.0)
            context: Optional description of how they learned it

        Returns:
            True if successfully recorded, False if fact doesn't exist
        """
        # Verify the fact exists in the graph
        fact_node = self._graph.get_node(fact_id)
        if not fact_node:
            logger.warning(
                f"Cannot learn fact {fact_id}: fact does not exist in graph"
            )
            return False

        # Convert source string to enum
        try:
            knowledge_source = KnowledgeSource(source.lower())
        except ValueError:
            knowledge_source = KnowledgeSource.DIRECT

        # Create knowledge entry
        entry = KnowledgeEntry(
            fact_id=fact_id,
            learned_chapter=chapter,
            source=knowledge_source,
            confidence=max(0.0, min(1.0, confidence)),
            context=context,
        )
        self._knowledge_entries[fact_id] = entry

        # Also update the graph's knowledge edge
        self._graph.add_character_knowledge(
            self.character_id,
            fact_id,
            confidence=confidence,
            source=source,
        )

        logger.debug(
            f"Character {self.character_id} learned fact {fact_id} "
            f"(chapter={chapter}, source={source}, confidence={confidence})"
        )
        return True

    def forget_fact(self, fact_id: str) -> bool:
        """Remove a fact from the character's knowledge.

        This could represent:
        - The character genuinely forgot
        - Memory manipulation in the story
        - Knowledge correction

        Args:
            fact_id: ID of the fact to forget

        Returns:
            True if the fact was forgotten, False if it wasn't known
        """
        if fact_id not in self._knowledge_entries:
            return False

        del self._knowledge_entries[fact_id]

        # Remove the edge from the graph
        # Note: CognitiveGraph doesn't have a remove_edge method,
        # so we use networkx directly
        if self._graph.graph.has_edge(self.character_id, fact_id):
            self._graph.graph.remove_edge(self.character_id, fact_id)

        logger.debug(f"Character {self.character_id} forgot fact {fact_id}")
        return True

    def knows_fact(self, fact_id: str, chapter: int | None = None) -> bool:
        """Check if the character knows a fact.

        Args:
            fact_id: ID of the fact to check
            chapter: Optional chapter number. If provided, checks if the character
                    knew the fact BY this chapter.

        Returns:
            True if the character knows the fact (by the given chapter if specified)
        """
        if fact_id not in self._knowledge_entries:
            return False

        if chapter is not None:
            entry = self._knowledge_entries[fact_id]
            return entry.learned_chapter <= chapter

        return True

    def get_knowledge(self, chapter: int | None = None) -> list[dict[str, Any]]:
        """Get all facts known by this character.

        Args:
            chapter: Optional chapter number. If provided, returns only facts
                    known by this chapter.

        Returns:
            List of fact dictionaries with knowledge metadata
        """
        knowledge = []
        for fact_id, entry in self._knowledge_entries.items():
            if chapter is not None and entry.learned_chapter > chapter:
                continue

            fact_node = self._graph.get_node(fact_id)
            if fact_node:
                knowledge.append({
                    "id": fact_id,
                    "content": fact_node.get("content", ""),
                    "fact_type": fact_node.get("fact_type", ""),
                    "source_chapter": fact_node.get("chapter", 0),
                    "learned_chapter": entry.learned_chapter,
                    "knowledge_source": entry.source.value,
                    "confidence": entry.confidence,
                    "context": entry.context,
                })

        return knowledge

    def get_knowledge_by_type(
        self, fact_type: str, chapter: int | None = None
    ) -> list[dict[str, Any]]:
        """Get facts of a specific type known by this character.

        Args:
            fact_type: Type of fact to filter by (e.g., "event", "secret", "relationship")
            chapter: Optional chapter number. If provided, returns only facts
                    known by this chapter.

        Returns:
            List of fact dictionaries of the specified type
        """
        all_knowledge = self.get_knowledge(chapter=chapter)
        return [k for k in all_knowledge if k.get("fact_type") == fact_type]

    def check_cognitive_conflict(
        self, action_description: str, chapter: int
    ) -> list[CognitiveConflict]:
        """Check if an action requires knowledge the character doesn't have.

        This method detects cognitive conflicts where a character acts on
        information they shouldn't know (either because they haven't learned
        it yet, or their knowledge source doesn't justify the action).

        Args:
            action_description: Description of the character's action
            chapter: Chapter number where this action occurs

        Returns:
            List of detected CognitiveConflict objects (empty if no conflicts)
        """
        conflicts: list[CognitiveConflict] = []

        # Get all facts from the graph to check against
        all_facts = self._get_all_fact_contents()

        # Check each fact to see if it's referenced in the action
        for fact_id, fact_content, fact_type in all_facts:
            if self._action_references_fact(action_description, fact_content):
                # Check if character knows this fact by this chapter
                if not self.knows_fact(fact_id, chapter=chapter):
                    conflicts.append(
                        CognitiveConflict(
                            fact_id=fact_id,
                            fact_content=fact_content,
                            conflict_type="unknown_knowledge",
                            description=(
                                f"Character acts on knowledge they shouldn't have: "
                                f"'{fact_content}' (character hasn't learned this by chapter {chapter})"
                            ),
                            chapter=chapter,
                            action_description=action_description,
                        )
                    )
                else:
                    # Check if confidence and source justify the action
                    entry = self._knowledge_entries.get(fact_id)
                    if entry:
                        # Hearsay with low confidence may not justify direct action
                        if (
                            entry.source == KnowledgeSource.HEARSAY
                            and entry.confidence < 0.5
                        ):
                            conflicts.append(
                                CognitiveConflict(
                                    fact_id=fact_id,
                                    fact_content=fact_content,
                                    conflict_type="insufficient_confidence",
                                    description=(
                                        f"Character acts on unreliable knowledge: "
                                        f"'{fact_content}' (hearsay with {entry.confidence:.0%} confidence)"
                                    ),
                                    chapter=chapter,
                                    action_description=action_description,
                                )
                            )

        return conflicts

    def update_from_chapter(
        self, chapter: int, facts_in_chapter: list[dict[str, Any]]
    ) -> int:
        """Update character knowledge after reading a chapter.

        This method processes facts that appeared in a chapter and updates
        the character's knowledge accordingly. It uses heuristics to determine
        what the character learned.

        Args:
            chapter: Chapter number being processed
            facts_in_chapter: List of fact dictionaries that appeared in this chapter
                            Each dict should have: fact_id, content, fact_type, and
                            optionally how_learned

        Returns:
            Number of new facts learned
        """
        learned_count = 0

        for fact_info in facts_in_chapter:
            fact_id = fact_info.get("fact_id") or fact_info.get("id")
            if not fact_id:
                continue

            # Check if character already knows this fact
            if self.knows_fact(fact_id):
                continue

            # Determine if this character should know this fact
            # Heuristic: Character knows facts they witnessed or were told about
            how_learned = fact_info.get("how_learned", "unknown")
            character_present = fact_info.get("character_present", False)
            told_by = fact_info.get("told_by")

            if how_learned == "witnessed" or character_present:
                source = "direct"
                confidence = 1.0
            elif told_by:
                source = "hearsay"
                confidence = 0.7
            elif how_learned == "inferred":
                source = "inference"
                confidence = 0.6
            elif how_learned == "discovered":
                source = "discovery"
                confidence = 0.9
            else:
                # Default: assume direct knowledge for facts in chapters
                # where the character is involved
                continue  # Skip if we can't determine how they learned it

            # Learn the fact
            if self.learn_fact(
                fact_id=fact_id,
                chapter=chapter,
                source=source,
                confidence=confidence,
                context=fact_info.get("context", ""),
            ):
                learned_count += 1

        logger.debug(
            f"Character {self.character_id} learned {learned_count} facts "
            f"from chapter {chapter}"
        )
        return learned_count

    def get_knowledge_scope(self) -> dict[str, Any]:
        """Get what the character can reasonably know.

        Returns a dictionary describing the character's cognitive scope:
        - Their tier/role in the story
        - Locations they've been to
        - Characters they've interacted with
        - Events they've witnessed

        Returns:
            Dictionary with scope information
        """
        # Update scope from graph if available
        char_node = self._graph.get_node(self.character_id)
        if char_node:
            self._scope["tier"] = char_node.get("tier", 1)

        # Get all facts to determine scope
        all_knowledge = self.get_knowledge()

        # Extract locations, characters, and events from knowledge
        for fact in all_knowledge:
            fact_type = fact.get("fact_type", "")
            content = fact.get("content", "")

            if fact_type == "location":
                if content not in self._scope["locations_known"]:
                    self._scope["locations_known"].append(content)
            elif fact_type == "relationship":
                # Extract character names from relationship facts
                if content not in self._scope["characters_known"]:
                    self._scope["characters_known"].append(content)
            elif fact_type == "event":
                if content not in self._scope["events_witnessed"]:
                    self._scope["events_witnessed"].append(content)

        return self._scope.copy()

    def get_fact_learning_info(self, fact_id: str) -> KnowledgeEntry | None:
        """Get information about when and how a fact was learned.

        Args:
            fact_id: ID of the fact to query

        Returns:
            KnowledgeEntry if the character knows the fact, None otherwise
        """
        return self._knowledge_entries.get(fact_id)

    def get_knowledge_summary(self, chapter: int | None = None) -> dict[str, Any]:
        """Get a summary of the character's knowledge.

        Args:
            chapter: Optional chapter number. If provided, summarizes knowledge
                    as of this chapter.

        Returns:
            Dictionary with counts by fact type and source
        """
        knowledge = self.get_knowledge(chapter=chapter)

        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}

        for fact in knowledge:
            fact_type = fact.get("fact_type", "unknown")
            source = fact.get("knowledge_source", "unknown")

            by_type[fact_type] = by_type.get(fact_type, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total_facts": len(knowledge),
            "by_type": by_type,
            "by_source": by_source,
        }

    def _get_all_fact_contents(self) -> list[tuple[str, str, str]]:
        """Get all facts from the graph.

        Returns:
            List of (fact_id, content, fact_type) tuples
        """
        facts = []
        for node_id, data in self._graph.graph.nodes(data=True):
            if data.get("node_type") == "fact":
                facts.append((
                    node_id,
                    data.get("content", ""),
                    data.get("fact_type", ""),
                ))
        return facts

    def _action_references_fact(
        self, action_description: str, fact_content: str
    ) -> bool:
        """Check if an action description references a fact.

        Uses simple keyword matching to determine if the action is related
        to the fact content.

        Args:
            action_description: The action to check
            fact_content: The fact content to check against

        Returns:
            True if the action appears to reference the fact
        """
        # Normalize for comparison
        action_lower = action_description.lower()
        content_lower = fact_content.lower()

        # Check for exact content match
        if content_lower in action_lower:
            return True

        # Extract key terms from fact content (simplified)
        # For Chinese text, extract meaningful words (2+ chars)
        # For English text, extract words

        # Chinese word extraction (simplified - 2-4 character segments)
        chinese_pattern = r'[\u4e00-\u9fff]{2,4}'
        chinese_terms = re.findall(chinese_pattern, fact_content)

        # English word extraction
        english_pattern = r'\b[a-zA-Z]{3,}\b'
        english_terms = re.findall(english_pattern, fact_content.lower())

        all_terms = chinese_terms + english_terms

        # Check if significant terms appear in action
        # Use terms that are more unique/meaningful
        meaningful_terms = [
            term for term in all_terms
            if len(term) >= 2 and term not in ['的', '是', '了', '在', '和', 'the', 'was', 'had']
        ]

        # If multiple meaningful terms appear, it's likely a reference
        matches = sum(1 for term in meaningful_terms if term.lower() in action_lower)

        # Require at least 2 term matches or 1 significant match
        return matches >= 2 or (matches >= 1 and len(meaningful_terms) <= 3)

    @property
    def fact_count(self) -> int:
        """Get total number of facts known by this character."""
        return len(self._knowledge_entries)

    @property
    def graph(self) -> CognitiveGraph:
        """Get the underlying cognitive graph."""
        return self._graph

    def to_dict(self) -> dict[str, Any]:
        """Serialize character knowledge to dictionary.

        Returns:
            Dictionary representation for persistence
        """
        return {
            "character_id": self.character_id,
            "knowledge_entries": {
                fid: entry.to_dict()
                for fid, entry in self._knowledge_entries.items()
            },
            "scope": self._scope,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        cognitive_graph: CognitiveGraph,
    ) -> CharacterKnowledge:
        """Deserialize character knowledge from dictionary.

        Args:
            data: Dictionary representation
            cognitive_graph: CognitiveGraph instance to use

        Returns:
            CharacterKnowledge instance
        """
        ck = cls(
            character_id=data["character_id"],
            cognitive_graph=cognitive_graph,
        )

        # Restore knowledge entries
        for fact_id, entry_data in data.get("knowledge_entries", {}).items():
            entry = KnowledgeEntry(
                fact_id=fact_id,
                learned_chapter=entry_data["learned_chapter"],
                source=KnowledgeSource(entry_data["source"]),
                confidence=entry_data.get("confidence", 1.0),
                context=entry_data.get("context", ""),
            )
            ck._knowledge_entries[fact_id] = entry

        # Restore scope
        if "scope" in data:
            ck._scope = data["scope"]

        return ck
