"""NLP utilities with optional spaCy support.

This module provides NLP functionality with graceful degradation when spaCy
is not installed. It supports named entity recognition, noun phrase extraction,
and other text analysis features for the novel writing system.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Try to import spaCy with graceful fallback
try:
    import spacy
    from spacy.tokens import Doc

    SPACY_AVAILABLE = True
    logger.debug("spaCy loaded successfully")
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None  # type: ignore
    Doc = Any  # type: ignore
    logger.debug("spaCy not installed. NLP features will be limited.")

# Model cache
_NLP_MODEL = None
_NLP_MODEL_NAME = None

# Entity type mapping from spaCy to our system
SPACY_TO_CUSTOM_ENTITY = {
    "PERSON": "character",
    "GPE": "location",  # Geopolitical entity
    "LOC": "location",  # Location
    "FAC": "location",  # Facility
    "ORG": "organization",
    "PRODUCT": "item",
    "WORK_OF_ART": "item",  # Could be book, song, etc.
    "EVENT": "event",
}


def get_nlp_model(model_name: str = "en_core_web_sm") -> Any:
    """Get or load spaCy model with caching.

    Args:
        model_name: Name of the spaCy model to load.
                   Options: en_core_web_sm (12MB), en_core_web_md (48MB),
                           en_core_web_lg (560MB), en_core_web_trf (438MB)

    Returns:
        Loaded spaCy nlp model

    Raises:
        RuntimeError: If spaCy is not installed
        OSError: If model download fails
    """
    global _NLP_MODEL, _NLP_MODEL_NAME

    if not SPACY_AVAILABLE:
        raise RuntimeError(
            "spaCy not installed. Install with: pip install spacy && "
            f"python -m spacy download {model_name}"
        )

    # Return cached model if name matches
    if _NLP_MODEL is not None and _NLP_MODEL_NAME == model_name:
        return _NLP_MODEL

    try:
        logger.info(f"Loading spaCy model: {model_name}")
        _NLP_MODEL = spacy.load(model_name)
        _NLP_MODEL_NAME = model_name
        return _NLP_MODEL
    except OSError:
        logger.warning(f"Model {model_name} not found. Attempting download...")
        import subprocess
        import sys

        try:
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", model_name],
                check=True,
                capture_output=True,
            )
            _NLP_MODEL = spacy.load(model_name)
            _NLP_MODEL_NAME = model_name
            logger.info(f"Successfully loaded {model_name}")
            return _NLP_MODEL
        except subprocess.CalledProcessError as e:
            raise OSError(
                f"Failed to download spaCy model {model_name}. "
                f"Install manually: python -m spacy download {model_name}"
            ) from e


class EntityExtractor:
    """Extract entities from text using spaCy or fallback to regex.

    This class provides named entity recognition with graceful degradation.
    When spaCy is available, it uses the NER model. Otherwise, it falls back
    to regex-based extraction.
    """

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        """Initialize the entity extractor.

        Args:
            model_name: spaCy model to use (only used if spaCy is available)
        """
        self._model_name = model_name
        self._nlp = None
        self._available = SPACY_AVAILABLE

    @property
    def available(self) -> bool:
        """Check if spaCy-based extraction is available."""
        return self._available

    def _get_nlp(self) -> Any:
        """Lazy load the NLP model."""
        if self._nlp is None and self._available:
            self._nlp = get_nlp_model(self._model_name)
        return self._nlp

    def extract_entities(
        self, text: str, entity_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Extract entities from text.

        Args:
            text: Input text to analyze
            entity_types: Optional list of entity types to filter by.
                         Types: "character", "location", "item", "organization", "event"

        Returns:
            List of entity dictionaries with keys:
            - text: The entity text
            - type: Entity type (mapped to our system)
            - start: Start character position
            - end: End character position
            - source: "spacy" or "fallback"
        """
        if self._available:
            return self._extract_with_spacy(text, entity_types)
        else:
            return self._extract_with_fallback(text, entity_types)

    def _extract_with_spacy(
        self, text: str, entity_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Extract entities using spaCy NER."""
        nlp = self._get_nlp()
        doc = nlp(text)

        entities = []
        for ent in doc.ents:
            # Map spaCy entity type to our system
            custom_type = SPACY_TO_CUSTOM_ENTITY.get(ent.label_, "other")

            # Filter by requested types
            if entity_types and custom_type not in entity_types:
                continue

            entities.append(
                {
                    "text": ent.text,
                    "type": custom_type,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "spacy_label": ent.label_,
                    "source": "spacy",
                }
            )

        return entities

    def _extract_with_fallback(
        self, text: str, entity_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Fallback regex-based entity extraction.

        This is a simplified version that catches obvious proper nouns.
        """
        import re

        entities = []

        # Pattern for capitalized words (potential proper nouns)
        # Matches sequences like "Sir Kael", "Forest of Elders", "Ancient Sword"
        pattern = r"\b([A-Z][a-z]+(?:\s+(?:of|the|and|in|on|at|to|from|by|with)?\s*[A-Z][a-z]+)*)\b"

        # Common words to exclude
        exclude_words = {
            "The",
            "A",
            "An",
            "This",
            "That",
            "These",
            "Those",
            "He",
            "She",
            "It",
            "They",
            "We",
            "You",
            "I",
            "His",
            "Her",
            "Its",
            "Their",
            "My",
            "Your",
            "Our",
        }

        for match in re.finditer(pattern, text):
            entity_text = match.group(1)

            # Skip if in exclude list
            if entity_text in exclude_words:
                continue

            # Skip if too short
            if len(entity_text) < 3:
                continue

            # Guess entity type based on context and patterns
            guessed_type = self._guess_entity_type(entity_text, text)

            # Filter by requested types
            if entity_types and guessed_type not in entity_types:
                continue

            entities.append(
                {
                    "text": entity_text,
                    "type": guessed_type,
                    "start": match.start(),
                    "end": match.end(),
                    "source": "fallback",
                }
            )

        return entities

    def _guess_entity_type(self, entity_text: str, context: str) -> str:
        """Guess entity type based on patterns and context.

        This is a heuristic-based approach for the fallback mode.
        """
        text_lower = entity_text.lower()
        context_lower = context.lower()

        # Title + Name pattern -> character
        title_pattern = r"\b(Sir|Lady|Lord|King|Queen|Prince|Princess|Duke|Duchess|Captain|Commander|Doctor|Dr|Professor)\s+"
        if re.search(title_pattern + re.escape(entity_text.split()[0]), entity_text, re.IGNORECASE):
            return "character"

        # Location indicators
        location_indicators = [
            "forest",
            "mountain",
            "river",
            "lake",
            "castle",
            "tower",
            "city",
            "town",
            "village",
            "kingdom",
            "empire",
            "realm",
            "hall",
            "room",
            "garden",
            "cave",
            "dungeon",
            "temple",
        ]
        if any(ind in text_lower for ind in location_indicators):
            return "location"

        # Item indicators
        item_indicators = [
            "sword",
            "shield",
            "armor",
            "ring",
            "necklace",
            "amulet",
            "book",
            "scroll",
            "map",
            "key",
            "crystal",
            "gem",
            "stone",
            "potion",
            "weapon",
            "staff",
            "wand",
            "artifact",
        ]
        if any(ind in text_lower for ind in item_indicators):
            return "item"

        # Check surrounding context for clues
        # Find the entity in context
        pos = context_lower.find(text_lower)
        if pos >= 0:
            before = context_lower[max(0, pos - 30) : pos]
            context_lower[pos + len(text_lower) : pos + len(text_lower) + 30]

            # Character context
            if any(word in before for word in ["said", "asked", "replied", "thought", "felt"]):
                return "character"

            # Location context
            if any(word in before for word in ["at", "in", "near", "toward", "from"]):
                return "location"

            # Item context
            if any(word in before for word in ["held", "carried", "wielded", "wore", "used"]):
                return "item"

        # Default to character for capitalized names
        return "character"

    def extract_noun_phrases(self, text: str, max_length: int = 5) -> list[dict[str, Any]]:
        """Extract noun phrases from text.

        Args:
            text: Input text
            max_length: Maximum number of words in a phrase

        Returns:
            List of noun phrase dictionaries
        """
        if not self._available:
            logger.debug("spaCy not available, skipping noun phrase extraction")
            return []

        nlp = self._get_nlp()
        doc = nlp(text)

        phrases = []
        for chunk in doc.noun_chunks:
            # Filter by length
            word_count = len(chunk.text.split())
            if word_count > max_length:
                continue

            phrases.append(
                {
                    "text": chunk.text,
                    "root": chunk.root.text,
                    "root_pos": chunk.root.pos_,
                    "start": chunk.start_char,
                    "end": chunk.end_char,
                }
            )

        return phrases


class NLPProcessor:
    """Main NLP processor providing various text analysis features.

    This is a high-level interface that aggregates various NLP capabilities
    with graceful degradation when spaCy is not available.
    """

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        """Initialize the NLP processor.

        Args:
            model_name: spaCy model to use
        """
        self.entity_extractor = EntityExtractor(model_name)
        self._available = SPACY_AVAILABLE

    @property
    def available(self) -> bool:
        """Check if full NLP features are available."""
        return self._available

    def analyze_text(self, text: str) -> dict[str, Any]:
        """Perform comprehensive text analysis.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary containing:
            - entities: List of extracted entities
            - noun_phrases: List of noun phrases (if spaCy available)
            - sentence_count: Number of sentences (if spaCy available)
            - word_count: Number of words
            - available: Whether spaCy was used
        """
        result = {
            "available": self._available,
            "word_count": len(text.split()),
        }

        # Extract entities (works with or without spaCy)
        result["entities"] = self.entity_extractor.extract_entities(text)

        # spaCy-specific features
        if self._available:
            nlp = self.entity_extractor._get_nlp()
            doc = nlp(text)

            result["sentence_count"] = len(list(doc.sents))
            result["noun_phrases"] = self.entity_extractor.extract_noun_phrases(text)

            # POS distribution
            pos_counts = {}
            for token in doc:
                pos_counts[token.pos_] = pos_counts.get(token.pos_, 0) + 1
            result["pos_distribution"] = pos_counts
        else:
            result["sentence_count"] = text.count(".") + text.count("!") + text.count("?")
            result["noun_phrases"] = []
            result["nlp_skipped"] = "spaCy not installed"

        return result

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the loaded spaCy model.

        Returns:
            Dictionary with model information or empty if spaCy not available
        """
        if not self._available:
            return {"available": False}

        try:
            nlp = self.entity_extractor._get_nlp()
            return {
                "available": True,
                "model_name": nlp.meta.get("name", "unknown"),
                "version": nlp.meta.get("version", "unknown"),
                "language": nlp.meta.get("lang", "unknown"),
                "pipeline": nlp.pipe_names,
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# Convenience function for quick entity extraction
def extract_entities(text: str, entity_types: list[str] | None = None) -> list[dict[str, Any]]:
    """Quick entity extraction function.

    This is a convenience function that creates a temporary EntityExtractor
    and extracts entities. For repeated use, create an EntityExtractor instance.

    Args:
        text: Text to analyze
        entity_types: Optional list of entity types to filter

    Returns:
        List of extracted entities
    """
    extractor = EntityExtractor()
    return extractor.extract_entities(text, entity_types)


def quick_analyze(text: str) -> dict[str, Any]:
    """Quick text analysis function.

    Args:
        text: Text to analyze

    Returns:
        Analysis results dictionary
    """
    processor = NLPProcessor()
    return processor.analyze_text(text)
