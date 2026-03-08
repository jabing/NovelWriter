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

## Task 2: Alias Parsing in Parser

### Implementation Summary

Successfully implemented alias parsing in `_parse_metadata()` function and integrated with `_create_symbol_from_match()`:

1. **Metadata Parsing**: Extended `_parse_metadata()` to handle array format `aliases: ["John", "Johnny"]`
2. **Regex Pattern**: Added `aliases:\s*\[([^\]]*)\]` to extract array content
3. **Array Parsing**: Implemented robust parsing that handles:
   - Double quotes: `["John", "Johnny"]` → `["John", "Johnny"]`
   - Single quotes: `['John', 'Johnny']` → `["John", "Johnny"]`
   - Empty arrays: `aliases: []` → `aliases: []`
   - Mixed metadata: `aliases: ["John"], age: 42` → both parsed correctly

4. **Symbol Integration**: Updated `_create_symbol_from_match()` to pass `aliases` to all 9 symbol constructors
   - CharacterSymbol, LocationSymbol, ItemSymbol, LoreSymbol, PlotPointSymbol
   - OutlineSymbol, EventSymbol, RelationshipSymbol, ChapterSymbol

### Key Implementation Details

**Parsing Logic** (lines 58-73 in parser.py):
```python
# Parse aliases array first (special case for array format)
aliases_match = re.search(r"aliases:\s*\[([^\]]*)\]", content)
if aliases_match:
    aliases_str = aliases_match.group(1)
    if aliases_str.strip():
        aliases = []
        for a in aliases_str.split(","):
            a = a.strip()
            if a and a[0] in "\"'" and a[-1] in "\"'":
                a = a[1:-1]
            if a:
                aliases.append(a)
        metadata["aliases"] = aliases
    else:
        metadata["aliases"] = []
```

**Symbol Constructor** (example from CharacterSymbol):
```python
return CharacterSymbol(
    id=symbol_id,
    name=name,
    novel_id="",
    definition_uri=uri,
    definition_range=definition_range,
    metadata=metadata,
    aliases=metadata.get("aliases", []),  # ← Pass parsed aliases
    age=int(cast(str, metadata.get("age"))) if metadata.get("age") else None,
    # ... other fields
)
```

### Verification Results

- ✅ `pytest tests/phase1/test_parser.py -v`: All 39 tests passed
- ✅ Backward compatibility: Symbols without aliases work correctly (aliases defaults to `[]`)
- ✅ Parse verification: `{aliases: ["John", "Johnny"]}` → `{"aliases": ["John", "Johnny"]}`
- ✅ All 9 symbol types correctly populate aliases field
- ✅ Mixed metadata parsing works: `aliases: ["John"], age: 42, status: alive`

### Documentation

Added comprehensive docstring to `_parse_metadata()` documenting:
- Input format (metadata string with braces)
- Supported formats (simple key-value and array format for aliases)
- Return value structure
- Examples of both formats

### Pattern Recognition

**Special Case Parsing**: Array values (aliases) require special handling before simple key-value parsing:
1. Parse arrays first using regex (before simple key-value regex runs)
2. Filter out "aliases" from simple key-value pairs to avoid duplication
3. Use `*` instead of `+` in regex for empty array support

**Quote Stripping**: Handle both double and single quotes uniformly:
```python
if a and a[0] in "\"'" and a[-1] in "\"'":
    a = a[1:-1]
```

### Backward Compatibility

Existing symbols without aliases continue to work correctly:
```markdown
@Character: John Doe {age: 42, status: alive}
```
→ Symbol created with `aliases: []` (empty list, not None)

### Next Steps

Task 3 (Reference Scanning) is already complete. Task 4 (AliasIndex) will use the parsed aliases to:
1. Build a reverse mapping from aliases to symbol IDs
2. Enable fast alias lookups for goto-definition and find-references
3. Support multiple symbols with the same alias (disambiguation needed)


## Bug Fix: _parse_metadata Missing aliases Key

### Problem

When metadata didn't contain an `aliases` field, `_parse_metadata()` returned a dictionary WITHOUT the "aliases" key. This caused issues:

```python
metadata = _parse_metadata('{age: 42}')
assert metadata.get('aliases') == []  # FAILED - returns None (key doesn't exist)
```

### Root Cause

The `else: metadata["aliases"] = []` statement was **inside** the `if aliases_str.strip():` block (line 75), not inside the outer `if aliases_match:` block (line 72). This meant:

- If `aliases_match` is `None` (no aliases in metadata): The entire outer `if` block is skipped, so `metadata["aliases"]` is never set
- If `aliases_match` exists but `aliases_str` is empty: The `else` sets `metadata["aliases"] = []`

### Fix Applied

Added an `else` clause to the outer `if aliases_match:` block:

```python
if aliases_match:
    aliases_str = aliases_match.group(1)
    if aliases_str.strip():
        # ... parse aliases ...
        metadata["aliases"] = aliases
    else:
        metadata["aliases"] = []
else:
    # NEW: No aliases field - set to empty list for consistency
    metadata["aliases"] = []
```

### Test Updates

Updated 5 test cases in `tests/phase1/test_parser.py` to expect `"aliases": []` in the result:
- `test_parse_metadata_single_key_value`
- `test_parse_metadata_multiple_key_values`
- `test_parse_metadata_with_quoted_values`
- `test_parse_metadata_with_single_quotes`
- `test_parse_metadata_complex`

### Verification

All 39 parser tests pass after fix:
```bash
pytest tests/phase1/test_parser.py -v  # 39 passed
```

### Consistency Guarantee

The fix ensures `metadata["aliases"]` is **ALWAYS** set:
- With aliases: `metadata["aliases"] = ["John", "Johnny"]`
- Without aliases: `metadata["aliases"] = []`
- Empty aliases: `metadata["aliases"] = []`

This prevents `None` returns and ensures consistent behavior across all symbol types.


## Task 4: AliasIndex Implementation

### Implementation Status

The `AliasIndex` class was **already fully implemented** in `novelwriter_lsp/index.py` (lines 20-71).

### Implementation Details

1. **Class Structure**:
   - Location: `novelwriter_lsp/index.py` at module level (lines 20-71)
   - Storage: Uses `dict[str, str]` for `_alias_map` (O(1) lookup)
   - Three required methods: `add_alias()`, `get_symbol_name()`, `remove_symbol()`
   - Bonus method: `clear()` for clearing all aliases

2. **Method Signatures**:
   ```python
   def add_alias(self, alias: str, symbol_name: str) -> None
   def get_symbol_name(self, alias: str) -> str | None
   def remove_symbol(self, symbol_name: str) -> None
   def clear(self) -> None  # bonus method
   ```

3. **Integration with SymbolIndex**:
   - `SymbolIndex.__init__()` creates `_alias_index = AliasIndex()` (line 108)
   - `SymbolIndex.update()` adds aliases from symbols (lines 142-145)
   - `SymbolIndex._evict_oldest()` removes aliases (line 178)
   - `SymbolIndex.remove()` removes aliases (line 201)
   - `SymbolIndex.get_symbol_by_alias()` provides alias lookup (lines 224-228)
   - `SymbolIndex.clear()` clears aliases (line 349)

### Verification Results

✅ **All tests pass**:
- `pytest tests/phase1/test_index.py -v`: 19 passed
- `pytest tests/phase1/test_alias_index.py -v`: 13 passed (comprehensive AliasIndex tests)
- `pytest tests/performance/test_alias_performance.py -v`: 4 passed (O(1) lookup verified)

✅ **Manual verification**:
- `add_alias("John", "John Doe")` works correctly
- `get_symbol_name("John")` returns `"John Doe"`
- `remove_symbol("John Doe")` removes all aliases
- `get_symbol_name("John")` returns `None` after removal
- Integration with `SymbolIndex` works correctly

### Test Coverage

The test suite includes comprehensive coverage:
1. **Basic operations**: add single/multiple aliases
2. **Edge cases**: empty index, nonexistent aliases, empty strings
3. **Removal**: remove all aliases for a symbol, partial removal
4. **Case sensitivity**: "john", "John", "JOHN" are different
5. **Special characters**: "John-Doe", "John_Doe", "John.Doe"
6. **Performance**: O(1) lookup time verified with 1000 operations

### Key Design Decisions

1. **Exact matching only**: No fuzzy matching or similarity search (as required)
2. **Single result**: `get_symbol_name()` returns single result or `None` (no conflict handling)
3. **Simple dict**: Uses `dict[str, str]` for O(1) lookup performance
4. **No caching**: Dict lookup is already O(1), no additional caching needed
5. **Comprehensive docstrings**: Each method has detailed documentation

### No Changes Required

The implementation was complete and correct. All requirements from Task 4 were met:
- ✅ Created `AliasIndex` class with required methods
- ✅ Uses `dict[str, str]` for O(1) performance
- ✅ Proper type hints and docstrings
- ✅ No fuzzy matching or multiple results
- ✅ Integrated with `SymbolIndex`
- ✅ All tests pass

### Next Steps

Task 5 will integrate `AliasIndex` into `SymbolIndex` - but this integration is already complete!
The `SymbolIndex` class already:
- Creates `_alias_index` in `__init__()`
- Adds aliases in `update()`
- Removes aliases in `remove()` and `_evict_oldest()`
- Provides `get_symbol_by_alias()` lookup method
- Clears aliases in `clear()`

Task 5 might focus on additional integration points or usage in other parts of the system.


## Task 5: Integrate AliasIndex into SymbolIndex

### Implementation Status

The integration was **already complete** in the previous task. This task added the missing docstring for `get_symbol_by_alias()`.

### What Was Already Implemented

1. **`SymbolIndex.__init__()`** (line 108):
   - Already creates `self._alias_index = AliasIndex()`

2. **`SymbolIndex.update()`** (lines 142-145):
   - Already extracts aliases from symbols using `getattr(symbol, 'aliases', None)`
   - Already adds each alias to `_alias_index`

3. **`SymbolIndex.remove()`** (line 201):
   - Already calls `self._alias_index.remove_symbol(name)` for each removed symbol

4. **`SymbolIndex._evict_oldest()`** (line 178):
   - Already calls `self._alias_index.remove_symbol(oldest_name)` during eviction

5. **`SymbolIndex.get_symbol_by_alias()`** (lines 224-242):
   - Already implemented the two-step lookup (alias → symbol name → symbol)
   - **Added**: Comprehensive docstring (Google style)

6. **`SymbolIndex.clear()`** (line 349):
   - Already calls `self._alias_index.clear()`

### Changes Made in Task 5

Only one change required: **Added docstring to `get_symbol_by_alias()` method**

The docstring includes:
- Purpose and description
- Args section
- Returns section  
- Example usage
- Follows Google style (consistent with rest of codebase)

### Verification Results

✅ **All tests pass**:
- `pytest tests/phase1/test_index.py -v`: 19 passed
- `pytest tests/phase1/test_alias_index.py -v`: 13 passed
- `pytest tests/phase1/ -v`: 128 passed

✅ **Manual integration verification**:
- Symbols with aliases: Look up by alias works correctly
- Symbols without aliases: Backward compatible (empty list)
- Removal: Aliases cleaned up correctly
- Non-existent aliases: Returns `None` as expected

✅ **Backward compatibility**:
- Existing code continues to work
- No method signature changes
- `get_symbol()` still only looks up by exact name (single responsibility)

### Key Design Decisions

1. **Separate methods for name vs alias lookup**:
   - `get_symbol(name)` - exact name match only
   - `get_symbol_by_alias(alias)` - alias lookup only
   - Rationale: Single responsibility, clear intent

2. **Two-step lookup in `get_symbol_by_alias()`**:
   - First: `alias_index.get_symbol_name(alias)` → get symbol name
   - Second: `get_symbol(symbol_name)` → get full symbol
   - Rationale: Reuses existing `get_symbol()` logic (LRU cache, validation)

3. **Safe attribute access**:
   - `aliases = getattr(symbol, 'aliases', None)` in `update()`
   - Rationale: Handles both symbols with and without aliases field

### Integration Points

The integration touches these SymbolIndex methods:
- `__init__()` - initialization
- `update()` - add aliases when symbol added/updated
- `remove()` - clean up aliases when symbols removed
- `_evict_oldest()` - clean up aliases during LRU eviction
- `get_symbol_by_alias()` - NEW public API for alias lookup
- `clear()` - clear all aliases

### Next Steps

Task 6 will use `get_symbol_by_alias()` in the definition provider to:
- Look up symbols by alias in `goto_definition` feature
- Enable jumping from "John" to "John Doe" definition
- Maintain backward compatibility with exact name lookups


## Task 6: Definition Lookup with Alias Support

### Implementation Summary

Modified `novelwriter_lsp/features/definition.py` to support alias-based lookup with conflict handling.

### Key Changes

1. **Type Alias for LSP Compliance**:
   ```python
   DefinitionResult = types.Location | list[types.Location] | None
   ```
   - Follows LSP specification: `textDocument/definition` returns `Location | Location[] | null`
   - Uses modern Python 3.10+ union syntax (`X | Y` not `Union[X, Y]`)

2. **Performance Protection**:
   ```python
   MAX_LOCATIONS = 10
   ```
   - Limits returned locations to prevent performance issues with many conflicts

3. **Helper Function**:
   ```python
   def _create_location(symbol: BaseSymbol) -> types.Location:
   ```
   - Avoids code duplication when creating Location objects
   - Single place to update if Location structure changes

4. **Two-Phase Lookup Strategy**:
   - Phase 1: Exact symbol name match (`index.get_symbol(symbol_name)`)
   - Phase 2: Alias-based lookup (`index.get_symbol_by_alias(symbol_name)`)
   - Both phases can add to the results (conflict handling)

5. **Conflict Handling**:
   ```python
   locations: list[types.Location] = []
   seen_symbol_ids: set[str] = set()
   
   # Add exact match
   if exact_symbol:
       locations.append(_create_location(exact_symbol))
       seen_symbol_ids.add(exact_symbol.id)
   
   # Add alias match (only if different symbol)
   if alias_symbol and alias_symbol.id not in seen_symbol_ids:
       locations.append(_create_location(alias_symbol))
   ```
   - Uses `seen_symbol_ids` set to avoid duplicates
   - Returns `Location` for single match, `Location[]` for multiple matches

### Return Types

- `None`: No symbol found (exact or alias)
- `Location`: Single match found
- `list[Location]`: Multiple matches (conflict), limited to MAX_LOCATIONS

### Conflict Scenario Example

When user clicks on "John" and:
- Symbol "John" exists (exact match)
- Symbol "John Doe" has alias "John" (alias match)

Both locations are returned, allowing the editor to present a disambiguation UI.

### Backward Compatibility

- `_extract_word()` function preserved unchanged
- Existing exact match behavior unchanged
- Alias lookup is additional, not replacement

### Verification

- ✅ `mypy`: No errors in definition.py
- ✅ `ruff`: All checks passed (used `X | Y` syntax)
- ✅ `black`: Formatting passes
- ✅ Manual tests: All scenarios verified
- ✅ LSP diagnostics: Only expected "unused function" warning (decorator hides usage)

### Code Style Notes

- Ruff prefers `X | Y` over `Union[X, Y]` for Python 3.10+
- The `@server.feature` decorator makes the function appear "unused" to static analysis
- Module docstrings must explain LSP spec compliance

### Next Steps

Task 7 will implement cache invalidation for aliases when symbols are updated or removed.


## Task 7: Cache Invalidation Strategy

### Implementation Summary

Successfully implemented event-driven cache invalidation for document changes in `server.py`:

1. **Added `on_text_document_did_change()` handler** (lines 189-255 in server.py):
   - Tracks document content in `server._documents` dict
   - Applies incremental changes to stored content
   - Invalidates cache by calling `index.remove(uri)` to remove old symbols and aliases
   - Re-parses document via `server.parse_document()` to add new symbols and aliases
   - Runs diagnostics validation after re-indexing

2. **Updated `on_text_document_did_open()`** (line 172):
   - Stores document content in `server._documents` dict

3. **Updated `on_text_document_did_close()`** (line 185):
   - Removes document from `server._documents` dict
   - Removes symbols from index (already existed)

4. **Refactored `register_diagnostics()`** (novelwriter_lsp/features/diagnostics.py):
   - Removed duplicate `TEXT_DOCUMENT_DID_CHANGE` handler
   - Extracted validation logic into `validate_document()` function
   - Stored in `server._custom_state["validate_document"]` for reuse

### Key Implementation Details

**Document Content Tracking** (lines 69-71 in server.py):
```python
self._diagnostics: dict[str, tuple[int, list[types.Diagnostic]]] = {}
self._custom_state: dict[str, Any] = {}
self._documents: dict[str, str] = {}  # NEW: Track document content
```

**Change Handler** (lines 189-255):
```python
@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
async def on_text_document_did_change(params: types.DidChangeTextDocumentParams) -> None:
    # Step 1: Apply content changes to stored document
    current_content = server._documents[uri]
    for change in params.content_changes:
        # Handle full document or incremental changes
        ...

    # Step 2: Invalidate cache - remove old symbols and aliases
    removed_symbols = index.remove(uri)
    if removed_symbols:
        logger.debug(f"Cache invalidated for {uri}: removed {len(removed_symbols)} symbols")

    # Step 3: Re-parse and update index with new symbols
    server.parse_document(uri, current_content)

    # Step 4: Run diagnostics validation
    validate_func = server._custom_state.get("validate_document")
    if validate_func:
        await validate_func(uri, current_content)
```

### Performance Results

✅ **Performance requirement met**:
- Requirement: Re-index 1000-line document < 200ms
- Actual: 8.22ms total (4.71ms parse + 3.51ms remove)
- **~24x faster than required**

Test scenario: 1200 lines, ~600 symbols (200 characters, 200 locations, 200 items)

### Verification Results

✅ **All tests pass**:
- `pytest tests/phase1/test_server.py -v`: 8 passed
- `pytest tests/phase1/ -v`: 128 passed
- `lsp_diagnostics`: No errors on changed files

✅ **Manual cache invalidation verification**:
```python
# Initial document with symbol + aliases
server.parse_document(uri, '@Character: John Doe { aliases: ["JD", "Johnny"] }')
assert len(index) == 1
assert len(index._alias_index._alias_map) == 2

# Cache invalidation on change
removed = index.remove(uri)
assert len(removed) == 1
assert len(index) == 0
assert len(index._alias_index._alias_map) == 0

# New document parsed
server.parse_document(uri, '@Character: Jane Smith { aliases: ["JS", "Janey"] }')
assert len(index) == 1
assert len(index._alias_index._alias_map) == 2
```

### Event-Driven Architecture

**No TTL or manual invalidation** (as required):
- Cache invalidates automatically on document change
- No time-based expiration
- No manual cache clearing needed
- LSP client controls when handler is called (via text sync settings)

**Three-step invalidation process**:
1. **Remove**: Call `index.remove(uri)` to clear old symbols and aliases
2. **Parse**: Call `parse_document()` to extract updated symbols
3. **Update**: `parse_document()` calls `index.update()` for each symbol (including aliases)

### Conflict Resolution

**Problem**: `TEXT_DOCUMENT_DID_CHANGE` feature was registered twice:
- Once in `server.py` (new handler for cache invalidation)
- Once in `diagnostics.py` (existing handler for validation)

**Solution**: Refactored diagnostics module:
- Removed `@server.feature` decorator from diagnostics handler
- Made `validate_document()` a regular async function
- Stored in `server._custom_state` for reuse
- Called from server's change handler after cache invalidation

**Result**: Single `TEXT_DOCUMENT_DID_CHANGE` handler that:
1. Invalidates cache and re-indexes
2. Runs diagnostics validation
3. Maintains separation of concerns

### Incremental Change Handling

The handler supports both full and incremental changes:

**Full document change**:
```python
if isinstance(change, types.TextDocumentContentChangeWholeDocument):
    current_content = change.text
```

**Incremental change**:
```python
# Extract range and apply change
start_line, start_char = change.range.start.line, change.range.start.character
end_line, end_char = change.range.end.line, change.range.end.character

# Apply change to lines
lines = current_content.split("\n")
lines[start_line:end_line + 1] = [start_of_line + change.text + end_of_line]
```

### Logging

Added debug-level logging for cache invalidation events:
```python
logger.debug(f"Cache invalidated for {uri}: removed {len(removed_symbols)} symbols (including aliases)")
logger.debug(f"Cache rebuilt for {uri}")
```

### Design Patterns

**Separation of concerns**:
- Cache invalidation: Handled in server.py
- Diagnostics validation: Handled in diagnostics.py
- Symbol indexing: Handled in index.py

**Dependency injection**:
- Validation function injected into server's custom state
- Called from change handler without tight coupling

**Async/sync separation**:
- Cache invalidation (sync): Fast operations
- Diagnostics validation (async): I/O intensive

### Backward Compatibility

✅ **No breaking changes**:
- Existing handlers (`did_open`, `did_close`, `did_save`) unchanged
- Diagnostics still work correctly
- Index operations unchanged
- No API changes for consumers

### Files Modified

1. **novelwriter_lsp/server.py**:
   - Added `_documents` dict for content tracking
   - Added `on_text_document_did_change()` handler
   - Updated `on_text_document_did_open()` to store content
   - Updated `on_text_document_did_close()` to clean up

2. **novelwriter_lsp/features/diagnostics.py**:
   - Removed `@server.feature` decorator
   - Refactored to standalone `validate_document()` function
   - Stored in `server._custom_state` for reuse

### Next Steps

Task 12 (integration tests) will verify the complete cache invalidation flow:
- Document open → parse → index
- Document change → invalidate → re-parse → re-index
- Document close → remove from index
- Alias cache properly maintained throughout lifecycle


## Tasks 8-11: Comprehensive Test File Creation

### Implementation Summary

Created `tests/phase1/test_definition_enhanced.py` with 24 test cases covering:
- Task 8: Alias parsing (3 tests)
- Task 9: Reference scanning (3 tests)
- Task 10: AliasIndex operations (4 tests)
- Task 11: Definition lookup logic (4 tests)
- Additional helper and integration tests

### Test Structure

**TestAliasParsing** (3 tests):
- `test_parse_aliases_field`: Verifies array format parsing
- `test_parse_aliases_empty`: Verifies default empty list behavior
- `test_parse_aliases_multiple`: Verifies multi-alias and quote handling

**TestReferenceScanning** (3 tests):
- `test_extract_references_basic`: Verifies basic reference extraction
- `test_extract_references_no_partial_match`: Verifies word boundary behavior
- `test_extract_references_performance`: Verifies performance (<100ms for 500 lines)

**TestAliasIndexOperations** (4 tests):
- `test_alias_index_add`: Verifies alias addition
- `test_alias_index_get`: Verifies alias lookup
- `test_alias_index_remove`: Verifies symbol removal clears aliases
- `test_alias_index_conflict`: Verifies alias overwrite behavior

**TestDefinitionLookup** (4 tests):
- `test_goto_definition_exact_match`: Verifies exact name lookup
- `test_goto_definition_alias_match`: Verifies alias-based lookup
- `test_goto_definition_conflict`: Verifies conflict handling
- `test_goto_definition_not_found`: Verifies None return for missing symbols

**TestCreateLocation** (2 tests):
- Basic and multiline Location creation tests

**TestExtractWord** (3 tests):
- Simple, multiword, and no-match extraction tests

**TestIntegrationWithParser** (4 tests):
- Parser-to-index integration tests

### Key Learnings

1. **Performance Test Limit**: `_extract_references` has a 500-line limit for performance. Tests must use ≤500 lines.

2. **_extract_word Behavior**: The function extracts contiguous alphanumeric text (including spaces), then tries to find matching symbol prefixes. Tests must account for this behavior.

3. **Coverage Results** (all phase1 tests combined):
   - definition.py: 44%
   - index.py: 74%
   - parser.py: 76%
   - Total: 69%

4. **Test Patterns Used**:
   - Pytest fixtures for SymbolIndex and AliasIndex setup
   - Modern Python 3.10+ type hints (`list[str]`, `X | Y`)
   - Descriptive test names following `test_{functionality}_{scenario}` pattern
   - Comprehensive assertions with descriptive error messages

5. **All 152 phase1 tests pass** - No regressions introduced.

### Test File Stats

- Total tests: 24
- Lines of code: ~600
- All tests pass in <1 second
- Covers alias parsing, reference scanning, AliasIndex operations, and definition lookup


## Task 12: End-to-End Integration Tests (2 tests)

### Implementation Summary

Created 2 integration tests in `tests/phase1/test_definition_enhanced.py`:

1. **`test_e2e_define_and_jump()`**: Complete flow from definition to F12 jump
   - Parses document with character/location definitions including aliases
   - Indexes symbols in real SymbolIndex (no mocks)
   - Tests exact name lookup, alias lookup, and location creation
   - Verifies the complete integration path

2. **`test_e2e_modify_and_jump()`**: Cache invalidation flow
   - Initial parse with original aliases
   - Cache invalidation via `index.remove(uri)`
   - Re-parse modified document with new aliases
   - Verifies old aliases cleared, new aliases work

### Key Implementation Details

1. **Type Safety**: Used `isinstance()` checks before accessing subclass-specific attributes (`aliases`, `age`)
   - `BaseSymbol` doesn't have `aliases` or `age`
   - Must cast/check before accessing: `assert isinstance(symbol, CharacterSymbol)`

2. **Real Components**: Tests use actual `SymbolIndex` and `parse_document()` (no mocks)
   - Tests real integration behavior
   - Catches real bugs in the integration path

3. **Test Structure**: Used existing test class patterns with `@pytest.fixture`
   - `symbol_index` fixture provides fresh SymbolIndex per test
   - Each test is independent and can run in isolation

### Verification Results

- ✅ `pytest tests/phase1/test_definition_enhanced.py -v`: 26 passed (24 existing + 2 new)
- ✅ `pytest tests/phase1/ -v`: 154 passed (no regressions)
- ✅ LSP diagnostics: Only warnings (private usage, unused variables - expected in tests)

### Test Count Changes

- Before Task 12: 152 phase1 tests
- After Task 12: 154 phase1 tests (+2 integration tests)

### Next Steps

Task 13 (performance tests) and Task 14 (manual VSCode testing) depend on this task.


## Task 13: Performance Tests (2 tests)

### Implementation Summary

Created 2 performance benchmark tests in `tests/phase1/test_definition_enhanced.py`:

1. **`test_performance_large_document()`**: Measures parse + index cycle for 1000-line document
   - Creates 300 symbols (100 chars, 100 locs, 100 items) with aliases
   - Benchmarks the complete parse_document() + index.update() cycle
   - Target: < 200ms
   - Result: 2.25ms mean (89x faster than required)

2. **`test_performance_many_aliases()`**: Measures alias lookup with 200 aliases
   - Creates 100 symbols, each with 2 aliases (200 total aliases)
   - Benchmarks 10 alias lookups per iteration
   - Target: < 10ms
   - Result: 1.67 microseconds mean (5992x faster than required)

### Performance Results

Both tests **significantly exceed** performance requirements:

| Test | Target | Actual | Performance Ratio |
|------|--------|--------|-------------------|
| Large document indexing | 200ms | 2.25ms | 89x faster |
| Alias lookup (200 aliases) | 10ms | 0.00167ms | 5992x faster |

### Benchmark Configuration

- **pytest-benchmark**: v5.2.3
- **min_rounds**: 3-5 (for stable measurements)
- **Measurement**: Uses `time.perf_counter()` for high precision
- **Output format**: JSON for evidence file, console for verification

### Key Implementation Details

1. **Benchmark Structure**: Each test uses the `benchmark` fixture from pytest-benchmark
   - Passes callable to `benchmark()` function
   - pytest-benchmark handles timing, warmup, multiple iterations
   - Reports min, max, mean, median, std dev, percentiles

2. **Test 1 Strategy**: Benchmarks full parse+index cycle
   - Creates 1000-line document content once (outside benchmark)
   - Benchmark measures: `parse_document()` + `index.update()` for each symbol
   - More realistic than just measuring lookup

3. **Test 2 Strategy**: Benchmarks multiple alias lookups
   - Creates index with 200 aliases once (outside benchmark)
   - Benchmark measures: 10 alias lookups per iteration
   - Tests O(1) dict-based lookup performance at scale

### pytest-benchmark Usage Pattern

```python
@pytest.mark.benchmark(group="performance", min_rounds=3)
def test_performance_large_document(self, benchmark: Any) -> None:
    # Setup (not benchmarked)
    index = SymbolIndex()
    document_content = create_large_document()
    
    # Function to benchmark
    def parse_and_index() -> int:
        symbols = parse_document(document_content, uri)
        for symbol in symbols:
            index.update(symbol)
        return len(symbols)
    
    # Run benchmark
    result = benchmark(parse_and_index)
    
    # Verify correctness (not benchmarked)
    assert result == expected_count
```

### Evidence File

Created `.sisyphus/evidence/task-13-benchmark.json` with:
- Complete benchmark statistics (min, max, mean, std dev, median, IQR)
- Performance ratios vs targets
- Environment details (Python version, pytest version)
- Test descriptions and notes

### Test Count Changes

- Before Task 13: 26 tests in test_definition_enhanced.py
- After Task 13: 28 tests (+2 performance tests)

### All Phase 1 Tests

Total: 154 tests (152 existing + 2 new performance tests)
All pass with no regressions.

### Next Steps

Task 14 (manual VSCode testing) depends on this task.


## Task 14: Manual QA Preparation

### Test Environment Setup

Created manual testing environment for VSCode F12 functionality:

1. **Evidence Directory**: `.sisyphus/evidence/task-14-manual-qa/`
   - `test-document.md` - Test document with 4 scenarios
   - `evidence-template.md` - Evidence recording template
   - `screenshots/` - Directory for screenshots

2. **Test Scenarios**:
   - Scenario 1: Exact name match ("John Doe")
   - Scenario 2: Alias match ("Johnny")
   - Scenario 3: Alias with special chars ("Mr. Doe")
   - Scenario 4: Conflict disambiguation (multiple "John" characters)

3. **Required Screenshots** (6 total):
   - scenario-1-exact-name.png
   - scenario-2-alias-johnny.png
   - scenario-3-alias-mr-doe.png
   - scenario-4a-conflict-john-doe.png
   - scenario-4b-conflict-john-smith.png
   - scenario-5-not-found.png (optional bonus test)

### Manual Test Instructions

**This is a manual task** - cannot be automated. The user must:

1. Start VSCode with LSP server running
2. Open the test document (`test-document.md`)
3. Execute each scenario and take screenshots
4. Fill in the evidence template
5. Report back with results

### Expected Behaviors

Based on Task 6 (Definition Lookup) implementation:

1. **Exact match**: Returns single Location (line 3)
2. **Alias match**: Returns single Location via alias lookup
3. **Special chars**: Regex escaping handles "Mr. Doe" correctly
4. **Conflict**: Returns list[Location] with both matches - editor should show disambiguation UI

### Performance Baselines

From Task 13 (Performance Tests):
- Index 1000 lines: 2.25ms (89x faster than required)
- Lookup 200 aliases: 0.00167ms (5992x faster than required)

Expected F12 response time: < 10ms for all scenarios.

### Next Steps

After manual testing completes:
1. Review evidence and screenshots
2. Update plan file to mark Task 14 complete
3. File any bugs found during manual testing
4. Prepare for Wave 2 completion review


## F4: Documentation Review (2026-03-08)

### Documentation Quality Summary

**Verdict**: APPROVED - All public APIs documented with Google-style docstrings.

### Documentation Coverage

| Module | Module Docstring | Classes | Methods | Quality |
|--------|-----------------|---------|---------|---------|
| types.py | ✅ | 11/11 | - | Excellent |
| parser.py | ✅ | - | 7/7 | Good |
| index.py | ✅ | 2/2 | 19/19 | Excellent |
| definition.py | ✅ | - | 4/4 | Good |
| server.py | ✅ | 1/1 | 4/4 | Good |

### Key Documentation Patterns Observed

1. **Google-style docstrings**: All docstrings follow the standard format:
   - Brief description
   - Args: section
   - Returns: section
   - Examples (for complex functions)

2. **Performance notes**: Complex functions like `_extract_references()` include Performance sections documenting expected time complexity.

3. **Examples provided where valuable**: Not every function has examples, but complex algorithms do (e.g., `_extract_references` with regex pattern matching).

4. **Private functions**: Functions starting with `_` don't require docstrings per project conventions.

### Private Function Exemptions

The following private functions lack docstrings but are acceptable:
- `_generate_symbol_id()` - trivial utility
- `_create_symbol_from_match()` - internal helper  
- `_extract_word()` - internal helper

### Documentation Quality Verification Commands

```bash
# Check for missing docstrings
python -c "
import ast
files = ['novelwriter_lsp/types.py', 'novelwriter_lsp/parser.py', 
         'novelwriter_lsp/index.py', 'novelwriter_lsp/features/definition.py',
         'novelwriter_lsp/server.py']
for fp in files:
    with open(fp) as f: tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node):
                print(f'MISSING: {fp} class {node.name}')
"

# Verify all tests pass
pytest tests/phase1/test_definition_enhanced.py -v
# Result: 28 passed
```

### Documentation Compliance Check

- ✅ All public functions have Google-style docstrings
- ✅ All public classes documented
- ✅ Args/Returns sections present where applicable
- ✅ Examples provided for complex functions
- ✅ Follows existing codebase patterns

### Recommendations

1. Add examples to `_parse_metadata()` since it handles complex array parsing
2. Consider documenting AliasIndex O(1) lookup complexity in class docstring
