# tests/test_platforms/test_publisher_agent.py
"""Tests for Publisher Agent."""


import pytest

from src.agents.base import AgentResult
from src.agents.publisher import PublisherAgent


class TestPublisherAgent:
    """Tests for PublisherAgent."""

    @pytest.fixture
    def agent(self) -> PublisherAgent:
        """Create Publisher Agent."""
        return PublisherAgent(name="Test Publisher")

    def test_agent_initialization(self, agent: PublisherAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Test Publisher"
        assert len(agent.PLATFORMS) == 3
        assert "wattpad" in agent.PLATFORMS
        assert "royalroad" in agent.PLATFORMS
        assert "kindle" in agent.PLATFORMS

    def test_get_available_platforms(self, agent: PublisherAgent) -> None:
        """Test getting available platforms."""
        platforms = agent.get_available_platforms()

        assert "wattpad" in platforms
        assert "royalroad" in platforms
        assert "kindle" in platforms

    def test_register_platform(self, agent: PublisherAgent) -> None:
        """Test registering a platform."""
        result = agent.register_platform("wattpad", api_key="test_key")

        assert result is True
        assert "wattpad" in agent.get_registered_platforms()

    def test_register_platform_case_insensitive(self, agent: PublisherAgent) -> None:
        """Test platform registration is case insensitive."""
        result = agent.register_platform("WATTPAD", api_key="test_key")

        assert result is True
        assert "wattpad" in agent.get_registered_platforms()

    def test_register_invalid_platform(self, agent: PublisherAgent) -> None:
        """Test registering invalid platform fails."""
        result = agent.register_platform("invalid_platform")

        assert result is False
        assert "invalid_platform" not in agent.get_registered_platforms()

    def test_set_story_id(self, agent: PublisherAgent) -> None:
        """Test setting story ID for platform."""
        agent.set_story_id("wattpad", "story_123")

        assert agent._story_ids.get("wattpad") == "story_123"

    def test_get_registered_platforms_empty(self, agent: PublisherAgent) -> None:
        """Test getting registered platforms when none registered."""
        platforms = agent.get_registered_platforms()
        assert platforms == []


class TestPublisherAgentExecute:
    """Tests for Publisher Agent execute method."""

    @pytest.fixture
    def agent(self) -> PublisherAgent:
        """Create Publisher Agent with platforms registered."""
        agent = PublisherAgent(name="Test Publisher")
        agent.register_platform("wattpad", api_key="test")
        agent.register_platform("royalroad", username="test", password="test")
        return agent

    @pytest.mark.asyncio
    async def test_execute_no_content(self, agent: PublisherAgent) -> None:
        """Test execute with no content fails."""
        result = await agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "platforms": ["wattpad"],
        })

        assert result.success is False
        assert "No content provided" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execute_no_platforms(self, agent: PublisherAgent) -> None:
        """Test execute with no platforms fails."""
        result = await agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "content": "Test content",
            "platforms": [],
        })

        assert result.success is False
        assert "No platforms specified" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execute_single_platform(self, agent: PublisherAgent) -> None:
        """Test execute with single platform."""
        result = await agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "title": "Chapter 1",
            "content": "This is the chapter content.",
            "platforms": ["wattpad"],
        })

        assert result.success is True
        assert "wattpad" in result.data["platforms_published"]

    @pytest.mark.asyncio
    async def test_execute_multiple_platforms(self, agent: PublisherAgent) -> None:
        """Test execute with multiple platforms."""
        result = await agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "title": "Chapter 1",
            "content": "This is the chapter content.",
            "platforms": ["wattpad", "royalroad"],
        })

        assert result.success is True
        assert "wattpad" in result.data["platforms_published"]
        assert "royalroad" in result.data["platforms_published"]

    @pytest.mark.asyncio
    async def test_execute_with_story_ids(self, agent: PublisherAgent) -> None:
        """Test execute with pre-existing story IDs."""
        # First create the story so it exists in the platform
        story_id = await agent.create_story_on_platform(
            platform_name="wattpad",
            title="Test Story",
            description="Test",
            tags=[],
        )

        result = await agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "title": "Chapter 1",
            "content": "Content",
            "platforms": ["wattpad"],
            "story_ids": {"wattpad": story_id},
        })

        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_returns_results(self, agent: PublisherAgent) -> None:
        """Test execute returns detailed results."""
        result = await agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "title": "Chapter 1",
            "content": "Content",
            "platforms": ["wattpad"],
        })

        assert "results" in result.data
        assert "wattpad" in result.data["results"]
        assert result.data["results"]["wattpad"]["success"] is True

    @pytest.mark.asyncio
    async def test_execute_unregistered_platform_auto_registers(self, agent: PublisherAgent) -> None:
        """Test that unregistered platforms are auto-registered."""
        # Create fresh agent without pre-registered platforms
        fresh_agent = PublisherAgent(name="Fresh Agent")

        result = await fresh_agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "title": "Chapter 1",
            "content": "Content",
            "platforms": ["wattpad"],
            "platform_configs": {
                "wattpad": {"api_key": "test_key"}
            },
        })

        # Should auto-register with config and succeed
        assert result.success is True


class TestPublisherAgentStoryCreation:
    """Tests for Publisher Agent story creation."""

    @pytest.fixture
    def agent(self) -> PublisherAgent:
        """Create Publisher Agent."""
        agent = PublisherAgent(name="Test Publisher")
        agent.register_platform("wattpad", api_key="test")
        return agent

    @pytest.mark.asyncio
    async def test_create_story_on_platform(self, agent: PublisherAgent) -> None:
        """Test creating story on platform."""
        story_id = await agent.create_story_on_platform(
            platform_name="wattpad",
            title="Test Story",
            description="Test description",
            tags=["scifi", "adventure"],
        )

        assert story_id is not None
        assert agent._story_ids.get("wattpad") == story_id

    @pytest.mark.asyncio
    async def test_create_story_on_unregistered_platform(self, agent: PublisherAgent) -> None:
        """Test creating story on unregistered platform fails."""
        story_id = await agent.create_story_on_platform(
            platform_name="kindle",
            title="Test",
            description="Test",
            tags=[],
        )

        assert story_id is None


class TestPublisherAgentComments:
    """Tests for Publisher Agent comment operations."""

    @pytest.fixture
    def agent(self) -> PublisherAgent:
        """Create Publisher Agent with platforms."""
        agent = PublisherAgent(name="Test Publisher")
        agent.register_platform("wattpad", api_key="test")
        return agent

    @pytest.mark.asyncio
    async def test_get_comments_from_platform(self, agent: PublisherAgent) -> None:
        """Test getting comments from platform."""
        # First create a story
        story_id = await agent.create_story_on_platform(
            platform_name="wattpad",
            title="Test",
            description="Test",
            tags=[],
        )

        comments = await agent.get_comments_from_platform(
            platform_name="wattpad",
            story_id=story_id,
            limit=10,
        )

        assert isinstance(comments, list)

    @pytest.mark.asyncio
    async def test_reply_to_comment(self, agent: PublisherAgent) -> None:
        """Test replying to comment."""
        result = await agent.reply_to_comment(
            platform_name="wattpad",
            story_id="test_story",
            comment_id="test_comment",
            reply_text="Thank you!",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_reply_to_comment_unregistered_platform(self, agent: PublisherAgent) -> None:
        """Test replying to comment on unregistered platform."""
        result = await agent.reply_to_comment(
            platform_name="kindle",
            story_id="test_story",
            comment_id="test_comment",
            reply_text="Thank you!",
        )

        assert result is False


class TestPublisherAgentErrorHandling:
    """Tests for Publisher Agent error handling."""

    @pytest.fixture
    def agent(self) -> PublisherAgent:
        """Create Publisher Agent."""
        return PublisherAgent(name="Test Publisher")

    @pytest.mark.asyncio
    async def test_execute_with_invalid_platform(self, agent: PublisherAgent) -> None:
        """Test execute with invalid platform handles gracefully."""
        result = await agent.execute({
            "novel_id": "test_novel",
            "chapter_number": 1,
            "title": "Chapter 1",
            "content": "Content",
            "platforms": ["invalid_platform"],
        })

        # Should fail because invalid platform can't be registered
        assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, agent: PublisherAgent) -> None:
        """Test execute handles exceptions."""
        # Pass malformed input that could cause exception
        result = await agent.execute({
            "novel_id": None,
            "chapter_number": "not_a_number",  # Invalid type
            "content": "Content",
            "platforms": ["wattpad"],
        })

        # Should handle gracefully
        assert isinstance(result, AgentResult)
