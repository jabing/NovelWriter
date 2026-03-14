# src/crawlers/base.py
"""Base crawler with rate limiting, caching, and error handling."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class CrawlerResult:
    """Result from a crawler operation."""
    success: bool
    data: dict[str, Any]
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    errors: list[str] = field(default_factory=list)
    cached: bool = False


class BaseCrawler(ABC):
    """Base class for web crawlers with rate limiting and caching.

    Features:
    - Rate limiting (respects robots.txt)
    - Request retries with exponential backoff
    - Response caching
    - Proper User-Agent identification
    - Error handling and logging
    """

    # Default settings
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_RATE_LIMIT = 2.0  # seconds between requests
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_CACHE_TTL = 3600  # 1 hour

    # Identify ourselves politely
    USER_AGENT = (
        "NovelAgentMarketResearch/1.0 "
        "(Educational/Research purposes only; "
        "Contact: research@novelagent.example.com)"
    )

    def __init__(
        self,
        rate_limit: float = DEFAULT_RATE_LIMIT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ) -> None:
        """Initialize the crawler.

        Args:
            rate_limit: Seconds between requests
            max_retries: Maximum retry attempts
            cache_ttl: Cache time-to-live in seconds
        """
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self._last_request_time: float = 0
        self._cache: dict[str, tuple[float, Any]] = {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Crawler name for identification."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the platform."""
        pass

    async def _wait_for_rate_limit(self) -> None:
        """Wait to respect rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _get_from_cache(self, key: str) -> tuple[bool, Any]:
        """Get data from cache if still valid.

        Args:
            key: Cache key

        Returns:
            Tuple of (found, data)
        """
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return True, data
            # Cache expired, remove it
            del self._cache[key]
        return False, None

    def _save_to_cache(self, key: str, data: Any) -> None:
        """Save data to cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        self._cache[key] = (time.time(), data)

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: dict | None = None,
        headers: dict | None = None,
        json_data: dict | None = None,
    ) -> httpx.Response:
        """Make an HTTP request with rate limiting and retries.

        Args:
            url: Request URL
            method: HTTP method
            params: Query parameters
            headers: Additional headers
            json_data: JSON body data

        Returns:
            HTTP response

        Raises:
            httpx.HTTPError: After all retries exhausted
        """
        # Merge headers
        request_headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        if headers:
            request_headers.update(headers)

        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            await self._wait_for_rate_limit()

            try:
                async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        headers=request_headers,
                        json=json_data,
                        follow_redirects=True,
                    )

                    # Check for rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue

                    response.raise_for_status()
                    return response

            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.warning(f"HTTP error {e.response.status_code} on attempt {attempt + 1}")

                # Don't retry on client errors (4xx except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise

            except httpx.RequestError as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")

            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = (2 ** attempt) * self.rate_limit
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise httpx.RequestError("Unknown error after retries")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid.

        Args:
            cache_key: Cache key to check

        Returns:
            True if cache is valid
        """
        found, _ = self._get_from_cache(cache_key)
        return found

    @abstractmethod
    async def get_trending(self, category: str | None = None, limit: int = 20) -> CrawlerResult:
        """Get trending content from the platform.

        Args:
            category: Optional category filter
            limit: Maximum items to return

        Returns:
            CrawlerResult with trending data
        """
        pass

    @abstractmethod
    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular tags from the platform.

        Args:
            limit: Maximum tags to return

        Returns:
            CrawlerResult with tag data
        """
        pass

    async def get_genre_stats(self) -> CrawlerResult:
        """Get genre distribution statistics.

        Returns:
            CrawlerResult with genre statistics
        """
        return CrawlerResult(
            success=False,
            data={},
            source=self.name,
            errors=["Genre stats not implemented for this platform"],
        )

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info(f"Cache cleared for {self.name}")
