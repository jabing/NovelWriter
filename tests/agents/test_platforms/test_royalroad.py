# tests/test_platforms/test_royalroad.py
"""Tests for Royal Road Platform."""

import pytest

from src.novel_agent.platforms.base import PublishStatus
from src.novel_agent.platforms.royalroad import RoyalRoadPlatform


class TestRoyalRoadPlatform:
    """Tests for RoyalRoadPlatform."""

    @pytest.fixture
    def platform(self) -> RoyalRoadPlatform:
        """Create Royal Road platform in simulation mode."""
        return RoyalRoadPlatform(
            username="test_user",
            password="test_pass",
            simulate=True
        )

    def test_platform_name(self, platform: RoyalRoadPlatform) -> None:
        """Test platform name is set correctly."""
        assert platform.PLATFORM_NAME == "royalroad"

    def test_simulate_mode_enabled(self, platform: RoyalRoadPlatform) -> None:
        """Test simulation mode is enabled."""
        assert platform._simulate is True

    @pytest.mark.asyncio
    async def test_authenticate_with_credentials(self, platform: RoyalRoadPlatform) -> None:
        """Test authentication with credentials."""
        result = await platform.authenticate()
        assert result is True
        assert platform._authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_without_credentials(self) -> None:
        """Test authentication fails without credentials."""
        platform = RoyalRoadPlatform(simulate=True)
        result = await platform.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_create_fiction(self, platform: RoyalRoadPlatform) -> None:
        """Test creating a fiction."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="A test fiction description",
            tags=["fantasy", "action"],
        )

        assert fiction_id is not None
        assert fiction_id.startswith("rr_fiction_")

    @pytest.mark.asyncio
    async def test_create_fiction_not_authenticated(self, platform: RoyalRoadPlatform) -> None:
        """Test creating fiction without authentication fails."""
        with pytest.raises(RuntimeError, match="Not authenticated"):
            await platform.create_story(
                title="Test Fiction",
                description="Test",
                tags=[],
            )

    @pytest.mark.asyncio
    async def test_publish_chapter(self, platform: RoyalRoadPlatform) -> None:
        """Test publishing a chapter."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=fiction_id,
            chapter_number=1,
            title="Chapter One",
            content="This is the chapter content.",
        )

        assert result.success is True
        assert result.status == PublishStatus.PUBLISHED
        assert result.chapter_id is not None

    @pytest.mark.asyncio
    async def test_publish_scheduled_chapter(self, platform: RoyalRoadPlatform) -> None:
        """Test publishing a scheduled chapter."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=fiction_id,
            chapter_number=1,
            title="Chapter One",
            content="Content",
            schedule_date="2024-12-25T10:00:00Z",
        )

        assert result.success is True
        assert result.status == PublishStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_publish_draft_chapter(self, platform: RoyalRoadPlatform) -> None:
        """Test publishing a chapter as draft."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=fiction_id,
            chapter_number=1,
            title="Chapter One",
            content="Content",
            draft=True,
        )

        assert result.success is True
        assert result.status == PublishStatus.DRAFT

    @pytest.mark.asyncio
    async def test_publish_chapter_invalid_fiction(self, platform: RoyalRoadPlatform) -> None:
        """Test publishing to invalid fiction fails."""
        await platform.authenticate()

        result = await platform.publish_chapter(
            story_id="invalid_fiction_id",
            chapter_number=1,
            title="Chapter",
            content="Content",
        )

        assert result.success is False
        assert result.status == PublishStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_comments(self, platform: RoyalRoadPlatform) -> None:
        """Test getting comments."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="Test",
            tags=[],
        )

        await platform.publish_chapter(
            story_id=fiction_id,
            chapter_number=1,
            title="Chapter",
            content="Content",
        )

        comments = await platform.get_comments(fiction_id, limit=10)
        assert isinstance(comments, list)

    @pytest.mark.asyncio
    async def test_reply_to_comment(self, platform: RoyalRoadPlatform) -> None:
        """Test replying to a comment."""
        await platform.authenticate()

        result = await platform.reply_to_comment(
            story_id="test_fiction",
            comment_id="test_comment",
            reply_text="Thank you!",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_fiction_info(self, platform: RoyalRoadPlatform) -> None:
        """Test getting fiction info."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="Test description",
            tags=["fantasy"],
        )

        info = await platform.get_fiction_info(fiction_id)

        assert info is not None
        assert info["title"] == "Test Fiction"
        assert info["description"] == "Test description"

    @pytest.mark.asyncio
    async def test_update_chapter(self, platform: RoyalRoadPlatform) -> None:
        """Test updating a chapter."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=fiction_id,
            chapter_number=1,
            title="Original Title",
            content="Original content.",
        )

        update_result = await platform.update_chapter(
            story_id=fiction_id,
            chapter_id=result.chapter_id,
            content="Updated content.",
            title="Updated Title",
        )

        assert update_result.success is True

    @pytest.mark.asyncio
    async def test_get_statistics(self, platform: RoyalRoadPlatform) -> None:
        """Test getting fiction statistics."""
        await platform.authenticate()

        fiction_id = await platform.create_story(
            title="Test Fiction",
            description="Test",
            tags=[],
        )

        stats = await platform.get_statistics(fiction_id)

        assert stats is not None
        assert "views" in stats
        assert "average_rating" in stats


class TestRoyalRoadPlatformTagLimits:
    """Tests for Royal Road tag limits."""

    @pytest.fixture
    def platform(self) -> RoyalRoadPlatform:
        """Create Royal Road platform."""
        return RoyalRoadPlatform(
            username="test_user",
            password="test_pass",
            simulate=True
        )

    @pytest.mark.asyncio
    async def test_tag_limit_enforced(self, platform: RoyalRoadPlatform) -> None:
        """Test that tag limit is enforced (max 10)."""
        await platform.authenticate()

        # Create with 15 tags
        tags = [f"tag{i}" for i in range(15)]
        fiction_id = await platform.create_story(
            title="Test",
            description="Test",
            tags=tags,
        )

        info = await platform.get_fiction_info(fiction_id)
        # Should be limited to 10
        assert len(info["tags"]) <= 10
