# src/publishing/__init__.py
"""Novel publishing module for multiple platforms."""

from src.publishing.base import (
    BasePublisher,
    ChapterInfo,
    PublishResult,
    PublishStatus,
    StoryInfo,
)
from src.publishing.publisher_manager import PublisherManager
from src.publishing.royalroad_publisher import RoyalRoadPublisher
from src.publishing.wattpad_publisher import WattpadPublisher

__all__ = [
    "BasePublisher",
    "PublishResult",
    "PublishStatus",
    "StoryInfo",
    "ChapterInfo",
    "WattpadPublisher",
    "RoyalRoadPublisher",
    "PublisherManager",
]
