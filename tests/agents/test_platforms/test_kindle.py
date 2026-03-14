# tests/test_platforms/test_kindle.py
"""Tests for Kindle/KDP Platform."""

import pytest

from src.novel_agent.platforms.base import PublishStatus
from src.novel_agent.platforms.kindle import KindlePlatform


class TestKindlePlatform:
    """Tests for KindlePlatform."""

    @pytest.fixture
    def platform(self) -> KindlePlatform:
        """Create Kindle platform in simulation mode."""
        return KindlePlatform(
            access_key="test_access_key",
            secret_key="test_secret_key",
            simulate=True
        )

    def test_platform_name(self, platform: KindlePlatform) -> None:
        """Test platform name is set correctly."""
        assert platform.PLATFORM_NAME == "kindle"

    def test_simulate_mode_enabled(self, platform: KindlePlatform) -> None:
        """Test simulation mode is enabled."""
        assert platform._simulate is True

    @pytest.mark.asyncio
    async def test_authenticate_with_credentials(self, platform: KindlePlatform) -> None:
        """Test authentication with credentials."""
        result = await platform.authenticate()
        assert result is True
        assert platform._authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_without_credentials(self) -> None:
        """Test authentication fails without credentials."""
        platform = KindlePlatform(simulate=True)
        result = await platform.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_create_book(self, platform: KindlePlatform) -> None:
        """Test creating a book."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="A test book description",
            tags=["scifi", "adventure"],
        )

        assert book_id is not None
        assert book_id.startswith("kdp_book_")

    @pytest.mark.asyncio
    async def test_create_book_with_existing_asin(self, platform: KindlePlatform) -> None:
        """Test creating a book with existing ASIN."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test",
            tags=[],
            asin="B0XXXXXXXX",
        )

        assert book_id == "B0XXXXXXXX"

    @pytest.mark.asyncio
    async def test_create_book_not_authenticated(self, platform: KindlePlatform) -> None:
        """Test creating book without authentication fails."""
        with pytest.raises(RuntimeError, match="Not authenticated"):
            await platform.create_story(
                title="Test Book",
                description="Test",
                tags=[],
            )

    @pytest.mark.asyncio
    async def test_publish_chapter(self, platform: KindlePlatform) -> None:
        """Test publishing a chapter (appends to manuscript)."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test",
            tags=[],
        )

        result = await platform.publish_chapter(
            story_id=book_id,
            chapter_number=1,
            title="Chapter One",
            content="This is the chapter content.",
        )

        assert result.success is True
        # KDP chapters are always drafts until full book publish
        assert result.status == PublishStatus.DRAFT

    @pytest.mark.asyncio
    async def test_publish_chapter_updates_word_count(self, platform: KindlePlatform) -> None:
        """Test that publishing chapters updates word count."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test",
            tags=[],
        )

        await platform.publish_chapter(
            story_id=book_id,
            chapter_number=1,
            title="Chapter One",
            content="One two three four five.",
        )

        info = await platform.get_book_info(book_id)
        assert info is not None
        assert info["word_count"] == 5

    @pytest.mark.asyncio
    async def test_publish_chapter_invalid_book(self, platform: KindlePlatform) -> None:
        """Test publishing to invalid book fails."""
        await platform.authenticate()

        result = await platform.publish_chapter(
            story_id="invalid_book_id",
            chapter_number=1,
            title="Chapter",
            content="Content",
        )

        assert result.success is False
        assert result.status == PublishStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_reviews(self, platform: KindlePlatform) -> None:
        """Test getting reviews (called comments in interface)."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test",
            tags=[],
        )

        reviews = await platform.get_comments(book_id, limit=10)
        assert isinstance(reviews, list)

    @pytest.mark.asyncio
    async def test_reply_to_review(self, platform: KindlePlatform) -> None:
        """Test replying to a review."""
        await platform.authenticate()

        result = await platform.reply_to_comment(
            story_id="test_book",
            comment_id="test_review",
            reply_text="Thank you!",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_book_info(self, platform: KindlePlatform) -> None:
        """Test getting book info."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test description",
            tags=["scifi"],
        )

        info = await platform.get_book_info(book_id)

        assert info is not None
        assert info["title"] == "Test Book"
        assert info["description"] == "Test description"

    @pytest.mark.asyncio
    async def test_get_manuscript(self, platform: KindlePlatform) -> None:
        """Test getting formatted manuscript."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test",
            tags=[],
        )

        await platform.publish_chapter(
            story_id=book_id,
            chapter_number=1,
            title="Chapter 1",
            content="Chapter content here.",
        )

        manuscript = await platform.get_manuscript(book_id)

        assert manuscript is not None
        assert len(manuscript) > 0

    @pytest.mark.asyncio
    async def test_publish_book(self, platform: KindlePlatform) -> None:
        """Test publishing the complete book."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test",
            tags=[],
            price=2.99,
        )

        await platform.publish_chapter(
            story_id=book_id,
            chapter_number=1,
            title="Chapter 1",
            content="Chapter content.",
        )

        result = await platform.publish_book(book_id)

        assert result.success is True
        assert result.status == PublishStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_publish_book_as_preorder(self, platform: KindlePlatform) -> None:
        """Test publishing book as pre-order."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test Book",
            description="Test",
            tags=[],
        )

        await platform.publish_chapter(
            story_id=book_id,
            chapter_number=1,
            title="Chapter 1",
            content="Content.",
        )

        result = await platform.publish_book(
            book_id,
            pre_order=True,
            release_date="2024-12-25",
        )

        assert result.success is True
        assert result.status == PublishStatus.SCHEDULED


class TestKindlePlatformRoyalties:
    """Tests for Kindle royalty calculations."""

    @pytest.fixture
    def platform(self) -> KindlePlatform:
        """Create Kindle platform."""
        return KindlePlatform(
            access_key="test_key",
            secret_key="test_secret",
            simulate=True
        )

    @pytest.mark.asyncio
    async def test_calculate_35_percent_royalties(self, platform: KindlePlatform) -> None:
        """Test 35% royalty calculation."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test",
            description="Test",
            tags=[],
            price=2.99,
            royalty_type="35%",
        )

        royalties = await platform.calculate_royalties(book_id)

        assert royalties["royalty_rate"] == 0.35
        assert royalties["list_price"] == 2.99
        # 2.99 * 0.35 = 1.05
        assert royalties["royalty_per_sale"] == pytest.approx(1.05, rel=0.01)

    @pytest.mark.asyncio
    async def test_calculate_70_percent_royalties(self, platform: KindlePlatform) -> None:
        """Test 70% royalty calculation."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test",
            description="Test",
            tags=[],
            price=3.99,
            royalty_type="70%",
        )

        royalties = await platform.calculate_royalties(book_id)

        assert royalties["royalty_rate"] == 0.70
        # Should have delivery fee for 70%
        assert "delivery_fee" in royalties

    @pytest.mark.asyncio
    async def test_calculate_royalties_with_custom_price(self, platform: KindlePlatform) -> None:
        """Test royalty calculation with custom price override."""
        await platform.authenticate()

        book_id = await platform.create_story(
            title="Test",
            description="Test",
            tags=[],
            price=2.99,
            royalty_type="35%",
        )

        royalties = await platform.calculate_royalties(book_id, price=4.99)

        assert royalties["list_price"] == 4.99


class TestKindlePlatformCategoryLimits:
    """Tests for KDP category/keyword limits."""

    @pytest.fixture
    def platform(self) -> KindlePlatform:
        """Create Kindle platform."""
        return KindlePlatform(
            access_key="test_key",
            secret_key="test_secret",
            simulate=True
        )

    @pytest.mark.asyncio
    async def test_category_limit_enforced(self, platform: KindlePlatform) -> None:
        """Test that category limit is enforced (max 2)."""
        await platform.authenticate()

        # Create with 5 categories
        tags = [f"category{i}" for i in range(5)]
        book_id = await platform.create_story(
            title="Test",
            description="Test",
            tags=tags,
        )

        info = await platform.get_book_info(book_id)
        # Categories should be limited to 2
        assert len(info["categories"]) <= 2

    @pytest.mark.asyncio
    async def test_keyword_limit_enforced(self, platform: KindlePlatform) -> None:
        """Test that keyword limit is enforced (max 7)."""
        await platform.authenticate()

        # Create with 10 keywords
        tags = [f"keyword{i}" for i in range(10)]
        book_id = await platform.create_story(
            title="Test",
            description="Test",
            tags=tags,
        )

        info = await platform.get_book_info(book_id)
        # Keywords should be limited to 7
        assert len(info["keywords"]) <= 7
