# novelwriter-shared

Shared data models and API interfaces for the NovelWriter ecosystem.

## Installation

```bash
pip install novelwriter-shared
```

For development:

```bash
pip install -e ".[dev]"
```

## Components

### Data Models

- **CharacterProfile**: Complete character profile with timeline tracking
- **CharacterTimelineEvent**: Individual timeline events
- **Fact**: Story facts for context injection
- **TimelineConflict**: Detected timeline conflicts

### API Interfaces

- **WriterAPI**: Abstract interface for Writer operations

### Utilities

- **generate_id**: Unique ID generation

## Usage

```python
from novelwriter_shared.models import CharacterProfile, CharacterStatus, Fact, FactType
from novelwriter_shared.utils import generate_id

# Create a character profile
profile = CharacterProfile(
    name="Alice",
    tier=0,
    bio="Main protagonist",
)

# Create a fact
fact = Fact(
    fact_type=FactType.CHARACTER,
    content="Alice is the protagonist",
    chapter_origin=1,
)

# Generate unique ID
unique_id = generate_id(prefix="char")
```

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Format
black .

# Type check
mypy src/
```

## License

MIT
