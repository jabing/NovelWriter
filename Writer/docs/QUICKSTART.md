# 快速入门指南

## 启动 Writer Studio

Writer Studio 是一个交互式写作界面，提供完整的写作功能：

```bash
# 启动 Writer Studio GUI
python -m src.main studio
```

### Studio 内置命令

在 Studio 中使用以下斜杠命令：

| 命令 | 说明 |
|------|------|
| `/project list` | 列出所有项目 |
| `/project create` | 创建新项目 |
| `/project info` | 显示当前项目信息 |
| `/plan quick <描述>` | 快速规划项目 |
| `/plan interactive` | 交互式规划 |
| `/write chapter N` | 生成第N章 |
| `/character create` | 创建角色 |
| `/outline create` | 创建大纲 |
| `/research trends` | 市场趋势分析 |
| `/publish wattpad` | 发布到 Wattpad |
| `/publish royalroad` | 发布到 Royal Road |
| `/status` | 显示当前状态 |
| `/help` | 显示所有命令 |

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Enter` | 发送消息 |
| `Tab` | 切换 Agent |
| `↑↓` | 浏览历史 |
| `Esc` | 取消 |

---

## CLI 命令行工具

如果不使用 GUI，可以通过命令行运行：

### 基本命令

```bash
# 检查系统健康状态
python -m src.main health-check

# 显示帮助
python -m src.main --help
```

### 生成章节

```bash
# 生成单章节
python -m src.main generate --novel-id <novel-id> --chapter 1 --genre fantasy

# 参数说明：
# --novel-id: 项目ID（必需）
# --chapter: 章节号（必需）
# --genre: 类型（可选：scifi, fantasy, romance, history, military）
```

### 工作流

```bash
# 运行基础工作流
python -m src.main workflow --genre fantasy --chapters 1

# 运行完整工作流（含发布）
python -m src.main workflow --full
```

### 每日自动发布

```bash
# 启动每日发布调度器
python -m src.main daily start --novel-id <novel-id> --platform wattpad --time 09:00

# 查看调度器状态
python -m src.main daily status

# 停止调度器
python -m src.main daily stop
```

---

## 完整示例流程

### 方式一：使用 Studio GUI（推荐）

```bash
# 1. 启动 Studio
python -m src.main studio

# 2. 在 Studio 中执行：
/project create --title "我的奇幻小说" --genre fantasy --premise "一个年轻法师发现能与远古巨龙交流"
/plan quick "一个年轻法师发现能与远古巨龙交流，必须拯救被黑暗势力控制的王国"
/character create
/outline create
/write chapter 1
/status
```

### 方式二：使用 CLI

```bash
# 1. 检查系统
python -m src.main health-check

# 2. 运行工作流
python -m src.main workflow --genre fantasy --chapters 1

# 3. 设置每日发布
python -m src.main daily start --novel-id <生成的novel-id> --platform wattpad --time 09:00
```

---

## 类型对照表

| 中文 | 英文标识符 | 特点 |
|------|-----------|------|
| 科幻 | `scifi` | 未来科技、太空、AI |
| 奇幻 | `fantasy` | 魔法、中世纪、神话 |
| 言情 | `romance` | 爱情、情感、关系 |
| 历史 | `history` | 历史背景、时代剧 |
| 军事 | `military` | 战争、战术、军队 |

---

## 平台对照表

| 平台 | 标识符 | 特点 |
|------|--------|------|
| Wattpad | `wattpad` | 最大读者群，适合连载 |
| Royal Road | `royalroad` | 奇幻/科幻社区 |
| Amazon KDP | `kindle` | 付费出版 |

---

## 运行测试

```bash
# 运行所有测试
python -m pytest

# 详细输出
python -m pytest -v

# 运行特定测试
python -m pytest tests/test_agents/test_writers.py
```

---

## 代码检查

```bash
# Lint 检查
ruff check .

# 格式化
black .

# 类型检查
mypy src/
```

---

## 下一步

1. 查看 [README.md](../README.md) 了解项目概述
2. 查看 [AGENTS.md](../AGENTS.md) 了解代码规范
3. 查看 [完整使用手册](./USER_MANUAL.md)
