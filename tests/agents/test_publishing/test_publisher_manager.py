# tests/test_publishing/test_publisher_manager.py
"""Tests for the PublisherManager and publishing components."""

import pytest

from src.novel_agent.publishing.base import (
    ChapterInfo,
    PublishResult,
    PublishStatus,
    StoryInfo,
)
from src.novel_agent.publishing.publisher_manager import Platform, PublisherManager


class TestStoryInfo:
    """Tests for StoryInfo dataclass."""

    def test_story_info_creation(self) -> None:
        """Test creating a StoryInfo instance."""
        story = StoryInfo(
            title="Test Story",
            description="A test story",
            genre="fantasy",
            tags=["magic", "adventure"],
        )

        assert story.title == "Test Story"
        assert story.description == "A test story"
        assert story.genre == "fantasy"
        assert story.tags == ["magic", "adventure"]
        assert story.language == "en"
        assert story.rating == "teen"

    def test_story_info_defaults(self) -> None:
        """Test StoryInfo default values."""
        story = StoryInfo(
            title="Minimal Story",
            description="Minimal",
            genre="scifi",
        )

        assert story.tags == []
        assert story.language == "en"
        assert story.rating == "teen"
        assert story.cover_image is None
        assert story.platform_id is None


class TestChapterInfo:
    """Tests for ChapterInfo dataclass."""

    def test_chapter_info_creation(self) -> None:
        """Test creating a ChapterInfo instance."""
        chapter = ChapterInfo(
            title="Chapter 1",
            content="Once upon a time...",
            chapter_number=1,
        )

        assert chapter.title == "Chapter 1"
        assert chapter.content == "Once upon a time..."
        assert chapter.chapter_number == 1
        assert chapter.word_count > 0

    def test_chapter_word_count(self) -> None:
        """Test automatic word count calculation."""
        chapter = ChapterInfo(
            title="Test",
            content="One two three four five",
            chapter_number=1,
        )

        assert chapter.word_count == 5

    def test_chapter_explicit_word_count(self) -> None:
        """Test explicit word count overrides auto-calculation."""
        chapter = ChapterInfo(
            title="Test",
            content="One two three",
            chapter_number=1,
            word_count=100,
        )

        assert chapter.word_count == 100


class TestPublishResult:
    """Tests for PublishResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = PublishResult(
            success=True,
            status=PublishStatus.SUCCESS,
            message="Published successfully",
            platform="wattpad",
            story_id="12345",
            url="https://wattpad.com/story/12345",
        )

        assert result.success is True
        assert result.status == PublishStatus.SUCCESS
        assert result.story_id == "12345"
        assert result.errors == []

    def test_failure_result(self) -> None:
        """Test creating a failed result."""
        result = PublishResult(
            success=False,
            status=PublishStatus.FAILED,
            message="Login failed",
            platform="royalroad",
            errors=["Invalid credentials"],
        )

        assert result.success is False
        assert result.status == PublishStatus.FAILED
        assert "Invalid credentials" in result.errors


class TestPlatform:
    """Tests for Platform enum."""

    def test_platform_values(self) -> None:
        """Test platform enum values."""
        assert Platform.WATTPAD.value == "wattpad"
        assert Platform.ROYALROAD.value == "royalroad"


class TestPublisherManager:
    """Tests for PublisherManager class."""

    def test_manager_initialization(self, tmp_path) -> None:
        """Test PublisherManager initialization."""
        manager = PublisherManager(
            credentials_dir=tmp_path / "creds",
            jobs_dir=tmp_path / "jobs",
            headless=True,
        )

        assert manager.headless is True
        assert manager._publishers == {}
        assert manager._credentials == {}

    def test_manager_creates_directories(self, tmp_path) -> None:
        """Test that manager creates necessary directories."""
        creds_dir = tmp_path / "credentials"
        jobs_dir = tmp_path / "jobs"

        PublisherManager(
            credentials_dir=creds_dir,
            jobs_dir=jobs_dir,
        )

        assert creds_dir.exists()
        assert jobs_dir.exists()

    @pytest.mark.asyncio
    async def test_create_job(self, tmp_path) -> None:
        """Test creating a publish job."""
        manager = PublisherManager(jobs_dir=tmp_path / "jobs")

        story = StoryInfo(
            title="Test Novel",
            description="A test novel",
            genre="fantasy",
        )

        chapters = [
            ChapterInfo(title="Ch 1", content="Content 1", chapter_number=1),
            ChapterInfo(title="Ch 2", content="Content 2", chapter_number=2),
        ]

        job = manager.create_job(
            story=story,
            chapters=chapters,
            platforms=[Platform.WATTPAD],
        )

        assert job.job_id.startswith("job_")
        assert job.story.title == "Test Novel"
        assert len(job.chapters) == 2
        assert Platform.WATTPAD in job.platforms
        assert job.status == PublishStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_job_status(self, tmp_path) -> None:
        """Test getting job status."""
        manager = PublisherManager(jobs_dir=tmp_path / "jobs")

        story = StoryInfo(
            title="Status Test",
            description="Testing status",
            genre="scifi",
        )

        chapters = [
            ChapterInfo(title="Ch 1", content="Content", chapter_number=1),
        ]

        job = manager.create_job(
            story=story,
            chapters=chapters,
            platforms=[Platform.ROYALROAD],
        )

        status = manager.get_job_status(job.job_id)

        assert status is not None
        assert status["job_id"] == job.job_id
        assert status["status"] == "pending"
        assert status["story_title"] == "Status Test"

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, tmp_path) -> None:
        """Test getting status of nonexistent job."""
        manager = PublisherManager(jobs_dir=tmp_path / "jobs")

        status = manager.get_job_status("nonexistent_job")

        assert status is None

    @pytest.mark.asyncio
    async def test_login_without_credentials(self, tmp_path) -> None:
        """Test login without credentials returns error."""
        manager = PublisherManager(jobs_dir=tmp_path / "jobs")

        result = await manager.login_platform(Platform.WATTPAD)

        assert result.success is False
        assert "credentials" in result.message.lower()

    @pytest.mark.asyncio
    async def test_context_manager(self, tmp_path) -> None:
        """Test async context manager usage."""
        async with PublisherManager(jobs_dir=tmp_path / "jobs") as manager:
            assert manager is not None
            # Should be able to use manager here

        # After context exit, publishers should be cleared
        assert manager._publishers == {}


class TestPublishStatus:
    """Tests for PublishStatus enum."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert PublishStatus.PENDING.value == "pending"
        assert PublishStatus.IN_PROGRESS.value == "in_progress"
        assert PublishStatus.SUCCESS.value == "success"
        assert PublishStatus.FAILED.value == "failed"
        assert PublishStatus.PARTIAL.value == "partial"
