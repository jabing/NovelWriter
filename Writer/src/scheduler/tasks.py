# src/scheduler/tasks.py
"""Task scheduling for daily operations.

Provides both Celery-based (for production) and simple asyncio-based (for MVP)
scheduling capabilities.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Status of a scheduled task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """A scheduled task with timing and execution info."""
    id: str
    name: str
    handler: Callable[..., Coroutine[Any, Any, Any]]
    interval_seconds: float
    last_run: datetime | None = None
    next_run: datetime | None = None
    status: TaskStatus = TaskStatus.PENDING
    error_message: str | None = None
    run_count: int = 0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.next_run is None:
            self.next_run = datetime.now() + timedelta(seconds=self.interval_seconds)


class TaskScheduler:
    """Simple task scheduler for MVP.

    For production use, consider using Celery with Redis.
    This implementation provides a lightweight alternative for
    development and testing.
    """

    def __init__(self, name: str = "NovelAgentScheduler") -> None:
        """Initialize the task scheduler.

        Args:
            name: Scheduler name for logging
        """
        self.name = name
        self._tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    def register_task(
        self,
        task_id: str,
        name: str,
        handler: Callable[..., Coroutine[Any, Any, Any]],
        interval_seconds: float,
        args: tuple = (),
        kwargs: dict | None = None,
        start_immediately: bool = False,
    ) -> ScheduledTask:
        """Register a new scheduled task.

        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            handler: Async function to execute
            interval_seconds: Time between runs
            args: Positional arguments for handler
            kwargs: Keyword arguments for handler
            start_immediately: If True, run immediately instead of waiting

        Returns:
            The registered task
        """
        if kwargs is None:
            kwargs = {}

        task = ScheduledTask(
            id=task_id,
            name=name,
            handler=handler,
            interval_seconds=interval_seconds,
            args=args,
            kwargs=kwargs,
        )

        if start_immediately:
            task.next_run = datetime.now()

        self._tasks[task_id] = task
        logger.info(f"Registered task: {name} (id={task_id}, interval={interval_seconds}s)")

        return task

    def unregister_task(self, task_id: str) -> bool:
        """Unregister a task.

        Args:
            task_id: Task identifier to remove

        Returns:
            True if task was removed
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.info(f"Unregistered task: {task_id}")
            return True
        return False

    def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task or None if not found
        """
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[ScheduledTask]:
        """Get all registered tasks.

        Returns:
            List of all tasks
        """
        return list(self._tasks.values())

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Scheduler '{self.name}' started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info(f"Scheduler '{self.name}' stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_run_tasks()
                await asyncio.sleep(1)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _check_and_run_tasks(self) -> None:
        """Check for tasks that need to run and execute them."""
        now = datetime.now()

        for task in self._tasks.values():
            if task.status == TaskStatus.RUNNING:
                continue

            if task.next_run and task.next_run <= now:
                asyncio.create_task(self._execute_task(task))

    async def _execute_task(self, task: ScheduledTask) -> None:
        """Execute a single task.

        Args:
            task: Task to execute
        """
        task.status = TaskStatus.RUNNING
        logger.info(f"Executing task: {task.name}")

        try:
            await task.handler(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
            task.error_message = None
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            logger.error(f"Task {task.name} failed: {e}")
        finally:
            task.last_run = datetime.now()
            task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)
            task.run_count += 1

    async def run_task_now(self, task_id: str) -> bool:
        """Run a specific task immediately.

        Args:
            task_id: Task to run

        Returns:
            True if task was found and executed
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        await self._execute_task(task)
        return True

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status.

        Returns:
            Status information
        """
        return {
            "name": self.name,
            "running": self._running,
            "task_count": len(self._tasks),
            "tasks": {
                task_id: {
                    "name": task.name,
                    "status": task.status.value,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "run_count": task.run_count,
                    "error": task.error_message,
                }
                for task_id, task in self._tasks.items()
            },
        }


# Default scheduler instance
default_scheduler = TaskScheduler()


# Pre-defined task handlers

async def daily_chapter_generation_handler(novel_id: str, **kwargs: Any) -> dict[str, Any]:
    """Handler for daily chapter generation.

    Args:
        novel_id: Novel to generate chapter for
        **kwargs: Additional arguments

    Returns:
        Generation result
    """
    logger.info(f"Generating daily chapter for novel: {novel_id}")

    # Import here to avoid circular imports
    from src.agents.orchestrator import AgentOrchestrator

    AgentOrchestrator()
    # In real implementation, would configure and run the workflow
    # result = await orchestrator.run_workflow("chapter_generation", {"novel_id": novel_id})

    return {
        "status": "completed",
        "novel_id": novel_id,
        "chapter_generated": True,
        "timestamp": datetime.now().isoformat(),
    }


async def daily_publishing_handler(novel_id: str, platforms: list[str], **kwargs: Any) -> dict[str, Any]:
    """Handler for daily publishing.

    Args:
        novel_id: Novel to publish
        platforms: Platforms to publish to
        **kwargs: Additional arguments

    Returns:
        Publishing result
    """
    logger.info(f"Publishing chapter for novel: {novel_id} to {platforms}")

    return {
        "status": "completed",
        "novel_id": novel_id,
        "platforms": platforms,
        "published": True,
        "timestamp": datetime.now().isoformat(),
    }


async def comment_collection_handler(novel_id: str, **kwargs: Any) -> dict[str, Any]:
    """Handler for comment collection and analysis.

    Args:
        novel_id: Novel to collect comments for
        **kwargs: Additional arguments

    Returns:
        Collection result
    """
    logger.info(f"Collecting comments for novel: {novel_id}")

    return {
        "status": "completed",
        "novel_id": novel_id,
        "comments_collected": True,
        "timestamp": datetime.now().isoformat(),
    }


def setup_default_schedule(scheduler: TaskScheduler | None = None) -> TaskScheduler:
    """Set up the default daily schedule.

    Args:
        scheduler: Scheduler to configure (uses default if None)

    Returns:
        Configured scheduler
    """
    if scheduler is None:
        scheduler = default_scheduler

    # Daily chapter generation (every 24 hours)
    scheduler.register_task(
        task_id="daily_chapter_generation",
        name="Daily Chapter Generation",
        handler=daily_chapter_generation_handler,
        interval_seconds=86400,  # 24 hours
        args=("default_novel",),
    )

    # Daily publishing (every 24 hours, offset by 1 hour from generation)
    scheduler.register_task(
        task_id="daily_publishing",
        name="Daily Publishing",
        handler=daily_publishing_handler,
        interval_seconds=86400,  # 24 hours
        args=("default_novel", ["wattpad", "royalroad"]),
    )

    # Hourly comment collection
    scheduler.register_task(
        task_id="hourly_comment_collection",
        name="Hourly Comment Collection",
        handler=comment_collection_handler,
        interval_seconds=3600,  # 1 hour
        args=("default_novel",),
    )

    return scheduler


# Celery configuration (for production use)
try:
    from celery import Celery

    celery_app = Celery("novel_agent")
    celery_app.config_from_object({
        "broker_url": "redis://localhost:6379/0",
        "result_backend": "redis://localhost:6379/0",
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
    })

    @celery_app.task(name="generate_daily_chapter")
    def generate_daily_chapter(novel_id: str) -> dict:
        """Celery task for daily chapter generation."""
        import asyncio
        return asyncio.run(daily_chapter_generation_handler(novel_id))

    @celery_app.task(name="publish_chapter")
    def publish_chapter(novel_id: str, chapter_number: int, platform: str) -> dict:
        """Celery task for chapter publishing."""
        import asyncio
        return asyncio.run(daily_publishing_handler(novel_id, [platform]))

    @celery_app.task(name="collect_comments")
    def collect_comments(novel_id: str) -> dict:
        """Celery task for comment collection."""
        import asyncio
        return asyncio.run(comment_collection_handler(novel_id))

    CELERY_AVAILABLE = True

except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None  # type: ignore
    generate_daily_chapter = None  # type: ignore
    publish_chapter = None  # type: ignore
    collect_comments = None  # type: ignore
