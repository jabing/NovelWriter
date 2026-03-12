# src/crawlers/__init__.py
"""Web crawlers for market research data."""

from src.crawlers.base import BaseCrawler, CrawlerResult
from src.crawlers.cache import CacheManager
from src.crawlers.chinese_platforms import (
    ChinesePlatformCrawler,
    JinjiangCrawler,
    QidianCrawler,
    ZonghengCrawler,
)
from src.crawlers.google_trends import GoogleTrendsCrawler
from src.crawlers.playwright_crawler import (
    PLAYWRIGHT_AVAILABLE,
    PlaywrightBaseCrawler,
    PlaywrightJinjiangCrawler,
    PlaywrightQidianCrawler,
    PlaywrightRoyalRoadCrawler,
    PlaywrightWattpadCrawler,
    get_playwright_crawler,
)
from src.crawlers.royalroad import RoyalRoadCrawler
from src.crawlers.wattpad import WattpadCrawler

__all__ = [
    "BaseCrawler",
    "CrawlerResult",
    "CacheManager",
    "WattpadCrawler",
    "RoyalRoadCrawler",
    "GoogleTrendsCrawler",
    "QidianCrawler",
    "JinjiangCrawler",
    "ZonghengCrawler",
    "ChinesePlatformCrawler",
    "PLAYWRIGHT_AVAILABLE",
    "PlaywrightBaseCrawler",
    "PlaywrightQidianCrawler",
    "PlaywrightJinjiangCrawler",
    "PlaywrightRoyalRoadCrawler",
    "PlaywrightWattpadCrawler",
    "get_playwright_crawler",
]
