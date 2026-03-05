# Naming Decision: NovelWriter LSP

**Date**: 2026-03-05  
**Decision**: Official service name

## Selected Name

**NovelWriter LSP**

## Rationale

1. **Semantic Clarity**: Novel (小说) + Writer (作者/写作工具)
2. **Professional**: Sounds like a 正式 writing tool
3. **Memorable**: 3 words, easy to remember
4. **International**: English words, suitable for open source
5. **Extensible**: Can 衍生 NovelWriter IDE, NovelWriter CLI, etc.

## Naming Convention

- **Service Name**: NovelWriter LSP
- **Python Package**: `novelwriter-lsp`
- **Import**: `from novelwriter_lsp import NovelWriterServer`
- **CLI Command**: `novelwriter-lsp`
- **Class Name**: `NovelWriterServer`
- **Protocol**: LSP (Language Server Protocol) - unchanged

## Rejected Alternatives

1. **Novelist LSP** - Good but less clear about tool nature
2. **Muse LSP** - Too ambiguous, not directly about writing
3. **StoryForge LSP** - Too industrial, less elegant
4. **PyNovel LSP** - Too technical, less professional

## Brand Guidelines

- Always use "NovelWriter LSP" (capital W, capital L, capital S, capital P)
- In code: `novelwriter_lsp` (snake_case for Python package)
- CLI: `novelwriter-lsp` (kebab-case for commands)
- Class: `NovelWriterServer` (PascalCase)

## Version History

- v1.0 (2026-03-05): Initial naming decision
- Previous: Generic "Python LSP Server"
