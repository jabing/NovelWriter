# src/publishing/__init__.py
"""Novel publishing module for multiple platforms."""

from src.novel_agent.publishing.base import (
    BasePublisher,
    ChapterInfo,
    PublishResult,
    PublishStatus,
    StoryInfo,
)
from src.novel_agent.publishing.publisher_manager import PublisherManager
from src.novel_agent.publishing.royalroad_publisher import RoyalRoadPublisher
from src.novel_agent.publishing.wattpad_publisher import WattpadPublisher

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
