# 开发环境配置指南

本文档详细介绍 Novel Agent System 项目的开发环境配置、构建流程、测试指南以及调试技巧。

## 目录

- [开发环境配置](#开发环境配置)
- [构建流程](#构建流程)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [故障排除](#故障排除)

## 开发环境配置

### 前置要求

在开始开发之前，请确保您的系统满足以下要求：

- **操作系统**: Windows 10/11, macOS 10.15+, 或 Linux (Ubuntu 20.04+ 推荐)
- **Python 版本**: 3.10 或更高版本
- **Git**: 最新版本
- **API 密钥**: DeepSeek API 密钥（必需）

### 环境配置步骤

#### 1. 克隆项目仓库

```bash
git clone <repository-url>
cd writer
```

#### 2. 创建虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装开发依赖

项目使用 `setuptools` 进行依赖管理，安装时包含开发工具：

```bash
pip install -e ".[dev]"
```

这将安装：
- 项目运行所需的核心依赖
- 代码质量工具（ruff, black, mypy）
- 测试框架（pytest, pytest-asyncio, pytest-cov）

#### 4. 配置环境变量

复制示例配置文件并编辑：

```bash
cp .env.example .env
```

使用文本编辑器打开 `.env` 文件，填入必要的配置信息：

- `DEEPSEEK_API_KEY`: 您的 DeepSeek API 密钥（必需）
- 其他可选配置（如 Redis URL、发布平台密钥等）

#### 5. 验证安装

运行健康检查命令验证环境配置是否正确：

```bash
python -m src.main health-check
```

如果一切正常，您将看到健康检查通过的消息。

## 构建流程

### 代码质量检查

项目使用三个主要工具确保代码质量：

#### 1. 代码格式化 (Black)

Black 是一个严格的 Python 代码格式化工具，确保代码风格一致：

```bash
# 格式化所有 Python 文件
black .

# 格式化特定文件
black src/agents/base.py

# 检查文件是否需要格式化（不修改文件）
black --check .
```

#### 2. 代码检查 (Ruff)

Ruff 是一个快速的 Python 代码检查工具，替代了 Flake8 和其他多个插件：

```bash
# 运行所有检查
ruff check .

# 检查特定文件
ruff check src/agents/base.py

# 自动修复可修复的问题
ruff check --fix .

# 显示详细的错误信息
ruff check --show-source .
```

#### 3. 类型检查 (Mypy)

Mypy 用于静态类型检查，帮助提前发现类型相关的错误：

```bash
# 对 src 目录进行类型检查
mypy src/

# 显示更详细的类型错误信息
mypy --show-error-codes src/

# 生成类型检查报告
mypy --html-report mypy-report src/
```

### 完整构建流程

在提交代码之前，建议运行完整的构建流程：

```bash
# 1. 格式化代码
black .

# 2. 运行代码检查
ruff check .

# 3. 运行类型检查
mypy src/

# 4. 运行测试
python -m pytest
```

## 测试指南

### 测试框架

项目使用 pytest 作为测试框架，支持异步测试和覆盖率报告。

### 运行测试

#### 基本测试命令

```bash
# 运行所有测试
python -m pytest

# 或使用更简洁的命令
pytest
```

#### 详细输出

```bash
# 显示详细的测试输出
pytest -v

# 显示每个测试的标准输出
pytest -s
```

#### 运行特定测试

```bash
# 运行单个测试文件
pytest tests/test_agents/test_writers.py

# 运行单个测试类
pytest tests/test_agents/test_writers.py::TestSciFiWriter

# 运行单个测试方法
pytest tests/test_agents/test_writers.py::TestSciFiWriter::test_write_chapter
```

#### 按标记运行测试

```bash
# 只运行异步测试
pytest -m asyncio

# 只运行集成测试
pytest -m integration

# 跳过特定标记的测试
pytest -m "not slow"
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src

# 显示未覆盖的代码行
pytest --cov=src --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html

# 生成 XML 覆盖率报告（用于 CI）
pytest --cov=src --cov-report=xml
```

覆盖率报告将生成在 `htmlcov` 目录中，您可以在浏览器中打开 `index.html` 查看详细的覆盖率信息。

### 测试模式

#### 异步测试

所有代理和 LLM 相关的测试都使用异步模式：

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_async_method():
    # 测试异步代码
    result = await some_async_function()
    assert result is not None
```

#### 使用 Fixtures

项目在 `tests/conftest.py` 中定义了共享 fixtures，您可以在测试中直接使用：

```python
@pytest.mark.asyncio
async def test_writer_execute(writer):
    # writer 是一个预配置好的 fixture
    result = await writer.execute({"input": "test"})
    assert result.success is True
```

## 调试技巧

### 日志调试

项目使用 Python 标准库的 logging 模块。您可以通过设置环境变量来调整日志级别：

```bash
# 设置日志级别为 DEBUG
export LOG_LEVEL=DEBUG

# 或在 .env 文件中设置
LOG_LEVEL=DEBUG
```

### 使用 print 语句

在开发过程中，可以使用 print 语句输出调试信息。但请记住在提交代码前移除这些调试语句。

### 使用调试器

#### Python 内置调试器 (pdb)

在代码中插入断点：

```python
import pdb; pdb.set_trace()
```

当程序运行到这一行时，会进入交互式调试模式。

#### VS Code 调试

如果您使用 VS Code，可以创建 `.vscode/launch.json` 文件：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: 模块",
            "type": "debugpy",
            "request": "launch",
            "module": "src.main",
            "args": ["health-check"],
            "justMyCode": true
        },
        {
            "name": "Python: 测试",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/test_agents/test_writers.py", "-v"],
            "justMyCode": true
        }
    ]
}
```

### 调试异步代码

调试异步代码时，可以使用 `asyncio.run()` 在同步上下文中运行异步函数：

```python
import asyncio

async def my_async_function():
    # 异步代码
    pass

# 在调试时运行
asyncio.run(my_async_function())
```

## 故障排除

### 常见问题

#### 1. 虚拟环境激活失败

**问题**: 在 Windows 上无法激活虚拟环境

**解决方案**:
- 确保您使用的是 PowerShell 或命令提示符
- 如果使用 PowerShell，可能需要先更改执行策略：
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

#### 2. 依赖安装失败

**问题**: `pip install -e ".[dev]"` 失败

**解决方案**:
- 确保 pip 是最新版本：`pip install --upgrade pip`
- 尝试使用国内镜像源：
  ```bash
  pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

#### 3. 测试失败

**问题**: 测试运行失败

**解决方案**:
- 确保虚拟环境已激活
- 检查是否所有依赖都已安装
- 尝试删除 `.pytest_cache` 目录后重新运行
- 使用 `pytest -v -s` 查看详细的错误信息

#### 4. API 调用失败

**问题**: LLM API 调用失败

**解决方案**:
- 检查 `.env` 文件中的 API 密钥是否正确
- 确保网络连接正常
- 检查 API 账户是否有足够的余额
- 查看日志文件获取更详细的错误信息

#### 5. 类型检查错误

**问题**: mypy 报告类型错误

**解决方案**:
- 检查类型注解是否正确
- 对于第三方库的类型问题，可以使用 `# type: ignore` 注释
- 参考 `AGENTS.md` 中的类型提示规范

### 获取帮助

如果您遇到了无法解决的问题：

1. 查看项目的 Issue 列表，看是否有类似问题
2. 搜索相关的错误信息
3. 提交新的 Issue，包含：
   - 详细的问题描述
   - 复现步骤
   - 错误日志
   - 您的系统环境信息

---

**祝您开发愉快！**
