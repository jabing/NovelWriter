# src/studio/core/state.py
"""State management for Writer Studio."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ProjectStatus(str, Enum):
    """Status of a writing project."""
    PLANNING = "planning"
    WRITING = "writing"
    PAUSED = "paused"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class NovelProject:
    """A novel writing project."""
    id: str
    title: str
    genre: str
    language: str = "en"
    status: ProjectStatus = ProjectStatus.PLANNING
    user_id: str | None = None

    # Story settings (for outline/character generation)
    premise: str = ""  # Story premise/核心设定
    themes: list[str] = field(default_factory=list)  # 故事主题
    pov: str = "first"  # first/third
    tone: str = "balanced"  # light/dark/balanced
    target_audience: str = "young_adult"  # young_adult/adult/new_adult
    story_structure: str = "three_act"  # three_act/heros_journey/save_the_cat

    # Content constraints
    content_rating: str = "teen"  # teen/mature/explicit
    sensitive_handling: str = "metaphor"  # direct/metaphor/implied

    # Progress
    target_chapters: int = 100
    completed_chapters: int = 0
    total_words: int = 0
    target_words: int = 300000

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Publishing
    platforms: list[str] = field(default_factory=list)
    published_chapters: int = 0

    # Analytics
    total_reads: int = 0
    total_votes: int = 0
    total_comments: int = 0
    followers: int = 0

    @property
    def progress_percent(self) -> float:
        """Calculate writing progress percentage."""
        if self.target_chapters == 0:
            return 0.0
        return (self.completed_chapters / self.target_chapters) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "language": self.language,
            "status": self.status.value,
            "user_id": self.user_id,
            "premise": self.premise,
            "themes": self.themes,
            "pov": self.pov,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "story_structure": self.story_structure,
            "content_rating": self.content_rating,
            "sensitive_handling": self.sensitive_handling,
            "target_chapters": self.target_chapters,
            "completed_chapters": self.completed_chapters,
            "total_words": self.total_words,
            "target_words": self.target_words,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "platforms": self.platforms,
            "published_chapters": self.published_chapters,
            "total_reads": self.total_reads,
            "total_votes": self.total_votes,
            "total_comments": self.total_comments,
            "followers": self.followers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NovelProject":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            genre=data["genre"],
            language=data.get("language", "en"),
            status=ProjectStatus(data.get("status", "planning")),
            user_id=data.get("user_id"),
            premise=data.get("premise", ""),
            themes=data.get("themes", []),
            pov=data.get("pov", "first"),
            tone=data.get("tone", "balanced"),
            target_audience=data.get("target_audience", "young_adult"),
            story_structure=data.get("story_structure", "three_act"),
            content_rating=data.get("content_rating", "teen"),
            sensitive_handling=data.get("sensitive_handling", "metaphor"),
            target_chapters=data.get("target_chapters", 100),
            completed_chapters=data.get("completed_chapters", 0),
            total_words=data.get("total_words", 0),
            target_words=data.get("target_words", 300000),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            platforms=data.get("platforms", []),
            published_chapters=data.get("published_chapters", 0),
            total_reads=data.get("total_reads", 0),
            total_votes=data.get("total_votes", 0),
            total_comments=data.get("total_comments", 0),
            followers=data.get("followers", 0),
        )


@dataclass
class Task:
    """A writing or publishing task."""
    id: str
    title: str
    task_type: str  # "write", "review", "publish", "research"
    status: TaskStatus = TaskStatus.PENDING
    novel_id: str | None = None
    chapter_number: int | None = None
    scheduled_time: str | None = None
    completed_time: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "task_type": self.task_type,
            "status": self.status.value,
            "novel_id": self.novel_id,
            "chapter_number": self.chapter_number,
            "scheduled_time": self.scheduled_time,
            "completed_time": self.completed_time,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            task_type=data["task_type"],
            status=TaskStatus(data.get("status", "pending")),
            novel_id=data.get("novel_id"),
            chapter_number=data.get("chapter_number"),
            scheduled_time=data.get("scheduled_time"),
            completed_time=data.get("completed_time"),
            details=data.get("details", {}),
        )


@dataclass
class Notification:
    """A notification for the user."""
    id: str
    message: str
    notification_type: str  # "comment", "vote", "follow", "system"
    novel_id: str | None = None
    read: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class StudioState:
    """Central state management for Writer Studio."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize state.

        Args:
            data_dir: Directory to store state data
        """
        self.data_dir = data_dir or Path("data/studio")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._projects: dict[str, NovelProject] = {}
        self._tasks: dict[str, Task] = {}
        self._notifications: list[Notification] = []
        self._current_project_id: str | None = None

        self._load_state()

    def _state_file(self) -> Path:
        """Get state file path."""
        return self.data_dir / "state.json"

    def _load_state(self) -> None:
        """Load state from disk."""
        state_file = self._state_file()
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)

                for project_data in data.get("projects", []):
                    project = NovelProject.from_dict(project_data)
                    self._projects[project.id] = project

                for task_data in data.get("tasks", []):
                    task = Task.from_dict(task_data)
                    self._tasks[task.id] = task

                for notif_data in data.get("notifications", []):
                    self._notifications.append(Notification(
                        id=notif_data["id"],
                        message=notif_data["message"],
                        notification_type=notif_data["notification_type"],
                        novel_id=notif_data.get("novel_id"),
                        read=notif_data.get("read", False),
                        created_at=notif_data.get("created_at", datetime.now().isoformat()),
                    ))

                self._current_project_id = data.get("current_project_id")

            except Exception:
                pass  # Start fresh if loading fails

    def _save_state(self) -> None:
        """Save state to disk."""
        state_file = self._state_file()
        data = {
            "projects": [p.to_dict() for p in self._projects.values()],
            "tasks": [t.to_dict() for t in self._tasks.values()],
            "notifications": [
                {
                    "id": n.id,
                    "message": n.message,
                    "notification_type": n.notification_type,
                    "novel_id": n.novel_id,
                    "read": n.read,
                    "created_at": n.created_at,
                }
                for n in self._notifications
            ],
            "current_project_id": self._current_project_id,
        }

        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    # Projects
    def get_projects(self) -> list[NovelProject]:
        """Get all projects."""
        return list(self._projects.values())

    def get_project(self, project_id: str) -> NovelProject | None:
        """Get a project by ID."""
        return self._projects.get(project_id)

    def add_project(self, project: NovelProject) -> None:
        """Add a new project."""
        self._projects[project.id] = project
        self._save_state()

    def update_project(self, project: NovelProject) -> None:
        """Update a project."""
        project.updated_at = datetime.now().isoformat()
        self._projects[project.id] = project
        self._save_state()

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self._projects:
            del self._projects[project_id]
            self._save_state()
            return True
        return False

    def set_current_project(self, project_id: str | None) -> None:
        """Set the current project."""
        self._current_project_id = project_id
        self._save_state()

    def get_current_project(self) -> NovelProject | None:
        """Get the current project. If none set, return first available."""
        if self._current_project_id:
            return self._projects.get(self._current_project_id)

        # If no current project set, auto-select first project
        if self._projects:
            first_id = next(iter(self._projects.keys()))
            self._current_project_id = first_id
            self._save_state()
            return self._projects[first_id]

        return None

    # Tasks
    def get_tasks(self, novel_id: str | None = None) -> list[Task]:
        """Get tasks, optionally filtered by novel."""
        tasks = list(self._tasks.values())
        if novel_id:
            tasks = [t for t in tasks if t.novel_id == novel_id]
        return sorted(tasks, key=lambda t: t.scheduled_time or "")

    def get_pending_tasks(self) -> list[Task]:
        """Get pending tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]

    def get_today_tasks(self) -> list[Task]:
        """Get tasks scheduled for today."""
        today = datetime.now().date().isoformat()
        return [
            t for t in self._tasks.values()
            if t.scheduled_time and t.scheduled_time.startswith(today)
        ]

    def add_task(self, task: Task) -> None:
        """Add a new task."""
        self._tasks[task.id] = task
        self._save_state()

    def update_task(self, task: Task) -> None:
        """Update a task."""
        self._tasks[task.id] = task
        self._save_state()

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.COMPLETED
            self._tasks[task_id].completed_time = datetime.now().isoformat()
            self._save_state()
            return True
        return False

    # Notifications
    def get_notifications(self, unread_only: bool = False) -> list[Notification]:
        """Get notifications."""
        notifications = self._notifications
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        return sorted(notifications, key=lambda n: n.created_at, reverse=True)

    def add_notification(self, notification: Notification) -> None:
        """Add a notification."""
        self._notifications.insert(0, notification)
        # Keep only last 100 notifications
        if len(self._notifications) > 100:
            self._notifications = self._notifications[:100]
        self._save_state()

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        for n in self._notifications:
            if n.id == notification_id:
                n.read = True
                self._save_state()
                return True
        return False

    # Statistics
    def get_total_stats(self) -> dict[str, Any]:
        """Get total statistics across all projects."""
        return {
            "total_words": sum(p.total_words for p in self._projects.values()),
            "total_chapters": sum(p.completed_chapters for p in self._projects.values()),
            "total_projects": len(self._projects),
            "active_projects": len([p for p in self._projects.values() if p.status == ProjectStatus.WRITING]),
            "total_reads": sum(p.total_reads for p in self._projects.values()),
            "total_followers": sum(p.followers for p in self._projects.values()),
            "pending_tasks": len(self.get_pending_tasks()),
            "unread_notifications": len(self.get_notifications(unread_only=True)),
        }

    # Settings
    def get_settings(self) -> "StudioSettings":
        """Get current studio settings.

        Returns:
            Current StudioSettings instance
        """
        from src.novel_agent.studio.core.settings import get_settings_manager
        return get_settings_manager().get_settings()

    def update_settings(self, **kwargs: Any) -> "StudioSettings":
        """Update studio settings.

        Args:
            **kwargs: Settings to update

        Returns:
            Updated StudioSettings instance
        """
        from src.novel_agent.studio.core.settings import get_settings_manager
        return get_settings_manager().update_settings(**kwargs)

    def apply_settings_preset(self, mode: str) -> str:
        """Apply a preset settings mode.

        Args:
            mode: Preset mode name (fast/balanced/high/ultra)

        Returns:
            Description of the applied mode
        """
        from src.novel_agent.studio.core.settings import get_settings_manager
        return get_settings_manager().apply_preset(mode)


# Global state instance
_studio_state: StudioState | None = None


def get_studio_state() -> StudioState:
    """Get the global studio state."""
    global _studio_state
    if _studio_state is None:
        _studio_state = StudioState()
    return _studio_state
