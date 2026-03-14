# src/crawlers/__init__.py
"""Web crawlers for market research data."""

from src.novel_agent.crawlers.base import BaseCrawler, CrawlerResult
from src.novel_agent.crawlers.cache import CacheManager
from src.novel_agent.crawlers.chinese_platforms import (
    ChinesePlatformCrawler,
    JinjiangCrawler,
    QidianCrawler,
    ZonghengCrawler,
)
from src.novel_agent.crawlers.google_trends import GoogleTrendsCrawler
from src.novel_agent.crawlers.playwright_crawler import (
    PLAYWRIGHT_AVAILABLE,
    PlaywrightBaseCrawler,
    PlaywrightJinjiangCrawler,
    PlaywrightQidianCrawler,
    PlaywrightRoyalRoadCrawler,
    PlaywrightWattpadCrawler,
    get_playwright_crawler,
)
from src.novel_agent.crawlers.royalroad import RoyalRoadCrawler
from src.novel_agent.crawlers.wattpad import WattpadCrawler

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
