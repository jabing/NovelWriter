"""Automatic inventory updating system for novel writing.

This module provides the InventoryUpdater class which automatically updates
knowledge graph, timeline, glossary, and memory systems after each chapter
generation to maintain a comprehensive inventory of story elements.
"""

import logging
import re
import time
from typing import Any

from src.novel_agent.novel.continuity import ContinuityManager, StoryState
from src.novel_agent.novel.glossary import GlossaryManager, GlossaryTerm, TermStatus, TermType
from src.novel_agent.novel.knowledge_graph import KnowledgeGraph
from src.novel_agent.novel.simple_glossary import SimpleGlossaryManager
from src.novel_agent.novel.timeline_manager import TimelineManager, TimeUnit

logger = logging.getLogger(__name__)


class InventoryUpdater:
    """Updates inventory systems after each chapter generation.

    Automatically extracts entities, relationships, and events from chapter
    content and updates:
    - Knowledge graph (entities and relationships)
    - Timeline (chronological events)
    - Glossary (terms and definitions)
    - Memory systems (character, world, plot memory)

    The updater is designed to be integrated into the chapter generation
    pipeline, running after each chapter is written but before validation.
    """

    # Common stop words to filter out
    _stop_words = {
        "his", "her", "its", "their", "my", "your", "our",
        "he", "she", "it", "they", "them", "we", "us",
        "him", "hers", "the", "a", "an", "and", "but", "or",
        "this", "that", "these", "those", "there", "here",
        "who", "what", "where", "when", "why", "how",
        "for", "with", "from", "by", "as", "at", "of",
        "in", "on", "to", "into", "onto", "upon",
        "while", "though", "although", "because", "since",
        "unless", "until", "whether", "both", "each", "every", "any", "some", "most", "many", "few",
        "more", "less", "much", "little", "several",
        "own", "same", "such", "only", "just", "very", "too",
        "also", "even", "still", "already", "yet", "not", "no",
        "so", "then", "therefore", "however", "thus", "hence",
        "maybe", "perhaps", "quite", "rather", "somewhat",
        "well", "almost", "nearly", "hardly",
        "really", "simply", "actually", "basically", "essentially",
        "generally", "usually", "often", "sometimes", "rarely",
        "never", "always", "forever", "constantly", "continuously",
        "suddenly", "immediately", "instantly", "quickly", "slowly",
        "carefully", "silently", "loudly", "happily", "sadly",
        "angrily", "calmly", "nervously", "bravely", "cowardly",
        "somewhere", "anywhere", "everywhere", "nowhere",
        "someone", "anyone", "everyone", "no one", "nobody",
        "something", "anything", "everything", "nothing",
        "somebody", "anybody", "everybody", "anyway", "anyhow", "somehow",
        "besides", "furthermore", "moreover", "otherwise",
        "nevertheless", "nonetheless", "notwithstanding",
        "consequently", "accordingly", "subsequently",
        "meanwhile", "afterwards", "beforehand", "previously",
        "currently", "presently", "recently", "lately",
        "eventually", "ultimately", "finally", "initially",
        "originally", "primarily", "secondarily", "tertiarily",
        "quarterly", "annually", "monthly", "weekly", "daily",
        "hourly", "minutely", "secondly", "thirdly", "fourthly",
        "fifthly", "sixthly", "seventhly", "eighthly", "ninthly",
        "tenthly", "eleventhly", "twelfthly", "thirteenthly",
        "fourteenthly", "fifteenthly", "sixteenthly", "seventeenthly",
        "eighteenthly", "nineteenthly", "twentiethly",
        "twenty-firstly", "twenty-secondly", "twenty-thirdly",
        "twenty-fourthly", "twenty-fifthly", "twenty-sixthly",
        "twenty-seventhly", "twenty-eighthly", "twenty-ninthly",
        "thirty-firstly", "thirty-secondly", "thirty-thirdly",
        "thirty-fourthly", "thirty-fifthly", "thirty-sixthly",
        "thirty-seventhly", "thirty-eighthly", "thirty-ninthly",
        "forty-firstly", "forty-secondly", "forty-thirdly",
        "forty-fourthly", "forty-fifthly", "forty-sixthly",
        "forty-seventhly", "forty-eighthly", "forty-ninthly",
        "fifty-firstly", "fifty-secondly", "fifty-thirdly",
        "fifty-fourthly", "fifty-fifthly", "fifty-sixthly",
        "fifty-seventhly", "fifty-eighthly", "fifty-ninthly",
        "through", "under", "over", "between", "among", "during", "before", "after",
    }

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph | None = None,
        timeline_manager: TimelineManager | None = None,
        glossary_manager: GlossaryManager | None = None,
        continuity_manager: ContinuityManager | None = None,
    ) -> None:
        """Initialize the inventory updater.

        Args:
            knowledge_graph: Knowledge graph for entity/relationship tracking
            timeline_manager: Timeline manager for event tracking
            glossary_manager: Glossary manager for term tracking
            continuity_manager: Continuity manager for character state extraction
        """
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self.timeline_manager = timeline_manager or TimelineManager()

        # Initialize glossary manager with fallback for missing dependencies
        if glossary_manager is not None:
            self.glossary_manager = glossary_manager
        else:
            try:
                self.glossary_manager = GlossaryManager()
            except Exception as e:
                logger.warning(f"Failed to initialize GlossaryManager: {e}. Trying SimpleGlossaryManager...")
                try:
                    self.glossary_manager = SimpleGlossaryManager()
                except Exception as e2:
                    logger.warning(f"Failed to initialize SimpleGlossaryManager: {e2}. Glossary updates will be skipped.")
                    self.glossary_manager = None

        self.continuity_manager = continuity_manager or ContinuityManager()

        # Entity extraction patterns
        self._character_pattern = re.compile(r"\b([A-Z][a-z]+)\b")
        self._location_pattern = re.compile(
            r"(?:at|in|the|from) (?:the )?([A-Z][a-z]+(?: [A-Z][a-z]+)?)", re.IGNORECASE
        )
        self._item_pattern = re.compile(
            r"(?:the|a|an|his|her|its|their|my|your|our) ([A-Z][a-z]+(?:\s+(?:of|the|and|in|on|at|to|from|by|with)?\s*[A-Z][a-z]+)*)", re.IGNORECASE
        )

        logger.info("InventoryUpdater initialized")

    async def update_inventory(
        self,
        chapter_content: str,
        chapter_number: int,
        story_state: StoryState | None = None,
    ) -> dict[str, Any]:
        """Update all inventory systems with content from a new chapter.

        Args:
            chapter_content: The full text of the chapter
            chapter_number: Chapter number for context
            story_state: Optional current story state for character context

        Returns:
            Dictionary with update statistics and any errors
        """
        logger.info(f"Updating inventory for chapter {chapter_number}")
        start_time = time.time()

        # Performance tracking
        perf_timings = {}
        stats = {
            "entities_extracted": 0,
            "relationships_extracted": 0,
            "events_extracted": 0,
            "glossary_terms_added": 0,
            "errors": [],
        }

        try:
            # Step 1: Extract entities from chapter content
            step_start = time.time()
            entities = self._extract_entities(chapter_content, story_state)
            stats["entities_extracted"] = len(entities)
            perf_timings["entity_extraction"] = time.time() - step_start

            # Step 2: Update knowledge graph with entities
            step_start = time.time()
            for entity_type, entity_name, properties in entities:
                await self._update_knowledge_graph(
                    entity_type, entity_name, properties, chapter_number
                )
            perf_timings["knowledge_graph_entities"] = time.time() - step_start

            # Step 3: Extract relationships between entities
            step_start = time.time()
            relationships = self._extract_relationships(chapter_content, entities)
            stats["relationships_extracted"] = len(relationships)
            perf_timings["relationship_extraction"] = time.time() - step_start

            # Step 4: Update knowledge graph with relationships
            step_start = time.time()
            for source, target, rel_type, evidence in relationships:
                await self._update_knowledge_graph_relationship(
                    source, target, rel_type, evidence, chapter_number
                )
            perf_timings["knowledge_graph_relationships"] = time.time() - step_start

            # Step 5: Extract events for timeline
            step_start = time.time()
            events = self._extract_events(chapter_content, chapter_number)
            stats["events_extracted"] = len(events)
            perf_timings["event_extraction"] = time.time() - step_start

            # Step 6: Update timeline with events
            step_start = time.time()
            for event_id, timestamp, description, event_type, metadata in events:
                await self._update_timeline(
                    event_id, timestamp, description, event_type, metadata, chapter_number
                )
            perf_timings["timeline_updates"] = time.time() - step_start

            # Step 7: Extract and update glossary terms
            step_start = time.time()
            glossary_terms = self._extract_glossary_terms(chapter_content)
            stats["glossary_terms_added"] = len(glossary_terms)
            perf_timings["glossary_extraction"] = time.time() - step_start

            step_start = time.time()
            for term, term_type, definition in glossary_terms:
                await self._update_glossary(term, term_type, definition, chapter_number)
            perf_timings["glossary_updates"] = time.time() - step_start

            # Calculate total time
            total_time = time.time() - start_time
            perf_timings["total"] = total_time

            # Add performance metrics to stats
            stats["performance"] = perf_timings

            logger.info(
                f"Inventory update complete for chapter {chapter_number}: "
                f"{stats['entities_extracted']} entities, "
                f"{stats['relationships_extracted']} relationships, "
                f"{stats['events_extracted']} events, "
                f"{stats['glossary_terms_added']} glossary terms "
                f"(total: {total_time:.3f}s)"
            )

            # Log detailed performance breakdown
            logger.debug(f"Performance breakdown: {perf_timings}")
            # Step 1: Extract entities from chapter content
            entities = self._extract_entities(chapter_content, story_state)
            stats["entities_extracted"] = len(entities)

            # Step 2: Update knowledge graph with entities
            for entity_type, entity_name, properties in entities:
                await self._update_knowledge_graph(
                    entity_type, entity_name, properties, chapter_number
                )

            # Step 3: Extract relationships between entities
            relationships = self._extract_relationships(chapter_content, entities)
            stats["relationships_extracted"] = len(relationships)

            # Step 4: Update knowledge graph with relationships
            for source, target, rel_type, evidence in relationships:
                await self._update_knowledge_graph_relationship(
                    source, target, rel_type, evidence, chapter_number
                )

            # Step 5: Extract events for timeline
            events = self._extract_events(chapter_content, chapter_number)
            stats["events_extracted"] = len(events)

            # Step 6: Update timeline with events
            for event_id, timestamp, description, event_type, metadata in events:
                await self._update_timeline(
                    event_id, timestamp, description, event_type, metadata, chapter_number
                )

            # Step 7: Extract and update glossary terms
            glossary_terms = self._extract_glossary_terms(chapter_content)
            stats["glossary_terms_added"] = len(glossary_terms)

            for term, term_type, definition in glossary_terms:
                await self._update_glossary(term, term_type, definition, chapter_number)

            logger.info(
                f"Inventory update complete for chapter {chapter_number}: "
                f"{stats['entities_extracted']} entities, "
                f"{stats['relationships_extracted']} relationships, "
                f"{stats['events_extracted']} events, "
                f"{stats['glossary_terms_added']} glossary terms"
            )

        except Exception as e:
            error_msg = f"Inventory update failed for chapter {chapter_number}: {e}"
            logger.error(error_msg)
            stats["errors"].append(error_msg)

        return stats

    def _extract_entities(
        self,
        content: str,
        story_state: StoryState | None = None,
    ) -> list[tuple[str, str, dict[str, Any]]]:
        """Extract entities (characters, locations, items) from chapter content.

        Args:
            content: Chapter content text
            story_state: Optional story state for character context

        Returns:
            List of (entity_type, entity_name, properties) tuples
        """
        entities = []

        # Extract characters using continuity manager's method
        character_names = self.continuity_manager._extract_character_names(content)

        # Also include characters from story state if available
        if story_state:
            for char_name in story_state.character_states:
                if char_name not in character_names:
                    character_names.append(char_name)

        for name in character_names:
            entities.append(
                (
                    "character",
                    name,
                    {
                        "name": name,
                        "type": "character",
                        "source": "chapter_extraction",
                    },
                )
            )

        # Extract locations using continuity manager's method
        location = self.continuity_manager._extract_location(content)
        if location:
            entities.append(
                (
                    "location",
                    location,
                    {
                        "name": location,
                        "type": "location",
                        "source": "chapter_extraction",
                    },
                )
            )

        # Extract items using simple pattern matching
        # This is a basic heuristic - can be improved with NLP
        item_matches = self._item_pattern.findall(content)
        for item in item_matches:
            # Clean item name: remove trailing prepositions and stop words
            words = item.split()
            # Remove trailing prepositions
            preposition_stop_words = {"of", "with", "for", "to", "from", "and", "or", "but", "yet", "so", "as", "at", "by", "in", "on", "up", "down", "the", "a", "an"}
            while words and words[-1].lower() in preposition_stop_words:
                words.pop()
            # Remove leading stop words
            while words and words[0].lower() in preposition_stop_words:
                words.pop(0)
            if not words:
                continue
            cleaned_item = " ".join(words)
            # Skip if already captured as character or location
            if any(e[1] == cleaned_item for e in entities):
                continue
            # Skip common words that aren't items
            if len(cleaned_item) < 3 or cleaned_item.lower() in ["the", "and", "but", "for", "with"]:
                continue
            # Skip verb phrases (words ending with common verb suffixes)
            last_word = words[-1].lower()
            if last_word.endswith(('ed', 'ing', 'es', 's')) and len(last_word) > 3:
                # But allow common nouns that also end with these suffixes
                common_nouns_with_suffixes = {'caves', 'swords', 'horses', 'crystals', 'weapons', 'dragons', 'forests', 'edges', 'skies'}
                if last_word not in common_nouns_with_suffixes:
                    continue
            logger.debug(f"Item extracted: '{item}' -> '{cleaned_item}'")
            entities.append(
                (
                    "item",
                    cleaned_item,
                    {
                        "name": cleaned_item,
                        "type": "item",
                        "source": "chapter_extraction",
                    },
                )
            )

        return entities

    def _extract_relationships(
        self,
        content: str,
        entities: list[tuple[str, str, dict[str, Any]]],
    ) -> list[tuple[str, str, str, str]]:
        """Extract relationships between entities from chapter content.

        Args:
            content: Chapter content text
            entities: List of extracted entities

        Returns:
            List of (source_entity, target_entity, relationship_type, evidence) tuples
        """
        relationships = []

        # Stop words are defined in class attribute _stop_words


        # Simple relationship patterns
        patterns = [
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:went to|arrived at|traveled to) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "traveled_to"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:gave|handed) ([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) to ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "gave"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:talked to|spoke with) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "spoke_with"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:fought|battled) ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "fought"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:loved|hated) ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "emotional_toward"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:found|discovered) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "found"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:used|wielded) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "used"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:belongs to|owned by) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "owned_by"),
            # New patterns based on common relationship verbs
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:met|saw|encountered) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "met"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:carried|held|wore) (?:the|a|an|his|her|their)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "possesses"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:defended|protected|rescued) (?:the|a|an|his|her|their)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "defended"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:attacked|chased|escaped from) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "combat"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:led|guided|accompanied) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "accompanied"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:raised|lifted) (?:his|her|their|the)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "raised"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:rode|mounted) (?:his|her|their|the)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "rode"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) and ([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:together|discovered|found) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "discovered_together"),
            # Additional relationship patterns for novel writing
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:promised|swore|vowed) to (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "promised"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:betrayed|deceived) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "betrayed"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:forgave|apologized to) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "forgave"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:taught|trained) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "taught"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:learned from|studied under) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "learned_from"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:married|wed) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "married"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:birthed|gave birth to) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "parent_of"),
            (r"([A-Za-z]+(?:\s+[A-Za-z]+){0,2}) (?:died for|sacrificed for) (?:the|a|an)? ([A-Za-z]+(?:\s+[A-Za-z]+){0,2})", "sacrificed_for"),
        ]

        for pattern, rel_type in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                logger.debug(f"Relationship pattern match: {match.group(0)}")
                # Extract entity names from match groups
                groups = match.groups()
                logger.debug(f"Groups: {groups}")
                if len(groups) >= 2:
                    source = groups[0]
                    target = groups[-1]

                    # Clean entity phrases by removing stop words
                    source_cleaned = self._clean_entity_phrase(source)
                    target_cleaned = self._clean_entity_phrase(target)
                    logger.debug(f"Cleaned: '{source}' -> '{source_cleaned}', '{target}' -> '{target_cleaned}'")

                    # Skip if cleaning resulted in empty phrases
                    if source_cleaned is None or target_cleaned is None:
                        continue

                    # Skip if source or target is a stop word (should not happen after cleaning)
                    if source_cleaned.lower() in self._stop_words or target_cleaned.lower() in self._stop_words:
                        continue

                    # Check if these entities are in our extracted list
                    source_entity = self._find_entity_by_name(entities, source_cleaned)
                    target_entity = self._find_entity_by_name(entities, target_cleaned)

                    # Require at least source entity to exist
                    if source_entity:
                        source_name = source_entity[1]
                        # Use target entity name if found, otherwise raw target string
                        target_name = target_entity[1] if target_entity else target_cleaned
                        relationships.append(
                            (
                                source_name,
                                target_name,
                                rel_type,
                                match.group(0),  # evidence text
                            )
                        )
                    else:
                        logger.debug(f"Skipping relationship: source entity '{source_cleaned}' not found in extracted entities")

        return relationships

    def _extract_events(
        self,
        content: str,
        chapter_number: int,
    ) -> list[tuple[str, str, str, str, dict[str, Any]]]:
        """Extract events for timeline from chapter content.

        Args:
            content: Chapter content text
            chapter_number: Chapter number for event ID generation

        Returns:
            List of (event_id, timestamp, description, event_type, metadata) tuples
        """
        events = []

        # Simple event detection - look for sentences with action verbs
        sentences = re.split(r"[.!?]+", content)
        event_counter = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            # Heuristic: sentences with certain keywords indicate events
            event_keywords = [
                ("battle", "combat"),
                ("discover", "discovery"),
                ("arrive", "arrival"),
                ("leave", "departure"),
                ("meet", "meeting"),
                ("kill", "death"),
                ("marry", "wedding"),
                ("begin", "start"),
                ("end", "conclusion"),
                ("decide", "decision"),
                # Common novel events
                ("fight", "combat"),
                ("attack", "combat"),
                ("defend", "defense"),
                ("escape", "escape"),
                ("capture", "capture"),
                ("rescue", "rescue"),
                ("betray", "betrayal"),
                ("reveal", "revelation"),
                ("learn", "discovery"),
                ("find", "discovery"),
                ("lose", "loss"),
                ("win", "victory"),
                ("fail", "failure"),
                ("promise", "promise"),
                ("swear", "oath"),
                ("vow", "oath"),
                ("confess", "confession"),
                ("apologize", "apology"),
                ("forgive", "forgiveness"),
                ("travel", "journey"),
                ("journey", "journey"),
                ("return", "return"),
                ("transform", "transformation"),
                ("change", "change"),
                ("grow", "growth"),
            ]

            for keyword, event_type in event_keywords:
                if keyword in sentence.lower():
                    event_id = f"ch{chapter_number:03d}_ev{event_counter:03d}"
                    timestamp = f"Chapter {chapter_number}"
                    description = sentence[:200]  # Truncate if too long
                    metadata = {
                        "sentence": sentence,
                        "keyword": keyword,
                        "chapter": chapter_number,
                    }

                    events.append(
                        (
                            event_id,
                            timestamp,
                            description,
                            event_type,
                            metadata,
                        )
                    )
                    event_counter += 1
                    break  # Only categorize once per sentence

        return events

    def _extract_glossary_terms(
        self,
        content: str,
    ) -> list[tuple[str, str, str]]:
        """Extract glossary terms from chapter content.

        Args:
            content: Chapter content text

        Returns:
            List of (term, term_type, definition) tuples
        """
        terms = []

        # Look for capitalized multi-word phrases (potential proper nouns)
        # This is a simple heuristic - can be enhanced with NLP
        proper_noun_pattern = r"\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b"
        matches = re.finditer(proper_noun_pattern, content)

        for match in matches:
            term = match.group(1)

            # Skip if it's likely a character name (already handled)
            # Skip common phrases
            common_phrases = ["Chapter", "The", "He", "She", "They", "It"]
            if any(term.startswith(phrase) for phrase in common_phrases):
                continue

            # Determine term type based on context
            term_type = self._classify_term_type(term, content)
            definition = f"Appears in chapter content: {term}"

            terms.append((term, term_type, definition))

        return terms

    async def _update_knowledge_graph(
        self,
        entity_type: str,
        entity_name: str,
        properties: dict[str, Any],
        chapter_number: int,
    ) -> None:
        """Update knowledge graph with an entity.

        Args:
            entity_type: Type of entity (character, location, item, concept)
            entity_name: Name of the entity
            properties: Entity properties
            chapter_number: Chapter number for context
        """
        try:
            node_id = f"{entity_type}:{entity_name.lower().replace(' ', '_')}"

            # Check if node already exists
            if node_id in self.knowledge_graph._nodes:
                # Update existing node with new properties
                self.knowledge_graph.update_node(
                    node_id,
                    properties=properties,
                    merge_properties=True,
                )
                logger.debug(f"Updated knowledge graph node: {node_id}")
            else:
                # Create new node
                self.knowledge_graph.add_node(
                    node_id=node_id,
                    node_type=entity_type,
                    properties=properties,
                )
                logger.debug(f"Added knowledge graph node: {node_id}")

        except Exception as e:
            logger.warning(f"Failed to update knowledge graph for {entity_name}: {e}")

    async def _update_knowledge_graph_relationship(
        self,
        source_entity: str,
        target_entity: str,
        relationship_type: str,
        evidence: str,
        chapter_number: int,
    ) -> None:
        """Update knowledge graph with a relationship between entities.

        Args:
            source_entity: Source entity name
            target_entity: Target entity name
            relationship_type: Type of relationship
            evidence: Text evidence for the relationship
            chapter_number: Chapter number for context
        """
        try:
            source_id = self._get_entity_node_id(source_entity)
            target_id = self._get_entity_node_id(target_entity)

            if not source_id or not target_id:
                logger.warning(
                    f"Cannot create relationship: missing node for source={source_entity}, target={target_entity}"
                )
                return

            edge_id = f"{source_id}->{target_id}:{relationship_type}:{chapter_number}"

            # Check if edge already exists
            if edge_id in self.knowledge_graph._edges:
                # Update existing edge
                # For simplicity, we'll just skip duplicates
                return

            # Create new edge
            self.knowledge_graph.add_edge(
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                relationship_type=relationship_type,
                properties={
                    "evidence": evidence,
                    "chapter": chapter_number,
                },
            )
            logger.debug(f"Added knowledge graph edge: {edge_id}")

        except Exception as e:
            logger.warning(
                f"Failed to update knowledge graph relationship {source_entity}->{target_entity}: {e}"
            )

    async def _update_timeline(
        self,
        event_id: str,
        timestamp: str,
        description: str,
        event_type: str,
        metadata: dict[str, Any],
        chapter_number: int,
    ) -> None:
        """Update timeline with an event.

        Args:
            event_id: Unique event identifier
            timestamp: Human-readable timestamp
            description: Event description
            event_type: Type of event
            metadata: Additional properties
            chapter_number: Chapter number for context
        """
        try:
            # Check if event already exists
            if event_id in self.timeline_manager._events:
                # Update existing event
                self.timeline_manager.update_event(
                    event_id,
                    description=description,
                    metadata=metadata,
                    merge_metadata=True,
                )
                logger.debug(f"Updated timeline event: {event_id}")
            else:
                # Create new event
                self.timeline_manager.add_event(
                    event_id=event_id,
                    timestamp=timestamp,
                    description=description,
                    event_type=event_type,
                    metadata=metadata,
                    time_unit=TimeUnit.SCENE,
                )
                logger.debug(f"Added timeline event: {event_id}")

        except Exception as e:
            logger.warning(f"Failed to update timeline event {event_id}: {e}")

    async def _update_glossary(
        self,
        term: str,
        term_type: str,
        definition: str,
        chapter_number: int,
    ) -> None:
        """Update glossary with a term.

        Args:
            term: The term
            term_type: Type of term (character, location, item, concept, etc.)
            definition: Term definition
            chapter_number: Chapter number for context
        """
        if self.glossary_manager is None:
            logger.debug(f"Skipping glossary update for term '{term}' (glossary manager not available)")
            return

        try:
            # Map our entity types to glossary term types
            type_mapping = {
                "character": TermType.CHARACTER,
                "location": TermType.LOCATION,
                "item": TermType.OBJECT,
                "concept": TermType.CONCEPT,
            }

            glossary_type = type_mapping.get(term_type, TermType.OTHER)

            # Check if term already exists
            existing_term = await self.glossary_manager.retrieve_term(term)
            if existing_term:
                # Update existing term
                existing_term.definition = definition
                existing_term.notes = f"Updated from chapter {chapter_number}"
                await self.glossary_manager.store_term(existing_term)
                logger.debug(f"Updated glossary term: {term}")
            else:
                # Create new term
                glossary_term = GlossaryTerm(
                    term=term,
                    type=glossary_type,
                    definition=definition,
                    status=TermStatus.APPROVED,
                    notes=f"Added from chapter {chapter_number}",
                    metadata={"source_chapter": chapter_number},
                )
                await self.glossary_manager.store_term(glossary_term)
                logger.debug(f"Added glossary term: {term}")

        except Exception as e:
            logger.warning(f"Failed to update glossary term {term}: {e}")

    # Helper methods

    def _find_entity_by_name(
        self,
        entities: list[tuple[str, str, dict[str, Any]]],
        name: str,
    ) -> tuple[str, str, dict[str, Any]] | None:
        """Find an entity by name (case-insensitive partial match).

        Args:
            entities: List of entities
            name: Entity name to find

        Returns:
            Matching entity tuple or None
        """
        name_lower = name.lower()
        for entity in entities:
            entity_name = entity[1].lower()
            if entity_name == name_lower or name_lower in entity_name:
                return entity
        return None

    def _get_entity_node_id(self, entity_name: str) -> str | None:
        """Get knowledge graph node ID for an entity name.

        Args:
            entity_name: Entity name

        Returns:
            Node ID or None if not found
        """
        # Skip stop words
        if entity_name.lower() in self._stop_words:
            return None

        # Try to find the node by searching through nodes
        for node_id, node in self.knowledge_graph._nodes.items():
            if node.properties.get("name", "").lower() == entity_name.lower():
                return node_id

        # If not found, construct a plausible ID
        # This assumes the node will be created later
        return f"unknown:{entity_name.lower().replace(' ', '_')}"

    def _clean_entity_phrase(self, phrase: str) -> str | None:
        """Clean an entity phrase by removing stop words.

        Args:
            phrase: Raw phrase extracted from text

        Returns:
            Cleaned phrase with stop words removed, or None if phrase is empty after cleaning
        """
        words = phrase.split()
        cleaned_words = []
        collecting = False
        for word in words:
            if word.lower() not in self._stop_words:
                # Start collecting when we hit first non-stop word
                collecting = True
                cleaned_words.append(word)
            elif collecting:
                # Once we've started collecting, encountering a stop word ends collection
                break
        if not cleaned_words:
            return None
        # Return the collected phrase (preserving original word order)
        return " ".join(cleaned_words)


    def _classify_term_type(self, term: str, context: str) -> str:
        """Classify a term's type based on context.

        Args:
            term: The term to classify
            context: Surrounding text context

        Returns:
            Term type string ("character", "location", "item", "concept")
        """
        context_lower = context.lower()


        # Check for character indicators
        character_indicators = ["said", "asked", "replied", "thought", "felt"]
        if any(indicator in context_lower for indicator in character_indicators):
            return "character"

        # Check for location indicators
        location_indicators = ["in", "at", "to", "from", "arrived", "traveled"]
        if any(indicator in context_lower for indicator in location_indicators):
            return "location"

        # Check for item indicators
        item_indicators = ["held", "carried", "used", "wielded", "found", "dropped"]
        if any(indicator in context_lower for indicator in item_indicators):
            return "item"

        # Default to concept
        return "concept"
