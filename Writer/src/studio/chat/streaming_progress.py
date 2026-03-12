"""Streaming progress reporter for creative workflow.

This module provides utilities for reporting progress during long-running
generation tasks like outline and character creation.
"""

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from enum import Enum


class GenerationStage(str, Enum):
    """Stages of content generation."""

    STARTING = "starting"
    OUTLINE_STRUCTURE = "outline_structure"  # 正在构建大纲结构
    OUTLINE_CHAPTERS = "outline_chapters"  # 正在生成各章节
    OUTLINE_POLISH = "outline_polish"  # 正在润色大纲
    CHARACTERS_CONCEPT = "characters_concept"  # 正在构思角色
    CHARACTERS_DETAIL = "characters_detail"  # 正在完善角色细节
    CHARACTERS_RELATIONSHIPS = "characters_relationships"  # 正在梳理角色关系
    FINALIZING = "finalizing"  # 正在完成
    COMPLETE = "complete"  # 完成


@dataclass
class ProgressUpdate:
    """A progress update during generation."""

    stage: GenerationStage
    message: str
    progress_percent: int  # 0-100
    detail: str | None = None  # 额外详细信息


class StreamingProgressReporter:
    """Reports progress during content generation.

    Usage:
        reporter = StreamingProgressReporter()

        async for update in reporter.generate_with_progress():
            print(f"{update.progress_percent}%: {update.message}")
    """

    def __init__(self):
        self._callbacks: list[Callable[[ProgressUpdate], None]] = []
        self._current_progress = 0

    def add_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """Add a progress callback."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """Remove a progress callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def report(
        self, stage: GenerationStage, message: str, progress: int, detail: str | None = None
    ) -> None:
        """Report a progress update."""
        self._current_progress = progress
        update = ProgressUpdate(
            stage=stage, message=message, progress_percent=progress, detail=detail
        )
        for callback in self._callbacks:
            try:
                callback(update)
            except Exception:
                pass  # Ignore callback errors

    async def generate_outline_progress(
        self, generate_func, context: str
    ) -> AsyncIterator[ProgressUpdate]:
        """Generate outline with progress updates.

        Args:
            generate_func: The actual generation function
            context: The generation context

        Yields:
            ProgressUpdate objects
        """
        # Stage 1: Starting (0-5%)
        yield ProgressUpdate(
            stage=GenerationStage.STARTING,
            message="🎨 开始生成创意大纲...",
            progress_percent=0,
            detail="分析讨论内容，提取关键要素",
        )

        # Stage 2: Structure (5-20%)
        yield ProgressUpdate(
            stage=GenerationStage.OUTLINE_STRUCTURE,
            message="📐 构建故事结构框架...",
            progress_percent=10,
            detail="设计三幕结构：建置、对抗、解决",
        )

        # Stage 3: Chapters (20-80%) - This is the actual generation
        yield ProgressUpdate(
            stage=GenerationStage.OUTLINE_CHAPTERS,
            message="📖 正在生成48章详细大纲...",
            progress_percent=25,
            detail="第1-12章：第一幕 - 建置",
        )

        # Call the actual generation function
        result = await generate_func(context)

        # Check result and continue progress
        if result and len(result) > 100:
            yield ProgressUpdate(
                stage=GenerationStage.OUTLINE_CHAPTERS,
                message="✨ 大纲主体生成完成",
                progress_percent=70,
                detail="第13-36章：第二幕 - 对抗与发展",
            )

            yield ProgressUpdate(
                stage=GenerationStage.OUTLINE_CHAPTERS,
                message="🎯 生成高潮和结局章节...",
                progress_percent=85,
                detail="第37-48章：第三幕 - 高潮与解决",
            )

        # Stage 4: Polish (80-95%)
        yield ProgressUpdate(
            stage=GenerationStage.OUTLINE_POLISH,
            message="🔍 润色和完善大纲细节...",
            progress_percent=90,
            detail="检查情节连贯性、伏笔设置、角色发展",
        )

        # Stage 5: Complete (95-100%)
        yield ProgressUpdate(
            stage=GenerationStage.COMPLETE,
            message="✅ 大纲生成完成！",
            progress_percent=100,
            detail=f"共生成 {result.count('Chapter') if result else 0} 章内容",
        )



    async def generate_characters_progress(
        self, generate_func, context: str, outline: str
    ) -> AsyncIterator[ProgressUpdate]:
        """Generate characters with progress updates.

        Args:
            generate_func: The actual generation function
            context: The generation context
            outline: The story outline

        Yields:
            ProgressUpdate objects
        """
        # Stage 1: Starting (0-10%)
        yield ProgressUpdate(
            stage=GenerationStage.STARTING,
            message="👤 开始构思角色阵容...",
            progress_percent=0,
            detail="基于大纲分析角色需求",
        )

        # Stage 2: Concept (10-30%)
        yield ProgressUpdate(
            stage=GenerationStage.CHARACTERS_CONCEPT,
            message="💭 设计主角与核心角色...",
            progress_percent=20,
            detail="主角：确定核心欲望、恐惧和成长弧线",
        )

        # Stage 3: Detail (30-70%) - Actual generation
        yield ProgressUpdate(
            stage=GenerationStage.CHARACTERS_DETAIL,
            message="🎭 完善角色详细设定...",
            progress_percent=40,
            detail="生成外貌、性格、背景故事",
        )

        # Call actual generation
        result = await generate_func(context, outline)

        if result and len(result) > 0:
            yield ProgressUpdate(
                stage=GenerationStage.CHARACTERS_DETAIL,
                message=f"✨ 已生成 {len(result)} 个角色",
                progress_percent=65,
                detail="包括主角、反派和重要配角",
            )

        # Stage 4: Relationships (70-90%)
        yield ProgressUpdate(
            stage=GenerationStage.CHARACTERS_RELATIONSHIPS,
            message="🔗 梳理角色之间的关系网...",
            progress_percent=80,
            detail="设计复杂的互动关系和发展弧线",
        )

        # Stage 5: Finalizing (90-100%)
        yield ProgressUpdate(
            stage=GenerationStage.FINALIZING,
            message="📝 最终调整角色设定...",
            progress_percent=95,
            detail="确保角色服务于主题和情节",
        )

        yield ProgressUpdate(
            stage=GenerationStage.COMPLETE,
            message="✅ 角色设定生成完成！",
            progress_percent=100,
            detail=f"共 {len(result) if result else 0} 个完整角色",
        )




class ProgressFormatter:
    """Format progress updates for display."""

    @staticmethod
    def format_progress_bar(percent: int, width: int = 30) -> str:
        """Create a text progress bar.

        Args:
            percent: Progress percentage (0-100)
            width: Width of the progress bar

        Returns:
            Formatted progress bar string
        """
        filled = int(width * percent / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percent}%"

    @staticmethod
    def format_update(update: ProgressUpdate, show_detail: bool = True) -> str:
        """Format a progress update for display.

        Args:
            update: The progress update
            show_detail: Whether to show detail text

        Returns:
            Formatted string
        """
        lines = [
            "",
            ProgressFormatter.format_progress_bar(update.progress_percent),
            f"{update.message}",
        ]

        if show_detail and update.detail:
            lines.append(f"  💡 {update.detail}")

        return "\n".join(lines)

    @staticmethod
    def format_compact(update: ProgressUpdate) -> str:
        """Format a compact single-line progress update.

        Args:
            update: The progress update

        Returns:
            Single line formatted string
        """
        bar = ProgressFormatter.format_progress_bar(update.progress_percent, width=20)
        return f"{bar} {update.message}"
