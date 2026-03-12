# VS Code 配置指南 - NovelWriter LSP 服务器

本指南详细说明如何在 VS Code 中配置和使用 NovelWriter LSP 服务器。

## 📋 前置要求

### 1. 安装 Python 3.14+

```bash
python --version  # 应该显示 Python 3.14 或更高版本
```

### 2. 创建虚拟环境（推荐）

在项目根目录执行：

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装开发工具（可选）

```bash
pip install black ruff mypy pytest pytest-cov pytest-asyncio
```

## 🔧 VS Code 配置

### 方法一：自动安装推荐扩展（推荐）

1. 在 VS Code 中打开项目：`File` → `Open Folder` → 选择 `C:\dev_projects\NovelWriter\LSP`
2. VS Code 会提示安装推荐扩展，点击 "Install All"

### 方法二：手动安装扩展

打开 VS Code 扩展面板（`Ctrl+Shift+X`），搜索并安装：

| 扩展名称 | 说明 |
|---------|------|
| Python (ms-python.python) | Python 语言支持 |
| Pylance (ms-python.vscode-pylance) | Python IntelliSense |
| Black Formatter (ms-python.black-formatter) | 代码格式化 |
| Ruff (charliermarsh.ruff) | 代码检查 |
| MyPy Type Checker (ms-python.mypy-type-checker) | 类型检查 |
| Markdown All in One (yzhang.markdown-all-in-one) | Markdown 编辑支持 |

## 🚀 启动 LSP 服务器

### 方式一：通过 Python 模块启动（推荐）

在 VS Code 终端中运行：

```bash
# 启动 LSP 服务器（stdio 模式）
python -m novelwriter_lsp

# 启用调试日志
python -m novelwriter_lsp --debug

# 查看版本信息
python -m novelwriter_lsp --version
```

### 方式二：通过 VS Code 调试器启动

1. 按 `F5` 或点击 "Run and Debug" 面板
2. 选择 "NovelWriter LSP Server" 配置
3. 服务器将在调试模式下启动

### 方式三：作为客户端调用（高级）

LSP 服务器通过 stdin/stdout 进行通信，通常由编辑器客户端自动启动。

**示例：测试服务器启动**

创建测试文件 `test_lsp_connection.md`：

```markdown
# Test Novel

@Character: John Doe {
    age: 42,
    status: "alive"
}

John walked into the scene.
```

## 📝 LSP 功能测试

### 1. 跳转到定义 (Go to Definition)

- 将光标放在 `@Character: John Doe` 上
- 按 `F12` 或右键 → "Go to Definition"
- 应该跳转到符号定义位置

### 2. 查找引用 (Find References)

- 按 `Shift+F12` 或右键 → "Find All References"
- 应该显示该符号在文档中的所有引用

### 3. 文档符号 (Document Symbols)

- 按 `Ctrl+Shift+O` 或 `Cmd+Shift+O` (Mac)
- 应该显示文档中的所有符号（Character、Location、Event 等）

### 4. 重命名符号 (Rename Symbol)

- 将光标放在符号上
- 按 `F2` 或右键 → "Rename Symbol"
- 输入新名称，所有引用会自动更新

### 5. 悬停信息 (Hover)

- 将光标放在符号上
- 应该显示符号的详细属性（age、status 等）

### 6. 代码补全 (Completion)

- 输入 `@` 符号
- 应该显示可用的符号类型建议

### 7. 诊断信息 (Diagnostics)

- 打开 "Problems" 面板（`Ctrl+Shift+M`）
- 应该显示文档中的诊断错误和警告

## 🎯 符号语法示例

### 角色定义

```markdown
@Character: John Doe {
    age: 42,
    status: "alive",
    occupation: "Private Investigator"
}
```

### 地点定义

```markdown
@Location: The Rusty Anchor Pub {
    city: "Boston",
    description: "A dimly lit waterfront bar"
}
```

### 事件定义

```markdown
@Event: John Meets Client {
    chapter: 1,
    location: "The Rusty Anchor Pub",
    participants: ["John Doe", "Jane Smith"]
}
```

## 🔍 调试 LSP 服务器

### 启用详细日志

```bash
python -m novelwriter_lsp --debug
```

### 查看 LSP 通信日志

在 VS Code 中打开 "Output" 面板（`Ctrl+Shift+U`），选择 "Python" 查看日志。

### 运行测试套件

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定阶段的测试
pytest tests/phase1/ -v
pytest tests/phase2/ -v
pytest tests/phase3/ -v
pytest tests/phase4/ -v

# 查看测试覆盖率
pytest tests/ --cov=tests/phase1 --cov-report=html
```

## 📦 项目结构

```
LSP/
├── .vscode/                    # VS Code 配置
│   ├── settings.json          # 编辑器设置
│   ├── launch.json            # 调试配置
│   └── extensions.json        # 推荐扩展
├── novelwriter_lsp/           # Python 包
│   ├── __init__.py
│   ├── __main__.py           # 模块入口
│   ├── server.py             # LSP 服务器
│   ├── types.py              # 类型定义
│   ├── parser.py             # Markdown 解析器
│   ├── index.py              # 符号索引
│   ├── features/             # LSP 功能处理器
│   ├── agents/               # Agent 系统
│   └── storage/              # 存储系统
├── tests/                    # 测试套件
├── pyproject.toml           # 项目配置
└── README.md                # 项目说明
```

## 🐛 常见问题

### Q1: LSP 服务器没有启动

**解决方案：**
- 检查 Python 版本：`python --version`（需要 3.14+）
- 确认虚拟环境已激活
- 检查依赖是否安装：`pip list`

### Q2: 无法跳转到定义

**解决方案：**
- 确保文档已保存（`Ctrl+S`）
- 等待 LSP 服务器完成索引（几秒钟）
- 检查 "Problems" 面板是否有错误

### Q3: 代码补全不工作

**解决方案：**
- 检查 VS Code 设置中的 "quickSuggestions" 是否启用
- 确认符号语法正确（以 `@` 开头）
- 尝试重启 LSP 服务器：`Ctrl+Shift+P` → "Python: Restart Language Server"

### Q4: 诊断信息不显示

**解决方案：**
- 打开 "Problems" 面板（`Ctrl+Shift+M`）
- 检查文件是否已保存
- 确认 LSP 服务器正在运行

### Q5: 测试失败

**解决方案：**
```bash
# 清理测试缓存
pytest tests/ --cache-clear

# 运行特定测试文件查看详细错误
pytest tests/phase1/test_server.py -v -s

# 查看详细错误堆栈
pytest tests/ --tb=long
```

## 📚 进一步学习

- [LSP 协议规范](https://microsoft.github.io/language-server-protocol/)
- [pygls 文档](https://github.com/openlawlibrary/pygls)
- [项目 README.md](README.md)
- [LSP 架构设计](LSP_ARCHITECTURE_REDESIGN.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

ISC

---

**配置完成后，你就可以享受 NovelWriter LSP 带来的智能写作体验了！** 🎉
