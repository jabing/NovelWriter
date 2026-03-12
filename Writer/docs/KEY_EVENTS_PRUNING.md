# Key Events Pruning Strategy

## Overview

This document defines the strategy for pruning `StoryState.key_events` to prevent unbounded memory growth while maintaining plot coherence.

## Problem Statement

- `key_events` grows linearly with chapter count
- At 50K words: ~50-100 events
- At 100K words: ~100-200 events
- Unbounded growth causes memory pressure and context window overflow

## Solution: MAX_KEY_EVENTS = 50

**Justification**:
- Average novel chapter: 2,000-3,000 words
- 50 events ≈ 25 chapters of key plot points
- Sufficient context for current chapter + recent history
- Balances memory usage vs. plot coherence

## Event Classification

### Plot-Critical Events (NEVER prune)

Events matching these patterns are marked as "critical":

| Pattern | Regex | Examples |
|---------|-------|----------|
| Character death | `died|killed|murdered|sacrificed` | "Alice was killed by the dragon" |
| Major revelation | `revealed|discovered|learned the truth` | "Bob discovered his true parentage" |
| Relationship change | `married|betrayed|allied with|became enemies` | "Alice and Bob allied against the empire" |
| Location change (main) | `arrived at|entered|reached` + capital location | "They arrived at the Crystal Palace" |
| Item acquisition | `obtained|found|claimed|inherited` + artifact name | "Alice claimed the Sword of Light" |
| Status change | `crowned|promoted|exiled|imprisoned` | "Bob was crowned King" |

### Disposable Events (Can prune)

- Minor dialogue
- Routine actions (ate, slept, traveled)
- Redundant descriptions
- Non-plot-relevant observations

## Pruning Algorithm

```python
def prune_key_events(key_events: list[str], max_events: int = 50) -> list[str]:
    """
    Prune key_events to max_events, preserving plot-critical events.
    
    Priority:
    1. Critical events (never remove)
    2. Recent events (keep last N)
    3. Referenced events (keep if mentioned in recent chapters)
    """
    if len(key_events) <= max_events:
        return key_events
    
    # Step 1: Classify events
    critical_events = [e for e in key_events if is_critical(e)]
    non_critical = [e for e in key_events if not is_critical(e)]
    
    # Step 2: Keep all critical events
    remaining_budget = max_events - len(critical_events)
    
    # Step 3: Keep most recent non-critical events
    recent_non_critical = non_critical[-remaining_budget:]
    
    # Step 4: Combine and maintain order
    pruned = critical_events + recent_non_critical
    
    # Log pruning action
    removed_count = len(key_events) - len(pruned)
    logger.info(f"Pruned {removed_count} events, kept {len(pruned)}")
    
    return pruned
```

## Critical Event Detection

```python
CRITICAL_PATTERNS = [
    r"(?i)\b(died|killed|murdered|sacrificed|slain)\b",
    r"(?i)\b(revealed|discovered|learned the truth|uncovered)\b",
    r"(?i)\b(married|betrayed|allied with|became enemies|fell in love)\b",
    r"(?i)\b(crowned|promoted|exiled|imprisoned|freed)\b",
    r"(?i)\b(obtained|found|claimed|inherited|stole)\s+(the\s+)?[A-Z]",
]

def is_critical(event: str) -> bool:
    """Check if event matches critical patterns."""
    return any(re.search(pattern, event) for pattern in CRITICAL_PATTERNS)
```

## Edge Cases

### Entity Reintroduction

**Problem**: Character not mentioned for 10+ chapters, returns later.

**Solution**: 
- Check `character_states` for all characters ever mentioned
- Keep at least ONE event per character in `character_states`
- This ensures continuity when character returns

```python
def ensure_character_continuity(events: list[str], character_states: dict) -> list[str]:
    """Ensure at least one event per known character."""
    for char_name in character_states.keys():
        if not any(char_name in e for e in events):
            # Find and include the character's most important event
            char_events = [e for e in all_events if char_name in e]
            if char_events:
                events.append(char_events[0])  # Add most recent
    return events
```

### Climax Chapters

**Problem**: Chapters 20-25 have many critical events (climax).

**Solution**:
- During climax detection, increase MAX_KEY_EVENTS temporarily
- Climax detection: high density of critical events in recent chapters

```python
def detect_climax(events: list[str], window: int = 5) -> bool:
    """Detect if we're in a climax sequence."""
    recent = events[-window * 3:]  # Last 15 events
    critical_count = sum(1 for e in recent if is_critical(e))
    return critical_count / len(recent) > 0.5  # >50% critical = climax
```

## Test Scenarios

### Scenario 1: Normal Pruning
- **Given**: 75 events, 25 critical, 50 non-critical
- **When**: Prune to MAX_KEY_EVENTS=50
- **Then**: Keep 25 critical + 25 most recent non-critical

### Scenario 2: All Critical
- **Given**: 60 events, all critical
- **When**: Prune to MAX_KEY_EVENTS=50
- **Then**: Keep all 60 (critical events preserved)

### Scenario 3: Entity Reintroduction
- **Given**: Alice in chapter 1, not mentioned until chapter 20
- **When**: Pruning occurs at chapter 15
- **Then**: Alice's chapter 1 event is preserved

### Scenario 4: Climax Handling
- **Given**: Chapters 20-25 have 80% critical events
- **When**: Detect climax
- **Then**: Temporarily increase limit to 75

## Configuration

```python
# In src/novel/continuity.py

MAX_KEY_EVENTS = 50  # Default limit
CLIMAX_THRESHOLD = 0.5  # 50% critical events = climax
CLIMAX_MULTIPLIER = 1.5  # Increase limit by 50% during climax
```

## Implementation Location

- `src/novel/continuity.py:StoryState` - Add `prune_key_events()` method
- `src/novel/chapter_generator.py` - Call pruning after each chapter

## Guardrails

- ✅ MUST preserve events marked as plot-critical
- ✅ MUST handle entity reintroduction
- ✅ MUST log all pruning actions
- ✅ MUST maintain plot coherence
- ❌ MUST NOT use AI-based scoring (keep deterministic)
