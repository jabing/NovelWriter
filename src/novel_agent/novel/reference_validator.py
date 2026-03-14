"""Reference validator for extracting and verifying citations in novel text.

Detects and validates references like "Character said X" or "According to character's memory Y"
to identify hallucinated or unsupported references in generated content.

Example:
    >>> from src.novel_agent.novel.reference_validator import ReferenceValidator
    >>> validator = ReferenceValidator(knowledge_graph, vector_store)
    >>> refs = validator.extract_references(chapter_content, 5)
    >>> verifications = validator.validate_chapter_references(chapter_content, 5)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.novel_agent.db.vector_store_factory import VectorStoreFactory
from src.novel_agent.novel.knowledge_graph import KnowledgeGraph
from src.novel_agent.utils.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Reference:
    """A reference to a past event, statement, or action in the novel.

    Attributes:
        text: Original text containing the reference
        speaker: Who is making the reference
        referenced_character: Who is being referenced
        referenced_action: Action type (说过, 做过, 提到, etc.)
        referenced_content: The content being referenced
        chapter: Chapter number where reference appears
        confidence: Confidence score for extraction (0.0-1.0)
    """

    text: str
    speaker: str
    referenced_character: str
    referenced_action: str
    referenced_content: str
    chapter: int
    confidence: float = 0.0


@dataclass
class ReferenceVerification:
    """Result of verifying a reference.

    Attributes:
        reference: The original reference being verified
        is_valid: Whether the reference has supporting evidence
        confidence: Verification confidence (0.0-1.0)
        evidence: List of evidence supporting or contradicting the reference
        issues: List of problems found (if any)
        similar_facts: Similar facts found in knowledge base
    """

    reference: Reference
    is_valid: bool
    confidence: float
    evidence: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    similar_facts: list[dict[str, Any]] = field(default_factory=list)


class ReferenceValidator:
    """Validates references in novel text against knowledge graph and vector store.

    Uses regex patterns to extract references, then verifies them against:
    1. Knowledge graph for explicit facts and events
    2. Vector store for semantic similarity to established facts

    Detects hallucinated references like "林晚说过天下大势，分久必合" when no
    such statement exists in the story.
    """

    # Reference extraction patterns (Chinese)
    REFERENCE_PATTERNS = [
        # Pattern: A说过"B"
        (r'([^。]+?)说过["\']([^"\']+)["\']', "说过"),
        # Pattern: A曾(提到|说|讲)B
        (r"([^。]+?)曾(提到|说|讲)([^。]+)", "mentioned"),
        # Pattern: 据A(回忆|记得)B
        (r"据([^。]+?)(回忆|记得)([^。]+)", "recalled"),
        # Pattern: A记得B
        (r"([^。]+?)记得([^。]+)", "recalled"),
        # Pattern: A提到过B
        (r"([^。]+?)提到过([^。]+)", "mentioned"),
        # Pattern: 正如A(所言|所说)B
        (r"正如([^。]+?)(所言|所说)([^。]+)", "quoted"),
    ]

    # Semantic similarity threshold for verification
    SIMILARITY_THRESHOLD = 0.75
    # Confidence threshold for hallucination detection
    HALLUCINATION_THRESHOLD = 0.3

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        hallucination_threshold: float = HALLUCINATION_THRESHOLD,
    ) -> None:
        """Initialize the reference validator.

        Args:
            knowledge_graph: Knowledge graph for fact verification
            similarity_threshold: Threshold for semantic similarity (0.0-1.0)
            hallucination_threshold: Threshold below which is considered hallucination (0.0-1.0)
        """
        self.knowledge_graph = knowledge_graph
        settings = get_settings()
        self.vector_store = VectorStoreFactory.get_vector_store(
            settings.vector_store_type,
            persist_path=settings.chroma_persist_path,
            collection_name=settings.chroma_collection_name,
        )
        self.similarity_threshold = similarity_threshold
        self.hallucination_threshold = hallucination_threshold

        logger.info(
            f"ReferenceValidator initialized with similarity_threshold={similarity_threshold}, "
            f"hallucination_threshold={hallucination_threshold}"
        )

    def extract_references(self, chapter_content: str, chapter_num: int) -> list[Reference]:
        """Extract all references from chapter content.

        Uses regex patterns to find statements like:
        - "林晚说过天下大势，分久必合"
        - "据他回忆，那是个寒冷的夜晚"
        - "正如丞相所言，危机四伏"

        Args:
            chapter_content: Full text of the chapter
            chapter_num: Chapter number being processed

        Returns:
            List of extracted Reference objects
        """
        references = []

        for pattern, action_type in self.REFERENCE_PATTERNS:
            matches = re.finditer(pattern, chapter_content)

            for match in matches:
                try:
                    ref = self._parse_reference_match(
                        match, action_type, chapter_num, chapter_content
                    )
                    if ref:
                        references.append(ref)
                except Exception as e:
                    logger.warning(f"Failed to parse reference match: {e}")
                    continue

        logger.info(f"Extracted {len(references)} references from chapter {chapter_num}")
        return references

    def _parse_reference_match(
        self,
        match: re.Match,
        action_type: str,
        chapter_num: int,
        chapter_content: str,
    ) -> Reference | None:
        """Parse a regex match into a Reference object.

        Args:
            match: Regex match object
            action_type: Type of reference action
            chapter_num: Chapter number
            chapter_content: Full chapter content for context

        Returns:
            Reference object or None if parsing fails
        """
        groups = match.groups()

        # Different patterns have different group structures
        if action_type == "说过":
            # Pattern: A说过"B"
            speaker = groups[0].strip()
            content = groups[1].strip()
            referenced_character = speaker
            referenced_action = "说过"
        elif action_type == "mentioned":
            # Pattern: A曾(提到|说|讲)B
            speaker = groups[0].strip()
            referenced_action = groups[1].strip()
            content = groups[2].strip()
            referenced_character = speaker
        elif action_type == "recalled":
            # Pattern: 据A(回忆|记得)B
            speaker = groups[0].strip()
            referenced_action = groups[1].strip()
            content = groups[2].strip()
            referenced_character = speaker
        elif action_type == "quoted":
            # Pattern: 正如A(所言|所说)B
            referenced_character = groups[0].strip()
            referenced_action = groups[1].strip()
            content = groups[2].strip()
            speaker = "narrator"  # Narrator is quoting
        else:
            return None

        # Extract full sentence for context
        start_pos = match.start()
        end_pos = match.end()

        # Find sentence boundaries
        sentence_start = chapter_content.rfind("。", 0, start_pos) + 1
        sentence_end = chapter_content.find("。", end_pos)
        if sentence_end == -1:
            sentence_end = len(chapter_content)

        full_text = chapter_content[sentence_start:sentence_end].strip()

        # Calculate confidence based on extraction quality
        confidence = self._calculate_extraction_confidence(speaker, referenced_character, content)

        return Reference(
            text=full_text,
            speaker=speaker,
            referenced_character=referenced_character,
            referenced_action=referenced_action,
            referenced_content=content,
            chapter=chapter_num,
            confidence=confidence,
        )

    def _calculate_extraction_confidence(
        self, speaker: str, referenced_character: str, content: str
    ) -> float:
        """Calculate confidence score for extraction quality.

        Args:
            speaker: Who is making the reference
            referenced_character: Who is being referenced
            content: The referenced content

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.5  # Base confidence

        # Boost confidence if speaker is a known character
        speaker_node = self.knowledge_graph.get_entity_by_name(speaker)
        if speaker_node:
            confidence += 0.2

        # Boost confidence if referenced character is known
        ref_node = self.knowledge_graph.get_entity_by_name(referenced_character)
        if ref_node:
            confidence += 0.2

        # Reduce confidence for very short content (likely false positive)
        if len(content) < 5:
            confidence -= 0.3

        # Boost confidence for substantive content
        if len(content) > 10:
            confidence += 0.1

        return max(0.0, min(1.0, confidence))

    async def verify_reference(self, ref: Reference) -> ReferenceVerification:
        """Verify a reference against knowledge graph and vector store.

        Checks:
        1. Does the referenced character exist?
        2. Is there evidence in the knowledge graph?
        3. Are there similar facts in the vector store?

        Args:
            ref: Reference to verify

        Returns:
            ReferenceVerification with results
        """
        evidence = []
        issues = []
        similar_facts = []

        # Check 1: Does referenced character exist?
        character_node = self.knowledge_graph.get_entity_by_name(ref.referenced_character)
        if not character_node:
            issues.append(
                f"Referenced character '{ref.referenced_character}' not found in knowledge graph"
            )

        # Check 2: Search knowledge graph for events involving this character
        kg_evidence = self._search_knowledge_graph(ref)
        evidence.extend(kg_evidence)

        # Check 3: Semantic similarity search in vector store
        if self.vector_store:
            similar_facts = await self._search_vector_store(ref)
            if similar_facts:
                evidence.append(f"Found {len(similar_facts)} similar facts in vector store")

        # Calculate verification confidence
        verification_confidence = self._calculate_verification_confidence(
            character_node is not None,
            len(kg_evidence) > 0,
            similar_facts,
            ref.confidence,
        )

        # Determine if reference is valid
        is_valid = verification_confidence >= self.similarity_threshold and len(issues) == 0

        # Flag as hallucination if confidence is very low or equal to threshold
        if verification_confidence <= self.hallucination_threshold:
            issues.append(
                f"Potential hallucination: No supporting evidence found (confidence: {verification_confidence:.2f})"
            )

        return ReferenceVerification(
            reference=ref,
            is_valid=is_valid,
            confidence=verification_confidence,
            evidence=evidence,
            issues=issues,
            similar_facts=similar_facts,
        )

    def _search_knowledge_graph(self, ref: Reference) -> list[str]:
        """Search knowledge graph for evidence supporting the reference.

        Args:
            ref: Reference to search for

        Returns:
            List of evidence strings
        """
        evidence = []

        # Search for nodes related to the referenced character
        character_node = self.knowledge_graph.get_entity_by_name(ref.referenced_character)

        if character_node:
            # Get timeline events for this character
            timeline = self.knowledge_graph.get_entity_timeline(character_node.node_id)

            # Check if referenced content appears in any events
            ref_content_lower = ref.referenced_content.lower()
            for event in timeline:
                event_desc = event.get("description", "").lower()
                if ref_content_lower in event_desc or any(
                    keyword in event_desc for keyword in ref_content_lower.split()[:5]
                ):
                    evidence.append(
                        f"Knowledge graph event (Chapter {event['chapter']}): {event['description']}"
                    )

            # Get relationships that might support the reference
            related_entities = self.knowledge_graph.query_related_entities(
                character_node.node_id, max_depth=1
            )

            for entity in related_entities[:5]:  # Limit to top 5
                entity_name = entity.properties.get("name", "")
                if entity_name and entity_name in ref.text:
                    evidence.append(f"Related entity found: {entity_name} ({entity.node_type})")

        return evidence

    async def _search_vector_store(self, ref: Reference) -> list[dict[str, Any]]:
        """Search vector store for semantically similar facts.

        Args:
            ref: Reference to search for

        Returns:
            List of similar facts with similarity scores
        """
        if not self.vector_store:
            return []

        try:
            # Search for similar content
            results = await self.vector_store.query_similar(
                query_text=ref.referenced_content, top_k=5, include_metadata=True
            )

            # Filter results by similarity threshold
            similar_facts = []
            for result in results:
                if result.score >= self.similarity_threshold:
                    similar_facts.append(
                        {
                            "id": result.id,
                            "score": result.score,
                            "text": result.metadata.get("text", ""),
                            "metadata": result.metadata,
                        }
                    )

            return similar_facts

        except Exception as e:
            logger.error(f"Vector store search failed: {e}")
            return []

    def _calculate_verification_confidence(
        self,
        character_exists: bool,
        has_kg_evidence: bool,
        similar_facts: list[dict[str, Any]],
        extraction_confidence: float,
    ) -> float:
        """Calculate overall verification confidence.

        Args:
            character_exists: Whether referenced character exists
            has_kg_evidence: Whether knowledge graph has supporting evidence
            similar_facts: List of similar facts from vector store
            extraction_confidence: Confidence of the extraction itself

        Returns:
            Verification confidence score (0.0-1.0)
        """
        confidence = 0.0

        # Character existence check (20%)
        if character_exists:
            confidence += 0.2

        # Knowledge graph evidence (30%)
        if has_kg_evidence:
            confidence += 0.3

        # Vector store similarity (40%)
        if similar_facts:
            # Weight by best similarity score
            best_score = max(fact["score"] for fact in similar_facts)
            confidence += 0.4 * best_score

        # Extraction confidence (10%)
        confidence += 0.1 * extraction_confidence

        return min(1.0, confidence)

    async def validate_chapter_references(
        self, chapter_content: str, chapter_num: int
    ) -> list[ReferenceVerification]:
        """Extract and validate all references in a chapter.

        This is the main entry point for reference validation.

        Args:
            chapter_content: Full text of the chapter
            chapter_num: Chapter number being validated

        Returns:
            List of ReferenceVerification results for all references found
        """
        # Extract all references
        references = self.extract_references(chapter_content, chapter_num)

        # Verify each reference
        verifications = []
        for ref in references:
            verification = await self.verify_reference(ref)
            verifications.append(verification)

            # Log issues found
            if verification.issues:
                logger.warning(
                    f"Reference validation issue in chapter {chapter_num}: {verification.issues[0]}"
                )

        # Summary logging
        total_refs = len(verifications)
        valid_refs = sum(1 for v in verifications if v.is_valid)
        hallucinated_refs = sum(
            1 for v in verifications if v.confidence < self.hallucination_threshold
        )

        logger.info(
            f"Chapter {chapter_num} reference validation: "
            f"{valid_refs}/{total_refs} valid, {hallucinated_refs} potential hallucinations"
        )

        return verifications

    def get_validation_report(self, verifications: list[ReferenceVerification]) -> dict[str, Any]:
        """Generate a summary report of reference validations.

        Args:
            verifications: List of verification results

        Returns:
            Dictionary with validation statistics and issues
        """
        total = len(verifications)
        valid = sum(1 for v in verifications if v.is_valid)
        hallucinated = sum(1 for v in verifications if v.confidence < self.hallucination_threshold)

        issues_by_type: dict[str, int] = {}
        for v in verifications:
            for issue in v.issues:
                issue_type = issue.split(":")[0]
                issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1

        return {
            "total_references": total,
            "valid_references": valid,
            "invalid_references": total - valid,
            "potential_hallucinations": hallucinated,
            "accuracy": valid / total if total > 0 else 1.0,
            "issues_by_type": issues_by_type,
            "low_confidence_references": [
                {
                    "text": v.reference.text,
                    "confidence": v.confidence,
                    "issues": v.issues,
                }
                for v in verifications
                if v.confidence < self.similarity_threshold
            ],
        }

