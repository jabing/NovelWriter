# Novel Agent System 使用手册

**版本:** 0.1.0  
**更新日期:** 2026-02-18  
**适用平台:** Windows / Linux / macOS

---

## 目录

1. [系统概述](#1-系统概述)
2. [环境要求](#2-环境要求)
3. [安装指南](#3-安装指南)
4. [配置说明](#4-配置说明)
5. [CLI命令详解](#5-cli命令详解)
6. [Agent详解](#6-agent详解)
7. [写作工作流](#7-写作工作流)
8. [平台发布](#8-平台发布)
9. [内存系统](#9-内存系统)
10. [监控与维护](#10-监控与维护)
11. [故障排除](#11-故障排除)
12. [最佳实践](#12-最佳实践)
13. [API参考](#13-api参考)

---

## 1. 系统概述

### 1.1 什么是 Novel Agent System？

Novel Agent System 是一个**完全自动化的AI小说写作和发布系统**，专为欧美网络小说市场设计。系统使用多个专业化AI代理(Agent)协同工作，完成从选题、写作到发布的全流程。

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 多Agent协作 | 11+专业代理分工合作 |
| 📚 长篇一致性 | 支持50-300万字小说的上下文连贯 |
| 🎯 类型专精 | 5种类型专精作家（科幻/奇幻/言情/历史/军事）|
| 📤 多平台发布 | Wattpad, Royal Road, Amazon KDP |
| 🔄 全自动化 | 每日自动生成章节并发布 |
| 💬 读者互动 | 自动分析评论并回复 |

### 1.3 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Novel Agent System                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Plot Agent │  │Character    │  │Worldbuilding│         │
│  │  (剧情规划)  │  │Agent(角色)   │  │Agent(世界观) │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Writer Agents (写作代理)                  │ │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │ │
│  │  │ Sci-Fi │ │Fantasy │ │Romance │ │History │ │Military│ │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └──────┘ │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Editor Agent │  │Publisher    │  │Engagement   │         │
│  │(编辑审核)    │  │Agent(发布)   │  │Agent(互动)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Memory System (OpenViking)              │   │
│  │  角色档案 │ 剧情大纲 │ 世界设定 │ 伏笔追踪            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 环境要求

### 2.1 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 10GB | 50GB+ |
| 网络 | 稳定互联网连接 | - |

### 2.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | ≥3.10 | 推荐3.11或3.12 |
| pip | 最新版 | Python包管理器 |
| Git | 任意版本 | 用于版本控制（可选）|
| Redis | ≥5.0 | 任务调度（可选）|

### 2.3 API密钥

| 服务 | 用途 | 获取方式 |
|------|------|----------|
| DeepSeek API | 文本生成 | https://platform.deepseek.com |
| Wattpad API | 平台发布 | https://dev.wattpad.com |
| Royal Road | 平台发布 | 需联系管理员 |

---

## 3. 安装指南

### 3.1 快速安装

```bash
# 1. 克隆项目（或下载源码）
git clone <repository-url>
cd writer

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. 安装依赖
pip install -e ".[dev]"

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入API密钥

# 6. 验证安装
python -m src.main health-check
```

### 3.2 验证安装成功

运行健康检查命令：

```bash
python -m src.main health-check
```

预期输出：
```
System Health Check

Configuration:
  ✓ pyproject.toml found

Directories:
  ✓ Data directory
  ✓ Novels directory
  ✓ OpenViking directory

API Keys:
  ✓ DEEPSEEK_API_KEY

Health check complete!
```

---

## 4. 配置说明

### 4.1 环境变量配置

创建 `.env` 文件在项目根目录：

```bash
# ========== 必需配置 ==========
# DeepSeek API密钥（必需）
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# ========== 可选配置 ==========
# Redis连接（用于任务调度）
REDIS_URL=redis://localhost:6379/0

# Wattpad发布配置
WATTPAD_API_KEY=your_wattpad_api_key
WATTPAD_API_SECRET=your_wattpad_api_secret

# Royal Road发布配置
ROYALROAD_USERNAME=your_username
ROYALROAD_PASSWORD=your_password

# Amazon KDP配置
KDP_ACCESS_KEY=your_access_key
KDP_SECRET_KEY=your_secret_key

# ========== 系统配置 ==========
# 日志级别
LOG_LEVEL=INFO

# 生成配置
DEFAULT_MODEL=deepseek-chat
DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=4096
```

### 4.2 目录结构

```
writer/
├── src/                      # 源代码
│   ├── agents/               # AI代理
│   │   ├── base.py          # 基类
│   │   ├── plot.py          # 剧情代理
│   │   ├── character.py     # 角色代理
│   │   ├── worldbuilding.py # 世界观代理
│   │   ├── editor.py        # 编辑代理
│   │   ├── publisher.py     # 发布代理
│   │   ├── market_research.py # 市场研究
│   │   ├── comment_analyzer.py # 评论分析
│   │   ├── engagement.py    # 互动代理
│   │   ├── orchestrator.py  # 编排器
│   │   └── writers/         # 类型作家
│   │       ├── scifi.py
│   │       ├── fantasy.py
│   │       ├── romance.py
│   │       ├── history.py
│   │       └── military.py
│   ├── llm/                  # LLM集成
│   │   ├── base.py
│   │   └── deepseek.py
│   ├── memory/               # 内存系统
│   │   └── file_memory.py
│   ├── platforms/            # 发布平台
│   │   ├── wattpad.py
│   │   ├── royalroad.py
│   │   └── kindle.py
│   ├── scheduler/            # 任务调度
│   ├── monitoring/           # 监控告警
│   ├── utils/                # 工具函数
│   └── main.py               # CLI入口
├── tests/                    # 测试文件
├── data/                     # 数据存储
│   ├── novels/              # 小说内容
│   ├── openviking/          # 内存数据库
│   │   ├── memory/
│   │   │   ├── characters/  # 角色档案
│   │   │   ├── plot/        # 剧情大纲
│   │   │   └── world/       # 世界设定
│   │   └── skills/          # 写作技能
│   └── config/              # 配置文件
├── .env                      # 环境变量
├── pyproject.toml           # 项目配置
└── README.md
```

---

## 5. CLI命令详解

### 5.1 命令概览

```bash
python -m src.main [命令] [选项]
```

| 命令 | 说明 |
|------|------|
| `health-check` | 检查系统健康状态 |
| `market-research` | 市场调研与趋势分析 |
| `plan-novel` | 规划新小说（剧情/角色/世界观）|
| `trending-tags` | 获取平台热门标签 |
| `generate` | 生成单个章节 |
| `workflow` | 运行完整写作工作流 |

### 5.2 市场调研与规划（推荐首先执行）

#### 5.2.1 market-research 市场调研

分析市场趋势、热门类型、关键词优化：

```bash
python -m src.main market-research [选项]
```

**选项：**

| 选项 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--genre` | - | all | 分析类型 (scifi/fantasy/romance/history/military/all) |
| `--platform` | - | all | 分析平台 (wattpad/royalroad/amazon/qidian/jinjiang/zongheng/all) |
| `--keywords` | - | - | 逗号分隔的关键词列表 |
| `--competitors` | - | false | 包含竞品分析 |
| `--region` | - | all | 市场区域 (western/chinese/all) |

**支持的平台：**

| 平台 | 区域 | 说明 |
|------|------|------|
| Wattpad | 西方 | 全球最大网络小说平台 |
| Royal Road | 西方 | 奇幻/科幻社区 |
| Amazon | 西方 | KDP出版平台 |
| 起点中文网 | 中文 | 中国最大原创文学平台 |
| 晋江文学城 | 中文 | 女性向原创文学平台 |
| 纵横中文网 | 中文 | 综合性原创平台 |

**示例：**

```bash
# 基础市场调研
python -m src.main market-research

# 分析特定类型
python -m src.main market-research --genre fantasy --platform all

# 带关键词分析
python -m src.main market-research --genre romance --keywords "slow burn,enemies to lovers"

# 完整调研（含竞品分析）
python -m src.main market-research --genre scifi --competitors

# 中国市场调研
python -m src.main market-research --platform qidian --region chinese

# 晋江文学城调研
python -m src.main market-research --platform jinjiang
```

**输出示例：**

```
📊 Platform Trends

  WATTPAD
    • Werewolf Romance: 95% popularity (+15%)
    • Billionaire Romance: 88% popularity (+8%)
    • Fantasy Adventure: 85% popularity (+12%)

📈 High Growth Areas
  • LitRPG: +22% growth
  • Progression Fantasy: +25% growth

📚 Genre Analysis: FANTASY
  Market Saturation: high
  Top Tropes: Chosen One, Magic School, Dragon Rider

💡 Recommendations
  Priority: HIGH
  • Market is saturated - consider unique twist or subgenre combination
```

#### 5.2.2 plan-novel 小说规划

创建完整的小说规划（剧情大纲、角色档案、世界设定）：

```bash
python -m src.main plan-novel [选项]
```

**选项：**

| 选项 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--genre` | ✓ | - | 小说类型 |
| `--chapters` | - | 50 | 目标章节数 |
| `--premise` | - | - | 故事前提/核心概念 |
| `--structure` | - | three_act | 故事结构 (three_act/heros_journey/save_the_cat) |
| `--novel-id` | - | 自动生成 | 小说唯一标识符 |
| `--with-research` | - | false | 规划前先做市场调研 |

**示例：**

```bash
# 基础规划（50章奇幻小说）
python -m src.main plan-novel --genre fantasy

# 带前提的规划
python -m src.main plan-novel --genre scifi --chapters 100 \
  --premise "Humanity's first contact with an alien civilization goes wrong"

# 英雄之旅结构
python -m src.main plan-novel --genre fantasy --structure heros_journey \
  --premise "A farm girl discovers she is the last of an ancient order of mages"

# 带市场调研的完整规划
python -m src.main plan-novel --genre romance --chapters 30 \
  --premise "Two rival chefs compete for the same restaurant" \
  --with-research
```

**规划步骤：**

1. **Market Research** (可选) - 分析市场趋势
2. **Plot Planning** - 生成故事弧线和章节大纲
3. **Character Creation** - 创建主角和配角档案
4. **Worldbuilding** - 构建世界观设定

**输出文件：**

```
data/openviking/memory/
├── plot/
│   ├── main_arc.yaml      # 主线剧情
│   └── chapter_001.yaml   # 章节大纲
├── characters/
│   ├── main/              # 主角档案
│   └── supporting/        # 配角档案
└── novels/{novel-id}/
    └── metadata.json      # 小说元数据
```

#### 5.2.3 trending-tags 热门标签

获取特定平台的热门标签：

```bash
python -m src.main trending-tags [选项]
```

**选项：**

| 选项 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--platform` | - | wattpad | 平台 (wattpad/royalroad/amazon) |
| `--limit` | - | 20 | 显示标签数量 |

**示例：**

```bash
# Wattpad热门标签
python -m src.main trending-tags --platform wattpad

# Royal Road前10标签
python -m src.main trending-tags --platform royalroad --limit 10
```

### 5.4 health-check 健康检查

检查系统配置和依赖：

```bash
python -m src.main health-check
```

检查项目：
- 配置文件是否存在
- 数据目录是否创建
- API密钥是否配置

### 5.3 generate 生成章节

生成单个小说章节：

```bash
python -m src.main generate [选项]
```

**选项：**

| 选项 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--novel-id` | ✓ | - | 小说唯一标识符 |
| `--chapter` | ✓ | - | 章节编号 |
| `--genre` | - | fantasy | 类型 (scifi/fantasy/romance/history/military) |
| `--outline` | - | - | 章节大纲/摘要 |

**示例：**

```bash
# 基础用法
python -m src.main generate --novel-id my-novel --chapter 1

# 指定类型
python -m src.main generate --novel-id scifi-story --chapter 5 --genre scifi

# 提供大纲
python -m src.main generate \
  --novel-id fantasy-epic \
  --chapter 10 \
  --genre fantasy \
  --outline "The hero discovers a hidden power within themselves"
```

**输出示例：**

```
Generating Chapter 10
  Novel ID: fantasy-epic
  Genre: fantasy

Generating content...

✓ Chapter generated successfully!
     Generation Summary     
┌────────────────┬─────────┐
│ Metric         │ Value   │
├────────────────┼─────────┤
│ Word Count     │ 1894    │
│ Chapter Number │ 10      │
│ Genre          │ fantasy │
└────────────────┴─────────┘

Preview:
## Chapter 10: The Unwritten Word

The bell above the door of *Arcanum & Ephemera* jingled...
```

### 5.4 workflow 工作流

运行完整的小说写作工作流：

```bash
python -m src.main workflow [选项]
```

**选项：**

| 选项 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--genre` | - | fantasy | 小说类型 |
| `--chapters` | - | 1 | 生成章节数 |
| `--full` | - | false | 完整工作流（包含发布）|

**工作流步骤：**

1. **Plot Planning** - 剧情规划
2. **Character Creation** - 角色创建
3. **Worldbuilding** - 世界观构建
4. **Chapter Writing** - 章节写作
5. **Editing** - 编辑审核
6. **Publishing** - 发布（仅 `--full` 模式）

**示例：**

```bash
# 基础工作流（1章节）
python -m src.main workflow --genre fantasy --chapters 1

# 完整工作流（10章节 + 发布）
python -m src.main workflow --genre scifi --chapters 10 --full

# 言情小说工作流
python -m src.main workflow --genre romance --chapters 5
```

---

## 6. Agent详解

### 6.1 Agent概览

| Agent | 功能 | 输入 | 输出 |
|-------|------|------|------|
| Plot Agent | 剧情结构规划 | 类型、目标章节 | 剧情大纲、章节分配 |
| Character Agent | 角色创建与发展 | 类型、角色数量 | 角色档案、关系图 |
| Worldbuilding Agent | 世界观构建 | 类型、主题 | 世界设定、规则系统 |
| Writer Agents | 内容生成 | 章节大纲、角色、世界观 | 章节内容 |
| Editor Agent | 质量审核 | 内容、角色、世界观 | 评分、修改建议 |
| Publisher Agent | 平台发布 | 内容、平台配置 | 发布结果 |
| Market Research | 市场趋势分析 | 平台、时间范围 | 热门主题、趋势报告 |
| Comment Analyzer | 评论分析 | 评论文本 | 情感分析、反馈分类 |
| Engagement Agent | 读者互动 | 评论、回复模板 | 回复内容 |
| Orchestrator | 流程编排 | 工作流配置 | 执行结果 |

### 6.2 类型作家 (Writer Agents)

每种类型有专门的写作知识和风格：

#### Sci-Fi Writer (科幻作家)

```yaml
专精领域:
  - 硬科幻物理
  - 太空探索
  - 未来科技
  - 时间旅行
  - 人工智能
风格特点:
  - 技术准确性
  - 逻辑严密
  - 未来感
```

#### Fantasy Writer (奇幻作家)

```yaml
专精领域:
  - 魔法系统
  - 世界构建
  - 神话元素
  - 种族设定
  - 史诗叙事
风格特点:
  - 想象力丰富
  - 沉浸式体验
  - 英雄主义
```

#### Romance Writer (言情作家)

```yaml
专精领域:
  - 情感弧线
  - 对话技巧
  - 关系动态
  - 情节节奏
  - 情感张力
风格特点:
  - 情感深度
  - 角色驱动
  - 浪漫氛围
```

#### History Writer (历史作家)

```yaml
专精领域:
  - 时代考证
  - 文化背景
  - 历史事件
  - 社会风貌
  - 语言风格
风格特点:
  - 历史准确性
  - 时代感
  - 文化深度
```

#### Military Writer (军事作家)

```yaml
专精领域:
  - 战术策略
  - 武器装备
  - 指挥体系
  - 战场描写
  - 军事术语
风格特点:
  - 专业性
  - 紧张感
  - 策略深度
```

### 6.3 使用示例

```python
import asyncio
from src.agents.writers.writer_factory import get_writer
from src.llm.deepseek import DeepSeekLLM
from src.memory.file_memory import FileMemory

async def generate_fantasy_chapter():
    # 初始化
    llm = DeepSeekLLM()
    memory = FileMemory()
    writer = get_writer("fantasy", llm)
    writer.memory = memory
    
    # 生成章节
    result = await writer.execute({
        "chapter_number": 1,
        "chapter_outline": "A young wizard discovers hidden powers",
        "characters": [
            {"name": "Elena", "role": "protagonist"},
            {"name": "Master Theron", "role": "mentor"},
        ],
        "world_context": {
            "genre": "fantasy",
            "setting": "The Kingdom of Aethermoor",
            "magic_system": "Elemental magic based on emotions",
        },
    })
    
    if result.success:
        print(result.data["content"])
    else:
        print("Errors:", result.errors)

asyncio.run(generate_fantasy_chapter())
```

---

## 7. 写作工作流

### 7.1 单章节生成流程

```
┌──────────────┐
│ 用户输入      │
│ novel-id     │
│ chapter      │
│ genre        │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 加载上下文    │◄──── Memory System
│ - 角色信息    │
│ - 剧情进度    │
│ - 世界设定    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Writer Agent │
│ 类型专精写作  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Editor Agent │
│ 质量审核      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 保存内容      │────► Memory System
│ 更新进度      │
└──────────────┘
```

### 7.2 完整工作流（从零开始）

```
Phase 1: 规划
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│ 1. 市场研究     │──►│ 2. 剧情规划     │──►│ 3. 角色创建     │
│ 趋势分析       │   │ 大纲/章节分配    │   │ 主角/配角档案   │
└────────────────┘   └────────────────┘   └───────┬────────┘
                                                   │
Phase 2: 构建                                      │
┌────────────────┐   ┌────────────────┐          │
│ 4. 世界观构建   │◄──┤ 5. 技能定义     │◄─────────┘
│ 设定/规则      │   │ 写作风格指南    │
└───────┬────────┘   └────────────────┘
        │
Phase 3: 写作
        │
┌───────▼────────┐   ┌────────────────┐   ┌────────────────┐
│ 6. 章节生成     │──►│ 7. 编辑审核     │──►│ 8. 修订         │
│ (循环执行)      │   │ 质量评分        │   │ 根据反馈修改    │
└───────┬────────┘   └────────────────┘   └────────────────┘
        │
Phase 4: 发布
        │
┌───────▼────────┐   ┌────────────────┐   ┌────────────────┐
│ 9. 格式转换     │──►│ 10. 平台发布    │──►│ 11. 互动管理    │
│ 平台适配       │   │ Wattpad/RR/KDP │   │ 评论/回复      │
└────────────────┘   └────────────────┘   └────────────────┘
```

### 7.3 日常运营流程

```bash
# 每日定时任务（建议使用cron或系统任务计划）

# 1. 检查系统健康
python -m src.main health-check

# 2. 生成今日章节
python -m src.main generate \
  --novel-id daily-novel \
  --chapter $(cat data/novels/daily-novel/current_chapter.txt) \
  --genre fantasy

# 3. 发布到平台
# (通过workflow --full自动完成)
```

---

## 8. 平台发布

### 8.1 支持的平台

| 平台 | 格式要求 | 发布方式 | 特点 |
|------|----------|----------|------|
| **Wattpad** | HTML/文本 | API | 最大读者群，适合连载 |
| **Royal Road** | BBCode | API/模拟 | 奇幻/科幻社区 |
| **Amazon KDP** | EPUB/MOBI | API | 付费出版，收益分成 |

### 8.2 Wattpad发布配置

```bash
# .env 配置
WATTPAD_API_KEY=your_api_key
WATTPAD_API_SECRET=your_api_secret
```

```python
from src.platforms.wattpad import WattpadPlatform

async def publish_to_wattpad():
    platform = WattpadPlatform()
    
    result = await platform.publish({
        "title": "Chapter 1: The Beginning",
        "content": "... chapter content ...",
        "story_id": "123456789",
        "tags": ["fantasy", "magic", "adventure"],
    })
    
    print(f"Published: {result['url']}")
```

### 8.3 Royal Road发布配置

```bash
# .env 配置
ROYALROAD_USERNAME=your_username
ROYALROAD_PASSWORD=your_password
```

### 8.4 Amazon KDP发布配置

```bash
# .env 配置
KDP_ACCESS_KEY=your_access_key
KDP_SECRET_KEY=your_secret_key
```

---

## 9. 内存系统

### 9.1 OpenViking架构

内存系统使用基于文件的YAML存储，确保长篇内容的一致性。

```
data/openviking/
├── memory/
│   ├── characters/           # 角色档案
│   │   ├── main/            # 主角
│   │   │   └── char_001.yaml
│   │   └── supporting/      # 配角
│   │       └── char_002.yaml
│   ├── plot/                 # 剧情追踪
│   │   ├── main_arc.yaml    # 主线剧情
│   │   └── chapter_001.yaml # 章节剧情
│   └── world/               # 世界设定
│       ├── geography.yaml
│       └── rules.yaml
└── skills/                   # 写作技能
    ├── fantasy_writing.yaml
    └── scifi_writing.yaml
```

### 9.2 角色档案格式

```yaml
# data/openviking/memory/characters/main/char_001.yaml
id: char_001
name: Elena Thornwood
role: protagonist
age: 19
occupation: Apprentice Wizard

appearance:
  hair: "silver-white, waist-length"
  eyes: "pale blue, almost white"
  height: "5'6\""
  distinctive_features:
    - "faint silver markings on arms (appear when using magic)"

personality:
  traits:
    - curious
    - determined
    - compassionate
  flaws:
    - impulsive
    - self-doubting
  speech_patterns:
    - "uses formal language when nervous"
    - "tends to ask many questions"

backstory: |
  Born in the village of Misthollow, Elena discovered her magical
  abilities at age 12 when she accidentally froze a pond during
  summer. Taken as an apprentice by Master Theron at the Academy
  of Aethermoor...

development:
  chapter_1:
    events: ["discovers hidden power"]
    emotional_state: "confused, frightened"
  chapter_2:
    events: ["first lesson with Master Theron"]
    emotional_state: "eager, nervous"

relationships:
  - character_id: char_002
    name: "Master Theron"
    relationship: "mentor"
    notes: "patient but demanding"
```

### 9.3 剧情追踪格式

```yaml
# data/openviking/memory/plot/main_arc.yaml
title: "The Aethermoor Chronicles"
genre: fantasy

main_conflict: |
  Elena must master her dangerous powers before the Shadow
  Conclave awakens an ancient evil.

structure:
  act_1:
    chapters: "1-10"
    focus: "discovery and training"
  act_2:
    chapters: "11-30"
    focus: "challenges and growth"
  act_3:
    chapters: "31-40"
    focus: "confrontation and resolution"

foreshadowing:
  - item: "mysterious pendant"
    introduced_chapter: 1
    payoff_chapter: 25
    notes: "Contains fragment of ancient power"
```

### 9.4 内存查询

```python
from src.memory.file_memory import FileMemory

memory = FileMemory()

# 查询角色
character = memory.get_character("char_001")
print(character["name"])  # Elena Thornwood

# 查询剧情
plot = memory.get_plot("main_arc")
print(plot["main_conflict"])

# 更新角色状态
memory.update_character("char_001", {
    "development": {
        "chapter_5": {
            "events": ["faced first real enemy"],
            "emotional_state": "shaken but resolute",
        }
    }
})
```

---

## 10. 监控与维护

### 10.1 系统监控

```python
from src.monitoring.health import HealthChecker
from src.monitoring.alerts import AlertManager

# 健康检查
checker = HealthChecker()
status = await checker.check_all()

print(status)
# {
#     "api": "healthy",
#     "memory": "healthy", 
#     "storage": "healthy",
#     "overall": "healthy"
# }

# 告警配置
alert_manager = AlertManager()
alert_manager.add_rule(
    name="high_error_rate",
    condition="error_rate > 0.1",
    action="send_email",
)
```

### 10.2 日志管理

日志级别可在 `.env` 中配置：

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

日志文件位置：`data/logs/`

### 10.3 数据备份

```bash
# 备份命令
cp -r data/ backup/data_$(date +%Y%m%d)/

# 或使用脚本
python scripts/backup.py --output backup/
```

### 10.4 定期维护任务

```bash
# 每周清理缓存
python scripts/cleanup.py --cache

# 每月归档旧章节
python scripts/archive.py --older-than 30
```

---

## 11. 故障排除

### 11.1 常见问题

#### 问题：API调用失败

```
Error: DeepSeek API key required
```

**解决方案：**
```bash
# 检查环境变量
echo $DEEPSEEK_API_KEY  # Linux/macOS
echo %DEEPSEEK_API_KEY%  # Windows

# 确保.env文件存在且包含正确配置
cat .env | grep DEEPSEEK
```

#### 问题：内存加载失败

```
Error: Character not found: char_001
```

**解决方案：**
```bash
# 检查文件是否存在
ls data/openviking/memory/characters/main/

# 如果缺失，重新初始化
python -m src.main workflow --genre fantasy --chapters 1
```

#### 问题：生成内容质量差

**可能原因和解决方案：**

| 原因 | 解决方案 |
|------|----------|
| 大纲不明确 | 提供详细的 `--outline` |
| 类型不匹配 | 确认 `--genre` 正确 |
| 上下文丢失 | 检查内存系统完整性 |

#### 问题：发布失败

```
Error: Wattpad authentication failed
```

**解决方案：**
1. 检查API密钥是否过期
2. 验证API权限配置
3. 查看平台API状态

#### 问题：F6/F9键在Windows CMD中无法使用

**症状：**
- F6/F9键无响应
- Ctrl+Enter无法提交多行输入

**原因：**
Windows CMD（命令提示符）是**传统终端**，缺少现代终端功能：
1. **不支持F键**：F6/F9等功能键在CMD中不可靠
2. **不支持Ctrl+Enter**：Ctrl+Enter可能被识别为普通Enter

**解决方案：**

**方案A：使用Windows Terminal（推荐）**
Windows 11已预装Windows Terminal，提供完整TUI支持：
1. 按 `Win + R`，输入 `wt` 并按回车
2. 或从开始菜单搜索"Windows Terminal"
3. 在Windows Terminal中运行程序，所有功能正常

**方案B：使用备用快捷键（仅限CMD）**
系统已自动检测CMD并启用备用快捷键：
- **多行输入**：`Ctrl+M` 或 `Alt+M`（替代F6）
- **提交发送**：`Ctrl+Enter` 或 `Alt+Enter`（替代F9）

**方案C：升级终端环境**
1. **Windows Terminal**：Windows 11自带，功能完整
2. **PowerShell**：比CMD更现代，但仍有部分限制
3. **Git Bash**：提供类Unix环境，功能完整

**技术说明：**
- 系统已内置终端检测功能，自动适配不同终端
- 启动时会显示当前终端类型和建议
- CMD用户会看到警告信息和备用快捷键提示

---

#### 功能：Ctrl+V 粘贴多行文本

**功能说明：**

系统现在支持直接使用 `Ctrl+V` 粘贴多行文本，无需按 F6/F9！

**使用方法：**

1. **复制多行文本**到剪贴板
2. **按 `Ctrl+V`** 在输入框中粘贴
3. **自动检测**：如果包含多行内容，会显示粘贴指示器
4. **按 `Enter`** 发送多行内容
5. **按 `Esc`** 取消粘贴

**粘贴指示器说明：**

当粘贴多行文本时，底部会显示黄色提示条：
```
📋 [pasted N lines]  Enter 发送 · Esc 取消
```

**不同终端的支持情况：**

| 终端 | 多行粘贴支持 | 说明 |
|------|-------------|------|
| Windows Terminal | ✅ 完全支持 | 原生支持 bracketed paste |
| VS Code Terminal | ✅ 完全支持 | 原生支持 bracketed paste |
| Windows CMD | ✅ 支持 | 通过 pyperclip 读取剪贴板 |
| PowerShell | ✅ 支持 | 通过 pyperclip 读取剪贴板 |
| Git Bash | ✅ 完全支持 | 原生支持 bracketed paste |

**依赖要求：**

Windows CMD/PowerShell 需要安装 pyperclip：
```bash
pip install pyperclip
```

**注意事项：**
- 单行文本会直接粘贴到输入框
- 多行文本会触发粘贴指示器模式
- 粘贴后按 Enter 即可发送，无需其他快捷键

---

#### 问题：如何使用鼠标滚动聊天记录？

**解决方法：**

系统根据终端类型智能启用鼠标支持：

**支持鼠标滚动的终端：**
- Windows Terminal ✅
- VS Code Terminal ✅
- PowerShell ✅
- Git Bash ✅

**不支持鼠标滚动的终端：**
- Windows CMD ❌（需要使用键盘滚动）

**键盘滚动（所有终端都支持）：**

| 按键 | 功能 |
|------|------|
| `↑` / `↓` | 上下滚动 |
| `PgUp` / `PgDn` | 快速翻页 |
| `Home` / `End` | 跳到开头/结尾 |

---

#### 问题：如何使用鼠标选择和复制文本？

**解决方法：**

**Windows Terminal / VS Code / PowerShell：**
1. **鼠标滚轮**：滚动聊天记录
2. **鼠标左键拖动**：选择文本
3. **鼠标右键**：复制或粘贴

**Windows CMD：**
1. **鼠标左键拖动**：选择文本
2. **鼠标右键**：复制选中的文本或粘贴
3. **注意**：CMD 中鼠标滚轮由终端处理，应用内滚动请使用键盘

**不同终端的操作方式：**

| 终端 | 滚动 | 选择方式 | 复制方式 |
|------|------|----------|----------|
| Windows CMD | 键盘 | 左键拖动选择 | 右键复制 |
| Windows Terminal | 滚轮/键盘 | 左键拖动选择 | Ctrl+Shift+C 或右键 |
| PowerShell | 滚轮/键盘 | 左键拖动选择 | 右键或 Enter |
| Git Bash | 滚轮/键盘 | 左键拖动选择 | 右键菜单 |

**注意事项：**
- Windows CMD 用户建议使用键盘滚动（PgUp/PgDn）
- Windows Terminal 提供最佳的鼠标体验
- 选择文本时可能需要先按住左键，再拖动
- 某些终端可能需要启用"快速编辑模式"

### 11.2 调试模式

启用详细日志：

```bash
# 设置调试级别
export LOG_LEVEL=DEBUG  # Linux/macOS
set LOG_LEVEL=DEBUG     # Windows

# 运行命令
python -m src.main generate --novel-id test --chapter 1
```

### 11.3 重置系统

```bash
# 清理所有数据（谨慎操作！）
rm -rf data/novels/*
rm -rf data/openviking/memory/*

# 重新初始化
python -m src.main health-check
```

---

## 12. 最佳实践

### 12.1 写作质量

1. **提供详细大纲**：每章提供100-200字的大纲摘要
2. **维护角色一致性**：定期更新角色档案
3. **伏笔管理**：在内存系统中追踪所有伏笔
4. **定期审核**：每10章运行一次完整审核

### 12.2 发布策略

1. **定时发布**：固定时间发布，培养读者习惯
2. **平台适配**：不同平台使用不同的标题和标签
3. **互动优先**：优先回复高互动评论

### 12.3 系统运维

1. **每日检查**：运行 `health-check`
2. **每周备份**：备份 `data/` 目录
3. **监控API用量**：避免超额费用
4. **版本控制**：使用Git管理配置和内存文件

### 12.4 成本优化

| 策略 | 说明 |
|------|------|
| 批量生成 | 一次生成多章减少API调用 |
| 缓存复用 | 复用已生成的背景描述 |
| 精简提示 | 优化prompt减少token消耗 |

---

## 13. API参考

### 13.1 Agent基类

```python
from src.agents.base import BaseAgent, AgentResult

class MyAgent(BaseAgent):
    async def execute(self, input_data: dict) -> AgentResult:
        # 实现代理逻辑
        return AgentResult(
            success=True,
            data={"result": "..."},
            errors=[],
            warnings=[],
        )
```

### 13.2 LLM接口

```python
from src.llm.deepseek import DeepSeekLLM

llm = DeepSeekLLM(
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=4096,
)

# 简单生成
response = await llm.generate("Write a fantasy scene...")

# 带系统提示
response = await llm.generate_with_system(
    system_prompt="You are a fantasy writer.",
    user_prompt="Write a scene about...",
)
```

### 13.3 内存接口

```python
from src.memory.file_memory import FileMemory

memory = FileMemory()

# 角色操作
memory.save_character(char_data)
character = memory.get_character("char_001")
characters = memory.list_characters(role="main")

# 剧情操作
memory.save_plot(plot_data)
plot = memory.get_plot("main_arc")

# 世界设定
memory.save_world(world_data)
world = memory.get_world()
```

### 13.4 平台接口

```python
from src.platforms.wattpad import WattpadPlatform
from src.platforms.royalroad import RoyalRoadPlatform

# Wattpad
wattpad = WattpadPlatform()
result = await wattpad.publish({
    "title": "Chapter 1",
    "content": "...",
    "story_id": "123",
})

# Royal Road
rr = RoyalRoadPlatform()
result = await rr.publish({
    "title": "Chapter 1",
    "content": "...",
    "fiction_id": "456",
})
```

---

## 14. 故事连续性保证

### 14.1 概述

故事连续性是小说创作的核心要求。Novel Agent System 默认启用 **STRICT 模式**，确保：

- 前序章节缺失时停止生成
- 章节不完整时自动重试
- KG 更新失败时停止后续生成
- 同名角色可正确区分

### 14.2 配置选项

通过环境变量或配置文件调整连续性检查行为：

```bash
# 环境变量
CONTINUITY_STRICTNESS=STRICT  # 默认值
CONTINUITY_MAX_RETRIES=3
CONTINUITY_MIN_CHAPTER_WORDS=500
ENABLE_CHARACTER_ID=false
```

或通过代码配置：

```python
from src.novel_agent.novel.continuity_config import ContinuityConfig, ContinuityStrictness

config = ContinuityConfig(
    strictness=ContinuityStrictness.STRICT,  # OFF | WARNING | STRICT
    max_retries=3,
    min_chapter_words=500,
    enable_character_id=False,
)
```

### 14.3 严格级别说明

| 级别 | 行为 | 适用场景 |
|------|------|----------|
| **STRICT** (默认) | 不合格时停止生成，强制重试 | 生产环境，确保质量 |
| WARNING | 不合格时记录警告，继续生成 | 测试环境 |
| OFF | 跳过所有检查 | 调试模式（不推荐） |

> ⚠️ **重要**: 连续性是强制要求，不建议在生产环境使用 OFF 模式。

### 14.4 角色唯一ID系统

启用角色唯一ID可以区分同名角色，解决"三个林晓"问题：

```python
from src.novel_agent.novel.character_registry import CharacterRegistry

# 创建注册表
registry = CharacterRegistry()

# 注册角色
role_id = registry.register("林晓", role="protagonist", chapter=1)
# 返回: "char_林晓_001"

# 同名角色自动分配不同ID
role_id2 = registry.register("林晓", role="antagonist")
# 返回: "char_林晓_002"

# 查询角色
entry = registry.get_by_id("char_林晓_001")
entries = registry.get_by_name("林晓")  # 返回所有同名角色
```

### 14.5 章节验证

章节生成后自动验证完整性：

```python
from src.novel_agent.novel.chapter_validator import ChapterValidator

validator = ChapterValidator()
result = validator.check_completeness(content, min_words=500)

# 检查结果
result.is_valid       # 是否通过所有检查
result.word_count     # 字数统计（中文计字、英文计词）
result.has_title      # 是否有章节标题
result.has_ending     # 是否有结束标记
result.issues         # 发现的问题列表
result.suggestions    # 改进建议列表
```

验证规则：
- **标题检测**：检查"第X章"或"Chapter X"格式
- **字数统计**：中文计字、英文计词
- **结束标记**：检测"完"、"待续"、"---"等标记

### 14.6 迁移现有项目

为现有项目添加角色唯一ID：

```bash
# 预览变更
python scripts/migrate_character_ids.py --project <path> --dry-run

# 执行迁移（自动创建备份）
python scripts/migrate_character_ids.py --project <path>

# 回滚到迁移前状态
python scripts/migrate_character_ids.py --project <path> --rollback
```

---

## 附录

### A. 命令速查表

```bash
# ========== 健康检查 ==========
python -m src.main health-check

# ========== 市场调研与规划 ==========
# 市场趋势分析
python -m src.main market-research --genre fantasy --platform all

# 竞品分析
python -m src.main market-research --genre scifi --competitors

# 热门标签
python -m src.main trending-tags --platform wattpad --limit 20

# 小说规划
python -m src.main plan-novel --genre fantasy --chapters 50 --premise "Your story idea"

# 带市场调研的规划
python -m src.main plan-novel --genre romance --chapters 30 --with-research

# ========== 内容生成 ==========
# 生成单章节
python -m src.main generate --novel-id <id> --chapter <n> --genre <type>

# 完整工作流
python -m src.main workflow --genre <type> --chapters <n> --full

# ========== 开发测试 ==========
# 运行测试
python -m pytest

# 类型检查
python -m mypy src/
```

### B. 支持的类型

| 类型 | 标识符 | 说明 |
|------|--------|------|
| 科幻 | `scifi` | 科学幻想、未来科技 |
| 奇幻 | `fantasy` | 魔法、中世纪、神话 |
| 言情 | `romance` | 爱情、情感、关系 |
| 历史 | `history` | 历史背景、时代剧 |
| 军事 | `military` | 战争、战术、军队 |

### C. 联系支持

- **问题反馈**: GitHub Issues
- **功能建议**: GitHub Discussions
- **文档更新**: 查看 `docs/` 目录

---

*本手册最后更新: 2026-02-18*
