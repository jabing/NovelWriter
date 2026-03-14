"""CLI extension commands for project management, settings, and more."""

import click
from rich.console import Console

console = Console()


def register_project_commands(project_group):
    """Register additional project commands."""

    @project_group.command()
    @click.argument("project_id")
    @click.option("--confirm", "-y", is_flag=True, help="Confirm deletion without prompt")
    def delete(project_id: str, confirm: bool) -> None:
        """Delete a project."""
        from src.novel_agent.studio.core.state import get_studio_state

        state = get_studio_state()
        projects = state.get_projects()

        # 检查是否为数字序号
        if project_id.isdigit():
            idx = int(project_id)
            if 1 <= idx <= len(projects):
                project_to_delete = projects[idx - 1]
            else:
                console.print(f"[red]Invalid number. Choose 1-{len(projects)}[/red]")
                return
        else:
            project_to_delete = state.get_project(project_id)

        if not project_to_delete:
            console.print(f"[red]Project not found: {project_id}[/red]")
            return

        # 显示确认提示
        if not confirm:
            console.print("\n[yellow]Project to delete:[/yellow]")
            console.print(f"  [bold]{project_to_delete.title}[/bold] ({project_to_delete.id})")
            console.print(f"  Genre: {project_to_delete.genre}")
            console.print(
                f"  Progress: {project_to_delete.completed_chapters}/{project_to_delete.target_chapters} chapters"
            )
            console.print("\n[red]This action cannot be undone![/red]")
            console.print("\n[yellow]To confirm, use:[/yellow]")
            console.print(f"  novel-agent project delete {project_id} --confirm")
            return

        # 执行删除
        success = state.delete_project(project_to_delete.id)

        if success:
            console.print(f"[green]Deleted:[/green] {project_to_delete.title}")
        else:
            console.print("[red]Failed to delete project[/red]")

    @project_group.command()
    @click.argument("project_id", required=False)
    def switch(project_id: str | None) -> None:
        """Switch to a different project."""
        from src.novel_agent.studio.core.state import get_studio_state

        state = get_studio_state()
        projects = state.get_projects()

        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            return

        current = state.get_current_project()
        current_id = current.id if current else None

        if project_id is None:
            console.print("[bold]Available Projects:[/bold]")
            for i, p in enumerate(projects, 1):
                marker = "-> " if current_id == p.id else "   "
                status_icon = {
                    "planning": "🔵",
                    "writing": "🟢",
                    "paused": "🟡",
                    "completed": "✅",
                }.get(p.status.value, "⚪")
                console.print(f"{marker}{i}. {status_icon} {p.title} ({p.id})")
                console.print(
                    f"     {p.completed_chapters}/{p.target_chapters} chapters | {p.genre}"
                )
            return

        # 查找项目
        project = state.get_project(project_id)
        if not project and project_id.isdigit():
            idx = int(project_id)
            if 1 <= idx <= len(projects):
                project = projects[idx - 1]

        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            return

        state.set_current_project(project.id)
        console.print(f"[green]Switched to:[/green] {project.title}")


def register_read_commands(cli_group):
    """Register read command."""

    @cli_group.command()
    @click.argument("chapter", required=False)
    @click.option("--list", "list_chapters", is_flag=True, help="List all chapters")
    @click.option("--latest", is_flag=True, help="Show the latest chapter")
    def read(chapter: str | None, list_chapters: bool, latest: bool) -> None:
        """Read generated chapters."""
        from pathlib import Path

        from src.novel_agent.studio.core.state import get_studio_state

        state = get_studio_state()
        project = state.get_current_project()

        if not project:
            console.print("[yellow]No current project selected.[/yellow]")
            return

        chapters_dir = Path(f"data/openviking/memory/novels/{project.id}/chapters")

        if not chapters_dir.exists():
            console.print("[yellow]No chapters found for this project.[/yellow]")
            return

        if list_chapters:
            files = sorted(chapters_dir.glob("chapter_*.md"))
            console.print(f"\n[bold]Chapters for {project.title}:[/bold]\n")
            if not files:
                console.print("  [yellow]No chapters found.[/yellow]")
            else:
                for f in files:
                    title = "Untitled"
                    with open(f, encoding="utf-8") as chapter_file:
                        first_line = chapter_file.readline().strip()
                        if first_line.startswith("#"):
                            title = first_line.lstrip("#").strip()
                    console.print(f"  [cyan]{f.stem}[/cyan] - {title}")
            return

        if latest:
            files = sorted(chapters_dir.glob("chapter_*.md"))
            if not files:
                console.print("[yellow]No chapters found.[/yellow]")
                return
            chapter_file = files[-1]
        elif chapter:
            if chapter.isdigit():
                chapter_num = int(chapter)
                chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
            else:
                chapter_file = chapters_dir / f"{chapter}.md"

            if not chapter_file.exists():
                console.print(f"[red]Chapter not found: {chapter}[/red]")
                return
        else:
            files = sorted(chapters_dir.glob("chapter_*.md"))
            if not files:
                console.print("[yellow]No chapters found.[/yellow]")
                return
            chapter_file = files[-1]

        with open(chapter_file, encoding="utf-8") as f:
            chapter_content = f.read()

        console.print(f"\n[bold]Reading: {chapter_file.stem}[/bold]\n")
        console.print(chapter_content)


def register_settings_commands(cli_group):
    """Register settings command group."""

    @cli_group.group()
    def settings() -> None:
        """Manage studio settings for content generation."""
        pass

    @settings.command()
    def show() -> None:
        """Show current settings."""
        from src.novel_agent.studio.core.settings import get_settings

        settings = get_settings()
        console.print("[bold]Studio Settings:[/bold]\n")
        console.print(f"  Quality Mode: [cyan]{settings.quality_mode}[/cyan]")
        console.print(f"  Iterations: {settings.iterations}")
        console.print(f"  Approval Threshold: {settings.approval_threshold}")
        console.print(f"  Auto-revise Threshold: {settings.auto_revise_threshold}")
        console.print(
            f"  Learning: [cyan]{'Enabled' if settings.enable_learning else 'Disabled'}[/cyan]"
        )
        console.print(f"  UI Language: {settings.ui_language}")

    @settings.command()
    @click.argument("mode", type=click.Choice(["fast", "balanced", "high", "ultra"]))
    def set_mode(mode: str) -> None:
        """Set quality preset mode."""
        from src.novel_agent.studio.core.settings import get_settings_manager

        manager = get_settings_manager()
        description = manager.apply_preset(mode)
        console.print(f"[green]Quality mode set to:[/green] [cyan]{mode}[/cyan]")
        console.print(f"  {description}")

    @settings.command("set")
    @click.argument("param", required=False)
    @click.argument("value", required=False)
    def set_setting(param: str | None, value: str | None) -> None:
        """Set a specific setting parameter."""
        from src.novel_agent.studio.core.settings import get_settings_manager

        manager = get_settings_manager()

        if param is None and value is None:
            # Show current settings (same as show command)
            settings = manager.get_settings()
            console.print("[bold]Studio Settings:[/bold]\n")
            console.print(f"  Quality Mode: [cyan]{settings.quality_mode}[/cyan]")
            console.print(f"  Iterations: {settings.iterations}")
            console.print(f"  Approval Threshold: {settings.approval_threshold}")
            console.print(f"  Auto-revise Threshold: {settings.auto_revise_threshold}")
            console.print(
                f"  Learning: [cyan]{'Enabled' if settings.enable_learning else 'Disabled'}[/cyan]"
            )
            console.print(f"  UI Language: {settings.ui_language}")
            return

        if param is None or value is None:
            console.print("[red]Both param and value are required[/red]")
            console.print("[yellow]Usage: novel-agent settings set <param> <value>[/yellow]")
            console.print("[yellow]Example: novel-agent settings set iterations 3[/yellow]")
            return

        # Convert value to appropriate type
        try:
            if param in ["iterations"]:
                parsed_value = int(value)
            elif param in ["approval_threshold", "auto_revise_threshold"]:
                parsed_value = float(value)
            elif param in ["enable_learning"]:
                parsed_value = value.lower() in ["true", "1", "yes", "on"]
            elif param in ["ui_language"]:
                parsed_value = value
            elif param in ["quality_mode"]:
                # Quality mode uses apply_preset
                description = manager.apply_preset(value)
                console.print(f"[green]Quality mode set to:[/green] [cyan]{value}[/cyan]")
                console.print(f"  {description}")
                return
            else:
                # Try to infer type or pass as string
                parsed_value = value
        except ValueError:
            console.print(f"[red]Invalid value for {param}: {value}[/red]")
            return

        # Update settings
        try:
            manager.update_settings(**{param: parsed_value})
            console.print(f"[green]Set {param} to:[/green] {parsed_value}")
        except Exception as e:
            console.print(f"[red]Failed to update setting: {e}[/red]")
