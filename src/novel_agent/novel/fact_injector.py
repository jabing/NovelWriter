"""Fact injection for relevant context during chapter generation.

This module provides the RelevantFactInjector class that selects and
injects the most relevant facts into the generation context.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.novel_agent.novel.fact_database import Fact, FactDatabase, FactType

logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """Score breakdown for fact relevance.

    Attributes:
        fact_id: ID of the scored fact
        recency_score: Score based on how recently referenced
        importance_score: Score based on fact importance
        frequency_score: Score based on reference frequency
        relationship_score: Score based on entity relationships
        total_score: Combined weighted score
    """

    fact_id: str
    recency_score: float
    importance_score: float
    frequency_score: float
    relationship_score: float
    total_score: float


class RelevanceScorer:
    """Multi-factor relevance scoring for facts.

    Scoring factors:
    - Recency: How recently the fact was referenced
    - Importance: How critical the fact is to the story
    - Frequency: How often the fact is referenced
    - Relationship: How related to current context
    """

    # Weight configuration for scoring factors
    WEIGHTS = {
        "recency": 0.3,
        "importance": 0.3,
        "frequency": 0.2,
        "relationship": 0.2,
    }

    def __init__(
        self,
        recency_weight: float = 0.3,
        importance_weight: float = 0.3,
        frequency_weight: float = 0.2,
        relationship_weight: float = 0.2,
    ) -> None:
        """Initialize scorer with custom weights.

        Args:
            recency_weight: Weight for recency factor
            importance_weight: Weight for importance factor
            frequency_weight: Weight for frequency factor
            relationship_weight: Weight for relationship factor
        """
        self.WEIGHTS = {
            "recency": recency_weight,
            "importance": importance_weight,
            "frequency": frequency_weight,
            "relationship": relationship_weight,
        }

    def score_fact(
        self,
        fact: Fact,
        current_chapter: int,
        active_entities: list[str] | None = None,
        max_chapters: int = 100,
    ) -> RelevanceScore:
        """Calculate relevance score for a fact.

        Args:
            fact: Fact to score
            current_chapter: Current chapter number
            active_entities: Entities currently in the scene
            max_chapters: Maximum chapters for normalization

        Returns:
            RelevanceScore with breakdown
        """
        # Recency score: higher if recently referenced
        if fact.last_referenced > 0:
            chapters_since_reference = current_chapter - fact.last_referenced
            recency_score = max(0, 1.0 - (chapters_since_reference / max_chapters))
        else:
            # Never referenced, use chapter origin
            chapters_since_origin = current_chapter - fact.chapter_origin
            recency_score = max(0, 1.0 - (chapters_since_origin / max_chapters))

        # Importance score: direct from fact
        importance_score = fact.importance

        # Frequency score: normalized by log scale
        import math
        frequency_score = min(1.0, math.log1p(fact.reference_count) / 5)

        # Relationship score: based on entity overlap
        relationship_score = 0.0
        if active_entities and fact.entities:
            overlap = set(active_entities) & set(fact.entities)
            if overlap:
                relationship_score = len(overlap) / len(active_entities)

        # Calculate total weighted score
        total_score = (
            recency_score * self.WEIGHTS["recency"]
            + importance_score * self.WEIGHTS["importance"]
            + frequency_score * self.WEIGHTS["frequency"]
            + relationship_score * self.WEIGHTS["relationship"]
        )

        return RelevanceScore(
            fact_id=fact.id,
            recency_score=recency_score,
            importance_score=importance_score,
            frequency_score=frequency_score,
            relationship_score=relationship_score,
            total_score=total_score,
        )


class RelevantFactInjector:
    """Injects relevant facts into generation context.

    This class coordinates with the FactDatabase to select the most
    relevant facts for the current chapter being generated.

    Attributes:
        fact_database: FactDatabase instance
        scorer: RelevanceScorer instance
        max_facts: Maximum facts to inject
        min_score: Minimum relevance score threshold
    """

    def __init__(
        self,
        storage_path: Path,
        novel_id: str,
        max_facts: int = 20,
        min_score: float = 0.1,
    ) -> None:
        """Initialize the fact injector.

        Args:
            storage_path: Base directory for storage
            novel_id: Novel identifier
            max_facts: Maximum facts to inject per chapter
            min_score: Minimum relevance score to include
        """
        self.fact_database = FactDatabase(storage_path, novel_id)
        self.scorer = RelevanceScorer()
        self.max_facts = max_facts
        self.min_score = min_score

    def get_relevant_facts(
        self,
        current_chapter: int,
        active_entities: list[str] | None = None,
        required_types: list[FactType] | None = None,
    ) -> list[tuple[Fact, RelevanceScore]]:
        """Get the most relevant facts for the current context.

        Args:
            current_chapter: Chapter being generated
            active_entities: Entities in current scene
            required_types: Fact types that must be included

        Returns:
            List of (Fact, RelevanceScore) tuples sorted by score
        """
        all_facts = self.fact_database.get_all_facts()

        if not all_facts:
            return []

        # Score all facts
        scored_facts: list[tuple[Fact, RelevanceScore]] = []
        for fact in all_facts:
            score = self.scorer.score_fact(
                fact=fact,
                current_chapter=current_chapter,
                active_entities=active_entities,
            )

            # Boost score for required types
            if required_types and fact.fact_type in required_types:
                score.total_score = min(1.0, score.total_score + 0.3)

            scored_facts.append((fact, score))

        # Sort by total score descending
        scored_facts.sort(key=lambda x: x[1].total_score, reverse=True)

        # Filter by minimum score
        scored_facts = [
            (f, s) for f, s in scored_facts if s.total_score >= self.min_score
        ]

        # Limit to max facts
        return scored_facts[: self.max_facts]

    def get_context_string(
        self,
        current_chapter: int,
        active_entities: list[str] | None = None,
        required_types: list[FactType] | None = None,
    ) -> str:
        """Generate context string from relevant facts.

        Args:
            current_chapter: Chapter being generated
            active_entities: Entities in current scene
            required_types: Fact types that must be included

        Returns:
            Formatted context string for LLM
        """
        relevant_facts = self.get_relevant_facts(
            current_chapter=current_chapter,
            active_entities=active_entities,
            required_types=required_types,
        )

        if not relevant_facts:
            return ""

        context_parts = ["【相关事实】"]

        # Group facts by type
        facts_by_type: dict[FactType, list[Fact]] = {}
        for fact, _ in relevant_facts:
            if fact.fact_type not in facts_by_type:
                facts_by_type[fact.fact_type] = []
            facts_by_type[fact.fact_type].append(fact)

        # Format each type
        type_labels = {
            FactType.CHARACTER: "角色信息",
            FactType.LOCATION: "地点信息",
            FactType.EVENT: "重要事件",
            FactType.RELATIONSHIP: "人物关系",
            FactType.ITEM: "重要物品",
            FactType.WORLD_RULE: "世界规则",
            FactType.PLOT_THREAD: "剧情线",
        }

        for fact_type, facts in facts_by_type.items():
            label = type_labels.get(fact_type, "其他")
            type_content = [f"  - {f.content}" for f in facts[:5]]  # Max 5 per type
            if type_content:
                context_parts.append(f"{label}:")
                context_parts.extend(type_content)

        return "\n".join(context_parts)

    def add_fact(
        self,
        fact_type: FactType | str,
        content: str,
        chapter_origin: int,
        importance: float = 0.5,
        entities: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Fact:
        """Add a new fact to the database.

        Args:
            fact_type: Type of fact
            content: Fact content
            chapter_origin: Chapter where introduced
            importance: Importance score
            entities: Related entities
            metadata: Additional metadata

        Returns:
            Created Fact
        """
        return self.fact_database.add_fact(
            fact_type=fact_type,
            content=content,
            chapter_origin=chapter_origin,
            importance=importance,
            entities=entities,
            metadata=metadata,
        )

    def mark_fact_referenced(self, fact_id: str, chapter: int) -> None:
        """Mark a fact as referenced in a chapter.

        Args:
            fact_id: Fact identifier
            chapter: Chapter where referenced
        """
        self.fact_database.update_fact_reference(fact_id, chapter)

    def get_fact(self, fact_id: str) -> Fact | None:
        """Get a fact by ID.

        Args:
            fact_id: Fact identifier

        Returns:
            Fact if found
        """
        return self.fact_database.get_fact(fact_id)

    def get_facts_by_entity(self, entity: str) -> list[Fact]:
        """Get all facts related to an entity.

        Args:
            entity: Entity name

        Returns:
            List of related facts
        """
        return self.fact_database.get_facts_by_entity(entity)

    def get_fact_count(self) -> int:
        """Get total fact count.

        Returns:
            Number of facts
        """
        return self.fact_database.get_fact_count()


class FactExtractor:
    """Extract facts from chapter content.

    This class provides utilities for extracting facts from chapter
    text, to be used by the consistency verification system.
    """

    def __init__(self) -> None:
        """Initialize the fact extractor."""
        pass

    def extract_entities(self, content: str) -> list[str]:
        """Extract entity names from content.

        Simple pattern-based extraction. For production, would use NER.

        Args:
            content: Chapter content

        Returns:
            List of entity names
        """
        # This is a simplified version - production would use NER
        import re

        entities = []

        # Extract quoted names (common in dialogue)
        quoted = re.findall(r'[""]([^""]+)[""]', content)
        entities.extend(quoted)

        # Extract potential character names before speech verbs
        caps = re.findall(r"[\u4e00-\u9fff]{2,4}(?:说|道|想|看|走|来|去)", content)
        entities.extend(caps)

        # Deduplicate
        return list(set(entities))

    def extract_locations(self, content: str) -> list[str]:
        """Extract location names from content.

        Args:
            content: Chapter content

        Returns:
            List of location names
        """
        import re

        # Pattern for locations (simplified)
        patterns = [
            r"在([^\s，。！？]{2,10})(?:里|中|上|下|边)",
            r"来到([^\s，。！？]{2,10})",
            r"离开([^\s，。！？]{2,10})",
        ]

        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            locations.extend(matches)

        return list(set(locations))
