# src/studio/chat/flet_app.py
"""Flet-based chat application - Modern GUI alternative to Textual."""

import asyncio
import logging
import sys
from pathlib import Path

import flet as ft

from src.llm.final_model_config import DOMESTIC_MODELS, INTERNATIONAL_MODELS
from src.llm.optimized_model_router import OptimizedModelRouter, TaskType
from src.studio.chat.agents import AgentManager
from src.studio.chat.commands import CommandRegistry
from src.studio.chat.message import ChatMessage, ConversationHistory, MessageRole
from src.studio.core.state import get_studio_state

# Set up debug logging to file
LOG_FILE = Path("data/studio/debug.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8', mode='w'),
        logging.StreamHandler(sys.stderr),
    ]
)

logger = logging.getLogger(__name__)
logger.info("=== Writer Studio Debug Log Started ===")


class ChatFletApp:
    """Writer Studio Chat Interface using Flet."""

    def __init__(self) -> None:
        self.state = get_studio_state()
        self.agent_manager = AgentManager()
        self.command_registry = CommandRegistry(self.state)
        self.history = ConversationHistory()
        self._input_history: list[str] = []
        self._history_index = -1

        # Initialize LLM
        self._init_llm()

    def _init_llm(self) -> None:
        """Initialize LLM client using optimized model router."""
        # Initialize attributes first
        self.llm = None
        self.model_name = "未配置"
        self._model_config = None
        self._infini_model = None

        try:
            # Use optimized router for CLI interaction (GLM-5 - FREE)
            router = OptimizedModelRouter(language="zh")
            assignment = router.route(TaskType.CLI_INTERACTION)

            # Get the appropriate model based on assignment
            model_key = assignment.primary_model
            if model_key in DOMESTIC_MODELS:
                model_config = DOMESTIC_MODELS[model_key]
            elif model_key in INTERNATIONAL_MODELS:
                model_config = INTERNATIONAL_MODELS[model_key]
            else:
                raise ValueError(f"Unknown model: {model_key}")

            # Store config for later use
            self._model_config = model_config

            # Create LLM instance based on provider
            if model_config.provider == "zhipu":
                from src.llm.glm import GLMLLM
                self.llm = GLMLLM(
                    api_key=model_config.api_key,
                    model=model_config.model_id
                )
            elif model_config.provider == "infini":
                # For Infini AI (OpenAI compatible)
                from openai import AsyncOpenAI
                self.llm = AsyncOpenAI(
                    api_key=model_config.api_key,
                    base_url=model_config.base_url
                )
                self._infini_model = model_config.model_id
            else:
                # Fallback
                self.llm = None
                self.model_name = f"不支持的提供商: {model_config.provider}"
                return

            self.model_name = model_config.name
            logger.info(f"LLM initialized: {self.model_name}")

        except Exception as e:
            self.llm = None
            self.model_name = f"错误: {e}"
            logger.error(f"LLM初始化失败: {e}")

    def main(self, page: ft.Page) -> None:
        """Main entry point for Flet app."""
        self.page = page

        # Page setup
        page.title = "Writer Studio"
        page.theme_mode = ft.ThemeMode.DARK
        page.window.width = 1200
        page.window.height = 800
        page.padding = 0

        # ========== STATUS BAR ==========
        # Using ft.Text with ref for reactive updates
        self.project_text = ft.Text("📚 无项目", size=14, weight=ft.FontWeight.BOLD)
        self.progress_text = ft.Text("", size=14, color="grey400")
        self.agent_text = ft.Text("✍️ Romance Writer", size=14, weight=ft.FontWeight.BOLD)
        self.model_text = ft.Text("🔮 deepseek-chat", size=14, color="grey400")

        status_bar = ft.Container(
            content=ft.Row(
                [
                    self.project_text,
                    self.progress_text,
                    ft.VerticalDivider(width=1, color="grey700"),
                    self.agent_text,
                    ft.VerticalDivider(width=1, color="grey700"),
                    self.model_text,
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="surfacevariant",
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )

        # ========== CHAT VIEW ==========
        self.chat_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            auto_scroll=True,
        )

        chat_container = ft.Container(
            content=self.chat_list,
            expand=True,
            bgcolor="background",
        )

        # ========== INPUT AREA ==========
        self.input_field = ft.TextField(
            hint_text="💬 输入消息... (Ctrl+Enter 发送, Tab: Agent, ↑↓: 历史)",
            expand=True,
            border_color="primary",
            filled=True,
            fill_color="surface",
            text_style=ft.TextStyle(size=14),
            autofocus=True,
            multiline=True,
            min_lines=1,
            max_lines=5,
            on_change=self._on_input_change,
            on_submit=self._on_multiline_submit,
        )

        send_button = ft.IconButton(
            icon=ft.icons.Icons.SEND,
            icon_color="primary",
            on_click=self._on_send_click,
            tooltip="发送 (Ctrl+Enter)",
        )

        agent_button = ft.IconButton(
            icon=ft.icons.Icons.SWAP_HORIZ,
            icon_color="secondary",
            on_click=self._on_switch_agent,
            tooltip="切换 Agent (Tab)",
        )

        clear_button = ft.IconButton(
            icon=ft.icons.Icons.CLEAR_ALL,
            icon_color="error",
            on_click=self._on_clear_chat,
            tooltip="清屏",
        )

        help_button = ft.IconButton(
            icon=ft.icons.Icons.HELP_OUTLINE,
            icon_color="info",
            on_click=self._on_show_help,
            tooltip="帮助",
        )

        input_row = ft.Row(
            [
                self.input_field,
                send_button,
                agent_button,
                clear_button,
                help_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        input_container = ft.Container(
            content=input_row,
            bgcolor="surfacevariant",
            padding=ft.padding.all(10),
        )

        # ========== MAIN LAYOUT ==========
        main_column = ft.Column(
            [
                status_bar,
                chat_container,
                input_container,
            ],
            expand=True,
            spacing=0,
        )

        page.add(main_column)

        # ========== KEYBOARD SHORTCUTS ==========
        page.on_keyboard_event = self._on_keyboard

        # Initialize
        self._update_status_bar()
        self._show_welcome()
        # Note: focus() is async, use autofocus property on TextField instead

    # ========== STATUS BAR UPDATE ==========
    def _update_status_bar(self) -> None:
        """Update status bar - Flet automatically refreshes!"""
        # Re-fetch state to ensure we have the latest data
        self.state = get_studio_state()
        current = self.state.get_current_project()
        agent = self.agent_manager.current

        if current:
            self.project_text.value = f"📚 {current.title}"
            self.progress_text.value = f"({current.completed_chapters}/{current.target_chapters})"
        else:
            self.project_text.value = "📚 无项目"
            self.progress_text.value = ""

        self.agent_text.value = f"{agent.icon} {agent.name}"
        self.model_text.value = f"🔮 {self.model_name}"

        # Force update each control individually
        self.project_text.update()
        self.progress_text.update()
        self.agent_text.update()
        self.model_text.update()
        self.page.update()

    # ========== MESSAGE RENDERING ==========
    def _add_message(self, message: ChatMessage) -> None:
        """Add a message to the chat view."""
        if message.role == MessageRole.USER:
            container = ft.Container(
                content=ft.Column([
                    ft.Text("你", color="grey400", size=12),
                    ft.Text(
                        message.content[:2000] if len(message.content) > 2000 else message.content,
                        selectable=True,
                        size=14,
                    ),
                ]),
                bgcolor="primarycontainer",
                padding=10,
                border_radius=10,
                margin=ft.margin.only(bottom=5),
            )
        elif message.role == MessageRole.ASSISTANT:
            agent_icon = {
                "romance": "✍️", "scifi": "🚀", "fantasy": "🔮",
                "editor": "📖", "research": "📊", "publisher": "📤",
                "orchestrator": "🎯", "illustrator": "🎨",
            }.get(message.agent, "🤖")

            container = ft.Container(
                content=ft.Column([
                    ft.Text(f"{agent_icon} {message.agent or 'Assistant'}",
                           color="cyan", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        message.content,
                        selectable=True,
                        size=14,
                    ),
                ]),
                bgcolor="surface",
                padding=10,
                border_radius=10,
                margin=ft.margin.only(bottom=5, left=20),
            )
        else:  # SYSTEM
            container = ft.Container(
                content=ft.Text(message.content, color="yellow"),
                padding=10,
                border_radius=5,
                margin=ft.margin.only(bottom=5),
            )

        self.chat_list.controls.append(container)
        self.chat_list.update()
        self.page.update()

    def _add_user_message(self, content: str) -> None:
        """Add user message."""
        self.history.add_user(content)
        self._add_message(self.history.messages[-1])

    def _add_assistant_message(self, content: str, agent: str | None = None) -> None:
        """Add assistant message."""
        if agent is None:
            agent = self.agent_manager.current_type.value
        self.history.add_assistant(content, agent)
        self._add_message(self.history.messages[-1])

    def _add_system_message(self, content: str) -> None:
        """Add system message."""
        self.history.add_system(content)
        self._add_message(self.history.messages[-1])

    def _add_progress_message(self, content: str, current: int, total: int) -> ft.Container:
        """Add a progress message with animated indicator.

        Args:
            content: The message content
            current: Current step number
            total: Total steps

        Returns:
            The container control for later removal
        """
        # Animated spinner characters (will be updated by timer)
        progress_ring = ft.ProgressRing(
            width=16,
            height=16,
            stroke_width=2,
            color="cyan",
        )

        progress_text = ft.Text(
            f"执行 {current}/{total}: {content}",
            color="yellow",
            size=14,
        )

        container = ft.Container(
            content=ft.Row(
                [
                    progress_ring,
                    progress_text,
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            padding=10,
            border_radius=5,
            margin=ft.margin.only(bottom=5),
            bgcolor="surfacevariant",
        )

        self.chat_list.controls.append(container)
        self.chat_list.update()
        self.page.update()

        return container

    def _update_progress_message(
        self,
        container: ft.Container,
        content: str,
        current: int,
        total: int,
        is_complete: bool = False
    ) -> None:
        """Update an existing progress message.

        Args:
            container: The container returned by _add_progress_message
            content: The message content
            current: Current step number
            total: Total steps
            is_complete: Whether this step is complete
        """
        if container.content is None:
            return

        row = container.content  # ft.Row

        if is_complete:
            # Replace spinner with checkmark
            row.controls[0] = ft.Icon(
                ft.icons.Icons.CHECK_CIRCLE,
                color="green",
                size=16,
            )
            row.controls[1].value = f"完成 {current}/{total}: {content}"
            row.controls[1].color = "green"
        else:
            row.controls[1].value = f"执行 {current}/{total}: {content}"

        container.update()
        self.page.update()

    def _remove_progress_message(self, container: ft.Container) -> None:
        """Remove a progress message from chat."""
        if container in self.chat_list.controls:
            self.chat_list.controls.remove(container)
            self.chat_list.update()
            self.page.update()

    # ========== WELCOME MESSAGE ==========
    def _show_welcome(self) -> None:
        """Show welcome message."""
        welcome = """# 📚 欢迎使用 Writer Studio

我是你的 AI 写作助手。我可以帮助你：

- **写作** 小说、章节和场景
- **编辑** 改进你的内容
- **研究** 市场趋势和竞品分析
- **发布** 到 Wattpad、Royal Road 等平台

## 快速开始

1. 选择或创建项目: `/project list` 或 `/project create`
2. 开始写作: `/write chapter 1` 或直接描述你想写的内容
3. 切换 Agent: 点击按钮或按 `Tab` 键
4. 命令补全: 输入 `/` 后可用 ↑↓ 选择命令

## 常用命令

| 命令 | 说明 |
|------|------|
| `/project list` | 列出所有项目 |
| `/write chapter N` | 生成第N章 |
| `/publish wattpad` | 发布到 Wattpad |
| `/research trends` | 分析市场趋势 |
| `/status` | 显示当前状态 |
| `/help` | 显示所有命令 |

**💡 提示**: 输入 `/help` 查看更多命令，或直接用自然语言与我交流！
"""
        self._add_assistant_message(welcome)

    # ========== INPUT HANDLING ==========
    def _on_input_change(self, e: ft.ControlEvent) -> None:
        """Handle input changes."""
        # Could add command autocomplete here
        pass

    def _on_multiline_submit(self, e: ft.ControlEvent) -> None:
        """Handle Ctrl+Enter key submit in multiline mode."""
        self._process_input()

    def _on_submit(self, e: ft.ControlEvent) -> None:
        """Handle Enter key submit."""
        self._process_input()

    def _on_send_click(self, e: ft.ControlEvent) -> None:
        """Handle send button click."""
        self._process_input()

    def _process_input(self) -> None:
        """Process user input."""
        text = self.input_field.value.strip()
        if not text:
            # Even on empty input, refocus the field
            async def refocus_empty():
                await self.input_field.focus()
            asyncio.create_task(refocus_empty())
            return

        # Clear input
        self.input_field.value = ""
        self.input_field.update()

        # Add to history
        self._input_history.append(text)
        self._history_index = len(self._input_history)

        # Add user message
        self._add_user_message(text)

        # Process asynchronously and refocus when done
        async def process_and_refocus():
            await self._process_input_async(text)
            # Refocus after processing completes - focus() is a coroutine
            await self.input_field.focus()

        asyncio.create_task(process_and_refocus())

def _is_long_running_command(self, text: str) -> bool:
    """Check if command is likely to take a long time."""
    long_running_prefixes = [
        "/outline create",
        "/character create",
        "/write chapter",
        "/write batch",
        "/cover generate",
        "/plan quick",      # NEW
        "/plan start",      # NEW
        "/collaborate",     # NEW
        "/illustrate",      # NEW
    ]
    text_lower = text.lower()
    return any(text_lower.startswith(prefix) for prefix in long_running_prefixes)

def _add_processing_message(self, command: str) -> int:
    """Add a processing message with animated progress ring."""
    # Determine what kind of operation is happening
    if "outline" in command.lower():
        msg = "正在生成大纲..."
        time_hint = "预计需要 1-3 分钟"
    elif "character" in command.lower():
        msg = "正在创建角色..."
        time_hint = "预计需要 30-60 秒"
    elif "write" in command.lower():
        msg = "正在生成章节..."
        time_hint = "预计需要 1-2 分钟"
    elif "cover" in command.lower():
        msg = "正在生成封面..."
        time_hint = "预计需要 30-60 秒"
    elif "plan" in command.lower():            # NEW
        msg = "正在制定项目计划..."
        time_hint = "预计需要 1-2 分钟"
    elif "collaborate" in command.lower():     # NEW
        msg = "正在协作生成内容..."
        time_hint = "预计需要 2-3 分钟"
    elif "illustrate" in command.lower():      # NEW
        msg = "正在生成场景插图..."
        time_hint = "预计需要 30-60 秒"
    else:
        msg = "正在处理..."
        time_hint = ""

    # Animated progress ring (same style as existing _add_progress_message)
    progress_ring = ft.ProgressRing(
        width=20,
        height=20,
        stroke_width=2,
        color="cyan",
    )

    # Build content
    controls = [
        ft.Row(
            [
                progress_ring,
                ft.Text(msg, color="cyan", size=14, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
    ]

    if time_hint:
        controls.append(ft.Text(time_hint, color="grey400", size=11))

    container = ft.Container(
        content=ft.Column(controls, spacing=8),
        bgcolor="surface",
        padding=15,
        border_radius=10,
        margin=ft.margin.only(bottom=5, left=20),
    )

    self.chat_list.controls.append(container)
    self.chat_list.update()
    self.page.update()

    # Return the index of the last UI control in chat_list
    return len(self.chat_list.controls) - 1

    def _update_message(self, index: int, new_content: str) -> None:
        """Update a previously added message by replacing its container."""
        if 0 <= index < len(self.chat_list.controls):
            # Create new container for assistant message
            agent_icon = "🤖"
            new_container = ft.Container(
                content=ft.Column([
                    ft.Text(f"{agent_icon} Assistant",
                           color="cyan", size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        new_content[:5000] if len(new_content) > 5000 else new_content,
                        selectable=True,
                        size=14,
                    ),
                ]),
                bgcolor="surface",
                padding=10,
                border_radius=10,
                margin=ft.margin.only(bottom=5, left=20),
            )
            # Replace the old container
            self.chat_list.controls[index] = new_container
            self.chat_list.update()
            self.page.update()

    async def _process_input_async(self, text: str) -> None:
        """Process input asynchronously with progress indication."""
        processing_msg_index = None

        try:
            if text.startswith("/"):
                # Check if this is a long-running command
                if self._is_long_running_command(text):
                    processing_msg_index = self._add_processing_message(text)

                result = await self.command_registry.execute(text)

                if result:
                    if result == "[CLEAR]":
                        self._clear_chat()
                        self._show_welcome()
                    else:
                        if processing_msg_index is not None:
                            # Replace the processing message with the actual result
                            self._update_message(processing_msg_index, result)
                        else:
                            self._add_assistant_message(result)
                elif processing_msg_index is not None:
                    # Command returned nothing, remove processing message
                    if processing_msg_index < len(self.chat_list.controls):
                        self.chat_list.controls.pop(processing_msg_index)
                        self.chat_list.update()
                        self.page.update()

                # Update status bar after command (especially for project switch)
                self._update_status_bar()
            else:
                # Natural language - let LLM detect intent and extract parameters
                response = await self._process_with_llm(text)
                self._add_assistant_message(response)
        except Exception as e:
            error_msg = f"❌ 错误: {e}"
            if processing_msg_index is not None:
                # Replace processing message with error
                self._update_message(processing_msg_index, error_msg)
            else:
                self._add_system_message(error_msg)

    async def _process_with_llm(self, text: str) -> str:
        """Process natural language input with LLM."""
        agent = self.agent_manager.current
        current = self.state.get_current_project()

        # Build context
        context_parts = []
        if current:
            context_parts.append(f"当前项目: {current.title}")
            context_parts.append(f"类型: {current.genre}")
            context_parts.append(f"进度: {current.completed_chapters}/{current.target_chapters}章")
        else:
            context_parts.append("⚠️ 当前没有项目，请先创建项目")

        context = "\n".join(context_parts)

        # Build system prompt with function calling capability
        system_prompt = f"""你是 {agent.name}，一个专业的AI写作助手。

角色描述: {agent.description}

当前上下文:
{context}

## 可用工具

你可以通过输出特殊格式的命令来执行操作。支持多个命令按顺序执行：

### 创建项目（完整参数）
```
[CMD]/project create --title "书名" --genre 类型 --chapters 章节数 --premise "故事核心设定" --themes "主题1,主题2" --tone 基调 --audience 目标读者 --rating 内容评级[/CMD]
```

**参数说明：**
- `--title`: 书名（必填）
- `--genre`: 类型（romance, dark romance, fantasy, scifi, thriller, history, military）
- `--chapters`: 目标章数
- `--premise`: 故事核心设定/前提（重要！影响大纲生成）
- `--themes`: 故事主题，用逗号分隔
- `--tone`: 基调（light/balanced/dark）
- `--audience`: 目标读者（young_adult/new_adult/adult）
- `--rating`: 内容评级（teen/mature/explicit）

**示例：**
```
[CMD]/project create --title "The Gilded Cage" --genre "dark romance" --chapters 350 --premise "一个女孩从天真无邪的中学恋情，逐渐发现并进入精英社会的黑暗腹地" --themes "纯真,诱惑,发现,救赎" --tone dark --audience young_adult --rating mature[/CMD]
```

### 创建角色
```
[CMD]/character create "完整角色名" --role 角色类型[/CMD]
```
可用的 role 类型：protagonist (主角), antagonist (反派), love_interest (恋爱对象), supporting (配角), mentor (导师)

**重要**：使用用户提供的完整角色名，不要简化！

**示例：**
```
[CMD]/character create "Clara Whitmore" --role protagonist[/CMD]
[CMD]/character create "Julian Ashford" --role love_interest[/CMD]
[CMD]/character create "Helena Van Der Berg" --role antagonist[/CMD]
```

### 生成故事大纲
```
[CMD]/outline create[/CMD]
```

### 开始写作
```
[CMD]/write chapter 章节号[/CMD]
```

### 其他命令
- 查看项目：`[CMD]/project list[/CMD]`
- 切换项目：`[CMD]/project switch 序号[/CMD]`
- 删除项目：`[CMD]/project delete 序号[/CMD]` (需确认)
- 帮助：`[CMD]/help[/CMD]`

### 修改设置（新功能）
```
[CMD]/set quality fast[/CMD]      # 快速模式（测试用）
[CMD]/set quality balanced[/CMD]  # 平衡模式
[CMD]/set quality high[/CMD]      # 高质量模式
[CMD]/set iterations 1[/CMD]      # 直接设置迭代次数
```

**设置命令说明：**
| 用户请求 | 转换为命令 |
|---------|-----------|
| "用最快模式" / "快速生成" | `[CMD]/set quality fast[/CMD]` |
| "质量优先" / "高质量模式" | `[CMD]/set quality high[/CMD]` |
| "把迭代次数调低一点" | `[CMD]/set iterations 2[/CMD]` |
| "只迭代1次" / "不要迭代" | `[CMD]/set iterations 1[/CMD]` |
| "关闭学习系统" | `[CMD]/set enable_learning false[/CMD]` |
| "恢复默认设置" | `[CMD]/set reset[/CMD]` |

**预设模式：**
- `fast` - 迭代1次，快速生成（测试/低质量）
- `balanced` - 迭代3次，平衡模式
- `high` - 迭代5次，高质量
- `ultra` - 迭代10次，极致质量

## 🎯 一键初始化项目

当用户提供详细的项目设定时，**必须按顺序执行以下所有命令**：

```
[CMD]/project create --title "书名" --genre 类型 --chapters 章节数 --premise "故事核心设定" --themes "主题1,主题2" --tone 基调 --audience 目标读者 --rating 内容评级[/CMD]
[CMD]/character create "完整角色名1" --role protagonist[/CMD]
[CMD]/character create "完整角色名2" --role love_interest[/CMD]
[CMD]/character create "完整角色名3" --role antagonist[/CMD]
[CMD]/outline create[/CMD]
```

### 提取规则（严格遵守）：

**项目信息提取：**
| 字段 | 提取规则 |
|------|----------|
| 书名 | 从"书名"或英文标题行提取完整名称 |
| 类型 | romance/dark romance/fantasy/scifi/thriller 等 |
| 章节数 | 从"目标章数"或"章"相关行提取数字 |
| 核心设定 | 从"前提"、"故事核心"或类似描述中提取完整内容 |
| 主题 | 从"主题"行或相关描述提取，用逗号分隔 |
| 基调 | light/balanced/dark（根据故事风格判断） |
| 目标读者 | young_adult (13-18) / new_adult (18-25) / adult (18+) |
| 内容评级 | teen/mature/explicit |

**角色提取（使用完整名称！）：**
| 用户设定 | 命令格式 |
|----------|----------|
| 女主角 Clara Whitmore | `[CMD]/character create "Clara Whitmore" --role protagonist[/CMD]` |
| 男主角 Julian Ashford | `[CMD]/character create "Julian Ashford" --role love_interest[/CMD]` |
| 反派 Helena Van Der Berg | `[CMD]/character create "Helena Van Der Berg" --role antagonist[/CMD]` |

## 重要规则

1. **必须提取完整设定**：不要简化用户的设定，特别是 premise 和 themes
2. **使用完整角色名**：不要把 "Clara Whitmore" 简化为 "Clara"
3. **命令顺序**：先创建项目（包含所有参数），再创建角色，最后生成大纲
4. **准确提取**：从表格、列表、描述中准确提取所有信息
5. **用中文回复**：保持专业但友好的语气

请用中文回复。"""

        # Build user prompt with history context
        history_context = self.history.to_context(max_tokens=2000)
        user_prompt = f"[历史对话]\n{history_context}\n\n[当前问题]\n{text}" if history_context else text

        if self.llm:
            try:
                # Show thinking indicator
                self._add_system_message("⏳ 思考中...")

                # Handle different LLM types
                if hasattr(self, '_model_config') and self._model_config.provider == "infini":
                    # Infini AI uses OpenAI-compatible API
                    response = await self.llm.chat.completions.create(
                        model=getattr(self, '_infini_model', 'kimi-k2.5'),
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.7,
                        max_tokens=2000,
                    )
                    content = response.choices[0].message.content
                else:
                    # Standard BaseLLM interface (GLM-5, etc.)
                    response = await self.llm.generate_with_system(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=0.7,
                        max_tokens=2000,
                    )
                    content = response.content

                # Remove thinking indicator (last message)
                if self.chat_list.controls:
                    self.chat_list.controls.pop()
                    self.chat_list.update()

                # Check for [CMD]...[/CMD] pattern and execute ALL commands
                import re
                cmd_pattern = r'\[CMD\](.+?)\[/CMD\]'
                cmd_matches = re.findall(cmd_pattern, content)

                if cmd_matches:
                    # Execute all commands in sequence with animated progress
                    results = []
                    progress_container = None

                    for i, command in enumerate(cmd_matches):
                        command = command.strip()
                        if command:
                            # Show animated progress indicator
                            if len(cmd_matches) > 1:
                                # Remove previous progress message if exists
                                if progress_container:
                                    self._remove_progress_message(progress_container)

                                # Show new progress with animated spinner
                                progress_container = self._add_progress_message(
                                    command[:60], i + 1, len(cmd_matches)
                                )
                            else:
                                # Single command - show simple thinking indicator
                                self._add_system_message(f"⏳ 执行: {command[:50]}...")

                            cmd_result = await self.command_registry.execute(command)
                            if cmd_result and cmd_result != "[CLEAR]":
                                results.append(cmd_result)

                            # Update status bar after each command
                            self._update_status_bar()

                    # Remove final progress message
                    if progress_container:
                        self._remove_progress_message(progress_container)
                    elif len(cmd_matches) == 1 and self.chat_list.controls:
                        # Remove single command indicator
                        self.chat_list.controls.pop()
                        self.chat_list.update()

                    # Remove all [CMD]...[/CMD] from response
                    content = re.sub(cmd_pattern, '', content).strip()

                    # Combine results
                    if results:
                        combined_result = "\n\n---\n\n".join(results)
                        return f"{combined_result}\n\n---\n\n{content}" if content else combined_result
                    elif content:
                        return content
                    else:
                        return "✅ 操作完成"

                return content

            except Exception as e:
                # Remove thinking indicator
                if self.chat_list.controls:
                    self.chat_list.controls.pop()
                    self.chat_list.update()
                return f"❌ LLM 调用失败: {e}\n\n当前模型: {self.model_name}"
        else:
            return """⚠️ LLM 未配置

当前使用模型路由系统。请检查:
1. ZHIPU_API_KEY 是否设置 (GLM-5)
2. INFINI_API_KEY 是否设置 (Kimi)

或在 .env 文件中配置相关 API Key。"""

    # ========== ACTION HANDLERS ==========
    def _on_switch_agent(self, e: ft.ControlEvent) -> None:
        """Switch to next agent."""
        agent = self.agent_manager.next_agent()
        self._update_status_bar()
        self._add_system_message(f"切换到 {agent.icon} {agent.name}")

    def _on_clear_chat(self, e: ft.ControlEvent) -> None:
        """Clear chat history."""
        self._clear_chat()
        self._show_welcome()

    def _clear_chat(self) -> None:
        """Clear chat view."""
        self.chat_list.controls.clear()
        self.chat_list.update()
        self.history.clear()

    def _on_show_help(self, e: ft.ControlEvent) -> None:
        """Show help dialog."""
        help_text = f"""# ⌨️ 快捷键

| 按键 | 功能 |
|-----|------|
| Tab | 下一个 Agent |
| Shift+Tab | 上一个 Agent |
| Enter | 发送消息 |
| Escape | 取消 |

# 当前配置

- Agent: {self.agent_manager.current.icon} {self.agent_manager.current.name}
- Model: 🔮 {self.model_name}

输入 `/help` 查看所有可用命令。
"""
        self._add_assistant_message(help_text)

    # ========== KEYBOARD HANDLING ==========
    def _on_keyboard(self, e: ft.KeyboardEvent) -> None:
        """Handle keyboard events."""
        # Ctrl+Enter to send message
        if e.key == "Enter" and e.ctrl:
            self._process_input()
            return

        if e.key == "Tab":
            # Switch agent
            if e.shift:
                agent = self.agent_manager.prev_agent()
            else:
                agent = self.agent_manager.next_agent()
            self._update_status_bar()
            self._add_system_message(f"切换到 {agent.icon} {agent.name}")
            e.control.page.update()

        elif e.key == "Escape":
            # Clear input
            self.input_field.value = ""
            self.input_field.update()

        elif e.key == "Arrow Up":
            # Navigate input history
            if self._input_history and self._history_index > 0:
                self._history_index -= 1
                self.input_field.value = self._input_history[self._history_index]
                self.input_field.update()

        elif e.key == "Arrow Down":
            # Navigate input history
            if self._history_index < len(self._input_history) - 1:
                self._history_index += 1
                self.input_field.value = self._input_history[self._history_index]
                self.input_field.update()
            else:
                self._history_index = len(self._input_history)
                self.input_field.value = ""
                self.input_field.update()


def run_flet_chat_studio() -> None:
    """Run the Flet-based Writer Studio."""
    app = ChatFletApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    run_flet_chat_studio()
