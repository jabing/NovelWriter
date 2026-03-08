# AI Writing LSP Server

A custom Language Server Protocol (LSP) server for AI writing systems—perfect for novels, creative writing, and documents!

## Features

| LSP Feature | Description |
|-------------|-------------|
| `goto_definition` | Jump from a character/location reference to its definition |
| `find_references` | Find all occurrences of a symbol in the document |
| `documentSymbol` | Show an outline of chapters, characters, locations, etc. |
| `rename` | Rename a character/location globally across all references |
| `diagnostics` | Check for consistency errors (future feature) |

## Symbol Types

- `@Character` - People, creatures, entities in your story
- `@Location` - Places and settings
- `@Item` - Significant objects
- `@Lore` - World-building facts, rules, history
- `@PlotPoint` - Foreshadowing, callbacks, key events
- `# Chapter`, `## Section` - Structural dividers

## Example Usage

```markdown
# Novel: The Rusty Detective

@Character: John Doe { description: "A rugged detective", age: 42 }
@Location: The Rusty Anchor Pub { city: "Boston" }

## Chapter 1

John Doe walked into The Rusty Anchor Pub...
```

## Requirements

- **Python 3.10+** (updated from 3.14 for compatibility with Writer component)

### Python Version Change (2026-03-08)

The Python version requirement has been unified with the Writer component:
- **Before**: `>=3.14`
- **After**: `>=3.10`

This change enables:
- Shared virtual environment with Writer
- Access to Writer's API and models
- Compatibility with all dependencies (including ChromaDB)

## Installation & Development

```bash
# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"

# Run the server
python -m novelwriter_lsp

# Run tests
pytest tests/ -v
```

## Project Structure

```
lsp-writing-server/
├── novelwriter_lsp/       # Python package
│   ├── __init__.py        # Package initialization
│   ├── server.py          # Main LSP server
│   ├── types.py           # Core dataclasses and types
│   ├── parser/            # Text parsing and symbol extraction
│   ├── index/             # Symbol index management
│   └── handlers/          # LSP feature handlers
├── tests/                 # Test suite
├── example.md             # Example novel content
├── DESIGN.md              # Full design document
├── pyproject.toml         # Python project configuration
└── README.md
```

## Roadmap

- [ ] Advanced diagnostics (inconsistent character attributes, broken plot points)
- [ ] AI integration for style checking and plot suggestions
- [ ] Hover information showing symbol attributes
- [ ] Completion suggestions for symbols
- [ ] Workspace-wide symbol support

## License

ISC
