# Type Errors Fix - Learnings

## test_parser.py Line 116 Fix

**Date**: 2026-03-08
**File**: tests/phase1/test_parser.py
**Line**: 116
**Issue**: mypy type error when accessing `symbols[1].age`

### Pattern Applied

Added `isinstance` assertion before accessing type-specific attributes:

```python
# Before
assert symbols[1].name == "Jane Smith"
assert symbols[1].age == 25

# After
assert symbols[1].name == "Jane Smith"
assert isinstance(symbols[1], CharacterSymbol)
assert symbols[1].age == 25
```

### Why This Works

- mypy narrows the type based on the `isinstance` check
- After the assertion, mypy knows `symbols[1]` is specifically a `CharacterSymbol`
- This allows safe access to `CharacterSymbol`-specific attributes like `age`

### Consistency

This follows the same pattern used in:
- test_definition.py
- test_index.py

### Verification

Run `mypy tests/phase1/test_parser.py` to confirm the type error is resolved.
