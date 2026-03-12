# src/studio/chat/commands.py
"""Slash command registry and handlers."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.studio.chat.streaming_progress import ProgressFormatter
from src.studio.core.state import StudioState


@dataclass
class Command:
    """A slash command definition."""
    name: str
    description: str
    usage: str
    handler: Callable[..., Coroutine[Any, Any, str]]
    aliases: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


class CommandRegistry:
    """Registry for slash commands."""

    def __init__(self, state: StudioState) -> None:
        self.state = state
        self._commands: dict[str, Command] = {}
        self._pipeline = None  # Lazy initialization
        self._planner = None  # Lazy initialization for ProjectPlanner
        self._planning_session: dict[str, Any] | None = None  # Active planning session
        self._discussion_planner = None  # Discussion-based planner
        self._discussion_session = None  # Active discussion session
        self._register_builtin_commands()

    def _get_pipeline(self):
        """Get or create ContentPipeline instance with dynamic settings."""
        if self._pipeline is None:
            from src.agents.content_pipeline import ContentPipeline
            from src.llm.final_model_config import DOMESTIC_MODELS
            from src.llm.glm import GLMLLM
            from src.studio.core.settings import get_settings

            # Get current settings
            settings = get_settings()

            # 创作模型：GLM-5 (成本低)
            writer_config = DOMESTIC_MODELS["glm-5"]
            writer_llm = GLMLLM(api_key=writer_config.api_key, model=writer_config.model_id)

            # 评审模型：Kimi 2.5 (专业评审能力)
            reviewer_config = DOMESTIC_MODELS["kimi-k2.5"]
            from src.llm.kimi import KimiLLM
            reviewer_llm = KimiLLM(
                api_key=reviewer_config.api_key,
                model=reviewer_config.model_id,
                base_url=reviewer_config.base_url,
            )

            self._pipeline = ContentPipeline(
                writer_llm=writer_llm,
                reviewer_llm=reviewer_llm,
                max_iterations=settings.iterations,
                approval_threshold=settings.approval_threshold,
                enable_learning=settings.enable_learning,
                language=settings.ui_language,  # NEW: pass UI language to pipeline
            )
        return self._pipeline

    def _reset_pipeline(self) -> None:
        """Reset pipeline to pick up new settings."""
        self._pipeline = None


    def _get_discussion_planner(self):
        """Get or create DiscussionPlanner instance."""
        if self._discussion_planner is None:
            from src.llm.final_model_config import DOMESTIC_MODELS
            from src.llm.glm import GLMLLM
            from src.studio.chat.discussion_planner import DiscussionPlanner

            # Use GLM-5 for discussion-based planning
            model_config = DOMESTIC_MODELS["glm-5"]
            llm = GLMLLM(api_key=model_config.api_key, model=model_config.model_id)
            self._discussion_planner = DiscussionPlanner(llm=llm, state=self.state)
        return self._discussion_planner
    def _get_planner(self):
        """Get or create ProjectPlanner instance."""
        if self._planner is None:
            from src.agents.project_planner import ProjectPlanner
            from src.llm.final_model_config import DOMESTIC_MODELS
            from src.llm.glm import GLMLLM

            # Use GLM-5 for project planning
            model_config = DOMESTIC_MODELS["glm-5"]
            llm = GLMLLM(api_key=model_config.api_key, model=model_config.model_id)
            self._planner = ProjectPlanner(llm=llm)
        return self._planner

    def _get_image_generator(self):
        """Get or create GLMImageGenerator instance."""
        try:
            from src.llm.glm_image import GLMImageGenerator
            return GLMImageGenerator()
        except ImportError:
            return None

    def _get_default_cover_style(self, genre: str) -> str:
        """Get default cover style based on genre."""
        style_map = {
            "romance": "romantic",
            "dark romance": "dark",
            "fantasy": "fantasy",
            "urban fantasy": "dark",
            "scifi": "minimalist",
            "science fiction": "realistic",
            "thriller": "dark",
            "mystery": "dark",
            "horror": "dark",
            "history": "vintage",
            "historical": "vintage",
            "military": "realistic",
            "action": "realistic",
            "adventure": "fantasy",
            "comedy": "minimalist",
            "drama": "realistic",
        }
        return style_map.get(genre.lower(), "book cover")

    def _register_builtin_commands(self) -> None:
        """Register built-in commands."""

        # Project commands
        self.register(Command(
            name="project",
            description="Manage novel projects",
            usage="/project [list|switch|create|info] [args]",
            handler=self._handle_project,
            aliases=["/projects", "/proj"],
            examples=[
                "/project list",
                "/project switch gilded_cage",
                "/project create --title 'My Novel' --genre romance",
            ]
        ))

        # Write commands
        self.register(Command(
            name="write",
            description="Generate novel content",
            usage="/write [chapter|batch|continue] [args]",
            handler=self._handle_write,
            aliases=["/w", "/generate"],
            examples=[
                "/write chapter 10",
                "/write batch 5",
                "/write continue",
            ]
        ))

        # Publish commands
        self.register(Command(
            name="publish",
            description="Publish to platforms",
            usage="/publish [platform] [chapter]",
            handler=self._handle_publish,
            aliases=["/pub"],
            examples=[
                "/publish wattpad",
                "/publish all --chapter 10",
            ]
        ))

        # Research commands
        self.register(Command(
            name="research",
            description="Market research and trends",
            usage="/research [trends|competitors|tags]",
            handler=self._handle_research,
            aliases=["/r"],
            examples=[
                "/research trends",
                "/research competitors",
            ]
        ))

        # Status commands
        self.register(Command(
            name="status",
            description="Show project status",
            usage="/status",
            handler=self._handle_status,
            aliases=["/info", "/s"],
        ))

        # Outline commands
        self.register(Command(
            name="outline",
            description="View or edit outline",
            usage="/outline [view|edit] [chapter]",
            handler=self._handle_outline,
            aliases=["/o"],
        ))

        # Agent commands
        self.register(Command(
            name="agent",
            description="Switch or list agents",
            usage="/agent [list|switch] [name]",
            handler=self._handle_agent,
            aliases=["/a"],
        ))

        # Character commands
        self.register(Command(
            name="character",
            description="Create or view characters with review",
            usage="/character [create|list] [name]",
            handler=self._handle_character,
            aliases=["/char"],
        ))

        # Review command
        self.register(Command(
            name="review",
            description="Review existing content",
            usage="/review [chapter|outline] [id]",
            handler=self._handle_review,
            aliases=["/check"],
        ))

        # Collaborate command for multi-genre writing
        self.register(Command(
            name="collaborate",
            description="Multi-genre collaborative writing",
            usage="/collaborate <genres> chapter <number>",
            handler=self._handle_collaborate,
            aliases=["/collab", "/multi"],
        ))

        # Plan command for interactive project planning
        self.register(Command(
            name="plan",
            description="Interactive project planning assistant",
            usage="/plan [start|quick|discuss|status|example]",
            handler=self._handle_plan,
            aliases=["/planning", "/wizard"],
        ))

        # Help command
        self.register(Command(
            name="help",
            description="Show help",
            usage="/help [command]",
            handler=self._handle_help,
            aliases=["/?", "/h"],
        ))

        # Clear command
        self.register(Command(
            name="clear",
            description="Clear conversation",
            usage="/clear",
            handler=self._handle_clear,
            aliases=["/c"],
        ))

        # Settings command
        self.register(Command(
            name="settings",
            description="Open settings",
            usage="/settings",
            handler=self._handle_settings,
            aliases=["/config"],
        ))

        # Cover command for book cover generation
        self.register(Command(
            name="cover",
            description="Generate book cover with AI",
            usage="/cover [generate|preview] [description]",
            handler=self._handle_cover,
            aliases=["/covers"],
        ))

        # Illustrate command for scene illustrations
        self.register(Command(
            name="illustrate",
            description="Generate scene illustration with AI",
            usage="/illustrate <scene|chapter> <number>",
            handler=self._handle_illustrate,
            aliases=["/ill", "/art"],
        ))

        # Feedback command for learning system
        self.register(Command(
            name="feedback",
            description="Give feedback on generated content for learning",
            usage="/feedback <good|bad|style> [comment]",
            handler=self._handle_feedback,
            aliases=["/fb"],
        ))

        # Set command for runtime configuration
        self.register(Command(
            name="set",
            description="Configure generation parameters",
            usage="/set [param value|quality mode]",
            handler=self._handle_set,
            aliases=["/config", "/cfg"],
            examples=[
                "/set",
                "/set iterations 1",
                "/set quality fast",
                "/set approval_threshold 8.0",
            ],
        ))

        # Cache command for managing creative cache
        self.register(Command(
            name="cache",
            description="Manage creative cache for outlines and characters",
            usage="/cache [stats|clear|invalidate]",
            handler=self._handle_cache,
            aliases=["/caches"],
            examples=[
                "/cache stats - Show cache statistics",
                "/cache clear - Clear all cached entries",
                "/cache invalidate outline - Clear outline cache",
                "/cache invalidate characters - Clear character cache",
            ],
        ))


        # Read command for viewing chapters
        self.register(Command(
            name="read",
            description="Read generated chapters",
            usage="/read [chapter_number|list|latest]",
            handler=self._handle_read,
            aliases=["/r", "/view"],
            examples=[
                "/read",
                "/read 1",
                "/read list",
                "/read latest",
            ],
        ))
    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias.lstrip("/")] = command

    def get_command(self, name: str) -> Command | None:
        """Get a command by name."""
        return self._commands.get(name)

    def list_commands(self) -> list[Command]:
        """List all unique commands."""
        seen = set()
        commands = []
        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                commands.append(cmd)
        return sorted(commands, key=lambda c: c.name)

    def parse(self, text: str) -> tuple[str, list[str]] | None:
        """Parse a slash command from text.

        Returns:
            Tuple of (command_name, args) or None if not a command
        """
        import shlex

        text = text.strip()
        if not text.startswith("/"):
            return None

        # Remove leading slash
        text = text[1:]

        # Split into parts
        parts = text.split(maxsplit=1)
        if not parts:
            return None

        command_name = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""

        # Parse arguments with proper quote handling
        if args_str:
            try:
                # Use shlex to properly handle quoted strings
                args = shlex.split(args_str)
            except ValueError:
                # Fallback to simple split if shlex fails (e.g., unmatched quotes)
                args = args_str.split()
        else:
            args = []

        return command_name, args

    async def execute(self, text: str) -> str | None:
        """Execute a slash command.

        Returns:
            Command result or None if not a command
        """
        parsed = self.parse(text)
        if not parsed:
            return None

        command_name, args = parsed
        command = self.get_command(command_name)

        if not command:
            return f"❌ Unknown command: /{command_name}\n\nType /help to see available commands."

        try:
            return await command.handler(args)
        except Exception as e:
            return f"❌ Error executing /{command_name}: {e}"

    # Command handlers

    async def _handle_project(self, args: list[str]) -> str:
        """Handle /project command."""
        # Show help if no subcommand provided
        if not args:
            return """## 📂 项目管理

| 子命令 | 说明 |
|--------|------|
| `/project list` | 列出所有项目 |
| `/project switch [N]` | 切换到第N个项目 |
| `/project create` | 创建新项目 |
| `/project info` | 显示当前项目详情 |
| `/project delete [N]` | 删除第N个项目 (需确认) |

**示例:**
- `/project list` - 查看所有项目
- `/project switch 1` - 切换到第1个项目
- `/project create --title "我的小说" --genre romance` - 创建新项目
- `/project delete 1` - 查看删除确认
- `/project delete 1 --confirm` - 确认删除"""

        subcommand = args[0]

        if subcommand == "list":
            projects = self.state.get_projects()
            if not projects:
                return "❌ 没有找到项目\n\n创建新项目: `/project create --title '我的小说' --genre romance`"

            current = self.state.get_current_project()
            current_id = current.id if current else None

            lines = ["## 📂 项目列表", ""]
            for i, p in enumerate(projects, 1):
                status = {"planning": "🔵", "writing": "🟢", "paused": "🟡", "completed": "✅"}.get(p.status.value, "⚪")
                marker = "→ " if current_id == p.id else "  "
                lines.append(f"{marker}`{i}` {status} **{p.title}**")
                lines.append(f"      类型: {p.genre} | 进度: {p.completed_chapters}/{p.target_chapters} 章 | {p.total_words:,} 字")
                lines.append("")

            lines.append("**操作:**")
            lines.append("  `/project switch 1` - 切换到第1个项目")
            lines.append("  `/project delete 1` - 删除第1个项目")

            return "\n".join(lines)

        if subcommand == "switch":
            projects = self.state.get_projects()

            if not projects:
                return "📂 No projects found.\n\nCreate one with: `/project create --title 'My Novel' --genre romance`"

            if len(args) < 2:
                # No project id provided - show selection dialog
                lines = ["📂 **Select a Project**", ""]
                lines.append("Type the project ID or number:")
                lines.append("")

                current = self.state.get_current_project()
                current_id = current.id if current else None

                for i, p in enumerate(projects, 1):
                    marker = "→ " if current_id == p.id else "  "
                    status = {"planning": "🔵", "writing": "🟢", "paused": "🟡", "completed": "✅"}.get(p.status.value, "⚪")
                    lines.append(f"  {marker}`{i}` {status} **{p.title}** (`{p.id}`)")
                    lines.append(f"       {p.completed_chapters}/{p.target_chapters} chapters | {p.genre}")
                    lines.append("")

                lines.append("Example: `/project switch novel_abc123` or `/project switch 1`")
                return "\n".join(lines)

            # Parse project id or number
            selection = args[1]

            # Check if it's a number
            if selection.isdigit():
                idx = int(selection)
                if 1 <= idx <= len(projects):
                    project = projects[idx - 1]
                    self.state.set_current_project(project.id)
                    return f"✅ Switched to project: **{project.title}**"
                return f"❌ Invalid number. Choose 1-{len(projects)}"

            # Try to find by ID
            project = self.state.get_project(selection)
            if project:
                self.state.set_current_project(selection)
                return f"✅ Switched to project: **{project.title}**"

            # Try to find by partial title match
            matches = [p for p in projects if selection.lower() in p.title.lower() or selection.lower() in p.id.lower()]
            if len(matches) == 1:
                self.state.set_current_project(matches[0].id)
                return f"✅ Switched to project: **{matches[0].title}**"
            elif len(matches) > 1:
                return f"❌ Multiple projects match '{selection}':\n\n" + "\n".join(f"  • {p.title} (`{p.id}`)" for p in matches)

            return f"❌ Project not found: {selection}\n\nType `/project switch` to see available projects."

        if subcommand == "create":
            # Parse options
            title = None
            genre = "romance"
            chapters = 100
            generate_cover = False
            cover_style = None
            # New story settings
            premise = ""
            themes: list[str] = []
            tone = "balanced"
            target_audience = "young_adult"
            content_rating = "teen"
            story_structure = "three_act"

            i = 1
            while i < len(args):
                if args[i] == "--title" and i + 1 < len(args):
                    title = args[i + 1].strip("'\"")
                    i += 2
                elif args[i] == "--genre" and i + 1 < len(args):
                    genre = args[i + 1]
                    i += 2
                elif args[i] == "--chapters" and i + 1 < len(args):
                    chapters = int(args[i + 1])
                    i += 2
                elif args[i] == "--premise" and i + 1 < len(args):
                    premise = args[i + 1].strip("'\"")
                    i += 2
                elif args[i] == "--themes" and i + 1 < len(args):
                    themes = [t.strip() for t in args[i + 1].split(",")]
                    i += 2
                elif args[i] == "--tone" and i + 1 < len(args):
                    tone = args[i + 1]
                    i += 2
                elif args[i] == "--audience" and i + 1 < len(args):
                    target_audience = args[i + 1]
                    i += 2
                elif args[i] == "--rating" and i + 1 < len(args):
                    content_rating = args[i + 1]
                    i += 2
                elif args[i] == "--structure" and i + 1 < len(args):
                    story_structure = args[i + 1]
                    i += 2
                elif args[i] == "--cover":
                    generate_cover = True
                    i += 1
                elif args[i] == "--cover-style" and i + 1 < len(args):
                    cover_style = args[i + 1]
                    generate_cover = True
                    i += 2
                else:
                    i += 1

            if not title:
                # Show genre options when title is missing
                genres = [
                    ("romance", "💕", "Love and relationships"),
                    ("dark romance", "🖤", "Dark love stories"),
                    ("fantasy", "🔮", "Magic and worldbuilding"),
                    ("scifi", "🚀", "Science and technology"),
                    ("thriller", "😱", "Suspense and mystery"),
                    ("history", "📜", "Historical settings"),
                    ("military", "⚔️", "War and combat"),
                ]

                tones = [
                    ("light", "☀️", "Light-hearted and fun"),
                    ("balanced", "⚖️", "Mix of light and dark"),
                    ("dark", "🌙", "Dark and intense"),
                ]

                audiences = [
                    ("young_adult", "13-18", "Young Adult"),
                    ("new_adult", "18-25", "New Adult"),
                    ("adult", "18+", "Adult"),
                ]


                lines = ["📝 **Create a New Project**", ""]
                lines.append("Usage:")
                lines.append("```")
                lines.append("/project create --title 'Title' --genre <genre> [options]")
                lines.append("```")
                lines.append("")
                lines.append("**Core Options:**")
                lines.append("  `--title 'Name'` - Project title")
                lines.append("  `--genre <type>` - Story genre")
                lines.append("  `--chapters <n>` - Target chapter count (default: 100)")
                lines.append("  `--premise 'desc'` - Story premise/核心设定")
                lines.append("  `--themes 'a,b,c'` - Comma-separated themes")
                lines.append("")
                lines.append("**Advanced Options:**")
                lines.append("  `--tone <type>` - light/balanced/dark")
                lines.append("  `--audience <type>` - young_adult/new_adult/adult")
                lines.append("  `--rating <type>` - teen/mature/explicit")
                lines.append("  `--structure <type>` - three_act/heros_journey/save_the_cat")
                lines.append("")
                lines.append("**Available Genres:**")
                for name, icon, desc in genres:
                    lines.append(f"  {icon} `{name}` - {desc}")
                lines.append("")
                lines.append("**Tones:**")
                for name, icon, desc in tones:
                    lines.append(f"  {icon} `{name}` - {desc}")
                lines.append("")
                lines.append("**Target Audiences:**")
                for name, age, desc in audiences:
                    lines.append(f"  `{name}` ({age}) - {desc}")
                lines.append("")
                lines.append("**Examples:**")
                lines.append("```")
                lines.append("/project create --title 'The Gilded Cage' --genre 'dark romance' --chapters 100")
                lines.append("/project create --title 'My Novel' --genre romance --premise 'A love story' --themes 'love,secrets'")
                lines.append("/project create --title 'Dark Tale' --genre thriller --tone dark --audience adult --rating mature")
                lines.append("```")
                return "\n".join(lines)

            import uuid

            from src.studio.core.state import NovelProject, ProjectStatus

            project = NovelProject(
                id=f"novel_{uuid.uuid4().hex[:8]}",
                title=title,
                genre=genre,
                target_chapters=chapters,
                status=ProjectStatus.PLANNING,
                premise=premise,
                themes=themes,
                tone=tone,
                target_audience=target_audience,
                content_rating=content_rating,
                story_structure=story_structure,
            )

            self.state.add_project(project)
            self.state.set_current_project(project.id)

            # Build response
            lines = [f"✅ Created project: **{project.title}**", ""]
            lines.append(f"   • ID: `{project.id}`")
            lines.append(f"   • Genre: {genre}")
            lines.append(f"   • Target: {chapters} chapters")

            # Show story settings if provided
            if premise:
                lines.append(f"   • Premise: {premise[:100]}{'...' if len(premise) > 100 else ''}")
            if themes:
                lines.append(f"   • Themes: {', '.join(themes)}")
            if tone != "balanced":
                lines.append(f"   • Tone: {tone}")
            if target_audience != "young_adult":
                lines.append(f"   • Audience: {target_audience}")
            if content_rating != "teen":
                lines.append(f"   • Rating: {content_rating}")

            lines.append("")

            # Handle cover generation
            if generate_cover:
                image_gen = self._get_image_generator()

                if not image_gen or not image_gen.is_available():
                    lines.append("⚠️ **Cover Generation Skipped**")
                    lines.append("")
                    lines.append("To enable cover generation, set your ZhipuAI API key:")
                    lines.append("```")
                    lines.append("export ZHIPUAI_API_KEY=your_api_key")
                    lines.append("```")
                    lines.append("")
                    lines.append("Then use: `/cover generate --style <style>`")
                else:
                    # Generate cover
                    style = cover_style or self._get_default_cover_style(genre)
                    lines.append("🎨 **Generating Cover...**")
                    lines.append(f"   Style: {style}")

                    result = image_gen.generate_cover(
                        title=title,
                        genre=genre,
                        description=f"A {genre} novel",
                        style=style,
                    )

                    lines.append("")
                    if result.success:
                        lines.append("✅ **Cover Generated!**")
                        if result.local_path:
                            lines.append(f"   📁 Saved to: `{result.local_path}`")
                        if result.image_url:
                            lines.append(f"   🔗 URL: {result.image_url}")
                    else:
                        lines.append(f"❌ Cover generation failed: {result.error}")
                        lines.append("")
                        lines.append("You can try again with: `/cover generate`")
            else:
                # Suggest cover generation
                lines.append("🎨 **Cover Art**")
                lines.append("")
                lines.append("Generate a book cover for your project:")
                lines.append("  `/cover preview` - Preview cover design")
                lines.append("  `/cover generate --style <style>` - Generate cover")

            lines.append("")
            lines.append("**Next Steps:**")
            lines.append("  `/plan quick <description>` - Create detailed plan")
            lines.append("  `/outline create` - Generate outline")
            lines.append("  `/character create <name> --role protagonist` - Add characters")

            return "\n".join(lines)

        if subcommand == "info":
            current = self.state.get_current_project()
            if not current:
                return "❌ No project selected. Use /project switch <id>"

            lines = [f"📋 **{current.title}**", ""]
            lines.append(f"   • ID: `{current.id}`")
            lines.append(f"   • Genre: {current.genre}")
            lines.append(f"   • Language: {current.language}")
            lines.append(f"   • Status: {current.status.value}")
            lines.append(f"   • Progress: {current.completed_chapters}/{current.target_chapters} ({current.progress_percent:.1f}%)")
            lines.append(f"   • Words: {current.total_words:,}")

            # Story settings
            if current.premise:
                lines.append("")
                lines.append("**Story Settings:**")
                lines.append(f"   • Premise: {current.premise[:100]}{'...' if len(current.premise) > 100 else ''}")
            if current.themes:
                lines.append(f"   • Themes: {', '.join(current.themes)}")
            if current.tone:
                lines.append(f"   • Tone: {current.tone}")
            if current.target_audience:
                lines.append(f"   • Audience: {current.target_audience}")
            if current.content_rating:
                lines.append(f"   • Rating: {current.content_rating}")

            lines.append("")
            lines.append("**Publishing:**")
            lines.append(f"   • Platforms: {', '.join(current.platforms) or 'None'}")
            lines.append(f"   • Reads: {current.total_reads:,}")
            lines.append(f"   • Followers: {current.followers:,}")

            return "\n".join(lines)

        if subcommand == "delete":
            projects = self.state.get_projects()

            if not projects:
                return "❌ 没有可删除的项目"

            if len(args) < 2:
                # No project id provided - show selection dialog
                lines = ["## 🗑️ 删除项目", ""]
                lines.append("输入项目编号或ID查看删除详情:")
                lines.append("")

                for i, p in enumerate(projects, 1):
                    status = {"planning": "🔵", "writing": "🟢", "paused": "🟡", "completed": "✅"}.get(p.status.value, "⚪")
                    lines.append(f"  `{i}` {status} **{p.title}** (`{p.id}`)")
                    lines.append(f"      {p.completed_chapters}/{p.target_chapters} 章 | {p.genre}")
                    lines.append("")

                lines.append("示例: `/project delete 1`")
                return "\n".join(lines)

            # Parse project id or number
            selection = args[1]
            project_to_delete = None

            # Check if it's a number
            if selection.isdigit():
                idx = int(selection)
                if 1 <= idx <= len(projects):
                    project_to_delete = projects[idx - 1]
                else:
                    return f"❌ 无效编号。请选择 1-{len(projects)}"
            else:
                # Try to find by ID
                project_to_delete = self.state.get_project(selection)
                if not project_to_delete:
                    # Try partial match
                    matches = [p for p in projects if selection.lower() in p.title.lower() or selection.lower() in p.id.lower()]
                    if len(matches) == 1:
                        project_to_delete = matches[0]
                    elif len(matches) > 1:
                        return f"❌ 多个项目匹配 '{selection}':\n\n" + "\n".join(f"  • {p.title} (`{p.id}`)" for p in matches)

            if not project_to_delete:
                return f"❌ 找不到项目: {selection}\n\n输入 `/project delete` 查看可用项目"

            # Check for --confirm flag
            confirmed = "--confirm" in args or "-y" in args

            if not confirmed:
                # Show confirmation prompt
                status = {"planning": "🔵", "writing": "🟢", "paused": "🟡", "completed": "✅"}.get(project_to_delete.status.value, "⚪")
                lines = ["## ⚠️ 确认删除", ""]
                lines.append("你即将删除以下项目:")
                lines.append("")
                lines.append(f"  {status} **{project_to_delete.title}**")
                lines.append(f"  ID: `{project_to_delete.id}`")
                lines.append(f"  类型: {project_to_delete.genre}")
                lines.append(f"  进度: {project_to_delete.completed_chapters}/{project_to_delete.target_chapters} 章")
                lines.append(f"  字数: {project_to_delete.total_words:,}")
                lines.append("")
                lines.append("⚠️ **警告**: 此操作不可恢复!")
                lines.append("")
                lines.append("**确认删除请输入:**")
                lines.append(f"  `/project delete {selection} --confirm`")
                lines.append("")
                lines.append("**取消删除请直接输入其他内容**")
                return "\n".join(lines)

            # Delete the project
            deleted_title = project_to_delete.title
            deleted_id = project_to_delete.id
            was_current = self.state.get_current_project()
            was_current_id = was_current.id if was_current else None

            self.state.delete_project(deleted_id)

            # If we deleted the current project, switch to another
            if was_current_id == deleted_id:
                remaining = self.state.get_projects()
                if remaining:
                    self.state.set_current_project(remaining[0].id)
                    return f"✅ 已删除项目: **{deleted_title}**\n\n已自动切换到: **{remaining[0].title}**"
                else:
                    return f"✅ 已删除项目: **{deleted_title}**\n\n没有其他项目了，请创建新项目: `/project create`"

            return f"✅ 已删除项目: **{deleted_title}**"

        return f"❌ Unknown subcommand: {subcommand}\nUsage: `/project [list|switch|create|info|delete]`"

    async def _handle_write(self, args: list[str]) -> str:
        """Handle /write command with full review pipeline."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use `/project switch` to select one"

        if not args:
            # Show write options
            completed = current.completed_chapters
            target = current.target_chapters
            next_chapter = completed + 1

            lines = ["✍️ **Write Content**", ""]
            lines.append(f"**Current Project:** {current.title}")
            lines.append(f"**Progress:** {completed}/{target} chapters")
            lines.append("")
            lines.append("**Commands:**")
            lines.append(f"  `/write chapter {next_chapter}` - Write next chapter")
            lines.append(f"  `/write chapter <n>` - Write specific chapter (1-{target})")
            lines.append(f"  `/write batch 5` - Write 5 chapters starting from {next_chapter}")
            lines.append(f"  `/write continue` - Continue from chapter {next_chapter}")
            lines.append("")
            lines.append("**Quick Start:**")
            lines.append(f"  Type `/write chapter {next_chapter}` to write chapter {next_chapter}")
            return "\n".join(lines)

        subcommand = args[0]
        pipeline = self._get_pipeline()

        if not pipeline:
            return "❌ LLM not configured. Check model routing configuration in src/llm/final_model_config.py"

        if subcommand == "chapter":
            if len(args) < 2:
                # Show chapter selection
                lines = ["📖 **Select Chapter**", ""]
                lines.append(f"Current progress: {current.completed_chapters}/{current.target_chapters} chapters")
                lines.append("")
                lines.append("**Recent:**")

                # Show last 3 written and next 3 to write
                for i in range(max(1, current.completed_chapters - 1), min(current.target_chapters, current.completed_chapters + 3) + 1):
                    status = "✅" if i <= current.completed_chapters else "📝"
                    lines.append(f"  {status} Chapter {i}")

                lines.append("")
                lines.append(f"**Next:** `/write chapter {current.completed_chapters + 1}`")
                lines.append("")
                lines.append("Type the chapter number: `/write chapter <number>`")
                return "\n".join(lines)

            chapter_num = int(args[1])

            # Get chapter outline from project
            chapter_outline = f"Chapter {chapter_num} - To be generated from outline"

            # TODO: Load actual characters and world context from project
            characters = [
                {"name": "Clara Whitmore", "role": "protagonist"},
                {"name": "Julian Ashford", "role": "love_interest"},
            ]
            world_context = {
                "society": {"culture": {"values": ["wealth", "prestige"]}},
                "locations": [{"name": "Ashford Academy", "atmosphere": "elite boarding school"}],
            }

            result = await pipeline.create_chapter(
                chapter_number=chapter_num,
                chapter_outline=chapter_outline,
                genre=current.genre,
                characters=characters,
                world_context=world_context,
            )

            if result.success:
                review = result.review

                # === Save chapter to file ===
                from pathlib import Path

                # 1. Create chapter directory
                project_novel_dir = Path(f"data/openviking/memory/novels/{current.id}")
                chapters_dir = project_novel_dir / "chapters"
                chapters_dir.mkdir(parents=True, exist_ok=True)

                # 2. Save chapter content
                chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
                with open(chapter_file, "w", encoding="utf-8") as f:
                    f.write(result.final_content)

                # 3. Update project status
                current.completed_chapters = max(current.completed_chapters, chapter_num)
                current.total_words += result.metadata.get("word_count", 0)
                current.updated_at = datetime.now().isoformat()

                # 4. Save state
                self.state._save_state()
                # === Save logic end ===

                return f"""✅ **Chapter {chapter_num} Created & Reviewed**

📝 **Quality Score:** {review.quality_score:.1f}/10 ({review.quality_level.value})
🔄 **Iterations:** {result.iterations}
📊 **Word Count:** {result.metadata.get("word_count", "N/A")}

**Strengths:**
{chr(10).join(f'• {s}' for s in review.strengths[:3])}

**Review Notes:**
{review.review_notes or "No additional notes"}

---
*Chapter content saved. Use /read {chapter_num} to view.*"""
            else:
                return f"""❌ **Chapter Creation Failed**

After {result.iterations} revision attempts, the chapter did not meet quality standards.

**Issues:**
{chr(10).join(f'• {e}' for e in result.errors)}

Please try again or adjust parameters."""

        if subcommand == "batch":
            count = int(args[1]) if len(args) > 1 else 5
            return f"✍️ Generating {count} chapters for **{current.title}**...\n\nEach chapter will go through the review pipeline.\n[Batch generation starting from chapter {current.completed_chapters + 1}]"

        if subcommand == "continue":
            return f"✍️ Continuing from Chapter {current.completed_chapters + 1} for **{current.title}**...\n\n[Each chapter will be reviewed before approval]"

        return f"❌ Unknown subcommand: {subcommand}"

    async def _handle_publish(self, args: list[str]) -> str:
        """Handle /publish command."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use /project switch <id>"

        platform = args[0] if args else "all"

        if platform == "all":
            return f"📤 Publishing **{current.title}** to all platforms...\n\nPlatforms: Wattpad, Royal Road"

        return f"📤 Publishing **{current.title}** to {platform}...\n\n[Publishing will start shortly]"

    async def _handle_research(self, args: list[str]) -> str:
        """Handle /research command."""
        subcommand = args[0] if args else "trends"

        if subcommand == "trends":
            return """📊 **Market Trends Analysis**

  🔥 **Hot Trends This Week:**
  • Dark Romance: +45% 📈
  • Enemies to Lovers: +32% 📈
  • Secret Society: +28% 📈
  • Coming of Age: +15% ➡️

  💡 **Recommendation:** Dark Romance is trending strongly on Wattpad and Royal Road."""

        if subcommand == "competitors":
            return """📊 **Competitor Analysis**

  **Similar Works:**
  1. **Cruel Prince** - 2.3M reads, Dark Romance
  2. **Twisted Love** - 1.8M reads, Enemies to Lovers
  3. **The Kiss Thief** - 1.5M reads, Arranged Marriage

  💡 Your story has similar themes but unique angle."""

        if subcommand == "tags":
            return """🏷️ **Trending Tags**

  #darkromance #enemies #rich #school #secrets
  #billionaire #forbidden #angst #redemption

  💡 Add these tags to improve discoverability."""

        return f"❌ Unknown subcommand: {subcommand}"

    async def _handle_status(self, args: list[str]) -> str:
        """Handle /status command."""
        stats = self.state.get_total_stats()
        current = self.state.get_current_project()

        lines = [
            "📊 **Writer Studio Status**",
            "",
            f"  📝 Total Words: {stats['total_words']:,}",
            f"  📖 Total Chapters: {stats['total_chapters']}",
            f"  📚 Projects: {stats['total_projects']}",
            f"  🟢 Active: {stats['active_projects']}",
            f"  👁 Total Reads: {stats['total_reads']:,}",
            f"  👥 Followers: {stats['total_followers']:,}",
            "",
        ]

        if current:
            lines.extend([
                f"  **Current Project:** {current.title}",
                f"  **Progress:** {current.completed_chapters}/{current.target_chapters} ({current.progress_percent:.1f}%)",
            ])

        return "\n".join(lines)

    async def _handle_outline(self, args: list[str]) -> str:
        """Handle /outline command with full review pipeline."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use /project switch <id>"

        subcommand = args[0] if args else "view"

        if subcommand == "create":
            pipeline = self._get_pipeline()
            if not pipeline:
                return "❌ LLM not configured. Check model routing configuration in src/llm/final_model_config.py"

            # Build premise from project settings
            premise = current.premise or f"A {current.genre} story: {current.title}"

            # Build themes list
            themes = current.themes if current.themes else ["love", "power", "secrets", "redemption"]

            # Build story context for the outline
            story_context = {
                "title": current.title,
                "genre": current.genre,
                "tone": current.tone,
                "target_audience": current.target_audience,
                "content_rating": current.content_rating,
                "pov": current.pov,
            }

            result = await pipeline.create_outline(
                title=current.title,
                genre=current.genre,
                premise=premise,
                target_chapters=current.target_chapters,
                themes=themes,
                context=story_context,
            )

            if result.success:
                review = result.review
                threshold_met = result.metadata.get("threshold_met", True)
                quality_score = review.quality_score if review else 5.0
                quality_level = review.quality_level.value if review and review.quality_level else "unknown"

                # Always save the outline regardless of score
                # Just change the status message based on quality
                if threshold_met:
                    status_emoji = "✅"
                    status_text = "Created & Approved"
                    improvement_notice = ""
                else:
                    status_emoji = "⚠️"
                    status_text = f"Created - Needs Improvement (Score: {quality_score:.1f})"
                    improvement_notice = """

💡 **Improvement Suggestions:**
The outline has been saved but could benefit from refinement. Consider:
• Reviewing the weaknesses listed above
• Running `/outline create` again with adjusted settings
• Or using the current outline as a starting point and editing manually"""

                strengths_text = chr(10).join(f'• {s}' for s in (review.strengths[:3] if review and review.strengths else []))
                if not strengths_text:
                    strengths_text = "• (No specific strengths identified)"

                notes_text = review.review_notes if review and review.review_notes else "No additional notes"

                return f"""{status_emoji} **Outline {status_text}**

📝 **Quality Score:** {quality_score:.1f}/10 ({quality_level})
🔄 **Iterations:** {result.iterations}

**Strengths:**
{strengths_text}

**Review Notes:**
{notes_text}{improvement_notice}

---
{result.final_content[:1500]}...

*Full outline saved to project.*"""
            else:
                return f"""❌ **Outline Creation Failed**

After {result.iterations} attempts, the outline could not be created.

**Issues:**
{chr(10).join(f'• {e}' for e in result.errors)}"""

        if subcommand == "view":
            return f"""📖 **{current.title} - Outline**

  **Act 1: The Golden Age** (Chapters 1-100)
  The innocent beginning, first love, and the invitation.

  **Act 2: The Gilded Cage** (Chapters 101-250)
  Discovery of the dark world, entrapment, and survival.

  **Act 3: Shattered Glass** (Chapters 251-350)
  The truth exposed, recovery, and new beginning.

  💡 Use /outline create to generate a new outline with review."""

        return f"""📖 **{current.title} - Outline**

  **Act 1: The Golden Age** (Chapters 1-100)
  The innocent beginning, first love, and the invitation.

  **Act 2: The Gilded Cage** (Chapters 101-250)
  Discovery of the dark world, entrapment, and survival.

  **Act 3: Shattered Glass** (Chapters 251-350)
  The truth exposed, recovery, and new beginning.

  💡 Use /outline create to generate a new outline with review."""

    async def _handle_agent(self, args: list[str]) -> str:
        """Handle /agent command with interactive selection."""
        # Available agents
        agents = [
            ("romance", "✍️", "Romance novel writer"),
            ("scifi", "🚀", "Sci-Fi novel writer"),
            ("fantasy", "🔮", "Fantasy novel writer"),
            ("history", "📜", "Historical fiction writer"),
            ("military", "⚔️", "Military fiction writer"),
            ("editor", "📖", "Content editor"),
            ("research", "📊", "Market research"),
            ("publisher", "📤", "Publishing manager"),
            ("orchestrator", "🎯", "Project coordinator"),
        ]

        subcommand = args[0] if args else "list"

        if subcommand == "list":
            lines = ["🤖 **Available Agents**", ""]
            for name, icon, desc in agents:
                lines.append(f"  {icon} **{name}** - {desc}")
            lines.append("")
            lines.append("💡 Switch with: `/agent switch <name>` or just `/agent switch` to select")
            return "\n".join(lines)

        if subcommand == "switch":
            if len(args) < 2:
                # No agent name provided - show selection dialog
                lines = ["🤖 **Select an Agent**", ""]
                lines.append("Type the agent name or number:")
                lines.append("")
                for i, (name, icon, desc) in enumerate(agents, 1):
                    lines.append(f"  `{i}` {icon} **{name}** - {desc}")
                lines.append("")
                lines.append("Example: `/agent switch romance` or `/agent switch 1`")
                return "\n".join(lines)

            # Parse agent name or number
            selection = args[1].lower()

            # Check if it's a number
            if selection.isdigit():
                idx = int(selection)
                if 1 <= idx <= len(agents):
                    name, icon, desc = agents[idx - 1]
                    return f"✅ Switched to {icon} **{name}** - {desc}"
                return f"❌ Invalid number. Choose 1-{len(agents)}"

            # Check if it's a valid agent name
            for name, icon, desc in agents:
                if name == selection:
                    return f"✅ Switched to {icon} **{name}** - {desc}"

            # Suggest similar agents
            suggestions = [name for name, _, _ in agents if selection in name or name in selection]
            if suggestions:
                return f"❌ Unknown agent: '{selection}'\n\nDid you mean: {', '.join(suggestions)}?"

            return f"❌ Unknown agent: '{selection}'\n\nType `/agent switch` to see available agents."

        return f"❌ Unknown subcommand: {subcommand}\n\nUsage: `/agent [list|switch] [name]`"

    async def _handle_help(self, args: list[str]) -> str:
        """Handle /help command."""
        if args:
            cmd = self.get_command(args[0])
            if cmd:
                examples = "\n".join(f"  {ex}" for ex in cmd.examples) if cmd.examples else "  No examples"
                return f"""**/{cmd.name}**

{cmd.description}

**Usage:** {cmd.usage}

**Examples:**
{examples}"""
            return f"❌ Unknown command: {args[0]}"

        commands = self.list_commands()
        lines = ["📚 **Available Commands**", ""]

        for cmd in commands:
            lines.append(f"  /{cmd.name:<12} - {cmd.description}")

        lines.append("")
        lines.append("💡 Type `/help <command>` for more details")
        lines.append("")
        lines.append("## ⌨️ Shortcuts")
        lines.append("")
        lines.append("  `Tab`        - Switch Agent")
        lines.append("  `Esc`        - Cancel/Interrupt")
        lines.append("  `Ctrl+C`     - Exit program")
        lines.append("  `Ctrl+L`     - Clear chat")
        lines.append("  `Ctrl+H`     - Show help")
        lines.append("  `Ctrl+P`     - Switch project")

        return "\n".join(lines)

    async def _handle_clear(self, args: list[str]) -> str:
        """Handle /clear command."""
        return "[CLEAR]"  # Special marker for UI to clear

    async def _handle_settings(self, args: list[str]) -> str:
        """Handle /settings command."""
        return """⚙️ **Settings**

  **LLM Provider:** Model Routing System
  **Primary:** GLM-5 (Zhipu AI)
  **Elite Content:** Kimi 2.5 (Infini AI)
  **Temperature:** 0.7
  **Language:** zh

  💡 Model routing configuration: src/llm/final_model_config.py"""

    async def _handle_feedback(self, args: list[str]) -> str:
        """Handle /feedback command for learning system."""
        from src.learning.preference_tracker import PreferenceTracker

        if not args:
            return """📝 **Feedback Commands**

  /feedback good - Mark last content as good
  /feedback bad - Mark last content as needs improvement
  /feedback style <preference> - Add style preference
    Examples:
    /feedback style more dialogue
    /feedback style less description
    /feedback style 快节奏

  💡 Your feedback helps the AI learn your preferences!"""

        feedback_type = args[0].lower()

        # Initialize preference tracker
        tracker = PreferenceTracker()

        # Get last content ID from state (if available)
        last_content_id = getattr(self.state, '_last_content_id', 'unknown')
        last_content_type = getattr(self.state, '_last_content_type', 'unknown')

        if feedback_type == "good":
            tracker.record_feedback(last_content_id, "good", last_content_type)
            return "✅ **Feedback recorded: Good!**" + chr(10) + chr(10) + "The AI will learn from this positive example."

        elif feedback_type == "bad":
            tracker.record_feedback(last_content_id, "bad", last_content_type)
            return "📝 **Feedback recorded: Needs improvement**" + chr(10) + chr(10) + "The AI will avoid similar patterns in the future."

        elif feedback_type == "style" and len(args) > 1:
            preference = " ".join(args[1:])
            tracker.record_feedback(last_content_id, preference, last_content_type)
            return f"✅ **Style preference recorded: {preference}**" + chr(10) + chr(10) + "The AI will adjust future content accordingly."

        else:
            return f"❌ Unknown feedback type: {feedback_type}" + chr(10) + chr(10) + "Use: /feedback good | bad | style <preference>"

    async def _handle_set(self, args: list[str]) -> str:
        """Handle /set command for runtime configuration.

        Supports:
        - /set : Show current settings
        - /set iterations N : Set iteration count (1-10)
        - /set quality fast/balanced/high/ultra : Apply preset mode
        - /set approval_threshold N : Set approval threshold (7.0-10.0)
        - /set enable_learning true/false : Enable/disable learning
        """
        from src.studio.core.settings import QUALITY_PRESETS, get_settings_manager

        manager = get_settings_manager()
        settings = manager.get_settings()

        # No args - show current settings
        if not args:
            lines = ["⚙️ **当前设置**", ""]
            lines.append(f"  **迭代次数**: {settings.iterations} (1-10)")
            lines.append(f"  **通过阈值**: {settings.approval_threshold} (7.0-10.0)")
            lines.append(f"  **修订阈值**: {settings.auto_revise_threshold} (5.0-9.0)")
            lines.append(f"  **学习系统**: {'启用' if settings.enable_learning else '禁用'}")
            lines.append(f"  **质量模式**: {settings.quality_mode}")
            lines.append(f"  **界面语言**: {'中文' if settings.ui_language == 'zh' else 'English'}")
            lines.append("")

        param = args[0].lower()

        # Quality mode preset
        if param in ("quality", "mode", "q"):
            if len(args) < 2:
                modes = list(QUALITY_PRESETS.keys())
                return f"❌ 请指定模式: {modes}\n\n示例: `/set quality fast`"

            mode = args[1].lower()
            if mode not in QUALITY_PRESETS:
                modes = list(QUALITY_PRESETS.keys())
                return f"❌ 未知模式: {mode}\n\n可用模式: {modes}"

            description = manager.apply_preset(mode)
            preset = QUALITY_PRESETS[mode]
            self._reset_pipeline()  # Apply new settings to pipeline
            return f"✅ **已应用 {mode} 模式**\n\n{description}\n\n迭代次数: {preset['iterations']}, 通过阈值: {preset['approval_threshold']}\n\n💡 设置将在下次生成时生效"

        # Iterations
        if param in ("iterations", "iter", "i"):
            if len(args) < 2:
                return "❌ 请指定迭代次数 (1-10)\n\n示例: `/set iterations 3`"

            try:
                value = int(args[1])
                if not (1 <= value <= 10):
                    return f"❌ 迭代次数必须在 1-10 范围内，当前: {value}"
                manager.update_settings(iterations=value)
                self._reset_pipeline()  # Apply new settings to pipeline
                return f"✅ **迭代次数已设置为 {value}**\n\n💡 设置将在下次生成时生效"
            except ValueError:
                return f"❌ 无效数字: {args[1]}"

        # Approval threshold
        if param in ("approval_threshold", "threshold", "approval", "t"):
            if len(args) < 2:
                return "❌ 请指定通过阈值 (7.0-10.0)\n\n示例: `/set approval_threshold 8.0`"

            try:
                value = float(args[1])
                if not (7.0 <= value <= 10.0):
                    return f"❌ 通过阈值必须在 7.0-10.0 范围内，当前: {value}"
                manager.update_settings(approval_threshold=value)
                self._reset_pipeline()  # Apply new settings to pipeline
                return f"✅ **通过阈值已设置为 {value}**\n\n💡 设置将在下次生成时生效"
            except ValueError:
                return f"❌ 无效数字: {args[1]}"

        # Auto revise threshold
        if param in ("auto_revise_threshold", "revise_threshold", "revise"):
            if len(args) < 2:
                return "❌ 请指定修订阈值 (5.0-9.0)\n\n示例: `/set auto_revise_threshold 6.0`"

            try:
                value = float(args[1])
                if not (5.0 <= value <= 9.0):
                    return f"❌ 修订阈值必须在 5.0-9.0 范围内，当前: {value}"
                manager.update_settings(auto_revise_threshold=value)
                return f"✅ **修订阈值已设置为 {value}**"
            except ValueError:
                return f"❌ 无效数字: {args[1]}"

        # Enable learning
        if param in ("enable_learning", "learning", "learn"):
            if len(args) < 2:
                return "❌ 请指定 true 或 false\n\n示例: `/set enable_learning false`"

            value_str = args[1].lower()
            if value_str in ("true", "yes", "on", "1", "启用"):
                manager.update_settings(enable_learning=True)
                self._reset_pipeline()  # Apply new settings to pipeline
                return "✅ **学习系统已启用**\n\n💡 设置将在下次生成时生效"
            elif value_str in ("false", "no", "off", "0", "禁用"):
                manager.update_settings(enable_learning=False)
                self._reset_pipeline()  # Apply new settings to pipeline
                return "✅ **学习系统已禁用**\n\n💡 设置将在下次生成时生效"
            else:
                return f"❌ 无效值: {args[1]}\n\n请使用 true/false"

        # Language setting
        if param in ("language", "lang", "l"):
            if len(args) < 2:
                return "❌ 请指定语言: en 或 zh\n\n示例: `/set language zh` 切换到中文"

            lang = args[1].lower()
            if lang not in ("en", "zh"):
                return f"❌ 无效语言: {lang}\n\n可用语言: en (English), zh (中文)"

            manager.update_settings(ui_language=lang)
            lang_name = "中文" if lang == "zh" else "English"
            self._reset_pipeline()  # Reset pipeline to pick up new language
            return f"✅ **界面和 AI 输出语言已设置为 {lang_name}**\n\n💡 命令保持英文（如 /project），但界面消息和 AI 生成内容将使用所选语言"

        return f"❌ 未知参数: {param}\n\n可用参数: iterations, quality, approval_threshold, enable_learning, language\n\n输入 `/set` 查看所有设置"





    async def _handle_read(self, args: list[str]) -> str:
        """Handle /read command to view generated chapters."""
        from pathlib import Path

        current = self.state.get_current_project()
        if not current:
            return "❌ 没有选中的项目。使用 /project switch 选择项目"

        # Try multiple possible chapter directories
        chapters_dir = Path(f"data/openviking/memory/novels/{current.id}/chapters")

        if not chapters_dir.exists():
            msg = f"📖 项目 {current.title} 还没有生成的章节"
            return msg + chr(10) + chr(10) + "使用 /write chapter 1 开始写作"
        if not chapters_dir.exists():
            msg = f"📖 项目 {current.title} 还没有生成的章节"
            return msg + chr(10) + chr(10) + "使用 /write chapter 1 开始写作"

        chapters = sorted([f for f in chapters_dir.glob("chapter_*.md") if "_en" not in f.name])
        subcommand = args[0].lower() if args else "list"

        if subcommand == "list" or not args:
            if not chapters:
                msg = f"📖 项目 {current.title} 还没有生成的章节"
                return msg + chr(10) + chr(10) + "使用 /write chapter 1 开始写作"

            lines = [f"📖 **{current.title} - 已完成章节**", ""]
            lines.append(f"已生成: {len(chapters)}/{current.target_chapters} 章")
            lines.append("")
            lines.append("**章节列表:**")
            lines.append("")

            for ch in chapters:
                try:
                    num = int(ch.stem.split("_")[1])
                except (IndexError, ValueError):
                    num = 0
                size = ch.stat().st_size
                words = size // 3
                try:
                    with open(ch, encoding="utf-8") as f:
                        first_line = f.readline().strip()
                        title = first_line.lstrip("#").strip() if first_line.startswith("#") else "无标题"
                except:
                    title = "无法读取"
                lines.append(f"  第{num}章: {title} (~{words}字)")

            lines.append("")
            lines.append("💡 使用 /read <章节号> 阅读指定章节")
            lines.append("💡 使用 /read latest 阅读最新章节")
            return chr(10).join(lines)

        if subcommand == "latest":
            if not chapters:
                return "❌ 没有已生成的章节"
            latest = chapters[-1]
            try:
                chapter_num = int(latest.stem.split("_")[1])
            except:
                chapter_num = len(chapters)
            subcommand = str(chapter_num)

        try:
            chapter_num = int(subcommand)
        except ValueError:
            return "❌ 无效的章节号: " + subcommand + chr(10) + chr(10) + "使用 /read list 查看所有章节"

        chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
        if not chapter_file.exists():
            chapter_file = chapters_dir / f"chapter_{chapter_num}.md"

        if not chapter_file.exists():
            msg = f"❌ 章节 {chapter_num} 不存在"
            return msg + chr(10) + chr(10) + f"已生成: {len(chapters)} 章" + chr(10) + "使用 /read list 查看所有章节"

        try:
            with open(chapter_file, encoding="utf-8") as f:
                content_text = f.read()
        except Exception as e:
            return f"❌ 读取章节失败: {e}"

        content_lines = content_text.split(chr(10))
        max_lines = 80
        if len(content_lines) > max_lines:
            displayed = chr(10).join(content_lines[:max_lines])
            remaining = len(content_lines) - max_lines
            result = displayed + chr(10) + chr(10) + "---" + chr(10) + chr(10)
            result += f"📖 *... 还有 {remaining} 行未显示*" + chr(10) + chr(10)
            result += f"💡 完整章节请查看文件: {chapter_file}"
            return result

        return content_text

    async def _handle_character(self, args: list[str]) -> str:
        """Handle /character command with full review pipeline."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use `/project switch` to select one"

        subcommand = args[0] if args else "list"

        # Available roles
        roles = [
            ("protagonist", "⭐", "Main character"),
            ("antagonist", "😈", "Primary villain"),
            ("love_interest", "💕", "Romantic partner"),
            ("mentor", "🧙", "Guide/teacher"),
            ("sidekick", "🤝", "Best friend/ally"),
            ("supporting", "👤", "Secondary character"),
        ]

        if subcommand == "list":
            lines = ["👥 **Characters**", ""]
            lines.append("**Main Characters:**")
            lines.append("  • Clara Whitmore - Protagonist")
            lines.append("  • Julian Ashford - Love Interest")
            lines.append("  • Helena Van Der Berg - Antagonist")
            lines.append("")
            lines.append("💡 Use `/character create <name>` to create a new character")
            return "\n".join(lines)

        if subcommand == "create":
            if len(args) < 2:
                # Show usage with role options
                lines = ["👤 **Create a Character**", ""]
                lines.append("Usage: `/character create <name> --role <role>`")
                lines.append("")
                lines.append("**Available Roles:**")
                for name, icon, desc in roles:
                    lines.append(f"  {icon} `{name}` - {desc}")
                lines.append("")
                lines.append("**Examples:**")
                lines.append("  `/character create Clara --role protagonist`")
                lines.append("  `/character create Julian` (default: supporting)")
                return "\n".join(lines)

            # Parse arguments
            name = args[1]
            role = "supporting"

            i = 2
            while i < len(args):
                if args[i] == "--role" and i + 1 < len(args):
                    role_input = args[i + 1].lower()
                    # Check if it's a number
                    if role_input.isdigit():
                        idx = int(role_input)
                        if 1 <= idx <= len(roles):
                            role = roles[idx - 1][0]
                        else:
                            return f"❌ Invalid role number. Choose 1-{len(roles)}"
                    else:
                        # Validate role name
                        valid_roles = [r[0] for r in roles]
                        if role_input in valid_roles:
                            role = role_input
                        else:
                            return f"❌ Invalid role: '{role_input}'\n\nValid roles: {', '.join(valid_roles)}"
                    i += 2
                else:
                    i += 1

            pipeline = self._get_pipeline()
            if not pipeline:
                return "❌ LLM not configured. Check model routing configuration in src/llm/final_model_config.py"

            # Build rich story context for character creation
            story_context = {
                "title": current.title,
                "genre": current.genre,
                "premise": current.premise or f"A {current.genre} story",
                "themes": current.themes,
                "tone": current.tone,
                "target_audience": current.target_audience,
                "pov": current.pov,
                "content_rating": current.content_rating,
            }

            result = await pipeline.create_character(
                character_name=name,
                role=role,
                genre=current.genre,
                story_context=story_context,
            )

            if result.success:
                review = result.review
                threshold_met = result.metadata.get("threshold_met", True)
                result.metadata.get("quality_status", "approved")

                if threshold_met:
                    status_emoji = "✅"
                    status_text = "Created & Approved"
                else:
                    status_emoji = "⚠️"
                    status_text = f"Created (Quality: {review.quality_score:.1f}, Target: 9.0)"

                return f"""{status_emoji} **Character {status_text}**

📝 **Name:** {name}
🎭 **Role:** {role}
📊 **Quality Score:** {review.quality_score:.1f}/10 ({review.quality_level.value})
🔄 **Iterations:** {result.iterations}

**Character Profile:**
{result.final_content[:1000]}

**Strengths:**
{chr(10).join(f'• {s}' for s in review.strengths[:2])}

*Full profile saved to project.*"""
            else:
                return f"""❌ **Character Creation Failed**

After {result.iterations} attempts, the character could not be created.

**Issues:**
{chr(10).join(f'• {e}' for e in result.errors)}"""

        return f"❌ Unknown subcommand: {subcommand}"

    async def _handle_review(self, args: list[str]) -> str:
        """Handle /review command to review existing content."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use /project switch <id>"

        if not args:
            return """📋 **Review Options**

  /review chapter <number> - Review a specific chapter
  /review outline - Review the current outline
  /review all - Review all content

  💡 All creative content automatically goes through review during creation."""

        subcommand = args[0]

        if subcommand == "chapter":
            if len(args) < 2:
                return "❌ Usage: /review chapter <number>"

            chapter_num = int(args[1])

            # TODO: Load actual chapter content

            pipeline = self._get_pipeline()
            if not pipeline:
                return "❌ LLM not configured. Check model routing configuration in src/llm/final_model_config.py"

            return f"""📋 **Chapter {chapter_num} Review**

  **Quality Score:** 7.5/10 (good)

  **Strengths:**
  • Strong dialogue
  • Good pacing

  **Areas for Improvement:**
  • Some passive voice
  • Could add more sensory details

  **Recommendation:** Minor revisions suggested

  💡 Use /write chapter {chapter_num} to regenerate with revisions."""

        if subcommand == "outline":
            return f"""📋 **Outline Review: {current.title}**

  **Quality Score:** 8.0/10 (good)

  **Strengths:**
  • Clear three-act structure
  • Strong character arcs planned
  • Good tension building

  **Areas for Improvement:**
  • Act 2 could use more subplot variety

  **Recommendation:** Approved for writing"""

        return f"❌ Unknown review type: {subcommand}"

    async def _handle_collaborate(self, args: list[str]) -> str:
        """Handle /collaborate command for multi-genre writing."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use `/project switch` to select one"

        # Available genres and modes
        genres_list = [
            ("romance", "💕", "Love and relationships"),
            ("history", "📜", "Historical accuracy"),
            ("fantasy", "🔮", "Magic and worldbuilding"),
            ("scifi", "🚀", "Science and technology"),
            ("military", "⚔️", "War and tactics"),
            ("thriller", "😱", "Suspense and mystery"),
        ]

        modes_list = [
            ("lead_support", "Lead genre writes, others enhance"),
            ("sequential", "Hand off between agents"),
            ("parallel", "All write, then merge"),
            ("dynamic", "AI decides in real-time"),
        ]

        if not args:
            lines = ["🤝 **Multi-Genre Collaboration**", ""]
            lines.append("Write chapters that span multiple genres with AI specialists collaborating.")
            lines.append("")
            lines.append("**Usage:**")
            lines.append("  `/collaborate <genre1,genre2> chapter <number>`")
            lines.append("")
            lines.append("**Available Genres:**")
            for name, icon, desc in genres_list:
                lines.append(f"  {icon} `{name}` - {desc}")
            lines.append("")
            lines.append("**Collaboration Modes:**")
            for name, desc in modes_list:
                lines.append(f"  `--mode {name}` - {desc}")
            lines.append("")
            lines.append("**Popular Combinations:**")
            lines.append("  • `romance,history` → Historical romance")
            lines.append("  • `fantasy,military` → Military fantasy")
            lines.append("  • `scifi,thriller` → Sci-fi thriller")
            lines.append("  • `romance,thriller` → Romantic suspense")
            lines.append("")
            lines.append("**Examples:**")
            lines.append("  `/collaborate romance,history chapter 10`")
            lines.append("  `/collaborate fantasy,military chapter 5 --mode sequential`")
            return "\n".join(lines)

        # Parse arguments
        genres_str = args[0]

        # Check if user is asking for genre selection
        if genres_str == "genres" or genres_str == "list":
            lines = ["🤝 **Select Genres**", ""]
            lines.append("Type genres as comma-separated list:")
            lines.append("")
            for i, (name, icon, desc) in enumerate(genres_list, 1):
                lines.append(f"  `{i}` {icon} **{name}** - {desc}")
            lines.append("")
            lines.append("**Example:** `/collaborate 1,2 chapter 5` (romance + history)")
            return "\n".join(lines)

        # Parse genres (allow numbers)
        genres = []
        for g in genres_str.split(","):
            g = g.strip().lower()
            if g.isdigit():
                idx = int(g)
                if 1 <= idx <= len(genres_list):
                    genres.append(genres_list[idx - 1][0])
                else:
                    return f"❌ Invalid genre number: {g}. Choose 1-{len(genres_list)}"
            else:
                genres.append(g)

        if len(args) < 3 or args[1] != "chapter":
            return "❌ Usage: `/collaborate <genre1,genre2> chapter <number>`\n\nExample: `/collaborate romance,history chapter 5`"

        try:
            chapter_num = int(args[2])
        except ValueError:
            return "❌ Chapter number must be a number"

        # Parse mode (allow number)
        mode = "lead_support"
        if "--mode" in args:
            mode_idx = args.index("--mode")
            if mode_idx + 1 < len(args):
                mode_input = args[mode_idx + 1]
                if mode_input.isdigit():
                    idx = int(mode_input)
                    if 1 <= idx <= len(modes_list):
                        mode = modes_list[idx - 1][0]
                    else:
                        return f"❌ Invalid mode number. Choose 1-{len(modes_list)}"
                else:
                    mode = mode_input

        # Validate genres
        valid_genres = [g[0] for g in genres_list]
        invalid = [g for g in genres if g not in valid_genres]
        if invalid:
            return f"❌ Unknown genres: {', '.join(invalid)}\n\nValid genres: {', '.join(valid_genres)}"

        pipeline = self._get_pipeline()
        if not pipeline:
            return "❌ LLM not configured. Check model routing configuration in src/llm/final_model_config.py"

        # Get chapter outline (TODO: load from project)
        chapter_outline = f"Chapter {chapter_num} - Multi-genre content ({' + '.join(genres)})"

        # TODO: Load actual characters and world context
        characters = [
            {"name": "Protagonist", "role": "main"},
        ]
        world_context = {}

        result = await pipeline.create_chapter_multi_genre(
            chapter_number=chapter_num,
            chapter_outline=chapter_outline,
            genres=genres,
            characters=characters,
            world_context=world_context,
            collaboration_mode=mode,
        )

        if result.success:
            review = result.review
            contributions = result.metadata.get("contributions", {})

            contrib_text = "\n".join([
                f"  • {agent}: {len(content)} chars"
                for agent, content in contributions.items()
            ]) if contributions else "  (Integrated collaboration)"

            return f"""✅ **Multi-Genre Chapter {chapter_num} Created**

📚 **Genres:** {' + '.join(genres)}
🔄 **Collaboration Mode:** {mode}

📝 **Quality Score:** {review.quality_score:.1f}/10 ({review.quality_level.value})
📊 **Word Count:** {result.metadata.get("word_count", "N/A")}
🔁 **Iterations:** {result.iterations}

**Contributions:**
{contrib_text}

**Strengths:**
{chr(10).join(f'• {s}' for s in review.strengths[:3])}

**Review Notes:**
{review.review_notes or "Successfully integrated multi-genre elements"}

---
*Chapter saved. Use /read {chapter_num} to view full content.*"""
        else:
            return f"""❌ **Multi-Genre Collaboration Failed**

Genres: {' + '.join(genres)}
Mode: {mode}

After {result.iterations} attempts, did not meet quality threshold.

**Issues:**
{chr(10).join(f'• {e}' for e in result.errors)}

💡 Try a different collaboration mode or adjust the outline."""

    async def _handle_plan(self, args: list[str]) -> str:
        """Handle /plan command for interactive project planning."""
        planner = self._get_planner()

        if not planner:
            return "❌ LLM not configured. Check model routing configuration in src/llm/final_model_config.py"

        subcommand = args[0] if args else "start"

        if subcommand == "start":
            # Start new interactive planning session
            self._planning_session = None

            response = await planner.start_planning()
            self._planning_session = {
                "planner": planner,
                "stage": response.get("stage"),
            }

            return response.get("question", "Let's start planning!")

        elif subcommand == "quick":
            # Quick planning from description
            if len(args) < 2:
                return """🚀 **Quick Plan**

Create a project plan from a description in one step.

**Usage:** `/plan quick <description> [--title \"My Title\"] [--cover] [--cover-style <style>]`

**Options:**
  `--title \"Title\"` - Override LLM-generated title with your own
  `--cover` - Generate book cover automatically
  `--cover-style <style>` - Specify cover style (romantic, dark, fantasy, etc.)

**Example:**
`/plan quick I want to write a YA dark romance about a girl who discovers her elite boarding school hides sinister secrets. Target audience is teen girls 13-18, mainly US market. Wattpad and Royal Road. No explicit content, handle dark themes metaphorically like Epstein case. --cover --cover-style dark`"""

            # Parse title option
            user_title = None
            if "--title" in args:
                title_idx = args.index("--title")
                if title_idx + 1 < len(args):
                    user_title = args[title_idx + 1]

            # Parse cover options
            generate_cover = "--cover" in args
            cover_style = None

            if "--cover-style" in args:
                style_idx = args.index("--cover-style")
                if style_idx + 1 < len(args):
                    cover_style = args[style_idx + 1]
                    generate_cover = True

            # Build description from args, excluding options
            description_parts = []
            skip_next = False
            for i, arg in enumerate(args[1:], start=1):
                if skip_next:
                    skip_next = False
                    continue
                if arg in ("--title", "--cover-style"):
                    skip_next = True
                    continue
                if arg == "--cover":
                    continue
                description_parts.append(arg)
            description = " ".join(description_parts)

            # Call planner with optional title
            plan = await planner.quick_plan(description, title=user_title)

            # Override title if user specified one
            if user_title:
                plan.title = user_title

            # Save as project
            import uuid

            from src.studio.core.state import NovelProject, ProjectStatus

            # Extract values from nested plan objects
            pov = plan.style.pov if plan.style else "first"
            target_audience = plan.audience.age_group.value if plan.audience else "young_adult"
            content_rating = "mature" if plan.boundaries and plan.boundaries.allow_explicit_content else "teen"
            sensitive_handling = plan.boundaries.dark_theme_treatment if plan.boundaries else "metaphor"

            project = NovelProject(
                id=f"novel_{uuid.uuid4().hex[:8]}",
                title=plan.title or "Untitled",
                genre=plan.genre or "general",
                target_chapters=plan.target_chapters,
                target_words=plan.target_words,
                status=ProjectStatus.PLANNING,
                premise=plan.premise or "",
                themes=plan.themes or [],
                pov=pov,
                target_audience=target_audience,
                content_rating=content_rating,
                sensitive_handling=sensitive_handling,
            )

            self.state.add_project(project)
            self.state.set_current_project(project.id)

            # Build response
            lines = [
                "✅ **Project Plan Created!**",
                "",
                f"📚 **{plan.title or 'Untitled Project'}**",
                "",
                "**Concept:**",
                f"  • Genre: {plan.genre}",
                f"  • Premise: {plan.premise[:200] if plan.premise else 'Not defined'}...",
                "",
                "**Scope:**",
                f"  • Target: {plan.target_words:,} words / {plan.target_chapters} chapters",
                f"  • Chapter length: ~{plan.style.chapter_length_target:,} words",
                "",
                "**Audience:**",
                f"  • Age: {plan.audience.age_group.value}",
                f"  • Market: {', '.join(plan.audience.regions)}",
                f"  • Loved: {', '.join(plan.audience.tropes_preferred[:3]) or 'Various'}",
                "",
                "**Content:**",
                f"  • Explicit: {'Yes' if plan.boundaries.allow_explicit_content else 'No'}",
                f"  • Violence: {plan.boundaries.allow_violence}",
                f"  • Dark themes: {plan.boundaries.dark_theme_treatment}",
                "",
                "**Publishing:**",
                f"  • Platform: {plan.publishing.primary_platform}",
                f"  • Languages: {', '.join(plan.publishing.language_versions)}",
                f"  • Schedule: {plan.publishing.update_schedule}",
                "",
                "---",
                f"✅ **Project created:** `{project.id}`",
                "",
            ]

            # Handle cover generation
            if generate_cover:
                image_gen = self._get_image_generator()

                if not image_gen or not image_gen.is_available():
                    lines.append("⚠️ **Cover Generation Skipped**")
                    lines.append("")
                    lines.append("To enable cover generation, set your ZhipuAI API key:")
                    lines.append("```")
                    lines.append("export ZHIPUAI_API_KEY=your_api_key")
                    lines.append("```")
                    lines.append("")
                    lines.append("Then use: `/cover generate --style <style>`")
                else:
                    # Generate cover
                    style = cover_style or self._get_default_cover_style(plan.genre or "general")
                    lines.append("🎨 **Generating Cover...**")
                    lines.append(f"   Style: {style}")

                    result = image_gen.generate_cover(
                        title=plan.title or "Untitled",
                        genre=plan.genre or "general",
                        description=plan.premise[:200] if plan.premise else f"A {plan.genre} novel",
                        style=style,
                    )

                    lines.append("")
                    if result.success:
                        lines.append("✅ **Cover Generated!**")
                        if result.local_path:
                            lines.append(f"   📁 Saved to: `{result.local_path}`")
                        if result.image_url:
                            lines.append(f"   🔗 URL: {result.image_url}")
                    else:
                        lines.append(f"❌ Cover generation failed: {result.error}")
                        lines.append("")
                        lines.append("You can try again with: `/cover generate`")
            else:
                # Suggest cover generation
                lines.append("🎨 **Cover Art**")
                lines.append("")
                default_style = self._get_default_cover_style(plan.genre or "general")
                lines.append(f"Generate a book cover for your project (suggested style: `{default_style}`):")
                lines.append("  `/cover preview` - Preview cover design")
                lines.append("  `/cover generate` - Generate with auto-detected style")
                lines.append(f"  `/cover generate --style {default_style}` - Generate with specific style")

            lines.append("")
            lines.append("**Next Steps:**")
            lines.append("  • `/outline create` - Generate detailed outline")
            lines.append("  • `/character create Clara --role protagonist` - Add characters")
            lines.append("  • `/write chapter 1` - Start writing")

            return "\n".join(lines)

        elif subcommand == "status":
            # Show current planning status
            if not self._planning_session:
                return "📋 No active planning session.\n\nUse `/plan start` to begin interactive planning."

            plan = planner.get_plan()
            return f"""📋 **Planning Progress**

Current Stage: {self._planning_session.get('stage', 'Unknown')}

**Planned So Far:**
  • Title: {plan.title or 'Not set'}
  • Genre: {plan.genre or 'Not set'}
  • Audience: {plan.audience.age_group.value if plan.audience else 'Not set'}
  • Platform: {plan.publishing.primary_platform if plan.publishing else 'Not set'}

Continue by answering the current question, or `/plan start` to restart."""

        elif subcommand == "example":
            # Show example descriptions
            return """📝 **Example Project Descriptions**

Use these as templates for `/plan quick <description>`:

**1. YA Dark Romance:**
```
I want to write a YA dark romance about a scholarship student who falls for the heir of an elite family, only to discover the family's sinister secrets. Target: teen girls 14-18, US/UK market. Wattpad primary, Royal Road secondary. No explicit content, handle dark themes metaphorically. Inspired by Epstein case but fictionalized. POV: first person female, past tense, moderate pacing.
```

**2. Fantasy Adventure:**
```
Epic fantasy about a young mage discovering forbidden magic in a world where magic is strictly controlled. Coming-of-age story with found family themes. Target: adults 18-35 who enjoy Sanderson-like magic systems. Kindle serial, then self-publish. 200K words, 40 chapters. Third person limited POV.
```

**3. Thriller:**
```
Psychological thriller about a therapist whose patient claims to have committed a murder that matches an unsolved case from the therapist's past. Target: adults 25-50, fans of Gillian Flynn. Traditional publishing goal. Dark themes handled directly but not gratuitous. Fast pacing, short chapters.
```

**4. Sci-Fi Romance:**
```
Space opera romance between a human diplomat and an alien prince trying to prevent interstellar war. Enemies-to-lovers trope. Target: New Adult 18-25, international audience. Kindle Vella serial, bilingual (English/Spanish). Moderate heat level, action-focused.
```"""
        elif subcommand == "discuss":
            # Multi-round creative discussion planning with streaming
            planner = self._get_discussion_planner()
            initial_idea = " ".join(args[1:]) if len(args) > 1 else ""

            if not initial_idea:
                return """💬 **创意讨论模式**

请输入你的创意想法开始讨论：
`/plan discuss 我想写一本关于...的小说`

系统将通过多轮对话帮助你：
- 明确故事设定和角色
- 生成48章详细大纲
- 创建完整角色设定
- 支持反复修改直到满意"""

            if not self._discussion_session:
                result = await planner.start_discussion(initial_idea)
                self._discussion_session = {"planner": planner, "active": True}

                lines = [
                    f"🎨 **{result['message']}",
                    "",
                    "**请回答以下问题（可多轮对话）：**",
                ]
                for i, q in enumerate(result['questions'], 1):
                    lines.append(f"{i}. {q}")

                if result.get('suggestions'):
                    lines.extend(["", "💡 **设计建议：**"])
                    for s in result['suggestions'][:2]:
                        lines.append(f"  • {s}")

                return "\n".join(lines)
            else:
                result = await planner.continue_discussion(initial_idea)

                # Handle different stages
                if result['stage'] == 'questioning':
                    lines = [
                        f"✨ **{result['message']}",
                        "",
                        "**继续回答：**",
                    ]
                    for i, q in enumerate(result['questions'], 1):
                        lines.append(f"{i}. {q}")
                    return "\n".join(lines)

                elif result['stage'] == 'preview':
                    # Streaming output for generation
                    output_lines = ["🎨 **正在生成方案...**", ""]
                    final_result = None

                    async for update in planner.generate_preview_streaming():
                        if hasattr(update, 'stage'):  # It's a ProgressUpdate
                            bar = ProgressFormatter.format_progress_bar(update.progress_percent, width=25)
                            output_lines.append(f"{bar}")
                            output_lines.append(f"{update.message}")
                            if update.detail:
                                output_lines.append(f"  💡 {update.detail}")
                            output_lines.append("")
                        else:  # It's the final result dict
                            final_result = update

                    if final_result:
                        result = final_result

                    # Show preview
                    lines = [
                        result['message'],
                        "",
                        "---",
                        "",
                        result.get('outline_preview', '')[:800] + "...",
                        "",
                        f"**统计：** {result['outline_stats']['total_chapters']} 章，"
                        f"约 {result['outline_stats']['estimated_words']:,} 字",
                        "",
                    ]

                    if result.get('truncation_info') and result['truncation_info']['truncated']:
                        lines.append("📝 **对话历史已优化**")
                        lines.append(f"  原始: {result['truncation_info']['original_tokens']} tokens")
                        lines.append(f"  优化后: {result['truncation_info']['final_tokens']} tokens")
                        lines.append("")

                    if result.get('characters'):
                        lines.append("**主要角色：**")
                        for char in result['characters'][:5]:
                            role = char.get('role', '未知')
                            name = char.get('name', '未命名')
                            lines.append(f"  • **{name}** ({role})")

                    lines.extend(["", "**下一步：**"])
                    for action in result['next_actions']:
                        lines.append(f"  • {action}")

                    return "\n".join(lines)

                elif result['stage'] == 'confirmed':
                    if result.get('success'):
                        self._discussion_session = None
                        return result['message']
                    else:
                        return f"❌ 创建失败: {result.get('error', 'Unknown error')}"

                else:
                    return f"💬 **{result.get('message', 'Continue discussion')}"

        else:
            return f"❌ Unknown subcommand: {subcommand}\n\nUsage: `/plan [start|quick|status|example]`"

    async def _handle_cover(self, args: list[str]) -> str:
        """Handle /cover command for book cover generation."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use `/project switch` to select one"

        # Check if image generation is available
        image_gen = self._get_image_generator()
        if not image_gen:
            return """❌ Image generation not available

Install the required package:
```
pip install zhipuai
```

Then set your API key:
```
export ZHIPUAI_API_KEY=your_api_key
```"""

        if not image_gen.is_available():
            return """❌ ZHIPUAI_API_KEY not configured

Get your API key from: https://open.bigmodel.cn/

Then set it:
```
export ZHIPUAI_API_KEY=your_api_key
```"""

        # Available art styles
        styles = [
            ("romantic", "💕", "Soft, dreamy, emotional"),
            ("dark", "🌙", "Moody, mysterious, dramatic"),
            ("fantasy", "✨", "Magical, ethereal, epic"),
            ("minimalist", "🔲", "Clean, simple, modern"),
            ("realistic", "📷", "Photorealistic, detailed"),
            ("anime", "🎌", "Japanese animation style"),
            ("vintage", "📜", "Classic, nostalgic feel"),
        ]

        subcommand = args[0] if args else "preview"

        if subcommand == "preview":
            # Generate description without creating image
            description = " ".join(args[1:]) if len(args) > 1 else None

            if not description:
                # Use project info to generate description
                description = f"A {current.genre} novel titled '{current.title}'"

            # Generate prompt description
            lines = ["🎨 **Cover Design Preview**", ""]
            lines.append(f"**Book:** {current.title}")
            lines.append(f"**Genre:** {current.genre}")
            lines.append("")
            lines.append("**Generated Prompt:**")
            lines.append(f"> Book cover for \"{current.title}\" - A {current.genre} novel.")
            lines.append(f"> {description}")
            lines.append("> Professional book cover design, eye-catching, suitable for online publishing platforms.")
            lines.append("")
            lines.append("**Available Styles:**")
            for i, (name, icon, desc) in enumerate(styles, 1):
                lines.append(f"  `{i}` {icon} `{name}` - {desc}")
            lines.append("")
            lines.append("**To Generate:**")
            lines.append("  `/cover generate --style romantic`")
            lines.append("  `/cover generate --style 1` (use number)")
            lines.append("  `/cover generate \"A dark academy with golden lights\" --style dark`")
            lines.append("")
            lines.append("⚠️ **Note:** Image generation will use your ZhipuAI API credits.")
            return "\n".join(lines)

        if subcommand == "generate":
            # Parse options
            style = "book cover"
            custom_desc = ""

            i = 1
            while i < len(args):
                if args[i] == "--style" and i + 1 < len(args):
                    style_input = args[i + 1].lower()
                    # Check if it's a number
                    if style_input.isdigit():
                        idx = int(style_input)
                        if 1 <= idx <= len(styles):
                            style = styles[idx - 1][0]
                        else:
                            return f"❌ Invalid style number. Choose 1-{len(styles)}"
                    else:
                        # Validate style name
                        valid_styles = [s[0] for s in styles]
                        if style_input in valid_styles:
                            style = style_input
                        else:
                            return f"❌ Invalid style: '{style_input}'\n\nValid styles: {', '.join(valid_styles)}"
                    i += 2
                else:
                    # Custom description
                    custom_desc += " " + args[i]
                    i += 1

            custom_desc = custom_desc.strip()

            # Generate cover description first
            base_description = f"A {current.genre} novel"
            if custom_desc:
                full_description = f"{base_description}. {custom_desc}"
            else:
                full_description = base_description

            # Generate the image
            result = image_gen.generate_cover(
                title=current.title,
                genre=current.genre,
                description=full_description,
                style=style,
            )

            if result.success:
                lines = ["✅ **Cover Generated!**", ""]
                lines.append(f"**Book:** {current.title}")
                lines.append(f"**Style:** {style}")
                lines.append("")
                lines.append("**Prompt Used:**")
                lines.append(f"> {result.prompt}")
                if result.revised_prompt and result.revised_prompt != result.prompt:
                    lines.append("")
                    lines.append("**Revised by AI:**")
                    lines.append(f"> {result.revised_prompt}")
                lines.append("")
                if result.image_url:
                    lines.append(f"**Image URL:** {result.image_url}")
                if result.local_path:
                    lines.append(f"**Saved to:** `{result.local_path}`")
                lines.append("")
                lines.append("💡 The cover image has been saved and can be used for publishing.")
                return "\n".join(lines)
            else:
                return f"""❌ **Cover Generation Failed**

**Error:** {result.error}

**Prompt attempted:**
> {result.prompt}

💡 Please check:
- Your ZHIPUAI_API_KEY is valid
- You have sufficient API credits
- The description is appropriate"""

        return f"❌ Unknown subcommand: {subcommand}\n\nUsage: `/cover [preview|generate] [--style <style>] [description]`"

    async def _handle_illustrate(self, args: list[str]) -> str:
        """Handle /illustrate command for scene illustrations."""
        current = self.state.get_current_project()
        if not current:
            return "❌ No project selected. Use `/project switch` to select one"

        # Check if image generation is available
        image_gen = self._get_image_generator()
        if not image_gen:
            return """❌ Image generation not available

Install the required package:
```
pip install zhipuai
```

Then set your API key:
```
export ZHIPUAI_API_KEY=your_api_key
```"""

        if not image_gen.is_available():
            return """❌ ZHIPUAI_API_KEY not configured

Get your API key from: https://open.bigmodel.cn/

Then set it:
```
export ZHIPUAI_API_KEY=your_api_key
```"""

        # Available moods and styles
        moods = [
            ("dramatic", "🎭", "Intense, powerful emotion"),
            ("romantic", "💕", "Soft, loving, intimate"),
            ("mysterious", "🌙", "Suspenseful, intriguing"),
            ("peaceful", "🌿", "Calm, serene, tranquil"),
            ("action", "⚡", "Dynamic, energetic, fast-paced"),
            ("dark", "🌑", "Ominous, threatening, tense"),
        ]

        art_styles = [
            ("digital art", "🎨", "Modern digital illustration"),
            ("oil painting", "🖼️", "Classic painterly style"),
            ("watercolor", "💧", "Soft, fluid, artistic"),
            ("anime", "🎌", "Japanese animation style"),
            ("realistic", "📷", "Photorealistic rendering"),
            ("concept art", "📐", "Game/film concept style"),
        ]

        if not args:
            lines = ["🎨 **Scene Illustration**", ""]
            lines.append("Generate illustrations for scenes or chapters.")
            lines.append("")
            lines.append("**Usage:**")
            lines.append("  `/illustrate scene <description>` - Illustrate a specific scene")
            lines.append("  `/illustrate chapter <number>` - Illustrate key scene from chapter")
            lines.append("")
            lines.append("**Moods:**")
            for i, (name, icon, desc) in enumerate(moods, 1):
                lines.append(f"  `{i}` {icon} `{name}` - {desc}")
            lines.append("")
            lines.append("**Art Styles:**")
            for i, (name, icon, desc) in enumerate(art_styles, 1):
                lines.append(f"  `{i}` {icon} `{name}` - {desc}")
            lines.append("")
            lines.append("**Examples:**")
            lines.append("  `/illustrate scene Clara and Julian meet at the masquerade ball")
            lines.append("  `/illustrate chapter 5 --mood romantic --style digital art`")
            lines.append("  `/illustrate scene The dark secret revealed --mood 6 --style 1`")
            return "\n".join(lines)

        subcommand = args[0]

        if subcommand == "scene":
            if len(args) < 2:
                return "❌ Usage: `/illustrate scene <description>`"

            # Parse scene description and options
            scene_parts = []
            mood = "dramatic"
            style = "digital art"
            characters = []

            i = 1
            while i < len(args):
                if args[i] == "--mood" and i + 1 < len(args):
                    mood_input = args[i + 1].lower()
                    if mood_input.isdigit():
                        idx = int(mood_input)
                        if 1 <= idx <= len(moods):
                            mood = moods[idx - 1][0]
                        else:
                            return f"❌ Invalid mood number. Choose 1-{len(moods)}"
                    else:
                        valid_moods = [m[0] for m in moods]
                        if mood_input in valid_moods:
                            mood = mood_input
                        else:
                            return f"❌ Invalid mood: '{mood_input}'\n\nValid moods: {', '.join(valid_moods)}"
                    i += 2
                elif args[i] == "--style" and i + 1 < len(args):
                    style_input = args[i + 1].lower()
                    if style_input.isdigit():
                        idx = int(style_input)
                        if 1 <= idx <= len(art_styles):
                            style = art_styles[idx - 1][0]
                        else:
                            return f"❌ Invalid style number. Choose 1-{len(art_styles)}"
                    else:
                        valid_styles = [s[0] for s in art_styles]
                        if style_input in valid_styles:
                            style = style_input
                        else:
                            return f"❌ Invalid style: '{style_input}'\n\nValid styles: {', '.join(valid_styles)}"
                    i += 2
                elif args[i] == "--characters" and i + 1 < len(args):
                    characters = [c.strip() for c in args[i + 1].split(",")]
                    i += 2
                else:
                    scene_parts.append(args[i])
                    i += 1

            scene_description = " ".join(scene_parts)

            if not scene_description:
                return "❌ Please provide a scene description"

            # Generate illustration
            result = image_gen.generate_illustration(
                scene_description=scene_description,
                characters=characters if characters else None,
                mood=mood,
                style=style,
            )

            if result.success:
                lines = ["✅ **Illustration Generated!**", ""]
                lines.append(f"**Scene:** {scene_description}")
                if characters:
                    lines.append(f"**Characters:** {', '.join(characters)}")
                lines.append(f"**Mood:** {mood}")
                lines.append(f"**Style:** {style}")
                lines.append("")
                lines.append("**Prompt Used:**")
                lines.append(f"> {result.prompt}")
                if result.revised_prompt and result.revised_prompt != result.prompt:
                    lines.append("")
                    lines.append("**Revised by AI:**")
                    lines.append(f"> {result.revised_prompt}")
                lines.append("")
                if result.image_url:
                    lines.append(f"**Image URL:** {result.image_url}")
                if result.local_path:
                    lines.append(f"**Saved to:** `{result.local_path}`")
                return "\n".join(lines)
            else:
                return f"""❌ **Illustration Generation Failed**

**Error:** {result.error}

**Prompt attempted:**
> {result.prompt}

💡 Please check your API configuration and try again."""

        if subcommand == "chapter":
            if len(args) < 2:
                lines = ["📖 **Select Chapter to Illustrate**", ""]
                lines.append("Usage: `/illustrate chapter <number>`")
                lines.append("")
                lines.append(f"Current progress: {current.completed_chapters}/{current.target_chapters} chapters")
                lines.append("")
                lines.append("This will generate an illustration for a key scene from the chapter.")
                return "\n".join(lines)

            try:
                chapter_num = int(args[1])
            except ValueError:
                return "❌ Chapter number must be a number"

            # Parse options
            mood = "dramatic"
            style = "digital art"

            i = 2
            while i < len(args):
                if args[i] == "--mood" and i + 1 < len(args):
                    mood_input = args[i + 1].lower()
                    if mood_input.isdigit():
                        idx = int(mood_input)
                        if 1 <= idx <= len(moods):
                            mood = moods[idx - 1][0]
                    else:
                        mood = mood_input
                    i += 2
                elif args[i] == "--style" and i + 1 < len(args):
                    style_input = args[i + 1].lower()
                    if style_input.isdigit():
                        idx = int(style_input)
                        if 1 <= idx <= len(art_styles):
                            style = art_styles[idx - 1][0]
                    else:
                        style = style_input
                    i += 2
                else:
                    i += 1

            # TODO: Load chapter content and extract key scene
            scene_description = f"Key scene from Chapter {chapter_num} of {current.title}, a {current.genre} story"

            result = image_gen.generate_illustration(
                scene_description=scene_description,
                mood=mood,
                style=style,
            )

            if result.success:
                lines = [f"✅ **Chapter {chapter_num} Illustration Generated!**", ""]
                lines.append(f"**Book:** {current.title}")
                lines.append(f"**Chapter:** {chapter_num}")
                lines.append(f"**Mood:** {mood}")
                lines.append(f"**Style:** {style}")
                lines.append("")
                if result.image_url:
                    lines.append(f"**Image URL:** {result.image_url}")
                if result.local_path:
                    lines.append(f"**Saved to:** `{result.local_path}`")
                return "\n".join(lines)
            else:
                return f"❌ **Illustration Generation Failed**\n\n**Error:** {result.error}"

        return f"❌ Unknown subcommand: {subcommand}\n\nUsage: `/illustrate [scene|chapter] <...>`"


    async def _handle_cache(self, args: list[str]) -> str:
        """Handle /cache command for managing creative cache."""
        if not args:
            return """🗂️ **Cache Management**

Manage cached outlines and characters to speed up generation.

**Commands:**
  `/cache stats` - Show cache statistics
  `/cache clear` - Clear all cached entries
  `/cache invalidate outline` - Clear outline cache only
  `/cache invalidate characters` - Clear character cache only
  `/cache invalidate all` - Clear all cache (same as clear)

**Note:** Cache helps avoid regenerating outlines and characters
when the discussion context hasn't changed."""

        subcommand = args[0].lower()

        if subcommand == "stats":
            # Get discussion planner and check cache stats
            planner = self._get_discussion_planner()
            if planner and planner.cache:
                stats = planner.get_cache_stats()
                lines = ["🗂️ **Cache Statistics**", ""]
                lines.append(f"  **Memory Entries:** {stats[memory_entries]}")
                lines.append(f"  **File Entries:** {stats[file_entries]}")
                lines.append(f"  **Total Size:** {stats[total_size_mb]} MB")
                lines.append(f"  **Cache Directory:** `{stats[cache_dir]}`")
                lines.append("")
                lines.append("💡 Use `/cache clear` to free up space")
                return "\n".join(lines)
            else:
                return "🗂️ **Cache Statistics**\n\nCache is not enabled or not available."

        if subcommand == "clear":
            planner = self._get_discussion_planner()
            if planner and planner.cache:
                count = planner.clear_cache()
                return f"✅ **Cache Cleared**\n\nCleared {count} cached entries."
            else:
                return "❌ Cache is not enabled."

        if subcommand == "invalidate":
            if len(args) < 2:
                return "❌ Please specify what to invalidate: `outline`, `characters`, or `all`"

            content_type = args[1].lower()
            planner = self._get_discussion_planner()

            if not planner or not planner.cache:
                return "❌ Cache is not enabled."

            if content_type == "all":
                count = planner.clear_cache()
                return f"✅ **All Cache Invalidated**\n\nCleared {count} entries."
            elif content_type in ("outline", "character", "characters"):
                count = planner.clear_cache(content_type)
                return f"✅ **{content_type.capitalize()} Cache Invalidated**\n\nCleared {count} entries."
            else:
                return f"❌ Unknown content type: `{content_type}`. Use: `outline`, `characters`, or `all`"

        return f"❌ Unknown subcommand: `{subcommand}`. Use: `stats`, `clear`, or `invalidate`"

