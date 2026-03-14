# tests/test_agents/test_market_research.py
"""Tests for Market Research Agent."""

import pytest

from src.agents.market_research import MarketResearchAgent


class TestMarketResearchAgent:
    """Tests for MarketResearchAgent."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    def test_agent_initialization(self, agent: MarketResearchAgent) -> None:
        """Test agent initializes correctly."""
        assert agent.name == "Test Market Research"
        assert len(agent.TRENDING_GENRES) > 0
        assert len(agent.TROPE_DATABASE) > 0
        assert len(agent.KEYWORD_DATABASE) > 0

    def test_trending_genres_defined(self, agent: MarketResearchAgent) -> None:
        """Test trending genres are defined for platforms."""
        assert "wattpad" in agent.TRENDING_GENRES
        assert "royalroad" in agent.TRENDING_GENRES
        assert "amazon" in agent.TRENDING_GENRES

    def test_trope_database_defined(self, agent: MarketResearchAgent) -> None:
        """Test trope database is populated."""
        assert "scifi" in agent.TROPE_DATABASE
        assert "fantasy" in agent.TROPE_DATABASE
        assert "romance" in agent.TROPE_DATABASE

    def test_keyword_database_defined(self, agent: MarketResearchAgent) -> None:
        """Test keyword database is populated."""
        assert "high_demand" in agent.KEYWORD_DATABASE
        assert "emerging" in agent.KEYWORD_DATABASE
        assert "evergreen" in agent.KEYWORD_DATABASE


class TestMarketResearchExecute:
    """Tests for Market Research Agent execute method."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_execute_basic(self, agent: MarketResearchAgent) -> None:
        """Test basic execution."""
        result = await agent.execute({})

        assert result.success is True
        assert "trends" in result.data
        assert "genre_analysis" in result.data
        assert "recommendations" in result.data

    @pytest.mark.asyncio
    async def test_execute_with_genre(self, agent: MarketResearchAgent) -> None:
        """Test execution with specific genre."""
        result = await agent.execute({"genre": "fantasy"})

        assert result.success is True
        assert result.data["target_genre"] == "fantasy"
        assert result.data["genre_analysis"]["found"] is True

    @pytest.mark.asyncio
    async def test_execute_with_platform(self, agent: MarketResearchAgent) -> None:
        """Test execution with specific platform."""
        result = await agent.execute({"platform": "wattpad"})

        assert result.success is True
        assert result.data["target_platform"] == "wattpad"
        assert "wattpad" in result.data["trends"]["platforms"]

    @pytest.mark.asyncio
    async def test_execute_with_keywords(self, agent: MarketResearchAgent) -> None:
        """Test execution with keywords."""
        result = await agent.execute({
            "keywords": ["magic system", "world building", "strong female lead"]
        })

        assert result.success is True
        assert "keyword_insights" in result.data
        assert result.data["keyword_insights"]["optimization_score"] > 0

    @pytest.mark.asyncio
    async def test_execute_returns_recommendations(self, agent: MarketResearchAgent) -> None:
        """Test that execute returns recommendations."""
        result = await agent.execute({"genre": "scifi"})

        assert result.success is True
        recs = result.data["recommendations"]
        assert "content_strategy" in recs
        assert "genre_recommendations" in recs
        assert "keyword_recommendations" in recs
        assert "timing_recommendations" in recs


class TestTrendAnalysis:
    """Tests for trend analysis methods."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_analyze_trends_all_platforms(self, agent: MarketResearchAgent) -> None:
        """Test analyzing trends for all platforms."""
        trends = await agent._analyze_trends("all")

        assert "platforms" in trends
        assert len(trends["platforms"]) >= 3  # At least wattpad, royalroad, and others
        assert "overall_trending" in trends
        assert "growth_areas" in trends

    @pytest.mark.asyncio
    async def test_analyze_trends_specific_platform(self, agent: MarketResearchAgent) -> None:
        """Test analyzing trends for specific platform."""
        trends = await agent._analyze_trends("wattpad")

        assert "wattpad" in trends["platforms"]
        assert len(trends["platforms"]) == 1

    @pytest.mark.asyncio
    async def test_analyze_trends_includes_growth_areas(self, agent: MarketResearchAgent) -> None:
        """Test that trend analysis identifies growth areas."""
        trends = await agent._analyze_trends("all")

        # Should have growth areas with >= 15% growth
        if trends["growth_areas"]:
            for area in trends["growth_areas"]:
                growth = int(area["growth"].replace("+", "").replace("%", ""))
                assert growth >= 15


class TestGenreAnalysis:
    """Tests for genre analysis methods."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_analyze_genre_all(self, agent: MarketResearchAgent) -> None:
        """Test analyzing all genres."""
        analysis = await agent._analyze_genre("all")

        assert "analyzed_genres" in analysis
        assert len(analysis["analyzed_genres"]) > 0
        assert "top_tropes_per_genre" in analysis

    @pytest.mark.asyncio
    async def test_analyze_specific_genre(self, agent: MarketResearchAgent) -> None:
        """Test analyzing specific genre."""
        analysis = await agent._analyze_genre("fantasy")

        assert analysis["found"] is True
        assert analysis["genre"] == "fantasy"
        assert "popular_tropes" in analysis
        assert "Chosen One" in analysis["popular_tropes"]

    @pytest.mark.asyncio
    async def test_analyze_unknown_genre(self, agent: MarketResearchAgent) -> None:
        """Test analyzing unknown genre."""
        analysis = await agent._analyze_genre("unknown_genre")

        assert analysis["found"] is False
        assert "message" in analysis

    @pytest.mark.asyncio
    async def test_analyze_genre_with_alias(self, agent: MarketResearchAgent) -> None:
        """Test analyzing genre with common alias."""
        # "sci-fi" should map to "scifi"
        analysis = await agent._analyze_genre("sci-fi")

        assert analysis["found"] is True
        assert "AI Uprising" in analysis["popular_tropes"]


class TestKeywordAnalysis:
    """Tests for keyword analysis methods."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_analyze_keywords_empty(self, agent: MarketResearchAgent) -> None:
        """Test analyzing empty keywords returns general insights."""
        insights = await agent._analyze_keywords([])

        assert "high_demand_keywords" in insights
        assert "emerging_keywords" in insights
        assert "evergreen_keywords" in insights

    @pytest.mark.asyncio
    async def test_analyze_keywords_high_demand(self, agent: MarketResearchAgent) -> None:
        """Test analyzing high demand keywords."""
        insights = await agent._analyze_keywords(["strong female lead", "slow burn"])

        assert insights["optimization_score"] > 0
        # Should identify these as high demand
        high_demand_found = any(
            kw["category"] == "high_demand"
            for kw in insights["analyzed_keywords"]
        )
        assert high_demand_found is True

    @pytest.mark.asyncio
    async def test_analyze_keywords_emerging(self, agent: MarketResearchAgent) -> None:
        """Test analyzing emerging keywords."""
        insights = await agent._analyze_keywords(["romantasy", "cozy fantasy"])

        # Should identify these as emerging
        emerging_found = any(
            kw["category"] == "emerging"
            for kw in insights["analyzed_keywords"]
        )
        assert emerging_found is True

    @pytest.mark.asyncio
    async def test_analyze_keywords_generates_suggestions(self, agent: MarketResearchAgent) -> None:
        """Test that keyword analysis generates suggestions."""
        # Use keywords that are not in high demand
        insights = await agent._analyze_keywords(["random", "keywords"])

        # Should have suggestions for missing high-demand keywords
        if insights["optimization_score"] < 100:
            assert len(insights["suggestions"]) > 0


class TestRecommendations:
    """Tests for recommendation generation."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, agent: MarketResearchAgent) -> None:
        """Test recommendation generation."""
        trends = await agent._analyze_trends("all")
        genre_analysis = await agent._analyze_genre("fantasy")
        keyword_insights = await agent._analyze_keywords([])

        recs = await agent._generate_recommendations(
            trends, genre_analysis, keyword_insights
        )

        assert "content_strategy" in recs
        assert "genre_recommendations" in recs
        assert "keyword_recommendations" in recs
        assert "timing_recommendations" in recs
        assert "priority" in recs

    @pytest.mark.asyncio
    async def test_recommendations_for_saturated_genre(self, agent: MarketResearchAgent) -> None:
        """Test recommendations for saturated genre."""
        trends = await agent._analyze_trends("all")
        # Fantasy is marked as "high" saturation
        genre_analysis = await agent._analyze_genre("fantasy")
        keyword_insights = await agent._analyze_keywords([])

        recs = await agent._generate_recommendations(
            trends, genre_analysis, keyword_insights
        )

        # Should warn about saturation
        assert any("saturated" in r.lower() for r in recs["genre_recommendations"])


class TestCompetitorAnalysis:
    """Tests for competitor analysis."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_get_competitor_analysis(self, agent: MarketResearchAgent) -> None:
        """Test getting competitor analysis."""
        analysis = await agent.get_competitor_analysis("fantasy")

        assert analysis["genre"] == "fantasy"
        assert "top_competitors" in analysis
        assert len(analysis["top_competitors"]) > 0
        assert "average_chapters" in analysis

    @pytest.mark.asyncio
    async def test_competitor_analysis_sorted_by_reads(self, agent: MarketResearchAgent) -> None:
        """Test that competitors are sorted by reads."""
        analysis = await agent.get_competitor_analysis("scifi")

        competitors = analysis["top_competitors"]
        for i in range(len(competitors) - 1):
            assert competitors[i]["estimated_reads"] >= competitors[i + 1]["estimated_reads"]


class TestTrendingTags:
    """Tests for trending tags."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    @pytest.mark.asyncio
    async def test_get_trending_tags(self, agent: MarketResearchAgent) -> None:
        """Test getting trending tags."""
        tags = await agent.get_trending_tags("wattpad", limit=10)

        assert len(tags) <= 10
        for tag in tags:
            assert "tag" in tag
            assert "popularity_score" in tag
            assert "growth" in tag

    @pytest.mark.asyncio
    async def test_trending_tags_sorted_by_popularity(self, agent: MarketResearchAgent) -> None:
        """Test that trending tags are sorted by popularity."""
        tags = await agent.get_trending_tags("royalroad", limit=15)

        for i in range(len(tags) - 1):
            assert tags[i]["popularity_score"] >= tags[i + 1]["popularity_score"]


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def agent(self) -> MarketResearchAgent:
        """Create Market Research Agent."""
        return MarketResearchAgent(name="Test Market Research")

    def test_estimate_saturation(self, agent: MarketResearchAgent) -> None:
        """Test saturation estimation."""
        assert agent._estimate_saturation("fantasy") == "high"
        assert agent._estimate_saturation("history") == "low"
        assert agent._estimate_saturation("scifi") == "medium"

    def test_get_reader_expectations(self, agent: MarketResearchAgent) -> None:
        """Test getting reader expectations."""
        expectations = agent._get_reader_expectations("romance")

        assert len(expectations) > 0
        assert any("HEA" in e or "HFN" in e for e in expectations)

    def test_get_last_research(self, agent: MarketResearchAgent) -> None:
        """Test getting last research."""
        # Initially empty
        assert agent.get_last_research() == {}

    @pytest.mark.asyncio
    async def test_get_last_research_after_execute(self, agent: MarketResearchAgent) -> None:
        """Test that last research is stored after execute."""
        await agent.execute({"genre": "fantasy"})

        last = agent.get_last_research()
        assert last != {}
        assert last["target_genre"] == "fantasy"
