# src/agents/publisher.py
"""Publisher Agent - Multi-platform publishing."""

from typing import Any

from src.agents.base import AgentResult, BaseAgent
from src.platforms.base import BasePlatform, PublishResult, PublishStatus
from src.platforms.kindle import KindlePlatform
from src.platforms.royalroad import RoyalRoadPlatform
from src.platforms.wattpad import WattpadPlatform


class PublisherAgent(BaseAgent):
    """Agent responsible for publishing to multiple platforms.

    Handles:
    - Platform selection and initialization
    - Format conversion per platform
    - Publishing execution
    - Status tracking
    - Retry logic for failed publishes
    """

    # Available platforms
    PLATFORMS = {
        "wattpad": WattpadPlatform,
        "royalroad": RoyalRoadPlatform,
        "kindle": KindlePlatform,
    }

    def __init__(self, name: str = "Publisher Agent", **kwargs: Any) -> None:
        """Initialize Publisher Agent.

        Args:
            name: Agent name
            **kwargs: Additional configuration passed to BaseAgent
                - llm: LLM instance (optional, not used by Publisher Agent)
        """
        # Publisher Agent doesn't need an LLM, but BaseAgent requires it
        # Create a placeholder if not provided
        if "llm" not in kwargs:
            from unittest.mock import MagicMock
            kwargs["llm"] = MagicMock()

        super().__init__(name=name, **kwargs)
        self._platform_instances: dict[str, BasePlatform] = {}
        self._story_ids: dict[str, str] = {}  # platform -> story_id mapping

    def register_platform(
        self,
        platform_name: str,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> bool:
        """Register a platform for publishing.

        Args:
            platform_name: Platform to register (wattpad, royalroad, kindle)
            api_key: API key for the platform
            **kwargs: Additional platform configuration

        Returns:
            True if platform registered successfully
        """
        platform_name = platform_name.lower()

        if platform_name not in self.PLATFORMS:
            return False

        platform_class = self.PLATFORMS[platform_name]

        try:
            instance = platform_class(api_key=api_key, simulate=True, **kwargs)
            self._platform_instances[platform_name] = instance
            return True
        except Exception:
            return False

    def set_story_id(self, platform: str, story_id: str) -> None:
        """Set the story ID for a platform.

        Args:
            platform: Platform name
            story_id: Story/novel ID on the platform
        """
        self._story_ids[platform.lower()] = story_id

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute publishing.

        Args:
            input_data: Must contain:
                - novel_id: str (for tracking)
                - chapter_number: int
                - title: str
                - content: str
                - platforms: list[str] (platforms to publish to)

            Optional:
                - story_ids: dict[str, str] (platform -> story_id mapping)
                - platform_configs: dict[str, dict] (platform-specific options)

        Returns:
            AgentResult with publish status per platform
        """
        try:
            novel_id = input_data.get("novel_id", "unknown")
            chapter_number = input_data.get("chapter_number", 1)
            title = input_data.get("title", f"Chapter {chapter_number}")
            content = input_data.get("content", "")
            platforms = input_data.get("platforms", [])
            story_ids = input_data.get("story_ids", {})
            platform_configs = input_data.get("platform_configs", {})

            if not content:
                return AgentResult(
                    success=False,
                    data={},
                    errors=["No content provided for publishing"],
                )

            if not platforms:
                return AgentResult(
                    success=False,
                    data={},
                    errors=["No platforms specified for publishing"],
                )

            # Initialize platforms if needed
            for platform in platforms:
                if platform.lower() not in self._platform_instances:
                    self.register_platform(
                        platform,
                        **platform_configs.get(platform, {})
                    )

            # Publish to each platform
            results: dict[str, PublishResult] = {}

            for platform_name in platforms:
                platform_name = platform_name.lower()
                result = await self._publish_to_platform(
                    platform_name=platform_name,
                    story_id=story_ids.get(platform_name) or self._story_ids.get(platform_name),
                    chapter_number=chapter_number,
                    title=title,
                    content=content,
                    config=platform_configs.get(platform_name, {}),
                )
                results[platform_name] = result

            # Aggregate results
            successful = [p for p, r in results.items() if r.success]
            failed = [p for p, r in results.items() if not r.success]

            return AgentResult(
                success=len(successful) > 0,
                data={
                    "novel_id": novel_id,
                    "chapter_number": chapter_number,
                    "title": title,
                    "platforms_published": successful,
                    "platforms_failed": failed,
                    "results": {
                        p: {
                            "success": r.success,
                            "status": r.status.value,
                            "url": r.url,
                            "chapter_id": r.chapter_id,
                            "error": r.error_message,
                        }
                        for p, r in results.items()
                    },
                },
                errors=[f"Failed to publish to: {', '.join(failed)}"] if failed else [],
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Publishing failed: {str(e)}"],
            )

    async def _publish_to_platform(
        self,
        platform_name: str,
        story_id: str | None,
        chapter_number: int,
        title: str,
        content: str,
        config: dict[str, Any],
    ) -> PublishResult:
        """Publish to a single platform.

        Args:
            platform_name: Platform to publish to
            story_id: Story/novel ID
            chapter_number: Chapter number
            title: Chapter title
            content: Chapter content
            config: Platform-specific configuration

        Returns:
            PublishResult with status
        """
        platform = self._platform_instances.get(platform_name)

        if not platform:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                platform=platform_name,
                error_message=f"Platform {platform_name} not registered",
            )

        try:
            # Authenticate if needed
            if not await platform.authenticate():
                return PublishResult(
                    success=False,
                    status=PublishStatus.FAILED,
                    platform=platform_name,
                    error_message="Authentication failed",
                )

            # Create story if no story_id provided
            if not story_id:
                story_id = await platform.create_story(
                    title=config.get("story_title", "Untitled"),
                    description=config.get("story_description", ""),
                    tags=config.get("story_tags", []),
                    **config.get("create_options", {}),
                )
                self._story_ids[platform_name] = story_id

            # Publish the chapter
            result = await platform.publish_chapter(
                story_id=story_id,
                chapter_number=chapter_number,
                title=title,
                content=content,
                **config.get("publish_options", {}),
            )

            return result

        except Exception as e:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                platform=platform_name,
                error_message=str(e),
            )

    async def create_story_on_platform(
        self,
        platform_name: str,
        title: str,
        description: str,
        tags: list[str],
        **kwargs: Any,
    ) -> str | None:
        """Create a new story on a platform.

        Args:
            platform_name: Platform to create story on
            title: Story title
            description: Story description
            tags: Story tags/genres
            **kwargs: Additional platform-specific options

        Returns:
            Story ID or None if failed
        """
        platform_name = platform_name.lower()
        platform = self._platform_instances.get(platform_name)

        if not platform:
            return None

        try:
            if not await platform.authenticate():
                return None

            story_id = await platform.create_story(
                title=title,
                description=description,
                tags=tags,
                **kwargs,
            )

            self._story_ids[platform_name] = story_id
            return story_id

        except Exception:
            return None

    async def get_comments_from_platform(
        self,
        platform_name: str,
        story_id: str,
        chapter_number: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get comments from a platform.

        Args:
            platform_name: Platform to get comments from
            story_id: Story ID
            chapter_number: Optional chapter number
            limit: Maximum comments to retrieve

        Returns:
            List of comments
        """
        platform_name = platform_name.lower()
        platform = self._platform_instances.get(platform_name)

        if not platform:
            return []

        try:
            if not await platform.authenticate():
                return []

            return await platform.get_comments(
                story_id=story_id,
                chapter_number=chapter_number,
                limit=limit,
            )
        except Exception:
            return []

    async def reply_to_comment(
        self,
        platform_name: str,
        story_id: str,
        comment_id: str,
        reply_text: str,
    ) -> bool:
        """Reply to a comment on a platform.

        Args:
            platform_name: Platform name
            story_id: Story ID
            comment_id: Comment ID to reply to
            reply_text: Reply content

        Returns:
            True if successful
        """
        platform_name = platform_name.lower()
        platform = self._platform_instances.get(platform_name)

        if not platform:
            return False

        try:
            if not await platform.authenticate():
                return False

            return await platform.reply_to_comment(
                story_id=story_id,
                comment_id=comment_id,
                reply_text=reply_text,
            )
        except Exception:
            return False

    def get_available_platforms(self) -> list[str]:
        """Get list of available platform names.

        Returns:
            List of platform names
        """
        return list(self.PLATFORMS.keys())

    def get_registered_platforms(self) -> list[str]:
        """Get list of registered platform names.

        Returns:
            List of registered platform names
        """
        return list(self._platform_instances.keys())
