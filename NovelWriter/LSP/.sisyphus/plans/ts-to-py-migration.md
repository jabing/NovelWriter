# TypeScript LSP to Python pygls 迁移计划

## TL;DR

> **Quick Summary**: 将现有 TypeScript LSP 服务器 (~400 行) 迁移到 Python pygls 框架，并基于设计文档实现完整架构。采用 4 阶段分步执行策略，Phase 1 从最小 MVP 开始验证，后续逐步集成数据库、Agent 和高级功能。
> 
> **Deliverables**:
> - Phase 1: 可运行的 pygls LSP 服务器（基础功能）
> - Phase 2: 数据库集成（Neo4j + Milvus + PostgreSQL）
> - Phase 3: Agent 系统（ValidatorAgent、UpdaterAgent 等）
> - Phase 4: 完整功能（Hover、Completion、Rename、性能优化）
> 
> **Estimated Effort**: XL (4 阶段，~2800+ 行 Python 代码)
> **Parallel Execution**: YES - 4 waves (Phases)
> **Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4

---

## Context

### Original Request
用户要求将 LSP 从 TypeScript 迁移到 Python (pygls)，采用一次性重写策略，删除 TypeScript 版本。

### Interview Summary
**Key Discussions**:
- **Migration strategy**: 一次性重写 - 完全删除 TypeScript，用 Python 重写整个 LSP
- **Framework choice**: pygls - Python 官方 LSP 框架
- **Code reference**: 不保留 TypeScript 版本，直接删除
- **Vector Database**: Milvus（与 Writer 保持一致）
- **Agent Strategy**: 混合策略 - Writer 按升级方案演进，LSP 复用基础 Agent + 新建 LSP 特定 Agent
- **Execution**: 分阶段执行，Phase 1 从最小 MVP 开始

**Research Findings**:
- pygls API: LanguageServer 类 + @server.feature 装饰器
- Types from lsprotocol.types 模块
- Writer 项目已有 Neo4j/PostgreSQL 客户端、内存系统
- Writer 有升级方案文档（Novel Agent System 改进方案文档.md）

### Metis Review
**Identified Gaps** (addressed):
- **Scope mismatch**: TypeScript 代码库 (~400 行简单 LSP) vs 设计文档（复杂架构）→ 用户确认实现完整架构
- **Database status**: Writer 项目已有 Neo4j/PostgreSQL 客户端 → 可复用
- **Agent status**: Writer Agent 与设计文档不完全匹配 → 混合策略（复用 + 新建）
- **Phase 1 scope**: 最初未明确 → 确认为最小 MVP（无数据库无 Agent）

---

## Work Objectives

### Core Objective
基于设计文档（LSP_ARCHITECTURE_REDESIGN.md）和 Writer 升级方案（Novel Agent System 改进方案文档.md），实现完整的 Python LSP 服务器，替代现有 TypeScript 版本。

### Concrete Deliverables
- `novelwriter_lsp/` Python 包（4 个模块：server.py, parser.py, index.py, features/）
- 4 个 Phase 的完整实现和测试
- pytest 测试套件（每个 Phase 至少 5 个测试）
- 删除 TypeScript 代码（package.json, tsconfig.json, src/）

### Definition of Done
- [ ] Phase 4 所有功能在 VS Code 中验证通过
- [ ] 所有 pytest 测试通过
- [ ] TypeScript 代码完全删除
- [ ] 文档更新完成

### Must Have
- pygls v2.x 框架
- 9 种符号类型（Character, Location, Item, Lore, PlotPoint, Outline, Event, Relationship, Chapter）
- 三级大纲支持（总纲 → 卷 → 章）
- 实时诊断（diagnostics）
- CodeLens 按钮（触发 Agent）

### Must NOT Have (Guardrails)
- ❌ 不保留 TypeScript 版本
- ❌ Phase 1 不包含数据库集成（避免范围膨胀）
- ❌ Phase 1 不包含 Agent 集成
- ❌ 不使用 ChromaDB（使用 Milvus 与 Writer 保持一致）
- ❌ 不添加设计文档未要求的新功能

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.
> Acceptance criteria requiring "user manually tests/confirms" are FORBIDDEN.

### Test Decision
- **Infrastructure exists**: NO (LSP 项目无测试基础设施)
- **Automated tests**: YES (TDD) - 每个 Phase 包含 pytest 测试
- **Framework**: pytest
- **If TDD**: 每个任务遵循 RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
每个任务 MUST 包含 agent-executed QA 场景（见 TODO 模板）。
证据保存到 `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: 使用 Playwright（playwright skill）— 导航、交互、断言 DOM、截图
- **TUI/CLI**: 使用 interactive_bash（tmux）— 运行命令、发送 keystrokes、验证输出
- **API/Backend**: 使用 Bash（curl）— 发送请求、断言状态 + 响应字段
- **Library/Module**: 使用 Bash（bun/node REPL）— 导入、调用函数、比较输出

---

## Execution Strategy

### Parallel Execution Waves

> 最大化并行执行。每个 Phase 内部任务可并行，Phase 之间顺序执行。

```
Phase 1 (MVP - 基础框架，可立即开始):
├── Task 1: Python 包结构 + pygls 框架搭建 [quick]
├── Task 2: 符号类型定义 (9 种) [quick]
├── Task 3: Markdown 解析器（正则） [quick]
├── Task 4: 内存索引（LRU 缓存） [quick]
├── Task 5: goto_definition 处理器 [quick]
├── Task 6: find_references 处理器 [quick]
├── Task 7: documentSymbol 处理器 [quick]
└── Task 8: pytest 配置 + 基础测试 [quick]

Phase 2 (After Phase 1 - 数据库集成):
├── Task 9: Milvus 客户端实现 [unspecified-high]
├── Task 10: 复用 Writer Neo4j/PostgreSQL 客户端 [quick]
├── Task 11: 符号持久化到数据库 [deep]
└── Task 12: 数据库测试 [deep]

Phase 3 (After Phase 2 - Agent 系统):
├── Task 13: 复用 Writer 基础 Agent [quick]
├── Task 14: ValidatorAgent 实现 [deep]
├── Task 15: UpdaterAgent 实现 [deep]
├── Task 16: diagnostics 实时诊断 [deep]
└── Task 17: CodeLens 按钮 [unspecified-high]

Phase 4 (After Phase 3 - 高级功能):
├── Task 18: Hover 信息 [quick]
├── Task 19: Completion 智能补全 [unspecified-high]
├── Task 20: Rename 批量重命名 [deep]
├── Task 21: 性能优化（增量解析） [deep]
└── Task 22: 最终验证 + 删除 TypeScript [quick]

Critical Path: Task 1 → Task 8 → Task 9 → Task 11 → Task 14 → Task 16 → Task 20 → Task 22
Parallel Speedup: ~60% faster than sequential (within each Phase)
Max Concurrent: 8 (Phase 1)
```

### Dependency Matrix (abbreviated)

- **1-8**: — — 9-12, 1
- **9-12**: 1-8 — 13-17, 2
- **13-17**: 9-12 — 18-22, 3
- **18-22**: 13-17 — Final, 4

### Agent Dispatch Summary

- **Phase 1**: **8** — All tasks → `quick` (基础框架)
- **Phase 2**: **4** — T9 → `unspecified-high`, T10 → `quick`, T11 → `deep`, T12 → `deep`
- **Phase 3**: **5** — T13 → `quick`, T14-T16 → `deep`, T17 → `unspecified-high`
- **Phase 4**: **5** — T18 → `quick`, T19 → `unspecified-high`, T20-T21 → `deep`, T22 → `quick`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info + QA Scenarios.
> **A task WITHOUT QA Scenarios is INCOMPLETE. No exceptions.**

### Phase 1: MVP 基础框架

- [x] 1. Python 包结构 + pygls 框架搭建

  **What to do**:
  - 创建 `novelwriter_lsp/` 包目录结构
  - 创建 `__init__.py`, `__main__.py`, `server.py`
  - 实现基础 LanguageServer 类（继承 pygls.server.LanguageServer）
  - 配置 `pyproject.toml` 和 `requirements.txt`
  - 实现 `python -m novelwriter_lsp` 入口
  - 创建基础测试 `tests/phase1/test_server.py`

  **Must NOT do**:
  - 不包含数据库连接
  - 不包含 Agent 集成
  - 不实现复杂功能（仅框架搭建）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 基础框架搭建，模式化任务

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 1 (with Tasks 2-8)
  - **Blocks**: Tasks 9-22 (all subsequent phases)
  - **Blocked By**: None

  **References**:
  - `pygls` official docs: https://pygls.readthedocs.io/en/latest/
  - `Writer/src/db/neo4j_client.py`:1-50 - Python 包结构和导入模式
  - TypeScript `src/server.ts:1-30` - 现有 LSP 服务器结构参考

  **Acceptance Criteria**:
  - [ ] `novelwriter_lsp/` 包可导入
  - [ ] `python -m novelwriter_lsp` 启动无错误
  - [ ] `pyproject.toml` 包含 pygls 依赖
  - [ ] `pytest tests/phase1/test_server.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Server starts successfully
    Tool: interactive_bash (tmux)
    Preconditions: Python 3.14.2, pygls installed
    Steps:
      1. Run: python -m novelwriter_lsp --help
      2. Verify: Exit code 0
      3. Verify: Output contains "NovelWriter LSP Server"
    Expected Result: Server help message displayed, exit code 0
    Evidence: .sisyphus/evidence/task-1-server-start.txt

  Scenario: Package imports correctly
    Tool: Bash (Python REPL)
    Preconditions: Package installed
    Steps:
      1. Run: python -c "from novelwriter_lsp import server; print('OK')"
      2. Verify: Output is "OK"
      3. Verify: Exit code 0
    Expected Result: Import successful, no errors
    Evidence: .sisyphus/evidence/task-1-import-check.txt
  ```

  **Commit**: YES (groups with 2-8)
  - Message: `feat(lsp): Python package structure and pygls foundation`
  - Files: `novelwriter_lsp/`, `pyproject.toml`, `requirements.txt`, `tests/phase1/`
  - Pre-commit: `pytest tests/phase1/`

- [x] 2. 符号类型定义 (9 种)

  **What to do**:
  - 创建 `novelwriter_lsp/types.py`
  - 定义 9 种 SymbolType enum (Character, Location, Item, Lore, PlotPoint, Outline, Event, Relationship, Chapter)
  - 定义 OutlineLevel enum (Master, Volume, Chapter)
  - 定义 BaseSymbol dataclass
  - 定义 9 种具体符号类型 (CharacterSymbol, LocationSymbol, etc.)
  - 创建测试 `tests/phase1/test_types.py`

  **Must NOT do**:
  - 不添加设计文档未要求的符号类型
  - 不包含数据库相关字段（Phase 1 仅内存）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 数据类型定义，模式化任务

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 1 (with Tasks 1, 3-8)
  - **Blocks**: Tasks 3-22 (all use types)
  - **Blocked By**: None

  **References**:
  - `LSP_ARCHITECTURE_REDESIGN.md:156-250` - 符号类型系统设计
  - `Writer/src/memory/base.py` - Python dataclass 模式
  - TypeScript `src/types.ts:1-25` - 现有类型定义参考

  **Acceptance Criteria**:
  - [ ] 9 种 SymbolType 定义完整
  - [ ] BaseSymbol 包含所有必需字段
  - [ ] 所有具体符号类型继承 BaseSymbol
  - [ ] `pytest tests/phase1/test_types.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Symbol types are correctly defined
    Tool: Bash (Python REPL)
    Preconditions: Package installed
    Steps:
      1. Run: python -c "from novelwriter_lsp.types import SymbolType; print(len(SymbolType))"
      2. Verify: Output is "9"
      3. Verify: All 9 types accessible
    Expected Result: 9 symbol types defined
    Evidence: .sisyphus/evidence/task-2-types-check.txt
  ```

  **Commit**: YES (groups with 1, 3-8)

- [x] 3. Markdown 解析器（正则）

  **What to do**:
  - 创建 `novelwriter_lsp/parser.py`
  - 实现正则 patterns 匹配 9 种符号定义
  - 实现 `parse_document(content: str) -> List[BaseSymbol]`
  - 实现 `parse_incremental()` 支持增量解析（预留接口）
  - 创建测试 `tests/phase1/test_parser.py`

  **Must NOT do**:
  - 不使用复杂 Markdown 解析库（保持简单正则）
  - 不实现跨文件解析（单文件范围）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 正则解析，模式匹配

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 1 (with Tasks 1-2, 4-8)
  - **Blocks**: Tasks 4-8 (depend on parser)
  - **Blocked By**: Task 2 (types)

  **References**:
  - TypeScript `src/parser/index.ts:6-42` - 正则 patterns 参考
  - `LSP_ARCHITECTURE_REDESIGN.md:390-430` - 文档解析层设计
  - `Writer/src/novel/validators.py:1-50` - Python 正则模式

  **Acceptance Criteria**:
  - [ ] 所有 9 种符号类型可正确解析
  - [ ] 正则 patterns 与 TypeScript 版本行为一致
  - [ ] 支持属性解析（如 `@Character: Name { age: 25 }`）
  - [ ] `pytest tests/phase1/test_parser.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Parse character definition
    Tool: Bash (Python REPL)
    Preconditions: Parser module imported
    Steps:
      1. Run: python -c "from novelwriter_lsp.parser import parse_document; symbols = parse_document('@Character: John Doe { age: 42 }'); print(len(symbols))"
      2. Verify: Output is "1"
      3. Verify: symbol.name == "John Doe", symbol.type == "character"
    Expected Result: Character parsed correctly
    Evidence: .sisyphus/evidence/task-3-parse-character.txt

  Scenario: Parse chapter outline
    Tool: Bash (Python REPL)
    Preconditions: Parser module imported
    Steps:
      1. Run: python -c "from novelwriter_lsp.parser import parse_document; symbols = parse_document('# Chapter 1\n## Section 1'); print(len(symbols))"
      2. Verify: Output is "2"
    Expected Result: Chapter and section parsed
    Evidence: .sisyphus/evidence/task-3-parse-outline.txt
  ```

  **Commit**: YES (groups with 1-2, 4-8)

- [ ] 4. 内存索引（LRU 缓存）

  **What to do**:
  - 创建 `novelwriter_lsp/index.py`
  - 实现 SymbolIndex 类（使用 OrderedDict 实现 LRU）
  - 实现 `update()`, `remove()`, `get_symbol()`, `search()` 方法
  - 实现位置索引（uri -> symbol_names 映射）
  - 创建测试 `tests/phase1/test_index.py`

  **Must NOT do**:
  - 不包含数据库持久化（Phase 1 仅内存）
  - 不使用外部缓存库（标准库实现）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 数据结构实现

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 1 (with Tasks 1-3, 5-8)
  - **Blocks**: Tasks 5-8 (depend on index)
  - **Blocked By**: Tasks 2-3 (types, parser)

  **References**:
  - `LSP_ARCHITECTURE_REDESIGN.md:495-540` - 符号索引层设计
  - TypeScript `src/index/index.ts:1-83` - 现有索引实现参考
  - `Writer/src/memory/composite_memory.py:1-50` - Python 内存管理模式

  **Acceptance Criteria**:
  - [ ] LRU 缓存工作正常（达到 max_size 后淘汰最旧）
  - [ ] update() 正确添加/更新符号
  - [ ] get_symbol() 优先返回缓存
  - [ ] `pytest tests/phase1/test_index.py` 通过

  **QA Scenarios**:
  ```
  Scenario: LRU eviction works
    Tool: Bash (Python REPL)
    Preconditions: Index created with max_size=3
    Steps:
      1. Add 4 symbols
      2. Verify: First symbol evicted
      3. Verify: Cache size is 3
    Expected Result: LRU eviction works correctly
    Evidence: .sisyphus/evidence/task-4-lru-eviction.txt
  ```

  **Commit**: YES (groups with 1-3, 5-8)

- [ ] 5. goto_definition 处理器

  **What to do**:
  - 创建 `novelwriter_lsp/features/definition.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_DEFINITION)`
  - 实现 `goto_definition(params)` 函数
  - 从索引查询符号定义位置
  - 返回 LSP Location 格式
  - 创建测试 `tests/phase1/test_definition.py`

  **Must NOT do**:
  - 不处理跨文件跳转（Phase 1 单文件）
  - 不处理未找到符号的复杂逻辑（返回 None）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: LSP 标准功能实现

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 1 (with Tasks 1-4, 6-8)
  - **Blocks**: None
  - **Blocked By**: Tasks 1-4 (framework, types, parser, index)

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/goto.html
  - TypeScript `src/server.ts:105-114` - 现有定义跳转实现
  - `LSP_ARCHITECTURE_REDESIGN.md:542-580` - goto_definition 实现示例

  **Acceptance Criteria**:
  - [ ] 点击符号跳转到定义位置
  - [ ] 未找到符号返回 None
  - [ ] 返回正确的 LSP Location 格式
  - [ ] `pytest tests/phase1/test_definition.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Goto definition on character
    Tool: Bash (Python test)
    Preconditions: Document with @Character: John Doe
    Steps:
      1. Open document, call goto_definition at "John Doe" reference
      2. Verify: Returns Location with definition range
      3. Verify: Location.uri matches document URI
    Expected Result: Correct definition location returned
    Evidence: .sisyphus/evidence/task-5-goto-def.txt
  ```

  **Commit**: YES (groups with 1-4, 6-8)

- [ ] 6. find_references 处理器

  **What to do**:
  - 创建 `novelwriter_lsp/features/references.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_REFERENCES)`
  - 实现 `find_references(params)` 函数
  - 从索引查询所有引用位置
  - 返回 LSP Location 列表
  - 创建测试 `tests/phase1/test_references.py`

  **Must NOT do**:
  - 不处理跨文件引用（Phase 1 单文件）
  - 不包含定义本身（仅引用）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: LSP 标准功能实现

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 1 (with Tasks 1-5, 7-8)
  - **Blocks**: None
  - **Blocked By**: Tasks 1-4 (framework, types, parser, index)

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/goto.html
  - TypeScript `src/server.ts:116-125` - 现有引用查找实现
  - `LSP_ARCHITECTURE_REDESIGN.md:582-620` - find_references 实现示例

  **Acceptance Criteria**:
  - [ ] 返回符号的所有引用位置
  - [ ] 不包含定义本身（或明确包含，保持与 TypeScript 一致）
  - [ ] 返回正确的 LSP Location 列表格式
  - [ ] `pytest tests/phase1/test_references.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Find all references
    Tool: Bash (Python test)
    Preconditions: Document with @Character: John Doe and 2 references
    Steps:
      1. Call find_references at "John Doe"
      2. Verify: Returns 3 locations (definition + 2 references, or 2 if excluding definition)
      3. Verify: All locations have correct URI and range
    Expected Result: All references found
    Evidence: .sisyphus/evidence/task-6-find-refs.txt
  ```

  **Commit**: YES (groups with 1-5, 7-8)

- [ ] 7. documentSymbol 处理器

  **What to do**:
  - 创建 `novelwriter_lsp/features/symbols.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)`
  - 实现 `document_symbol(params)` 函数
  - 构建层级结构（# Chapter → ## Section）
  - 返回 LSP DocumentSymbol 列表
  - 创建测试 `tests/phase1/test_symbols.py`

  **Must NOT do**:
  - 不实现跨文件大纲（单文件范围）
  - 不实现三级大纲树（Phase 1 简单层级）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: LSP 标准功能实现

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 1 (with Tasks 1-6, 8)
  - **Blocks**: None
  - **Blocked By**: Tasks 1-4 (framework, types, parser, index)

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/symbols.html
  - TypeScript `src/server.ts:127-140` - 现有文档大纲实现
  - `LSP_ARCHITECTURE_REDESIGN.md:622-695` - documentSymbol 实现示例

  **Acceptance Criteria**:
  - [ ] 返回文档中所有符号（章节、角色等）
  - [ ] 支持层级结构（children）
  - [ ] 正确的 SymbolKind 映射
  - [ ] `pytest tests/phase1/test_symbols.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Document symbols with hierarchy
    Tool: Bash (Python test)
    Preconditions: Document with # Chapter 1 and ## Section 1
    Steps:
      1. Call document_symbol
      2. Verify: Returns 2 symbols (chapter and section)
      3. Verify: Section is child of chapter (or sibling with correct kind)
    Expected Result: Hierarchical symbols returned
    Evidence: .sisyphus/evidence/task-7-doc-symbols.txt
  ```

  **Commit**: YES (groups with 1-6, 8)

- [ ] 8. pytest 配置 + 基础测试

  **What to do**:
  - 创建 `pytest.ini` 或 `pyproject.toml` 配置
  - 创建 `tests/conftest.py` 共享 fixtures
  - 创建 `tests/phase1/` 测试目录
  - 为 Tasks 1-7 编写测试
  - 实现 CI 测试命令

  **Must NOT do**:
  - 不包含集成测试（Phase 1 单元测试）
  - 不使用复杂 mock（简单测试）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 测试配置

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on all Phase 1 tasks)
  - **Parallel Group**: Phase 1 (final task)
  - **Blocks**: Phase 2 tasks
  - **Blocked By**: Tasks 1-7

  **References**:
  - `Writer/tests/conftest.py` - pytest fixtures 模式
  - `Writer/tests/db/test_neo4j_client.py` - 测试结构参考
  - `pygls` examples: https://github.com/openlawlibrary/pygls/tree/main/tests

  **Acceptance Criteria**:
  - [ ] `pytest tests/phase1/` 运行所有测试
  - [ ] 所有测试通过（0 failures）
  - [ ] 测试覆盖率 > 80%
  - [ ] CI 命令可用

  **QA Scenarios**:
  ```
  Scenario: Run all Phase 1 tests
    Tool: Bash
    Preconditions: pytest installed, tests written
    Steps:
      1. Run: pytest tests/phase1/ -v
      2. Verify: Exit code 0
      3. Verify: All tests pass (N passed, 0 failed)
    Expected Result: All tests pass
    Evidence: .sisyphus/evidence/task-8-pytest-run.txt
  ```

  **Commit**: YES (groups with 1-7)
  - Message: `feat(lsp): Phase 1 MVP complete with tests`

---

### Phase 2: 数据库集成

- [ ] 9. Milvus 客户端实现

  **What to do**:
  - 创建 `novelwriter_lsp/storage/milvus_client.py`
  - 实现 MilvusClient 类（异步）
  - 实现 `connect()`, `search()`, `insert()` 方法
  - 实现事件档案向量存储
  - 创建测试 `tests/phase2/test_milvus.py`

  **Must NOT do**:
  - 不实现完整 CRUD（仅 LSP 需要的查询）
  - 不使用 ChromaDB（使用 Milvus）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - **Reason**: 数据库客户端实现，需要异步编程

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 2 (with Tasks 10-12)
  - **Blocks**: Task 11 (persistence)
  - **Blocked By**: Phase 1 complete

  **References**:
  - `Writer/src/memory/composite_memory.py:40-70` - Milvus URI 参数模式
  - Milvus official docs: https://milvus.io/docs
  - `Writer/src/db/neo4j_client.py:1-100` - 异步客户端模式

  **Acceptance Criteria**:
  - [ ] MilvusClient 可连接
  - [ ] 支持向量搜索
  - [ ] 支持插入事件档案
  - [ ] `pytest tests/phase2/test_milvus.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Milvus search works
    Tool: Bash (Python test)
    Preconditions: Milvus running, client connected
    Steps:
      1. Insert test event embeddings
      2. Search with query vector
      3. Verify: Returns similar events
    Expected Result: Vector search returns correct results
    Evidence: .sisyphus/evidence/task-9-milvus-search.txt
  ```

  **Commit**: YES (groups with 10-12)

- [ ] 10. 复用 Writer Neo4j/PostgreSQL 客户端

  **What to do**:
  - 复制 `Writer/src/db/neo4j_client.py` 到 `novelwriter_lsp/storage/`
  - 复制 `Writer/src/db/postgres_client.py` 到 `novelwriter_lsp/storage/`
  - 调整导入路径
  - 添加 LSP 特定查询方法（如 `find_references()`）
  - 创建测试 `tests/phase2/test_db_clients.py`

  **Must NOT do**:
  - 不重写客户端（直接复用）
  - 不修改核心逻辑（仅适配）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  - **Reason**: 代码复用和适配

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 2 (with Tasks 9, 11-12)
  - **Blocks**: Task 11 (persistence)
  - **Blocked By**: Phase 1 complete

  **References**:
  - `Writer/src/db/neo4j_client.py` - Neo4j 客户端源码
  - `Writer/src/db/postgres_client.py` - PostgreSQL 客户端源码
  - `LSP_ARCHITECTURE_REDESIGN.md:582-620` - find_references Neo4j 查询示例

  **Acceptance Criteria**:
  - [ ] Neo4j 客户端可连接
  - [ ] PostgreSQL 客户端可连接
  - [ ] `find_references()` 查询返回正确结果
  - [ ] `pytest tests/phase2/test_db_clients.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Neo4j find_references query
    Tool: Bash (Python test)
    Preconditions: Neo4j running with test data
    Steps:
      1. Call client.find_references("John Doe")
      2. Verify: Returns list of reference locations
      3. Verify: Each location has uri, line, start_char, end_char
    Expected Result: References found via Neo4j
    Evidence: .sisyphus/evidence/task-10-neo4j-refs.txt
  ```

  **Commit**: YES (groups with 9, 11-12)

- [ ] 11. 符号持久化到数据库

  **What to do**:
  - 修改 `novelwriter_lsp/index.py` 支持数据库后端
  - 实现 `persist_to_db()` 方法
  - 实现从数据库加载符号
  - 实现重启后符号不丢失
  - 创建测试 `tests/phase2/test_persistence.py`

  **Must NOT do**:
  - 不改变 LSP API（内部实现变更）
  - 不删除内存缓存（数据库 + 缓存混合）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: 核心索引逻辑修改，需要理解缓存 + 数据库交互

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Phase 2 (depends on 9-10)
  - **Blocks**: Phase 3
  - **Blocked By**: Tasks 9-10 (database clients)

  **References**:
  - `LSP_ARCHITECTURE_REDESIGN.md:495-540` - 三层缓存架构
  - `novelwriter_lsp/index.py` (Task 4 output) - 现有索引实现
  - `Writer/src/db/neo4j_models.py` - 数据模型定义

  **Acceptance Criteria**:
  - [ ] 符号保存到数据库
  - [ ] 重启 LSP 后符号从数据库加载
  - [ ] 内存缓存仍然工作（LRU）
  - [ ] `pytest tests/phase2/test_persistence.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Symbols persist across restart
    Tool: Bash (Python test)
    Preconditions: LSP started, symbols added
    Steps:
      1. Add @Character: John Doe
      2. Restart LSP server
      3. Query for "John Doe"
      4. Verify: Symbol found (loaded from database)
    Expected Result: Symbol persists after restart
    Evidence: .sisyphus/evidence/task-11-persistence.txt
  ```

  **Commit**: YES (groups with 9-10, 12)

- [ ] 12. 数据库测试

  **What to do**:
  - 创建 `tests/phase2/` 完整测试套件
  - 实现数据库集成测试
  - 实现 mock 数据库（CI 使用）
  - 添加性能测试（查询延迟 < 目标）
  - 创建测试报告

  **Must NOT do**:
  - 不包含手动测试（全部自动化）
  - 不跳过错误处理测试

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: 测试套件编写，需要覆盖多种场景

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on all Phase 2 tasks)
  - **Parallel Group**: Phase 2 (final task)
  - **Blocks**: Phase 3
  - **Blocked By**: Tasks 9-11

  **References**:
  - `Writer/tests/db/test_neo4j_client.py` - 数据库测试模式
  - `Writer/tests/conftest.py` - fixtures 和 mock
  - `pytest` docs: https://docs.pytest.org/

  **Acceptance Criteria**:
  - [ ] `pytest tests/phase2/` 运行所有测试
  - [ ] 所有测试通过
  - [ ] 性能测试：查询延迟 < 50ms (find_references), < 10ms (goto_definition)
  - [ ] CI 集成测试可用

  **QA Scenarios**:
  ```
  Scenario: Run all Phase 2 tests
    Tool: Bash
    Preconditions: pytest installed, databases running (or mocked)
    Steps:
      1. Run: pytest tests/phase2/ -v
      2. Verify: Exit code 0
      3. Verify: All tests pass
    Expected Result: All Phase 2 tests pass
    Evidence: .sisyphus/evidence/task-12-pytest-phase2.txt
  ```

  **Commit**: YES (groups with 9-11)
  - Message: `feat(lsp): Phase 2 database integration complete`

---

### Phase 3: Agent 系统

- [ ] 13. 复用 Writer 基础 Agent

  **What to do**:
  - 分析 Writer 升级方案（Novel Agent System 改进方案文档.md）
  - 识别可复用的 Agent
  - 复制并适配到 LSP 项目
  - 调整导入路径和依赖
  - 创建测试 `tests/phase3/test_agents.py`

  **Must NOT do**:
  - 不重写 Agent（直接复用）
  - 不修改核心逻辑（仅适配 LSP）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 代码复用和适配

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 3 (with Tasks 14-17)
  - **Blocks**: Tasks 14-17 (depend on base agents)
  - **Blocked By**: Phase 2 complete

  **References**:
  - `Writer/Novel Agent System 改进方案文档.md` - Agent 系统升级方案
  - `Writer/src/agents/` - Writer Agent 源码
  - `LSP_ARCHITECTURE_REDESIGN.md:2-3` - 10 个 Agent 列表

  **Acceptance Criteria**:
  - [ ] 可复用 Agent 已识别
  - [ ] Agent 已复制到 LSP 项目
  - [ ] 导入路径正确
  - [ ] `pytest tests/phase3/test_agents.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Reused agent imports correctly
    Tool: Bash (Python REPL)
    Preconditions: Agents copied to LSP project
    Steps:
      1. Run: python -c "from novelwriter_lsp.agents import <agent_name>; print('OK')"
      2. Verify: Import successful
    Expected Result: Agent imports work
    Evidence: .sisyphus/evidence/task-13-agent-import.txt
  ```

  **Commit**: YES (groups with 14-17)

- [ ] 14. ValidatorAgent 实现

  **What to do**:
  - 创建 `novelwriter_lsp/agents/validator.py`
  - 实现 ValidatorAgent 类
  - 实现 `validate(uri, content)` 方法
  - 集成 ContinuityValidator（复用 Writer）
  - 实现一致性检查（角色状态、事件细节、时间线）
  - 创建测试 `tests/phase3/test_validator.py`

  **Must NOT do**:
  - 不实现完整 AI 校验（使用规则 + Writer 验证器）
  - 不添加设计文档未要求的检查

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: Agent 实现，需要理解校验逻辑

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 3 (with Tasks 13, 15-17)
  - **Blocks**: Task 16 (diagnostics)
  - **Blocked By**: Task 13 (base agents)

  **References**:
  - `Writer/src/novel/validators.py` - ContinuityValidator 源码
  - `LSP_ARCHITECTURE_REDESIGN.md:700-750` - diagnostics 实现示例
  - `Writer/Novel Agent System 改进方案文档.md:50-60` - 校验代理描述

  **Acceptance Criteria**:
  - [ ] ValidatorAgent 可校验章节
  - [ ] 返回 ValidationResult（errors, warnings）
  - [ ] 检测角色状态不一致
  - [ ] `pytest tests/phase3/test_validator.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Validator detects dead character appearing alive
    Tool: Bash (Python test)
    Preconditions: ValidatorAgent initialized, character marked as dead
    Steps:
      1. Call validator.validate() with chapter containing dead character
      2. Verify: Returns error "Dead character appeared alive"
      3. Verify: Error includes line number and character name
    Expected Result: Validation error detected
    Evidence: .sisyphus/evidence/task-14-validator-dead-char.txt
  ```

  **Commit**: YES (groups with 13, 15-17)

- [ ] 15. UpdaterAgent 实现

  **What to do**:
  - 创建 `novelwriter_lsp/agents/updater.py`
  - 实现 UpdaterAgent 类
  - 实现 `extract_and_update(uri, content)` 方法
  - 从章节抽取结构化信息（事件、角色状态、关系）
  - 更新内存系统（Neo4j + Milvus）
  - 创建测试 `tests/phase3/test_updater.py`

  **Must NOT do**:
  - 不实现完整 LLM 抽取（使用规则 + 简单 NLP）
  - 不修改数据库 schema（使用现有模型）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: Agent 实现，需要理解信息抽取和数据库更新

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 3 (with Tasks 13-14, 16-17)
  - **Blocks**: Task 16 (diagnostics)
  - **Blocked By**: Task 13 (base agents)

  **References**:
  - `LSP_ARCHITECTURE_REDESIGN.md:2-4` - 更新代理描述（第四阶段）
  - `Writer/src/novel/validators.py` - 参考验证器结构
  - `Writer/src/db/neo4j_models.py` - 数据模型

  **Acceptance Criteria**:
  - [ ] UpdaterAgent 可抽取事件信息
  - [ ] 更新角色状态到数据库
  - [ ] 更新关系图谱（版本化）
  - [ ] `pytest tests/phase3/test_updater.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Updater extracts new event
    Tool: Bash (Python test)
    Preconditions: UpdaterAgent initialized, chapter with new event
    Steps:
      1. Call updater.extract_and_update() with chapter content
      2. Verify: New event added to Milvus
      3. Verify: Character states updated in Neo4j
    Expected Result: Event extracted and stored
    Evidence: .sisyphus/evidence/task-15-updater-extract.txt
  ```

  **Commit**: YES (groups with 13-14, 16-17)

- [ ] 16. diagnostics 实时诊断

  **What to do**:
  - 创建 `novelwriter_lsp/features/diagnostics.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_DID_CHANGE)`
  - 实现 `on_document_change(params)` 处理器
  - 调用 ValidatorAgent 进行校验
  - 推送 Diagnostic 到客户端
  - 创建测试 `tests/phase3/test_diagnostics.py`

  **Must NOT do**:
  - 不阻塞编辑（异步校验）
  - 不过度推送（去重、节流）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: LSP 诊断功能，需要理解异步和推送机制

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Phase 3 (depends on 14-15)
  - **Blocks**: Phase 4
  - **Blocked By**: Tasks 14-15 (ValidatorAgent, UpdaterAgent)

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/diagnostics.html
  - `LSP_ARCHITECTURE_REDESIGN.md:700-750` - diagnostics 实现示例
  - TypeScript `src/server.ts:94-102` - 现有诊断框架

  **Acceptance Criteria**:
  - [ ] 文档变更时自动触发诊断
  - [ ] ValidatorAgent 校验结果转换为 Diagnostic
  - [ ] 诊断推送到 VS Code
  - [ ] `pytest tests/phase3/test_diagnostics.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Real-time diagnostics on edit
    Tool: Bash (Python test with mock LSP client)
    Preconditions: LSP server running, document open
    Steps:
      1. Edit document to introduce validation error
      2. Wait for diagnostic push
      3. Verify: Diagnostic received with correct message and range
    Expected Result: Diagnostic pushed on edit
    Evidence: .sisyphus/evidence/task-16-diagnostics.txt
  ```

  **Commit**: YES (groups with 13-15, 17)

- [ ] 17. CodeLens 按钮

  **What to do**:
  - 创建 `novelwriter_lsp/features/codelens.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_CODE_LENS)`
  - 实现 `code_lens(params)` 处理器
  - 添加按钮："✓ 运行一致性检查", "↻ 更新内存系统", "↻ 重试生成"
  - 实现 `novel/validateChapter`, `novel/updateMemory`, `novel/retryChapter` 命令
  - 创建测试 `tests/phase3/test_codelens.py`

  **Must NOT do**:
  - 不添加设计文档未要求的按钮
  - 不实现复杂 UI（标准 CodeLens）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - **Reason**: LSP CodeLens 功能，需要理解命令注册和执行

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Phase 3 (depends on 14-15)
  - **Blocks**: Phase 4
  - **Blocked By**: Tasks 14-15 (ValidatorAgent, UpdaterAgent)

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/code-lens.html
  - `LSP_ARCHITECTURE_REDESIGN.md:825-900` - CodeLens 实现示例
  - `LSP_ARCHITECTURE_REDESIGN.md:902-970` - executeCommand 实现示例

  **Acceptance Criteria**:
  - [ ] CodeLens 按钮在章节文件显示
  - [ ] 点击按钮触发对应命令
  - [ ] 命令执行结果显示
  - [ ] `pytest tests/phase3/test_codelens.py` 通过

  **QA Scenarios**:
  ```
  Scenario: CodeLens buttons appear
    Tool: Bash (Python test with mock LSP client)
    Preconditions: LSP server running, chapter file open
    Steps:
      1. Call code_lens request
      2. Verify: Returns 3 CodeLens (validate, update, retry)
      3. Verify: Each has correct command and title
    Expected Result: CodeLens buttons returned
    Evidence: .sisyphus/evidence/task-17-codelens.txt
  ```

  **Commit**: YES (groups with 13-16)
  - Message: `feat(lsp): Phase 3 agent system complete`

---

### Phase 4: 高级功能

- [ ] 18. Hover 信息

  **What to do**:
  - 创建 `novelwriter_lsp/features/hover.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_HOVER)`
  - 实现 `hover(params)` 处理器
  - 显示符号属性（角色年龄、状态等）
  - 创建测试 `tests/phase4/test_hover.py`

  **Must NOT do**:
  - 不显示过多信息（简洁）
  - 不使用复杂格式化（Markdown 支持）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: LSP 标准功能实现

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 4 (with Tasks 19-22)
  - **Blocks**: None
  - **Blocked By**: Phase 3 complete

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/hover.html
  - `LSP_ARCHITECTURE_REDESIGN.md:752-800` - hover 实现示例
  - TypeScript `src/server.ts` - 无现有 hover 实现（新增）

  **Acceptance Criteria**:
  - [ ] 悬停显示符号信息
  - [ ] 信息格式正确（Markdown）
  - [ ] `pytest tests/phase4/test_hover.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Hover shows character info
    Tool: Bash (Python test)
    Preconditions: Document with @Character: John Doe { age: 42 }
    Steps:
      1. Call hover at "John Doe"
      2. Verify: Returns Hover with contents "Character: John Doe\nAge: 42"
    Expected Result: Hover information displayed
    Evidence: .sisyphus/evidence/task-18-hover.txt
  ```

  **Commit**: YES (groups with 19-22)

- [ ] 19. Completion 智能补全

  **What to do**:
  - 创建 `novelwriter_lsp/features/completion.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_COMPLETION)`
  - 实现 `completion(params)` 处理器
  - 触发字符：`@`, `#`, `[`
  - 从索引搜索符号返回补全列表
  - 创建测试 `tests/phase4/test_completion.py`

  **Must NOT do**:
  - 不实现 AI 补全（基于索引）
  - 不显示过多建议（limit=20）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - **Reason**: LSP 补全功能，需要理解触发和搜索逻辑

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 4 (with Tasks 18, 20-22)
  - **Blocks**: None
  - **Blocked By**: Phase 3 complete

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/json_server.py
  - `LSP_ARCHITECTURE_REDESIGN.md:802-850` - completion 实现示例
  - TypeScript `src/server.ts:58-60` - 现有触发字符配置

  **Acceptance Criteria**:
  - [ ] 输入 `@` 触发角色补全
  - [ ] 输入 `#` 触发章节补全
  - [ ] 补全列表包含符号名称和类型图标
  - [ ] `pytest tests/phase4/test_completion.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Completion triggered by @
    Tool: Bash (Python test)
    Preconditions: Document with @Character: John Doe
    Steps:
      1. Call completion at position after "@"
      2. Verify: Returns CompletionList with "John Doe"
      3. Verify: CompletionItem.kind is Class (character)
    Expected Result: Completion suggestions returned
    Evidence: .sisyphus/evidence/task-19-completion.txt
  ```

  **Commit**: YES (groups with 18, 20-22)

- [ ] 20. Rename 批量重命名

  **What to do**:
  - 创建 `novelwriter_lsp/features/rename.py`
  - 注册 `@server.feature(TEXT_DOCUMENT_RENAME)`
  - 实现 `rename(params)` 处理器
  - 重命名定义和所有引用
  - 返回 WorkspaceEdit
  - 创建测试 `tests/phase4/test_rename.py`

  **Must NOT do**:
  - 不重命名不在索引中的符号
  - 不处理跨文件重命名（Phase 4 单文件）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: LSP 重命名功能，需要理解工作区编辑

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Phase 4 (with Tasks 18-19, 21-22)
  - **Blocks**: None
  - **Blocked By**: Phase 3 complete

  **References**:
  - `pygls` docs: https://pygls.readthedocs.io/en/latest/servers/examples/rename.html
  - TypeScript `src/server.ts:142-168` - 现有重命名实现参考
  - `LSP_ARCHITECTURE_REDESIGN.md` - 无详细 rename 示例（参考 TypeScript）

  **Acceptance Criteria**:
  - [ ] 重命名角色名称
  - [ ] 定义和所有引用同时更新
  - [ ] 返回正确的 WorkspaceEdit 格式
  - [ ] `pytest tests/phase4/test_rename.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Rename character
    Tool: Bash (Python test)
    Preconditions: Document with @Character: John Doe and 2 references
    Steps:
      1. Call rename at "John Doe" with newName="Jane Doe"
      2. Verify: WorkspaceEdit contains 3 changes (definition + 2 refs)
      3. Verify: All changes have correct ranges and newText
    Expected Result: Rename applied to all occurrences
    Evidence: .sisyphus/evidence/task-20-rename.txt
  ```

  **Commit**: YES (groups with 18-19, 21-22)

- [ ] 21. 性能优化（增量解析）

  **What to do**:
  - 修改 `novelwriter_lsp/parser.py` 支持增量解析
  - 实现 `parse_incremental(changes)` 方法
  - 只重新解析变更部分
  - 实现缓存失效逻辑
  - 添加性能基准测试
  - 创建测试 `tests/phase4/test_incremental.py`

  **Must NOT do**:
  - 不优化过早（先确保正确性）
  - 不引入复杂依赖（标准库实现）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: 性能优化，需要理解解析器内部和缓存策略

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Phase 4 (final implementation task)
  - **Blocks**: Final verification
  - **Blocked By**: Tasks 18-20 (other Phase 4 features)

  **References**:
  - `LSP_ARCHITECTURE_REDESIGN.md:995-1020` - 增量更新示例
  - `LSP_ARCHITECTURE_REDESIGN.md:1015-1020` - 性能基准目标
  - `novelwriter_lsp/parser.py` (Task 3 output) - 现有解析器实现

  **Acceptance Criteria**:
  - [ ] 增量解析比全量解析快 50%+
  - [ ] 变更检测正确
  - [ ] 缓存失效逻辑正确
  - [ ] 性能基准：goto_definition < 10ms, find_references < 50ms
  - [ ] `pytest tests/phase4/test_incremental.py` 通过

  **QA Scenarios**:
  ```
  Scenario: Incremental parse is faster
    Tool: Bash (Python benchmark)
    Preconditions: Large document (1000+ lines), parser initialized
    Steps:
      1. Make small edit (1 line)
      2. Time incremental parse
      3. Time full parse
      4. Verify: Incremental is 50%+ faster
    Expected Result: Incremental parsing is significantly faster
    Evidence: .sisyphus/evidence/task-21-incremental-benchmark.txt
  ```

  **Commit**: YES (groups with 18-20, 22)

- [ ] 22. 最终验证 + 删除 TypeScript

  **What to do**:
  - 运行所有测试 `pytest tests/`
  - 在 VS Code 中验证所有功能
  - 删除 TypeScript 代码（`src/`, `package.json`, `tsconfig.json`）
  - 更新 README.md
  - 创建发布版本（git tag）

  **Must NOT do**:
  - 不保留 TypeScript 文件（完全删除）
  - 不跳过最终验证

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`git-master`]
  - **Reason**: 清理和发布

  **Parallelization**:
  - **Can Run In Parallel**: NO (final task)
  - **Parallel Group**: Phase 4 (final task)
  - **Blocks**: Final verification wave
  - **Blocked By**: Tasks 18-21 (all Phase 4 features)

  **References**:
  - `git` commands for cleanup
  - Project root files to delete

  **Acceptance Criteria**:
  - [ ] `pytest tests/` 所有测试通过（100% pass）
  - [ ] VS Code 中所有功能验证通过
  - [ ] TypeScript 文件完全删除
  - [ ] README.md 更新为 Python 使用说明
  - [ ] Git tag 创建（v1.0.0）

  **QA Scenarios**:
  ```
  Scenario: All tests pass
    Tool: Bash
    Preconditions: All phases complete
    Steps:
      1. Run: pytest tests/ -v
      2. Verify: Exit code 0
      3. Verify: All tests pass (N passed, 0 failed)
    Expected Result: 100% test pass
    Evidence: .sisyphus/evidence/task-22-all-tests.txt

  Scenario: TypeScript deleted
    Tool: Bash
    Preconditions: All features verified
    Steps:
      1. Run: ls src/ package.json tsconfig.json
      2. Verify: Files not found (deleted)
      3. Verify: Only novelwriter_lsp/ exists
    Expected Result: TypeScript completely removed
    Evidence: .sisyphus/evidence/task-22-ts-deleted.txt
  ```

  **Commit**: YES (standalone)
  - Message: `chore(lsp): remove TypeScript, Phase 4 complete`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `bun test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill if UI)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (features working together, not isolation). Test edge cases: empty state, invalid input, rapid actions. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Phase 1**: `feat(lsp): MVP foundation` — novelwriter_lsp/, pytest config
- **Phase 2**: `feat(lsp): database integration` — Milvus client, persistence
- **Phase 3**: `feat(lsp): agent system` — ValidatorAgent, UpdaterAgent, diagnostics
- **Phase 4**: `feat(lsp): advanced features` — Hover, Completion, Rename, optimization
- **Final**: `chore(lsp): remove TypeScript` — delete src/, package.json, tsconfig.json

---

## Success Criteria

### Verification Commands
```bash
# Phase 1: MVP verification
python -m novelwriter_lsp  # Should start without errors
pytest tests/phase1/       # Should pass all tests

# Phase 2: Database verification
pytest tests/phase2/       # Database integration tests
python -c "from novelwriter_lsp import server; print('OK')"  # Import check

# Phase 3: Agent verification
pytest tests/phase3/       # Agent tests
python -m novelwriter_lsp --validate-chapter chapter1.md  # CLI test

# Phase 4: Full verification
pytest tests/              # All tests
python -m novelwriter_lsp --help  # Help command
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All tests pass (pytest)
- [ ] TypeScript code deleted
- [ ] Documentation updated
- [ ] VS Code integration verified
