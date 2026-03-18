"""Fact injection for relevant context during chapter generation.

This module provides the RelevantFactInjector class that selects and
injects the most relevant facts into the generation context.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.novel_agent.novel.fact_database import (
    Fact,
    FactDatabase,
    FactType,
    ProtectedFactCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class RelevanceScore:
    """Score breakdown for fact relevance.

    Attributes:
        fact_id: ID of the scored fact
        recency_score: Score based on how recently referenced
        importance_score: Score based on fact importance
        narrative_significance_score: Score based on narrative impact
        frequency_score: Score based on reference frequency
        relationship_score: Score based on entity relationships
        debt_urgency_score: Score based on fact debt urgency
        total_score: Combined weighted score
    """

    fact_id: str
    recency_score: float
    importance_score: float
    narrative_significance_score: float
    frequency_score: float
    relationship_score: float
    debt_urgency_score: float
    total_score: float


class RelevanceScorer:
    """Multi-factor relevance scoring for facts.

    Scoring factors:
    - Recency: How recently the fact was referenced
    - Importance: How critical the fact is to the story
    - Narrative Significance: Impact on narrative flow and cohesion
    - Frequency: How often the fact is referenced
    - Relationship: How related to current context
    - Debt Urgency: Priority of addressing known issues
    """

    # Weight configuration for scoring factors
    WEIGHTS = {
        "recency": 0.15,
        "importance": 0.20,
        "narrative_significance": 0.25,
        "frequency": 0.10,
        "relationship": 0.15,
        "debt_urgency": 0.15,
    }

    def __init__(
        self,
        recency_weight: float = 0.15,
        importance_weight: float = 0.20,
        narrative_significance_weight: float = 0.25,
        frequency_weight: float = 0.10,
        relationship_weight: float = 0.15,
        debt_urgency_weight: float = 0.15,
    ) -> None:
        """Initialize scorer with custom weights.

        Args:
            recency_weight: Weight for recency factor
            importance_weight: Weight for importance factor
            narrative_significance_weight: Weight for narrative significance factor
            frequency_weight: Weight for frequency factor
            relationship_weight: Weight for relationship factor
            debt_urgency_weight: Weight for debt urgency factor
        """
        self.WEIGHTS = {
            "recency": recency_weight,
            "importance": importance_weight,
            "narrative_significance": narrative_significance_weight,
            "frequency": frequency_weight,
            "relationship": relationship_weight,
            "debt_urgency": debt_urgency_weight,
        }

    def score_fact(
        self,
        fact: Fact,
        current_chapter: int,
        active_entities: list[str] | None = None,
        max_chapters: int = 100,
        narrative_significance: float = 0.5,
        debt_urgency: float = 0.0,
    ) -> RelevanceScore:
        """Calculate relevance score for a fact.

        Args:
            fact: Fact to score
            current_chapter: Current chapter number
            active_entities: Entities currently in the scene
            max_chapters: Maximum chapters for normalization
            narrative_significance: Pre-computed narrative significance score
            debt_urgency: Pre-computed debt urgency score

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
            + narrative_significance * self.WEIGHTS["narrative_significance"]
            + frequency_score * self.WEIGHTS["frequency"]
            + relationship_score * self.WEIGHTS["relationship"]
            + debt_urgency * self.WEIGHTS["debt_urgency"]
        )

        return RelevanceScore(
            fact_id=fact.id,
            recency_score=recency_score,
            importance_score=importance_score,
            narrative_significance_score=narrative_significance,
            frequency_score=frequency_score,
            relationship_score=relationship_score,
            debt_urgency_score=debt_urgency,
            total_score=total_score,
        )


def calculate_max_facts(chapter_count: int) -> int:
    """Calculate maximum facts to inject based on chapter count.

    Formula: max(30, min(50, int(chapter_count * 1.5)))

    Args:
        chapter_count: Total number of chapters in the novel

    Returns:
        Maximum number of facts to inject
    """
    return max(30, min(50, int(chapter_count * 1.5)))


class RelevantFactInjector:
    """Injects relevant facts into generation context.

    This class coordinates with the FactDatabase to select the most
    relevant facts for the current chapter being generated.

    Attributes:
        fact_database: FactDatabase instance
        scorer: RelevanceScorer instance
        max_facts: Maximum facts to inject
        min_score: Minimum relevance score threshold
        PROTECTED_SLOTS: Reserved slots per protected category
    """

    # Reserved slots for protected facts (total: 14 slots)
    PROTECTED_SLOTS = {
        ProtectedFactCategory.IMMUTABLE: 3,
        ProtectedFactCategory.SECRET: 3,
        ProtectedFactCategory.PROMISE: 3,
        ProtectedFactCategory.WORLD_RULE: 2,
        ProtectedFactCategory.FORESHADOW: 3,
    }

    def __init__(
        self,
        storage_path: Path,
        novel_id: str,
        max_facts: int | None = None,
        min_score: float = 0.1,
        chapter_count: int | None = None,
    ) -> None:
        """Initialize the fact injector.

        Args:
            storage_path: Base directory for storage
            novel_id: Novel identifier
            max_facts: Maximum facts to inject per chapter (auto-calculated if None)
            min_score: Minimum relevance score to include
            chapter_count: Total chapters for auto-calculation (optional)
        """
        self.fact_database = FactDatabase(storage_path, novel_id)
        self.scorer = RelevanceScorer()

        # Priority: explicit max_facts > chapter_count calculation > default 20
        if max_facts is not None:
            self.max_facts = max_facts
        elif chapter_count is not None:
            self.max_facts = calculate_max_facts(chapter_count)
        else:
            self.max_facts = 20

        self.min_score = min_score

    def get_relevant_facts(
        self,
        current_chapter: int,
        active_entities: list[str] | None = None,
        required_types: list[FactType] | None = None,
    ) -> list[tuple[Fact, RelevanceScore]]:
        """Get the most relevant facts for the current context.

        Protected facts are reserved slots that are never filtered out.
        All protected facts are included first (up to their category limit),
        then remaining slots are filled by regular relevance scoring.

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

        # Separate protected and regular facts
        protected_facts = [f for f in all_facts if f.protected_category is not None]
        regular_facts = [f for f in all_facts if f.protected_category is None]

        result: list[tuple[Fact, RelevanceScore]] = []

        # Fill protected slots by category
        for category, max_slots in self.PROTECTED_SLOTS.items():
            category_facts = [f for f in protected_facts if f.protected_category == category]
            # Sort by importance within category
            category_facts.sort(key=lambda f: f.importance, reverse=True)
            # Add up to max_slots protected facts from this category
            for fact in category_facts[:max_slots]:
                score = self.scorer.score_fact(
                    fact=fact,
                    current_chapter=current_chapter,
                    active_entities=active_entities,
                )
                result.append((fact, score))

        # Calculate remaining slots
        remaining = self.max_facts - len(result)

        # Score and fill remaining with regular facts
        if remaining > 0 and regular_facts:
            scored_facts: list[tuple[Fact, RelevanceScore]] = []
            for fact in regular_facts:
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

            # Filter by minimum score and limit
            scored_facts = [(f, s) for f, s in scored_facts if s.total_score >= self.min_score]
            result.extend(scored_facts[:remaining])

        return result

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
