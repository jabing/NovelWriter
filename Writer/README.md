# Novel Agent System

<p align="center">
  <strong>AI驱动的小说创作与发布系统</strong>
</p>

<p align="center">
  <a href="#项目简介">项目简介</a> ·
  <a href="#核心功能">核心功能</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#技术栈">技术栈</a>
</p>

---

## 项目简介

Novel Agent System 是一个完全自动化的 AI 小说写作和发布系统，专为网络小说市场设计。系统使用多个专业化 AI 代理协作工作，完成从选题、写作到发布的全流程。

## 核心功能

### 🤖 多代理协作系统
- **剧情规划代理** - 设计故事弧线和章节大纲
- **角色创建代理** - 构建主角和配角档案
- **世界观构建代理** - 创建完整的世界设定和规则
- **类型专精作家** - 5 种类型专业作家（科幻/奇幻/言情/历史/军事）
- **编辑审核代理** - 质量控制和修改建议
- **发布代理** - 多平台一键发布
- **市场研究代理** - 趋势分析和竞品调研
- **读者互动代理** - 评论分析和自动回复

### 📚 长篇一致性
- 支持 50-300 万字小说的上下文连贯
- OpenViking 内存系统：角色档案、剧情追踪、世界观管理
- 伏笔追踪和一致性检查

### 🎯 类型专精
| 类型 | 特点 |
|------|------|
| **科幻** | 硬科幻物理、太空探索、未来科技、时间旅行、人工智能 |
| **奇幻** | 魔法系统、世界构建、神话元素、种族设定、史诗叙事 |
| **言情** | 情感弧线、对话技巧、关系动态、情节节奏、情感张力 |
| **历史** | 时代考证、文化背景、历史事件、社会风貌、语言风格 |
| **军事** | 战术策略、武器装备、指挥体系、战场描写、军事术语 |

### 📤 多平台发布
- **Wattpad** - 最大读者群，适合连载
- **Royal Road** - 奇幻/科幻社区
- **Amazon KDP** - 付费出版
- 自动格式转换和平台适配

### 🔄 全自动化
- 每日自动生成章节并发布
- 任务调度系统
- 健康监控和告警

## 快速开始

### 环境要求
- Python 3.10+
- DeepSeek API 密钥

### 安装

```bash
# 1. 克隆项目
git clone <repository-url>
cd writer

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API 密钥

# 5. 验证安装
python -m src.main health-check
```

### 快速使用

#### 方式一：使用 Writer Studio GUI（推荐）

```bash
# 启动 Writer Studio
python -m src.main studio
```

在 Studio 中使用斜杠命令：
- `/project create` - 创建新项目
- `/plan quick <描述>` - 快速规划项目
- `/write chapter N` - 生成第 N 章
- `/character create` - 创建角色
- `/publish wattpad` - 发布到 Wattpad

#### 方式二：使用 CLI

```bash
# 运行完整工作流
python -m src.main workflow --genre fantasy --chapters 1

# 生成单章节
python -m src.main generate --novel-id my-novel --chapter 1 --genre fantasy

# 市场调研
python -m src.main market-research --genre fantasy
```

## 技术栈

| 类别 | 技术 |
|------|------|
| **编程语言** | Python 3.10+ |
| **LLM 集成** | DeepSeek API |
| **GUI 框架** | Flet |
| **任务调度** | Celery + Redis |
| **代码质量** | Ruff, Black, MyPy |
| **测试框架** | pytest |
| **配置管理** | Pydantic Settings |

## 文档

- [快速入门指南](docs/QUICKSTART.md) - 详细的使用教程
- [用户手册](docs/USER_MANUAL.md) - 完整的功能说明
- [AGENTS.md](AGENTS.md) - 代码规范和开发指南

## 开发

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 详细输出
pytest -v

# 运行特定测试
pytest tests/test_agents/test_writers.py
```

### 代码检查
```bash
# Lint 检查
ruff check .

# 格式化
black .

# 类型检查
mypy src/
```

## P0 改进说明

### 测试修复 (2026-03-08)

P0 阶段完成了关键的基础设施修复：

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 测试收集错误 | 64 | 6 |
| 测试通过率 | N/A | 95.11% |

### 依赖安装

以下依赖已添加到 `pyproject.toml`：
- `memsearch` - 向量内存系统
- `pydantic-settings` - 配置管理
- `tiktoken` - Token 计数
- `flet` - GUI 框架
- `build` - 包构建

### Python 版本兼容性

项目现统一要求 **Python 3.10+**：
- Writer: `>=3.10` (不变)
- LSP: `>=3.10` (从 3.14 降级)

### CI/CD

GitHub Actions 工作流已创建（`.github/workflows/ci.yml`），自动运行测试。

### 详细文档

完整的改进说明请参见 [P0_IMPROVEMENTS.md](../P0_IMPROVEMENTS.md)。

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

---

<p align="center">
  Made with ❤️ for storytellers
</p>
