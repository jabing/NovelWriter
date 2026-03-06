# NovelWriter LSP 架构设计

> 基于改进方案文档（Novel Agent System 改进方案文档.md）的 LSP 集成方案
> 
> **NovelWriter LSP - Python 实现**  
> 版本：v1.0  
> 日期：2026年3月5日

---

## 一、设计背景与目标

### 1.1 背景

Novel Agent System 是一个完全自动化的 AI 小说写作和发布系统，当前系统包含：

- **10 个专业化 AI 代理**：总规划、分卷规划、章节规划、角色创建、世界观构建、5 位类型作家、校验、更新、发布、市场研究、读者互动
- **OpenViking 内存系统**：角色记忆、剧情记忆、世界观记忆
- **存储架构**：PostgreSQL + Milvus/ChromaDB + Neo4j

改进方案引入了以下关键特性：

1. **三级大纲层级**：总纲 → 卷大纲 → 章大纲
2. **日常写作循环**：规划 → 写作 → 校验 → 更新
3. **版本化关系图谱**：追踪关系随卷数的变化
4. **混合存储升级**：Neo4j（图数据库）+ Chroma（向量数据库）
5. **校验代理**：集成一致性检查引擎
6. **更新代理**：从章节抽取结构化信息

### 1.2 设计目标

LSP（Language Server Protocol）作为编辑器集成层，需要实现：

1. **实时编辑体验**：将 AI 系统能力带到编辑器
2. **大纲导航支持**：三级层级跳转和显示
3. **实时一致性诊断**：利用校验代理提供实时反馈
4. **人工介入桥梁**：支持校验失败时的人工编辑
5. **关系追踪查询**：支持版本化关系图谱查询
6. **代理触发接口**：在编辑器中触发代理操作
7. **技术栈统一** ★核心：全Python实现，无中间层

### 1.3 架构决策：为什么选择 NovelWriter LSP

| 对比维度 | TypeScript LSP + Bridge API | NovelWriter LSP |
|---------|----------------------------|------------------|
| **技术栈** | Python + TypeScript | 纯Python ✅ |
| **架构复杂度** | 三层（LSP→Bridge→Writer） | 两层（LSP→Writer）✅ |
| **性能** | HTTP序列化开销 | 直接函数调用 ✅ |
| **代码复用** | 需要重复定义数据模型 | 共享数据模型 ✅ |
| **部署** | 两个进程 | 单一进程 ✅ |
| **依赖管理** | requirements.txt + package.json | requirements.txt ✅ |
| **调试** | 跨语言调试困难 | Python统一调试 ✅ |
| **维护成本** | 高（两种语言） | 低（单一语言）✅ |

---

## 二、整体架构设计

### 2.1 核心设计原则

1. **技术栈统一**：全Python实现，降低维护成本
2. **架构简化**：去掉Bridge API层，直接函数调用
3. **实时性优先**：编辑时即获得 AI 系统能力
4. **复用而非重建**：直接使用现有的内存系统、代理
5. **渐进式集成**：分阶段实现，先 MVP 后增强
6. **人工可控**：支持人工介入，而非完全黑盒

### 2.2 架构层次

```
┌─────────────────────────────────────────┐
│         编辑器 (VS Code)                 │
│         LSP Client (内置)                │
└──────────────┬──────────────────────────┘
               │ LSP Protocol (JSON-RPC)
┌──────────────▼──────────────────────────┐
│      NovelWriter LSP (pygls)          │
│  ┌────────────────────────────────────┐ │
│  │  LSP 功能层                         │ │
│  │  - goto_definition                  │ │
│  │  - find_references                  │ │
│  │  - documentSymbol                   │ │
│  │  - diagnostics                      │ │
│  │  - hover                            │ │
│  │  - completion                       │ │
│  │  - codeLens                         │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  文档解析层                         │ │
│  │  - Markdown 解析器                  │ │
│  │  - 三级大纲解析                     │ │
│  │  - 符号提取                         │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  符号索引层                         │ │
│  │  - 本地缓存 (LRU)                   │ │
│  │  - 增量更新                         │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │ 直接函数调用（无需API）
┌──────────────▼──────────────────────────┐
│       Writer System Core (Python)       │
│  ┌────────────────────────────────────┐ │
│  │  内存系统                           │ │
│  │  - CharacterMemory                  │ │
│  │  - PlotMemory                       │ │
│  │  - WorldMemory                      │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  混合存储                           │ │
│  │  - Neo4j (关系图谱)                 │ │
│  │  - Chroma (向量检索)                │ │
│  │  - PostgreSQL (结构化数据)          │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  代理层                             │ │
│  │  - ValidatorAgent (校验代理)        │ │
│  │  - UpdaterAgent (更新代理)          │ │
│  │  - ChapterPlannerAgent              │ │
│  │  - TypeWriterAgents                 │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### 2.3 核心优势

**1. 直接访问，零延迟**
```python
# 无需HTTP调用
async def goto_definition(params):
    # 直接调用内存系统
    symbol = await self.memory.get_symbol(symbol_name)
    return symbol.definition
```

**2. 共享数据模型**
```python
# 无需重复定义
from src.memory.schemas import CharacterSymbol, EventSymbol
# NovelWriter LSP 和 Writer System 使用相同的模型
```

**3. 单一进程，易于调试**
```bash
# 之前：启动两个进程
python bridge_api.py &
node lsp_server.js

# 现在：单一进程
python -m src.lsp.server
```

---

## 三、符号类型系统设计

### 3.1 符号类型定义

**原有类型（5种）：**
- Character（角色）
- Location（地点）
- Item（物品）
- Lore（设定/规则）
- PlotPoint（情节节点）

**新增类型（4种）：**
- Outline（大纲符号）
- Event（事件档案）
- Relationship（关系）
- Chapter（章节）

### 3.2 核心符号接口（共享数据模型）

```python
# src/memory/schemas.py (共享)
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class SymbolType(Enum):
    CHARACTER = "character"
    LOCATION = "location"
    ITEM = "item"
    LORE = "lore"
    PLOTPOINT = "plotpoint"
    OUTLINE = "outline"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    CHAPTER = "chapter"

class OutlineLevel(Enum):
    MASTER = "master"
    VOLUME = "volume"
    CHAPTER = "chapter"

@dataclass
class BaseSymbol:
    id: str
    type: SymbolType
    name: str
    novel_id: str
    definition_uri: str
    definition_range: Dict[str, int]
    references: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class OutlineSymbol(BaseSymbol):
    """大纲符号"""
    type: SymbolType = SymbolType.OUTLINE
    level: OutlineLevel = OutlineLevel.MASTER
    volume_number: Optional[int] = None
    chapter_number: Optional[int] = None
    content: Dict[str, Any] = None
    parent: Optional[str] = None
    children: List[str] = None

@dataclass
class EventSymbol(BaseSymbol):
    """事件符号"""
    type: SymbolType = SymbolType.EVENT
    event_id: str = ""
    chapter: int = 0
    volume: Optional[int] = None
    time: str = ""
    location: str = ""
    participants: List[str] = None
    description: str = ""
    evidence: List[str] = None
    impact: List[str] = None
    importance: str = "minor"  # critical, major, minor

@dataclass
class RelationshipSymbol(BaseSymbol):
    """关系符号"""
    type: SymbolType = SymbolType.RELATIONSHIP
    from_character: str = ""
    to_character: str = ""
    relation_type: str = ""
    since_volume: Optional[int] = None
    since_chapter: Optional[int] = None
    history: List[Dict[str, Any]] = None

@dataclass
class CharacterSymbol(BaseSymbol):
    """角色符号"""
    type: SymbolType = SymbolType.CHARACTER
    age: Optional[int] = None
    status: str = "alive"
    occupation: Optional[str] = None
    description: str = ""
    personality: List[str] = None
    goals: List[str] = None
    timeline: List[Dict[str, Any]] = None
    relationships: List[Dict[str, Any]] = None
    current_location: Optional[str] = None
    inventory: List[str] = None
```


---

## 四、NovelWriter LSP 核心实现

### 4.1 pygls 框架搭建

#### 安装依赖

```bash
pip install pygls lsprotocol
```

#### 服务器基础结构

```python
# src/lsp/server.py
from pygls.server import LanguageServer
from lsprotocol.types import (
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind
)

class NovelWriterServer(LanguageServer):
    """NovelWriter LSP 服务器"""
    
    def __init__(self):
        super().__init__("novelwriter-lsp", "v1.0")
        
        # 直接初始化 Writer System 组件（无需 Bridge API）
        self._init_writer_components()
        self._init_lsp_features()
    
    def _init_writer_components(self):
        """初始化 Writer System 组件"""
        from src.memory.composite_memory import CompositeMemory
        from src.storage.neo4j_client import Neo4jClient
        from src.storage.chroma_client import ChromaClient
        from src.agents.validator import ValidatorAgent
        from src.agents.updater import UpdaterAgent
        
        # 内存系统
        self.memory = CompositeMemory(
            namespace="default",
            embedding_provider="sentence-transformers"
        )
        
        # 存储组件
        self.neo4j = Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )
        
        self.chroma = ChromaClient(
            persist_directory=".chroma"
        )
        
        # 代理
        self.validator = ValidatorAgent(self.memory)
        self.updater = UpdaterAgent(self.memory)
        
        # 符号索引
        from src.lsp.index import SymbolIndex
        self.symbol_index = SymbolIndex(self.memory)
    
    def _init_lsp_features(self):
        """注册 LSP 功能"""
        from src.lsp.features import (
            register_definition,
            register_references,
            register_symbols,
            register_diagnostics,
            register_hover,
            register_completion,
            register_rename,
            register_codelens
        )
        
        register_definition(self)
        register_references(self)
        register_symbols(self)
        register_diagnostics(self)
        register_hover(self)
        register_completion(self)
        register_rename(self)
        register_codelens(self)

# 创建服务器实例
server = NovelWriterServer()

@server.feature('initialize')
async def initialize(params: InitializeParams):
    """初始化 LSP 服务器"""
    return InitializeResult(
        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Incremental,
            definition_provider=True,
            references_provider=True,
            document_symbol_provider=True,
            completion_provider={
                'trigger_characters': ['@', '#', '[']
            },
            hover_provider=True,
            rename_provider={'prepare_provider': True},
            code_lens_provider={'resolve_provider': False}
        )
    )

def main():
    """启动服务器"""
    server.start_io()

if __name__ == '__main__':
    main()
```

### 4.2 文档管理

```python
# src/lsp/document_manager.py
from pygls.workspace import Document
from typing import Dict, Optional

class DocumentManager:
    """文档管理器"""
    
    def __init__(self, server: NovelWriterServer):
        self.server = server
        self._documents: Dict[str, Document] = {}
        self._parsers: Dict[str, DocumentParser] = {}
    
    async def open_document(self, uri: str, content: str):
        """打开文档"""
        doc = Document(uri, content)
        self._documents[uri] = doc
        
        # 创建解析器
        parser = DocumentParser(doc, self.server.memory)
        self._parsers[uri] = parser
        
        # 解析文档
        await parser.parse()
        
        # 更新符号索引
        self.server.symbol_index.update(uri, parser.symbols)
    
    async def update_document(self, uri: str, changes: list):
        """更新文档（增量）"""
        parser = self._parsers.get(uri)
        if not parser:
            return
        
        for change in changes:
            await parser.apply_change(change)
        
        self.server.symbol_index.update(uri, parser.symbols)
    
    def close_document(self, uri: str):
        """关闭文档"""
        self._documents.pop(uri, None)
        self._parsers.pop(uri, None)
        self.server.symbol_index.remove(uri)
```

### 4.3 符号索引

```python
# src/lsp/index/symbol_index.py
from typing import Dict, List, Optional
from collections import OrderedDict

class SymbolIndex:
    """符号索引（LRU缓存）"""
    
    def __init__(self, memory, max_size: int = 1000):
        self.memory = memory
        self.max_size = max_size
        self._cache: OrderedDict[str, BaseSymbol] = OrderedDict()
        self._location_index: Dict[str, List[str]] = {}
    
    def get_symbol(self, name: str) -> Optional[BaseSymbol]:
        """获取符号（优先缓存）"""
        if name in self._cache:
            self._cache.move_to_end(name)
            return self._cache[name]
        
        # 从内存系统查询
        symbol = self.memory.get_symbol(name)
        if symbol:
            self._add_to_cache(name, symbol)
        
        return symbol
    
    def _add_to_cache(self, name: str, symbol: BaseSymbol):
        """添加到缓存"""
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[name] = symbol
    
    def update(self, uri: str, symbols: List[BaseSymbol]):
        """更新索引"""
        old_symbols = self._location_index.get(uri, [])
        for symbol_name in old_symbols:
            self._cache.pop(symbol_name, None)
        
        new_symbols = [s.name for s in symbols]
        self._location_index[uri] = new_symbols
        
        for symbol in symbols:
            self._add_to_cache(symbol.name, symbol)
    
    def remove(self, uri: str):
        """移除索引"""
        symbols = self._location_index.pop(uri, [])
        for name in symbols:
            self._cache.pop(name, None)
```

 
    def search(self, query: str, limit: int = 20) -> List[BaseSymbol]:
        """搜索符号"""
        results = []
        query_lower = query.lower()
        
        for name, symbol in self._cache.items():
            if query_lower in name.lower():
                results.append(symbol)
                if len(results) >= limit:
                    break
        
        return results
```

---

## 五、LSP 功能实现

### 5.1 goto_definition

```python
# src/lsp/features/definition.py
from lsprotocol.types import Location, Range, Position

def register_definition(server: NovelWriterServer):
    """注册 goto_definition 功能"""
    
    @server.feature('textDocument/definition')
    async def goto_definition(params):
        """跳转到符号定义"""
        document = server.workspace.get_document(params.text_document.uri)
        
        # 获取当前位置的符号名
        symbol_name = get_symbol_at_position(
            document.source,
            params.position.line,
            params.position.character
        )
        
        if not symbol_name:
            return None
        
        # 从索引获取符号（优先缓存）
        symbol = server.symbol_index.get_symbol(symbol_name)
        
        if not symbol:
            return None
        
        # 返回定义位置
        return Location(
            uri=symbol.definition_uri,
            range=Range(
                start=Position(
                    line=symbol.definition_range['start_line'],
                    character=0
                ),
                end=Position(
                    line=symbol.definition_range['end_line'],
                    character=999
                )
            )
        )

def get_symbol_at_position(content: str, line: int, char: int) -> str:
    """提取光标位置的符号名"""
    lines = content.split('\n')
    if line >= len(lines):
        return None
    
    text = lines[line]
    
    # 向前和向后扩展，找到完整符号名
    start = char
    end = char
    
    # 向左扩展
    while start > 0 and (text[start-1].isalnum() or text[start-1] == '_'):
        start -= 1
    
    # 向右扩展
    while end < len(text) and (text[end].isalnum() or text[end] == '_'):
        end += 1
    
    return text[start:end] if start != end else None
```

### 5.2 find_references

```python
# src/lsp/features/references.py
from lsprotocol.types import Location, Range, Position

def register_references(server: NovelWriterServer):
    """注册 find_references 功能"""
    
    @server.feature('textDocument/references')
    async def find_references(params):
        """查找所有引用"""
        document = server.workspace.get_document(params.text_document.uri)
        
        # 获取符号名
        symbol_name = get_symbol_at_position(
            document.source,
            params.position.line,
            params.position.character
        )
        
        if not symbol_name:
            return []
        
        # 从 Neo4j 查询所有引用
        references = await server.neo4j.find_references(symbol_name)
        
        # 从 PostgreSQL 补充位置信息
        locations = []
        for ref in references:
            locations.append(Location(
                uri=ref['uri'],
                range=Range(
                    start=Position(line=ref['line'], character=ref['start_char']),
                    end=Position(line=ref['line'], character=ref['end_char'])
                )
            ))
        
        return locations
```

### 5.3 documentSymbol

```python
# src/lsp/features/symbols.py
from lsprotocol.types import DocumentSymbol, SymbolKind, Range, Position

def register_symbols(server: NovelWriterServer):
    """注册 documentSymbol 功能"""
    
    @server.feature('textDocument/documentSymbol')
    async def document_symbol(params):
        """显示文档大纲"""
        document = server.workspace.get_document(params.text_document.uri)
        
        # 解析文档获取符号
        symbols = await parse_document_symbols(document.source, server.memory)
        
        # 构建层级结构
        return build_symbol_tree(symbols)

def build_symbol_tree(symbols: List[BaseSymbol]) -> List[DocumentSymbol]:
    """构建符号树"""
    root_symbols = []
    
    # 按层级组织
    outline_symbols = [s for s in symbols if s.type == SymbolType.OUTLINE]
    
    # 构建三级大纲树
    master = next((s for s in outline_symbols if s.level == OutlineLevel.MASTER), None)
    
    if master:
        master_symbol = DocumentSymbol(
            name=master.name,
            kind=SymbolKind.File,
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=999, character=0)
            ),
            selection_range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=len(master.name))
            ),
            children=[]
        )
        
        # 添加卷
        volumes = [s for s in outline_symbols if s.level == OutlineLevel.VOLUME]
        for vol in sorted(volumes, key=lambda x: x.volume_number):
            vol_symbol = DocumentSymbol(
                name=vol.name,
                kind=SymbolKind.Module,
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=999, character=0)
                ),
                selection_range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=len(vol.name))
                ),
                children=[]
            )
            
            # 添加章节
            chapters = [s for s in outline_symbols 
                       if s.level == OutlineLevel.CHAPTER and s.volume_number == vol.volume_number]
            for ch in sorted(chapters, key=lambda x: x.chapter_number):
                ch_symbol = DocumentSymbol(
                    name=ch.name,
                    kind=SymbolKind.Class,
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=999, character=0)
                    ),
                    selection_range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=len(ch.name))
                    ),
                    children=[]
                )
                vol_symbol.children.append(ch_symbol)
            
            master_symbol.children.append(vol_symbol)
        
        root_symbols.append(master_symbol)
    
    return root_symbols
```

### 5.4 diagnostics

```python
# src/lsp/features/diagnostics.py
from lsprotocol.types import Diagnostic, DiagnosticSeverity

def register_diagnostics(server: NovelWriterServer):
    """注册实时诊断功能"""
    
    @server.feature('textDocument/didChange')
    async def on_document_change(params):
        """文档变更时执行诊断"""
        document = server.workspace.get_document(params.text_document.uri)
        
        # 直接调用校验代理
        validation_result = await server.validator.validate(
            document.uri,
            document.source
        )
        
        # 转换为 LSP 诊断格式
        diagnostics = []
        for issue in validation_result.issues:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(
                        line=issue.line,
                        character=issue.start_char
                    ),
                    end=Position(
                        line=issue.line,
                        character=issue.end_char
                    )
                ),
                message=issue.message,
                severity=map_severity(issue.type),
                source="novelwriter-lsp",
                code=issue.code
            ))
        
        # 推送诊断结果
        server.publish_diagnostics(document.uri, diagnostics)

def map_severity(issue_type: str) -> DiagnosticSeverity:
    """映射严重级别"""
    severity_map = {
        'error': DiagnosticSeverity.Error,
        'warning': DiagnosticSeverity.Warning,
        'hint': DiagnosticSeverity.Hint,
        'information': DiagnosticSeverity.Information
    }
    return severity_map.get(issue_type, DiagnosticSeverity.Information)
```

### 5.5 hover

```python
# src/lsp/features/hover.py
from lsprotocol.types import Hover,

### 5.6 completion

```python
# src/lsp/features/completion.py
from lsprotocol.types import CompletionItem, CompletionItemKind

def register_completion(server: NovelWriterServer):
    """注册智能补全功能"""
    
    @server.feature('textDocument/completion')
    async def completion(params):
        """智能补全"""
        document = server.workspace.get_document(params.text_document.uri)
        
        # 获取前缀
        prefix = get_prefix_at_position(
            document.source,
            params.position.line,
            params.position.character
        )
        
        if not prefix:
            return []
        
        # 搜索符号
        symbols = server.symbol_index.search(prefix, limit=20)
        
        # 构建补全列表
        items = []
        for symbol in symbols:
            kind = map_symbol_kind(symbol.type)
            
            items.append(CompletionItem(
                label=symbol.name,
                kind=kind,
                detail=get_symbol_detail(symbol),
                documentation=f"{symbol.type.value}: {symbol.description if hasattr(symbol, 'description') else ''}"
            ))
        
        return items

def get_prefix_at_position(content: str, line: int, char: int) -> str:
    """获取当前位置的前缀"""
    lines = content.split('\n')
    if line >= len(lines):
        return None
    
    text = lines[line]
    start = char - 1
    
    while start >= 0 and (text[start].isalnum() or text[start] == '_'):
        start -= 1
    
    return text[start+1:char] if start < char else None

def map_symbol_kind(symbol_type: SymbolType) -> CompletionItemKind:
    """映射符号类型到补全图标"""
    kind_map = {
        SymbolType.CHARACTER: CompletionItemKind.Class,
        SymbolType.LOCATION: CompletionItemKind.Module,
        SymbolType.ITEM: CompletionItemKind.Property,
        SymbolType.LORE: CompletionItemKind.Enum,
        SymbolType.EVENT: CompletionItemKind.Event,
        SymbolType.OUTLINE: CompletionItemKind.File
    }
    return kind_map.get(symbol_type, CompletionItemKind.Text)
```

### 5.7 codeLens

```python
# src/lsp/features/codelens.py
from lsprotocol.types import CodeLens, Command

def register_codelens(server: NovelWriterServer):
    """注册代理触发按钮"""
    
    @server.feature('textDocument/codeLens')
    async def code_lens(params):
        """显示代理触发按钮"""
        document = server.workspace.get_document(params.text_document.uri)
        
        # 只在章节文件显示
        if not is_chapter_file(document.uri):
            return []
        
        lenses = []
        
        # 一致性检查按钮
        lenses.append(CodeLens(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=0)
            ),
            command=Command(
                title="✓ 运行一致性检查",
                command="novel.validateChapter",
                arguments=[document.uri]
            )
        ))
        
        # 更新内存按钮
        lenses.append(CodeLens(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=0)
            ),
            command=Command(
                title="↻ 更新内存系统",
                command="novel.updateMemory",
                arguments=[document.uri]
            )
        ))
        
        # 重试生成按钮
        lenses.append(CodeLens(
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=0)
            ),
            command=Command(
                title="↻ 重试生成",
                command="novel.retryChapter",
                arguments=[document.uri]
            )
        ))
        
        return lenses
```

### 5.8 executeCommand

```python
# src/lsp/features/commands.py
from lsprotocol.types import MessageType

def register_commands(server: NovelWriterServer):
    """注册自定义命令"""
    
    @server.command("novel.validateChapter")
    async def validate_chapter(args):
        """运行一致性检查"""
        uri = args[0]
        document = server.workspace.get_document(uri)
        
        # 直接调用校验代理
        result = await server.validator.validate(uri, document.source)
        
        # 显示诊断
        diagnostics = []
        for issue in result.issues:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=issue.line, character=issue.start_char),
                    end=Position(line=issue.line, character=issue.end_char)
                ),
                message=issue.message,
                severity=map_severity(issue.type),
                source="novelwriter-lsp"
            ))
        
        server.publish_diagnostics(uri, diagnostics)
        
        # 如果需要人工介入
        if result.needs_intervention:
            server.show_message(
                f"校验失败（重试{result.retry_count}次），需要人工介入：{result.reason}",
                MessageType.Error
            )
    
    @server.command("novel.updateMemory")
    async def update_memory(args):
        """更新内存系统"""
        uri = args[0]
        document = server.workspace.get_document(uri)
        
        # 直接调用更新代理
        result = await server.updater.extract_and_update(uri, document.source)
        
        server.show_message(
            f"内存系统已更新：{result.new_events}个新事件，{result.character_updates}个角色更新",
            MessageType.Info
        )
    
    @server.command("novel.retryChapter")
    async def retry_chapter(args):
        """重试章节生成"""
        uri = args[0]
        
        # 解析章节号
        chapter_number = extract_chapter_number(uri)
        
        # 调用章节规划代理
        result = await server.chapter_planner.retry(
            chapter_number=chapter_number,
            reason="用户手动触发"
        )
        
        if result.success:
            server.show_message(
                f"第{chapter_number}章已重新生成",
                MessageType.Info
            )
        else:
            server.show_message(
                f"重试失败：{result.message}",
                MessageType.Error
            )
```

---

## 六、性能优化策略

### 6.1 三层缓存架构

```python
# Layer 1: 符号索引缓存（LRU）
class SymbolIndex:
    def __init__(self, memory, max_size=1000):
        self._cache = OrderedDict()  # LRU
        self.max_size = max_size

# Layer 2: Neo4j 查询缓存
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_relationship_history(char1: str, char2: str):
    return await neo4j.query(...)

# Layer 3: Chroma 向量缓存
@lru_cache(maxsize=50)
async def search_events(query: str):
    return await chroma.search(query)
```

### 6.2 增量更新

```python
@server.feature('textDocument/didChange')
async def on_change(params):
    # 只重新解析变更部分
    changes = params.content_changes
    affected_lines = get_changed_lines(changes)
    
    # 增量解析
    parser = parsers[uri]
    affected_symbols = await parser.parse_incremental(affected_lines)
    
    # 更新索引
    symbol_index.update_incremental(uri, affected_symbols)
```

### 6.3 性能基准

| 操作 | 目标 | 实现 |
|------|------|------|
| goto_definition | < 10ms | 直接内存访问 |
| find_references | < 50ms | Neo4j查询+缓存 |
| documentSymbol | < 20ms | 本地索引 |
| diagnostics | < 100ms | 直接代理调用 |
| completion | < 50ms | 本地搜索 |

---

## 七、错误处理机制

### 7.1 异常分类

```python
class NovelLSPException(Exception):
    """基础异常"""
    pass

class SymbolNotFoundError(NovelLSPException):
    """符号未找到"""
    pass

class StorageError(NovelLSPException):
    """存储错误"""
    pass

class ValidationError(NovelLSPException):
    """校验错误"""
    pass
```

### 7.2 错误处理装饰器

```python
def handle_errors(func):
    """统一错误处理"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SymbolNotFoundError as e:
            server.show_message(f"符号未找到: {e}", MessageType.Warning)
            return None
        except StorageError as e:
            server.show_message(f"存储错误: {e}", MessageType.Error)
            # 降级：使用缓存
            return get_from_cache(...)
        except Exception as e:
            logger.exception("Unexpected error")
            server.show_message(f"内部错误: {e}", MessageType.Error)
            return None
    return wrapper
```

---

## 八、项目结构设计

```
novel-agent
