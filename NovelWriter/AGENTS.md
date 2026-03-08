# AGENTS.md - NovelWriter Project Guide

This document provides essential information for AI coding agents working in this repository.

## Project Overview

NovelWriter is a dual-component Python project for AI-assisted novel writing:

| Component | Purpose | Python Version |
|-----------|---------|----------------|
| **LSP/** | Language Server Protocol implementation for novel editing | Python 3.14 |
| **Writer/** | AI-powered novel writing and publishing system | Python 3.10+ |

**LSP Features:** Go-to-definition, find-references, rename, diagnostics for novel symbols (@Character, @Location, @Item, @Lore, @PlotPoint)

**Writer Features:** Multi-agent collaboration (plot planning, character creation, worldbuilding), genre-specific writers, multi-platform publishing (Wattpad, Royal Road, Amazon KDP)

---

## Build/Lint/Test Commands

### LSP Component (`LSP/`)

```bash
cd LSP

# Setup
python -m venv .venv && source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/phase1/test_parser.py -v

# Run single test class/method
pytest tests/phase1/test_parser.py::TestParseMetadata -v
pytest tests/phase1/test_parser.py::TestParseMetadata::test_parse_character -v

# Run with coverage
pytest --cov=novelwriter_lsp --cov-report=term-missing

# Run by marker
pytest -m "not slow"  # Skip slow tests
pytest -m unit        # Unit tests only

# Linting & Formatting
ruff check .
black .
mypy novelwriter_lsp/

# Run server
python -m novelwriter_lsp
```

### Writer Component (`Writer/`)

```bash
cd Writer

# Setup
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Run all tests
pytest -v

# Run single test file/class/method
pytest tests/test_agents/test_writers.py -v
pytest tests/test_agents/test_writers.py::TestSciFiWriter -v
pytest tests/test_agents/test_writers.py::TestSciFiWriter::test_write_chapter -v

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Linting & Formatting
ruff check .
black .
mypy src/

# Run application
python -m src.main --help
python -m src.main health-check
python -m src.main workflow --genre fantasy --chapters 1
```

---

## Code Style Guidelines

### Import Order (Three-Section Style)

```python
# 1. Standard library (alphabetically sorted)
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# 2. Third-party packages
import pytest
from pydantic import Field
from pydantic_settings import BaseSettings

# 3. Local imports
from src.agents.base import AgentResult, BaseAgent
from src.llm.base import BaseLLM
```

### Type Hints (Python 3.10+ Modern Syntax)

```python
# Modern union syntax
def get_symbol(self, name: str) -> BaseSymbol | None:

# Modern generics
def execute(self, input_data: dict[str, Any]) -> AgentResult:
aliases: list[str] = field(default_factory=list)

# Always include return type
def __init__(self, name: str) -> None:
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | `snake_case.py` | `base_writer.py`, `parser.py` |
| Classes | `PascalCase` | `NovelWriterLSP`, `SciFiWriter` |
| Functions/Methods | `snake_case` | `write_chapter`, `parse_document` |
| Constants | `UPPER_SNAKE_CASE` | `GENRE`, `DOMAIN_KNOWLEDGE` |
| Private attributes | `_leading_underscore` | `_cache`, `_token_budget` |

### Docstrings (Google Style)

```python
class NovelWriterLSP(LanguageServer):
    """NovelWriter Language Server.

    A custom LSP server for AI writing systems.

    Attributes:
        version: Server version string
        name: Server name
    """

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute agent's main task.

        Args:
            input_data: Input data for agent's task

        Returns:
            AgentResult with success status and output data
        """
```

### Error Handling (AgentResult Pattern)

```python
# Return errors in result, don't raise for expected failures
async def execute(self, input_data: dict[str, Any]) -> AgentResult:
    try:
        content = await self.write_chapter(...)
        return AgentResult(success=True, data={"content": content})
    except Exception as e:
        logger.error(f"Writing failed: {e}")
        return AgentResult(
            success=False,
            data={},
            errors=[f"Writing failed: {str(e)}"],
        )
```

---

## Formatting & Linting Configuration

| Tool | Setting | Value |
|------|---------|-------|
| **Black** | line-length | 100 |
| **Ruff** | select | E, F, W, I, B, C4, UP |
| **Ruff** | ignore | E501 |
| **MyPy** | check_untyped_defs | true |

---

## Project Structure

```
NovelWriter/
├── LSP/                          # Language Server Protocol component
│   ├── novelwriter_lsp/          # Main package
│   │   ├── server.py             # LSP server implementation
│   │   ├── types.py              # Symbol dataclasses
│   │   ├── parser.py             # Text parsing
│   │   ├── index.py              # Symbol index management
│   │   ├── features/             # LSP feature handlers
│   │   ├── storage/              # Database clients (Neo4j, Milvus, Postgres)
│   │   └── agents/               # AI agents (validator, updater)
│   └── tests/                    # Test suite (phase1-4)
│
└── Writer/                       # Novel writing system component
    ├── src/
    │   ├── agents/               # AI agents (writers, orchestrator)
    │   ├── llm/                  # LLM integrations (DeepSeek)
    │   ├── memory/               # Memory systems
    │   ├── platforms/            # Publishing adapters
    │   ├── publishing/           # Publishing workflow
    │   ├── utils/                # Config, logging, caching
    │   └── main.py               # CLI entry point
    └── tests/                    # Test suite
```

---

## Testing Patterns

```python
# Fixture definition (conftest.py)
@pytest.fixture
def server() -> NovelWriterLSP:
    """Create a fresh server instance for each test."""
    return NovelWriterLSP()

# Async test
@pytest.mark.asyncio
async def test_parse_document(self, server: NovelWriterLSP) -> None:
    result = await server.parse_document(uri, content)
    assert result is not None

# Test class naming
class TestParseMetadata:
    class TestCharacterSymbol:
```

---

## Environment Variables

**Writer component** (see `Writer/.env.example`):
- `DEEPSEEK_API_KEY` - LLM API key (required)
- `REDIS_URL` - Redis for Celery scheduling
- `WATTPAD_API_KEY`, `ROYALROAD_USERNAME` - Publishing platforms

---

## Key Patterns

1. **Agent Pattern:** Inherit from `BaseAgent`, implement `async execute()`
2. **Result Pattern:** Return `AgentResult(success=True/False, data={...}, errors=[...])`
3. **Configuration Pattern:** Use Pydantic Settings with `@lru_cache` for singleton
4. **LSP Feature Pattern:** Register handlers via `register_*` functions
