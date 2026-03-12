# src/crawlers/wattpad.py
"""Wattpad crawler for market research data.

Scrapes publicly available trending and popular story data from Wattpad.
Only accesses public pages, respects robots.txt, and uses rate limiting.
"""

import json
import logging
import re
from typing import Any
from urllib.parse import quote

from src.crawlers.base import BaseCrawler, CrawlerResult
from src.crawlers.cache import CacheManager

logger = logging.getLogger(__name__)


class WattpadCrawler(BaseCrawler):
    """Crawler for Wattpad public data.

    Crawls:
    - Trending stories by genre
    - Popular tags
    - Story metadata (public only)

    Note: This only accesses publicly visible data without authentication.
    """

    BASE_URL = "https://www.wattpad.com"

    # Genre mapping for Wattpad
    GENRES = {
        "fantasy": "fantasy",
        "scifi": "science-fiction",
        "romance": "romance",
        "historical": "historical-fiction",
        "adventure": "adventure",
        "mystery": "mystery",
        "thriller": "thriller",
        "horror": "horror",
        "teen": "teen-fiction",
        "fanfiction": "fanfiction",
    }

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        rate_limit: float = 3.0,  # Be extra polite to Wattpad
        **kwargs: Any,
    ) -> None:
        """Initialize Wattpad crawler.

        Args:
            cache_manager: Optional cache manager
            rate_limit: Seconds between requests
            **kwargs: Additional arguments for BaseCrawler
        """
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.cache = cache_manager or CacheManager()

    @property
    def name(self) -> str:
        return "wattpad"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending stories from Wattpad.

        Args:
            category: Genre category (optional)
            limit: Maximum stories to return

        Returns:
            CrawlerResult with trending stories
        """
        cache_key = f"wattpad_trending_{category or 'all'}_{limit}"

        # Check cache first
        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            # Build URL for browse page
            if category and category in self.GENRES:
                url = f"{self.BASE_URL}/stories/{self.GENRES[category]}"
            else:
                url = f"{self.BASE_URL}/stories"

            response = await self._make_request(url)
            html = response.text

            # Parse trending stories from HTML
            stories = self._parse_stories_from_html(html, limit)

            result_data = {
                "stories": stories,
                "category": category,
                "total": len(stories),
                "url": url,
            }

            # Cache the results
            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Wattpad trending: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular tags from Wattpad.

        Args:
            limit: Maximum tags to return

        Returns:
            CrawlerResult with tag data
        """
        cache_key = f"wattpad_tags_{limit}"

        # Check cache first
        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            # Wattpad has a tags page
            url = f"{self.BASE_URL}/stories"
            response = await self._make_request(url)
            html = response.text

            # Parse tags from HTML
            tags = self._parse_tags_from_html(html, limit)

            result_data = {
                "tags": tags,
                "total": len(tags),
            }

            # Cache the results
            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Wattpad tags: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_genre_stats(self) -> CrawlerResult:
        """Get genre distribution statistics.

        Returns:
            CrawlerResult with genre statistics
        """
        cache_key = "wattpad_genre_stats"

        # Check cache first
        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            genre_data = {}

            # Sample each genre to get approximate counts
            for genre, slug in list(self.GENRES.items())[:5]:  # Limit to 5 genres to be polite
                try:
                    url = f"{self.BASE_URL}/stories/{slug}"
                    response = await self._make_request(url)
                    html = response.text

                    # Extract story count if available
                    count_match = re.search(r'(\d+(?:,\d+)*)\s*(?:Stories|stories)', html)
                    story_count = 0
                    if count_match:
                        story_count = int(count_match.group(1).replace(",", ""))

                    genre_data[genre] = {
                        "slug": slug,
                        "estimated_stories": story_count,
                        "url": url,
                    }

                except Exception as e:
                    logger.warning(f"Failed to get stats for {genre}: {e}")
                    genre_data[genre] = {
                        "slug": slug,
                        "estimated_stories": 0,
                        "error": str(e),
                    }

            result_data = {
                "genres": genre_data,
                "platform": self.name,
            }

            # Cache for longer since this data changes slowly
            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 24)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Wattpad genre stats: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    def _parse_stories_from_html(self, html: str, limit: int) -> list[dict[str, Any]]:
        """Parse story data from HTML.

        Args:
            html: Raw HTML content
            limit: Maximum stories to extract

        Returns:
            List of story dictionaries
        """
        stories = []

        # Look for story cards/links in the HTML
        # Wattpad uses various patterns, we'll look for common ones

        # Pattern 1: Story links in browse results
        story_pattern = re.compile(
            r'<a[^>]*href="/story/(\d+)[^"]*"[^>]*>\s*'
            r'(?:<[^>]*>)*([^<]+?)(?:</[^>]*>)*\s*</a>',
            re.IGNORECASE | re.DOTALL
        )

        # Pattern 2: Story cards with title
        re.compile(
            r'<div[^>]*class="[^"]*story-card[^"]*"[^>]*>.*?'
            r'<a[^>]*href="(/story/\d+[^"]*)"[^>]*>.*?'
            r'(<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>.*?)?'
            r'</div>',
            re.IGNORECASE | re.DOTALL
        )

        # Try to extract story IDs and titles
        seen_ids = set()

        # Method 1: Look for JSON data embedded in page
        json_pattern = re.compile(r'"stories"\s*:\s*(\[.*?\])', re.DOTALL)
        json_match = json_pattern.search(html)

        if json_match:
            try:
                stories_data = json.loads(json_match.group(1))
                for story in stories_data[:limit]:
                    story_id = story.get("id") or story.get("storyId")
                    if story_id and str(story_id) not in seen_ids:
                        seen_ids.add(str(story_id))
                        stories.append({
                            "id": str(story_id),
                            "title": story.get("title", "Unknown"),
                            "reads": story.get("readCount", 0),
                            "votes": story.get("voteCount", 0),
                            "chapters": story.get("numParts", 0),
                            "author": story.get("user", {}).get("name", "Unknown"),
                            "url": f"{self.BASE_URL}/story/{story_id}",
                        })
            except (json.JSONDecodeError, KeyError):
                pass

        # Method 2: Fallback to regex parsing if JSON extraction failed
        if len(stories) < limit:
            for match in story_pattern.finditer(html):
                if len(stories) >= limit:
                    break

                story_id = match.group(1)
                title = match.group(2).strip()

                # Clean up title
                title = re.sub(r'\s+', ' ', title).strip()

                if story_id not in seen_ids and len(title) > 2:
                    seen_ids.add(story_id)
                    stories.append({
                        "id": story_id,
                        "title": title,
                        "url": f"{self.BASE_URL}/story/{story_id}",
                    })

        return stories

    def _parse_tags_from_html(self, html: str, limit: int) -> list[dict[str, Any]]:
        """Parse tag data from HTML.

        Args:
            html: Raw HTML content
            limit: Maximum tags to extract

        Returns:
            List of tag dictionaries
        """
        tags = []
        seen_tags = set()

        # Look for tag links
        tag_pattern = re.compile(
            r'<a[^>]*href="/stories/([^"]+)"[^>]*>\s*'
            r'#?(\w[\w\s-]+\w)\s*</a>',
            re.IGNORECASE
        )

        # Also look for tag elements
        tag_class_pattern = re.compile(
            r'<[^>]*class="[^"]*tag[^"]*"[^>]*>([^<]+)</[^>]*>',
            re.IGNORECASE
        )

        for match in tag_pattern.finditer(html):
            if len(tags) >= limit:
                break

            slug = match.group(1)
            name = match.group(2).strip().lower()

            if name not in seen_tags and len(name) > 1:
                seen_tags.add(name)
                tags.append({
                    "name": name,
                    "slug": slug,
                    "url": f"{self.BASE_URL}/stories/{slug}",
                })

        # If we didn't find enough, try the class pattern
        if len(tags) < limit:
            for match in tag_class_pattern.finditer(html):
                if len(tags) >= limit:
                    break

                name = match.group(1).strip().lstrip('#').lower()

                if name not in seen_tags and len(name) > 1 and name.isalnum():
                    seen_tags.add(name)
                    tags.append({
                        "name": name,
                        "url": f"{self.BASE_URL}/stories/{name}",
                    })

        return tags

    async def search_stories(
        self,
        query: str,
        limit: int = 20,
    ) -> CrawlerResult:
        """Search for stories on Wattpad.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            CrawlerResult with search results
        """
        cache_key = f"wattpad_search_{query}_{limit}"

        # Check cache
        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            # Wattpad search URL
            encoded_query = quote(query)
            url = f"{self.BASE_URL}/search/{encoded_query}"

            response = await self._make_request(url)
            html = response.text

            stories = self._parse_stories_from_html(html, limit)

            result_data = {
                "stories": stories,
                "query": query,
                "total": len(stories),
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to search Wattpad: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )
