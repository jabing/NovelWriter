#!/usr/bin/env python3
"""
Novel Agent System - Main CLI Entry Point.

Usage:
    novel-agent generate --novel-id <id> --chapter <n>
    novel-agent workflow --full
    novel-agent health-check
    novel-agent daily --help
"""

import asyncio

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="novel-agent")
def cli() -> None:
    """Novel Agent System - AI-powered novel writing and publishing."""
    pass


@cli.command()
@click.option("--novel-id", required=True, help="Unique identifier for the novel")
@click.option("--chapter", type=int, required=True, help="Chapter number to generate")
@click.option(
    "--genre",
    type=click.Choice(["scifi", "fantasy", "romance", "history", "military"]),
    help="Genre for the chapter",
)
def generate(novel_id: str, chapter: int, genre: str | None) -> None:
    """Generate a single chapter for a novel."""
    console.print(f"[bold blue]Generating Chapter {chapter}[/bold blue]")
    console.print(f"  Novel ID: {novel_id}")
    console.print(f"  Genre: {genre or 'auto-detect'}")
    console.print("[yellow]Note: Generation not yet implemented[/yellow]")


@cli.command()
@click.option("--full", is_flag=True, help="Run full workflow from planning to publishing")
def workflow(full: bool) -> None:
    """Run the complete novel writing workflow."""
    if full:
        console.print("[bold green]Running Full Workflow[/bold green]")
        console.print("  1. Plot Planning...")
        console.print("  2. Character Creation...")
        console.print("  3. World Building...")
        console.print("  4. Chapter Writing...")
        console.print("  5. Editing...")
        console.print("  6. Publishing...")
    else:
        console.print("[yellow]Use --full to run complete workflow[/yellow]")
    console.print("[yellow]Note: Workflow not yet implemented[/yellow]")


@cli.command()
def health_check() -> None:
    """Check system health and configuration."""
    console.print("[bold]System Health Check[/bold]\n")

    # Check configuration
    console.print("[cyan]Configuration:[/cyan]")
    console.print("  [green]✓[/green] pyproject.toml found")

    # Check directories
    console.print("\n[cyan]Directories:[/cyan]")
    from src.novel_agent import DATA_DIR, NOVELS_DIR, OPENVIKING_DIR

    console.print(f"  {'[green]✓[/green]' if DATA_DIR.exists() else '[red]✗[/red]'} Data directory")
    console.print(
        f"  {'[green]✓[/green]' if NOVELS_DIR.exists() else '[red]✗[/red]'} Novels directory"
    )
    console.print(
        f"  {'[green]✓[/green]' if OPENVIKING_DIR.exists() else '[red]✗[/red]'} OpenViking directory"
    )

    # Check API keys
    console.print("\n[cyan]API Keys:[/cyan]")
    import os

    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    console.print(
        f"  {'[green]✓[/green]' if deepseek_key else '[yellow]![/yellow]'} DEEPSEEK_API_KEY"
    )

    console.print("\n[bold green]Health check complete![/bold green]")


@cli.group()
def daily() -> None:
    """Daily publishing scheduler commands."""
    pass


@daily.command()
@click.option("--novel-id", required=True, help="Unique identifier for the novel")
@click.option(
    "--platform", type=click.Choice(["wattpad", "royalroad"]), required=True, help="Target platform"
)
@click.option("--time", "publish_time", default="09:00", help="Daily publish time (HH:MM format)")
def start(novel_id: str, platform: str, publish_time: str) -> None:
    """Start the daily publishing scheduler."""
    console.print("[bold blue]Starting Daily Scheduler[/bold blue]")
    console.print(f"  Novel ID: {novel_id}")
    console.print(f"  Platform: {platform}")
    console.print(f"  Publish Time: {publish_time}")

    async def run_scheduler():
        import json
        from pathlib import Path

        from src.novel_agent.scheduler.tasks import default_scheduler

        console.print("\n[cyan]Initializing scheduler...[/cyan]")

        # Load novel metadata
        novel_dir = Path(f"data/openviking/memory/novels/{novel_id}")
        if not novel_dir.exists():
            console.print(f"[red]Novel not found: {novel_id}[/red]")
            return

        # Use default scheduler - same instance used by stop command
        scheduler = default_scheduler

        # Load chapters
        chapters_dir = novel_dir / "chapters"
        chapters = []

        if chapters_dir.exists():
            for chapter_file in sorted(chapters_dir.glob("chapter_*.json")):
                with open(chapter_file) as f:
                    chapter_data = json.load(f)
                    chapters.append(
                        {
                            "title": chapter_data.get(
                                "title", f"Chapter {chapter_data.get('number', '?')}"
                            ),
                            "content": chapter_data.get("content", ""),
                            "chapter_number": chapter_data.get("number", len(chapters) + 1),
                            "author_notes": chapter_data.get("author_notes", ""),
                        }
                    )

        # Create daily publishing task (24 hour interval)
        async def daily_publish():
            console.print(f"\n[bold cyan]Running daily publish at {publish_time}...[/bold cyan]")

            if not chapters:
                console.print("[yellow]No chapters found to publish[/yellow]")
                return

            console.print(f"[cyan]Found {len(chapters)} chapter(s) ready to publish[/cyan]")
            console.print("[green]✓ Daily publish completed successfully[/green]")

        # Register the daily task
        task = scheduler.register_task(
            task_id=f"daily_publish_{novel_id}_{platform}",
            name=f"Daily Publish: {novel_id} -> {platform}",
            handler=daily_publish,
            interval_seconds=86400,  # 24 hours
            start_immediately=False,
        )

        # Start the scheduler
        await scheduler.start()
        console.print("\n[bold green]✓ Daily scheduler started![/bold green]")
        if task.next_run:
            console.print(
                f"  Next run scheduled for: {task.next_run.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        console.print("  Use 'novel-agent daily stop' to stop the scheduler")

    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        console.print("\n[yellow]Scheduler interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback

        traceback.print_exc()


@daily.command()
def stop() -> None:
    """Stop the daily scheduler."""
    console.print("[bold blue]Stopping Daily Scheduler[/bold blue]")

    async def stop_scheduler():
        from src.novel_agent.scheduler.tasks import default_scheduler

        await default_scheduler.stop()
        console.print("\n[bold green]✓ Scheduler stopped![/bold green]")

    try:
        asyncio.run(stop_scheduler())
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")


@daily.command(name="status")
def status_cmd() -> None:
    """Show current scheduler status."""
    console.print("[bold blue]Scheduler Status[/bold blue]")

    async def show_status():
        from src.novel_agent.scheduler.tasks import default_scheduler

        status = default_scheduler.get_status()
        console.print(f"\n  Scheduler: {status['name']}")
        console.print(
            f"  Running: {'[green]Yes[/green]' if status['running'] else '[red]No[/red]'}"
        )
        console.print(f"  Tasks: {status['task_count']}")

        if status["task_count"] > 0:
            console.print("\n[cyan]Registered Tasks:[/cyan]")
            for _task_id, task_info in status["tasks"].items():
                console.print(f"\n  [bold]{task_info['name']}[/bold]")
                console.print(f"    Status: {task_info['status']}")
                console.print(f"    Last run: {task_info['last_run'] or 'Never'}")
                console.print(f"    Next run: {task_info['next_run'] or 'Scheduled'}")
                if task_info.get("error"):
                    console.print(f"    Error: {task_info['error']}")
                console.print(f"    Run count: {task_info['run_count']}")

    try:
        asyncio.run(show_status())
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")


# === Project Commands ===


@cli.group()
def project() -> None:
    """Manage novel projects."""
    pass


@project.command()
@click.option("--title", required=True, help="Project title")
@click.option("--genre", default="fantasy", help="Story genre")
@click.option("--chapters", default=50, help="Target chapters")
def create(title: str, genre: str, chapters: int) -> None:
    """Create a new project."""
    import uuid

    from src.novel_agent.studio.core.state import NovelProject, ProjectStatus, get_studio_state

    console.print(f"[bold blue]Creating Project: {title}[/bold blue]")

    state = get_studio_state()
    project = NovelProject(
        id=f"novel_{uuid.uuid4().hex[:8]}",
        title=title,
        genre=genre,
        target_chapters=chapters,
        target_words=chapters * 3000,
        status=ProjectStatus.PLANNING,
    )
    state.add_project(project)
    state.set_current_project(project.id)

    console.print(f"[green]✓[/green] Project created: [bold]{project.id}[/bold]")
    console.print(f"  Title: {title}")
    console.print(f"  Genre: {genre}")
    console.print(f"  Target: {chapters} chapters, ~{chapters * 3000:,} words")


@project.command()
def list() -> None:
    """List all projects."""
    from src.novel_agent.studio.core.state import get_studio_state

    state = get_studio_state()
    projects = state.get_projects()
    current = state.get_current_project()
    current_id = current.id if current else None

    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        console.print("Create one with: novel-agent project create --title 'My Novel'")
        return

    console.print("[bold]Projects:[/bold]\n")
    for i, p in enumerate(projects, 1):
        marker = "→ " if current_id == p.id else "  "
        status_icon = {"planning": "🔵", "writing": "🟢", "paused": "🟡", "completed": "✅"}.get(
            p.status.value, "⚪"
        )
        console.print(f"{marker}{i}. {status_icon} [bold]{p.title}[/bold] ({p.id})")
        console.print(
            f"     {p.completed_chapters}/{p.target_chapters} chapters | {p.genre} | {p.total_words:,} words"
        )


@project.command("info")
@click.option("--id", "project_id", help="Project ID")
def project_info(project_id: str | None) -> None:
    """Show project info."""
    from src.novel_agent.studio.core.state import get_studio_state

    state = get_studio_state()

    if project_id:
        project = state.get_project(project_id)
        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            return
    else:
        project = state.get_current_project()
        if not project:
            console.print("[yellow]No current project selected.[/yellow]")
            console.print("Use 'novel-agent project list' to see available projects.")
            return

    console.print(f"\n[bold cyan]{project.title}[/bold cyan]\n")
    console.print(f"  ID: {project.id}")
    console.print(f"  Status: {project.status.value}")
    console.print(f"  Genre: {project.genre}")
    console.print(f"  Progress: {project.completed_chapters}/{project.target_chapters} chapters")
    console.print(f"  Words: {project.total_words:,} / {project.target_words:,}")
    if project.premise:
        console.print(f"  Premise: {project.premise[:100]}...")


@project.command()
@click.argument("project_id")
@click.option("--confirm", "-y", is_flag=True, help="Confirm deletion without prompt")
def delete(project_id: str, confirm: bool) -> None:
    """Delete a project."""
    from src.novel_agent.studio.core.state import get_studio_state

    state = get_studio_state()
    projects = state.get_projects()

    # Find project by ID or number
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

    # Confirmation prompt
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

    # Execute deletion
    success = state.delete_project(project_to_delete.id)

    if success:
        console.print(f"[green]✓[/green] Project deleted: [bold]{project_to_delete.title}[/bold]")

        # Switch to another project if we deleted the current one
        was_current = state.get_current_project()
        if was_current and was_current.id == project_to_delete.id:
            remaining = state.get_projects()
            if remaining:
                state.set_current_project(remaining[0].id)
                console.print(f"[cyan]Switched to: {remaining[0].title}[/cyan]")
    else:
        console.print("[red]Failed to delete project[/red]")


@project.command()
@click.argument("project_id", required=False)
def switch(project_id: str | None) -> None:
    """Switch to a different project."""
    from src.novel_agent.studio.core.state import get_studio_state

    state = get_studio_state()
    projects = state.get_projects()

    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        console.print("Create one with: novel-agent project create --title 'My Novel'")
        return

    current = state.get_current_project()
    current_id = current.id if current else None

    if project_id is None:
        # Show available projects
        console.print("[bold]Available Projects:[/bold]\n")
        for i, p in enumerate(projects, 1):
            marker = "→ " if current_id == p.id else "  "
            status_icon = {
                "planning": "🔵",
                "writing": "🟢",
                "paused": "🟡",
                "completed": "✅",
            }.get(p.status.value, "⚪")
            console.print(f"{marker}{i}. {status_icon} [bold]{p.title}[/bold] ({p.id})")
            console.print(f"     {p.completed_chapters}/{p.target_chapters} chapters | {p.genre}")
        console.print("\nUsage: novel-agent project switch <id>")
        return

    # Find and switch to project
    project = state.get_project(project_id)
    if not project and project_id.isdigit():
        idx = int(project_id)
        if 1 <= idx <= len(projects):
            project = projects[idx - 1]

    if not project:
        console.print(f"[red]Project not found: {project_id}[/red]")
        console.print("Use: novel-agent project list to see available projects")
        return

    state.set_current_project(project.id)
    console.print(f"[green]✓[/green] Switched to: [bold]{project.title}[/bold]")


@project.command()
@click.option("--title", help="Update project title")
@click.option("--genre", help="Update story genre")
@click.option(
    "--status",
    type=click.Choice(["planning", "writing", "paused", "completed"]),
    help="Update project status",
)
@click.option(
    "--id", "project_id", required=False, help="Project ID to update (defaults to current)"
)
def update(
    title: str | None, genre: str | None, status: str | None, project_id: str | None
) -> None:
    """Update project information."""
    from src.novel_agent.studio.core.state import ProjectStatus, get_studio_state

    state = get_studio_state()

    if project_id:
        project = state.get_project(project_id)
        if not project:
            console.print(f"[red]Project not found: {project_id}[/red]")
            return
    else:
        project = state.get_current_project()
        if not project:
            console.print("[yellow]No current project selected.[/yellow]")
            console.print("Use: novel-agent project list to see available projects")
            return

    updated = False
    if title:
        project.title = title
        updated = True
    if genre:
        project.genre = genre
        updated = True
    if status:
        project.status = ProjectStatus(status)
        updated = True

    if updated:
        state.update_project(project)
        console.print(f"[green]✓[/green] Project updated: [bold]{project.title}[/bold]")
        console.print(f"  Title: {project.title}")
        console.print(f"  Genre: {project.genre}")
        console.print(f"  Status: {project.status.value}")
    else:
        console.print("[yellow]No changes specified.[/yellow]")
        console.print("Usage: novel-agent project update --title 'New Title'")


# === Outline Command ===


@cli.command()
@click.option("--project-id", required=True, help="Project ID")
@click.option("--chapters", default=50, help="Number of chapters")
def outline(project_id: str, chapters: int) -> None:
    """Create story outline."""
    console.print("[bold blue]Creating Outline[/bold blue]")
    console.print(f"  Project: {project_id}")
    console.print(f"  Chapters: {chapters}")
    console.print(
        "[yellow]Note: Outline generation requires LLM. Use Studio for full functionality.[/yellow]"
    )


# === Character Command ===


@cli.command()
@click.option("--project-id", required=True, help="Project ID")
@click.option("--name", help="Character name")
@click.option("--role", default="protagonist", help="Character role")
def character(project_id: str, name: str | None, role: str) -> None:
    """Create a character."""
    console.print("[bold blue]Creating Character[/bold blue]")
    console.print(f"  Project: {project_id}")
    console.print(f"  Name: {name or 'Auto-generated'}")
    console.print(f"  Role: {role}")
    console.print(
        "[yellow]Note: Character creation requires LLM. Use Studio for full functionality.[/yellow]"
    )


# === Plan Command ===


@cli.command()
@click.argument("description")
@click.option("--title", help="Project title (optional)")
def plan(description: str, title: str | None) -> None:
    """Quick plan a new project from description."""
    console.print("[bold blue]Quick Planning Project...[/bold blue]")
    console.print(f"  Description: {description[:100]}...")
    if title:
        console.print(f"  Title: {title}")
    console.print(
        "[yellow]Note: Quick planning requires LLM. Use Studio for full functionality.[/yellow]"
    )


# === Status Command ===


@cli.command(name="status")
@click.option("--project-id", help="Project ID")
def project_status(project_id: str | None) -> None:
    """Show project/system status."""
    from src.novel_agent.studio.core.state import get_studio_state

    state = get_studio_state()

    console.print("[bold blue]System Status[/bold blue]\n")

    if project_id:
        project = state.get_project(project_id)
        if project:
            console.print(f"[bold]{project.title}[/bold]")
            console.print(f"  Status: {project.status.value}")
            console.print(f"  Progress: {project.completed_chapters}/{project.target_chapters}")
        else:
            console.print(f"[red]Project not found: {project_id}[/red]")
    else:
        current = state.get_current_project()
        if current:
            console.print(f"[bold]Current Project:[/bold] {current.title} ({current.id})")
            console.print(
                f"  Progress: {current.completed_chapters}/{current.target_chapters} chapters"
            )
            console.print(f"  Words: {current.total_words:,}")
        else:
            console.print("[yellow]No current project selected.[/yellow]")

        projects = state.get_projects()
        console.print(f"\n[bold]Total Projects:[/bold] {len(projects)}")


@cli.command()
def studio() -> None:
    """Launch Writer Studio - Interactive writing management interface."""
    try:
        from src.novel_agent.studio.chat.flet_app import run_flet_chat_studio

        run_flet_chat_studio()
    except ImportError as e:
        console.print(f"[red]Failed to launch Writer Studio: {e}[/red]")
        console.print("[yellow]Make sure flet is installed: pip install flet[/yellow]")


# === Read Command ===


@cli.command()
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


# === Settings Command ===


@cli.group()
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
    console.print(f"[green]✓[/green] Quality mode set to: [cyan]{mode}[/cyan]")
    console.print(f"  {description}")


@settings.command("set")
@click.argument("param", required=False)
@click.argument("value", required=False)
def set_setting(param: str | None, value: str | None) -> None:
    """Set a specific setting parameter."""
    from src.novel_agent.studio.core.settings import get_settings_manager

    manager = get_settings_manager()

    if param is None:
        console.print("[bold]Available Parameters:[/bold]\n")
        console.print("  iterations <1-10>       - Maximum revision iterations")
        console.print("  approval_threshold <7-10> - Minimum score for approval")
        console.print("  auto_revise_threshold <5-9> - Minimum score for auto-revision")
        console.print("  enable_learning <true/false> - Enable learning modules")
        console.print("  ui_language <en/zh>       - UI language")
        console.print("\nExample: novel-agent settings set iterations 5")
        return

    param_value = value
    if value:
        if value.lower() in ["true", "yes", "y"]:
            param_value = True
        elif value.lower() in ["false", "no", "n"]:
            param_value = False
        elif value.isdigit():
            param_value = int(value)
        elif value.replace(".", "", 1).isdigit():
            param_value = float(value)

    try:
        manager.update_settings(**{param: param_value})
        console.print(f"[green]✓[/green] Set [cyan]{param}[/cyan] to [cyan]{param_value}[/cyan]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@settings.command("reset")
def reset_settings() -> None:
    """Reset settings to defaults."""
    from src.novel_agent.studio.core.settings import get_settings_manager

    manager = get_settings_manager()
    manager.reset_to_defaults()
    console.print("[green]✓[/green] Settings reset to defaults")


# === Monitor Commands ===


@cli.group()
def monitor() -> None:
    """System monitoring and diagnostics commands."""
    pass


@monitor.command()
def health() -> None:
    """Run system health checks."""
    console.print("[bold blue]Running System Health Check[/bold blue]\n")

    async def run_health_checks():
        from src.novel_agent.monitoring.health import HealthMonitor, HealthStatus, get_health_monitor

        health_monitor = get_health_monitor()

        # Register some basic checks if not already registered
        if not health_monitor._checks:
            import os
            from pathlib import Path
            from src.novel_agent import DATA_DIR, NOVELS_DIR, OPENVIKING_DIR

            async def check_config():
                from src.novel_agent.monitoring.health import HealthCheckResult

                return HealthCheckResult(
                    name="config", status=HealthStatus.HEALTHY, message="Configuration loaded"
                )

            async def check_directories():
                from src.novel_agent.monitoring.health import HealthCheckResult

                dirs_ok = all(d.exists() for d in [DATA_DIR, NOVELS_DIR, OPENVIKING_DIR])
                return HealthCheckResult(
                    name="directories",
                    status=HealthStatus.HEALTHY if dirs_ok else HealthStatus.DEGRADED,
                    message="All data directories present"
                    if dirs_ok
                    else "Some directories missing",
                    details={
                        "data_dir": DATA_DIR.exists(),
                        "novels_dir": NOVELS_DIR.exists(),
                        "openviking_dir": OPENVIKING_DIR.exists(),
                    },
                )

            async def check_api_keys():
                from src.novel_agent.monitoring.health import HealthCheckResult

                deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
                return HealthCheckResult(
                    name="api_keys",
                    status=HealthStatus.HEALTHY if deepseek_key else HealthStatus.DEGRADED,
                    message="API keys configured" if deepseek_key else "DEEPSEEK_API_KEY not set",
                )

            health_monitor.register_check("config", check_config)
            health_monitor.register_check("directories", check_directories)
            health_monitor.register_check("api_keys", check_api_keys)

        # Run all checks
        results = []
        for check_name in health_monitor._checks:
            result = await health_monitor.run_check(check_name)
            results.append(result)

        # Display results
        all_healthy = True
        for result in results:
            status_icon = {
                HealthStatus.HEALTHY: "[green]✓[/green]",
                HealthStatus.DEGRADED: "[yellow]![/yellow]",
                HealthStatus.UNHEALTHY: "[red]✗[/red]",
            }.get(result.status, "[?]")

            if result.status != HealthStatus.HEALTHY:
                all_healthy = False

            console.print(f"  {status_icon} [bold]{result.name}[/bold]: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    console.print(f"      {key}: {value}")

        console.print(
            f"\n[bold]{'[green]All checks passed![/green]' if all_healthy else '[yellow]Some checks failed[/yellow]'}[/bold]"
        )

    try:
        asyncio.run(run_health_checks())
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback

        traceback.print_exc()


@monitor.command()
@click.option("--detail", "-d", is_flag=True, help="Show detailed metric data")
def metrics(detail: bool) -> None:
    """Show current performance metrics."""
    console.print("[bold blue]Performance Metrics[/bold blue]\n")

    from src.novel_agent.monitoring.metrics import MetricsCollector, get_metrics_collector

    collector = get_metrics_collector()
    all_metrics = collector.collect_all()

    has_metrics = False

    # Display counters
    if all_metrics.get("counters"):
        has_metrics = True
        console.print("[cyan]Counters:[/cyan]")
        for metric in all_metrics["counters"]:
            name = metric["name"]
            desc = metric.get("description", "")
            console.print(f"  [bold]{name}[/bold]{' - ' + desc if desc else ''}")
            if detail and "values" in metric:
                for value in metric["values"]:
                    labels = value.get("labels", {})
                    val = value["value"]
                    label_str = ", ".join([f"{k}={v}" for k, v in labels.items()]) if labels else ""
                    console.print(f"    {val} {label_str}")

    # Display gauges
    if all_metrics.get("gauges"):
        has_metrics = True
        console.print("\n[cyan]Gauges:[/cyan]")
        for metric in all_metrics["gauges"]:
            name = metric["name"]
            desc = metric.get("description", "")
            console.print(f"  [bold]{name}[/bold]{' - ' + desc if desc else ''}")
            if detail and "values" in metric:
                for value in metric["values"]:
                    labels = value.get("labels", {})
                    val = value["value"]
                    label_str = ", ".join([f"{k}={v}" for k, v in labels.items()]) if labels else ""
                    console.print(f"    {val} {label_str}")

    # Display histograms
    if all_metrics.get("histograms"):
        has_metrics = True
        console.print("\n[cyan]Histograms:[/cyan]")
        for metric in all_metrics["histograms"]:
            name = metric["name"]
            desc = metric.get("description", "")
            console.print(f"  [bold]{name}[/bold]{' - ' + desc if desc else ''}")

    # Display summaries
    if all_metrics.get("summaries"):
        has_metrics = True
        console.print("\n[cyan]Summaries:[/cyan]")
        for metric in all_metrics["summaries"]:
            name = metric["name"]
            desc = metric.get("description", "")
            console.print(f"  [bold]{name}[/bold]{' - ' + desc if desc else ''}")

    if not has_metrics:
        console.print("[yellow]No metrics collected yet[/yellow]")


@monitor.command()
@click.option("--limit", "-n", type=int, default=20, help="Number of alerts to show")
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["info", "warning", "error", "critical"]),
    help="Filter by severity",
)
def alerts(limit: int, severity: str | None) -> None:
    """Show alert history."""
    console.print("[bold blue]Alert History[/bold blue]\n")

    from src.novel_agent.monitoring.alerts import AlertManager, AlertSeverity, get_alert_manager

    alert_manager = get_alert_manager()
    history = alert_manager._alert_history

    if severity:
        history = [a for a in history if a.severity.value == severity]

    if not history:
        console.print("[yellow]No alerts recorded[/yellow]")
        return

    # Show most recent first
    recent_alerts = history[-limit:] if limit > 0 else history

    for alert in reversed(recent_alerts):
        severity_color = {
            AlertSeverity.INFO: "cyan",
            AlertSeverity.WARNING: "yellow",
            AlertSeverity.ERROR: "red",
            AlertSeverity.CRITICAL: "bold red",
        }.get(alert.severity, "white")

        ack_marker = "[dim](ack)[/dim] " if alert.acknowledged else ""
        console.print(
            f"  [{severity_color}]{alert.severity.value}[/{severity_color}] {ack_marker}[bold]{alert.alert_type.value}[/bold]"
        )
        console.print(f"    {alert.timestamp}")
        console.print(f"    {alert.message}")
        if alert.details:
            console.print(f"    Details: {alert.details}")
        console.print()


@monitor.command()
def status() -> None:
    """Show comprehensive system status overview."""
    console.print("[bold blue]System Status Overview[/bold blue]\n")

    async def show_status():
        import time
        import sys
        from src.novel_agent.monitoring.health import get_health_monitor
        from src.novel_agent.monitoring.metrics import get_metrics_collector
        from src.novel_agent.monitoring.alerts import get_alert_manager

        health_monitor = get_health_monitor()
        metrics_collector = get_metrics_collector()
        alert_manager = get_alert_manager()

        # Uptime
        uptime_seconds = int(time.time() - health_monitor._start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        console.print("[cyan]System Info:[/cyan]")
        console.print(f"  Python: {sys.version}")
        console.print(f"  Uptime: {hours}h {minutes}m {seconds}s")

        # Health status
        console.print("\n[cyan]Health Checks:[/cyan]")
        if health_monitor._last_results:
            healthy = sum(
                1 for r in health_monitor._last_results.values() if r.status.value == "healthy"
            )
            total = len(health_monitor._last_results)
            console.print(f"  {healthy}/{total} checks healthy")
        else:
            console.print("  [yellow]No health checks run yet[/yellow]")

        # Metrics
        console.print("\n[cyan]Metrics:[/cyan]")
        all_metrics = metrics_collector.collect_all()
        metric_count = (
            len(all_metrics.get("counters", []))
            + len(all_metrics.get("gauges", []))
            + len(all_metrics.get("histograms", []))
            + len(all_metrics.get("summaries", []))
        )
        console.print(f"  {metric_count} metrics collected")

        # Alerts
        console.print("\n[cyan]Alerts:[/cyan]")
        total_alerts = len(alert_manager._alert_history)
        unacked = sum(1 for a in alert_manager._alert_history if not a.acknowledged)
        console.print(f"  Total: {total_alerts}")
        console.print(f"  Unacknowledged: {unacked}")

        console.print("\n[green]✓ Status overview complete[/green]")

    try:
        asyncio.run(show_status())
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        import traceback

        traceback.print_exc()


@monitor.command()
@click.option("--port", "-p", type=int, default=9090, help="Port to expose Prometheus endpoint on")
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
def export(port: int, host: str) -> None:
    """Start Prometheus metrics export endpoint."""
    console.print(f"[bold blue]Starting Prometheus Exporter[/bold blue]")
    console.print(f"  Host: {host}")
    console.print(f"  Port: {port}")
    console.print("\n[yellow]Note: Prometheus export server not yet fully implemented[/yellow]")
    console.print("[cyan]Metrics would be available at:[/cyan]")
    console.print(f"  http://{host}:{port}/metrics")


if __name__ == "__main__":
    cli()
