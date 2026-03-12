"""Relation inference module for extracting entity relationships from text.

This module provides the RelationInference class that infers relationships between
entities from chapter content using both rule-based patterns and LLM-based inference.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.novel.entity_extractor import Entity, Relation, RelationType

if TYPE_CHECKING:
    from src.llm.base import BaseLLM
    from src.novel.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


@dataclass
class RelationTimelineEvent:
    """Timeline event for a relation."""

    chapter: int
    status: str  # "active", "ended", "changed"
    note: str = ""


@dataclass
class InferredRelation:
    """Extended relation with timeline support."""

    source: str  # Source entity ID
    target: str  # Target entity ID
    type: RelationType
    description: str = ""
    chapter: int = 0
    evidence: str = ""  # Text evidence from source
    weight: float = 1.0
    is_active: bool = True
    timeline: list[RelationTimelineEvent] = field(default_factory=list)

    def to_relation(self) -> Relation:
        """Convert to base Relation."""
        return Relation(
            source=self.source,
            target=self.target,
            type=self.type,
            description=self.description,
            chapter=self.chapter,
            evidence=self.evidence,
            weight=self.weight,
        )

    @classmethod
    def from_relation(cls, relation: Relation) -> InferredRelation:
        """Create from base Relation."""
        return cls(
            source=relation.source,
            target=relation.target,
            type=relation.type,
            description=relation.description,
            chapter=relation.chapter,
            evidence=relation.evidence,
            weight=relation.weight,
            timeline=[RelationTimelineEvent(chapter=relation.chapter, status="active")],
        )


# Relation patterns for rule-based inference
RELATION_PATTERNS = [
    # Family relations
    {
        "type": RelationType.FAMILY,
        "patterns": [
            r"(.+?)是(.+?)的父亲",
            r"(.+?)是(.+?)的母亲",
            r"(.+?)是(.+?)的哥哥",
            r"(.+?)是(.+?)的姐姐",
            r"(.+?)是(.+?)的弟弟",
            r"(.+?)是(.+?)的妹妹",
            r"(.+?)和(.+?)是兄弟",
            r"(.+?)和(.+?)是姐妹",
            r"(.+?)是(.+?)的儿子",
            r"(.+?)是(.+?)的女儿",
        ],
    },
    # Enemy relations
    {
        "type": RelationType.ENEMY,
        "patterns": [
            r"(.+?)与(.+?)为敌",
            r"(.+?)憎恨(.+?)",
            r"(.+?)打败了(.+?)",
            r"(.+?)杀死了(.+?)",
            r"(.+?)击败了(.+?)",
            r"(.+?)与(.+?)战斗",
            r"(.+?)追杀(.+?)",
        ],
    },
    # Friend/Ally relations
    {
        "type": RelationType.FRIEND,
        "patterns": [
            r"(.+?)和(.+?)是朋友",
            r"(.+?)帮助(.+?)",
            r"(.+?)协助(.+?)",
            r"(.+?)与(.+?)合作",
            r"(.+?)救了(.+?)",
        ],
    },
    # Location relations
    {
        "type": RelationType.LOCATED_AT,
        "patterns": [
            r"(.+?)在(.+?)",
            r"(.+?)来到了(.+?)",
            r"(.+?)前往(.+?)",
            r"(.+?)到达(.+?)",
            r"(.+?)位于(.+?)",
        ],
    },
    # Ownership relations
    {
        "type": RelationType.OWNS,
        "patterns": [
            r"(.+?)拥有(.+?)",
            r"(.+?)得到了(.+?)",
            r"(.+?)手持(.+?)",
            r"(.+?)带着(.+?)",
        ],
    },
    # Romance relations
    {
        "type": RelationType.LOVER,
        "patterns": [
            r"(.+?)爱(.+?)",
            r"(.+?)和(.+?)相爱",
            r"(.+?)是(.+?)的爱人",
            r"(.+?)与(.+?)结婚",
        ],
    },
    # Mentorship relations
    {
        "type": RelationType.MENTOR,
        "patterns": [
            r"(.+?)教导(.+?)",
            r"(.+?)是(.+?)的师傅",
            r"(.+?)教(.+?)",
        ],
    },
]


class RelationInference:
    """Infer relationships between entities from text.

    This class provides methods to infer relationships between entities using:
    1. Rule-based pattern matching (fast, no LLM needed)
    2. LLM-based inference (more accurate)
    3. Conflict detection for existing relationships
    4. Timeline tracking for relationship evolution
    """

    def __init__(self, knowledge_graph: KnowledgeGraph, llm: BaseLLM | None = None) -> None:
        """Initialize the relation inference.

        Args:
            knowledge_graph: Knowledge graph to store inferred relations
            llm: Optional LLM for LLM-based inference
        """
        self.kg = knowledge_graph
        self.llm = llm

        # Cache for inferred relations
        self._relation_cache: dict[str, InferredRelation] = {}

    def infer_relations(
        self, content: str, entities: list[Entity], chapter: int
    ) -> list[InferredRelation]:
        """Infer relationships from text.

        Args:
            content: Chapter content
            entities: List of already extracted entities
            chapter: Chapter number

        Returns:
            List of inferred relations
        """
        if not entities or len(entities) < 2:
            return []

        logger.info(f"Inferring relations for chapter {chapter} with {len(entities)} entities")

        relations: list[InferredRelation] = []

        # 1. Rule-based inference
        pattern_relations = self._infer_by_patterns(content, entities, chapter)
        relations.extend(pattern_relations)
        logger.debug(f"Pattern-based inference found {len(pattern_relations)} relations")

        # 2. Context-based inference (using co-occurrence)
        context_relations = self._infer_by_context(content, entities, chapter)
        relations.extend(context_relations)
        logger.debug(f"Context-based inference found {len(context_relations)} relations")

        # 3. LLM-based inference (if available)
        if self.llm:
            try:
                import asyncio

                llm_relations = asyncio.run(self._infer_by_llm(content, entities, chapter))
                relations.extend(llm_relations)
                logger.debug(f"LLM-based inference found {len(llm_relations)} relations")
            except Exception as e:
                logger.warning(f"LLM inference failed: {e}")

        # 4. Deduplicate and check conflicts
        deduplicated = self._deduplicate_relations(relations)
        logger.info(f"Total unique relations inferred: {len(deduplicated)}")

        return deduplicated

    def _infer_by_patterns(
        self, content: str, entities: list[Entity], chapter: int
    ) -> list[InferredRelation]:
        """Infer relations based on regex patterns.

        Args:
            content: Chapter content
            entities: List of entities
            chapter: Chapter number

        Returns:
            List of inferred relations
        """
        relations: list[InferredRelation] = []
        entity_names = {e.name: e for e in entities}

        for pattern_def in RELATION_PATTERNS:
            rel_type = pattern_def["type"]
            for pattern in pattern_def["patterns"]:
                for match in re.finditer(pattern, content):
                    # Extract the full match and search for entity names within it
                    full_match = match.group(0)
                    found_entities: list[Entity] = []

                    # Find which entities are mentioned in this match
                    for name, entity in entity_names.items():
                        if name in full_match:
                            found_entities.append(entity)

                    # If we found exactly 2 entities, create a relation
                    if len(found_entities) == 2:
                        source_entity, target_entity = found_entities[0], found_entities[1]
                        relation = InferredRelation(
                            source=source_entity.id,
                            target=target_entity.id,
                            type=rel_type,
                            description=f"{rel_type.value} relationship inferred from pattern",
                            chapter=chapter,
                            evidence=match.group(0),
                            weight=0.8,  # High confidence for pattern match
                        )
                        relations.append(relation)
                    elif len(found_entities) > 2:
                        # Create relations for all pairs if multiple entities found
                        for i, e1 in enumerate(found_entities):
                            for e2 in found_entities[i + 1 :]:
                                relation = InferredRelation(
                                    source=e1.id,
                                    target=e2.id,
                                    type=rel_type,
                                    description=f"{rel_type.value} relationship inferred from pattern",
                                    chapter=chapter,
                                    evidence=match.group(0),
                                    weight=0.7,  # Slightly lower confidence for multiple matches
                                )
                                relations.append(relation)

        return relations

    def _infer_by_context(
        self, content: str, entities: list[Entity], chapter: int
    ) -> list[InferredRelation]:
        """Infer relations based on entity co-occurrence in sentences.

        Args:
            content: Chapter content
            entities: List of entities
            chapter: Chapter number

        Returns:
            List of inferred relations
        """
        relations: list[InferredRelation] = []

        # Split content into sentences
        sentences = re.split(r"[。！？.!?]", content)

        for sentence in sentences:
            # Find all entities in this sentence
            present_entities: list[Entity] = []
            for entity in entities:
                if entity.name in sentence:
                    present_entities.append(entity)

            # If multiple entities appear together, infer a weak relation
            if len(present_entities) >= 2:
                for i, e1 in enumerate(present_entities):
                    for e2 in present_entities[i + 1 :]:
                        # Check for relation keywords
                        rel_type = self._detect_relation_type(sentence)

                        if rel_type:
                            relation = InferredRelation(
                                source=e1.id,
                                target=e2.id,
                                type=rel_type,
                                description="Inferred from co-occurrence in sentence",
                                chapter=chapter,
                                evidence=sentence.strip(),
                                weight=0.5,  # Lower confidence for context-based
                            )
                            relations.append(relation)

        return relations

    def _detect_relation_type(self, sentence: str) -> RelationType | None:
        """Detect relation type from keywords in sentence.

        Args:
            sentence: Sentence text

        Returns:
            Detected relation type or None
        """
        relation_keywords: dict[RelationType, list[str]] = {
            RelationType.FAMILY: [
                "父亲",
                "母亲",
                "兄弟",
                "姐妹",
                "家人",
                "family",
                "father",
                "mother",
            ],
            RelationType.FRIEND: ["朋友", "friend", "同伴", "companion", "帮助", "help"],
            RelationType.ENEMY: [
                "敌人",
                "enemy",
                "对手",
                "rival",
                "憎恨",
                "hate",
                "战斗",
                "battle",
            ],
            RelationType.LOVER: [
                "爱",
                "love",
                "爱人",
                "beloved",
                "妻子",
                "丈夫",
                "wife",
                "husband",
            ],
            RelationType.LOCATED_AT: ["在", "at", "位于", "located", "来到", "came to"],
            RelationType.OWNS: ["拥有", "own", "拿着", "hold", "得到", "got"],
            RelationType.MENTOR: ["师傅", "master", "教导", "teach", "指导", "guide"],
        }

        for rel_type, keywords in relation_keywords.items():
            if any(kw in sentence for kw in keywords):
                return rel_type

        return None

    async def _infer_by_llm(
        self, content: str, entities: list[Entity], chapter: int
    ) -> list[InferredRelation]:
        """Infer relations using LLM.

        Args:
            content: Chapter content
            entities: List of entities
            chapter: Chapter number

        Returns:
            List of inferred relations
        """
        if not self.llm:
            return []

        entity_names = [e.name for e in entities]
        entity_map = {e.name: e.id for e in entities}

        system_prompt = "你是一个专业的关系推理助手。从文本中分析实体之间的关系。\n\n请识别以下类型的关系：\n- family（亲属）：父子、母子、兄弟姐妹等\n- friend（朋友）：朋友、同伴、盟友\n- enemy（敌对）：敌人、对手、仇敌\n- lover（恋爱）：爱人、情侣、夫妻\n- located_at（位于）：角色所在地点\n- owns（拥有）：角色拥有的物品\n- mentor（师徒）：师父、导师、教导关系\n\n只输出确定的关系，格式如下：\n实体A|实体B|关系类型|简要描述\n\n不确定的关系不要输出。"

        user_prompt = f"""分析以下文本中的实体关系：

实体列表: {", ".join(entity_names)}

文本内容（第{chapter}章）：
{content[:1000]}

请识别实体间的关系，每行输出一个关系：实体A|实体B|关系类型|描述"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            return self._parse_llm_relation_response(response.content, entity_map, chapter)
        except Exception as e:
            logger.error(f"LLM relation inference failed: {e}")
            return []

    def _parse_llm_relation_response(
        self, content: str, entity_map: dict[str, str], chapter: int
    ) -> list[InferredRelation]:
        """Parse LLM response to extract relations.

        Args:
            content: LLM response content
            entity_map: Mapping from entity name to ID
            chapter: Chapter number

        Returns:
            List of inferred relations
        """
        relations: list[InferredRelation] = []

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line or "|" not in line:
                continue

            parts = line.split("|")
            if len(parts) >= 3:
                source_name = parts[0].strip()
                target_name = parts[1].strip()
                rel_type_str = parts[2].strip().lower()
                description = parts[3].strip() if len(parts) > 3 else ""

                source_id = entity_map.get(source_name)
                target_id = entity_map.get(target_name)

                if source_id and target_id:
                    try:
                        rel_type = RelationType(rel_type_str)
                        relation = InferredRelation(
                            source=source_id,
                            target=target_id,
                            type=rel_type,
                            description=description or f"LLM inferred {rel_type_str}",
                            chapter=chapter,
                            evidence=line,
                            weight=0.9,  # High confidence for LLM
                        )
                        relations.append(relation)
                    except ValueError:
                        logger.warning(f"Unknown relation type: {rel_type_str}")

        return relations

    def _deduplicate_relations(self, relations: list[InferredRelation]) -> list[InferredRelation]:
        """Deduplicate relations by (source, target, type).

        Args:
            relations: List of relations

        Returns:
            Deduplicated list
        """
        seen: dict[tuple[str, str, RelationType], InferredRelation] = {}

        for relation in relations:
            key = (relation.source, relation.target, relation.type)
            if key in seen:
                # Keep the one with higher weight
                if relation.weight > seen[key].weight:
                    seen[key] = relation
            else:
                seen[key] = relation

        return list(seen.values())

    def _check_relation_conflict(
        self, new_relation: InferredRelation
    ) -> InferredRelation | None:
        """Check if new relation conflicts with existing relations.

        Args:
            new_relation: New relation to check

        Returns:
            Conflicting relation if found, None otherwise
        """
        # Get existing relations between these entities
        existing = self._get_relations_between(new_relation.source, new_relation.target)

        for rel in existing:
            if self._is_conflicting(rel.type, new_relation.type):
                return rel

        return None

    def _get_relations_between(self, source_id: str, target_id: str) -> list[InferredRelation]:
        """Get cached relations between two entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID

        Returns:
            List of relations
        """
        relations: list[InferredRelation] = []
        for rel in self._relation_cache.values():
            if (rel.source == source_id and rel.target == target_id) or (
                rel.source == target_id and rel.target == source_id
            ):
                relations.append(rel)
        return relations

    def _is_conflicting(self, type1: RelationType, type2: RelationType) -> bool:
        """Check if two relation types conflict.

        Args:
            type1: First relation type
            type2: Second relation type

        Returns:
            True if they conflict
        """
        conflicts: dict[RelationType, list[RelationType]] = {
            RelationType.FRIEND: [RelationType.ENEMY],
            RelationType.ENEMY: [RelationType.FRIEND, RelationType.LOVER],
            RelationType.LOVER: [RelationType.ENEMY],
            RelationType.ALLY: [RelationType.ENEMY, RelationType.RIVAL],
            RelationType.RIVAL: [RelationType.FRIEND, RelationType.ALLY],
        }
        return type2 in conflicts.get(type1, [])

    def update_relation_timeline(
        self, relation_id: str, chapter: int, status: str = "active", note: str = ""
    ) -> None:
        """Update relation timeline.

        Args:
            relation_id: Relation identifier
            chapter: Chapter number
            status: Status ("active", "ended", "changed")
            note: Optional note
        """
        if relation_id not in self._relation_cache:
            logger.warning(f"Relation {relation_id} not found in cache")
            return

        relation = self._relation_cache[relation_id]

        # Add timeline event
        event = RelationTimelineEvent(chapter=chapter, status=status, note=note)
        relation.timeline.append(event)

        # Update active status
        if status == "ended":
            relation.is_active = False
        elif status == "active":
            relation.is_active = True

        logger.debug(f"Updated relation {relation_id} timeline: {status} at chapter {chapter}")

    def add_relation_to_cache(self, relation: InferredRelation) -> str:
        """Add relation to cache with generated ID.

        Args:
            relation: Relation to add

        Returns:
            Generated relation ID
        """
        relation_id = f"{relation.source}_{relation.target}_{relation.type.value}"
        self._relation_cache[relation_id] = relation
        return relation_id

    def get_relation_from_cache(self, relation_id: str) -> InferredRelation | None:
        """Get relation from cache.

        Args:
            relation_id: Relation identifier

        Returns:
            Relation or None
        """
        return self._relation_cache.get(relation_id)

    def add_relations_to_knowledge_graph(self, relations: list[InferredRelation]) -> None:
        """Add inferred relations to knowledge graph.

        Args:
            relations: List of relations to add
        """
        from src.novel.schemas import KnowledgeGraphEdge

        for relation in relations:
            try:
                # Check for conflicts
                conflict = self._check_relation_conflict(relation)
                if conflict:
                    logger.info(
                        f"Relation conflict detected: {relation.type.value} vs {conflict.type.value}"
                    )
                    # Add timeline event for change
                    relation_id = self.add_relation_to_cache(relation)
                    self.update_relation_timeline(
                        relation_id,
                        relation.chapter,
                        "changed",
                        f"Conflicts with {conflict.type.value}",
                    )
                else:
                    relation_id = self.add_relation_to_cache(relation)

                # Add to knowledge graph as edge
                edge_id = f"rel_{relation.source}_{relation.target}_{relation.chapter}"
                edge = KnowledgeGraphEdge(
                    edge_id=edge_id,
                    source_id=relation.source,
                    target_id=relation.target,
                    relationship_type=relation.type.value,
                    weight=relation.weight,
                    properties={
                        "description": relation.description,
                        "chapter": relation.chapter,
                        "evidence": relation.evidence,
                        "is_active": relation.is_active,
                        "timeline": [t.__dict__ for t in relation.timeline]
                        if relation.timeline
                        else [],
                    },
                )

                # Check if edge already exists
                existing_edge = self.kg.get_edge(edge_id)
                if existing_edge:
                    # Update existing edge
                    self.kg.update_edge(
                        edge_id=edge_id,
                        weight=relation.weight,
                        properties={
                            "description": relation.description,
                            "chapter": relation.chapter,
                            "evidence": relation.evidence,
                            "is_active": relation.is_active,
                            "timeline": [t.__dict__ for t in relation.timeline]
                            if relation.timeline
                            else [],
                        },
                    )
                else:
                    # Add new edge
                    self.kg.add_edge(
                        edge_id=edge.edge_id,
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        relationship_type=edge.relationship_type,
                        weight=edge.weight,
                        properties=edge.properties,
                    )

            except Exception as e:
                logger.error(f"Failed to add relation to knowledge graph: {e}")


__all__ = [
    "RelationInference",
    "InferredRelation",
    "RelationTimelineEvent",
    "RELATION_PATTERNS",
]
