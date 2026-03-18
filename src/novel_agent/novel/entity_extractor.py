"""Entity extraction from chapter content for knowledge graph population.

This module provides the EntityExtractor class that extracts characters, locations,
events, and relationships from chapter text and adds them to the knowledge graph.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from src.novel_agent.novel.schemas import KnowledgeGraphEdge, KnowledgeGraphNode

if TYPE_CHECKING:
    from src.novel_agent.llm.base import BaseLLM
    from src.novel_agent.novel.character_registry import CharacterRegistry
    from src.novel_agent.novel.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Types of entities that can be extracted."""

    CHARACTER = "character"
    LOCATION = "location"
    EVENT = "event"
    ITEM = "item"
    ORGANIZATION = "organization"
    CONCEPT = "concept"


class RelationType(str, Enum):
    """Types of relationships between entities."""

    # Character relations
    FRIEND = "friend"
    ENEMY = "enemy"
    FAMILY = "family"
    LOVER = "lover"
    ALLY = "ally"
    RIVAL = "rival"
    MENTOR = "mentor"
    STUDENT = "student"

    # Location relations
    LOCATED_AT = "located_at"
    BORN_IN = "born_in"
    LIVES_IN = "lives_in"
    VISITS = "visits"
    FROM = "from"

    # Event relations
    PARTICIPANT = "participant"
    WITNESS = "witness"
    VICTIM = "victim"
    PERPETRATOR = "perpetrator"
    ORGANIZER = "organizer"

    # Item relations
    OWNS = "owns"
    USES = "uses"
    SEEKS = "seeks"
    CARRIES = "carries"

    # General
    RELATED_TO = "related_to"
    MENTIONS = "mentions"
    APPEARS_IN = "appears_in"


class ExtractionStrategy(Enum):
    """Strategies for entity extraction."""

    RULE_BASED = auto()  # Fast, regex-based extraction
    LLM_BASED = auto()  # Accurate, LLM-based extraction
    HYBRID = auto()  # Combine rule and LLM approaches


@dataclass
class Entity:
    """Base entity extracted from text."""

    id: str
    name: str
    type: EntityType = field(default=EntityType.CHARACTER, init=False)
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    first_appearance: int = 0  # Chapter number
    appearances: list[int] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_knowledge_graph_node(self) -> KnowledgeGraphNode:
        """Convert entity to KnowledgeGraphNode."""
        return KnowledgeGraphNode(
            node_id=self.id,
            node_type=self.type.value,
            properties={
                "name": self.name,
                "aliases": self.aliases,
                "description": self.description,
                "first_appearance": self.first_appearance,
                "appearances": self.appearances,
                **self.properties,
            },
        )


@dataclass
class CharacterEntity(Entity):
    """Character entity with specific attributes."""

    type: EntityType = field(default=EntityType.CHARACTER, init=False)
    gender: str = ""
    age: int | None = None
    role: str = ""  # protagonist, antagonist, supporting, etc.
    role_id: str | None = None  # Unique character ID from CharacterRegistry
    personality: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)


@dataclass
class LocationEntity(Entity):
    """Location entity with specific attributes."""

    type: EntityType = field(default=EntityType.LOCATION, init=False)
    location_type: str = ""  # city, building, room, etc.
    parent_location: str | None = None
    is_main: bool = False


@dataclass
class EventEntity(Entity):
    """Event entity with specific attributes."""

    type: EntityType = field(default=EntityType.EVENT, init=False)
    event_type: str = ""  # meeting, battle, conversation, etc.
    participants: list[str] = field(default_factory=list)
    location_id: str | None = None
    chapter: int = 0
    timestamp: str = ""


@dataclass
class Relation:
    """Relationship between two entities."""

    source: str  # Source entity ID
    target: str  # Target entity ID
    type: RelationType
    description: str = ""
    chapter: int = 0
    evidence: str = ""  # Text evidence from source
    weight: float = 1.0

    def to_knowledge_graph_edge(self, edge_id: str) -> KnowledgeGraphEdge:
        """Convert relation to KnowledgeGraphEdge."""
        return KnowledgeGraphEdge(
            edge_id=edge_id,
            source_id=self.source,
            target_id=self.target,
            relationship_type=self.type.value,
            weight=self.weight,
            properties={
                "description": self.description,
                "chapter": self.chapter,
                "evidence": self.evidence,
            },
        )


@dataclass
class ExtractionResult:
    """Result of entity extraction from a chapter."""

    entities: list[Entity]
    relations: list[Relation]
    events: list[EventEntity]
    chapter: int
    strategy_used: ExtractionStrategy = ExtractionStrategy.HYBRID
    extraction_time: datetime = field(default_factory=datetime.now)

    @property
    def entity_count(self) -> int:
        """Total number of entities extracted."""
        return len(self.entities)

    @property
    def relation_count(self) -> int:
        """Total number of relations extracted."""
        return len(self.relations)

    @property
    def event_count(self) -> int:
        """Total number of events extracted."""
        return len(self.events)

    def get_entities_by_type(self, entity_type: EntityType) -> list[Entity]:
        """Get all entities of a specific type."""
        return [e for e in self.entities if e.type == entity_type]

    def get_relations_by_type(self, relation_type: RelationType) -> list[Relation]:
        """Get all relations of a specific type."""
        return [r for r in self.relations if r.type == relation_type]


class RuleBasedExtractor:
    """Rule-based entity extractor using regex patterns."""

    # Common Chinese location suffixes - require word boundaries
    LOCATION_PATTERNS = [
        # Pattern 1: City/Province/Country with negative lookbehind for verbs
        # Excludes matches preceded by common verbs/particles like 到了, 去了, 在
        r"(?<![到去来走在过从往向了在])[\u4e00-\u9fa5]{2,8}(?:市|省|县|镇|村|街|路|区|城|国|都|府)",
        # Pattern 2: Buildings/Geography with negative lookbehind
        r"(?<![到去来走在过从往向了在])[\u4e00-\u9fa5]{2,6}(?:宫|殿|府|寺|院|庙|观|塔|桥|门|楼|阁|馆|岛|山|江|河|湖|海|岭|林|原|野|谷|溪|泉)",
    ]
    LOCATION_PATTERNS = [
        r"[\u4e00-\u9fa5]{2,10}(?:市|省|县|镇|村|街|路|区|城|国)",
        r"[\u4e00-\u9fa5]{2,8}(?:宫|殿|府|寺|院|庙|观|塔|桥|门|楼|阁|馆|岛|山|江|河|湖|海)",
    ]
    # Common event indicators
    EVENT_INDICATORS = [
        "会议",
        "战斗",
        "战争",
        "会谈",
        "讨论",
        "争吵",
        "决斗",
        "相遇",
        "离别",
        "婚礼",
        "葬礼",
        "庆典",
        "袭击",
        "逃亡",
        "meeting",
        "battle",
        "war",
        "discussion",
        "argument",
        "duel",
        "wedding",
        "funeral",
        "celebration",
        "attack",
        "escape",
    ]

    def __init__(
        self,
        known_characters: dict[str, str] | None = None,
        known_locations: dict[str, str] | None = None,
        registry: CharacterRegistry | None = None,
    ) -> None:
        """Initialize rule-based extractor.

        Args:
            known_characters: Dict of character names to their IDs
            known_locations: Dict of location names to their IDs
            registry: Optional CharacterRegistry for role_id assignment
        """
        self.known_characters = known_characters or {}
        self.known_locations = known_locations or {}
        self.registry = registry
        self._character_pattern: re.Pattern | None = None
        self._location_pattern: re.Pattern | None = None
        self._build_patterns()

    def _build_patterns(self) -> None:
        """Build regex patterns from known entities."""
        if self.known_characters:
            # Sort by length (longest first) to avoid partial matches
            chars = sorted(self.known_characters.keys(), key=len, reverse=True)
            pattern = "|".join(re.escape(c) for c in chars)
            self._character_pattern = re.compile(pattern)

        if self.known_locations:
            locs = sorted(self.known_locations.keys(), key=len, reverse=True)
            pattern = "|".join(re.escape(l) for l in locs)
            self._location_pattern = re.compile(pattern)

    def extract_characters(self, content: str, chapter_num: int) -> list[CharacterEntity]:
        """Extract character mentions using known character list.

        Args:
            content: Chapter content
            chapter_num: Chapter number

        Returns:
            List of character entities found
        """
        entities = []
        if not self._character_pattern:
            return entities

        found = set()
        for match in self._character_pattern.finditer(content):
            name = match.group()
            if name in found:
                continue
            found.add(name)

            char_id = self.known_characters.get(name, f"char_{name}")

            role_id: str | None = None
            if self.registry is not None:
                role_id = self.registry.get_or_create(name, chapter=chapter_num)

            entity = CharacterEntity(
                id=char_id,
                name=name,
                first_appearance=chapter_num,
                appearances=[chapter_num],
                role_id=role_id,
                properties={"role_id": role_id} if role_id else {},
            )
            entities.append(entity)

        logger.debug(f"Rule-based extracted {len(entities)} characters")
        return entities

    def extract_locations(self, content: str, chapter_num: int) -> list[LocationEntity]:
        """Extract location mentions using known location list and patterns.

        Args:
            content: Chapter content
            chapter_num: Chapter number

        Returns:
            List of location entities found
        """
        entities = []
        found = set()

        # First check known locations
        if self._location_pattern:
            for match in self._location_pattern.finditer(content):
                name = match.group()
                if name in found:
                    continue
                found.add(name)

                loc_id = self.known_locations.get(name, f"loc_{name}")
                entity = LocationEntity(
                    id=loc_id,
                    name=name,
                    first_appearance=chapter_num,
                    appearances=[chapter_num],
                )
                entities.append(entity)

        # Then check patterns for new locations
        for pattern in self.LOCATION_PATTERNS:
            for match in re.finditer(pattern, content):
                full_match = match.group()

                # Filter out overly long matches (likely not pure location names)
                if len(full_match) > 8:
                    continue

                # Filter out matches that contain verbs or particles
                invalid_chars = "到去来走在过从往向了在和"
                if any(c in full_match for c in invalid_chars):
                    continue

                # Use the full match as the location name (regex handles boundaries)
                name = full_match
                if name in found or name in self.known_locations:
                    continue
                found.add(name)

                entity = LocationEntity(
                    id=f"loc_{name}",
                    name=name,
                    first_appearance=chapter_num,
                    appearances=[chapter_num],
                )
                entities.append(entity)
        for pattern in self.LOCATION_PATTERNS:
            for match in re.finditer(pattern, content):
                # Extract just the location name (last 2-4 characters typically)
                full_match = match.group()
                # For location patterns, the name is typically the last 2-4 chars
                # Extract suffix (1 char) + preceding 1-3 chars
                name = full_match[-4:] if len(full_match) > 4 else full_match
                # Further refine: for 城/宫 suffix, usually 2-3 chars total
                if len(name) > 3 and name[-1] in "城宫殿府省市县镇":
                    name = name[-3:]
                if name in found or name in self.known_locations:
                    continue
                found.add(name)

                entity = LocationEntity(
                    id=f"loc_{name}",
                    name=name,
                    first_appearance=chapter_num,
                    appearances=[chapter_num],
                )
                entities.append(entity)

        logger.debug(f"Rule-based extracted {len(entities)} locations")
        return entities

    def extract_events(
        self, content: str, chapter_num: int, entities: list[Entity]
    ) -> list[EventEntity]:
        """Extract events based on indicators and context.

        Args:
            content: Chapter content
            chapter_num: Chapter number
            entities: Already extracted entities for context

        Returns:
            List of event entities found
        """
        events = []
        char_names = {e.name for e in entities if e.type == EntityType.CHARACTER}

        # Simple event detection based on indicators
        lines = content.split("\n")
        for _i, line in enumerate(lines):
            for indicator in self.EVENT_INDICATORS:
                # Use regex to check for word boundaries (not followed by CJK char)
                pattern = re.escape(indicator) + r"(?![\u4e00-\u9fa5])"
                if re.search(pattern, line):
                    # Found potential event
                    # Extract participants (characters in same sentence)
                    participants = []
                    for char_name in char_names:
                        if char_name in line:
                            participants.append(char_name)

                    if participants:  # Only create event if we have participants
                        event_id = f"evt_ch{chapter_num}_{len(events)}"
                        event = EventEntity(
                            id=event_id,
                            name=f"{indicator.capitalize()} in chapter {chapter_num}",
                            event_type=indicator,
                            participants=participants,
                            chapter=chapter_num,
                            first_appearance=chapter_num,
                            appearances=[chapter_num],
                        )
                        events.append(event)
                        break  # One event per line max

        logger.debug(f"Rule-based extracted {len(events)} events")
        return events

    def extract_relations(
        self, content: str, chapter_num: int, entities: list[Entity]
    ) -> list[Relation]:
        """Extract relations between entities based on context.

        Args:
            content: Chapter content
            chapter_num: Chapter number
            entities: Extracted entities

        Returns:
            List of relations found
        """
        relations = []

        # Build entity name to ID mapping
        {e.name: e.id for e in entities}

        # Simple relation detection based on proximity and keywords
        relation_keywords = {
            RelationType.FRIEND: ["朋友", "friend", "同伴", "companion", "盟友"],
            RelationType.ENEMY: ["敌人", "enemy", " foe", "对手", "rival"],
            RelationType.FAMILY: [
                "父亲",
                "母亲",
                "兄弟",
                "姐妹",
                "family",
                "father",
                "mother",
                "brother",
                "sister",
            ],
            RelationType.LOVER: ["爱", "lover", "爱人", "beloved", "夫妻"],
            RelationType.LOCATED_AT: ["在", "at", "位于", "located at"],
        }

        sentences = re.split(r"[。！？.!?]", content)

        for sentence in sentences:
            # Find entities in this sentence
            present_entities = []
            for entity in entities:
                if entity.name in sentence:
                    present_entities.append(entity)

            # If 2+ entities present, check for relations
            if len(present_entities) >= 2:
                for rel_type, keywords in relation_keywords.items():
                    for keyword in keywords:
                        if keyword in sentence:
                            # Create relations between all pairs
                            for i, e1 in enumerate(present_entities):
                                for e2 in present_entities[i + 1 :]:
                                    rel = Relation(
                                        source=e1.id,
                                        target=e2.id,
                                        type=rel_type,
                                        chapter=chapter_num,
                                        evidence=sentence.strip(),
                                    )
                                    relations.append(rel)
                            break

        logger.debug(f"Rule-based extracted {len(relations)} relations")
        return relations


class LLMBasedExtractor:
    """LLM-based entity extractor for accurate extraction."""

    def __init__(self, llm: BaseLLM) -> None:
        """Initialize LLM-based extractor.

        Args:
            llm: LLM instance for extraction
        """
        self.llm = llm

    async def extract_entities(self, content: str, chapter_num: int) -> dict[str, Any]:
        """Extract entities using LLM.

        Args:
            content: Chapter content
            chapter_num: Chapter number

        Returns:
            Dictionary with extracted entities, relations, events
        """
        system_prompt = """你是一个专业的实体提取助手。从小说章节中提取所有实体和关系。

提取以下类型的实体：
1. **角色** (character): 人名，包括主角、配角、提及的人物
2. **地点** (location): 地名、建筑名、场所
3. **事件** (event): 章节中发生的重要事件
4. **物品** (item): 重要的物品、武器、道具
5. **组织** (organization): 组织、门派、国家等

对于关系，提取：
- 角色间关系（朋友、敌人、家人等）
- 角色与地点关系（位于、来自等）
- 角色与事件关系（参与者、目击者等）

以JSON格式返回，结构如下：
{
  "entities": [
    {
      "id": "唯一标识符",
      "name": "实体名称",
      "type": "character/location/event/item/organization",
      "aliases": ["别名1", "别名2"],
      "description": "简短描述"
    }
  ],
  "relations": [
    {
      "source": "源实体ID",
      "target": "目标实体ID",
      "type": "关系类型",
      "description": "关系描述"
    }
  ],
  "events": [
    {
      "id": "事件ID",
      "name": "事件名称",
      "type": "事件类型",
      "participants": ["参与者ID列表"],
      "location": "发生地点ID"
    }
  ]
}"""

        user_prompt = f"""请从以下第{chapter_num}章内容中提取实体和关系：

{content[:3000]}  # Limit content length for token efficiency

请只返回JSON格式，不要其他解释。"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,  # Lower temperature for structured output
                max_tokens=2000,
            )

            # Parse JSON response
            result = self._parse_llm_response(response.content)
            logger.info(f"LLM extracted {len(result.get('entities', []))} entities")
            return result

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {"entities": [], "relations": [], "events": []}

    def _parse_llm_response(self, content: str) -> dict[str, Any]:
        """Parse LLM JSON response.

        Args:
            content: LLM response content

        Returns:
            Parsed dictionary
        """
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        # Try to find JSON object directly
        json_match = re.search(r"(\{.*\})", content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return {"entities": [], "relations": [], "events": []}


class EntityExtractor:
    """Extract entities from chapter content and add to knowledge graph."""

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        llm: BaseLLM | None = None,
        strategy: ExtractionStrategy = ExtractionStrategy.HYBRID,
        registry: CharacterRegistry | None = None,
    ) -> None:
        """Initialize entity extractor.

        Args:
            knowledge_graph: Knowledge graph to populate
            llm: Optional LLM for LLM-based extraction
            strategy: Extraction strategy to use
            registry: Optional CharacterRegistry for role_id assignment
        """
        self.kg = knowledge_graph
        self.llm = llm
        self.strategy = strategy
        self.registry = registry

        # Initialize extractors
        self._rule_extractor: RuleBasedExtractor | None = None
        self._llm_extractor: LLMBasedExtractor | None = None

        if llm:
            self._llm_extractor = LLMBasedExtractor(llm)

        self._refresh_known_entities()

    def _refresh_known_entities(self) -> None:
        """Refresh known entities from knowledge graph."""
        known_chars: dict[str, str] = {}
        known_locs: dict[str, str] = {}

        # Get existing entities from KG
        for node in self.kg.find_nodes_by_type("character"):
            name = node.properties.get("name", node.node_id)
            known_chars[name] = node.node_id
            # Also add aliases
            for alias in node.properties.get("aliases", []):
                known_chars[alias] = node.node_id

        for node in self.kg.find_nodes_by_type("location"):
            name = node.properties.get("name", node.node_id)
            known_locs[name] = node.node_id

        self._rule_extractor = RuleBasedExtractor(known_chars, known_locs, self.registry)

    async def extract_from_chapter(
        self,
        chapter_num: int,
        content: str,
    ) -> ExtractionResult:
        """Extract all entities and relations from a chapter.

        Args:
            chapter_num: Chapter number
            content: Chapter content

        Returns:
            ExtractionResult with extracted data
        """
        logger.info(f"Extracting entities from chapter {chapter_num}")

        # Refresh known entities before extraction
        self._refresh_known_entities()

        entities: list[Entity] = []
        relations: list[Relation] = []
        events: list[EventEntity] = []

        if self.strategy == ExtractionStrategy.RULE_BASED:
            entities, relations, events = await self._extract_rule_based(chapter_num, content)
        elif self.strategy == ExtractionStrategy.LLM_BASED and self.llm:
            entities, relations, events = await self._extract_llm_based(chapter_num, content)
        else:  # HYBRID
            entities, relations, events = await self._extract_hybrid(chapter_num, content)

        # Add to knowledge graph
        self._add_to_knowledge_graph(entities, relations, events)

        result = ExtractionResult(
            entities=entities,
            relations=relations,
            events=events,
            chapter=chapter_num,
            strategy_used=self.strategy,
        )

        logger.info(
            f"Chapter {chapter_num}: extracted {result.entity_count} entities, "
            f"{result.relation_count} relations, {result.event_count} events"
        )

        return result

    async def _extract_rule_based(
        self, chapter_num: int, content: str
    ) -> tuple[list[Entity], list[Relation], list[EventEntity]]:
        """Extract using rule-based approach.

        Args:
            chapter_num: Chapter number
            content: Chapter content

        Returns:
            Tuple of (entities, relations, events)
        """
        assert self._rule_extractor is not None

        entities: list[Entity] = []

        # Extract characters
        chars = self._rule_extractor.extract_characters(content, chapter_num)
        entities.extend(chars)

        # Extract locations
        locs = self._rule_extractor.extract_locations(content, chapter_num)
        entities.extend(locs)

        # Extract events
        events = self._rule_extractor.extract_events(content, chapter_num, entities)

        # Extract relations
        relations = self._rule_extractor.extract_relations(content, chapter_num, entities)

        return entities, relations, events

    async def _extract_llm_based(
        self, chapter_num: int, content: str
    ) -> tuple[list[Entity], list[Relation], list[EventEntity]]:
        """Extract using LLM-based approach.

        Args:
            chapter_num: Chapter number
            content: Chapter content

        Returns:
            Tuple of (entities, relations, events)
        """
        assert self._llm_extractor is not None

        result = await self._llm_extractor.extract_entities(content, chapter_num)

        entities: list[Entity] = []
        relations: list[Relation] = []
        events: list[EventEntity] = []

        # Convert LLM result to entities
        for e_data in result.get("entities", []):
            entity = self._convert_to_entity(e_data, chapter_num)
            if entity:
                entities.append(entity)

        # Convert relations
        for r_data in result.get("relations", []):
            relation = self._convert_to_relation(r_data, chapter_num)
            if relation:
                relations.append(relation)

        # Convert events
        for ev_data in result.get("events", []):
            event = self._convert_to_event(ev_data, chapter_num)
            if event:
                events.append(event)

        return entities, relations, events

    async def _extract_hybrid(
        self, chapter_num: int, content: str
    ) -> tuple[list[Entity], list[Relation], list[EventEntity]]:
        """Extract using hybrid approach (rule + LLM).

        Args:
            chapter_num: Chapter number
            content: Chapter content

        Returns:
            Tuple of (entities, relations, events)
        """
        # Start with rule-based extraction
        entities, relations, events = await self._extract_rule_based(chapter_num, content)

        # If LLM available, use it to find new entities
        if self._llm_extractor and self.llm:
            try:
                llm_entities, llm_relations, llm_events = await self._extract_llm_based(
                    chapter_num, content
                )

                # Merge results (avoid duplicates)
                existing_ids = {e.id for e in entities}
                for e in llm_entities:
                    if e.id not in existing_ids:
                        entities.append(e)

                existing_rels = {(r.source, r.target, r.type) for r in relations}
                for r in llm_relations:
                    key = (r.source, r.target, r.type)
                    if key not in existing_rels:
                        relations.append(r)

                existing_events = {ev.id for ev in events}
                for ev in llm_events:
                    if ev.id not in existing_events:
                        events.append(ev)

            except Exception as e:
                logger.warning(f"LLM extraction failed in hybrid mode: {e}")

        return entities, relations, events

    def _convert_to_entity(self, data: dict[str, Any], chapter_num: int) -> Entity | None:
        """Convert LLM entity data to Entity object.

        Args:
            data: Entity data from LLM
            chapter_num: Chapter number

        Returns:
            Entity object or None if invalid
        """
        try:
            entity_type = EntityType(data.get("type", "character"))
            entity_id = data.get("id", f"ent_{data.get('name', 'unknown')}")

            common_props = {
                "id": entity_id,
                "name": data.get("name", ""),
                # type field removed - Entity subclasses define it with init=False
                "aliases": data.get("aliases", []),
                "description": data.get("description", ""),
                "first_appearance": chapter_num,
                "appearances": [chapter_num],
            }

            if entity_type == EntityType.CHARACTER:
                return CharacterEntity(
                    **common_props,
                    gender=data.get("gender", ""),
                    role=data.get("role", ""),
                )
            elif entity_type == EntityType.LOCATION:
                return LocationEntity(
                    **common_props,
                    location_type=data.get("location_type", ""),
                    is_main=data.get("is_main", False),
                )
            elif entity_type == EntityType.EVENT:
                return EventEntity(
                    **common_props,
                    event_type=data.get("event_type", ""),
                    participants=data.get("participants", []),
                    location_id=data.get("location"),
                    chapter=chapter_num,
                )
            else:
                return Entity(**common_props)

        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to convert entity data: {e}")
            return None

    def _convert_to_relation(self, data: dict[str, Any], chapter_num: int) -> Relation | None:
        """Convert LLM relation data to Relation object.

        Args:
            data: Relation data from LLM
            chapter_num: Chapter number

        Returns:
            Relation object or None if invalid
        """
        try:
            return Relation(
                source=data.get("source", ""),
                target=data.get("target", ""),
                type=RelationType(data.get("type", "related_to")),
                description=data.get("description", ""),
                chapter=chapter_num,
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to convert relation data: {e}")
            return None

    def _convert_to_event(self, data: dict[str, Any], chapter_num: int) -> EventEntity | None:
        """Convert LLM event data to EventEntity object.

        Args:
            data: Event data from LLM
            chapter_num: Chapter number

        Returns:
            EventEntity object or None if invalid
        """
        try:
            return EventEntity(
                id=data.get("id", f"evt_ch{chapter_num}_{data.get('name', 'unknown')}"),
                name=data.get("name", ""),
                event_type=data.get("type", ""),
                participants=data.get("participants", []),
                location_id=data.get("location"),
                chapter=chapter_num,
                first_appearance=chapter_num,
                appearances=[chapter_num],
            )
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to convert event data: {e}")
            return None

    def _add_to_knowledge_graph(
        self,
        entities: list[Entity],
        relations: list[Relation],
        events: list[EventEntity],
    ) -> None:
        """Add extracted data to knowledge graph.

        Args:
            entities: List of entities to add
            relations: List of relations to add
            events: List of events to add
        """
        # Add entities as nodes
        for entity in entities:
            try:
                # Check if entity already exists
                existing = self.kg.get_node(entity.id)
                if existing:
                    # Update appearances
                    appearances = set(existing.properties.get("appearances", []))
                    appearances.update(entity.appearances)
                    # Merge new properties (like role_id) while preserving existing
                    merged_props = dict(existing.properties)
                    merged_props.update(entity.properties)
                    merged_props["appearances"] = sorted(appearances)
                    self.kg.update_node(
                        entity.id,
                        properties=merged_props,
                    )
                else:
                    # Add new node
                    node = entity.to_knowledge_graph_node()
                    self.kg.add_node(
                        node_id=node.node_id,
                        node_type=node.node_type,
                        properties=node.properties,
                    )
            except ValueError:
                # Entity already exists (from another source)
                pass

        # Add events as nodes too
        for event in events:
            try:
                existing = self.kg.get_node(event.id)
                if not existing:
                    node = event.to_knowledge_graph_node()
                    self.kg.add_node(
                        node_id=node.node_id,
                        node_type=node.node_type,
                        properties=node.properties,
                    )
            except ValueError:
                pass

        # Add relations as edges
        for relation in relations:
            try:
                edge_id = f"rel_{relation.source}_{relation.target}_{relation.chapter}"
                edge = relation.to_knowledge_graph_edge(edge_id)
                self.kg.add_edge(
                    edge_id=edge.edge_id,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    relationship_type=edge.relationship_type,
                    weight=edge.weight,
                    properties=edge.properties,
                )
            except ValueError:
                # Edge already exists or nodes don't exist
                pass

    def extract_characters(self, content: str) -> list[CharacterEntity]:
        """Extract character entities from content.

        Args:
            content: Text content to extract from

        Returns:
            List of character entities
        """
        self._refresh_known_entities()
        assert self._rule_extractor is not None
        return self._rule_extractor.extract_characters(content, chapter_num=0)

    def extract_locations(self, content: str) -> list[LocationEntity]:
        """Extract location entities from content.

        Args:
            content: Text content to extract from

        Returns:
            List of location entities
        """
        self._refresh_known_entities()
        assert self._rule_extractor is not None
        return self._rule_extractor.extract_locations(content, chapter_num=0)

    async def extract_events(self, chapter_num: int, content: str) -> list[EventEntity]:
        """Extract events from content.

        Args:
            chapter_num: Chapter number
            content: Text content to extract from

        Returns:
            List of event entities
        """
        self._refresh_known_entities()

        if self._llm_extractor:
            result = await self._llm_extractor.extract_entities(content, chapter_num)
            events = []
            for ev_data in result.get("events", []):
                event = self._convert_to_event(ev_data, chapter_num)
                if event:
                    events.append(event)
            return events
        else:
            assert self._rule_extractor is not None
            entities = self.extract_characters(content)
            entities.extend(self.extract_locations(content))
            return self._rule_extractor.extract_events(content, chapter_num, entities)

    async def extract_relations(self, content: str, entities: list[Entity]) -> list[Relation]:
        """Extract relations between entities.

        Args:
            content: Text content to extract from
            entities: List of entities to find relations between

        Returns:
            List of relations
        """
        self._refresh_known_entities()
        assert self._rule_extractor is not None
        return self._rule_extractor.extract_relations(content, chapter_num=0, entities=entities)

    def update_entity_appearances(self, entity_id: str, chapter_num: int) -> None:
        """Update entity appearance record.

        Args:
            entity_id: Entity ID to update
            chapter_num: Chapter number where entity appeared
        """
        node = self.kg.get_node(entity_id)
        if node:
            appearances = set(node.properties.get("appearances", []))
            appearances.add(chapter_num)
            self.kg.update_node(
                entity_id,
                properties={"appearances": sorted(appearances)},
            )
            logger.debug(f"Updated appearances for {entity_id}: chapter {chapter_num}")


__all__ = [
    "EntityExtractor",
    "Entity",
    "CharacterEntity",
    "LocationEntity",
    "EventEntity",
    "Relation",
    "ExtractionResult",
    "EntityType",
    "RelationType",
    "ExtractionStrategy",
    "RuleBasedExtractor",
    "LLMBasedExtractor",
]
