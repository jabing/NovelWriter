# src/crawlers/royalroad.py
"""Royal Road crawler for market research data.

Scrapes publicly available trending and popular fiction data from Royal Road.
Only accesses public pages, respects robots.txt, and uses rate limiting.
"""

import json
import logging
import re
from typing import Any

from src.novel_agent.crawlers.base import BaseCrawler, CrawlerResult
from src.novel_agent.crawlers.cache import CacheManager

logger = logging.getLogger(__name__)


class RoyalRoadCrawler(BaseCrawler):
    """Crawler for Royal Road public data.

    Crawls:
    - Best Rated fictions
    - Trending fictions
    - Rising Stars
    - Popular this week
    - Popular tags

    Note: This only accesses publicly visible data without authentication.
    """

    BASE_URL = "https://www.royalroad.com"

    # Royal Road fiction lists
    LISTS = {
        "best_rated": "/fictions/best-rated",
        "trending": "/fictions/trending",
        "rising_stars": "/fictions/rising-stars",
        "popular_weekly": "/fictions/popular-weekly",
        "active": "/fictions/active-popular",
        "complete": "/fictions/complete",
        "latest_updates": "/fictions/latest-updates",
    }

    # Genre/Fiction tags commonly used
    TAGS = [
        "action", "adventure", "comedy", "drama", "fantasy", "horror",
        "mystery", "psychological", "romance", "sci-fi", "thriller",
        "tragedy", "cultivation", "isekai", "litrpg", "magic",
        "martial-arts", "monster", "progression", "reincarnation",
        "summoned-hero", "system", "time-travel", "virtual-reality",
    ]

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        rate_limit: float = 3.0,
        **kwargs: Any,
    ) -> None:
        """Initialize Royal Road crawler.

        Args:
            cache_manager: Optional cache manager
            rate_limit: Seconds between requests
            **kwargs: Additional arguments for BaseCrawler
        """
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.cache = cache_manager or CacheManager()

    @property
    def name(self) -> str:
        return "royalroad"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending fictions from Royal Road.

        Args:
            category: List type (best_rated, trending, rising_stars, etc.)
            limit: Maximum fictions to return

        Returns:
            CrawlerResult with trending fictions
        """
        list_type = category or "trending"
        cache_key = f"royalroad_{list_type}_{limit}"

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
            # Get the appropriate list
            path = self.LISTS.get(list_type, self.LISTS["trending"])
            url = f"{self.BASE_URL}{path}"

            response = await self._make_request(url)
            html = response.text

            fictions = self._parse_fictions_from_html(html, limit)

            result_data = {
                "fictions": fictions,
                "list_type": list_type,
                "total": len(fictions),
                "url": url,
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Royal Road trending: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular tags from Royal Road.

        Args:
            limit: Maximum tags to return

        Returns:
            CrawlerResult with tag data
        """
        cache_key = f"royalroad_tags_{limit}"

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
            # Search page has tag filter
            url = f"{self.BASE_URL}/fictions/search"
            response = await self._make_request(url)
            html = response.text

            tags = self._parse_tags_from_html(html, limit)

            # If we didn't find enough, supplement with known tags
            if len(tags) < limit:
                for tag in self.TAGS:
                    if len(tags) >= limit:
                        break
                    if not any(t["name"].lower() == tag.lower() for t in tags):
                        tags.append({
                            "name": tag,
                            "url": f"{self.BASE_URL}/fictions/search?tagsAdd={tag}",
                            "source": "known_list",
                        })

            result_data = {
                "tags": tags,
                "total": len(tags),
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 24)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Royal Road tags: {e}")
            # Return known tags as fallback
            return CrawlerResult(
                success=True,
                data={
                    "tags": [{"name": t, "source": "fallback"} for t in self.TAGS[:limit]],
                    "total": min(len(self.TAGS), limit),
                },
                source=self.name,
                errors=[str(e)],
            )

    async def get_genre_stats(self) -> CrawlerResult:
        """Get genre/tag distribution statistics.

        Returns:
            CrawlerResult with genre statistics
        """
        cache_key = "royalroad_genre_stats"

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
            tag_stats = {}

            # Get fiction counts for each list type
            for list_name, path in self.LISTS.items():
                try:
                    url = f"{self.BASE_URL}{path}"
                    response = await self._make_request(url)
                    html = response.text

                    # Count fictions on page
                    fiction_count = len(re.findall(r'fiction-title', html, re.IGNORECASE))

                    tag_stats[list_name] = {
                        "fictions_on_page": fiction_count,
                        "url": url,
                    }

                except Exception as e:
                    logger.warning(f"Failed to get stats for {list_name}: {e}")

            result_data = {
                "lists": tag_stats,
                "platform": self.name,
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 24)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Royal Road genre stats: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_fiction_details(self, fiction_id: int) -> CrawlerResult:
        """Get details for a specific fiction.

        Args:
            fiction_id: Royal Road fiction ID

        Returns:
            CrawlerResult with fiction details
        """
        cache_key = f"royalroad_fiction_{fiction_id}"

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
            url = f"{self.BASE_URL}/fiction/{fiction_id}"
            response = await self._make_request(url)
            html = response.text

            details = self._parse_fiction_details(html)
            details["id"] = fiction_id
            details["url"] = url

            await self.cache.set(cache_key, details, ttl=self.cache_ttl * 24)

            return CrawlerResult(
                success=True,
                data=details,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get fiction {fiction_id}: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    def _parse_fictions_from_html(self, html: str, limit: int) -> list[dict[str, Any]]:
        """Parse fiction data from HTML.

        Args:
            html: Raw HTML content
            limit: Maximum fictions to extract

        Returns:
            List of fiction dictionaries
        """
        fictions = []
        seen_ids = set()

        # Royal Road uses a table/list structure for fiction listings

        # Pattern 1: Fiction row with title link
        fiction_pattern = re.compile(
            r'<a[^>]*href="/fiction/(\d+)[^"]*"[^>]*class="[^"]*fiction-link[^"]*"[^>]*>'
            r'([^<]+)</a>',
            re.IGNORECASE
        )

        # Pattern 2: General fiction title pattern
        title_pattern = re.compile(
            r'<a[^>]*href="/fiction/(\d+)[^"]*"[^>]*>\s*'
            r'(?:<strong[^>]*>)?([^<]+?)(?:</strong>)?\s*</a>',
            re.IGNORECASE
        )

        # Pattern 3: Look for JSON data in script tags
        json_pattern = re.compile(r'window\.INITIAL_STATE\s*=\s*(\{.*?\});', re.DOTALL)

        # Try JSON extraction first
        json_match = json_pattern.search(html)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                # Navigate to fictions data
                fictions_data = data.get("fictions", {}).get("data", [])
                for fic in fictions_data[:limit]:
                    fic_id = str(fic.get("id", ""))
                    if fic_id and fic_id not in seen_ids:
                        seen_ids.add(fic_id)
                        fictions.append({
                            "id": fic_id,
                            "title": fic.get("title", "Unknown"),
                            "author": fic.get("author", {}).get("name", "Unknown"),
                            "rating": fic.get("rating", 0),
                            "followers": fic.get("followers", 0),
                            "pages": fic.get("pages", 0),
                            "url": f"{self.BASE_URL}/fiction/{fic_id}",
                        })
            except (json.JSONDecodeError, KeyError, AttributeError):
                pass

        # Fallback to regex if JSON extraction failed
        if len(fictions) < limit:
            for pattern in [fiction_pattern, title_pattern]:
                for match in pattern.finditer(html):
                    if len(fictions) >= limit:
                        break

                    fic_id = match.group(1)
                    title = match.group(2).strip()

                    # Clean title
                    title = re.sub(r'\s+', ' ', title).strip()

                    if fic_id not in seen_ids and len(title) > 2:
                        seen_ids.add(fic_id)
                        fictions.append({
                            "id": fic_id,
                            "title": title,
                            "url": f"{self.BASE_URL}/fiction/{fic_id}",
                        })

        return fictions

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
            r'<a[^>]*href="/fictions/search\?tagsAdd=([^"&]+)[^"]*"[^>]*>\s*'
            r'([^<]+)\s*</a>',
            re.IGNORECASE
        )

        # Also look for tag badges
        badge_pattern = re.compile(
            r'<span[^>]*class="[^"]*label[^"]*"[^>]*>\s*([^<]+)\s*</span>',
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
                    "url": f"{self.BASE_URL}/fictions/search?tagsAdd={slug}",
                })

        # If we didn't find enough, try badge pattern
        if len(tags) < limit:
            for match in badge_pattern.finditer(html):
                if len(tags) >= limit:
                    break

                name = match.group(1).strip().lower()

                if name not in seen_tags and len(name) > 1 and len(name) < 30:
                    # Filter out non-tag badges
                    if not any(x in name for x in ["chapter", "page", "min", "max"]):
                        seen_tags.add(name)
                        tags.append({
                            "name": name,
                            "url": f"{self.BASE_URL}/fictions/search?tagsAdd={name}",
                        })

        return tags

    def _parse_fiction_details(self, html: str) -> dict[str, Any]:
        """Parse detailed fiction information from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Dictionary with fiction details
        """
        details = {}

        # Extract title
        title_match = re.search(r'<h1[^>]*class="[^"]*fic-header[^"]*"[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
        if title_match:
            details["title"] = title_match.group(1).strip()

        # Extract author
        author_match = re.search(r'<a[^>]*class="[^"]*author[^"]*"[^>]*>([^<]+)</a>', html, re.IGNORECASE)
        if author_match:
            details["author"] = author_match.group(1).strip()

        # Extract description
        desc_match = re.search(r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
        if desc_match:
            desc = re.sub(r'<[^>]+>', '', desc_match.group(1))
            details["description"] = desc.strip()[:500]

        # Extract stats
        rating_match = re.search(r'(\d+\.?\d*)\s*stars', html, re.IGNORECASE)
        if rating_match:
            details["rating"] = float(rating_match.group(1))

        followers_match = re.search(r'([\d,]+)\s*Followers', html, re.IGNORECASE)
        if followers_match:
            details["followers"] = int(followers_match.group(1).replace(",", ""))

        pages_match = re.search(r'([\d,]+)\s*Pages', html, re.IGNORECASE)
        if pages_match:
            details["pages"] = int(pages_match.group(1).replace(",", ""))

        # Extract tags
        tags = re.findall(r'<a[^>]*href="/fictions/search\?tagsAdd=([^"&]+)', html, re.IGNORECASE)
        if tags:
            details["tags"] = list(set(tags))

        return details

    async def get_all_lists(self, limit_per_list: int = 10) -> CrawlerResult:
        """Get data from all available lists.

        Args:
            limit_per_list: Maximum fictions per list

        Returns:
            CrawlerResult with all list data
        """
        cache_key = f"royalroad_all_lists_{limit_per_list}"

        # Check cache
        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        all_data = {}

        for list_name, _path in self.LISTS.items():
            result = await self.get_trending(list_name, limit_per_list)
            if result.success:
                all_data[list_name] = result.data

        await self.cache.set(cache_key, all_data, ttl=self.cache_ttl)

        return CrawlerResult(
            success=True,
            data={"lists": all_data, "platform": self.name},
            source=self.name,
        )
