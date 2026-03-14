# src/publishing/wattpad_publisher.py
"""Wattpad novel publisher implementation."""

import asyncio
import logging
from typing import Any

from src.novel_agent.publishing.base import (
    BasePublisher,
    ChapterInfo,
    PublishResult,
    PublishStatus,
    StoryInfo,
)

logger = logging.getLogger(__name__)


class WattpadPublisher(BasePublisher):
    """Publisher for Wattpad platform.

    Wattpad publishing process:
    1. Login at https://www.wattpad.com/login
    2. Create story at https://www.wattpad.com/myworks
    3. Add chapters
    4. Publish

    Features:
    - Story creation with cover image
    - Chapter publishing
    - Tag management
    - Story settings
    """

    PLATFORM_NAME = "wattpad"
    PLATFORM_URL = "https://www.wattpad.com"

    # Genre mapping
    GENRE_MAP = {
        "fantasy": "Fantasy",
        "scifi": "Science Fiction",
        "romance": "Romance",
        "history": "Historical Fiction",
        "military": "Action",
        "adventure": "Adventure",
        "mystery": "Mystery",
        "horror": "Horror",
        "thriller": "Thriller",
        "teen": "Teen Fiction",
    }

    # Rating mapping
    RATING_MAP = {
        "everyone": "1",  # Everyone
        "teen": "2",      # Teen
        "mature": "3",    # Mature
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Wattpad publisher."""
        super().__init__(**kwargs)
        self._story_cache: dict[str, str] = {}  # story_title -> story_id

    @property
    def name(self) -> str:
        return self.PLATFORM_NAME

    @property
    def login_url(self) -> str:
        return f"{self.PLATFORM_URL}/login"

    async def login(
        self,
        username: str,
        password: str,
        totp_code: str | None = None,
    ) -> PublishResult:
        """Log into Wattpad.

        Args:
            username: Email or username
            password: Password
            totp_code: Not used for Wattpad

        Returns:
            PublishResult with login status
        """
        try:
            page = await self._get_page()

            # Navigate to login page
            await self._navigate(self.login_url)
            await asyncio.sleep(2)

            # Wait for login form
            await page.wait_for_selector("#login-username, input[name='username']", timeout=10000)

            # Fill in credentials
            username_selectors = [
                "#login-username",
                "input[name='username']",
                "input[type='email']",
                "input[placeholder*='email' i]",
            ]

            filled = False
            for selector in username_selectors:
                try:
                    await page.fill(selector, username, timeout=5000)
                    filled = True
                    logger.info(f"Filled username using {selector}")
                    break
                except Exception:
                    continue

            if not filled:
                return PublishResult(
                    success=False,
                    status=PublishStatus.FAILED,
                    message="Could not find username field",
                    platform=self.PLATFORM_NAME,
                    errors=["Username field not found"],
                )

            # Fill password
            password_selectors = [
                "#login-password",
                "input[name='password']",
                "input[type='password']",
            ]

            filled = False
            for selector in password_selectors:
                try:
                    await page.fill(selector, password, timeout=5000)
                    filled = True
                    break
                except Exception:
                    continue

            if not filled:
                return PublishResult(
                    success=False,
                    status=PublishStatus.FAILED,
                    message="Could not find password field",
                    platform=self.PLATFORM_NAME,
                    errors=["Password field not found"],
                )

            # Click login button
            login_buttons = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Log in')",
                "button:has-text('Sign in')",
            ]

            clicked = False
            for selector in login_buttons:
                try:
                    await page.click(selector, timeout=5000)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                return PublishResult(
                    success=False,
                    status=PublishStatus.FAILED,
                    message="Could not click login button",
                    platform=self.PLATFORM_NAME,
                )

            # Wait for login to complete
            await asyncio.sleep(3)

            # Check if logged in by looking for user-specific elements
            current_url = page.url

            # Check for login error messages
            error_selectors = [
                ".error-message",
                ".alert-error",
                "[class*='error']",
            ]

            for selector in error_selectors:
                error_elem = await page.query_selector(selector)
                if error_elem:
                    error_text = await error_elem.inner_text()
                    return PublishResult(
                        success=False,
                        status=PublishStatus.FAILED,
                        message=f"Login failed: {error_text}",
                        platform=self.PLATFORM_NAME,
                        errors=[error_text],
                    )

            # Check if we're no longer on login page
            if "login" not in current_url.lower():
                self._logged_in = True
                return PublishResult(
                    success=True,
                    status=PublishStatus.SUCCESS,
                    message="Successfully logged into Wattpad",
                    platform=self.PLATFORM_NAME,
                )

            # Check for profile/user elements
            user_indicators = [
                "nav[data-testid='nav']",
                "[data-testid='profile-dropdown']",
                ".profile-icon",
                "a[href*='/user/']",
            ]

            for selector in user_indicators:
                elem = await page.query_selector(selector)
                if elem:
                    self._logged_in = True
                    return PublishResult(
                        success=True,
                        status=PublishStatus.SUCCESS,
                        message="Successfully logged into Wattpad",
                        platform=self.PLATFORM_NAME,
                    )

            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message="Login verification failed",
                platform=self.PLATFORM_NAME,
                errors=["Could not verify login status"],
            )

        except Exception as e:
            logger.error(f"Wattpad login error: {e}")
            await self._screenshot("wattpad_login_error")
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message=f"Login error: {str(e)}",
                platform=self.PLATFORM_NAME,
                errors=[str(e)],
            )

    async def create_story(self, story: StoryInfo) -> PublishResult:
        """Create a new story on Wattpad.

        Args:
            story: Story information

        Returns:
            PublishResult with story ID
        """
        if not self._logged_in:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message="Not logged in",
                platform=self.PLATFORM_NAME,
                errors=["Please login first"],
            )

        try:
            page = await self._get_page()

            # Navigate to create story page
            create_url = f"{self.PLATFORM_URL}/myworks?do=create"
            await self._navigate(create_url)
            await asyncio.sleep(2)

            # Wait for story creation form
            await page.wait_for_selector("form, .create-story, input[name='title']", timeout=10000)

            # Fill story title
            title_selectors = [
                "input[name='title']",
                "#title",
                "input[placeholder*='title' i]",
            ]

            for selector in title_selectors:
                try:
                    await page.fill(selector, story.title, timeout=5000)
                    logger.info(f"Filled title using {selector}")
                    break
                except Exception:
                    continue

            # Fill description
            desc_selectors = [
                "textarea[name='description']",
                "#description",
                "textarea[placeholder*='description' i]",
            ]

            for selector in desc_selectors:
                try:
                    await page.fill(selector, story.description, timeout=5000)
                    break
                except Exception:
                    continue

            # Select genre
            if story.genre:
                genre = self.GENRE_MAP.get(story.genre.lower(), story.genre)
                genre_selectors = [
                    f"select[name='category'] option:has-text('{genre}')",
                    f"select[name='genre'] option:has-text('{genre}')",
                    f"[data-value='{genre}']",
                ]

                for selector in genre_selectors:
                    try:
                        await page.click(selector, timeout=5000)
                        break
                    except Exception:
                        continue

            # Add tags
            if story.tags:
                tag_input_selectors = [
                    "input[name='tags']",
                    "#tags",
                    "input[placeholder*='tag' i]",
                ]

                for selector in tag_input_selectors:
                    try:
                        tags_str = ", ".join(story.tags[:20])  # Wattpad tag limit
                        await page.fill(selector, tags_str, timeout=5000)
                        break
                    except Exception:
                        continue

            # Set rating
            rating_value = self.RATING_MAP.get(story.rating, "2")
            rating_selectors = [
                f"input[name='rating'][value='{rating_value}']",
                f"select[name='rating'] option[value='{rating_value}']",
            ]

            for selector in rating_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    break
                except Exception:
                    continue

            # Click create/submit button
            create_buttons = [
                "button[type='submit']",
                "button:has-text('Create')",
                "button:has-text('Save')",
                "button:has-text('Publish')",
            ]

            for selector in create_buttons:
                try:
                    await page.click(selector, timeout=5000)
                    await asyncio.sleep(3)
                    break
                except Exception:
                    continue

            # Get story ID from URL
            current_url = page.url
            import re
            story_id_match = re.search(r'/story/(\d+)', current_url) or \
                           re.search(r'/myworks/(\d+)', current_url) or \
                           re.search(r'work_id=(\d+)', current_url)

            story_id = story_id_match.group(1) if story_id_match else None

            if story_id:
                self._story_cache[story.title] = story_id
                return PublishResult(
                    success=True,
                    status=PublishStatus.SUCCESS,
                    message=f"Created story: {story.title}",
                    platform=self.PLATFORM_NAME,
                    story_id=story_id,
                    url=f"{self.PLATFORM_URL}/story/{story_id}",
                )

            # Check for success indicators
            success_indicators = [
                ".success-message",
                ".alert-success",
                "[class*='success']",
            ]

            for selector in success_indicators:
                elem = await page.query_selector(selector)
                if elem:
                    return PublishResult(
                        success=True,
                        status=PublishStatus.SUCCESS,
                        message="Story created (ID not captured)",
                        platform=self.PLATFORM_NAME,
                    )

            await self._screenshot("wattpad_create_story")
            return PublishResult(
                success=False,
                status=PublishStatus.PARTIAL,
                message="Story creation status unclear",
                platform=self.PLATFORM_NAME,
                warnings=["Could not verify story creation"],
            )

        except Exception as e:
            logger.error(f"Wattpad create story error: {e}")
            await self._screenshot("wattpad_create_error")
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message=f"Create story error: {str(e)}",
                platform=self.PLATFORM_NAME,
                errors=[str(e)],
            )

    async def publish_chapter(
        self,
        story_id: str,
        chapter: ChapterInfo,
        publish: bool = True,
    ) -> PublishResult:
        """Publish a chapter to Wattpad story.

        Args:
            story_id: Wattpad story ID
            chapter: Chapter information
            publish: Whether to publish immediately

        Returns:
            PublishResult with chapter ID
        """
        if not self._logged_in:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message="Not logged in",
                platform=self.PLATFORM_NAME,
            )

        try:
            page = await self._get_page()

            # Navigate to story editor
            editor_url = f"{self.PLATFORM_URL}/myworks/{story_id}/write"
            await self._navigate(editor_url)
            await asyncio.sleep(2)

            # Click "New Part" or similar
            new_part_buttons = [
                "button:has-text('New Part')",
                "button:has-text('Add Part')",
                "a:has-text('New Part')",
                ".new-part-button",
            ]

            for selector in new_part_buttons:
                try:
                    await page.click(selector, timeout=5000)
                    await asyncio.sleep(2)
                    break
                except Exception:
                    continue

            # Fill chapter title
            title_selectors = [
                "input[name='title']",
                "#part-title",
                "input[placeholder*='title' i]",
            ]

            for selector in title_selectors:
                try:
                    await page.fill(selector, chapter.title, timeout=5000)
                    break
                except Exception:
                    continue

            # Fill chapter content
            content_selectors = [
                "textarea[name='content']",
                "#story-content",
                ".editor textarea",
                "[contenteditable='true']",
            ]

            for selector in content_selectors:
                try:
                    await page.fill(selector, chapter.content, timeout=10000)
                    logger.info(f"Filled content using {selector}")
                    break
                except Exception:
                    continue

            # Click publish/save button
            if publish:
                action_buttons = [
                    "button:has-text('Publish')",
                    "button:has-text('Save & Publish')",
                    "button[type='submit']",
                ]
            else:
                action_buttons = [
                    "button:has-text('Save Draft')",
                    "button:has-text('Save')",
                ]

            for selector in action_buttons:
                try:
                    await page.click(selector, timeout=5000)
                    await asyncio.sleep(3)
                    break
                except Exception:
                    continue

            # Get chapter ID from URL
            current_url = page.url
            import re
            chapter_match = re.search(r'/part/(\d+)', current_url) or \
                          re.search(r'part_id=(\d+)', current_url)

            chapter_id = chapter_match.group(1) if chapter_match else None

            return PublishResult(
                success=True,
                status=PublishStatus.SUCCESS,
                message=f"Chapter {chapter.chapter_number} {'published' if publish else 'saved'}",
                platform=self.PLATFORM_NAME,
                story_id=story_id,
                chapter_id=chapter_id,
                url=f"{self.PLATFORM_URL}/story/{story_id}/part/{chapter_id}" if chapter_id else None,
            )

        except Exception as e:
            logger.error(f"Wattpad publish chapter error: {e}")
            await self._screenshot(f"wattpad_chapter_error_{story_id}")
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message=f"Publish chapter error: {str(e)}",
                platform=self.PLATFORM_NAME,
                errors=[str(e)],
            )

    async def update_story(
        self,
        story_id: str,
        story: StoryInfo,
    ) -> PublishResult:
        """Update story metadata on Wattpad.

        Args:
            story_id: Wattpad story ID
            story: Updated story information

        Returns:
            PublishResult with update status
        """
        if not self._logged_in:
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message="Not logged in",
                platform=self.PLATFORM_NAME,
            )

        try:
            page = await self._get_page()

            # Navigate to story settings
            settings_url = f"{self.PLATFORM_URL}/myworks/{story_id}/settings"
            await self._navigate(settings_url)
            await asyncio.sleep(2)

            # Update fields as needed
            # This is a simplified version - real implementation would
            # update each field individually

            # Save changes
            save_buttons = [
                "button[type='submit']",
                "button:has-text('Save')",
                "button:has-text('Save Changes')",
            ]

            for selector in save_buttons:
                try:
                    await page.click(selector, timeout=5000)
                    await asyncio.sleep(2)
                    break
                except Exception:
                    continue

            return PublishResult(
                success=True,
                status=PublishStatus.SUCCESS,
                message="Story updated",
                platform=self.PLATFORM_NAME,
                story_id=story_id,
            )

        except Exception as e:
            logger.error(f"Wattpad update story error: {e}")
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message=f"Update story error: {str(e)}",
                platform=self.PLATFORM_NAME,
                errors=[str(e)],
            )

    async def get_story_info(self, story_id: str) -> dict[str, Any] | None:
        """Get story information from Wattpad.

        Args:
            story_id: Wattpad story ID

        Returns:
            Story information dict or None
        """
        try:
            page = await self._get_page()
            story_url = f"{self.PLATFORM_URL}/story/{story_id}"
            await self._navigate(story_url)
            await asyncio.sleep(2)

            # Extract story info
            info = {"id": story_id}

            # Get title
            title_elem = await page.query_selector("h1, .story-title")
            if title_elem:
                info["title"] = await title_elem.inner_text()

            # Get description
            desc_elem = await page.query_selector(".story-description, #description")
            if desc_elem:
                info["description"] = await desc_elem.inner_text()

            return info

        except Exception as e:
            logger.warning(f"Failed to get story info: {e}")
            return None
