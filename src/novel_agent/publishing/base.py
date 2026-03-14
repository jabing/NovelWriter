# src/publishing/base.py
"""Base classes for novel publishing."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Try to import playwright
try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any  # type: ignore
    Browser = Any  # type: ignore
    BrowserContext = Any  # type: ignore


class PublishStatus(str, Enum):
    """Status of a publish operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some parts succeeded, some failed


@dataclass
class StoryInfo:
    """Information about a story/novel."""
    title: str
    description: str
    genre: str
    tags: list[str] = field(default_factory=list)
    language: str = "en"
    rating: str = "teen"  # teen, mature, everyone
    cover_image: str | None = None
    author_notes: str = ""

    # Platform-specific IDs (populated after creation)
    platform_id: str | None = None
    platform_url: str | None = None


@dataclass
class ChapterInfo:
    """Information about a chapter."""
    title: str
    content: str
    chapter_number: int

    # Optional fields
    author_notes: str = ""
    word_count: int = 0

    # Platform-specific IDs
    platform_id: str | None = None
    platform_url: str | None = None

    def __post_init__(self) -> None:
        if self.word_count == 0:
            self.word_count = len(self.content.split())


@dataclass
class PublishResult:
    """Result of a publish operation."""
    success: bool
    status: PublishStatus
    message: str

    # Platform-specific data
    platform: str = ""
    story_id: str | None = None
    chapter_id: str | None = None
    url: str | None = None

    # Error information
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Timestamps
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BasePublisher(ABC):
    """Abstract base class for novel publishers.

    Publishers handle the process of:
    1. Logging into the platform
    2. Creating/updating stories
    3. Publishing chapters
    4. Managing story metadata
    """

    # Platform configuration
    PLATFORM_NAME: str = ""
    PLATFORM_URL: str = ""

    # Browser settings
    STEALTH_SCRIPT = """
    // Anti-detection measures
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    window.chrome = {runtime: {}};
    """

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 0,  # Milliseconds between actions (for debugging)
        timeout: int = 30000,
    ) -> None:
        """Initialize the publisher.

        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations for debugging
            timeout: Default timeout for operations
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright not installed. "
                "Run: pip install playwright && playwright install chromium"
            )

        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout

        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._logged_in = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Publisher name."""
        pass

    @property
    @abstractmethod
    def login_url(self) -> str:
        """URL for login page."""
        pass

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is launched."""
        if self._browser is None or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
        return self._browser

    async def _create_context(self) -> BrowserContext:
        """Create browser context."""
        browser = await self._ensure_browser()
        self._context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )
        return self._context

    async def _get_page(self) -> Page:
        """Get or create a page."""
        if self._page is None or self._page.is_closed():
            if self._context is None:
                await self._create_context()
            self._page = await self._context.new_page()
            await self._page.add_init_script(self.STEALTH_SCRIPT)
            self._page.set_default_timeout(self.timeout)
        return self._page

    async def _navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navigate to URL."""
        page = await self._get_page()
        await page.goto(url, wait_until=wait_until, timeout=self.timeout)
        logger.info(f"Navigated to {url}")

    async def _wait_and_click(
        self,
        selector: str,
        timeout: int | None = None,
    ) -> bool:
        """Wait for element and click it."""
        page = await self._get_page()
        try:
            await page.wait_for_selector(selector, timeout=timeout or self.timeout)
            await page.click(selector)
            return True
        except Exception as e:
            logger.warning(f"Failed to click {selector}: {e}")
            return False

    async def _fill_input(
        self,
        selector: str,
        value: str,
        timeout: int | None = None,
    ) -> bool:
        """Fill an input field."""
        page = await self._get_page()
        try:
            await page.wait_for_selector(selector, timeout=timeout or self.timeout)
            await page.fill(selector, value)
            return True
        except Exception as e:
            logger.warning(f"Failed to fill {selector}: {e}")
            return False

    async def _get_text(self, selector: str) -> str:
        """Get text from element."""
        page = await self._get_page()
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.inner_text()
        except Exception as e:
            logger.warning(f"Failed to get text from {selector}: {e}")
        return ""

    async def _screenshot(self, name: str) -> str | None:
        """Take screenshot for debugging."""
        if self._page:
            try:
                import os
                os.makedirs("data/debug_screenshots", exist_ok=True)
                path = f"data/debug_screenshots/{name}.png"
                await self._page.screenshot(path=path)
                return path
            except Exception as e:
                logger.warning(f"Screenshot failed: {e}")
        return None

    @abstractmethod
    async def login(
        self,
        username: str,
        password: str,
        totp_code: str | None = None,
    ) -> PublishResult:
        """Log into the platform.

        Args:
            username: Username or email
            password: Password
            totp_code: Time-based OTP if 2FA is enabled

        Returns:
            PublishResult with login status
        """
        pass

    @abstractmethod
    async def create_story(self, story: StoryInfo) -> PublishResult:
        """Create a new story on the platform.

        Args:
            story: Story information

        Returns:
            PublishResult with story ID and URL
        """
        pass

    @abstractmethod
    async def publish_chapter(
        self,
        story_id: str,
        chapter: ChapterInfo,
        publish: bool = True,
    ) -> PublishResult:
        """Publish a chapter to an existing story.

        Args:
            story_id: Platform-specific story ID
            chapter: Chapter information
            publish: Whether to publish immediately or save as draft

        Returns:
            PublishResult with chapter ID and URL
        """
        pass

    @abstractmethod
    async def update_story(
        self,
        story_id: str,
        story: StoryInfo,
    ) -> PublishResult:
        """Update story metadata.

        Args:
            story_id: Platform-specific story ID
            story: Updated story information

        Returns:
            PublishResult with update status
        """
        pass

    async def logout(self) -> None:
        """Log out from the platform."""
        self._logged_in = False
        # Most platforms handle logout via cookie clearing

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._logged_in = False

    async def __aenter__(self) -> "BasePublisher":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    @property
    def is_logged_in(self) -> bool:
        """Check if currently logged in."""
        return self._logged_in
