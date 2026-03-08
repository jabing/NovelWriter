# Learnings: Enhance Definition Provider

## Task 3: Reference Scanning Implementation

### Performance Insights

**Regex Performance**: The `_extract_references()` function significantly exceeds performance requirements:
- **Requirement**: < 100ms for 1000 lines
- **Actual**: ~0.77ms for 1000 lines (129x faster than required)
- **Result**: 584 references found in 37,529 characters

### Implementation Details

1. **Longest Match Strategy**: Sorting aliases by length (descending) ensures proper matching
   - Example: "John Doe" matches before "John" when both are aliases
   - Critical for avoiding partial matches

2. **Word Boundaries**: Using `\b` in regex prevents false positives
   - Correctly avoids matching "John" within "Johnson"
   - Essential for accurate reference detection

3. **Module-Level Compilation**: Regex compiled once per call (not at module level) due to dynamic aliases
   - Still achieves excellent performance
   - Flexibility to handle different alias sets per document

### API Design

Function returns structured data for easy integration:
```python
[{
    "word": "John",          # The matched alias
    "line": 0,               # 0-indexed line number  
    "character": 0           # 0-indexed character position
}]
```

This format is ready for Task 4 (index population) and Task 5 (integration with parse_document).

### Next Steps

- Task 4: Integrate with index to populate `symbol.references` field
- Task 5: Call from `parse_document()` to automatically extract references
- Consider caching compiled patterns if same aliases used repeatedly

## Task 3 Completion Notes

### Added Performance Protection

- **500-line limit**: Documents exceeding 500 lines are skipped with a warning log
- **Rationale**: Prevents excessive processing on very large documents
- **Performance confirmed**: 500 lines with 3 aliases per line = 1500 references in ~0.75ms (well under 100ms target)

### Function Signature

```python
def _extract_references(text: str, aliases_dict: dict[str, str]) -> list[dict]:
```

Returns: `[{"word": "John", "line": 0, "character": 0}, ...]`

### Key Implementation Details

1. **Logging added**: `logger = logging.getLogger(__name__)` at module level
2. **Line count check**: Early return with warning if `len(lines) > 500`
3. **Longest match first**: Aliases sorted by length descending ensures "John Doe" matches before "John"
4. **Word boundaries**: `\b` regex prevents "John" matching within "Johnson"
5. **Special char escaping**: `re.escape()` handles aliases like "Mr. Doe"


## Task 1: Extended Symbol Type Definitions

### Implementation Summary

Successfully added `aliases: list[str] = field(default_factory=list)` field to all 9 symbol types:
1. CharacterSymbol
2. LocationSymbol  
3. ItemSymbol
4. LoreSymbol
5. PlotPointSymbol
6. OutlineSymbol
7. EventSymbol
8. RelationshipSymbol
9. ChapterSymbol

### Key Changes

1. **Field Definition**: Used `field(default_factory=list)` pattern for mutable default values
2. **Type Hints**: Modern Python 3.10+ syntax (`list[str]`, not `List[str]`)
3. **Documentation**: Updated all docstrings to include `aliases` in attributes list
4. **Backward Compatibility**: Existing symbols continue to work without aliases (defaults to empty list)

### Verification Results

- ✅ `mypy novelwriter_lsp/types.py`: Zero type errors in types.py (pre-existing errors in other files unrelated)
- ✅ `pytest tests/phase1/test_types.py -v`: All 31 tests passed
- ✅ `lsp_diagnostics`: No diagnostics on types.py
- ✅ Default value verification: `aliases` defaults to `[]`
- ✅ Configuration verification: `aliases` can be set to custom lists

### Usage Examples

```python
# Character with aliases
character = CharacterSymbol(
    id="char-1",
    name="John Doe",
    novel_id="novel-1",
    definition_uri="file:///test.md",
    definition_range={"start": 0, "end": 10},
    aliases=["John", "Mr. Doe", "Detective"]
)

# Character without aliases (backward compatible)
character = CharacterSymbol(
    id="char-2",
    name="Jane Smith",
    novel_id="novel-1",
    definition_uri="file:///test.md",
    definition_range={"start": 0, "end": 10},
    # aliases defaults to []
)
```

### Pattern Recognition

The `field(default_factory=list)` pattern is critical for mutable defaults in dataclasses:
- ❌ WRONG: `aliases: list[str] = []` (shared mutable default)
- ✅ CORRECT: `aliases: list[str] = field(default_factory=list)` (unique list per instance)

### Next Steps

Task 2 will extend the parser to extract aliases from symbol definitions like:
```markdown
@Character: John Doe { aliases: ["John", "Mr. Doe", "Detective"] }
```
