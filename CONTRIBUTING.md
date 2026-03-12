# 贡献指南

欢迎参与 NovelWriter 项目的开发！本文档将帮助你快速搭建开发环境，了解代码规范，并顺利提交贡献。

## 目录

- [项目简介](#项目简介)
- [开发环境搭建](#开发环境搭建)
- [代码风格](#代码风格)
- [测试要求](#测试要求)
- [提交流程](#提交流程)
- [Issue 报告](#issue-报告)
- [社区行为准则](#社区行为准则)

---

## 项目简介

NovelWriter 是一个 AI 驱动的小说写作和发布系统，包含两个主要组件：

- **Writer**：AI 小说写作系统（约 57K 行代码），提供情节规划、角色创建、世界观构建等功能
- **LSP**：编辑器语言服务器集成（约 3K 行代码），为编辑器提供智能提示和集成支持

项目特点：
- 支持多种题材（科幻、奇幻、言情、历史、军事）
- 多平台发布（Wattpad、Royal Road、Amazon KDP）
- 市场调研和读者互动分析
- 完整的 CI/CD 流程

---

## 开发环境搭建

### 系统要求

- **操作系统**：Windows 10/11、Linux、macOS
- **Python 版本**：3.10 或更高版本（推荐 3.11）
- **Git**：2.0 或更高版本
- **内存**：至少 8GB RAM（推荐 16GB）

### 1. 克隆仓库

```bash
git clone https://github.com/novelwriter/NovelWriter.git
cd NovelWriter
```

### 2. 创建虚拟环境

#### Windows

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

#### Linux/macOS

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 3. 安装依赖

#### 安装 Writer 组件

```bash
cd Writer
pip install -e ".[dev]"
cd ..
```

#### 安装 LSP 组件

```bash
cd LSP
pip install -e ".[dev]"
cd ..
```

#### 验证安装

```bash
# 检查 Writer 安装
python -m src.main --help

# 检查 LSP 安装
novelwriter-lsp --help
```

### 4. 安装可选工具

#### pre-commit 钩子（推荐）

```bash
# 安装 pre-commit
pip install pre-commit

# 启用钩子
pre-commit install
```

启用后，每次提交前会自动运行格式化和 linting 检查。

### 5. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的配置：

```bash
# LLM API 密钥（必需）
DEEPSEEK_API_KEY=your_api_key_here

# Redis 连接（可选，用于任务调度）
REDIS_URL=redis://localhost:6379/0

# 发布平台凭证（可选）
WATTPAD_API_KEY=your_wattpad_key
ROYALROAD_USERNAME=your_username
```

### 6. 验证开发环境

运行快速检查：

```bash
# 运行健康检查
python -m src.main health-check

# 运行测试套件
pytest Writer/tests -v
pytest LSP/tests -v
```

---

## 代码风格

本项目使用统一的代码风格工具链，确保代码质量和一致性。

### 工具链

| 工具 | 用途 | 配置位置 |
|------|------|----------|
| **Black** | 代码格式化 | `pyproject.toml` |
| **Ruff** | Linting 检查 | `pyproject.toml` |
| **Mypy** | 类型检查 | `pyproject.toml` |

### 格式化规范

#### Black 配置

```toml
[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]
```

**运行格式化**：

```bash
# 格式化所有代码
black .

# 格式化特定文件
black src/agents/base.py

# 检查格式（不修改）
black --check .
```

#### 格式化示例

```python
# ✅ 正确：行宽不超过 100 字符
def process_novel_data(
    novel_id: str,
    chapter: int,
    genre: str,
) -> AgentResult:
    """处理小说数据。"""
    pass

# ❌ 错误：行宽过长
def process_novel_data(novel_id: str, chapter: int, genre: str) -> AgentResult:  # 超过 100 字符
    pass
```

### Linting 规范

#### Ruff 配置

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
lint.select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]
lint.ignore = ["E501"]  # 行宽由 Black 处理
```

**运行 Linting**：

```bash
# 检查所有文件
ruff check .

# 检查特定目录
ruff check src/

# 自动修复问题
ruff check --fix .

# 查看详细报告
ruff check --output-format=full
```

#### 常见 Linting 规则

| 代码 | 说明 | 示例 |
|------|------|------|
| **E** | pycodestyle 错误 | 语法错误、格式问题 |
| **F** | pyflakes | 未使用的导入、未定义的变量 |
| **W** | pycodestyle 警告 | 代码风格警告 |
| **I** | isort | 导入顺序 |
| **N** | pep8-naming | 命名规范 |
| **UP** | pyupgrade | Python 语法升级建议 |
| **B** | flake8-bugbear | 常见 bug 模式 |
| **C4** | flake8-comprehensions | 推导式优化 |

### 类型检查规范

#### Mypy 配置

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

**运行类型检查**：

```bash
# 检查 Writer 组件
cd Writer && mypy src/

# 检查 LSP 组件
cd LSP && mypy novelwriter_lsp/
```

#### 类型注解规范

```python
# ✅ 正确：使用现代 Python 3.10+ 语法
from typing import Any

def get_character(name: str) -> Character | None:
    """获取角色信息。"""
    pass

def process_data(items: list[str]) -> dict[str, Any]:
    """处理数据列表。"""
    pass

# ❌ 错误：使用旧版语法
from typing import Optional, List, Dict

def get_character(name: str) -> Optional[Character]:  # 应使用 Character | None
    pass

def process_data(items: List[str]) -> Dict[str, Any]:  # 应使用 list[str], dict[str, Any]
    pass
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| **模块/文件** | `snake_case.py` | `file_memory.py`, `base_writer.py` |
| **类** | `PascalCase` | `AgentOrchestrator`, `SciFiWriter` |
| **函数/方法** | `snake_case` | `write_chapter`, `get_writer` |
| **常量** | `UPPER_SNAKE_CASE` | `BASE_URL`, `MAX_RETRIES` |
| **私有属性** | `_leading_underscore` | `_total_tokens_used` |
| **类常量** | `UPPER_CASE` | `GENRE`, `DOMAIN_KNOWLEDGE` |

### 导入顺序

```python
# 1. 标准库
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# 2. 第三方包
import pytest
from pydantic import Field
from pydantic_settings import BaseSettings

# 3. 本地导入
from src.agents.base import AgentResult, BaseAgent
from src.llm.base import BaseLLM
```

使用 Ruff 自动排序导入：

```bash
ruff check --select=I --fix .
```

### 文档字符串规范

```python
class BaseAgent(ABC):
    """所有代理的基类。
    
    提供通用的执行接口和结果处理逻辑。
    """
    
    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """执行代理的主要任务。
        
        Args:
            input_data: 输入数据字典，包含任务所需的所有参数。
            
        Returns:
            AgentResult 对象，包含执行状态、结果数据和错误信息。
            
        Raises:
            ValueError: 当输入数据格式不正确时。
        """
        pass
```

---

## 测试要求

### 测试框架

- **pytest**：主测试框架
- **pytest-asyncio**：异步测试支持
- **pytest-cov**：覆盖率报告

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定组件测试
pytest Writer/tests/
pytest LSP/tests/

# 运行特定测试文件
pytest tests/test_agents/test_writers.py

# 运行特定测试类
pytest tests/test_agents/test_writers.py::TestSciFiWriter

# 运行特定测试方法
pytest tests/test_agents/test_writers.py::TestSciFiWriter::test_write_chapter

# 详细输出
pytest -v

# 运行并显示覆盖率
pytest --cov=src --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html
# 报告位置：htmlcov/index.html
```

### 测试覆盖率要求

| 组件 | 最低覆盖率 | 目标覆盖率 |
|------|-----------|-----------|
| **核心模块** | 80% | 90% |
| **代理模块** | 75% | 85% |
| **工具模块** | 70% | 80% |

查看覆盖率报告：

```bash
# 终端报告
pytest --cov=src --cov-report=term-missing

# HTML 报告（浏览器查看）
pytest --cov=src --cov-report=html
# 打开 htmlcov/index.html
```

### 编写测试

#### 单元测试示例

```python
# tests/test_agents/test_writers.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.writers.scifi import SciFiWriter
from src.agents.base import AgentResult


class TestSciFiWriter:
    """科幻作家代理测试。"""
    
    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """创建模拟 LLM。"""
        mock = MagicMock()
        mock.generate_with_system = AsyncMock(
            return_value=MagicMock(content="Test content")
        )
        return mock
    
    @pytest.fixture
    def writer(self, mock_llm: MagicMock) -> SciFiWriter:
        """创建测试用作家实例。"""
        return SciFiWriter(name="Test Writer", llm=mock_llm)
    
    @pytest.mark.asyncio
    async def test_write_chapter(
        self,
        writer: SciFiWriter,
    ) -> None:
        """测试章节生成功能。"""
        result = await writer.execute({
            "novel_id": "test",
            "chapter": 1,
        })
        
        assert result.success is True
        assert "content" in result.data
        assert isinstance(result.data["content"], str)
```

#### 异步测试规范

```python
# ✅ 正确：使用 pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_operation() -> None:
    result = await some_async_function()
    assert result is not None

# ❌ 错误：缺少标记
async def test_async_operation() -> None:  # 不会被识别为测试
    pass
```

### 性能测试

性能测试使用 `@pytest.mark.benchmark` 标记：

```python
@pytest.mark.benchmark
def test_vector_search_performance() -> None:
    """测试向量搜索性能。"""
    import time
    
    start = time.perf_counter()
    # 执行搜索操作
    results = vector_store.query_similar("test query", n_results=10)
    elapsed = time.perf_counter() - start
    
    # 要求查询时间小于 100ms
    assert elapsed < 0.1
```

运行性能测试：

```bash
pytest -m benchmark -v
```

---

## 提交流程

### Git 分支策略

本项目采用简化的 Git Flow 分支模型：

```
main          - 主分支，始终可部署
  └── develop - 开发分支，新功能合并至此
       └── feature/* - 功能分支，从 develop 检出
```

#### 分支命名

| 分支类型 | 命名格式 | 示例 |
|---------|---------|------|
| **主分支** | `main` | `main` |
| **开发分支** | `develop` | `develop` |
| **功能分支** | `feature/<description>` | `feature/add-character-agent` |
| **修复分支** | `fix/<description>` | `fix/vector-store-bug` |
| **文档分支** | `docs/<description>` | `docs/add-api-docs` |

#### 创建功能分支

```bash
# 确保基于最新的 develop
git checkout develop
git pull origin develop

# 创建功能分支
git checkout -b feature/add-character-agent
```

### Commit Message 规范

采用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### Type 类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(agent): add character creation agent` |
| `fix` | Bug 修复 | `fix(db): resolve chromadb import error` |
| `docs` | 文档更新 | `docs(readme): add installation guide` |
| `style` | 代码格式 | `style(format): run black on all files` |
| `refactor` | 重构 | `refactor(memory): simplify vector store interface` |
| `test` | 测试相关 | `test(writer): add unit tests for scifi writer` |
| `chore` | 构建/工具 | `chore(deps): update pytest to 8.0` |

#### Scope 范围

| 范围 | 说明 |
|------|------|
| `agent` | 代理相关 |
| `llm` | LLM 集成 |
| `memory` | 记忆系统 |
| `db` | 数据库 |
| `api` | API 接口 |
| `ui` | 用户界面 |
| `config` | 配置文件 |
| `deps` | 依赖管理 |

#### Commit 示例

```bash
# ✅ 正确的提交信息
git commit -m "feat(agent): add character creation agent"
git commit -m "fix(db): resolve chromadb import error on Python 3.14"
git commit -m "docs(readme): add installation guide for Windows"

# ❌ 错误的提交信息
git commit -m "fix bug"  # 太模糊
git commit -m "update code"  # 没有说明更新内容
git commit -m "WIP"  # 不应提交半成品
```

#### 多行提交信息

```bash
git commit -m "feat(memory): implement vector store factory

- Add VectorStoreFactory for unified vector storage interface
- Support Chroma (local) and Pinecone (cloud) backends
- Add configuration for embedding model selection
- Include fallback handling for Python 3.14+

Closes #123"
```

### Pull Request 流程

#### 1. 推送分支

```bash
# 推送功能分支到远程
git push -u origin feature/add-character-agent
```

#### 2. 创建 Pull Request

在 GitHub 上创建 PR，从你的功能分支到 `develop` 分支。

#### 3. PR 模板

```markdown
## 变更说明
<!-- 简要描述此 PR 的变更内容 -->

## 相关问题
<!-- 关联的 Issue 编号，例如：Closes #123 -->

## 测试计划
<!-- 描述如何测试这些变更 -->

- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试已完成

## 检查清单

- [ ] 代码已通过 Black 格式化
- [ ] 代码已通过 Ruff Linting
- [ ] 类型注解完整并通过 Mypy 检查
- [ ] 添加了必要的单元测试
- [ ] 更新了相关文档
- [ ] Commit message 符合规范
```

#### 4. CI/CD 检查

PR 创建后，GitHub Actions 会自动运行以下检查：

- **Lint**：Black 格式化、Ruff Linting、Mypy 类型检查
- **Writer 测试**：Python 3.10 和 3.14 环境下的完整测试套件
- **LSP 测试**：Python 3.10 和 3.14 环境下的完整测试套件
- **覆盖率报告**：代码覆盖率检查

所有检查必须通过才能合并。

#### 5. 代码审查

- 至少需要 1 名维护者审查批准
- 解决所有审查意见
- 保持 PR 简洁，避免过大变更

#### 6. 合并

审查通过后，维护者会将 PR 合并到 `develop` 分支。

---

## Issue 报告

### Bug 报告模板

创建 Issue 时，请使用以下模板：

```markdown
## Bug 描述
<!-- 清晰简洁地描述 bug -->

## 复现步骤
<!-- 描述如何复现此 bug -->

1. 执行命令 '...'
2. 输入 '...'
3. 看到错误 '...'

## 期望行为
<!-- 描述期望发生什么 -->

## 实际行为
<!-- 描述实际发生了什么 -->

## 环境信息
<!-- 请填写以下信息 -->

- **操作系统**: [例如：Windows 11, Ubuntu 22.04, macOS 14]
- **Python 版本**: [例如：3.10.12]
- **NovelWriter 版本**: [例如：0.1.0 或 commit hash]
- **相关组件**: [例如：Writer, LSP]

## 错误日志
<!-- 如果有错误日志或堆栈跟踪，请粘贴在此处 -->

```python
# 粘贴错误日志
```

## 附加信息
<!-- 其他有助于解决问题的信息 -->
```

### 功能请求模板

```markdown
## 功能描述
<!-- 清晰简洁地描述新功能 -->

## 使用场景
<!-- 描述此功能的使用场景和目标用户 -->

## 实现建议
<!-- 如果有实现思路或技术方案，请在此说明 -->

## 替代方案
<!-- 是否考虑过其他实现方式？ -->

## 附加信息
<!-- 其他相关信息、截图或示例 -->
```

### Issue 标签

| 标签 | 说明 |
|------|------|
| `bug` | 错误修复 |
| `enhancement` | 功能增强 |
| `feature` | 新功能 |
| `documentation` | 文档相关 |
| `good first issue` | 适合新手 |
| `help wanted` | 需要帮助 |
| `question` | 问题咨询 |
| `wontfix` | 不会修复 |

---

## 社区行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性化的语言或图像
- 人身攻击或侮辱性评论
- 公开或私下骚扰
- 未经许可发布他人信息
- 其他不道德或不专业的行为

### 执行

如发现不可接受的行为，请通过以下方式报告：

- 发送邮件至：conduct@novelwriter.dev
- 在 GitHub Issue 中标记维护者

所有投诉都将得到审查和调查。

---

## 开发资源

### 重要文档

- [Writer/AGENTS.md](Writer/AGENTS.md) - Writer 组件开发指南
- [P0_IMPROVEMENTS.md](P0_IMPROVEMENTS.md) - P0 阶段改进总结
- [LSP_ARCHITECTURE_REDESIGN.md](LSP_ARCHITECTURE_REDESIGN.md) - LSP 架构设计

### 代码库结构

```
NovelWriter/
├── Writer/                 # Writer 组件
│   ├── src/               # 源代码
│   │   ├── agents/        # AI 代理
│   │   ├── llm/           # LLM 集成
│   │   ├── memory/        # 记忆系统
│   │   ├── db/            # 数据库
│   │   └── utils/         # 工具函数
│   ├── tests/             # 测试
│   └── pyproject.toml     # 项目配置
├── LSP/                   # LSP 组件
│   ├── novelwriter_lsp/   # 源代码
│   ├── tests/             # 测试
│   └── pyproject.toml     # 项目配置
├── .github/workflows/     # CI/CD 配置
└── CONTRIBUTING.md        # 贡献指南（本文档）
```

### 常用命令速查

```bash
# 环境设置
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -e ".[dev]"

# 代码质量
black .                    # 格式化
ruff check . --fix         # Linting 并修复
mypy src/                  # 类型检查

# 测试
pytest                     # 运行所有测试
pytest -v --cov=src        # 带覆盖率
pytest tests/file.py::Class::method  # 运行单个测试

# Git
git checkout -b feature/name  # 创建功能分支
git commit -m "type(scope): message"  # 提交
git push -u origin feature/name  # 推送
```

---

## 许可证

本项目采用 MIT 许可证。提交贡献即表示你同意将你的贡献授权给本项目，遵循相同的许可证条款。

---

## 致谢

感谢所有为 NovelWriter 项目做出贡献的开发者！

你的每一次提交、每一个 Issue、每一条评论都在帮助这个项目变得更好。

欢迎加入我们的社区！
