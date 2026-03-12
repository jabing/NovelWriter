# Knowledge Graph Cleanup Logic

## Overview

This document defines the strategy for cleaning up unreferenced entities in the Knowledge Graph while protecting plot-relevant entities.

## Problem Statement

- Knowledge Graph stores entities in memory: `_nodes: dict[str, KnowledgeGraphNode]`
- No cleanup mechanism exists
- At 50K words: ~100-200 entities
- At 100K words: ~200-400 entities
- Unbounded growth causes memory pressure

## Solution: Periodic Cleanup with Entity Protection

**Cleanup Frequency**: Every 10 chapters

**Strategy**: Remove "unreferenced" entities while protecting plot-relevant ones.

## Unreferenced Criteria

An entity is considered "unreferenced" if ALL of the following are true:

1. **Not mentioned in last 5 chapters**: No appearance in `key_events` or chapter content
2. **Not a primary character**: `node_type != "character"` OR not in `primary_characters` list
3. **Not in active plot threads**: Not referenced in any `active` plot thread
4. **Not a main location**: `node_type != "location"` OR not marked as `is_main=True`

```python
def is_unreferenced(
    entity: KnowledgeGraphNode,
    recent_chapters: list[str],
    primary_characters: set[str],
    active_plot_threads: list[str]
) -> bool:
    """Determine if entity is safe to remove."""
    
    # Protection Rule 1: Primary characters NEVER removed
    if entity.node_id in primary_characters:
        return False
    
    # Protection Rule 2: Recently mentioned
    entity_name = entity.properties.get("name", entity.node_id)
    if any(entity_name in chapter for chapter in recent_chapters):
        return False
    
    # Protection Rule 3: In active plot threads
    if any(entity_name in thread for thread in active_plot_threads):
        return False
    
    # Protection Rule 4: Main locations
    if entity.node_type == "location" and entity.properties.get("is_main", False):
        return False
    
    return True
```

## Entity Protection Rules

### NEVER Remove

| Entity Type | Condition | Reason |
|-------------|-----------|--------|
| Primary character | In `primary_characters` set | Protagonist/antagonist always relevant |
| Recently mentioned | In last 5 chapters | May be reintroduced soon |
| Active status | `status == "active"` | Currently in story |
| Main location | `is_main == True` | Core story setting |

### Safe to Remove

| Entity Type | Condition | Reason |
|-------------|-----------|--------|
| Minor character | Not in last 5 chapters | Unlikely to return |
| Mentioned-once location | Single mention | Background flavor only |
| Resolved plot thread | `status == "resolved"` | No longer relevant |

## Cleanup Algorithm

```python
def cleanup_unreferenced(
    knowledge_graph: KnowledgeGraph,
    recent_chapters: list[str],  # Last 5 chapters
    primary_characters: set[str],
    active_plot_threads: list[str]
) -> list[str]:
    """
    Remove unreferenced entities from knowledge graph.
    
    Returns list of removed entity IDs for audit logging.
    """
    removed = []
    
    for node_id, node in list(knowledge_graph._nodes.items()):
        if is_unreferenced(node, recent_chapters, primary_characters, active_plot_threads):
            # Log before removing
            logger.info(f"Removing unreferenced entity: {node_id} ({node.node_type})")
            
            # Remove node
            del knowledge_graph._nodes[node_id]
            
            # Remove from indexes
            if node.node_type in knowledge_graph._node_type_index:
                knowledge_graph._node_type_index[node.node_type].discard(node_id)
            
            # Remove related edges
            edges_to_remove = [
                edge_id for edge_id in knowledge_graph._source_index.get(node_id, set())
            ]
            for edge_id in edges_to_remove:
                del knowledge_graph._edges[edge_id]
            
            removed.append(node_id)
    
    logger.info(f"Cleanup complete: removed {len(removed)} entities")
    return removed
```

## Configuration

```python
# In src/novel/knowledge_graph.py

CLEANUP_FREQUENCY = 10  # Every N chapters
LOOKBACK_CHAPTERS = 5  # How many chapters to check for references
PRIMARY_CHARACTERS = set()  # Set during initialization from character creation
```

## Edge Cases

### Entity Reintroduction

**Problem**: Entity removed at chapter 10, returns at chapter 25.

**Solutions**:
1. **Primary character protection**: Main characters never removed
2. **5-chapter lookback**: Reduces false positives
3. **Active plot thread check**: If mentioned in plot, kept
4. **Re-extraction on return**: If entity returns, it's re-added by inventory updater

### Rapid Entity Introduction

**Problem**: Many new entities in short time (e.g., party scene).

**Solutions**:
1. **Cleanup doesn't trigger immediately**: 10-chapter delay
2. **5-chapter lookback**: Recent entities protected
3. **Primary characters protected**: Key figures always kept

### Cross-Chapter References

**Problem**: Entity not mentioned but referenced by name.

**Solutions**:
1. **Check `key_events`**: References in events count
2. **Check plot threads**: References in active threads count
3. **Check relationships**: If entity has edges to active characters, keep

## Test Scenarios

### Scenario 1: Normal Cleanup
- **Given**: 150 entities, 100 referenced, 50 unreferenced
- **When**: Cleanup at chapter 10
- **Then**: Remove 50 unreferenced, keep 100

### Scenario 2: Primary Character Protection
- **Given**: Alice (primary) not mentioned in last 5 chapters
- **When**: Cleanup runs
- **Then**: Alice is NOT removed

### Scenario 3: Recently Mentioned
- **Given**: Bob mentioned in chapter 8
- **When**: Cleanup at chapter 10 (lookback=5)
- **Then**: Bob is NOT removed

### Scenario 4: Entity Reintroduction
- **Given**: Tavern Keeper removed at chapter 10
- **When**: Tavern Keeper mentioned again at chapter 20
- **Then**: Re-added by inventory updater (normal flow)

### Scenario 5: Main Location Protection
- **Given**: "Crystal Palace" marked as `is_main=True`
- **When**: Cleanup runs
- **Then**: Crystal Palace is NOT removed

## Integration Points

1. **ChapterGenerator**: Trigger cleanup after every 10th chapter
2. **ContinuityManager**: Provide `primary_characters` and `active_plot_threads`
3. **InventoryUpdater**: Provide recent chapter content for reference checking

```python
# In src/novel/chapter_generator.py

async def generate_chapter(self, chapter_num: int, ...):
    # ... existing chapter generation ...
    
    # Trigger cleanup every 10 chapters
    if chapter_num % 10 == 0:
        recent_chapters = self._get_recent_chapters(5)
        primary_chars = self.continuity.get_primary_characters()
        active_threads = [t.name for t in self.continuity.story_state.get_active_plot_threads()]
        
        removed = self.knowledge_graph.cleanup_unreferenced(
            recent_chapters=recent_chapters,
            primary_characters=primary_chars,
            active_plot_threads=active_threads
        )
```

## Audit Logging

All removals are logged for debugging:

```
[INFO] Knowledge graph cleanup starting at chapter 10
[INFO] Total entities: 150
[INFO] Primary characters: Alice, Bob, Charlie
[INFO] Removing unreferenced entity: tavern_keeper_3 (character)
[INFO] Removing unreferenced entity: old_forest_path (location)
[INFO] Cleanup complete: removed 25 entities, 125 remaining
```

## Guardrails

- ✅ MUST NOT remove primary characters
- ✅ MUST NOT remove entities mentioned in last 5 chapters
- ✅ MUST NOT remove entities with `status == "active"`
- ✅ MUST log all removals for audit
- ✅ MUST preserve entity relationships (remove edges with nodes)
- ❌ MUST NOT migrate to database (keep in-memory)
