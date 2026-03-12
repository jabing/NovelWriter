# src/platforms/base.py
"""Base class for publishing platforms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PublishStatus(str, Enum):
    """Status of a publish operation."""
    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"


@dataclass
class PublishResult:
    """Result of a publish operation."""
    success: bool
    status: PublishStatus
    platform: str
    chapter_id: str | None = None
    url: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class BasePlatform(ABC):
    """Abstract base class for publishing platforms.

    Each platform (Wattpad, Royal Road, Kindle) should inherit from
    this class and implement the required methods.
    """

    PLATFORM_NAME: str = "base"

    def __init__(self, api_key: str | None = None, **kwargs: Any) -> None:
        """Initialize platform client.

        Args:
            api_key: Platform API key
            **kwargs: Platform-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform.

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    async def create_story(
        self,
        title: str,
        description: str,
        tags: list[str],
        **kwargs: Any,
    ) -> str:
        """Create a new story on the platform.

        Args:
            title: Story title
            description: Story description
            tags: List of tags/genres
            **kwargs: Platform-specific options

        Returns:
            Story ID on the platform
        """
        pass

    @abstractmethod
    async def publish_chapter(
        self,
        story_id: str,
        chapter_number: int,
        title: str,
        content: str,
        **kwargs: Any,
    ) -> PublishResult:
        """Publish a chapter.

        Args:
            story_id: Platform story ID
            chapter_number: Chapter number
            title: Chapter title
            content: Chapter content
            **kwargs: Platform-specific options

        Returns:
            PublishResult with status
        """
        pass

    @abstractmethod
    async def get_comments(
        self,
        story_id: str,
        chapter_number: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get comments for a story or chapter.

        Args:
            story_id: Platform story ID
            chapter_number: Optional specific chapter
            limit: Maximum comments to retrieve

        Returns:
            List of comment data
        """
        pass

    @abstractmethod
    async def reply_to_comment(
        self,
        story_id: str,
        comment_id: str,
        reply_text: str,
    ) -> bool:
        """Reply to a comment.

        Args:
            story_id: Platform story ID
            comment_id: Comment to reply to
            reply_text: Reply content

        Returns:
            True if reply successful
        """
        pass
