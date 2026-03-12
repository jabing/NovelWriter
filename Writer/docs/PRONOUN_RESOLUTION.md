# Pronoun Resolution System

This module provides pronoun resolution functionality for the novel writing system. It resolves pronouns (he, she, they, etc.) to specific character names based on context and recent mentions.

## Features

- **Character Extraction**: Automatically extracts character names from text, including those with titles (Sir, Lady, King, Queen, etc.)
- **Gender Inference**: Infers character gender from titles and name patterns
- **Pronoun Resolution**: Resolves pronouns to the most likely character based on:
  - Recency of mention (closer mentions are preferred)
  - Gender matching (he→male, she→female)
  - Number matching (they→plural, singular→singular)
- **Pronoun Replacement**: Can replace pronouns with character names in text

## Usage

### Basic Usage

```python
from src.novel.pronoun_resolver import PronounResolver

# Create a resolver
resolver = PronounResolver(max_distance=3)

# Extract characters from text
text = "Sir Kael entered the room. He looked around. Lady Elara followed. She smiled."
characters = resolver.extract_characters(text)
# Returns: ['Sir Kael', 'Lady Elara']

# Resolve pronouns
resolutions = resolver.resolve_pronouns(text)
# Returns: {'He_1:0': 'Sir Kael', 'She_2:0': 'Lady Elara'}

# Replace pronouns with names
result = resolver.replace_pronouns(text)
# Returns: "Sir Kael entered the room. Sir Kael looked around. Lady Elara followed. Lady Elara smiled."
```

### Convenience Functions

```python
from src.novel.pronoun_resolver import resolve_pronouns_in_text, replace_pronouns_in_text

# Quick pronoun resolution
text = "Sir Kael entered. He sat down."
resolutions = resolve_pronouns_in_text(text)

# Quick pronoun replacement
result = replace_pronouns_in_text(text)
```

### Configuration

The `PronounResolver` accepts a `max_distance` parameter that controls how many sentences back to look for character mentions:

```python
# Look back up to 5 sentences
resolver = PronounResolver(max_distance=5)
```

## How It Works

### Character Extraction

The system uses two patterns to identify characters:

1. **Title + Name Pattern**: Matches patterns like "Sir Kael", "Lady Elara", "King Arthur"
2. **Capitalized Names**: Matches capitalized words that are likely names (not common words)

### Gender Inference

Gender is inferred from:

1. **Titles**: Sir/Lord/King → male, Lady/Queen/Princess → female
2. **Name patterns**: Names ending in 'a', 'e', 'i', 'y' often female; 'el', 'or', 'an', 'er', 'on' often male

### Pronoun Resolution Algorithm

1. Extract all character mentions from the text
2. Track the position (sentence index) of each mention
3. For each pronoun, find candidate mentions within `max_distance` sentences
4. Filter candidates by gender compatibility
5. Score candidates based on:
   - Distance (closer = higher score)
   - Gender match (+50 points)
   - Number match (+30 points)
6. Select the highest-scoring candidate

## Supported Pronouns

- **Male**: he, him, his, himself
- **Female**: she, her, hers, herself
- **Neutral/Plural**: they, them, their, theirs, themselves

## Testing

Run the tests:

```bash
python -m pytest tests/novel/test_pronoun_resolver.py -v
```

## Limitations

- Simple sentence splitting (may not handle all edge cases)
- Gender inference is heuristic-based and may not be accurate for all names
- Does not handle ambiguous cases where multiple characters of the same gender are mentioned
- Does not handle complex narrative structures (flashbacks, multiple viewpoints, etc.)

## Future Improvements

- Integrate with spaCy for better named entity recognition
- Add support for custom character name lists
- Improve sentence boundary detection
- Add confidence scores for resolutions
- Handle more complex pronoun resolution scenarios
