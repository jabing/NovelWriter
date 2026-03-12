# src/publishing/publisher_manager.py
"""Multi-platform publisher manager for coordinating publishing across platforms."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.publishing.base import (
    BasePublisher,
    ChapterInfo,
    PublishResult,
    PublishStatus,
    StoryInfo,
)
from src.publishing.royalroad_publisher import RoyalRoadPublisher
from src.publishing.wattpad_publisher import WattpadPublisher

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Supported publishing platforms."""
    WATTPAD = "wattpad"
    ROYALROAD = "royalroad"
    # Future platforms
    # AMAZON_KDP = "amazon_kdp"
    # QIDIAN = "qidian"
    # JINJIANG = "jinjiang"


@dataclass
class PlatformCredentials:
    """Credentials for a platform."""
    platform: Platform
    username: str
    password: str
    totp_secret: str | None = None  # For 2FA

    # Session/token data (populated after login)
    session_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishJob:
    """A publishing job containing story and chapters."""
    job_id: str
    story: StoryInfo
    chapters: list[ChapterInfo]
    platforms: list[Platform]
    status: PublishStatus = PublishStatus.PENDING

    # Results per platform
    results: dict[str, PublishResult] = field(default_factory=dict)

    # Story IDs per platform (populated after creation)
    story_ids: dict[str, str] = field(default_factory=dict)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None


class PublisherManager:
    """Manages publishing across multiple platforms.

    Features:
    - Multi-platform coordination
    - Credential management
    - Job tracking and status
    - Batch publishing
    - Error handling and retry
    - Session persistence
    """

    def __init__(
        self,
        credentials_dir: Path | None = None,
        jobs_dir: Path | None = None,
        headless: bool = True,
    ) -> None:
        """Initialize the publisher manager.

        Args:
            credentials_dir: Directory to store encrypted credentials
            jobs_dir: Directory to store job status
            headless: Run browsers in headless mode
        """
        self.credentials_dir = credentials_dir or Path("data/credentials")
        self.jobs_dir = jobs_dir or Path("data/publish_jobs")
        self.headless = headless

        self._publishers: dict[Platform, BasePublisher] = {}
        self._credentials: dict[Platform, PlatformCredentials] = {}
        self._active_jobs: dict[str, PublishJob] = {}

        # Ensure directories exist
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def _get_publisher(self, platform: Platform) -> BasePublisher:
        """Get or create a publisher for a platform.

        Args:
            platform: Target platform

        Returns:
            Publisher instance
        """
        if platform not in self._publishers:
            if platform == Platform.WATTPAD:
                self._publishers[platform] = WattpadPublisher(headless=self.headless)
            elif platform == Platform.ROYALROAD:
                self._publishers[platform] = RoyalRoadPublisher(headless=self.headless)
            else:
                raise ValueError(f"Unsupported platform: {platform}")

        return self._publishers[platform]

    async def load_credentials(
        self,
        platform: Platform,
        username: str,
        password: str,
        totp_code: str | None = None,
    ) -> None:
        """Load credentials for a platform.

        Args:
            platform: Target platform
            username: Username/email
            password: Password
            totp_code: TOTP code for 2FA
        """
        self._credentials[platform] = PlatformCredentials(
            platform=platform,
            username=username,
            password=password,
            totp_secret=totp_code,
        )

    async def login_platform(
        self,
        platform: Platform,
        username: str | None = None,
        password: str | None = None,
        totp_code: str | None = None,
    ) -> PublishResult:
        """Log into a platform.

        Args:
            platform: Target platform
            username: Username (uses stored credentials if not provided)
            password: Password (uses stored credentials if not provided)
            totp_code: TOTP code for 2FA

        Returns:
            Login result
        """
        # Use stored credentials if not provided
        if platform in self._credentials:
            creds = self._credentials[platform]
            username = username or creds.username
            password = password or creds.password
            totp_code = totp_code or creds.totp_secret

        if not username or not password:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message="No credentials provided",
                platform=platform.value,
                errors=["Username and password required"],
            )

        publisher = self._get_publisher(platform)
        result = await publisher.login(username, password, totp_code)

        if result.success:
            logger.info(f"Successfully logged into {platform.value}")
        else:
            logger.error(f"Failed to login to {platform.value}: {result.message}")

        return result

    async def login_all_platforms(
        self,
        credentials: dict[Platform, tuple[str, str, str | None]],
    ) -> dict[Platform, PublishResult]:
        """Log into all platforms with provided credentials.

        Args:
            credentials: Dict mapping platform to (username, password, totp_code)

        Returns:
            Dict of login results per platform
        """
        results = {}

        for platform, (username, password, totp) in credentials.items():
            results[platform] = await self.login_platform(
                platform, username, password, totp
            )

        return results

    async def create_story(
        self,
        platform: Platform,
        story: StoryInfo,
    ) -> PublishResult:
        """Create a story on a platform.

        Args:
            platform: Target platform
            story: Story information

        Returns:
            Creation result with story ID
        """
        publisher = self._get_publisher(platform)

        if not publisher.is_logged_in:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message="Not logged in",
                platform=platform.value,
                errors=["Please login first"],
            )

        result = await publisher.create_story(story)

        if result.success and result.story_id:
            logger.info(f"Created story on {platform.value}: {result.story_id}")

        return result

    async def publish_chapter(
        self,
        platform: Platform,
        story_id: str,
        chapter: ChapterInfo,
        publish: bool = True,
    ) -> PublishResult:
        """Publish a chapter to a platform.

        Args:
            platform: Target platform
            story_id: Platform-specific story ID
            chapter: Chapter information
            publish: Whether to publish immediately

        Returns:
            Publish result
        """
        publisher = self._get_publisher(platform)

        if not publisher.is_logged_in:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message="Not logged in",
                platform=platform.value,
            )

        result = await publisher.publish_chapter(story_id, chapter, publish)

        if result.success:
            logger.info(
                f"Published chapter {chapter.chapter_number} to {platform.value}"
            )

        return result

    async def publish_to_all_platforms(
        self,
        story: StoryInfo,
        chapters: list[ChapterInfo],
        platforms: list[Platform],
        create_story: bool = True,
    ) -> dict[Platform, dict[str, Any]]:
        """Publish story and chapters to multiple platforms.

        Args:
            story: Story information
            chapters: List of chapters to publish
            platforms: Target platforms
            create_story: Whether to create the story (skip if already exists)

        Returns:
            Dict of results per platform
        """
        results = {}

        for platform in platforms:
            platform_results: dict[str, Any] = {
                "platform": platform.value,
                "story_created": False,
                "story_id": None,
                "chapters_published": 0,
                "chapters_failed": 0,
                "errors": [],
            }

            try:
                # Create story if needed
                final_story_id: str | None = None

                if create_story:
                    story_result = await self.create_story(platform, story)

                    if story_result.success:
                        platform_results["story_created"] = True
                        platform_results["story_id"] = story_result.story_id
                        final_story_id = story_result.story_id
                    else:
                        platform_results["errors"].append(
                            f"Story creation failed: {story_result.message}"
                        )
                        results[platform] = platform_results
                        continue
                else:
                    # Use provided story ID
                    final_story_id = story.platform_id
                    if not final_story_id:
                        platform_results["errors"].append(
                            "No story ID provided for existing story"
                        )
                        results[platform] = platform_results
                        continue

                # Publish chapters - final_story_id is guaranteed non-None here
                for chapter in chapters:
                    chapter_result = await self.publish_chapter(
                        platform, final_story_id, chapter  # type: ignore[arg-type]
                    )

                    if chapter_result.success:
                        platform_results["chapters_published"] += 1
                    else:
                        platform_results["chapters_failed"] += 1
                        platform_results["errors"].append(
                            f"Chapter {chapter.chapter_number}: {chapter_result.message}"
                        )

            except Exception as e:
                platform_results["errors"].append(f"Exception: {str(e)}")
                logger.error(f"Error publishing to {platform.value}: {e}")

            results[platform] = platform_results

        return results

    def create_job(
        self,
        story: StoryInfo,
        chapters: list[ChapterInfo],
        platforms: list[Platform],
    ) -> PublishJob:
        """Create a new publishing job.

        Args:
            story: Story information
            chapters: Chapters to publish
            platforms: Target platforms

        Returns:
            Created job
        """
        import uuid

        job = PublishJob(
            job_id=f"job_{uuid.uuid4().hex[:8]}",
            story=story,
            chapters=chapters,
            platforms=platforms,
        )

        self._active_jobs[job.job_id] = job
        self._save_job(job)

        return job

    async def execute_job(self, job_id: str) -> dict[str, Any]:
        """Execute a publishing job.

        Args:
            job_id: Job ID to execute

        Returns:
            Job execution results
        """
        job = self._active_jobs.get(job_id)

        if not job:
            # Try to load from disk
            job = self._load_job(job_id)
            if not job:
                return {"error": f"Job not found: {job_id}"}

        job.status = PublishStatus.IN_PROGRESS
        job.started_at = datetime.now().isoformat()
        self._save_job(job)

        results = await self.publish_to_all_platforms(
            job.story,
            job.chapters,
            job.platforms,
        )

        # Determine overall status
        all_success = all(
            r["chapters_failed"] == 0 and len(r["errors"]) == 0
            for r in results.values()
        )

        job.status = PublishStatus.SUCCESS if all_success else PublishStatus.PARTIAL
        job.completed_at = datetime.now().isoformat()

        # Store results
        for platform, result in results.items():
            job.results[platform.value] = PublishResult(
                success=result["chapters_failed"] == 0,
                status=PublishStatus.SUCCESS if result["chapters_failed"] == 0 else PublishStatus.PARTIAL,
                message=f"Published {result['chapters_published']} chapters",
                platform=platform.value,
                story_id=result["story_id"],
                errors=result["errors"],
            )

        self._save_job(job)

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "platforms": {p.value: r for p, r in results.items()},
        }

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """Get status of a publishing job.

        Args:
            job_id: Job ID

        Returns:
            Job status or None if not found
        """
        job = self._active_jobs.get(job_id) or self._load_job(job_id)

        if not job:
            return None

        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "story_title": job.story.title,
            "chapters": len(job.chapters),
            "platforms": [p.value for p in job.platforms],
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "results": {
                platform: {
                    "success": r.success,
                    "message": r.message,
                    "story_id": r.story_id,
                }
                for platform, r in job.results.items()
            },
        }

    def _save_job(self, job: PublishJob) -> None:
        """Save job state to disk."""
        job_path = self.jobs_dir / f"{job.job_id}.json"

        data = {
            "job_id": job.job_id,
            "story": {
                "title": job.story.title,
                "description": job.story.description,
                "genre": job.story.genre,
                "tags": job.story.tags,
            },
            "chapters": [
                {
                    "title": ch.title,
                    "chapter_number": ch.chapter_number,
                    "word_count": ch.word_count,
                }
                for ch in job.chapters
            ],
            "platforms": [p.value for p in job.platforms],
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }

        with open(job_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_job(self, job_id: str) -> PublishJob | None:
        """Load job state from disk."""
        job_path = self.jobs_dir / f"{job_id}.json"

        if not job_path.exists():
            return None

        try:
            with open(job_path) as f:
                data = json.load(f)

            story = StoryInfo(
                title=data["story"]["title"],
                description=data["story"]["description"],
                genre=data["story"]["genre"],
                tags=data["story"]["tags"],
            )

            chapters = [
                ChapterInfo(
                    title=ch["title"],
                    content="",  # Content not stored in job file
                    chapter_number=ch["chapter_number"],
                    word_count=ch["word_count"],
                )
                for ch in data["chapters"]
            ]

            platforms = [Platform(p) for p in data["platforms"]]

            job = PublishJob(
                job_id=data["job_id"],
                story=story,
                chapters=chapters,
                platforms=platforms,
                status=PublishStatus(data["status"]),
                created_at=data["created_at"],
                started_at=data.get("started_at"),
                completed_at=data.get("completed_at"),
            )

            self._active_jobs[job_id] = job
            return job

        except Exception as e:
            logger.error(f"Failed to load job {job_id}: {e}")
            return None

    async def close_all(self) -> None:
        """Close all publisher connections."""
        for platform, publisher in self._publishers.items():
            try:
                await publisher.close()
                logger.info(f"Closed {platform.value} publisher")
            except Exception as e:
                logger.warning(f"Error closing {platform.value} publisher: {e}")

        self._publishers.clear()

    async def __aenter__(self) -> "PublisherManager":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close_all()
