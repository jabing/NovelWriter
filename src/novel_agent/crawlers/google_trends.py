# src/crawlers/google_trends.py
"""Google Trends integration for market research.

Uses the pytrends library to fetch search trend data.
"""

import logging
from typing import Any

from src.novel_agent.crawlers.base import BaseCrawler, CrawlerResult
from src.novel_agent.crawlers.cache import CacheManager

logger = logging.getLogger(__name__)


class GoogleTrendsCrawler(BaseCrawler):
    """Google Trends crawler using pytrends library.

    Fetches:
    - Interest over time for keywords
    - Related topics
    - Trending searches
    - Regional interest data
    """

    BASE_URL = "https://trends.google.com"

    # Book/reading related categories
    BOOK_CATEGORIES = {
        "fantasy_books": "/m/0dwft",  # Fantasy literature
        "science_fiction": "/m/06b5p",  # Science fiction
        "romance_novels": "/m/0gq6m",  # Romance novels
        "web_novels": "/m/0fpk7z",  # Web fiction
        " ebooks": "/m/011826",  # E-books
    }

    # Key terms to track
    NOVEL_KEYWORDS = [
        "wattpad stories",
        "webnovel",
        "royal road",
        "fantasy books",
        "romance novels",
        "sci fi books",
        "litRPG",
        "cultivation novel",
        "isekai",
    ]

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        rate_limit: float = 5.0,  # Google is stricter
        **kwargs: Any,
    ) -> None:
        """Initialize Google Trends crawler.

        Args:
            cache_manager: Optional cache manager
            rate_limit: Seconds between requests
            **kwargs: Additional arguments for BaseCrawler
        """
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.cache = cache_manager or CacheManager()
        self._pytrends = None

    @property
    def name(self) -> str:
        return "google_trends"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    def _get_pytrends(self) -> Any:
        """Lazy load pytrends library."""
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq
                self._pytrends = TrendReq(
                    hl='en-US',
                    tz=360,  # US Pacific time
                    timeout=(10, 25),
                    retries=2,
                    backoff_factor=0.1,
                )
            except ImportError:
                raise ImportError(
                    "pytrends library required. Install with: pip install pytrends"
                )
        return self._pytrends

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending searches related to books/novels.

        Args:
            category: Optional category filter
            limit: Maximum items to return

        Returns:
            CrawlerResult with trending searches
        """
        cache_key = f"google_trends_trending_{category or 'all'}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            # Run pytrends in a thread since it's synchronous
            import asyncio

            def _fetch_trending():
                pt = self._get_pytrends()
                # Get trending searches
                trending = pt.trending_searches(pn='united_states')
                return trending.head(limit).to_dict('records')

            loop = asyncio.get_event_loop()
            trending_data = await loop.run_in_executor(None, _fetch_trending)

            result_data = {
                "trending_searches": trending_data,
                "category": category,
                "total": len(trending_data),
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Google Trends: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular search terms related to novels.

        Args:
            limit: Maximum terms to return

        Returns:
            CrawlerResult with popular terms
        """
        cache_key = f"google_trends_terms_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            import asyncio

            def _fetch_interest():
                pt = self._get_pytrends()
                # Build payload with novel keywords
                keywords = self.NOVEL_KEYWORDS[:5]  # Max 5 keywords per request
                pt.build_payload(keywords, cat=0, timeframe='today 3-m')

                # Get interest over time
                interest = pt.interest_over_time()

                # Get related topics
                related = pt.related_topics()

                return {
                    "interest_data": interest.to_dict() if not interest.empty else {},
                    "related_topics": related,
                }

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _fetch_interest)

            # Process related topics
            tags = []
            if data.get("related_topics"):
                for keyword, topics in data["related_topics"].items():
                    if topics and not topics.empty:
                        top_topics = topics.head(limit // 5)
                        for _, row in top_topics.iterrows():
                            tags.append({
                                "name": row.get("topic_title", ""),
                                "type": row.get("topic_type", ""),
                                "value": row.get("value", 0),
                                "keyword": keyword,
                            })

            result_data = {
                "tags": tags[:limit],
                "interest_over_time": data.get("interest_data", {}),
                "total": len(tags[:limit]),
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Google Trends terms: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_keyword_interest(
        self,
        keywords: list[str],
        timeframe: str = "today 3-m",
    ) -> CrawlerResult:
        """Get interest over time for specific keywords.

        Args:
            keywords: List of keywords to analyze (max 5)
            timeframe: Time range (e.g., "today 3-m", "today 12-m")

        Returns:
            CrawlerResult with interest data
        """
        # Limit to 5 keywords (Google Trends limit)
        keywords = keywords[:5]
        cache_key = f"google_trends_interest_{'_'.join(keywords)}_{timeframe}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            import asyncio

            def _fetch():
                pt = self._get_pytrends()
                pt.build_payload(keywords, cat=0, timeframe=timeframe)
                interest = pt.interest_over_time()
                related = pt.related_queries()
                return {
                    "interest": interest.to_dict() if not interest.empty else {},
                    "related_queries": related,
                }

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _fetch)

            result_data = {
                "keywords": keywords,
                "timeframe": timeframe,
                "interest_over_time": data.get("interest", {}),
                "related_queries": data.get("related_queries", {}),
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get keyword interest: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def compare_genres(
        self,
        genres: list[str] | None = None,
    ) -> CrawlerResult:
        """Compare interest between different genres.

        Args:
            genres: List of genre keywords to compare

        Returns:
            CrawlerResult with comparison data
        """
        if genres is None:
            genres = [
                "fantasy books",
                "science fiction books",
                "romance novels",
                "thriller books",
                "horror books",
            ]

        cache_key = f"google_trends_compare_{'_'.join(genres[:5])}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        result = await self.get_keyword_interest(genres[:5], "today 12-m")

        if result.success:
            # Process the comparison data
            interest_data = result.data.get("interest_over_time", {})

            # Calculate average interest per genre
            genre_stats = {}
            for genre in genres[:5]:
                if genre in interest_data:
                    values = list(interest_data[genre].values())
                    if values:
                        genre_stats[genre] = {
                            "average_interest": sum(values) / len(values),
                            "peak_interest": max(values),
                            "data_points": len(values),
                        }

            result_data = {
                "genres": genre_stats,
                "raw_data": interest_data,
                "timeframe": "today 12-m",
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 24)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        return result
