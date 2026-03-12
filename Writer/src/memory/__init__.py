# src/memory/__init__.py
"""Memory module - Context and memory management.

CompositeMemory is the primary memory implementation, providing:
- Routing to specialized memory implementations (character, plot, world)
- Semantic search via MemSearch and Milvus vector index
- L0/L1/L2 tiered context loading
- Backward compatibility with MemSearchAdapter
"""

from src.memory.base import BaseMemory, MemoryEntry
from src.memory.character_memory import CharacterMemory
from src.memory.composite_memory import CompositeMemory
from src.memory.memsearch_adapter import ContextLevel, MemSearchAdapter
from src.memory.plot_memory import PlotMemory
from src.memory.world_memory import WorldMemory

__all__ = [
    "BaseMemory",
    "MemoryEntry",
    "MemSearchAdapter",
    "ContextLevel",
    "CharacterMemory",
    "PlotMemory",
    "WorldMemory",
    "CompositeMemory",
]

# Default memory implementation
Memory = CompositeMemory
