# tests/test_agents/test_comment_analyzer.py
"""Tests for Comment Analyzer Agent."""

import pytest

from src.novel_agent.agents.comment_analyzer import CommentAnalyzerAgent


class TestCommentAnalyzerAgent:
    """Tests for CommentAnalyzerAgent."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    def test_agent_initialization(self, agent: CommentAnalyzerAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Test Comment Analyzer"
        assert len(agent.POSITIVE_WORDS) > 0
        assert len(agent.NEGATIVE_WORDS) > 0
        assert len(agent.THEME_KEYWORDS) > 0

    def test_positive_words_defined(self, agent: CommentAnalyzerAgent) -> None:
        """Test positive words are defined."""
        assert "love" in agent.POSITIVE_WORDS
        assert "amazing" in agent.POSITIVE_WORDS
        assert "great" in agent.POSITIVE_WORDS

    def test_negative_words_defined(self, agent: CommentAnalyzerAgent) -> None:
        """Test negative words are defined."""
        assert "hate" in agent.NEGATIVE_WORDS
        assert "terrible" in agent.NEGATIVE_WORDS
        assert "boring" in agent.NEGATIVE_WORDS

    def test_theme_keywords_defined(self, agent: CommentAnalyzerAgent) -> None:
        """Test theme keywords are defined."""
        assert "characters" in agent.THEME_KEYWORDS
        assert "plot" in agent.THEME_KEYWORDS
        assert "pacing" in agent.THEME_KEYWORDS


class TestCommentAnalyzerExecute:
    """Tests for Comment Analyzer Agent execute method."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    @pytest.mark.asyncio
    async def test_execute_no_comments(self, agent: CommentAnalyzerAgent) -> None:
        """Test execute with no comments fails."""
        result = await agent.execute({})

        assert result.success is False
        assert "No comments" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execute_with_comments(self, agent: CommentAnalyzerAgent) -> None:
        """Test execute with comments."""
        comments = [
            {"id": "1", "text": "This is amazing! Love it!"},
            {"id": "2", "text": "Great chapter!"},
            {"id": "3", "text": "It was okay."},
        ]

        result = await agent.execute({"comments": comments})

        assert result.success is True
        assert result.data["total_comments"] == 3

    @pytest.mark.asyncio
    async def test_execute_returns_sentiment(self, agent: CommentAnalyzerAgent) -> None:
        """Test execute returns sentiment analysis."""
        comments = [
            {"id": "1", "text": "Love this story!"},
        ]

        result = await agent.execute({"comments": comments})

        assert "sentiment" in result.data
        assert result.data["sentiment"]["positive"] >= 1

    @pytest.mark.asyncio
    async def test_execute_returns_themes(self, agent: CommentAnalyzerAgent) -> None:
        """Test execute returns theme analysis."""
        comments = [
            {"id": "1", "text": "The character development is amazing!"},
        ]

        result = await agent.execute({"comments": comments})

        assert "themes" in result.data
        assert "theme_counts" in result.data["themes"]

    @pytest.mark.asyncio
    async def test_execute_returns_keywords(self, agent: CommentAnalyzerAgent) -> None:
        """Test execute returns keyword analysis."""
        comments = [
            {"id": "1", "text": "Great chapter with amazing plot!"},
        ]

        result = await agent.execute({"comments": comments})

        assert "keywords" in result.data
        assert "top_keywords" in result.data["keywords"]

    @pytest.mark.asyncio
    async def test_execute_returns_suggestions(self, agent: CommentAnalyzerAgent) -> None:
        """Test execute returns suggestions."""
        comments = [
            {"id": "1", "text": "Love it!"},
        ]

        result = await agent.execute({"comments": comments})

        assert "suggestions" in result.data
        assert len(result.data["suggestions"]) > 0


class TestSentimentAnalysis:
    """Tests for sentiment analysis."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    def test_analyze_sentiment_positive(self, agent: CommentAnalyzerAgent) -> None:
        """Test analyzing positive comments."""
        comments = [
            {"id": "1", "text": "I love this story! It's amazing and fantastic!"},
            {"id": "2", "text": "Great chapter! Can't wait for more!"},
        ]

        result = agent._analyze_sentiment(comments)

        assert result["positive"] >= 2
        assert result["positive_percentage"] > 50

    def test_analyze_sentiment_negative(self, agent: CommentAnalyzerAgent) -> None:
        """Test analyzing negative comments."""
        comments = [
            {"id": "1", "text": "This is terrible and boring."},
            {"id": "2", "text": "I hate the plot holes."},
        ]

        result = agent._analyze_sentiment(comments)

        assert result["negative"] >= 2
        assert result["negative_percentage"] > 50

    def test_analyze_sentiment_mixed(self, agent: CommentAnalyzerAgent) -> None:
        """Test analyzing mixed comments."""
        comments = [
            {"id": "1", "text": "Love it!"},
            {"id": "2", "text": "Hate it."},
            {"id": "3", "text": "It's okay."},
        ]

        result = agent._analyze_sentiment(comments)

        assert result["positive"] >= 1
        assert result["negative"] >= 1

    def test_get_overall_sentiment_very_positive(self, agent: CommentAnalyzerAgent) -> None:
        """Test overall sentiment calculation - very positive."""
        result = agent._get_overall_sentiment(70, 10, 20)

        assert result == "very_positive"

    def test_get_overall_sentiment_positive(self, agent: CommentAnalyzerAgent) -> None:
        """Test overall sentiment calculation - positive."""
        result = agent._get_overall_sentiment(55, 20, 25)

        assert result == "positive"

    def test_get_overall_sentiment_mixed(self, agent: CommentAnalyzerAgent) -> None:
        """Test overall sentiment calculation - mixed."""
        result = agent._get_overall_sentiment(35, 30, 35)

        assert result == "mixed"

    def test_get_overall_sentiment_negative(self, agent: CommentAnalyzerAgent) -> None:
        """Test overall sentiment calculation - negative."""
        result = agent._get_overall_sentiment(20, 60, 20)

        assert result == "negative"


class TestThemeExtraction:
    """Tests for theme extraction."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    def test_extract_themes_characters(self, agent: CommentAnalyzerAgent) -> None:
        """Test extracting character theme."""
        comments = [
            {"id": "1", "text": "The main character is well developed."},
            {"id": "2", "text": "Love the protagonist!"},
        ]

        result = agent._extract_themes(comments)

        assert result["theme_counts"]["characters"] > 0
        assert "characters" in result["top_themes"]

    def test_extract_themes_plot(self, agent: CommentAnalyzerAgent) -> None:
        """Test extracting plot theme."""
        comments = [
            {"id": "1", "text": "The plot twist was unexpected!"},
            {"id": "2", "text": "Great storyline!"},
        ]

        result = agent._extract_themes(comments)

        assert result["theme_counts"]["plot"] > 0

    def test_extract_themes_pacing(self, agent: CommentAnalyzerAgent) -> None:
        """Test extracting pacing theme."""
        comments = [
            {"id": "1", "text": "The pacing is too slow."},
            {"id": "2", "text": "Great fast-paced action!"},
        ]

        result = agent._extract_themes(comments)

        assert result["theme_counts"]["pacing"] > 0

    def test_extract_themes_returns_examples(self, agent: CommentAnalyzerAgent) -> None:
        """Test that theme extraction includes examples."""
        comments = [
            {"id": "1", "text": "The character development is great."},
        ]

        result = agent._extract_themes(comments)

        assert "theme_examples" in result
        assert len(result["theme_examples"]["characters"]) > 0


class TestKeywordExtraction:
    """Tests for keyword extraction."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    def test_extract_keywords(self, agent: CommentAnalyzerAgent) -> None:
        """Test extracting keywords."""
        comments = [
            {"id": "1", "text": "Great chapter with amazing characters."},
            {"id": "2", "text": "Amazing story with great plot."},
        ]

        result = agent._extract_keywords(comments)

        assert len(result["top_keywords"]) > 0
        # "amazing" and "great" should be top keywords
        top_words = [kw["word"] for kw in result["top_keywords"]]
        assert "amazing" in top_words or "great" in top_words

    def test_extract_keywords_filters_stopwords(self, agent: CommentAnalyzerAgent) -> None:
        """Test that stop words are filtered."""
        comments = [
            {"id": "1", "text": "The story was very good and very interesting."},
        ]

        result = agent._extract_keywords(comments)

        top_words = [kw["word"] for kw in result["top_keywords"]]
        # Stop words should not be in top keywords
        assert "the" not in top_words
        assert "was" not in top_words

    def test_extract_keywords_counts_unique(self, agent: CommentAnalyzerAgent) -> None:
        """Test that unique word count is calculated."""
        comments = [
            {"id": "1", "text": "Good story with good characters."},
        ]

        result = agent._extract_keywords(comments)

        assert result["unique_words"] > 0
        assert result["total_words"] > 0


class TestEngagementMetrics:
    """Tests for engagement metrics."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    def test_calculate_engagement(self, agent: CommentAnalyzerAgent) -> None:
        """Test calculating engagement metrics."""
        comments = [
            {"id": "1", "text": "Great!", "votes": 5, "user": "user1"},
            {"id": "2", "text": "Amazing chapter!", "votes": 10, "user": "user2"},
            {"id": "3", "text": "Love it!", "votes": 3, "user": "user1"},
        ]

        result = agent._calculate_engagement(comments)

        assert result["total_votes"] == 18
        assert result["unique_users"] == 2
        assert result["average_length"] > 0

    def test_calculate_engagement_empty(self, agent: CommentAnalyzerAgent) -> None:
        """Test calculating engagement with no comments."""
        result = agent._calculate_engagement([])

        assert result["average_length"] == 0
        assert result["total_votes"] == 0
        assert result["unique_users"] == 0


class TestSuggestionsGeneration:
    """Tests for suggestions generation."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    @pytest.mark.asyncio
    async def test_generate_suggestions_positive(self, agent: CommentAnalyzerAgent) -> None:
        """Test generating suggestions for positive feedback."""
        sentiment = {"overall_sentiment": "very_positive", "negative_percentage": 5}
        themes = {"top_themes": ["characters"]}
        keywords = {"top_keywords": []}

        suggestions = await agent._generate_suggestions(sentiment, themes, keywords)

        assert len(suggestions) > 0
        # Should mention positive reception or encourage continuation
        assert any(
            "positive" in s.lower() or "excellent" in s.lower() or "engaging" in s.lower()
            for s in suggestions
        )

    @pytest.mark.asyncio
    async def test_generate_suggestions_negative(self, agent: CommentAnalyzerAgent) -> None:
        """Test generating suggestions for negative feedback."""
        sentiment = {"overall_sentiment": "negative", "negative_percentage": 60}
        themes = {"top_themes": []}
        keywords = {"top_keywords": []}

        suggestions = await agent._generate_suggestions(sentiment, themes, keywords)

        assert len(suggestions) > 0
        assert any("negative" in s.lower() or "review" in s.lower() for s in suggestions)


class TestSingleCommentAnalysis:
    """Tests for single comment analysis."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    @pytest.mark.asyncio
    async def test_analyze_single_comment_positive(self, agent: CommentAnalyzerAgent) -> None:
        """Test analyzing single positive comment."""
        comment = {"id": "1", "text": "I love this amazing story!"}

        result = await agent.analyze_single_comment(comment)

        assert result["sentiment"] == "positive"
        assert "love" in result["positive_words"]
        assert "amazing" in result["positive_words"]

    @pytest.mark.asyncio
    async def test_analyze_single_comment_negative(self, agent: CommentAnalyzerAgent) -> None:
        """Test analyzing single negative comment."""
        comment = {"id": "1", "text": "This is terrible and boring."}

        result = await agent.analyze_single_comment(comment)

        assert result["sentiment"] == "negative"
        assert "terrible" in result["negative_words"]

    @pytest.mark.asyncio
    async def test_analyze_single_comment_themes(self, agent: CommentAnalyzerAgent) -> None:
        """Test analyzing themes in single comment."""
        comment = {"id": "1", "text": "The character development and plot are great."}

        result = await agent.analyze_single_comment(comment)

        assert "characters" in result["themes"]
        assert "plot" in result["themes"]


class TestSentimentTrends:
    """Tests for sentiment trends."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    def test_get_sentiment_trends_by_chapter(self, agent: CommentAnalyzerAgent) -> None:
        """Test getting sentiment trends by chapter."""
        comments = [
            {"chapter": "1", "text": "Love it!"},
            {"chapter": "1", "text": "Great!"},
            {"chapter": "2", "text": "Boring."},
            {"chapter": "2", "text": "Terrible."},
        ]

        result = agent.get_sentiment_trends(comments, group_by="chapter")

        assert result["grouped_by"] == "chapter"
        assert "1" in result["trends"]
        assert "2" in result["trends"]

    def test_get_sentiment_trends_by_date(self, agent: CommentAnalyzerAgent) -> None:
        """Test getting sentiment trends by date."""
        comments = [
            {"date": "2024-01-01", "text": "Love it!"},
            {"date": "2024-01-02", "text": "Hate it."},
        ]

        result = agent.get_sentiment_trends(comments, group_by="date")

        assert result["grouped_by"] == "date"


class TestLastAnalysis:
    """Tests for last analysis storage."""

    @pytest.fixture
    def agent(self) -> CommentAnalyzerAgent:
        """Create Comment Analyzer Agent."""
        return CommentAnalyzerAgent(name="Test Comment Analyzer")

    def test_get_last_analysis_empty(self, agent: CommentAnalyzerAgent) -> None:
        """Test getting last analysis when none exists."""
        assert agent.get_last_analysis() == {}

    @pytest.mark.asyncio
    async def test_get_last_analysis_after_execute(self, agent: CommentAnalyzerAgent) -> None:
        """Test that last analysis is stored after execute."""
        comments = [{"id": "1", "text": "Great!"}]
        await agent.execute({"comments": comments})

        last = agent.get_last_analysis()

        assert last != {}
        assert last["total_comments"] == 1
