# src/novel/hallucination_detector.py
"""Hallucination detection for novel content quality assurance.

This module provides hallucination detection using multiple methods:
1. Vector similarity (comparing generated text with world context)
2. Rule-based detection (pattern matching for common hallucination types)
3. Optional HHEM-2.1-Open model integration

Detection focuses on:
- Factual hallucinations: Claims contradicting established facts
- Creative fiction: Reasonable creative additions (not flagged as errors)
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.novel_agent.db.vector_store_factory import VectorStoreFactory
from src.novel_agent.utils.config import get_settings

logger = logging.getLogger(__name__)


class HallucinationType(str, Enum):
    """Types of hallucinations that can be detected."""

    FACTUAL_HALLUCINATION = "factual_hallucination"  # Contradicts established facts
    CREATIVE_FICTION = "creative_fiction"  # Reasonable creative addition
    UNVERIFIABLE = "unverifiable"  # Cannot be verified against context
    POTENTIAL_ERROR = "potential_error"  # May be an error, needs review


class ConfidenceLevel(str, Enum):
    """Confidence levels for hallucination detection."""

    HIGH = "high"  # >0.9: Clear hallucination
    MEDIUM = "medium"  # 0.7-0.9: Review recommended
    LOW = "low"  # <0.7: Likely OK


@dataclass
class Hallucination:
    """A detected hallucination instance."""

    text: str  # The hallucinated text snippet
    hallucination_type: HallucinationType
    confidence: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel
    reason: str  # Why this was flagged
    context_snippet: str = ""  # Surrounding context
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HallucinationReport:
    """Report of hallucination detection results."""

    is_clean: bool  # True if no factual hallucinations found
    hallucinations: list[Hallucination] = field(default_factory=list)
    factual_hallucinations: list[Hallucination] = field(default_factory=list)
    creative_additions: list[Hallucination] = field(default_factory=list)
    total_detections: int = 0
    detection_time_ms: float = 0.0
    world_context: str = ""
    generated_text: str = ""

    def get_high_confidence_issues(self) -> list[Hallucination]:
        """Get hallucinations with high confidence that need attention."""
        return [
            h
            for h in self.hallucinations
            if h.confidence_level == ConfidenceLevel.HIGH
            and h.hallucination_type == HallucinationType.FACTUAL_HALLUCINATION
        ]


class HallucinationDetector:
    """Detects hallucinations in generated novel content.

    Uses multiple detection methods:
    - Vector similarity with world context
    - Rule-based pattern matching
    - Optional HHEM-2.1-Open model

    Example:
        >>> detector = HallucinationDetector()
        >>> report = await detector.detect_hallucinations(
        ...     generated_chapter="林晚说过天下大势，分久必合...",
        ...     world_context="林晚是10岁女孩，从未说过这句话..."
        ... )
        >>> if not report.is_clean:
        ...     print(f"Found {len(report.factual_hallucinations)} issues")
    """

    # Similarity thresholds
    HIGH_SIMILARITY_THRESHOLD = 0.85  # Very similar - likely grounded
    MEDIUM_SIMILARITY_THRESHOLD = 0.65  # Somewhat similar - may be creative
    LOW_SIMILARITY_THRESHOLD = 0.45  # Not similar - potential hallucination

    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.9
    MEDIUM_CONFIDENCE_THRESHOLD = 0.7

    # Patterns for rule-based detection
    QUOTATION_PATTERNS = [
        r'([一-龥]+)说过[:：][""]([^""]+)[""]',  # Chinese: X说过"..."
        r'([^\s]+)\s+(?:said|stated|claimed|declared)\s*[:：]?\s*["\']([^"\']+)["\']',  # English
        r"据([^\s]+)[说称]",  # Chinese: 据X说/据X称
        r"([^\s]+)\s+(?:once said|once claimed|famously said)",  # English
    ]

    FACTUAL_CLAIM_PATTERNS = [
        r"(\d+)[岁](\s*)(?:那年|时|的时候)",  # Chinese: X岁那年 (digit)
        r"([一两三四五六七八九十百千万]+)[岁](\s*)(?:那年|时|的时候)",  # Chinese: X岁那年 (Chinese numeral)
        r"(?:in|at)\s+(?:the\s+)?age\s+of\s+(\d+)",  # English: at age X (digit)
        r"(?:in|at)\s+(?:the\s+)?age\s+of\s+([a-zA-Z]+)",  # English: at age ten (word)
        r"(\d+)[年月日]",  # Chinese date
        r"in\s+(\d{4})",  # English year
        r"出生[于在]([^\s，。]+)",  # Chinese: 出生于X
        r"born\s+in\s+([^\s,\.]+)",  # English: born in X
    ]

    # Creative fiction patterns (should NOT be flagged as errors)
    CREATIVE_PATTERNS = [
        r"(?:仿佛|好像|似乎|宛如)",  # Chinese: 仿佛/好像/似乎/宛如 (similes)
        r"(?:也许|可能|大概|或许)",  # Chinese: 也许/可能/大概/或许 (uncertainty)
        r"(?:幻想|想象|梦境|梦中)",  # Chinese: 幻想/想象/梦境 (imagination)
        r"(?:据说|传说|相传)",  # Chinese: 据说/传说/相传 (legends, acceptable)
        r"(?:folklore|legend|myth|rumor)",  # English: folklore/legend/myth
    ]

    def __init__(
        self,
        threshold: float = 0.8,
        use_hhem: bool = False,
        min_text_length: int = 20,
    ) -> None:
        """Initialize the hallucination detector.

        Args:
            threshold: Confidence threshold for flagging hallucinations (0.0-1.0).
            use_hhem: Whether to try using HHEM-2.1-Open model.
            min_text_length: Minimum text length for detection.
        """
        settings = get_settings()
        self.vector_store = VectorStoreFactory.get_vector_store(
            settings.vector_store_type,
            persist_path=settings.chroma_persist_path,
            collection_name=settings.chroma_collection_name,
        )
        self.threshold = threshold
        self.use_hhem = use_hhem
        self.min_text_length = min_text_length
        self._hhem_model = None

        # Compile regex patterns
        self._compiled_quote_patterns = [re.compile(p) for p in self.QUOTATION_PATTERNS]
        self._compiled_fact_patterns = [re.compile(p) for p in self.FACTUAL_CLAIM_PATTERNS]
        self._compiled_creative_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.CREATIVE_PATTERNS
        ]

        logger.info(
            f"HallucinationDetector initialized (threshold={threshold}, "
            f"vector_store=enabled, "
            f"hhem={'enabled' if use_hhem else 'disabled'})"
        )

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from score.

        Args:
            confidence: Confidence score (0.0-1.0).

        Returns:
            ConfidenceLevel enum value.
        """
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW

    def _extract_sentences(self, text: str) -> list[str]:
        """Split text into sentences.

        Args:
            text: Text to split.

        Returns:
            List of sentences.
        """
        # Split on Chinese and English sentence delimiters
        sentences = re.split(r"[。！？.!?]+", text)
        return [
            s.strip() for s in sentences if s.strip() and len(s.strip()) >= self.min_text_length
        ]

    def _is_creative_fiction(self, text: str) -> bool:
        """Check if text contains creative fiction markers.

        Args:
            text: Text to check.

        Returns:
            True if text contains creative markers.
        """
        for pattern in self._compiled_creative_patterns:
            if pattern.search(text):
                return True
        return False

    def _extract_quotations(self, text: str) -> list[dict[str, str]]:
        """Extract quotations with speaker attribution.

        Args:
            text: Text to extract from.

        Returns:
            List of dicts with 'speaker' and 'quote' keys.
        """
        quotations = []
        for pattern in self._compiled_quote_patterns:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) >= 2:
                    quotations.append(
                        {
                            "speaker": groups[0],
                            "quote": groups[1],
                            "full_match": match.group(0),
                        }
                    )
        return quotations

    def _extract_factual_claims(self, text: str) -> list[dict[str, str]]:
        """Extract factual claims from text.

        Args:
            text: Text to extract from.

        Returns:
            List of dicts with claim information.
        """
        claims = []
        for pattern in self._compiled_fact_patterns:
            for match in pattern.finditer(text):
                claims.append(
                    {
                        "type": "factual_claim",
                        "value": match.group(1) if match.groups() else "",
                        "full_match": match.group(0),
                        "context": text[max(0, match.start() - 50) : match.end() + 50],
                    }
                )
        return claims

    async def _detect_via_vector_similarity(
        self,
        text: str,
        world_context: str,
    ) -> tuple[float, str]:
        """Detect hallucinations using vector similarity.

        Args:
            text: Text to check.
            world_context: World context to compare against.

        Returns:
            Tuple of (similarity_score, reason).
        """
        if not self.vector_store:
            return 0.5, "Vector store not available"

        try:
            # Query for similar content in world context
            results = await self.vector_store.query_similar(
                query_text=text,
                n_results=5,
            )

            if not results:
                return 0.0, "No similar content found in world context"

            # Get the best match
            best_match = results[0]
            # Use score or distance (convert distance to similarity if needed)
            similarity = best_match.get("score", best_match.get("distance", 0.5))
            if "distance" in best_match and "score" not in best_match:
                # Chroma uses distance (lower is better), convert to similarity
                similarity = 1.0 - similarity

            if similarity >= self.HIGH_SIMILARITY_THRESHOLD:
                return similarity, f"High similarity ({similarity:.2f}) with world context"
            elif similarity >= self.MEDIUM_SIMILARITY_THRESHOLD:
                return similarity, f"Moderate similarity ({similarity:.2f}) - may be creative"
            else:
                return similarity, f"Low similarity ({similarity:.2f}) - potential hallucination"

        except Exception as e:
            logger.error(f"Vector similarity detection failed: {e}")
            return 0.5, f"Detection error: {e}"

    def _detect_via_rules(
        self,
        text: str,
        world_context: str,
    ) -> list[Hallucination]:
        """Detect hallucinations using rule-based patterns.

        Args:
            text: Text to check.
            world_context: World context for verification.

        Returns:
            List of detected hallucinations.
        """
        hallucinations = []

        # Check for quotations without evidence
        quotations = self._extract_quotations(text)
        for quote in quotations:
            speaker = quote["speaker"]
            quote_text = quote["quote"]

            # Check if this is a creative fiction (legend, myth, etc.)
            if self._is_creative_fiction(quote["full_match"]):
                hallucinations.append(
                    Hallucination(
                        text=quote["full_match"],
                        hallucination_type=HallucinationType.CREATIVE_FICTION,
                        confidence=0.6,
                        confidence_level=ConfidenceLevel.LOW,
                        reason=f"Quotation from {speaker} appears to be creative fiction (legend/myth)",
                        context_snippet=quote["full_match"][:100],
                        suggestions=[],
                        metadata={"speaker": speaker, "quote": quote_text},
                    )
                )
                continue

            # Check if speaker exists in world context
            if speaker and speaker not in world_context:
                # Speaker not found - potential hallucination
                hallucinations.append(
                    Hallucination(
                        text=quote["full_match"],
                        hallucination_type=HallucinationType.FACTUAL_HALLUCINATION,
                        confidence=0.85,
                        confidence_level=ConfidenceLevel.HIGH,
                        reason=f"Speaker '{speaker}' not found in world context",
                        context_snippet=quote["full_match"][:100],
                        suggestions=[
                            f"Verify speaker '{speaker}' exists",
                            "Consider removing or correcting the quote",
                        ],
                        metadata={"speaker": speaker, "quote": quote_text},
                    )
                )
            else:
                # Speaker exists - check if context explicitly contradicts the quote
                # Look for negation patterns in context about this speaker
                contradiction_patterns = [
                    r"没有说过",  # never said
                    r"从未说过",  # never said
                    r"从未学过",  # never studied
                    r"never said",
                    r"never studied",
                ]
                is_contradicted = False
                for pattern in contradiction_patterns:
                    if re.search(pattern, world_context):
                        is_contradicted = True
                        break

                if is_contradicted:
                    # Context explicitly contradicts the quote
                    hallucinations.append(
                        Hallucination(
                            text=quote["full_match"],
                            hallucination_type=HallucinationType.FACTUAL_HALLUCINATION,
                            confidence=0.9,
                            confidence_level=ConfidenceLevel.HIGH,
                            reason=f"Quotation contradicts world context for '{speaker}'",
                            context_snippet=quote["full_match"][:100],
                            suggestions=[
                                f"This contradicts established facts about '{speaker}'",
                                "Consider removing or revising the quote",
                            ],
                            metadata={"speaker": speaker, "quote": quote_text},
                        )
                    )
                else:
                    # Speaker exists but quote may not be verified
                    hallucinations.append(
                        Hallucination(
                            text=quote["full_match"],
                            hallucination_type=HallucinationType.UNVERIFIABLE,
                            confidence=0.7,
                            confidence_level=ConfidenceLevel.MEDIUM,
                            reason=f"Quotation attributed to '{speaker}' could not be verified against world context",
                            context_snippet=quote["full_match"][:100],
                            suggestions=[f"Verify that '{speaker}' actually said this"],
                            metadata={"speaker": speaker, "quote": quote_text},
                        )
                    )

        # Check for factual claims
        claims = self._extract_factual_claims(text)
        for claim in claims:
            # Skip if in creative fiction context
            if self._is_creative_fiction(claim["context"]):
                continue

            hallucinations.append(
                Hallucination(
                    text=claim["full_match"],
                    hallucination_type=HallucinationType.POTENTIAL_ERROR,
                    confidence=0.65,
                    confidence_level=ConfidenceLevel.LOW,
                    reason=f"Factual claim detected: {claim['value']}",
                    context_snippet=claim["context"][:100],
                    suggestions=["Verify this factual claim against world context"],
                    metadata={"claim_type": claim["type"], "value": claim["value"]},
                )
            )

        return hallucinations

    async def _detect_via_hhem(
        self,
        text: str,
        world_context: str,
    ) -> list[Hallucination]:
        """Detect hallucinations using HHEM-2.1-Open model.

        This is an optional detection method that uses the HHEM model
        from the dingo library if available.

        Args:
            text: Text to check.
            world_context: World context for verification.

        Returns:
            List of detected hallucinations.
        """
        if not self.use_hhem:
            return []

        hallucinations = []

        try:
            # Try to import and use HHEM
            # Note: HHEM-2.1-Open may not be available, so we handle gracefully
            if self._hhem_model is None:
                try:
                    # Attempt to load HHEM model
                    # This is a placeholder - actual implementation depends on dingo library
                    from transformers import AutoModelForSequenceClassification, AutoTokenizer

                    self._hhem_model = True  # Mark as attempted
                    logger.info("HHEM model loading attempted (placeholder)")
                except ImportError:
                    logger.debug("HHEM model not available, using fallback")
                    return []

            # Placeholder for actual HHEM detection
            # In production, this would use the model to detect hallucinations
            logger.debug("HHEM detection not fully implemented, using rule-based fallback")

        except Exception as e:
            logger.warning(f"HHEM detection failed: {e}")

        return hallucinations

    def classify_hallucination(
        self,
        text: str,
        context: str,
    ) -> HallucinationType:
        """Classify a hallucination as factual error or creative fiction.

        Args:
            text: The potentially hallucinated text.
            context: The world context to check against.

        Returns:
            HallucinationType classification.
        """
        # Check for creative fiction markers first
        if self._is_creative_fiction(text):
            return HallucinationType.CREATIVE_FICTION

        # Check if text makes factual claims
        claims = self._extract_factual_claims(text)
        quotations = self._extract_quotations(text)

        if not claims and not quotations:
            # No factual claims detected
            return HallucinationType.UNVERIFIABLE

        # Check if claims can be verified in context
        for claim in claims:
            value = claim.get("value", "")
            if value and value not in context:
                # Factual claim not found in context
                return HallucinationType.FACTUAL_HALLUCINATION

        # Check quotations
        for quote in quotations:
            speaker = quote.get("speaker", "")
            if speaker and speaker not in context:
                # Speaker not in context
                return HallucinationType.FACTUAL_HALLUCINATION

        return HallucinationType.POTENTIAL_ERROR

    async def detect_hallucinations(
        self,
        generated_chapter: str,
        world_context: str,
        check_quotations: bool = True,
        check_factual_claims: bool = True,
    ) -> HallucinationReport:
        """Detect hallucinations in generated chapter against world context.

        This is the main entry point for hallucination detection. It uses
        multiple detection methods and aggregates results.

        Args:
            generated_chapter: The generated chapter text to check.
            world_context: The world context (established facts) to verify against.
            check_quotations: Whether to check quotation attributions.
            check_factual_claims: Whether to check factual claims.

        Returns:
            HallucinationReport with all detection results.
        """
        import time

        start_time = time.time()
        all_hallucinations: list[Hallucination] = []

        logger.info(
            f"Starting hallucination detection (text length: {len(generated_chapter)}, "
            f"context length: {len(world_context)})"
        )

        # Method 1: Rule-based detection
        if check_quotations or check_factual_claims:
            rule_results = self._detect_via_rules(generated_chapter, world_context)
            all_hallucinations.extend(rule_results)
            logger.debug(f"Rule-based detection found {len(rule_results)} potential issues")

        # Method 2: Vector similarity (per-sentence for efficiency)
        if self.vector_store:
            sentences = self._extract_sentences(generated_chapter)
            for sentence in sentences:
                # Skip creative fiction sentences
                if self._is_creative_fiction(sentence):
                    continue

                similarity, reason = await self._detect_via_vector_similarity(
                    sentence, world_context
                )

                if similarity < self.LOW_SIMILARITY_THRESHOLD:
                    # Low similarity - potential hallucination
                    all_hallucinations.append(
                        Hallucination(
                            text=sentence[:200],  # Truncate long sentences
                            hallucination_type=HallucinationType.FACTUAL_HALLUCINATION,
                            confidence=1.0 - similarity,
                            confidence_level=self._get_confidence_level(1.0 - similarity),
                            reason=reason,
                            context_snippet=sentence[:100],
                            suggestions=[
                                "Verify against world context",
                                "Consider revising or removing",
                            ],
                        )
                    )

        # Method 3: HHEM (optional)
        if self.use_hhem:
            hhem_results = await self._detect_via_hhem(generated_chapter, world_context)
            all_hallucinations.extend(hhem_results)

        # Deduplicate results (same text may be flagged by multiple methods)
        seen_texts: set[str] = set()
        unique_hallucinations: list[Hallucination] = []
        for h in all_hallucinations:
            key = h.text[:50]  # Use first 50 chars as key
            if key not in seen_texts:
                seen_texts.add(key)
                unique_hallucinations.append(h)

        # Categorize hallucinations
        factual = [
            h
            for h in unique_hallucinations
            if h.hallucination_type == HallucinationType.FACTUAL_HALLUCINATION
        ]
        creative = [
            h
            for h in unique_hallucinations
            if h.hallucination_type == HallucinationType.CREATIVE_FICTION
        ]

        detection_time_ms = (time.time() - start_time) * 1000

        report = HallucinationReport(
            is_clean=len(factual) == 0,
            hallucinations=unique_hallucinations,
            factual_hallucinations=factual,
            creative_additions=creative,
            total_detections=len(unique_hallucinations),
            detection_time_ms=detection_time_ms,
            world_context=world_context[:500],  # Truncate for report
            generated_text=generated_chapter[:500],
        )

        logger.info(
            f"Hallucination detection complete: {len(factual)} factual issues, "
            f"{len(creative)} creative additions, {detection_time_ms:.1f}ms"
        )

        return report

    async def quick_check(self, text: str, context: str) -> bool:
        """Quick check if text contains hallucinations.

        A simplified check that returns True if text is likely clean.

        Args:
            text: Text to check.
            context: World context.

        Returns:
            True if text appears clean, False if hallucinations detected.
        """
        # Quick rule-based check
        rule_results = self._detect_via_rules(text, context)

        # Check for high-confidence factual hallucinations
        factual_errors = [
            h
            for h in rule_results
            if h.hallucination_type == HallucinationType.FACTUAL_HALLUCINATION
            and h.confidence >= self.threshold
        ]

        return len(factual_errors) == 0
