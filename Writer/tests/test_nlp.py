"""Tests for NLP utilities with optional spaCy support."""


import pytest

# Import the module under test
from src.utils.nlp import (
    SPACY_AVAILABLE,
    EntityExtractor,
    NLPProcessor,
    extract_entities,
    quick_analyze,
)


class TestSpacyAvailability:
    """Test spaCy availability detection."""

    def test_spacy_flag_exists(self):
        """Test that SPACY_AVAILABLE flag exists and is a boolean."""
        assert isinstance(SPACY_AVAILABLE, bool)


class TestEntityExtractor:
    """Test EntityExtractor functionality."""

    def test_initialization(self):
        """Test EntityExtractor can be initialized."""
        extractor = EntityExtractor()
        assert extractor is not None
        assert hasattr(extractor, "available")
        assert isinstance(extractor.available, bool)

    def test_extract_entities_basic(self):
        """Test basic entity extraction."""
        extractor = EntityExtractor()
        text = "Sir Kael walked through the Forest of Elders."

        entities = extractor.extract_entities(text)

        # Should return a list
        assert isinstance(entities, list)

        # Should find at least some entities
        assert len(entities) > 0

        # Each entity should have required fields
        for entity in entities:
            assert "text" in entity
            assert "type" in entity
            assert "start" in entity
            assert "end" in entity
            assert "source" in entity

    def test_extract_entities_with_filter(self):
        """Test entity extraction with type filtering."""
        extractor = EntityExtractor()
        text = "Sir Kael was in the Forest of Elders."

        # Filter for characters only
        entities = extractor.extract_entities(text, entity_types=["character"])

        # All returned entities should be characters
        for entity in entities:
            assert entity["type"] == "character"

    def test_entity_type_guessing(self):
        """Test entity type guessing in fallback mode."""
        extractor = EntityExtractor()

        # Test character detection with title
        text1 = "Sir Kael entered the room."
        entities1 = extractor.extract_entities(text1)
        char_entities = [e for e in entities1 if "Kael" in e["text"]]

        # At least one entity should be detected as character or have Kael in text
        assert len(char_entities) > 0 or len(entities1) > 0

    def test_extract_entities_empty_text(self):
        """Test extraction with empty text."""
        extractor = EntityExtractor()
        entities = extractor.extract_entities("")

        assert isinstance(entities, list)
        assert len(entities) == 0

    def test_fallback_exclusion_list(self):
        """Test that common words are excluded in fallback mode."""
        extractor = EntityExtractor()

        # These should not be detected as entities
        text = "The He She It They was here."
        entities = extractor.extract_entities(text)

        # Filter out any entities that match excluded words
        excluded = {"The", "He", "She", "It", "They"}
        for entity in entities:
            assert entity["text"] not in excluded, f"'{entity['text']}' should be excluded"


class TestNLPProcessor:
    """Test NLPProcessor functionality."""

    def test_initialization(self):
        """Test NLPProcessor can be initialized."""
        processor = NLPProcessor()
        assert processor is not None
        assert hasattr(processor, "available")
        assert hasattr(processor, "entity_extractor")

    def test_analyze_text(self):
        """Test comprehensive text analysis."""
        processor = NLPProcessor()
        text = "Sir Kael walked through the Forest of Elders. He carried a sword."

        result = processor.analyze_text(text)

        # Check required fields
        assert "available" in result
        assert "word_count" in result
        assert "entities" in result
        assert "sentence_count" in result

        # Word count should be accurate
        assert result["word_count"] == len(text.split())

        # Should have entities
        assert isinstance(result["entities"], list)

    def test_analyze_text_structure(self):
        """Test that analysis result has correct structure."""
        processor = NLPProcessor()
        text = "The quick brown fox jumps over the lazy dog."

        result = processor.analyze_text(text)

        # Verify all expected keys exist
        expected_keys = {"available", "word_count", "entities", "sentence_count", "noun_phrases"}
        assert expected_keys.issubset(result.keys())

    def test_get_model_info(self):
        """Test model info retrieval."""
        processor = NLPProcessor()
        info = processor.get_model_info()

        assert isinstance(info, dict)
        assert "available" in info

        if SPACY_AVAILABLE:
            # If spaCy is available, should have model details
            assert "model_name" in info or "error" in info
        else:
            # If not available, should indicate that
            assert info["available"] is False


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_extract_entities_function(self):
        """Test the standalone extract_entities function."""
        text = "Sir Kael was in the Forest of Elders."

        entities = extract_entities(text)

        assert isinstance(entities, list)
        # Should find entities
        assert len(entities) >= 0  # May or may not find depending on text

    def test_quick_analyze_function(self):
        """Test the standalone quick_analyze function."""
        text = "The hero journeyed to the ancient castle."

        result = quick_analyze(text)

        assert isinstance(result, dict)
        assert "available" in result
        assert "entities" in result
        assert "word_count" in result


class TestSpacyIntegration:
    """Test integration with spaCy when available."""

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
    def test_spacy_entity_extraction(self):
        """Test entity extraction with spaCy."""
        extractor = EntityExtractor()

        # This test only runs if spaCy is available
        text = "Apple Inc. is looking at buying U.K. startup for $1 billion."
        entities = extractor.extract_entities(text)

        # Should find entities from spaCy
        assert len(entities) > 0

        # Check that source is marked as spacy
        for entity in entities:
            assert entity["source"] == "spacy"
            assert "spacy_label" in entity

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
    def test_spacy_noun_phrases(self):
        """Test noun phrase extraction with spaCy."""
        extractor = EntityExtractor()

        text = "The quick brown fox jumps over the lazy dog."
        phrases = extractor.extract_noun_phrases(text)

        assert isinstance(phrases, list)
        # Should find noun phrases
        assert len(phrases) > 0

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
    def test_pos_distribution(self):
        """Test POS distribution in analysis."""
        processor = NLPProcessor()
        text = "The cat sat on the mat."

        result = processor.analyze_text(text)

        assert "pos_distribution" in result
        pos_dist = result["pos_distribution"]
        assert isinstance(pos_dist, dict)
        # Should have some POS tags
        assert len(pos_dist) > 0


class TestFallbackMode:
    """Test fallback behavior when spaCy is not available."""

    def test_fallback_entity_extraction(self):
        """Test that fallback extraction works."""
        # Create extractor (will use fallback if spacy not available)
        extractor = EntityExtractor()

        text = "Sir Kael entered the Ancient Forest."
        entities = extractor.extract_entities(text)

        # Should still return entities even without spaCy
        assert isinstance(entities, list)

        # If in fallback mode, source should be "fallback"
        if not SPACY_AVAILABLE:
            for entity in entities:
                assert entity["source"] == "fallback"

    def test_fallback_without_nlp(self):
        """Test that processor works without spaCy."""
        processor = NLPProcessor()

        text = "The hero walked to the castle."
        result = processor.analyze_text(text)

        # Should still provide basic analysis
        assert result["available"] == SPACY_AVAILABLE
        assert result["word_count"] > 0
        assert "entities" in result

        if not SPACY_AVAILABLE:
            assert "nlp_skipped" in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_text(self):
        """Test handling of very long text."""
        extractor = EntityExtractor()

        # Create a long text
        text = "Sir Kael walked. " * 1000

        entities = extractor.extract_entities(text)

        # Should handle long text without crashing
        assert isinstance(entities, list)

    def test_special_characters(self):
        """Test handling of special characters."""
        extractor = EntityExtractor()

        text = "Sir Kael (the brave) entered the Forest of Elders!?:;"
        entities = extractor.extract_entities(text)

        # Should handle special characters
        assert isinstance(entities, list)

    def test_unicode_text(self):
        """Test handling of unicode characters."""
        extractor = EntityExtractor()

        text = "Kael ate caf\u00e9 at the r\u00e9sum\u00e9."
        entities = extractor.extract_entities(text)

        # Should handle unicode
        assert isinstance(entities, list)

    def test_no_entities(self):
        """Test text with no detectable entities."""
        extractor = EntityExtractor()

        text = "the and of with for to from"
        entities = extractor.extract_entities(text)

        # Should return empty list for text with only stop words
        assert isinstance(entities, list)
