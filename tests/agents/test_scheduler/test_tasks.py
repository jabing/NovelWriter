# tests/test_scheduler/test_tasks.py
"""Tests for Task Scheduler."""

from datetime import datetime, timedelta

import pytest

from src.novel_agent.scheduler.tasks import (
    ScheduledTask,
    TaskScheduler,
    TaskStatus,
    comment_collection_handler,
    daily_chapter_generation_handler,
    daily_publishing_handler,
    setup_default_schedule,
)


class TestScheduledTask:
    """Tests for ScheduledTask dataclass."""

    def test_scheduled_task_creation(self) -> None:
        """Test creating a scheduled task."""
        async def handler() -> None:
            pass

        task = ScheduledTask(
            id="test_task",
            name="Test Task",
            handler=handler,
            interval_seconds=60,
        )

        assert task.id == "test_task"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.run_count == 0
        assert task.next_run is not None

    def test_scheduled_task_with_args(self) -> None:
        """Test creating a task with arguments."""
        async def handler(x: int, y: str = "default") -> None:
            pass

        task = ScheduledTask(
            id="test",
            name="Test",
            handler=handler,
            interval_seconds=30,
            args=(1,),
            kwargs={"y": "custom"},
        )

        assert task.args == (1,)
        assert task.kwargs == {"y": "custom"}


class TestTaskScheduler:
    """Tests for TaskScheduler."""

    @pytest.fixture
    def scheduler(self) -> TaskScheduler:
        """Create a fresh scheduler."""
        return TaskScheduler(name="TestScheduler")

    def test_scheduler_initialization(self, scheduler: TaskScheduler) -> None:
        """Test scheduler initializes correctly."""
        assert scheduler.name == "TestScheduler"
        assert scheduler._running is False
        assert len(scheduler._tasks) == 0

    def test_register_task(self, scheduler: TaskScheduler) -> None:
        """Test registering a task."""
        async def handler() -> None:
            pass

        task = scheduler.register_task(
            task_id="task1",
            name="Task One",
            handler=handler,
            interval_seconds=60,
        )

        assert len(scheduler._tasks) == 1
        assert scheduler.get_task("task1") == task

    def test_register_multiple_tasks(self, scheduler: TaskScheduler) -> None:
        """Test registering multiple tasks."""
        async def handler() -> None:
            pass

        scheduler.register_task("task1", "Task 1", handler, 60)
        scheduler.register_task("task2", "Task 2", handler, 120)
        scheduler.register_task("task3", "Task 3", handler, 180)

        assert len(scheduler._tasks) == 3

    def test_unregister_task(self, scheduler: TaskScheduler) -> None:
        """Test unregistering a task."""
        async def handler() -> None:
            pass

        scheduler.register_task("task1", "Task 1", handler, 60)

        result = scheduler.unregister_task("task1")

        assert result is True
        assert len(scheduler._tasks) == 0

    def test_unregister_nonexistent_task(self, scheduler: TaskScheduler) -> None:
        """Test unregistering a task that doesn't exist."""
        result = scheduler.unregister_task("nonexistent")
        assert result is False

    def test_get_task(self, scheduler: TaskScheduler) -> None:
        """Test getting a task by ID."""
        async def handler() -> None:
            pass

        registered = scheduler.register_task("task1", "Task 1", handler, 60)
        retrieved = scheduler.get_task("task1")

        assert retrieved == registered

    def test_get_nonexistent_task(self, scheduler: TaskScheduler) -> None:
        """Test getting a task that doesn't exist."""
        result = scheduler.get_task("nonexistent")
        assert result is None

    def test_get_all_tasks(self, scheduler: TaskScheduler) -> None:
        """Test getting all tasks."""
        async def handler() -> None:
            pass

        scheduler.register_task("task1", "Task 1", handler, 60)
        scheduler.register_task("task2", "Task 2", handler, 120)

        all_tasks = scheduler.get_all_tasks()

        assert len(all_tasks) == 2

    def test_get_status(self, scheduler: TaskScheduler) -> None:
        """Test getting scheduler status."""
        async def handler() -> None:
            pass

        scheduler.register_task("task1", "Task 1", handler, 60)

        status = scheduler.get_status()

        assert status["name"] == "TestScheduler"
        assert status["running"] is False
        assert status["task_count"] == 1
        assert "task1" in status["tasks"]


class TestTaskSchedulerExecution:
    """Tests for task execution."""

    @pytest.fixture
    def scheduler(self) -> TaskScheduler:
        """Create a fresh scheduler."""
        return TaskScheduler(name="TestScheduler")

    @pytest.mark.asyncio
    async def test_run_task_now(self, scheduler: TaskScheduler) -> None:
        """Test running a task immediately."""
        executed = []

        async def handler(value: str) -> None:
            executed.append(value)

        scheduler.register_task(
            "task1",
            "Task 1",
            handler,
            60,
            args=("executed",),
        )

        result = await scheduler.run_task_now("task1")

        assert result is True
        assert "executed" in executed

    @pytest.mark.asyncio
    async def test_run_nonexistent_task(self, scheduler: TaskScheduler) -> None:
        """Test running a task that doesn't exist."""
        result = await scheduler.run_task_now("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_task_updates_status_on_success(self, scheduler: TaskScheduler) -> None:
        """Test that task status is updated on success."""
        async def handler() -> None:
            pass

        scheduler.register_task("task1", "Task 1", handler, 60)
        await scheduler.run_task_now("task1")

        task = scheduler.get_task("task1")
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.run_count == 1

    @pytest.mark.asyncio
    async def test_task_updates_status_on_failure(self, scheduler: TaskScheduler) -> None:
        """Test that task status is updated on failure."""
        async def failing_handler() -> None:
            raise ValueError("Test error")

        scheduler.register_task("task1", "Task 1", failing_handler, 60)
        await scheduler.run_task_now("task1")

        task = scheduler.get_task("task1")
        assert task is not None
        assert task.status == TaskStatus.FAILED
        assert "Test error" in task.error_message

    @pytest.mark.asyncio
    async def test_task_updates_next_run(self, scheduler: TaskScheduler) -> None:
        """Test that next_run is updated after execution."""
        async def handler() -> None:
            pass

        scheduler.register_task("task1", "Task 1", handler, 60)
        task = scheduler.get_task("task1")
        original_next_run = task.next_run if task else None

        await scheduler.run_task_now("task1")

        task = scheduler.get_task("task1")
        assert task is not None
        assert task.next_run != original_next_run
        assert task.last_run is not None

    @pytest.mark.asyncio
    async def test_start_and_stop_scheduler(self, scheduler: TaskScheduler) -> None:
        """Test starting and stopping the scheduler."""
        async def handler() -> None:
            pass

        scheduler.register_task("task1", "Task 1", handler, 1)

        await scheduler.start()
        assert scheduler._running is True

        await scheduler.stop()
        assert scheduler._running is False


class TestTaskHandlers:
    """Tests for predefined task handlers."""

    @pytest.mark.asyncio
    async def test_daily_chapter_generation_handler(self) -> None:
        """Test daily chapter generation handler."""
        result = await daily_chapter_generation_handler("test_novel")

        assert result["status"] == "completed"
        assert result["novel_id"] == "test_novel"
        assert result["chapter_generated"] is True

    @pytest.mark.asyncio
    async def test_daily_publishing_handler(self) -> None:
        """Test daily publishing handler."""
        result = await daily_publishing_handler(
            "test_novel",
            ["wattpad", "royalroad"]
        )

        assert result["status"] == "completed"
        assert result["novel_id"] == "test_novel"
        assert "wattpad" in result["platforms"]
        assert result["published"] is True

    @pytest.mark.asyncio
    async def test_comment_collection_handler(self) -> None:
        """Test comment collection handler."""
        result = await comment_collection_handler("test_novel")

        assert result["status"] == "completed"
        assert result["novel_id"] == "test_novel"
        assert result["comments_collected"] is True


class TestSetupDefaultSchedule:
    """Tests for default schedule setup."""

    def test_setup_default_schedule(self) -> None:
        """Test setting up default schedule."""
        scheduler = TaskScheduler(name="TestScheduler")
        result = setup_default_schedule(scheduler)

        assert result == scheduler
        assert len(scheduler._tasks) == 3

        task_ids = [t.id for t in scheduler.get_all_tasks()]
        assert "daily_chapter_generation" in task_ids
        assert "daily_publishing" in task_ids
        assert "hourly_comment_collection" in task_ids

    def test_setup_default_schedule_uses_default(self) -> None:
        """Test that setup uses default scheduler if none provided."""
        from src.novel_agent.scheduler.tasks import default_scheduler

        # Clear any existing tasks
        default_scheduler._tasks.clear()

        result = setup_default_schedule()

        assert result == default_scheduler
        assert len(default_scheduler._tasks) == 3


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_task_status_values(self) -> None:
        """Test task status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestScheduledTaskTiming:
    """Tests for scheduled task timing."""

    def test_task_schedules_next_run(self) -> None:
        """Test that task schedules next run correctly."""
        async def handler() -> None:
            pass

        task = ScheduledTask(
            id="test",
            name="Test",
            handler=handler,
            interval_seconds=3600,  # 1 hour
        )

        assert task.next_run is not None
        expected = datetime.now() + timedelta(seconds=3600)
        # Allow 1 second tolerance
        diff = abs((task.next_run - expected).total_seconds())
        assert diff < 1

    def test_task_start_immediately(self) -> None:
        """Test task can be set to start immediately."""
        async def handler() -> None:
            pass

        scheduler = TaskScheduler()
        task = scheduler.register_task(
            "immediate",
            "Immediate",
            handler,
            60,
            start_immediately=True,
        )

        # next_run should be very close to now
        assert task.next_run is not None
        diff = abs((task.next_run - datetime.now()).total_seconds())
        assert diff < 1
