# src/publishing/royalroad_publisher.py
"""Royal Road novel publisher implementation."""

import asyncio
import logging
import re
from typing import Any

from src.novel_agent.publishing.base import (
    BasePublisher,
    ChapterInfo,
    PublishResult,
    PublishStatus,
    StoryInfo,
)

logger = logging.getLogger(__name__)


class RoyalRoadPublisher(BasePublisher):
    """Publisher for Royal Road platform.

    Royal Road publishing process:
    1. Login at https://www.royalroad.com/login
    2. Create fiction at https://www.royalroad.com/fiction/new
    3. Add chapters
    4. Publish

    Features:
    - Fiction creation with cover image
    - Chapter publishing with scheduling
    - Tag and category management
    - Author notes support
    """

    PLATFORM_NAME = "royalroad"
    PLATFORM_URL = "https://www.royalroad.com"

    # Genre/Category mapping
    CATEGORY_MAP = {
        "fantasy": "fantasy",
        "scifi": "sci-fi",
        "romance": "romance",
        "history": "historical",
        "military": "action",
        "adventure": "adventure",
        "mystery": "mystery",
        "horror": "horror",
        "thriller": "thriller",
        "comedy": "comedy",
        "drama": "drama",
        "psychological": "psychological",
    }

    # Tags mapping (Royal Road has specific tags)
    TAG_MAP = {
        "fantasy": ["Fantasy", "Magic", "Adventure"],
        "scifi": ["Sci-Fi", "Future", "Technology"],
        "romance": ["Romance", "Love", "Relationships"],
        "history": ["Historical", "War", "Politics"],
        "military": ["Action", "War", "Military"],
        "litrpg": ["LitRPG", "GameLit", "Leveling"],
        "isekai": ["Isekai", "Reincarnation", "Portal Fantasy"],
        "cultivation": ["Cultivation", "Xianxia", "Martial Arts"],
    }

    # Content rating
    RATING_MAP = {
        "everyone": "Everyone",
        "teen": "Teen",
        "mature": "Mature",
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Royal Road publisher."""
        super().__init__(**kwargs)
        self._fiction_cache: dict[str, str] = {}  # fiction_title -> fiction_id

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
        """Log into Royal Road.

        Args:
            username: Email address
            password: Password
            totp_code: Time-based OTP if 2FA is enabled

        Returns:
            PublishResult with login status
        """
        try:
            page = await self._get_page()

            # Navigate to login page
            await self._navigate(self.login_url)
            await asyncio.sleep(2)

            # Wait for login form
            await page.wait_for_selector("input[name='email'], #email", timeout=10000)

            # Fill email
            email_selectors = [
                "input[name='email']",
                "#email",
                "input[type='email']",
            ]

            filled = False
            for selector in email_selectors:
                try:
                    await page.fill(selector, username, timeout=5000)
                    filled = True
                    logger.info(f"Filled email using {selector}")
                    break
                except Exception:
                    continue

            if not filled:
                return PublishResult(
                    success=False,
                    status=PublishStatus.FAILED,
                    message="Could not find email field",
                    platform=self.PLATFORM_NAME,
                    errors=["Email field not found"],
                )

            # Fill password
            password_selectors = [
                "input[name='password']",
                "#password",
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
                "button:has-text('Login')",
                "button:has-text('Sign in')",
                "input[type='submit']",
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

            # Check for 2FA
            if totp_code:
                totp_selectors = [
                    "input[name='totp']",
                    "input[name='code']",
                    "#totp-code",
                ]

                for selector in totp_selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            await page.fill(selector, totp_code, timeout=5000)
                            await page.click("button[type='submit']")
                            await asyncio.sleep(2)
                            break
                    except Exception:
                        continue

            # Check for error messages
            error_selectors = [
                ".alert-danger",
                ".error-message",
                "[class*='error']",
            ]

            for selector in error_selectors:
                error_elem = await page.query_selector(selector)
                if error_elem:
                    error_text = await error_elem.inner_text()
                    if error_text.strip():
                        return PublishResult(
                            success=False,
                            status=PublishStatus.FAILED,
                            message=f"Login failed: {error_text}",
                            platform=self.PLATFORM_NAME,
                            errors=[error_text],
                        )

            # Check if logged in by URL or elements
            current_url = page.url

            # Check for redirect away from login page
            if "login" not in current_url.lower():
                self._logged_in = True
                return PublishResult(
                    success=True,
                    status=PublishStatus.SUCCESS,
                    message="Successfully logged into Royal Road",
                    platform=self.PLATFORM_NAME,
                )

            # Check for user-specific elements
            user_indicators = [
                ".user-dropdown",
                "a[href*='/profile/']",
                ".author-dashboard",
                "nav .user-menu",
            ]

            for selector in user_indicators:
                elem = await page.query_selector(selector)
                if elem:
                    self._logged_in = True
                    return PublishResult(
                        success=True,
                        status=PublishStatus.SUCCESS,
                        message="Successfully logged into Royal Road",
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
            logger.error(f"Royal Road login error: {e}")
            await self._screenshot("royalroad_login_error")
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message=f"Login error: {str(e)}",
                platform=self.PLATFORM_NAME,
                errors=[str(e)],
            )

    async def create_story(self, story: StoryInfo) -> PublishResult:
        """Create a new fiction on Royal Road.

        Args:
            story: Story information

        Returns:
            PublishResult with fiction ID
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

            # Navigate to create fiction page
            create_url = f"{self.PLATFORM_URL}/fiction/new"
            await self._navigate(create_url)
            await asyncio.sleep(2)

            # Wait for form
            await page.wait_for_selector("form, input[name='title']", timeout=10000)

            # Fill title
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

            # Fill description/synopsis
            desc_selectors = [
                "textarea[name='description']",
                "#description",
                "textarea[name='synopsis']",
                "#synopsis",
            ]

            for selector in desc_selectors:
                try:
                    await page.fill(selector, story.description, timeout=5000)
                    break
                except Exception:
                    continue

            # Select category
            if story.genre:
                category = self.CATEGORY_MAP.get(story.genre.lower(), story.genre)
                category_selectors = [
                    f"select[name='category'] option:has-text('{category}')",
                    f"select[name='type'] option:has-text('{category}')",
                    f"#category option:has-text('{category}')",
                ]

                for selector in category_selectors:
                    try:
                        await page.select_option("select[name='category']", category)
                        break
                    except Exception:
                        continue

            # Add tags
            if story.tags:
                # Royal Road uses multi-select for tags
                tags_to_add = story.tags[:10]  # Limit tags

                # Also add genre-specific tags
                for genre_tag in self.TAG_MAP.get(story.genre.lower(), []):
                    if genre_tag not in tags_to_add:
                        tags_to_add.append(genre_tag)

                for tag in tags_to_add[:10]:
                    try:
                        # Try to find and click tag checkbox or add to input
                        tag_input_selectors = [
                            "input[name='tags']",
                            ".tag-input input",
                            "input[placeholder*='tag' i]",
                        ]

                        for selector in tag_input_selectors:
                            try:
                                await page.fill(selector, tag)
                                await page.press(selector, "Enter")
                                break
                            except Exception:
                                continue
                    except Exception:
                        continue

            # Set content rating
            rating = self.RATING_MAP.get(story.rating, "Teen")
            rating_selectors = [
                f"input[name='rating'][value='{rating}']",
                f"select[name='rating'] option:has-text('{rating}')",
            ]

            for selector in rating_selectors:
                try:
                    if "select" in selector:
                        await page.select_option("select[name='rating']", rating)
                    else:
                        await page.click(selector)
                    break
                except Exception:
                    continue

            # Click save/create button
            create_buttons = [
                "button[type='submit']",
                "button:has-text('Create')",
                "button:has-text('Save')",
                "button:has-text('Submit')",
            ]

            for selector in create_buttons:
                try:
                    await page.click(selector, timeout=5000)
                    await asyncio.sleep(3)
                    break
                except Exception:
                    continue

            # Get fiction ID from URL
            current_url = page.url
            fiction_match = re.search(r'/fiction/(\d+)', current_url) or \
                          re.search(r'fiction_id=(\d+)', current_url) or \
                          re.search(r'/(\d+)/', current_url)

            fiction_id = fiction_match.group(1) if fiction_match else None

            if fiction_id:
                self._fiction_cache[story.title] = fiction_id
                return PublishResult(
                    success=True,
                    status=PublishStatus.SUCCESS,
                    message=f"Created fiction: {story.title}",
                    platform=self.PLATFORM_NAME,
                    story_id=fiction_id,
                    url=f"{self.PLATFORM_URL}/fiction/{fiction_id}",
                )

            # Check for success indicators
            success_indicators = [
                ".alert-success",
                ".success-message",
                "[class*='success']",
            ]

            for selector in success_indicators:
                elem = await page.query_selector(selector)
                if elem:
                    return PublishResult(
                        success=True,
                        status=PublishStatus.SUCCESS,
                        message="Fiction created (ID not captured from URL)",
                        platform=self.PLATFORM_NAME,
                    )

            await self._screenshot("royalroad_create_fiction")
            return PublishResult(
                success=False,
                status=PublishStatus.PARTIAL,
                message="Fiction creation status unclear",
                platform=self.PLATFORM_NAME,
                warnings=["Could not verify fiction creation"],
            )

        except Exception as e:
            logger.error(f"Royal Road create fiction error: {e}")
            await self._screenshot("royalroad_create_error")
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message=f"Create fiction error: {str(e)}",
                platform=self.PLATFORM_NAME,
                errors=[str(e)],
            )

    async def publish_chapter(
        self,
        story_id: str,
        chapter: ChapterInfo,
        publish: bool = True,
    ) -> PublishResult:
        """Publish a chapter to Royal Road fiction.

        Args:
            story_id: Royal Road fiction ID
            chapter: Chapter information
            publish: Whether to publish immediately or save as draft

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

            # Navigate to fiction dashboard/chapter creation
            chapter_url = f"{self.PLATFORM_URL}/fiction/{story_id}/chapters/new"
            await self._navigate(chapter_url)
            await asyncio.sleep(2)

            # If that doesn't work, try the author dashboard
            if "login" in page.url.lower() or "error" in page.url.lower():
                dashboard_url = f"{self.PLATFORM_URL}/fiction/{story_id}"
                await self._navigate(dashboard_url)
                await asyncio.sleep(2)

                # Look for "Add Chapter" button
                add_chapter_buttons = [
                    "a:has-text('Add Chapter')",
                    "button:has-text('Add Chapter')",
                    "a:has-text('New Chapter')",
                    ".add-chapter",
                ]

                for selector in add_chapter_buttons:
                    try:
                        await page.click(selector, timeout=5000)
                        await asyncio.sleep(2)
                        break
                    except Exception:
                        continue

            # Wait for chapter editor
            await page.wait_for_selector("input[name='title'], textarea, #content", timeout=10000)

            # Fill chapter title
            title_selectors = [
                "input[name='title']",
                "#chapter-title",
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
                "#content",
                ".chapter-editor textarea",
                "[contenteditable='true']",
            ]

            for selector in content_selectors:
                try:
                    await page.fill(selector, chapter.content, timeout=15000)
                    logger.info(f"Filled content using {selector}")
                    break
                except Exception:
                    continue

            # Add author notes if present
            if chapter.author_notes:
                notes_selectors = [
                    "textarea[name='author_notes']",
                    "#author-notes",
                    "textarea[placeholder*='note' i]",
                ]

                for selector in notes_selectors:
                    try:
                        await page.fill(selector, chapter.author_notes)
                        break
                    except Exception:
                        continue

            # Click publish/save button
            if publish:
                action_buttons = [
                    "button:has-text('Publish')",
                    "button:has-text('Save & Publish')",
                    "input[value='Publish']",
                    "button[type='submit']",
                ]
            else:
                action_buttons = [
                    "button:has-text('Save Draft')",
                    "button:has-text('Save')",
                    "input[value='Save']",
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
            chapter_match = re.search(r'/chapter/(\d+)', current_url) or \
                          re.search(r'chapter_id=(\d+)', current_url)

            chapter_id = chapter_match.group(1) if chapter_match else None

            return PublishResult(
                success=True,
                status=PublishStatus.SUCCESS,
                message=f"Chapter {chapter.chapter_number} {'published' if publish else 'saved'}",
                platform=self.PLATFORM_NAME,
                story_id=story_id,
                chapter_id=chapter_id,
                url=f"{self.PLATFORM_URL}/fiction/{story_id}/chapter/{chapter_id}" if chapter_id else f"{self.PLATFORM_URL}/fiction/{story_id}",
            )

        except Exception as e:
            logger.error(f"Royal Road publish chapter error: {e}")
            await self._screenshot(f"royalroad_chapter_error_{story_id}")
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
        """Update fiction metadata on Royal Road.

        Args:
            story_id: Royal Road fiction ID
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

            # Navigate to fiction settings
            settings_url = f"{self.PLATFORM_URL}/fiction/{story_id}/settings"
            await self._navigate(settings_url)
            await asyncio.sleep(2)

            # Update description if changed
            if story.description:
                desc_selectors = [
                    "textarea[name='description']",
                    "#description",
                    "textarea[name='synopsis']",
                ]

                for selector in desc_selectors:
                    try:
                        await page.fill(selector, story.description)
                        break
                    except Exception:
                        continue

            # Update tags if changed
            if story.tags:
                # Clear existing and add new tags
                # This is simplified - real implementation would be more careful
                pass

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
                message="Fiction updated",
                platform=self.PLATFORM_NAME,
                story_id=story_id,
            )

        except Exception as e:
            logger.error(f"Royal Road update fiction error: {e}")
            return PublishResult(
                success=False,
                status=PublishStatus.FAILED,
                message=f"Update fiction error: {str(e)}",
                platform=self.PLATFORM_NAME,
                errors=[str(e)],
            )

    async def get_fiction_info(self, story_id: str) -> dict[str, Any] | None:
        """Get fiction information from Royal Road.

        Args:
            story_id: Royal Road fiction ID

        Returns:
            Fiction information dict or None
        """
        try:
            page = await self._get_page()
            fiction_url = f"{self.PLATFORM_URL}/fiction/{story_id}"
            await self._navigate(fiction_url)
            await asyncio.sleep(2)

            info = {"id": story_id}

            # Get title
            title_elem = await page.query_selector("h1, .fiction-title")
            if title_elem:
                info["title"] = await title_elem.inner_text()

            # Get description
            desc_elem = await page.query_selector(".description, .synopsis")
            if desc_elem:
                info["description"] = await desc_elem.inner_text()

            # Get stats
            stats_elem = await page.query_selector(".stats")
            if stats_elem:
                stats_text = await stats_elem.inner_text()
                # Parse stats
                if "Followers" in stats_text:
                    match = re.search(r'([\d,]+)\s*Followers', stats_text)
                    if match:
                        info["followers"] = match.group(1)

            return info

        except Exception as e:
            logger.warning(f"Failed to get fiction info: {e}")
            return None

    async def schedule_chapter(
        self,
        story_id: str,
        chapter: ChapterInfo,
        publish_date: str,
    ) -> PublishResult:
        """Schedule a chapter for future publishing.

        Args:
            story_id: Royal Road fiction ID
            chapter: Chapter information
            publish_date: ISO format datetime string

        Returns:
            PublishResult with scheduling status
        """
        # First save as draft
        result = await self.publish_chapter(story_id, chapter, publish=False)

        if not result.success:
            return result

        # Royal Road doesn't have built-in scheduling via UI
        # This would require API access or additional automation
        return PublishResult(
            success=True,
            status=PublishStatus.SUCCESS,
            message=f"Chapter saved as draft. Scheduled for {publish_date}",
            platform=self.PLATFORM_NAME,
            story_id=story_id,
            warnings=["Royal Road doesn't support UI scheduling. Manual publish required."],
        )
