# Writer Studio - OpenCode 风格 UI 设计

## 概念

将 Writer Studio 改造为类似 OpenCode 的自然语言交互界面：
- 主界面是一个聊天窗口
- 用户可以用自然语言与 AI 交流
- 支持 /commands 快捷操作
- Tab 键切换不同的功能模块/Agent

---

## 界面布局

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 📚 Writer Studio                    The Gilded Cage    [Romance Writer]   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  用户: 帮我写第三章，Clara在派对上的场景                         [14:32]    │
│                                                                            │
│  ✍️ Romance Writer:                                                        │
│  好的，我来为你写第三章。Clara在Helena的派对上...                          │
│                                                                            │
│  ─────────────────────────────────────────────────────────────────────    │
│                                                                            │
│  用户: /project list                                                       │
│                                                                            │
│  📋 Projects:                                                              │
│  • The Gilded Cage (350章, 进度 0%)                                      │
│  • 镀金笼子 (350章, 进度 0%)                                               │
│                                                                            │
│  ─────────────────────────────────────────────────────────────────────    │
│                                                                            │
│  用户: 这个场景需要更多紧张感                                               │
│                                                                            │
│  ✍️ Romance Writer:                                                        │
│  明白，我来增加紧张感。Clara注意到角落里的那个男人...                      │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ [Tab] 切换Agent │ [/] 命令 │ [↑↓] 历史 │ [Ctrl+C] 退出                     │
├────────────────────────────────────────────────────────────────────────────┤
│ > 帮我修改这段描写，增加Clara内心的不安感_                                 │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 交互模式

### 1. 自然语言对话
用户直接输入文字，当前 Agent 响应：
```
> 帮我写第五章的开头
> Clara和Julian的关系发展太快了，放慢节奏
> 这个对话感觉不自然，改一下
```

### 2. Slash Commands
```
> /project list          # 列出所有项目
> /project switch gilded_cage   # 切换项目
> /project create        # 创建新项目
> /write chapter 10      # 写第10章
> /write batch 5         # 批量写5章
> /publish wattpad       # 发布到Wattpad
> /publish all           # 发布到所有平台
> /research trends       # 市场研究
> /research competitors  # 竞品分析
> /status               # 查看状态
> /outline              # 查看大纲
> /settings             # 设置
> /help                 # 帮助
> /clear                # 清屏
```

### 3. Tab 切换 Agent
```
当前 Agent: [Romance Writer]
按 Tab 循环切换:
  → [Romance Writer] - 言情写作
  → [Sci-Fi Writer] - 科幻写作
  → [Fantasy Writer] - 奇幻写作
  → [Editor] - 编辑审核
  → [Market Research] - 市场研究
  → [Publisher] - 发布管理
  → [Orchestrator] - 项目协调
```

---

## 状态栏信息

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📚 Writer Studio │ The Gilded Cage │ 📝 0/350章 │ 🔵 Planning │ [Romance]  │
└─────────────────────────────────────────────────────────────────────────────┘

状态栏显示:
- 当前项目名称
- 写作进度
- 项目状态
- 当前 Agent
```

---

## Agent 列表

| Agent | 功能 | 示例命令 |
|-------|------|----------|
| 🖋️ Romance | 言情小说写作 | "写一段Clara的心理描写" |
| 🚀 Sci-Fi | 科幻小说写作 | "设计一个外星文明" |
| 🔮 Fantasy | 奇幻小说写作 | "创建魔法体系" |
| 📖 Editor | 编辑审核 | "检查第三章的语法错误" |
| 📊 Research | 市场研究 | "分析Wattpad言情趋势" |
| 📤 Publisher | 发布管理 | "发布最新章节" |
| 🎯 Orchestrator | 项目协调 | "规划接下来的写作计划" |

---

## 技术实现

### 消息结构
```python
@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str
    agent: str | None = None
    command: str | None = None
```

### 命令处理
```python
class CommandRegistry:
    commands = {
        "/project": handle_project,
        "/write": handle_write,
        "/publish": handle_publish,
        "/research": handle_research,
        "/status": handle_status,
        "/help": handle_help,
    }
```

### Agent 切换
```python
class AgentManager:
    agents = [
        ("romance", RomanceWriter),
        ("scifi", SciFiWriter),
        ("fantasy", FantasyWriter),
        ("editor", EditorAgent),
        ("research", MarketResearchAgent),
        ("publisher", PublisherAgent),
    ]
    
    def switch_agent(self, direction: int):
        # Tab 切换
        pass
```

---

## 文件结构

```
src/studio/
├── chat/
│   ├── __init__.py
│   ├── app.py           # 主应用
│   ├── message.py       # 消息处理
│   ├── commands.py      # 命令注册
│   ├── agents.py        # Agent 管理
│   └── widgets.py       # UI 组件
├── core/
│   ├── state.py         # 状态管理
│   └── history.py       # 对话历史
└── tui/
    └── ...              # 旧版 TUI (保留)
```
