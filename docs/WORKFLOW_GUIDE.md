# NovelWriter 工作流程指导

> AI 驱动的小说创作与发布系统 - CLI 和 Web UI 使用指南

---

## 目录

1. [系统概述](#系统概述)
2. [CLI 工作流程](#cli-工作流程)
3. [Web UI 工作流程](#web-ui-工作流程)
4. [API 参考](#api-参考)
5. [常见工作场景](#常见工作场景)

---

## 系统概述

NovelWriter 提供两种交互方式：

| 方式 | 适用场景 | 入口 |
|------|----------|------|
| **CLI** | 自动化脚本、服务器部署、快速操作 | `novel-agent` 命令 |
| **Web UI** | 可视化管理、实时监控、交互式创作 | http://localhost:5173 |

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  CLI (Click)│  │ Web (Vue3) │  │  Studio GUI (Flet) │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼───────────────────┼──────────────┘
          │                │                   │
          ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                     API 层 (FastAPI)                         │
│  REST API: /api/projects, /api/novels, /api/agents, etc.   │
│  WebSocket: /ws/agents (实时代理状态)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     业务逻辑层                               │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────┐  │
│  │ Project   │ │  Agent    │ │  Memory   │ │  Platform   │  │
│  │ Manager   │ │ Orchestr. │ │  System   │ │  Adapters   │  │
│  └───────────┘ └───────────┘ └───────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     数据存储层                               │
│  SQLite (元数据) │ ChromaDB (向量) │ 文件系统 (章节/配置)   │
└─────────────────────────────────────────────────────────────┘
```

---

## CLI 工作流程

### 安装与启动

```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# 2. 安装依赖
pip install -e ".[dev]"

# 3. 验证安装
novel-agent --version
novel-agent --help
```

### CLI 命令总览

```
novel-agent
├── generate          # 生成单章节
├── workflow          # 运行完整工作流
├── health-check      # 系统健康检查
├── studio            # 启动 GUI Studio
├── outline           # 创建故事大纲
├── character         # 创建角色
├── plan              # 快速规划项目
├── status            # 查看项目/系统状态
├── read              # 阅读生成的章节
│
├── project           # 项目管理
│   ├── create        # 创建新项目
│   ├── list          # 列出所有项目
│   ├── info          # 显示项目详情
│   ├── update        # 更新项目信息
│   ├── switch        # 切换当前项目
│   └── delete        # 删除项目
│
├── daily             # 每日发布调度
│   ├── start         # 启动定时发布
│   ├── stop          # 停止调度
│   └── status        # 查看调度状态
│
├── settings          # Studio 设置
│   ├── show          # 显示当前设置
│   ├── set-mode      # 设置质量模式
│   ├── set           # 设置单个参数
│   └── reset         # 重置为默认值
│
└── monitor           # 系统监控
    ├── health        # 健康检查
    ├── metrics       # 性能指标
    ├── alerts        # 告警历史
    ├── status        # 系统状态
    └── export        # Prometheus 导出
```

### CLI 详细命令说明

#### 1. 项目管理 (project)

```bash
# 创建新项目
novel-agent project create --title "我的奇幻小说" --genre fantasy --chapters 50

# 列出所有项目
novel-agent project list

# 查看项目详情
novel-agent project info --id <project-id>
# 或查看当前项目
novel-agent project info

# 切换当前项目
novel-agent project switch <project-id>
# 或通过编号切换
novel-agent project switch 1

# 更新项目信息
novel-agent project update --title "新标题" --status writing

# 删除项目（需要确认）
novel-agent project delete <project-id> --confirm
```

#### 2. 内容生成 (generate / workflow)

```bash
# 生成单章节
novel-agent generate --novel-id <id> --chapter 1 --genre fantasy

# 运行完整工作流
novel-agent workflow --full
# 执行流程：
#   1. Plot Planning (情节规划)
#   2. Character Creation (角色创建)
#   3. World Building (世界观构建)
#   4. Chapter Writing (章节写作)
#   5. Editing (编辑修订)
#   6. Publishing (发布)
```

#### 3. 每日发布调度 (daily)

```bash
# 启动每日发布（每日 09:00 发布到 Wattpad）
novel-agent daily start --novel-id <id> --platform wattpad --time 09:00

# 启动每日发布（发布到 Royal Road）
novel-agent daily start --novel-id <id> --platform royalroad --time 21:00

# 查看调度状态
novel-agent daily status

# 停止调度
novel-agent daily stop
```

#### 4. 阅读章节 (read)

```bash
# 列出所有章节
novel-agent read --list

# 阅读最新章节
novel-agent read --latest

# 阅读指定章节
novel-agent read 1      # 按编号
novel-agent read chapter_001  # 按文件名
```

#### 5. 系统设置 (settings)

```bash
# 查看当前设置
novel-agent settings show

# 设置质量模式
novel-agent settings set-mode fast      # 快速模式
novel-agent settings set-mode balanced  # 平衡模式（默认）
novel-agent settings set-mode high      # 高质量模式
novel-agent settings set-mode ultra     # 超高质量模式

# 设置单个参数
novel-agent settings set iterations 5
novel-agent settings set approval_threshold 8
novel-agent settings set enable_learning true
novel-agent settings set ui_language zh

# 重置设置
novel-agent settings reset
```

**设置参数说明：**

| 参数 | 范围 | 说明 |
|------|------|------|
| `iterations` | 1-10 | 最大修订迭代次数 |
| `approval_threshold` | 7-10 | 批准的最低分数 |
| `auto_revise_threshold` | 5-9 | 自动修订的最低分数 |
| `enable_learning` | true/false | 启用学习模块 |
| `ui_language` | en/zh | 界面语言 |

#### 6. 系统监控 (monitor)

```bash
# 系统健康检查
novel-agent monitor health

# 查看性能指标
novel-agent monitor metrics
novel-agent monitor metrics --detail  # 详细信息

# 查看告警历史
novel-agent monitor alerts
novel-agent monitor alerts --severity error  # 按严重级别过滤
novel-agent monitor alerts --limit 50        # 限制数量

# 系统状态概览
novel-agent monitor status

# 启动 Prometheus 导出端点
novel-agent monitor export --port 9090
```

#### 7. GUI Studio (studio)

```bash
# 启动 Writer Studio（Flet GUI）
novel-agent studio

# 功能包括：
# - 项目管理界面
# - AI 代理交互
# - 实时写作预览
# - 设置配置
```

### CLI 典型工作流程

```
┌──────────────────────────────────────────────────────────────┐
│                    新项目完整流程                             │
└──────────────────────────────────────────────────────────────┘

Step 1: 环境检查
$ novel-agent health-check
✓ Configuration loaded
✓ Data directory present
✓ API keys configured

Step 2: 创建项目
$ novel-agent project create --title "星际迷途" --genre scifi --chapters 30
✓ Project created: novel_a1b2c3d4
  Title: 星际迷途
  Genre: scifi
  Target: 30 chapters, ~90,000 words

Step 3: 切换到新项目
$ novel-agent project switch novel_a1b2c3d4
✓ Switched to: 星际迷途

Step 4: 运行工作流
$ novel-agent workflow --full
Running Full Workflow
  1. Plot Planning... ✓
  2. Character Creation... ✓
  3. World Building... ✓
  4. Chapter Writing... [进行中]
  ...

Step 5: 查看状态
$ novel-agent status
Current Project: 星际迷途 (novel_a1b2c3d4)
  Progress: 5/30 chapters
  Words: 15,234 / 90,000

Step 6: 阅读章节
$ novel-agent read --latest
Reading: chapter_005
[章节内容...]

Step 7: 设置每日发布
$ novel-agent daily start --novel-id novel_a1b2c3d4 --platform wattpad --time 09:00
✓ Daily scheduler started!
  Next run scheduled for: 2026-03-15 09:00:00
```

---

## Web UI 工作流程

### 启动 Web 服务

```bash
# 终端 1: 启动后端 API
cd NovelWriter
python -m uvicorn src.novel_agent.api.main:app --reload --port 8000

# 终端 2: 启动前端
cd NovelWriter/web
npm install
npm run dev
```

### 访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| 前端界面 | http://localhost:5173 | Vue3 Web UI |
| API 文档 | http://localhost:8000/docs | FastAPI Swagger UI |
| API ReDoc | http://localhost:8000/redoc | FastAPI ReDoc |

### Web UI 页面导航

```
┌────────────────────────────────────────────────────────────────┐
│  NovelWriter                                    [🌙 Dark] [⚙️] │
├────────────────────────────────────────────────────────────────┤
│ [📊 Dashboard] [📚 Projects] [✍️ Writing] [📖 Reading]          │
│ [🤖 Agents] [📤 Publish] [💬 Comments] [📈 Analytics]           │
└────────────────────────────────────────────────────────────────┘
```

### 页面功能详解

#### 1. Dashboard (仪表盘)

**路径**: `/` 或 `/dashboard`

**功能**:
- 项目概览卡片
- 快速操作按钮
- 最近活动列表
- 写作统计图表
- AI 代理状态指示器

**使用流程**:
```
打开 Dashboard → 查看当前项目进度 → 点击快捷操作
```

#### 2. Projects (项目管理)

**路径**: `/projects`

**功能**:
- 项目列表展示
- 新建项目向导
- 项目搜索/过滤
- 批量操作

**项目详情页** (`/projects/:id`):
- 基本信息 (标题、类型、状态)
- 章节列表与排序
- 角色管理标签页
- 大纲编辑器
- 发布配置

**创建项目流程**:
```
1. 点击 "新建项目" 按钮
2. 填写基本信息:
   - 标题 (必填)
   - 类型 (fantasy/scifi/romance/history/military)
   - 语言 (zh/en)
   - 目标章节数
   - 目标字数
   - 简介/前提
   - 主题标签
3. 配置高级选项:
   - 叙事视角 (第一人称/第三人称)
   - 基调风格
   - 目标读者
   - 故事结构
   - 内容分级
   - 发布平台
4. 点击 "创建" 保存
```

#### 3. Writing (写作)

**路径**: `/writing`

**功能**:
- 实时写作编辑器
- AI 写作助手面板
- 章节导航
- 自动保存
- Markdown 支持

**写作流程**:
```
1. 选择要编辑的项目和章节
2. 在编辑器中写作
3. AI 助手提供:
   - 情节建议
   - 角色对话
   - 场景描写
   - 风格调整
4. 保存草稿或发布
```

#### 4. Reading (阅读)

**路径**: `/reading`

**功能**:
- 书架视图展示所有作品
- 章节列表导航
- Markdown 渲染阅读
- 阅读进度追踪
- 全屏阅读模式

**全屏阅读器** (`/reader/:chapter/:total`):
- 无干扰阅读界面
- 翻页导航
- 阅读进度显示

#### 5. Agents (AI 代理)

**路径**: `/agents`

**功能**:
- 代理列表与状态
- 实时 WebSocket 状态更新
- 执行历史查看
- 手动触发执行

**可用代理类型**:

| 代理 | 功能 | 触发条件 |
|------|------|----------|
| Orchestrator | 总协调器 | 工作流启动 |
| Plot Agent | 情节规划 | 新项目/大纲变更 |
| Character Agent | 角色创建 | 新角色/角色更新 |
| Worldbuilding Agent | 世界观构建 | 世界观设定 |
| Editor Agent | 编辑修订 | 章节完成后 |
| Publisher Agent | 发布管理 | 发布触发 |
| SciFi Writer | 科幻写作 | 科幻类型项目 |
| Fantasy Writer | 奇幻写作 | 奇幻类型项目 |
| Romance Writer | 言情写作 | 言情类型项目 |
| Historical Writer | 历史写作 | 历史类型项目 |

**代理状态说明**:
```
🟢 running    - 正在执行
🔵 idle       - 空闲等待
🟡 paused     - 已暂停
🔴 failed     - 执行失败
✅ completed  - 已完成
```

#### 6. Publish (发布)

**路径**: `/publish`

**功能**:
- 发布平台管理
- 平台连接配置
- 一键发布
- 发布状态跟踪

**支持平台**:

| 平台 | 状态 | 说明 |
|------|------|------|
| Wattpad | ✅ 启用 | 全球最大小说平台 |
| Royal Road | ✅ 启用 | Web serial 平台 |
| Amazon KDP | ✅ 启用 | Kindle 自出版 |
| Webnovel | ⏳ 计划中 | 待启用 |

**发布流程**:
```
1. 选择项目和平台
2. 选择要发布的章节
3. 配置发布设置:
   - 标题
   - 简介
   - 标签
   - 封面
4. 预览发布内容
5. 点击 "发布"
6. 查看发布状态
```

#### 7. Comments (评论)

**路径**: `/comments`

**功能**:
- 跨平台评论聚合
- 评论回复管理
- 读者反馈分析

#### 8. Analytics (分析)

**路径**: `/analytics`

**功能**:
- 写作统计图表
- 阅读数据分析
- 发布效果追踪
- 读者互动趋势

**统计指标**:
- 总字数 / 日均字数
- 章节完成率
- 总阅读量
- 投票/收藏数
- 评论数

#### 9. Settings (设置)

**路径**: `/settings`

**功能**:
- 界面语言切换 (中文/英文)
- 主题切换 (亮色/暗色)
- API 密钥配置
- 代理设置
- 数据备份/恢复

---

## API 参考

### REST API 端点

#### Projects API (`/api/projects`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/projects` | 获取项目列表 |
| POST | `/api/projects` | 创建新项目 |
| GET | `/api/projects/{id}` | 获取项目详情 |
| PUT | `/api/projects/{id}` | 更新项目 |
| DELETE | `/api/projects/{id}` | 删除项目 |

#### Chapters API (`/api/novels/{novel_id}/chapters`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/novels/{id}/chapters` | 获取章节列表 |
| POST | `/api/novels/{id}/chapters` | 创建新章节 |
| GET | `/api/novels/{id}/chapters/{num}` | 获取章节内容 |
| PUT | `/api/novels/{id}/chapters/{num}` | 更新章节 |
| DELETE | `/api/novels/{id}/chapters/{num}` | 删除章节 |
| PUT | `/api/novels/{id}/chapters/{num}/reorder` | 重排章节顺序 |

#### Characters API (`/api/novels/{novel_id}/characters`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/novels/{id}/characters` | 获取角色列表 |
| POST | `/api/novels/{id}/characters` | 创建新角色 |
| GET | `/api/characters/{id}` | 获取角色详情 |
| PUT | `/api/characters/{id}` | 更新角色 |
| DELETE | `/api/characters/{id}` | 删除角色 |

#### Agents API (`/api/agents`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/agents` | 获取代理类型列表 |
| GET | `/api/agents/{type}/status` | 获取代理状态 |
| POST | `/api/agents/{type}/execute` | 执行代理任务 |

#### Publishing API (`/api/publishing`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/publishing/platforms` | 获取平台列表 |
| POST | `/api/publishing/novels/{id}/publish` | 发布小说 |
| GET | `/api/publishing/comments/{id}` | 获取评论 |

#### Monitoring API (`/api/monitoring`)

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/monitoring/health` | 健康检查 |
| GET | `/api/monitoring/metrics` | 性能指标 |
| GET | `/api/monitoring/alerts` | 告警列表 |

### WebSocket

**端点**: `/ws/agents`

**消息格式**:
```json
{
  "type": "agent_status",
  "data": {
    "agent_type": "plot",
    "status": "running",
    "progress": 0.5,
    "message": "Processing..."
  }
}
```

**客户端使用**:
```typescript
import { useAgentStore } from '@/stores/agentStore'

const agentStore = useAgentStore()
agentStore.connectWebSocket()

// 响应式访问代理状态
const agents = computed(() => agentStore.agents)
const connectionStatus = computed(() => agentStore.connectionStatus)
```

---

## 常见工作场景

### 场景 1: 新建并完成一部小说

```bash
# CLI 方式
novel-agent project create --title "龙族崛起" --genre fantasy --chapters 20
novel-agent project switch novel_xxx
novel-agent workflow --full
novel-agent read --list
novel-agent daily start --novel-id novel_xxx --platform wattpad
```

```
Web UI 方式:
1. 访问 http://localhost:5173
2. 点击 Projects → 新建项目
3. 填写表单并保存
4. 进入项目详情 → 点击 "开始创作"
5. 在 Agents 页面监控进度
6. 在 Reading 页面阅读
7. 在 Publish 页面配置发布
```

### 场景 2: 日常写作与发布

```bash
# CLI 方式
novel-agent status                    # 检查进度
novel-agent generate --novel-id xxx --chapter 15  # 生成新章节
novel-agent read 15                   # 阅读并审核
novel-agent daily status              # 检查发布状态
```

```
Web UI 方式:
1. Dashboard 查看进度
2. Writing 页面编辑章节
3. Agents 页面触发 AI 辅助
4. Publish 页面手动发布
```

### 场景 3: 系统维护与监控

```bash
# CLI 方式
novel-agent health-check              # 健康检查
novel-agent monitor health            # 详细检查
novel-agent monitor metrics --detail  # 性能指标
novel-agent monitor alerts            # 告警历史
novel-agent settings show             # 当前设置
```

```
Web UI 方式:
1. Settings 页面配置
2. Analytics 页面查看统计
3. 通过 API 文档调试: http://localhost:8000/docs
```

### 场景 4: 多项目管理

```bash
# CLI 方式
novel-agent project list              # 列出所有项目
novel-agent project switch 2          # 切换到第2个项目
novel-agent project info              # 查看当前项目
novel-agent project update --status writing  # 更新状态
```

```
Web UI 方式:
1. Projects 页面查看所有项目
2. 点击项目卡片进入详情
3. 使用项目切换下拉菜单
4. 项目详情页更新设置
```

---

## 附录: 数据存储位置

```
data/
├── glossary.json              # 术语表
├── openviking/
│   └── memory/
│       └── novels/
│           └── {novel_id}/
│               ├── chapters/
│               │   ├── chapter_001.json
│               │   ├── chapter_001.md
│               │   └── ...
│               ├── characters/
│               ├── outline.json
│               └── worldbuilding.json
├── chroma/                    # ChromaDB 向量存储
└── studio_state.json          # Studio 状态
```

---

## 故障排除

### CLI 问题

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError` | 运行 `pip install -e ".[dev]"` |
| `DEEPSEEK_API_KEY not set` | 设置环境变量或在 `.env` 中配置 |
| `Flet import error` | 运行 `pip install flet` |

### Web UI 问题

| 问题 | 解决方案 |
|------|----------|
| 白屏/加载失败 | 检查后端是否启动，运行 `npm run dev` |
| API 请求失败 | 检查 CORS 配置，确认端口 8000 可访问 |
| WebSocket 断开 | 检查 `/ws/agents` 端点，确认 WebSocket 连接 |

### 日志查看

```bash
# CLI 日志
# 日志级别由 LOG_LEVEL 环境变量控制
export LOG_LEVEL=DEBUG

# API 日志
# uvicorn 会输出请求日志
python -m uvicorn src.novel_agent.api.main:app --reload --log-level debug
```

---

*最后更新: 2026-03-14*