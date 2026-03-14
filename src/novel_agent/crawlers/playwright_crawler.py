# src/crawlers/playwright_crawler.py
"""Playwright-based crawlers for dynamic content scraping.

Uses real browser for:
- JavaScript-rendered content
- Anti-bot bypass
- Login state persistence
- Form submissions (for publishing)

More reliable but slower than httpx-based crawlers.
"""

import asyncio
import logging
import random
import re
from abc import abstractmethod
from typing import Any, ClassVar, Literal

from src.novel_agent.crawlers.base import BaseCrawler, CrawlerResult
from src.novel_agent.crawlers.cache import CacheManager

logger = logging.getLogger(__name__)

# Try to import playwright
try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any  # type: ignore
    Browser = Any  # type: ignore
    BrowserContext = Any  # type: ignore
    async_playwright = Any  # type: ignore
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")


class PlaywrightBaseCrawler(BaseCrawler):
    """Base crawler using Playwright for dynamic content.

    Features:
    - Real browser rendering (JavaScript support)
    - Anti-detection measures
    - Cookie/session persistence
    - Screenshot capability
    - Form interaction
    """

    # Common anti-detection settings
    STEALTH_SCRIPT = """
    // Override navigator properties
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});

    // Override chrome property
    window.chrome = {runtime: {}};

    // Override permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    """

    # Browser launch options
    BROWSER_OPTIONS: ClassVar[dict[str, Any]] = {
        "headless": True,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ],
    }

    # Context options for anti-detection
    CONTEXT_OPTIONS: ClassVar[dict[str, Any]] = {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
    }

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        headless: bool = True,
        rate_limit: float = 3.0,
        **kwargs: Any,
    ) -> None:
        """Initialize Playwright crawler.

        Args:
            cache_manager: Optional cache manager
            headless: Run browser in headless mode
            rate_limit: Seconds between requests
            **kwargs: Additional arguments
        """
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.cache = cache_manager or CacheManager()
        self.headless = headless
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._playwright = None

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        pass

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is launched."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                **{**self.BROWSER_OPTIONS, "headless": self.headless}
            )

        return self._browser

    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with anti-detection."""
        browser = await self._ensure_browser()
        self._context = await browser.new_context(**self.CONTEXT_OPTIONS)
        return self._context

    async def _new_page(self) -> Page:
        """Create a new page with stealth measures."""
        if self._context is None:
            await self._create_context()

        page = await self._context.new_page()

        # Apply stealth measures
        await page.add_init_script(self.STEALTH_SCRIPT)

        # Set additional headers
        await page.set_extra_http_headers({
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })

        return page

    async def _navigate(
        self,
        page: Page,
        url: str,
        wait_until: "Literal['commit', 'domcontentloaded', 'load', 'networkidle']" = "domcontentloaded",
        timeout: int = 60000,
    ) -> None:
        """Navigate to URL with error handling.

        Args:
            page: Playwright page
            url: URL to navigate to
            wait_until: When to consider navigation complete
            timeout: Timeout in milliseconds
        """
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            logger.info(f"Successfully navigated to {url}")
        except Exception as e:
            logger.warning(f"Navigation warning for {url}: {e}")

    async def _wait_for_content(
        self,
        page: Page,
        selector: str | None = None,
        timeout: int = 10000,
    ) -> None:
        """Wait for content to load.

        Args:
            page: Playwright page
            selector: Optional selector to wait for
            timeout: Timeout in milliseconds
        """
        if selector:
            try:
                await page.wait_for_selector(selector, timeout=timeout)
            except Exception:
                pass  # Selector might not exist, continue anyway
        else:
            # Wait a bit for dynamic content
            await asyncio.sleep(random.uniform(0.5, 1.5))

    async def _take_screenshot(self, page: Page, name: str) -> str | None:
        """Take a screenshot for debugging.

        Args:
            page: Playwright page
            name: Screenshot name

        Returns:
            Path to screenshot or None
        """
        try:
            import os
            screenshot_dir = "data/debug_screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            path = f"{screenshot_dir}/{name}.png"
            await page.screenshot(path=path)
            return path
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {e}")
            return None

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self) -> "PlaywrightBaseCrawler":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


class PlaywrightQidianCrawler(PlaywrightBaseCrawler):
    """Playwright-based crawler for 起点中文网.

    Handles JavaScript-rendered content and anti-bot measures.
    """

    BASE_URL = "https://www.qidian.com"

    RANKINGS = {
        "hot": "/rank/hotsales",
        "yuepiao": "/rank/yuepiao",
        "newbook": "/rank/newbook",
        "collect": "/rank/collect",
        "recommend": "/rank/recommend",
    }

    @property
    def name(self) -> str:
        return "qidian_playwright"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending novels using real browser.

        Args:
            category: Ranking type (hot, yuepiao, etc.)
            limit: Maximum novels to return

        Returns:
            CrawlerResult with novel data
        """
        rank_type = category or "hot"
        cache_key = f"qidian_pw_{rank_type}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        page = None
        try:
            page = await self._new_page()

            path = self.RANKINGS.get(rank_type, self.RANKINGS["hot"])
            url = f"{self.BASE_URL}{path}"

            await self._navigate(page, url)
            await self._wait_for_content(page, ".rank-list, .book-list, .rank-view")

            # Wait a bit more for dynamic content
            await asyncio.sleep(2)

            # Extract novel data
            novels = await self._extract_novels(page, limit)

            result_data = {
                "novels": novels,
                "ranking_type": rank_type,
                "total": len(novels),
                "url": url,
                "source": "playwright",
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Playwright Qidian crawl failed: {e}")

            # Take debug screenshot
            if page:
                await self._take_screenshot(page, f"qidian_error_{rank_type}")

            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )
        finally:
            if page:
                await page.close()

    async def _extract_novels(self, page: Page, limit: int) -> list[dict[str, Any]]:
        """Extract novel data from page.

        Args:
            page: Playwright page
            limit: Maximum novels to extract

        Returns:
            List of novel dictionaries
        """
        novels = []

        # Try multiple selectors for different page layouts
        selectors = [
            # Modern rank page
            ".rank-list .book-wrap",
            ".rank-view .book-info",
            # List layout
            ".book-list li",
            ".all-img-list li",
            # Generic
            "[data-bid]",
            ".book-mid-info",
        ]

        elements = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    break
            except Exception:
                continue

        for i, elem in enumerate(elements[:limit]):
            try:
                novel = await self._extract_novel_from_element(elem, i + 1)
                if novel:
                    novels.append(novel)
            except Exception as e:
                logger.warning(f"Failed to extract novel {i}: {e}")
                continue

        return novels

    async def _extract_novel_from_element(
        self,
        elem: Any,
        rank: int,
    ) -> dict[str, Any] | None:
        """Extract single novel data from element.

        Args:
            elem: Playwright element
            rank: Ranking position

        Returns:
            Novel dictionary or None
        """
        title = ""
        author = ""
        novel_id = ""
        url = ""

        # Try to get title
        title_elem = await elem.query_selector("h4 a, .book-name, .title a, a[href*='/book/']")
        if title_elem:
            title = await title_elem.inner_text()
            href = await title_elem.get_attribute("href")
            if href:
                url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                # Extract ID from URL
                id_match = re.search(r'/book/(\d+)', href)
                if id_match:
                    novel_id = id_match.group(1)

        # Try to get author
        author_elem = await elem.query_selector(".author .name, .book-author, .author-name, a[data-bid]")
        if author_elem:
            author = await author_elem.inner_text()

        # Try to get data-bid attribute
        if not novel_id:
            bid = await elem.get_attribute("data-bid")
            if bid:
                novel_id = bid

        # Clean up data
        title = title.strip() if title else ""
        author = author.strip() if author else ""

        if not title:
            return None

        # Generate ID if not found
        if not novel_id:
            novel_id = f"unknown_{rank}"

        return {
            "id": novel_id,
            "title": title,
            "author": author,
            "url": url or f"{self.BASE_URL}/book/{novel_id}",
            "rank": rank,
        }

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular tags from Qidian."""
        # Use static data as tags rarely change
        tags = [
            {"name": "玄幻", "url": f"{self.BASE_URL}/category/1"},
            {"name": "奇幻", "url": f"{self.BASE_URL}/category/2"},
            {"name": "武侠", "url": f"{self.BASE_URL}/category/3"},
            {"name": "仙侠", "url": f"{self.BASE_URL}/category/4"},
            {"name": "都市", "url": f"{self.BASE_URL}/category/5"},
            {"name": "历史", "url": f"{self.BASE_URL}/category/6"},
            {"name": "军事", "url": f"{self.BASE_URL}/category/7"},
            {"name": "科幻", "url": f"{self.BASE_URL}/category/8"},
            {"name": "灵异", "url": f"{self.BASE_URL}/category/9"},
            {"name": "游戏", "url": f"{self.BASE_URL}/category/10"},
        ]

        return CrawlerResult(
            success=True,
            data={"tags": tags[:limit], "total": len(tags[:limit])},
            source=self.name,
        )


class PlaywrightJinjiangCrawler(PlaywrightBaseCrawler):
    """Playwright-based crawler for 晋江文学城."""

    BASE_URL = "https://www.jjwxc.net"

    @property
    def name(self) -> str:
        return "jinjiang_playwright"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending novels from Jinjiang."""
        cache_key = f"jinjiang_pw_{category or 'vipgold'}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        page = None
        try:
            page = await self._new_page()

            # Jinjiang VIP gold ranking page
            url = f"{self.BASE_URL}/topten.php?orderstr=12"

            await self._navigate(page, url)
            await self._wait_for_content(page, "table, .rank-table, .novel-list")
            await asyncio.sleep(2)

            novels = await self._extract_jinjiang_novels(page, limit)

            result_data = {
                "novels": novels,
                "total": len(novels),
                "url": url,
                "source": "playwright",
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Playwright Jinjiang crawl failed: {e}")
            if page:
                await self._take_screenshot(page, "jinjiang_error")

            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )
        finally:
            if page:
                await page.close()

    async def _extract_jinjiang_novels(
        self,
        page: Page,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Extract novels from Jinjiang page."""
        novels = []

        # Jinjiang uses table-based layout
        selectors = [
            "table tr:has(a[href*='onebook'])",
            ".novel-item",
            "[href*='onebook.php']",
        ]

        elements = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    break
            except Exception:
                continue

        for i, elem in enumerate(elements[:limit]):
            try:
                # Find the link
                link = await elem.query_selector("a[href*='onebook']")
                if not link:
                    link = elem

                title = await link.inner_text() if link else ""
                href = await link.get_attribute("href") if link else ""

                # Extract novel ID
                novel_id = ""
                if href:
                    id_match = re.search(r'novelid=(\d+)', href)
                    if id_match:
                        novel_id = id_match.group(1)

                if title and title.strip():
                    novels.append({
                        "id": novel_id or f"jj_{i}",
                        "title": title.strip(),
                        "url": f"{self.BASE_URL}/{href}" if href else "",
                        "rank": i + 1,
                    })
            except Exception:
                continue

        return novels

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular Jinjiang tags."""
        tags = [
            {"name": "甜文", "type": "风格"},
            {"name": "爽文", "type": "风格"},
            {"name": "穿越", "type": "题材"},
            {"name": "重生", "type": "题材"},
            {"name": "古代言情", "type": "分类"},
            {"name": "现代言情", "type": "分类"},
            {"name": "纯爱", "type": "分类"},
            {"name": "先婚后爱", "type": "梗"},
            {"name": "豪门世家", "type": "背景"},
            {"name": "宫廷侯爵", "type": "背景"},
        ]

        return CrawlerResult(
            success=True,
            data={"tags": tags[:limit], "total": len(tags[:limit])},
            source=self.name,
        )


class PlaywrightRoyalRoadCrawler(PlaywrightBaseCrawler):
    """Playwright-based crawler for Royal Road."""

    BASE_URL = "https://www.royalroad.com"

    LISTS = {
        "best_rated": "/fictions/best-rated",
        "trending": "/fictions/trending",
        "rising_stars": "/fictions/rising-stars",
        "popular_weekly": "/fictions/popular-weekly",
        "active": "/fictions/active-popular",
    }

    @property
    def name(self) -> str:
        return "royalroad_playwright"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending fictions from Royal Road."""
        list_type = category or "best_rated"
        cache_key = f"royalroad_pw_{list_type}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        page = None
        try:
            page = await self._new_page()

            path = self.LISTS.get(list_type, self.LISTS["best_rated"])
            url = f"{self.BASE_URL}{path}"

            await self._navigate(page, url)

            # Wait for fiction list to load
            try:
                await page.wait_for_selector(".fiction-list-item", timeout=10000)
            except Exception:
                logger.warning("Timeout waiting for .fiction-list-item selector")

            await asyncio.sleep(2)  # Additional time for JS rendering

            fictions = await self._extract_fictions(page, limit)

            result_data = {
                "fictions": fictions,
                "list_type": list_type,
                "total": len(fictions),
                "url": url,
                "source": "playwright",
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Playwright Royal Road crawl failed: {e}")
            if page:
                await self._take_screenshot(page, f"royalroad_error_{list_type}")

            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )
        finally:
            if page:
                await page.close()

    async def _extract_fictions(
        self,
        page: Page,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Extract fiction data from Royal Road page."""
        fictions = []

        # Royal Road uses .fiction-list-item for each fiction
        selectors = [
            ".fiction-list-item",
            ".fiction-list .list-item",
            "h2 a[href*='/fiction/']",
        ]

        elements = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with {selector}")
                    break
            except Exception:
                continue

        for i, elem in enumerate(elements[:limit]):
            try:
                # For fiction-list-item, find the title link inside
                if "fiction-list-item" in (await elem.evaluate("el => el.className") or ""):
                    link = await elem.query_selector("h2 a[href*='/fiction/']")
                else:
                    link = elem

                if link:
                    title = await link.inner_text()
                    href = await link.get_attribute("href") or ""

                    # Extract fiction ID
                    fic_id = ""
                    id_match = re.search(r'/fiction/(\d+)', href)
                    if id_match:
                        fic_id = id_match.group(1)

                    if title and title.strip():
                        fictions.append({
                            "id": fic_id or f"rr_{i}",
                            "title": title.strip(),
                            "url": f"{self.BASE_URL}{href}" if href.startswith("/") else href,
                            "rank": i + 1,
                        })
            except Exception as e:
                logger.warning(f"Failed to extract fiction {i}: {e}")
                continue

        return fictions

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular Royal Road tags."""
        tags = [
            {"name": "action"}, {"name": "adventure"}, {"name": "comedy"},
            {"name": "drama"}, {"name": "fantasy"}, {"name": "horror"},
            {"name": "mystery"}, {"name": "romance"}, {"name": "sci-fi"},
            {"name": "litrpg"}, {"name": "cultivation"}, {"name": "isekai"},
        ]

        return CrawlerResult(
            success=True,
            data={"tags": tags[:limit], "total": len(tags[:limit])},
            source=self.name,
        )


class PlaywrightWattpadCrawler(PlaywrightBaseCrawler):
    """Playwright-based crawler for Wattpad."""

    BASE_URL = "https://www.wattpad.com"

    @property
    def name(self) -> str:
        return "wattpad_playwright"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending stories from Wattpad."""
        cache_key = f"wattpad_pw_{category or 'all'}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        page = None
        try:
            page = await self._new_page()

            url = f"{self.BASE_URL}/stories"
            if category:
                url += f"/{category}"

            await self._navigate(page, url)
            await self._wait_for_content(page, ".story-card, .browse-story-item, article")
            await asyncio.sleep(2)

            stories = await self._extract_stories(page, limit)

            result_data = {
                "stories": stories,
                "total": len(stories),
                "url": url,
                "source": "playwright",
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Playwright Wattpad crawl failed: {e}")
            if page:
                await self._take_screenshot(page, "wattpad_error")

            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )
        finally:
            if page:
                await page.close()

    async def _extract_stories(
        self,
        page: Page,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Extract story data from Wattpad page."""
        stories = []

        selectors = [
            ".story-card",
            ".browse-story-item",
            "article",
            "[data-story-id]",
        ]

        elements = []
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    break
            except Exception:
                continue

        for i, elem in enumerate(elements[:limit]):
            try:
                link = await elem.query_selector("a[href*='/story/']")
                if link:
                    title = await link.inner_text()
                    href = await link.get_attribute("href") or ""

                    story_id = ""
                    id_match = re.search(r'/story/(\d+)', href)
                    if id_match:
                        story_id = id_match.group(1)

                    if title and title.strip():
                        stories.append({
                            "id": story_id or f"wp_{i}",
                            "title": title.strip(),
                            "url": f"{self.BASE_URL}{href}" if href.startswith("/") else href,
                            "rank": i + 1,
                        })
            except Exception:
                continue

        return stories

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular Wattpad tags."""
        tags = [
            {"name": "romance"}, {"name": "fantasy"}, {"name": "werewolf"},
            {"name": "vampire"}, {"name": "fanfiction"}, {"name": "teen-fiction"},
            {"name": "billionaire"}, {"name": "bad-boy"}, {"name": "love"},
            {"name": "completed"},
        ]

        return CrawlerResult(
            success=True,
            data={"tags": tags[:limit], "total": len(tags[:limit])},
            source=self.name,
        )


# Factory function for easy crawler selection
def get_playwright_crawler(platform: str, **kwargs: Any) -> PlaywrightBaseCrawler:
    """Get appropriate Playwright crawler for platform.

    Args:
        platform: Platform name (qidian, jinjiang, royalroad, wattpad)
        **kwargs: Additional arguments for crawler

    Returns:
        Playwright crawler instance
    """
    crawlers = {
        "qidian": PlaywrightQidianCrawler,
        "jinjiang": PlaywrightJinjiangCrawler,
        "royalroad": PlaywrightRoyalRoadCrawler,
        "wattpad": PlaywrightWattpadCrawler,
    }

    crawler_class = crawlers.get(platform.lower())
    if not crawler_class:
        raise ValueError(f"Unknown platform: {platform}. Available: {list(crawlers.keys())}")

    return crawler_class(**kwargs)
