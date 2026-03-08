# Decisions - enhance-definition-provider

## [2026-03-08T16:00:00Z] Technical Approach

- Chose manual alias mapping + TDD approach (Plan's Option 1)
- Exact match prioritized over alias match
- Conflict handling: Return Location[] array (let editor handle selection)
- Performance threshold: 500 lines (adjustable)
- Cache invalidation: Event-driven (on document change)
