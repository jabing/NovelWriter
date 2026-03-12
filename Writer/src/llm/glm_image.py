# src/llm/glm_image.py
"""GLM-4V Image Generation integration.

This module provides integration with ZhipuAI's GLM-4V model for image generation.
API Documentation: https://open.bigmodel.cn/dev/api#text-to-image
"""

import base64
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationResult:
    """Result of an image generation request."""
    success: bool
    image_url: str | None = None
    image_base64: str | None = None
    local_path: str | None = None
    error: str | None = None
    prompt: str = ""
    revised_prompt: str = ""  # Prompt as revised by the model
    model: str = ""
    created_at: str = ""


class GLMImageGenerator:
    """GLM-4V Image Generation client using ZhipuAI API.

    Supports text-to-image generation with the GLM-4V model.
    Requires ZHIPUAI_API_KEY environment variable.
    """

    # ZhipuAI API base URL
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    # Available models for image generation
    MODELS = {
        "cogview-3": "High quality text-to-image model",
        "cogview-3-plus": "Premium quality with better details",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "cogview-3",
        output_dir: str | None = None,
    ) -> None:
        """Initialize GLM Image Generator.

        Args:
            api_key: ZhipuAI API key (defaults to ZHIPUAI_API_KEY env var)
            model: Image generation model to use
            output_dir: Directory to save generated images (defaults to ./generated_images)
        """
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not self.api_key:
            logger.warning("ZHIPUAI_API_KEY not set. Image generation will be disabled.")

        self.model = model
        self.output_dir = Path(output_dir or "./generated_images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._client = None

    def _get_client(self) -> Any:
        """Lazy initialization of ZhipuAI client."""
        if self._client is None:
            try:
                from zhipuai import ZhipuAI
            except ImportError:
                raise ImportError(
                    "zhipuai package required. Install with: pip install zhipuai"
                )

            self._client = ZhipuAI(api_key=self.api_key)
        return self._client

    def generate_image(
        self,
        prompt: str,
        style: str | None = None,
        size: str = "1024x1024",
        save_locally: bool = True,
        filename_prefix: str = "generated",
    ) -> ImageGenerationResult:
        """Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate
            style: Optional style modifier (e.g., "realistic", "anime", "oil painting")
            size: Image size (e.g., "1024x1024", "768x1024")
            save_locally: Whether to save the image locally
            filename_prefix: Prefix for the saved filename

        Returns:
            ImageGenerationResult with the result details
        """
        if not self.api_key:
            return ImageGenerationResult(
                success=False,
                error="ZHIPUAI_API_KEY not configured. Please set the environment variable.",
                prompt=prompt,
            )

        # Enhance prompt with style if provided
        enhanced_prompt = f"{prompt}, {style} style" if style else prompt

        try:
            client = self._get_client()

            # Call the image generation API
            response = client.images.generations(
                model=self.model,
                prompt=enhanced_prompt,
                size=size,
            )

            # Extract image data from response
            if hasattr(response, 'data') and response.data:
                image_data = response.data[0]
                image_url = getattr(image_data, 'url', None)
                image_b64 = getattr(image_data, 'b64_json', None)
                revised_prompt = getattr(image_data, 'revised_prompt', enhanced_prompt)

                result = ImageGenerationResult(
                    success=True,
                    image_url=image_url,
                    image_base64=image_b64,
                    prompt=prompt,
                    revised_prompt=revised_prompt,
                    model=self.model,
                    created_at=datetime.now().isoformat(),
                )

                # Save image locally if requested
                if save_locally and (image_url or image_b64):
                    result.local_path = self._save_image(
                        image_url=image_url,
                        image_b64=image_b64,
                        prefix=filename_prefix,
                    )

                return result
            else:
                return ImageGenerationResult(
                    success=False,
                    error="No image data in response",
                    prompt=prompt,
                )

        except ImportError as e:
            return ImageGenerationResult(
                success=False,
                error=f"Missing dependency: {e}. Install with: pip install zhipuai",
                prompt=prompt,
            )
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return ImageGenerationResult(
                success=False,
                error=str(e),
                prompt=prompt,
            )

    def _save_image(
        self,
        image_url: str | None,
        image_b64: str | None,
        prefix: str = "generated",
    ) -> str | None:
        """Save generated image to local file.

        Args:
            image_url: URL of the image
            image_b64: Base64 encoded image data
            prefix: Filename prefix

        Returns:
            Path to saved file or None on failure
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.png"
            filepath = self.output_dir / filename

            if image_b64:
                # Save from base64 data
                image_data = base64.b64decode(image_b64)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                logger.info(f"Image saved to {filepath}")
                return str(filepath)

            elif image_url:
                # Download from URL
                import urllib.request
                urllib.request.urlretrieve(image_url, filepath)
                logger.info(f"Image downloaded to {filepath}")
                return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save image: {e}")

        return None

    def generate_cover(
        self,
        title: str,
        genre: str,
        description: str,
        style: str = "book cover",
    ) -> ImageGenerationResult:
        """Generate a book cover image.

        Args:
            title: Book title
            genre: Book genre
            description: Brief description of the book's theme/setting
            style: Art style for the cover

        Returns:
            ImageGenerationResult with the generated cover
        """
        prompt = f"""Book cover for "{title}" - A {genre} novel.
{description}
Professional book cover design, eye-catching, suitable for online publishing platforms."""

        return self.generate_image(
            prompt=prompt,
            style=style,
            save_locally=True,
            filename_prefix=f"cover_{title.replace(' ', '_')[:30]}",
        )

    def generate_illustration(
        self,
        scene_description: str,
        characters: list[str] | None = None,
        mood: str = "dramatic",
        style: str = "digital art",
    ) -> ImageGenerationResult:
        """Generate an illustration for a scene.

        Args:
            scene_description: Description of the scene to illustrate
            characters: List of characters in the scene
            mood: Mood/atmosphere of the scene
            style: Art style for the illustration

        Returns:
            ImageGenerationResult with the generated illustration
        """
        char_text = ""
        if characters:
            char_text = f"Characters: {', '.join(characters)}. "

        prompt = f"""{scene_description}
{char_text}Mood: {mood}.
High quality illustration suitable for a novel."""

        return self.generate_image(
            prompt=prompt,
            style=style,
            save_locally=True,
            filename_prefix="illustration",
        )

    def is_available(self) -> bool:
        """Check if the image generator is properly configured."""
        return bool(self.api_key)
