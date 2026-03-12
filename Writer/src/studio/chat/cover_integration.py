# src/studio/chat/cover_integration.py
"""Cover generation integration for creative workflow."""

import logging
from typing import Any

from src.llm.glm_image import GLMImageGenerator
from src.studio.core.state import NovelProject

logger = logging.getLogger(__name__)


class CoverIntegration:
    """Integrates cover generation into the creative workflow."""

    # Genre to cover style mapping
    GENRE_STYLE_MAP = {
        "fantasy": "fantasy",
        "scifi": "minimalist",
        "romance": "romantic",
        "dark romance": "dark",
        "thriller": "dark",
        "mystery": "dark",
        "horror": "dark",
        "history": "vintage",
        "military": "realistic",
        "action": "realistic",
        "adventure": "fantasy",
        "comedy": "minimalist",
        "drama": "realistic",
    }

    def __init__(self):
        self._generator: GLMImageGenerator | None = None

    def _get_generator(self) -> GLMImageGenerator | None:
        """Lazy initialization of image generator."""
        if self._generator is None:
            try:
                self._generator = GLMImageGenerator()
            except Exception as e:
                logger.error(f"Failed to initialize image generator: {e}")
                return None
        return self._generator

    def is_available(self) -> bool:
        """Check if cover generation is available."""
        generator = self._get_generator()
        return generator is not None and generator.is_available()

    def get_style_for_genre(self, genre: str) -> str:
        """Get recommended cover style for a genre."""
        return self.GENRE_STYLE_MAP.get(genre.lower(), "book cover")

    async def generate_cover_for_project(
        self,
        project: NovelProject,
        custom_description: str | None = None,
        custom_style: str | None = None,
    ) -> dict[str, Any]:
        """Generate a cover for a project.

        Args:
            project: The novel project
            custom_description: Optional custom description
            custom_style: Optional custom style

        Returns:
            Dict with success status, message, and result details
        """
        generator = self._get_generator()

        if not generator or not generator.is_available():
            return {
                "success": False,
                "message": "封面生成不可用。请设置 ZHIPUAI_API_KEY",
                "error": "Image generator not available",
            }

        # Build cover description
        if custom_description:
            description = custom_description
        else:
            # Use project premise or build from available info
            description = project.premise or f"A {project.genre} story"

            # Add themes if available
            if project.themes:
                description += f". Themes: {', '.join(project.themes)}"

            # Add tone if available
            if project.tone:
                description += f". Tone: {project.tone}"

        # Get style
        style = custom_style or self.get_style_for_genre(project.genre)

        try:
            # Generate cover
            result = generator.generate_cover(
                title=project.title,
                genre=project.genre,
                description=description[:500],  # Limit length
                style=style,
            )

            if result.success:
                # Save cover path to project
                if result.local_path:
                    project.cover_image_path = result.local_path

                return {
                    "success": True,
                    "message": "✅ 封面生成成功！",
                    "cover_path": result.local_path,
                    "cover_url": result.image_url,
                    "style": style,
                    "prompt": result.prompt,
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ 封面生成失败: {result.error}",
                    "error": result.error,
                }

        except Exception as e:
            logger.error(f"Cover generation error: {e}")
            return {
                "success": False,
                "message": f"❌ 生成封面时出错: {e}",
                "error": str(e),
            }

    async def generate_cover_from_discussion(
        self,
        project: NovelProject,
        discussion_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate cover based on discussion context.

        This creates a more tailored cover prompt based on the
        creative discussion that led to the project.

        Args:
            project: The novel project
            discussion_context: Context from creative discussion

        Returns:
            Dict with generation result
        """
        # Build enhanced description from discussion
        description_parts = [project.premise or f"A {project.genre} story"]

        # Add character info if available
        if "main_character" in discussion_context:
            char = discussion_context["main_character"]
            description_parts.append(f"Main character: {char}")

        # Add setting info if available
        if "setting" in discussion_context:
            description_parts.append(f"Setting: {discussion_context['setting']}")

        # Add mood/atmosphere
        if project.tone:
            description_parts.append(f"Atmosphere: {project.tone}")

        # Combine into rich description
        description = ". ".join(description_parts)

        # Get appropriate style
        style = self.get_style_for_genre(project.genre)

        return await self.generate_cover_for_project(
            project=project,
            custom_description=description,
            custom_style=style,
        )

    def generate_cover_prompt_suggestion(
        self,
        title: str,
        genre: str,
        premise: str,
        themes: list[str],
    ) -> str:
        """Generate a suggested cover description for user review.

        This is used to show the user what kind of cover will be
        generated before actually calling the API.

        Args:
            title: Book title
            genre: Book genre
            premise: Book premise
            themes: Book themes

        Returns:
            A suggested cover description
        """
        style = self.get_style_for_genre(genre)

        prompt = f"""基于你的创意，建议的封面设计：

**书名:** 《{title}》
**风格:** {style}
**类型:** {genre}

**设计元素建议:**
"""

        # Add genre-specific suggestions
        if genre.lower() in ["fantasy", "奇幻"]:
            prompt += """
• 魔法元素（龙、法术光芒、神秘符文）
• 史诗感背景（城堡、山脉、星空）
• 主角剪影或神秘人物
• 金/蓝/紫色调
"""
        elif genre.lower() in ["romance", "romantic", "言情"]:
            prompt += """
• 浪漫元素（玫瑰、心形、柔和光线）
• 情侣剪影或亲密场景
• 温暖色调（红/粉/金）
• 优雅字体
"""
        elif genre.lower() in ["thriller", "mystery", "horror", "悬疑", "恐怖"]:
            prompt += """
• 悬疑元素（阴影、迷雾、暗角）
• 紧张氛围（红色点缀、锐利线条）
• 暗色调（黑/深蓝/深红）
• 神秘感
"""
        elif genre.lower() in ["scifi", "science fiction", "科幻"]:
            prompt += """
• 科幻元素（飞船、城市、科技光效）
• 未来感设计
• 冷色调（蓝/银/白）
• 简洁现代
"""
        else:
            prompt += """
• 符合类型特征的视觉元素
• 引人注目的构图
• 专业书籍封面质感
"""

        if themes:
            prompt += f"\n**主题呼应:** {', '.join(themes[:3])}\n"

        prompt += """
💡 使用 `/cover generate` 生成封面
💡 使用 `/cover generate --style <风格>` 改变风格
"""

        return prompt

    async def regenerate_cover_with_feedback(
        self,
        project: NovelProject,
        feedback: str,
        previous_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Regenerate cover based on user feedback.

        Args:
            project: The novel project
            feedback: User feedback for improvement
            previous_result: Previous generation result if any

        Returns:
            New generation result
        """
        # Build improved description based on feedback
        base_description = project.premise or f"A {project.genre} story"

        # Add feedback as instructions
        improved_description = f"""{base_description}

Important requirements based on user feedback:
{feedback}

Make sure to incorporate these requirements into the design."""

        # Try different style if feedback suggests it
        style = self.get_style_for_genre(project.genre)
        if "明亮" in feedback or "brighter" in feedback.lower():
            style = "light " + style
        elif "黑暗" in feedback or "darker" in feedback.lower():
            style = "dark " + style

        return await self.generate_cover_for_project(
            project=project,
            custom_description=improved_description,
            custom_style=style,
        )
