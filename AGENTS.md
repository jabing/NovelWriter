# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work atomically
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations to avoid hanging on confirmation prompts.

Shell commands like `cp`, `mv`, and `rm` may be aliased to include `-i` (interactive) mode on some systems, causing the agent to hang indefinitely waiting for y/n input.

**Use these forms instead:**
```bash
# Force overwrite without prompting
cp -f source dest           # NOT: cp source dest
mv -f source dest           # NOT: mv source dest
rm -f file                  # NOT: rm file

# For recursive operations
rm -rf directory            # NOT: rm -r directory
cp -rf source dest          # NOT: cp -r source dest
```

**Other commands that may prompt:**
- `scp` - use `-o BatchMode=yes` for non-interactive
- `ssh` - use `-o BatchMode=yes` to fail instead of prompting
- `apt-get` - use `-y` flag
- `brew` - use `HOMEBREW_NO_AUTO_UPDATE=1` env var

<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update <id> --claim --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task atomically**: `bd update <id> --claim`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs with git:

- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

<!-- END BEADS INTEGRATION -->

<!-- BEGIN TECHNICAL DOCUMENTATION -->
## NovelWriter Technical Documentation

This section provides comprehensive technical guidance for AI agents working on the NovelWriter codebase.

### Project Overview

NovelWriter is an AI-powered novel writing and publishing system with specialized agents for:
- Plot planning, character creation, worldbuilding
- Genre-specific writing (Sci-Fi, Fantasy, Romance, History, Military)
- Multi-platform publishing (Wattpad, Royal Road, Amazon KDP)
- Market research and reader engagement

The system consists of two main components:
- **Novel Agent System** (`src/novel_agent/`) - Python backend with AI agents and publishing workflow
- **NovelWriter LSP** (`src/novelwriter_lsp/`) - Language Server Protocol implementation for editor integration

### Build/Lint/Test Commands

#### Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Install dependencies (including dev tools)
pip install -e ".[dev]"
```

#### Testing
```bash
# Run all tests
python -m pytest

# Run with verbose output
pytest -v

# Run agent tests
pytest tests/agents/test_writers.py

# Run LSP tests
pytest tests/lsp/test_server.py

# Run single test class
pytest tests/agents/test_writers.py::TestSciFiWriter

# Run single test method
pytest tests/agents/test_writers.py::TestSciFiWriter::test_write_chapter

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test markers
pytest -m asyncio  # Async tests only
```

#### Linting & Formatting
```bash
# Check with ruff (linting)
ruff check .

# Check specific file
ruff check src/novel_agent/agents/base.py

# Format with black
black .

# Format specific file
black src/novel_agent/agents/base.py

# Type checking with mypy
mypy src/
```

#### Running the Application
```bash
# CLI entry point for novel agent system
python -m src.novel_agent.main --help

# Or use the installed script
novel-agent --help

# Common commands
python -m src.novel_agent.main health-check
python -m src.novel_agent.main generate --novel-id test --chapter 1 --genre fantasy
python -m src.novel_agent.main workflow --genre fantasy --chapters 1
python -m src.novel_agent.main studio --flet  # Launch GUI

# LSP server (for editor integration)
python -m src.novelwriter_lsp.server
```

### Project Structure

```
NovelWriter/
├── src/
│   ├── novel_agent/           # AI agent system (Python backend)
│   │   ├── agents/           # AI agents (Plot, Character, Worldbuilding, Writers, Editor)
│   │   │   ├── base.py       # BaseAgent, AgentResult, AgentState
│   │   │   ├── orchestrator.py
│   │   │   └── writers/      # Genre-specific writers (scifi, fantasy, etc.)
│   │   ├── llm/              # LLM integrations (DeepSeek, base class)
│   │   ├── memory/           # Memory systems (file-based, character, plot, world)
│   │   ├── platforms/        # Publishing platform adapters
│   │   ├── publishing/       # Publishing workflow management
│   │   ├── crawlers/         # Web crawlers for market research
│   │   ├── scheduler/        # Task scheduling (Celery-based)
│   │   ├── studio/           # GUI/TUI interfaces
│   │   ├── utils/            # Configuration, logging, caching
│   │   └── main.py           # CLI entry point (Click-based)
│   │
│   └── novelwriter_lsp/       # Language Server Protocol (editor integration)
│       ├── server.py         # LSP server implementation
│       ├── handlers/         # LSP request handlers
│       └── features/          # LSP features (completion, diagnostics, etc.)
│
├── tests/
│   ├── agents/               # Novel agent system tests
│   │   ├── conftest.py       # Shared fixtures
│   │   ├── test_agents/      # Agent tests
│   │   ├── test_llm/         # LLM tests
│   │   ├── test_memory/      # Memory tests
│   │   └── test_integration/ # End-to-end workflow tests
│   │
│   └── lsp/                   # LSP tests
│       ├── test_server.py     # LSP server tests
│       ├── test_handlers/    # Handler tests
│       └── test_features/    # Feature tests
│
├── web/                      # Vue3 frontend (optional)
│   ├── src/
│   │   ├── components/       # Vue components
│   │   ├── views/            # Page views
│   │   ├── stores/           # Pinia state management
│   │   ├── api/              # API client
│   │   └── locales/          # i18n translations
│   └── e2e/                  # Playwright E2E tests
│
└── docs/                     # Documentation
    ├── QUICKSTART.md         # Quick start guide
    ├── ARCHITECTURE.md       # System architecture
    ├── DEVELOPMENT.md        # Development guide
    └── USER_MANUAL.md        # User manual
```

### Code Style Guidelines

#### Python Version & Type Hints
- **Python 3.10+** required
- Use modern union syntax: `X | None` instead of `Optional[X]`
- Use modern generics: `list[str]`, `dict[str, Any]` instead of `List[str]`, `Dict[str, Any]`
- Always add return type hints for functions: `-> None`, `-> str`, `-> AgentResult`

#### Import Order
```python
# 1. Standard library
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# 2. Third-party packages
import pytest
from pydantic import Field
from pydantic_settings import BaseSettings

# 3. Local imports (src.*)
from src.novel_agent.agents.base import AgentResult, BaseAgent
from src.novel_agent.llm.base import BaseLLM
```

#### File Structure
```python
# src/novel_agent/module_name.py
"""Module docstring describing purpose."""

import asyncio
from typing import Any

from src.novel_agent.base_module import BaseClass

logger = logging.getLogger(__name__)


class MyClass:
    """Class docstring.

    Longer description if needed.
    """

    def __init__(self, name: str) -> None:
        """Initialize the class.

        Args:
            name: Description of name parameter.
        """
        self.name = name

    async def do_something(self, input_data: dict[str, Any]) -> str:
        """Do something useful.

        Args:
            input_data: Input dictionary description.

        Returns:
            Description of return value.
        """
        return "result"
```

#### Naming Conventions
- **Modules**: `snake_case.py` (e.g., `file_memory.py`, `base_writer.py`)
- **Classes**: `PascalCase` (e.g., `AgentOrchestrator`, `SciFiWriter`)
- **Functions/Methods**: `snake_case` (e.g., `write_chapter`, `get_writer`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `BASE_URL`, `MODELS`)
- **Private attributes**: `_leading_underscore` (e.g., `_total_tokens_used`)
- **Class attributes**: `UPPER_CASE` for class constants (e.g., `GENRE`, `DOMAIN_KNOWLEDGE`)

#### Data Classes & Models
```python
# Use dataclasses for simple data containers
from dataclasses import dataclass, field

@dataclass
class AgentResult:
    success: bool
    data: dict[str, Any]
    errors: list[str] = field(default_factory=list)

# Use Pydantic for configuration and validation
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str = Field(default="", description="API key")
    timeout: int = Field(default=30, ge=1)
```

#### Abstract Base Classes
```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base class for all agents."""

    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the agent's main task."""
        pass
```

#### Async Patterns
- Use `async/await` for all agent operations
- Use `AsyncMock` for mocking async methods in tests
- Use `asyncio.run()` for synchronous entry points

```python
# In agents
async def execute(self, input_data: dict[str, Any]) -> AgentResult:
    result = await self.llm.generate(prompt)
    return AgentResult(success=True, data={"content": result.content})

# In tests
@pytest.mark.asyncio
async def test_execute(self, writer: SciFiWriter) -> None:
    result = await writer.execute({...})
    assert result.success is True

# In CLI (sync entry point)
def cli_command():
    result = asyncio.run(run_generation())
```

#### Error Handling
```python
# Return errors in AgentResult, don't raise exceptions for expected failures
async def execute(self, input_data: dict[str, Any]) -> AgentResult:
    try:
        content = await self.write_chapter(...)
        return AgentResult(success=True, data={"content": content})
    except Exception as e:
        return AgentResult(
            success=False,
            data={},
            errors=[f"Writing failed: {str(e)}"],
        )
```

#### Enums
```python
from enum import Enum

class AgentState(str, Enum):
    """Possible states for an agent."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Vector Storage

The Novel Agent System supports local vector storage using Chroma or cloud storage using Pinecone.

#### Migration from Pinecone to Chroma

Chroma has been adopted as the default vector store for:
- Zero-cost operation (vs Pinecone $70-840/month)
- Local deployment (no API key management)
- Lower latency (1-10ms local vs <50ms network)
- Chinese text support via multilingual embedding model

#### Configuration

Chroma settings (in `src/novel_agent/utils/config.py`):

```python
class Settings(BaseSettings):
    # Chroma configuration
    chroma_persist_path: str = "data/chroma"
    chroma_collection_name: str = "novel-facts"
    chroma_embedding_model: str = "shibing624/text2vec-base-multilingual"

    # Vector store type selector
    vector_store_type: str = "chroma"  # or "pinecone"

    # Milvus as fallback (preserved for future use)
    milvus_enabled: bool = False
    milvus_uri: str = "~/.memsearch/milvus.db"
```

#### Using VectorStoreFactory

The `VectorStoreFactory` provides a unified interface for vector storage:

```python
from src.novel_agent.db.vector_store_factory import VectorStoreFactory
from src.novel_agent.utils.config import get_settings

settings = get_settings()
vector_store = VectorStoreFactory.get_vector_store(
    settings.vector_store_type,
    persist_path=settings.chroma_persist_path,
    collection_name=settings.chroma_collection_name,
)

# Use vector store
await vector_store.upsert_vectors(ids=["test"], texts=["test"])
results = await vector_store.query_similar("search query", n_results=10)
await vector_store.delete_vectors(ids=["test"])
```

#### Performance Characteristics

- **Query latency**: <20ms (Chroma local)
- **Batch insert throughput**: >1000 vectors/s
- **Embedding generation**: <500ms (cold cache), <100ms (warm cache)
- **Deployment**: Local SQLite-based persistent storage

#### Environment Variables

- `VECTOR_STORE_TYPE`: "chroma" (default) or "pinecone"
- Configuration loaded from environment or defaults

### Testing Patterns

#### Fixtures
```python
# tests/agents/conftest.py - shared fixtures
@pytest.fixture
def mock_settings():
    from src.novel_agent.utils.config import Settings
    return Settings(deepseek_api_key="test_key", log_level="DEBUG")

# In test files
@pytest.fixture
def writer(self) -> SciFiWriter:
    mock_llm = MagicMock()
    mock_llm.generate_with_system = AsyncMock(return_value=MagicMock(content="Test content"))
    return SciFiWriter(name="Test Writer", llm=mock_llm)
```

#### Async Test Pattern
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestMyClass:
    @pytest.mark.asyncio
    async def test_async_method(self, fixture) -> None:
        result = await fixture.execute({...})
        assert result.success is True
        assert "content" in result.data
```

### Environment Variables

Required for operation (see `.env.example`):
- `DEEPSEEK_API_KEY` - LLM API key (required)
- `REDIS_URL` - Redis connection (for scheduling)
- `WATTPAD_API_KEY` / `ROYALROAD_USERNAME` - For publishing

### Key Patterns

1. **Agent Pattern**: All agents inherit from `BaseAgent` and implement `async execute()`
2. **LLM Pattern**: All LLMs inherit from `BaseLLM` and implement `async generate()` and `async generate_with_system()`
3. **Memory Pattern**: Memory systems implement `BaseMemory` with `async store()` and `async retrieve()`
4. **Result Pattern**: Return `AgentResult(success=True/False, data={...}, errors=[...])`
5. **Configuration Pattern**: Use Pydantic Settings with `@lru_cache` for singleton access

### Troubleshooting

#### Common Import Errors

##### ModuleNotFoundError: memsearch
The `memsearch` module is optional. Tests should use `importlib.util` to load modules directly:
```python
import importlib.util
spec = importlib.util.spec_from_file_location('module', 'path/to/module.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

##### ImportError: cannot import 'override' from typing
`typing.override` was added in Python 3.12. Use conditional import:
```python
try:
    from typing import override
except ImportError:
    from typing_extensions import override
```

##### TypeError: callable | None
`callable` is a builtin function, not a type. Use `Callable` from typing:
```python
from typing import Callable
def foo(callback: Callable | None = None): ...
```

##### ModuleNotFoundError: chromadb
ChromaDB is an optional dependency. Install with:
```bash
pip install chromadb
```

Or skip tests that require it using pytest markers.

### Genre-Specific Writing Guidelines

The Novel Agent System includes specialized writers for different genres:

#### Sci-Fi Writer
- Focus on hard science concepts, physics, space exploration
- Future technology and societal implications
- Time travel paradoxes and causality
- Artificial intelligence and robotics

#### Fantasy Writer
- Magic systems with internal logic and rules
- Worldbuilding with races, cultures, and history
- Mythological elements and epic narratives
- Quest structures and hero journeys

#### Romance Writer
- Emotional arcs and character development
- Dialogue and relationship dynamics
- Pacing and tension building
- Subgenres: contemporary, historical, paranormal

#### Historical Writer
- Period-accurate details and cultural context
- Historical events and figures integration
- Language style appropriate to the era
- Social customs and daily life details

#### Military Writer
- Tactical strategies and chain of command
- Weapon systems and technology
- Battle sequences and combat realism
- Military terminology and jargon

<!-- END TECHNICAL DOCUMENTATION -->
