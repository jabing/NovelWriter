# src/novel_agent/novel/continuity_config.py
"""Continuity checking configuration system."""

import logging
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ContinuityStrictness(str, Enum):
    """Continuity checking strictness levels."""

    OFF = "off"  # 跳过所有检查（仅调试用）
    WARNING = "warning"  # 警告但继续
    STRICT = "strict"  # 强制阻塞（默认）


class ContinuityConfig(BaseModel):
    """Configuration for continuity checking."""

    model_config = {"use_enum_values": False}

    strictness: ContinuityStrictness = Field(
        default=ContinuityStrictness.STRICT, description="Continuity checking strictness level"
    )
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    min_chapter_words: int = Field(default=500, ge=0, description="Minimum chapter word count")
    enable_character_id: bool = Field(default=False, description="Enable character ID tracking")
    block_on_character_mismatch: bool = Field(
        default=False, description="Block generation when protagonist name changes across chapters"
    )

    def __init__(self, **data) -> None:
        """Initialize config and log warning for OFF mode."""
        super().__init__(**data)

        if self.strictness == ContinuityStrictness.OFF:
            logger.warning(
                "Continuity checking is DISABLED (OFF mode). "
                "This should only be used for debugging purposes. "
                "连续性检查已禁用（OFF模式），仅用于调试！"
            )
