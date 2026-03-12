# src/crawlers/chinese_platforms.py
"""Chinese novel platforms crawlers.

Crawls public ranking data from:
- 起点中文网 (Qidian)
- 晋江文学城 (Jinjiang)
- 纵横中文网 (Zongheng)
- 17K小说网

Note: These platforms may have anti-scraping measures.
Uses polite rate limiting and caching to minimize impact.
"""

import logging
import re
from typing import Any

from src.crawlers.base import BaseCrawler, CrawlerResult
from src.crawlers.cache import CacheManager

logger = logging.getLogger(__name__)


class QidianCrawler(BaseCrawler):
    """Crawler for 起点中文网 (Qidian Chinese Network).

    Crawls:
    - 热门榜单 (Hot rankings)
    - 月票榜 (Monthly ticket rankings)
    - 新书榜 (New book rankings)
    """

    BASE_URL = "https://www.qidian.com"

    # Available ranking lists
    RANKINGS = {
        "hot": "/rank/hotsales",        # 畅销榜
        "yuepiao": "/rank/yuepiao",     # 月票榜
        "newbook": "/rank/newbook",     # 新书榜
        "collect": "/rank/collect",     # 收藏榜
        "recommend": "/rank/recommend", # 推荐榜
        "sign": "/rank/sign",           # 签约榜
    }

    # Category IDs
    CATEGORIES = {
        "xuanhuan": 1,      # 玄幻
        "qihuan": 2,        # 奇幻
        "wuxia": 3,         # 武侠
        "xianxia": 4,       # 仙侠
        "dushi": 5,         # 都市
        "lishi": 6,         # 历史
        "junshi": 7,        # 军事
        "kehuan": 8,        # 科幻
        "lingyi": 9,        # 灵异
        "youxi": 10,        # 游戏
    }

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        rate_limit: float = 5.0,  # Be extra polite
        **kwargs: Any,
    ) -> None:
        """Initialize Qidian crawler."""
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.cache = cache_manager or CacheManager()

    @property
    def name(self) -> str:
        return "qidian"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    def _get_chrome_headers(self) -> dict[str, str]:
        """Get headers mimicking Chrome browser."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending novels from Qidian.

        Args:
            category: Ranking type (hot, yuepiao, newbook, etc.)
            limit: Maximum novels to return

        Returns:
            CrawlerResult with novel data
        """
        rank_type = category or "hot"
        cache_key = f"qidian_{rank_type}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            path = self.RANKINGS.get(rank_type, self.RANKINGS["hot"])
            url = f"{self.BASE_URL}{path}"

            response = await self._make_request(
                url,
                headers=self._get_chrome_headers(),
            )
            html = response.text

            novels = self._parse_novels_from_html(html, limit)

            result_data = {
                "novels": novels,
                "ranking_type": rank_type,
                "total": len(novels),
                "url": url,
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Qidian trending: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular tags/categories from Qidian.

        Args:
            limit: Maximum tags to return

        Returns:
            CrawlerResult with tag data
        """
        cache_key = f"qidian_tags_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        # Use predefined categories as tags
        tags = [
            {"name": "玄幻", "category_id": 1, "url": f"{self.BASE_URL}/category/1"},
            {"name": "奇幻", "category_id": 2, "url": f"{self.BASE_URL}/category/2"},
            {"name": "武侠", "category_id": 3, "url": f"{self.BASE_URL}/category/3"},
            {"name": "仙侠", "category_id": 4, "url": f"{self.BASE_URL}/category/4"},
            {"name": "都市", "category_id": 5, "url": f"{self.BASE_URL}/category/5"},
            {"name": "历史", "category_id": 6, "url": f"{self.BASE_URL}/category/6"},
            {"name": "军事", "category_id": 7, "url": f"{self.BASE_URL}/category/7"},
            {"name": "科幻", "category_id": 8, "url": f"{self.BASE_URL}/category/8"},
            {"name": "灵异", "category_id": 9, "url": f"{self.BASE_URL}/category/9"},
            {"name": "游戏", "category_id": 10, "url": f"{self.BASE_URL}/category/10"},
        ]

        result_data = {
            "tags": tags[:limit],
            "total": len(tags[:limit]),
        }

        await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 24)

        return CrawlerResult(
            success=True,
            data=result_data,
            source=self.name,
        )

    def _parse_novels_from_html(self, html: str, limit: int) -> list[dict[str, Any]]:
        """Parse novel data from Qidian HTML.

        Args:
            html: Raw HTML content
            limit: Maximum novels to extract

        Returns:
            List of novel dictionaries
        """
        novels = []
        seen_ids = set()

        # Pattern 1: Book info div
        book_pattern = re.compile(
            r'<div[^>]*class="[^"]*book-mid-info[^"]*"[^>]*>.*?'
            r'<h4[^>]*><a[^>]*href="([^"]+)"[^>]*data-bid="(\d+)"[^>]*>([^<]+)</a></h4>.*?'
            r'<p[^>]*class="[^"]*author[^"]*"[^>]*>.*?'
            r'<a[^>]*class="[^"]*name[^"]*"[^>]*>([^<]+)</a>.*?'
            r'</div>',
            re.IGNORECASE | re.DOTALL
        )

        # Pattern 2: List item pattern
        list_pattern = re.compile(
            r'<li[^>]*data-bid="(\d+)"[^>]*>.*?'
            r'<a[^>]*class="[^"]*book-name[^"]*"[^>]*>([^<]+)</a>.*?'
            r'<a[^>]*class="[^"]*author[^"]*"[^>]*>([^<]+)</a>',
            re.IGNORECASE | re.DOTALL
        )

        # Try list pattern first
        for match in list_pattern.finditer(html):
            if len(novels) >= limit:
                break

            book_id = match.group(1)
            title = match.group(2).strip()
            author = match.group(3).strip()

            if book_id not in seen_ids:
                seen_ids.add(book_id)
                novels.append({
                    "id": book_id,
                    "title": title,
                    "author": author,
                    "url": f"{self.BASE_URL}/book/{book_id}",
                })

        # Try book info pattern
        if len(novels) < limit:
            for match in book_pattern.finditer(html):
                if len(novels) >= limit:
                    break

                url_path = match.group(1)
                book_id = match.group(2)
                title = match.group(3).strip()
                author = match.group(4).strip()

                if book_id not in seen_ids:
                    seen_ids.add(book_id)
                    novels.append({
                        "id": book_id,
                        "title": title,
                        "author": author,
                        "url": f"{self.BASE_URL}{url_path}",
                    })

        return novels


class JinjiangCrawler(BaseCrawler):
    """Crawler for 晋江文学城 (Jinjiang Literature City).

    Crawls:
    - 原创金榜 (Original gold ranking)
    - 季度排行榜 (Quarterly ranking)
    - 分类排行榜 (Category rankings)
    """

    BASE_URL = "https://www.jjwxc.net"
    WAP_URL = "https://wap.jjwxc.net"

    # Ranking types
    RANKINGS = {
        "vipgold": "/ranks/vipgold/yc",      # VIP金榜
        "monthly": "/topten.php?orderstr=1",  # 月榜
        "quarterly": "/topten.php?orderstr=4", # 季榜
        "yearly": "/topten.php?orderstr=5",   # 年榜
        "total": "/topten.php?orderstr=6",    # 总榜
    }

    # Categories
    CATEGORIES = {
        "gudai": "古代言情",
        "xiandai": "现代言情",
        "chuanji": "穿越架空",
        "xuanhuan": "玄幻仙侠",
        "chunai": "纯爱",
        "yansheng": "衍生",
    }

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        rate_limit: float = 5.0,
        **kwargs: Any,
    ) -> None:
        """Initialize Jinjiang crawler."""
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.cache = cache_manager or CacheManager()

    @property
    def name(self) -> str:
        return "jinjiang"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    def _get_chrome_headers(self) -> dict[str, str]:
        """Get headers mimicking Chrome browser."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending novels from Jinjiang.

        Args:
            category: Ranking type (vipgold, monthly, quarterly, etc.)
            limit: Maximum novels to return

        Returns:
            CrawlerResult with novel data
        """
        rank_type = category or "vipgold"
        cache_key = f"jinjiang_{rank_type}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            # Use WAP version for simpler parsing
            if rank_type == "vipgold":
                url = f"{self.WAP_URL}{self.RANKINGS['vipgold']}"
            else:
                url = f"{self.BASE_URL}{self.RANKINGS.get(rank_type, self.RANKINGS['vipgold'])}"

            response = await self._make_request(
                url,
                headers=self._get_chrome_headers(),
            )
            html = response.text

            novels = self._parse_novels_from_html(html, limit)

            result_data = {
                "novels": novels,
                "ranking_type": rank_type,
                "total": len(novels),
                "url": url,
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Jinjiang trending: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular tags from Jinjiang.

        Args:
            limit: Maximum tags to return

        Returns:
            CrawlerResult with tag data
        """
        cache_key = f"jinjiang_tags_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        # Jinjiang popular tags
        tags = [
            {"name": "甜文", "type": "风格"},
            {"name": "爽文", "type": "风格"},
            {"name": "穿越", "type": "题材"},
            {"name": "重生", "type": "题材"},
            {"name": "系统", "type": "元素"},
            {"name": "先婚后爱", "type": "梗"},
            {"name": "豪门世家", "type": "背景"},
            {"name": "宫廷侯爵", "type": "背景"},
            {"name": "情有独钟", "type": "情感"},
            {"name": "强强", "type": "情感"},
        ]

        result_data = {
            "tags": tags[:limit],
            "total": len(tags[:limit]),
        }

        await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 24)

        return CrawlerResult(
            success=True,
            data=result_data,
            source=self.name,
        )

    def _parse_novels_from_html(self, html: str, limit: int) -> list[dict[str, Any]]:
        """Parse novel data from Jinjiang HTML.

        Args:
            html: Raw HTML content
            limit: Maximum novels to extract

        Returns:
            List of novel dictionaries
        """
        novels = []
        seen_ids = set()

        # Pattern for novel links with ID
        novel_pattern = re.compile(
            r'<a[^>]*href="[^"]*onebook\.php\?novelid=(\d+)"[^>]*>([^<]+)</a>',
            re.IGNORECASE
        )

        # Pattern for WAP version
        wap_pattern = re.compile(
            r'<a[^>]*href="/book/(\d+)"[^>]*>.*?<span[^>]*>([^<]+)</span>',
            re.IGNORECASE | re.DOTALL
        )

        # Try standard pattern
        for match in novel_pattern.finditer(html):
            if len(novels) >= limit:
                break

            novel_id = match.group(1)
            title = match.group(2).strip()

            if novel_id not in seen_ids and len(title) > 1:
                seen_ids.add(novel_id)
                novels.append({
                    "id": novel_id,
                    "title": title,
                    "url": f"{self.BASE_URL}/onebook.php?novelid={novel_id}",
                })

        # Try WAP pattern
        if len(novels) < limit:
            for match in wap_pattern.finditer(html):
                if len(novels) >= limit:
                    break

                novel_id = match.group(1)
                title = match.group(2).strip()

                if novel_id not in seen_ids and len(title) > 1:
                    seen_ids.add(novel_id)
                    novels.append({
                        "id": novel_id,
                        "title": title,
                        "url": f"{self.BASE_URL}/onebook.php?novelid={novel_id}",
                    })

        return novels


class ZonghengCrawler(BaseCrawler):
    """Crawler for 纵横中文网.

    Crawls ranking data from Zongheng.
    """

    BASE_URL = "https://www.zongheng.com"

    RANKINGS = {
        "hot": "/rank/details.html?rankType=1",    # 热销榜
        "monthly": "/rank/details.html?rankType=2", # 月票榜
        "newbook": "/rank/details.html?rankType=3", # 新书榜
        "collect": "/rank/details.html?rankType=4", # 收藏榜
    }

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        rate_limit: float = 5.0,
        **kwargs: Any,
    ) -> None:
        """Initialize Zongheng crawler."""
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.cache = cache_manager or CacheManager()

    @property
    def name(self) -> str:
        return "zongheng"

    @property
    def base_url(self) -> str:
        return self.BASE_URL

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending novels from Zongheng."""
        rank_type = category or "hot"
        cache_key = f"zongheng_{rank_type}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        try:
            path = self.RANKINGS.get(rank_type, self.RANKINGS["hot"])
            url = f"{self.BASE_URL}{path}"

            response = await self._make_request(url)
            html = response.text

            novels = self._parse_novels_from_html(html, limit)

            result_data = {
                "novels": novels,
                "ranking_type": rank_type,
                "total": len(novels),
                "url": url,
            }

            await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

            return CrawlerResult(
                success=True,
                data=result_data,
                source=self.name,
            )

        except Exception as e:
            logger.error(f"Failed to get Zongheng trending: {e}")
            return CrawlerResult(
                success=False,
                data={},
                source=self.name,
                errors=[str(e)],
            )

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get popular tags from Zongheng."""
        cache_key = f"zongheng_tags_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        tags = [
            {"name": "玄幻", "type": "类型"},
            {"name": "奇幻", "type": "类型"},
            {"name": "都市", "type": "类型"},
            {"name": "历史", "type": "类型"},
            {"name": "武侠", "type": "类型"},
            {"name": "仙侠", "type": "类型"},
        ]

        result_data = {"tags": tags[:limit], "total": len(tags[:limit])}
        await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 24)

        return CrawlerResult(
            success=True,
            data=result_data,
            source=self.name,
        )

    def _parse_novels_from_html(self, html: str, limit: int) -> list[dict[str, Any]]:
        """Parse novel data from Zongheng HTML."""
        novels = []
        seen_ids = set()

        # Pattern for book links
        book_pattern = re.compile(
            r'<a[^>]*href="https?://www\.zongheng\.com/book/(\d+)\.html"[^>]*>([^<]+)</a>',
            re.IGNORECASE
        )

        for match in book_pattern.finditer(html):
            if len(novels) >= limit:
                break

            book_id = match.group(1)
            title = match.group(2).strip()

            if book_id not in seen_ids and len(title) > 1:
                seen_ids.add(book_id)
                novels.append({
                    "id": book_id,
                    "title": title,
                    "url": f"{self.BASE_URL}/book/{book_id}.html",
                })

        return novels


# Combined crawler for all Chinese platforms
class ChinesePlatformCrawler(BaseCrawler):
    """Combined crawler for all Chinese novel platforms.

    Aggregates data from:
    - 起点 (Qidian)
    - 晋江 (Jinjiang)
    - 纵横 (Zongheng)
    """

    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize combined crawler."""
        super().__init__(**kwargs)
        self.cache = cache_manager or CacheManager()
        self._qidian = None
        self._jinjiang = None
        self._zongheng = None

    @property
    def name(self) -> str:
        return "chinese_platforms"

    @property
    def base_url(self) -> str:
        return "https://www.qidian.com"  # Primary platform

    @property
    def qidian(self) -> QidianCrawler:
        if self._qidian is None:
            self._qidian = QidianCrawler(self.cache)
        return self._qidian

    @property
    def jinjiang(self) -> JinjiangCrawler:
        if self._jinjiang is None:
            self._jinjiang = JinjiangCrawler(self.cache)
        return self._jinjiang

    @property
    def zongheng(self) -> ZonghengCrawler:
        if self._zongheng is None:
            self._zongheng = ZonghengCrawler(self.cache)
        return self._zongheng

    async def get_trending(
        self,
        category: str | None = None,
        limit: int = 20,
    ) -> CrawlerResult:
        """Get trending from all platforms.

        Args:
            category: Platform name (qidian, jinjiang, zongheng) or None for all
            limit: Maximum novels per platform

        Returns:
            CrawlerResult with aggregated data
        """
        cache_key = f"chinese_all_{category or 'all'}_{limit}"

        found, cached = await self.cache.get(cache_key)
        if found:
            return CrawlerResult(
                success=True,
                data=cached,
                source=self.name,
                cached=True,
            )

        results = {}

        if category is None or category == "qidian":
            qidian_result = await self.qidian.get_trending(limit=limit)
            if qidian_result.success:
                results["qidian"] = qidian_result.data

        if category is None or category == "jinjiang":
            jinjiang_result = await self.jinjiang.get_trending(limit=limit)
            if jinjiang_result.success:
                results["jinjiang"] = jinjiang_result.data

        if category is None or category == "zongheng":
            zongheng_result = await self.zongheng.get_trending(limit=limit)
            if zongheng_result.success:
                results["zongheng"] = zongheng_result.data

        result_data = {
            "platforms": results,
            "total_platforms": len(results),
        }

        await self.cache.set(cache_key, result_data, ttl=self.cache_ttl * 6)

        return CrawlerResult(
            success=len(results) > 0,
            data=result_data,
            source=self.name,
        )

    async def get_popular_tags(self, limit: int = 50) -> CrawlerResult:
        """Get aggregated popular tags."""
        all_tags = []

        qidian_result = await self.qidian.get_popular_tags(limit=limit // 3)
        if qidian_result.success:
            for tag in qidian_result.data.get("tags", []):
                tag["platform"] = "qidian"
                all_tags.append(tag)

        jinjiang_result = await self.jinjiang.get_popular_tags(limit=limit // 3)
        if jinjiang_result.success:
            for tag in jinjiang_result.data.get("tags", []):
                tag["platform"] = "jinjiang"
                all_tags.append(tag)

        return CrawlerResult(
            success=True,
            data={"tags": all_tags[:limit], "total": len(all_tags[:limit])},
            source=self.name,
        )
