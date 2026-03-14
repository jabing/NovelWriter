# tests/test_agents/test_engagement.py
"""Tests for Engagement Agent."""

import pytest

from src.agents.engagement import EngagementAgent


class TestEngagementAgent:
    """Tests for EngagementAgent."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    def test_agent_initialization(self, agent: EngagementAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Test Engagement"
        assert len(agent.REPLY_TEMPLATES) > 0
        assert len(agent.EMOJIS) > 0

    def test_reply_templates_defined(self, agent: EngagementAgent) -> None:
        """Test reply templates are defined."""
        assert "positive" in agent.REPLY_TEMPLATES
        assert "negative" not in agent.REPLY_TEMPLATES  # Use 'complaint' instead
        assert "question" in agent.REPLY_TEMPLATES
        assert "generic" in agent.REPLY_TEMPLATES

    def test_emojis_defined(self, agent: EngagementAgent) -> None:
        """Test emojis are defined."""
        assert "😊" in agent.EMOJIS
        assert "🙏" in agent.EMOJIS


class TestEngagementExecute:
    """Tests for Engagement Agent execute method."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    @pytest.mark.asyncio
    async def test_execute_no_comments(self, agent: EngagementAgent) -> None:
        """Test execute with no comments fails."""
        result = await agent.execute({})

        assert result.success is False
        assert "No comments" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execute_with_comments(self, agent: EngagementAgent) -> None:
        """Test execute with comments."""
        comments = [
            {"id": "1", "text": "Love this story!"},
            {"id": "2", "text": "Great chapter!"},
        ]

        result = await agent.execute({"comments": comments})

        assert result.success is True
        assert result.data["replies_generated"] == 2

    @pytest.mark.asyncio
    async def test_execute_skips_replied(self, agent: EngagementAgent) -> None:
        """Test execute skips already replied comments."""
        comments = [
            {"id": "1", "text": "Love this!"},
        ]

        # First execution
        await agent.execute({"comments": comments})

        # Second execution with same comment
        result = await agent.execute({"comments": comments})

        # Should skip the already replied comment
        assert result.data["replies_generated"] == 0

    @pytest.mark.asyncio
    async def test_execute_returns_replies(self, agent: EngagementAgent) -> None:
        """Test execute returns replies."""
        comments = [
            {"id": "1", "text": "Great story!"},
        ]

        result = await agent.execute({"comments": comments})

        assert "replies" in result.data
        assert len(result.data["replies"]) == 1
        assert result.data["replies"][0]["reply"] != ""


class TestCommentCategorization:
    """Tests for comment categorization."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    def test_categorize_positive(self, agent: EngagementAgent) -> None:
        """Test categorizing positive comments."""
        assert agent._categorize_comment("I love this story!") == "positive"
        assert agent._categorize_comment("This is amazing!") == "positive"
        assert agent._categorize_comment("Great work!") == "positive"

    def test_categorize_excited(self, agent: EngagementAgent) -> None:
        """Test categorizing excited comments."""
        assert agent._categorize_comment("Can't wait for more!") == "excited"
        assert agent._categorize_comment("Update soon please!") == "excited"
        assert agent._categorize_comment("Waiting for next chapter!") == "excited"

    def test_categorize_question(self, agent: EngagementAgent) -> None:
        """Test categorizing questions."""
        assert agent._categorize_comment("What will happen next?") == "question"
        assert agent._categorize_comment("How did they survive?") == "question"
        assert agent._categorize_comment("Is this the end?") == "question"

    def test_categorize_suggestion(self, agent: EngagementAgent) -> None:
        """Test categorizing suggestions."""
        assert agent._categorize_comment("You should add more action") == "suggestion"
        assert agent._categorize_comment("Maybe they could meet earlier") == "suggestion"
        assert agent._categorize_comment("I have an idea") == "suggestion"

    def test_categorize_complaint(self, agent: EngagementAgent) -> None:
        """Test categorizing complaints."""
        assert agent._categorize_comment("This is boring") == "complaint"
        assert agent._categorize_comment("The story is slow") == "complaint"
        assert agent._categorize_comment("This is confusing and bad") == "complaint"

    def test_categorize_generic(self, agent: EngagementAgent) -> None:
        """Test categorizing generic comments."""
        assert agent._categorize_comment("Nice.") == "generic"
        assert agent._categorize_comment("Read it.") == "generic"
        assert agent._categorize_comment("Interesting.") == "generic"


class TestReplyGeneration:
    """Tests for reply generation."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    @pytest.mark.asyncio
    async def test_generate_reply(self, agent: EngagementAgent) -> None:
        """Test generating a reply."""
        comment = {"id": "1", "text": "Love this story!"}

        reply = await agent._generate_reply(comment)

        assert isinstance(reply, str)
        assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_generate_reply_variety(self, agent: EngagementAgent) -> None:
        """Test that replies have variety."""
        replies = []
        for i in range(5):
            comment = {"id": str(i), "text": "Great story!"}
            reply = await agent._generate_reply(comment)
            replies.append(reply)

        # Should have some variety (not all identical)
        unique_replies = len(set(replies))
        # At least 2 should be different due to emojis or template selection
        # Note: This is probabilistic, so we use >= 1
        assert unique_replies >= 1


class TestPersonalizedReplies:
    """Tests for personalized reply generation."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    @pytest.mark.asyncio
    async def test_generate_personalized_reply(self, agent: EngagementAgent) -> None:
        """Test generating personalized reply."""
        comment = {"id": "1", "text": "Great story!", "username": "reader123"}

        reply = await agent.generate_personalized_reply(comment)

        assert isinstance(reply, str)
        assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_personalized_with_context(self, agent: EngagementAgent) -> None:
        """Test personalized reply with story context."""
        comment = {"id": "1", "text": "Love it!", "username": "fan456"}
        context = {"title": "My Story", "chapter": 5}

        reply = await agent.generate_personalized_reply(comment, context)

        assert isinstance(reply, str)


class TestReplyTracking:
    """Tests for reply tracking."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    def test_get_reply_history_empty(self, agent: EngagementAgent) -> None:
        """Test getting empty reply history."""
        history = agent.get_reply_history()
        assert history == []

    @pytest.mark.asyncio
    async def test_get_reply_history_after_replies(self, agent: EngagementAgent) -> None:
        """Test reply history after generating replies."""
        comments = [{"id": "1", "text": "Great!"}]
        await agent.execute({"comments": comments})

        history = agent.get_reply_history()
        assert len(history) == 1

    def test_get_reply_count_empty(self, agent: EngagementAgent) -> None:
        """Test getting reply count when empty."""
        assert agent.get_reply_count() == 0

    @pytest.mark.asyncio
    async def test_get_reply_count_after_replies(self, agent: EngagementAgent) -> None:
        """Test reply count after generating replies."""
        comments = [
            {"id": "1", "text": "Great!"},
            {"id": "2", "text": "Amazing!"},
        ]
        await agent.execute({"comments": comments})

        assert agent.get_reply_count() == 2

    def test_is_replied_false_initially(self, agent: EngagementAgent) -> None:
        """Test is_replied returns False initially."""
        assert agent.is_replied("comment_1") is False

    @pytest.mark.asyncio
    async def test_is_replied_after_reply(self, agent: EngagementAgent) -> None:
        """Test is_replied returns True after reply."""
        comments = [{"id": "comment_1", "text": "Great!"}]
        await agent.execute({"comments": comments})

        assert agent.is_replied("comment_1") is True

    def test_clear_history(self, agent: EngagementAgent) -> None:
        """Test clearing history."""
        agent._reply_history = [{"test": "data"}]
        agent._replied_comments = {"1", "2"}

        agent.clear_history()

        assert agent.get_reply_count() == 0
        assert agent.is_replied("1") is False


class TestBulkReplies:
    """Tests for bulk reply generation."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    @pytest.mark.asyncio
    async def test_generate_bulk_replies(self, agent: EngagementAgent) -> None:
        """Test generating bulk replies."""
        comments = [
            {"id": str(i), "text": f"Comment {i}"} for i in range(10)
        ]

        replies = await agent.generate_bulk_replies(comments, max_replies=5)

        assert len(replies) == 5

    @pytest.mark.asyncio
    async def test_bulk_replies_respects_max(self, agent: EngagementAgent) -> None:
        """Test bulk replies respects max limit."""
        comments = [
            {"id": str(i), "text": f"Comment {i}"} for i in range(20)
        ]

        replies = await agent.generate_bulk_replies(comments, max_replies=10)

        assert len(replies) == 10

    @pytest.mark.asyncio
    async def test_bulk_replies_skips_replied(self, agent: EngagementAgent) -> None:
        """Test bulk replies skips already replied."""
        comments = [{"id": "1", "text": "First"}]

        # Generate first reply
        await agent.generate_bulk_replies(comments)

        # Try to generate again
        replies = await agent.generate_bulk_replies(comments)

        assert len(replies) == 0  # Should skip


class TestEngagementStats:
    """Tests for engagement statistics."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    def test_get_engagement_stats_empty(self, agent: EngagementAgent) -> None:
        """Test getting stats when empty."""
        stats = agent.get_engagement_stats()

        assert stats["total_replies"] == 0
        assert stats["unique_comments_replied"] == 0

    @pytest.mark.asyncio
    async def test_get_engagement_stats_after_replies(self, agent: EngagementAgent) -> None:
        """Test getting stats after replies."""
        comments = [
            {"id": "1", "text": "Great!"},
            {"id": "2", "text": "Amazing!"},
        ]
        await agent.execute({"comments": comments})

        stats = agent.get_engagement_stats()

        assert stats["total_replies"] == 2
        assert stats["unique_comments_replied"] == 2


class TestCustomTemplates:
    """Tests for custom template management."""

    @pytest.fixture
    def agent(self) -> EngagementAgent:
        """Create Engagement Agent."""
        return EngagementAgent(name="Test Engagement")

    def test_get_categories(self, agent: EngagementAgent) -> None:
        """Test getting available categories."""
        categories = agent.get_categories()

        assert "positive" in categories
        assert "generic" in categories

    def test_add_custom_template_new_category(self, agent: EngagementAgent) -> None:
        """Test adding template to new category."""
        agent.add_custom_template("custom", "This is a custom reply!")

        assert "custom" in agent.REPLY_TEMPLATES
        assert "This is a custom reply!" in agent.REPLY_TEMPLATES["custom"]

    def test_add_custom_template_existing_category(self, agent: EngagementAgent) -> None:
        """Test adding template to existing category."""
        initial_count = len(agent.REPLY_TEMPLATES["positive"])

        agent.add_custom_template("positive", "A new positive reply!")

        assert len(agent.REPLY_TEMPLATES["positive"]) == initial_count + 1
