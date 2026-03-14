# src/platforms/__init__.py
"""Platform integrations for publishing."""

from src.novel_agent.platforms.base import BasePlatform, PublishResult, PublishStatus
from src.novel_agent.platforms.formatters import PlatformFormatter
from src.novel_agent.platforms.kindle import KindlePlatform
from src.novel_agent.platforms.royalroad import RoyalRoadPlatform
from src.novel_agent.platforms.wattpad import WattpadPlatform

__all__ = [
    "BasePlatform",
    "PublishResult",
    "PublishStatus",
    "PlatformFormatter",
    "WattpadPlatform",
    "RoyalRoadPlatform",
    "KindlePlatform",
]
