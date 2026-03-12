# src/platforms/__init__.py
"""Platform integrations for publishing."""

from src.platforms.base import BasePlatform, PublishResult, PublishStatus
from src.platforms.formatters import PlatformFormatter
from src.platforms.kindle import KindlePlatform
from src.platforms.royalroad import RoyalRoadPlatform
from src.platforms.wattpad import WattpadPlatform

__all__ = [
    "BasePlatform",
    "PublishResult",
    "PublishStatus",
    "PlatformFormatter",
    "WattpadPlatform",
    "RoyalRoadPlatform",
    "KindlePlatform",
]
