# NovelWriter LSP Server

专为小说和创意写作设计的自定义语言服务器协议 (LSP) 服务器，提供智能符号管理、一致性检查和 AI 辅助功能。

## 功能特性

### LSP 核心功能

| LSP 功能 | 描述 | 状态 |
|----------|------|------|
| `goto_definition` | 从角色/地点引用跳转到其定义 | ✅ 已实现 |
| `find_references` | 查找符号在文档中的所有引用 | ✅ 已实现 |
| `documentSymbol` | 显示章节、角色、地点等的文档大纲 | ✅ 已实现 |
| `rename` | 全局重命名角色/地点及其所有引用 | ✅ 已实现 |
| `diagnostics` | 实时一致性检查和错误诊断 | ✅ 已实现 |
| `hover` | 悬停显示符号详细属性 | ✅ 已实现 |
| `completion` | 智能补全建议 | ✅ 已实现 |
| `codeLens` | 可点击按钮触发 Agent 操作 | ✅ 已实现 |

### Agent 系统

- **BaseAgent** - 所有 Agent 的基础类
- **ValidatorAgent** - 一致性校验代理，检测角色状态不一致、事件细节矛盾等
- **UpdaterAgent** - 内存更新代理，从章节提取结构化信息并更新数据库

### 存储系统

- **Neo4j** - 图数据库，存储角色、关系和情节结构
- **PostgreSQL** - 关系数据库，存储元数据和结构化信息
- **Milvus** - 向量数据库，用于事件档案的语义搜索

## 符号类型

NovelWriter LSP 支持 9 种符号类型：

| 符号类型 | 描述 | 语法示例 |
|----------|------|----------|
| `@Character` | 小说中的人物、生物、实体 | `@Character: John Doe { age: 42, status: "alive" }` |
| `@Location` | 地点和场景 | `@Location: The Rusty Anchor Pub { city: "Boston" }` |
| `@Item` | 重要物品 | `@Item: The Crystal Key { owner: "John Doe" }` |
| `@Lore` | 世界观设定、规则、历史 | `@Lore: Magic System { rules: [...] }` |
| `@PlotPoint` | 伏笔、呼应、关键事件 | `@PlotPoint: The Inciting Incident { chapter: 1 }` |
| `@Outline` | 三级大纲（总纲 → 卷 → 章） | `@Outline: Master Outline { level: "master" }` |
| `@Event` | 故事事件（时间线追踪） | `@Event: The Meeting { chapter: 1, location: "The Rusty Anchor Pub" }` |
| `@Relationship` | 角色之间的关系 | `@Relationship: John → Jane { type: "lover" }` |
| `@Chapter` | 小说章节 | `@Chapter: Chapter 1 { word_count: 2500 }` |

## 使用示例

```markdown
# Novel: The Rusty Detective

@Character: John Doe { 
    description: "A rugged detective with a past", 
    age: 42,
    status: "alive",
    occupation: "Private Investigator"
}

@Location: The Rusty Anchor Pub { 
    city: "Boston",
    description: "A dimly lit waterfront bar"
}

## Chapter 1

John Doe walked into The Rusty Anchor Pub. The air smelled of stale beer and old wood.

@Event: John Meets Client {
    chapter: 1,
    location: "The Rusty Anchor Pub",
    participants: ["John Doe", "Jane Smith"],
    description: "Jane hires John to find her missing sister"
}
```

## 安装与开发

### 安装依赖

```bash
# 克隆仓库
git clone <repository-url>
cd NovelWriter/LSP

# 安装 Python 依赖
pip install -r requirements.txt
```

### 运行服务器

```bash
# 启动 LSP 服务器
python -m novelwriter_lsp
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 按阶段运行测试
pytest tests/phase1/  # Phase 1: MVP 基础功能
pytest tests/phase2/  # Phase 2: 数据库集成
pytest tests/phase3/  # Phase 3: Agent 系统
pytest tests/phase4/  # Phase 4: 高级功能
```

## 项目结构

```
lsp/
├── novelwriter_lsp/          # Python 包
│   ├── __init__.py           # 包初始化
│   ├── __main__.py           # 命令行入口
│   ├── server.py             # 主 LSP 服务器
│   ├── types.py              # 核心数据类和类型
│   ├── parser.py             # Markdown 解析器
│   ├── index.py              # 符号索引管理（带 LRU 缓存）
│   ├── features/             # LSP 功能处理器
│   │   ├── __init__.py
│   │   ├── definition.py     # goto_definition
│   │   ├── references.py     # find_references
│   │   ├── symbols.py        # documentSymbol
│   │   ├── rename.py         # rename
│   │   ├── diagnostics.py    # 实时诊断
│   │   ├── hover.py          # 悬停信息
│   │   ├── completion.py     # 智能补全
│   │   └── codelens.py       # CodeLens 按钮
│   ├── agents/               # Agent 系统
│   │   ├── __init__.py
│   │   ├── base.py           # BaseAgent
│   │   ├── validator.py      # ValidatorAgent
│   │   └── updater.py        # UpdaterAgent
│   └── storage/              # 存储系统
│       ├── __init__.py
│       ├── neo4j_client.py   # Neo4j 客户端
│       ├── postgres_client.py # PostgreSQL 客户端
│       ├── milvus_client.py  # Milvus 客户端
│       └── symbol_graph_client.py # 符号图客户端
├── tests/                     # 测试套件（200+ 测试）
│   ├── conftest.py
│   ├── phase1/               # Phase 1 测试
│   ├── phase2/               # Phase 2 测试
│   ├── phase3/               # Phase 3 测试
│   └── phase4/               # Phase 4 测试
├── pyproject.toml            # Python 项目配置
├── requirements.txt          # 依赖列表
└── README.md                 # 本文档
```

## 架构概述

### 三层架构

1. **解析层** - Markdown 文本解析，提取符号定义和引用
2. **索引层** - 内存索引（LRU 缓存）+ 持久化存储
3. **功能层** - LSP 处理器实现各种功能

### 数据流向

```
文本变更 → 解析器 → 索引更新 → Agent 处理 → 诊断推送
                ↓
            数据库存储（Neo4j/PostgreSQL/Milvus）
```

## 开发状态

- ✅ **Phase 1**: MVP 基础框架（已完成）
- ✅ **Phase 2**: 数据库集成（已完成）
- ✅ **Phase 3**: Agent 系统（已完成）
- ✅ **Phase 4**: 高级功能（已完成）
- ✅ **200+ 测试通过**

## 许可证

ISC
