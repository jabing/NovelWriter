# tests/test_platforms/test_wattpad.py
"""Tests for Wattpad Platform."""

import pytest

from src.platforms.base import PublishStatus
from src.platforms.wattpad import WattpadPlatform


class TestWattpadPlatform:
    """Tests for WattpadPlatform."""

    @pytest.fixture
    def platform(self) -> WattpadPlatform:
        """Create Wattpad platform in simulation mode."""
        return WattpadPlatform(api_key="test_key", simulate=True)

    def test_platform_name(self, platform: WattpadPlatform) -> None:
        """Test platform name is set correctly."""
        assert platform.PLATFORM_NAME == "wattpad"

    def test_simulate_mode_enabled(self, platform: WattpadPlatform) -> None:
        """Test simulation mode is enabled."""
        assert platform._simulate is True

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key(self, platform: WattpadPlatform) -> None:
        """Test authentication with API key."""
        result = await platform.authenticate()
        assert result is True
        assert platform._authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_without_api_key(self) -> None:
        """Test authentication fails without API key."""
        platform = WattpadPlatform(simulate=True)
        result = await platform.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_create_story(self, platform: WattpadPlatform) -> None:
        """Test creating a story."""
        await platform.authenticate()

        story_id = await platform.create_story(
            title="Test Story",
            description="A test story description",
            tags=["scifi", "adventure"],
        )

        assert story_id is not None
        assert story_id.startswith("wp_story_")

    @pytest.mark.asyncio
    async def test_create_story_not_authenticated(self, platform: WattpadPlatform) -> None:
        """Test creating story without authentication fails."""
        with pytest.raises(RuntimeError, match="Not authenticated"):
            await platform.create_story(
                title="Test Story",
                description="Test",
                tags=[],
            )

    @pytest.mark.asyncio
    async def test_publish_chapter(self, platform: WattpadPlatform) -> None:
        """Test publishing a chapter."""
        await platform.authenticate()

        story_id = await platform.create_story(
            title="Test Story",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=story_id,
            chapter_number=1,
            title="Chapter One",
            content="This is the chapter content.",
        )

        assert result.success is True
        assert result.status == PublishStatus.PUBLISHED
        assert result.chapter_id is not None

    @pytest.mark.asyncio
    async def test_publish_chapter_as_draft(self, platform: WattpadPlatform) -> None:
        """Test publishing a chapter as draft."""
        await platform.authenticate()

        story_id = await platform.create_story(
            title="Test Story",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=story_id,
            chapter_number=1,
            title="Chapter One",
            content="Content",
            draft=True,
        )

        assert result.success is True
        assert result.status == PublishStatus.DRAFT

    @pytest.mark.asyncio
    async def test_publish_chapter_invalid_story(self, platform: WattpadPlatform) -> None:
        """Test publishing to invalid story fails."""
        await platform.authenticate()

        result = await platform.publish_chapter(
            story_id="invalid_story_id",
            chapter_number=1,
            title="Chapter",
            content="Content",
        )

        assert result.success is False
        assert result.status == PublishStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_comments(self, platform: WattpadPlatform) -> None:
        """Test getting comments."""
        await platform.authenticate()

        story_id = await platform.create_story(
            title="Test Story",
            description="Test",
            tags=[],
        )

        # Publish a chapter first
        await platform.publish_chapter(
            story_id=story_id,
            chapter_number=1,
            title="Chapter",
            content="Content",
        )

        comments = await platform.get_comments(story_id, limit=10)
        assert isinstance(comments, list)

    @pytest.mark.asyncio
    async def test_get_comments_for_chapter(self, platform: WattpadPlatform) -> None:
        """Test getting comments for specific chapter."""
        await platform.authenticate()

        story_id = await platform.create_story(
            title="Test Story",
            description="Test",
            tags=[],
        )

        await platform.publish_chapter(
            story_id=story_id,
            chapter_number=1,
            title="Chapter 1",
            content="Content",
        )

        comments = await platform.get_comments(story_id, chapter_number=1, limit=10)
        assert isinstance(comments, list)

    @pytest.mark.asyncio
    async def test_reply_to_comment(self, platform: WattpadPlatform) -> None:
        """Test replying to a comment."""
        await platform.authenticate()

        result = await platform.reply_to_comment(
            story_id="test_story",
            comment_id="test_comment",
            reply_text="Thank you for your comment!",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_story_info(self, platform: WattpadPlatform) -> None:
        """Test getting story info."""
        await platform.authenticate()

        story_id = await platform.create_story(
            title="Test Story",
            description="Test description",
            tags=["scifi"],
        )

        info = await platform.get_story_info(story_id)

        assert info is not None
        assert info["title"] == "Test Story"
        assert info["description"] == "Test description"

    @pytest.mark.asyncio
    async def test_update_chapter(self, platform: WattpadPlatform) -> None:
        """Test updating a chapter."""
        await platform.authenticate()

        story_id = await platform.create_story(
            title="Test Story",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=story_id,
            chapter_number=1,
            title="Original Title",
            content="Original content.",
        )

        update_result = await platform.update_chapter(
            story_id=story_id,
            chapter_id=result.chapter_id,
            content="Updated content.",
            title="Updated Title",
        )

        assert update_result.success is True


class TestWattpadPlatformTagLimits:
    """Tests for Wattpad tag limits."""

    @pytest.fixture
    def platform(self) -> WattpadPlatform:
        """Create Wattpad platform."""
        return WattpadPlatform(api_key="test_key", simulate=True)

    @pytest.mark.asyncio
    async def test_tag_limit_enforced(self, platform: WattpadPlatform) -> None:
        """Test that tag limit is enforced (max 25)."""
        await platform.authenticate()

        # Create with 30 tags
        tags = [f"tag{i}" for i in range(30)]
        story_id = await platform.create_story(
            title="Test",
            description="Test",
            tags=tags,
        )

        info = await platform.get_story_info(story_id)
        # Should be limited to 25
        assert len(info["tags"]) <= 25
