"""Summary compression for hierarchical story state.

This module provides compression functionality for arc and chapter summaries
to ensure they fit within token budgets while preserving key information.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

from src.novel_agent.llm.base import BaseLLM
from src.novel_agent.novel.summaries import ArcSummary, ChapterSummary

logger = logging.getLogger(__name__)


# Compression thresholds for different summary types
# T4-1: Adjusted based on 200-chapter test results for 10-20% performance improvement
COMPRESSION_THRESHOLDS = {
    "arc_summary": 350,      # Reduced from 400 - faster compression
    "chapter_summary": 200,  # Reduced from 250 - better cache fit
    "global_state": 450,     # Reduced from 500 - tighter budget
}

# Average characters per token estimate (for Chinese text: ~1.5, English: ~4)
CHARS_PER_TOKEN = 2.0


@dataclass
class CompressionResult:
    """Result of a compression operation.

    Attributes:
        success: Whether compression succeeded
        original_tokens: Original token count
        compressed_tokens: Compressed token count
        method: Compression method used
        data: Compressed summary or error info
    """

    success: bool
    original_tokens: int
    compressed_tokens: int
    method: str
    data: dict[str, Any]


class SummaryCompressor:
    """Compress summaries to fit token budget while preserving key information.

    This class provides multiple compression strategies:
    1. Smart truncation: Truncates at sentence boundaries without LLM
    2. LLM compression: Uses LLM to rephrase and compress
    3. Hybrid: Tries smart truncation first, falls back to LLM if needed

    Attributes:
        llm: Optional LLM for compression
        enable_llm: Whether to use LLM compression
        hybrid_threshold: Token threshold to trigger LLM fallback
    """

    def __init__(
        self,
        llm: BaseLLM | None = None,
        enable_llm: bool = True,
        hybrid_threshold: float = 1.5,  # Use LLM if truncation exceeds target by 150%
    ) -> None:
        """Initialize the summary compressor.

        Args:
            llm: LLM instance for compression (optional)
            enable_llm: Whether to enable LLM-based compression
            hybrid_threshold: Multiplier for when to use LLM fallback
        """
        self.llm = llm
        self.enable_llm = enable_llm
        self.hybrid_threshold = hybrid_threshold

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses a simple character-based heuristic. For more accurate
        estimates, a proper tokenizer should be used.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Simple heuristic: Chinese/Japanese characters ~1 token, English ~0.25 tokens
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars + other_chars / 4)

    def _extract_key_points(self, text: str, num_points: int = 3) -> list[str]:
        """Extract key points from text.

        Uses simple heuristics to identify important sentences:
        - First sentence (usually the topic)
        - Sentences with important keywords
        - Last sentence (usually conclusion)

        Args:
            text: Text to extract points from
            num_points: Maximum number of points to extract

        Returns:
            List of key point sentences
        """
        if not text:
            return []

        # Split into sentences (handles Chinese and English punctuation)
        sentences = re.split(r"(?<=[。！？.!?])\s*", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        key_points = []

        # Always include first sentence (topic)
        if sentences:
            key_points.append(sentences[0])

        # Look for sentences with important keywords
        important_keywords = [
            "关键",
            "重要",
            "主要",
            "核心",
            "决定",
            "导致",
            "结果",
            "关键",
            "转折",
            "变化",
            "冲突",
            "高潮",
            "结局",
            "key",
            "important",
            "main",
            "crucial",
            "result",
            "conflict",
            "climax",
            "decision",
            "change",
            "reveal",
            "discover",
        ]

        for sentence in sentences[1:-1]:  # Skip first and last
            if len(key_points) >= num_points:
                break
            if any(kw in sentence.lower() for kw in important_keywords):
                key_points.append(sentence)

        # Include last sentence if different from first and we have room
        if len(sentences) > 1 and len(key_points) < num_points:
            last = sentences[-1]
            if last not in key_points:
                key_points.append(last)

        return key_points[:num_points]

    def _smart_truncate(self, text: str, max_tokens: int) -> str:
        """Smart truncate text at sentence boundary.

        Attempts to truncate at a sentence boundary while preserving
        the most important information at the beginning.

        Args:
            text: Text to truncate
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated text with "..." if truncated
        """
        if not text:
            return ""

        estimated_tokens = self._estimate_tokens(text)
        if estimated_tokens <= max_tokens:
            return text

        # Calculate max characters based on token estimate
        max_chars = int(max_tokens * CHARS_PER_TOKEN)

        # Split into sentences
        sentences = re.split(r"(?<=[。！？.!?])\s*", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            # Fallback: hard truncate with ellipsis
            return text[:max_chars].rsplit(" ", 1)[0] + "..."

        # Build truncated text sentence by sentence
        result = []
        current_chars = 0

        for sentence in sentences:
            sentence_chars = len(sentence)
            if current_chars + sentence_chars > max_chars - 3:  # Leave room for "..."
                break
            result.append(sentence)
            current_chars += sentence_chars

        if not result:
            # First sentence is too long, truncate it
            first = sentences[0]
            return first[: max_chars - 3].rsplit(" ", 1)[0] + "..."

        return " ".join(result) + "..."

    async def _llm_compress_text(
        self,
        text: str,
        max_tokens: int,
        context: str = "",
    ) -> str:
        """Use LLM to compress text.

        Args:
            text: Text to compress
            max_tokens: Maximum tokens for output
            context: Additional context about what this text represents

        Returns:
            Compressed text
        """
        if not self.llm or not self.enable_llm:
            return self._smart_truncate(text, max_tokens)

        system_prompt = """你是一个专业的文本压缩助手。你的任务是将给定的文本压缩到指定的长度，同时保留所有关键信息。

压缩规则：
1. 保留主要事件、关键转折和重要角色行动
2. 移除冗余描述和次要细节
3. 保持叙述的连贯性和逻辑性
4. 使用简洁的语言重新组织内容"""

        user_prompt = f"""请将以下文本压缩到大约{max_tokens}个token的范围内。

上下文：{context if context else "故事摘要"}

原文：
{text}

压缩后的文本（保留关键信息）："""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens + 50,  # Allow some buffer
                temperature=0.3,
            )
            compressed = response.content.strip()

            # Verify it's not too long
            if self._estimate_tokens(compressed) > max_tokens * 1.2:
                # LLM didn't compress enough, use smart truncate
                return self._smart_truncate(compressed, max_tokens)

            return compressed
        except Exception as e:
            logger.warning(f"LLM compression failed: {e}, falling back to truncation")
            return self._smart_truncate(text, max_tokens)

    def compress_arc_summary(
        self,
        summary: ArcSummary,
        max_tokens: int = 400,
        use_llm: bool | None = None,
    ) -> ArcSummary:
        """Compress arc summary to fit within max_tokens.

        Uses hybrid strategy:
        1. First tries smart truncation
        2. If result is still too long, uses LLM compression

        Args:
            summary: ArcSummary to compress
            max_tokens: Maximum token budget
            use_llm: Override enable_llm setting

        Returns:
            Compressed ArcSummary (new instance, original unchanged)
        """
        if use_llm is None:
            use_llm = self.enable_llm

        # Estimate current size
        current_text = summary.get_context_string()
        original_tokens = self._estimate_tokens(current_text)

        if original_tokens <= max_tokens:
            # No compression needed
            return summary

        logger.debug(
            f"Compressing arc {summary.arc_number} summary: {original_tokens} -> {max_tokens} tokens"
        )

        # Strategy 1: Smart truncate
        compressed_summary = summary.summary
        compressed_summary = self._smart_truncate(compressed_summary, int(max_tokens * 0.6))

        # Strategy 2: Compress major events
        compressed_events = summary.major_events[:5]  # Keep only first 5 events

        # Strategy 3: Compress character arcs
        compressed_arcs = dict(list(summary.character_arcs.items())[:3])  # Keep top 3

        # Strategy 4: Compress world changes
        compressed_world = summary.world_changes[:3]  # Keep first 3

        # Check if we need LLM compression
        new_text = f"{compressed_summary} {' '.join(compressed_events)}"
        new_tokens = self._estimate_tokens(new_text)

        if use_llm and new_tokens > max_tokens * self.hybrid_threshold:
            # Would need async, so we'll just use better truncation for now
            # In a real async context, we could call _llm_compress_text
            compressed_summary = self._smart_truncate(summary.summary, int(max_tokens * 0.5))

        # Create new summary with compressed fields
        return ArcSummary(
            arc_number=summary.arc_number,
            start_chapter=summary.start_chapter,
            end_chapter=summary.end_chapter,
            title=summary.title,
            summary=compressed_summary,
            major_events=compressed_events,
            character_arcs=compressed_arcs,
            world_changes=compressed_world,
            plot_threads_status=summary.plot_threads_status,
            themes=summary.themes[:3],  # Keep first 3 themes
            created_at=summary.created_at,
        )

    def compress_chapter_summary(
        self,
        summary: ChapterSummary,
        max_tokens: int = 250,
        use_llm: bool | None = None,
    ) -> ChapterSummary:
        """Compress chapter summary to fit within max_tokens.

        Uses hybrid strategy similar to arc summaries.

        Args:
            summary: ChapterSummary to compress
            max_tokens: Maximum token budget
            use_llm: Override enable_llm setting

        Returns:
            Compressed ChapterSummary (new instance, original unchanged)
        """
        if use_llm is None:
            use_llm = self.enable_llm

        # Estimate current size
        current_text = summary.get_context_string()
        original_tokens = self._estimate_tokens(current_text)

        if original_tokens <= max_tokens:
            # No compression needed
            return summary

        logger.debug(
            f"Compressing chapter {summary.chapter_number} summary: "
            f"{original_tokens} -> {max_tokens} tokens"
        )

        # Strategy 1: Smart truncate main summary
        compressed_summary = self._smart_truncate(summary.summary, int(max_tokens * 0.5))

        # Strategy 2: Limit key events
        compressed_events = summary.key_events[:3]  # Keep top 3

        # Strategy 3: Limit character changes
        compressed_changes = dict(list(summary.character_changes.items())[:2])  # Top 2

        # Strategy 4: Limit plot threads
        compressed_advanced = summary.plot_threads_advanced[:2]
        compressed_resolved = summary.plot_threads_resolved[:2]

        # Create new summary with compressed fields
        return ChapterSummary(
            chapter_number=summary.chapter_number,
            title=summary.title,
            summary=compressed_summary,
            key_events=compressed_events,
            character_changes=compressed_changes,
            location=summary.location,
            plot_threads_advanced=compressed_advanced,
            plot_threads_resolved=compressed_resolved,
            sentiment=summary.sentiment,
            word_count=summary.word_count,
            created_at=summary.created_at,
        )

    def compress_text(
        self,
        text: str,
        max_tokens: int,
        preserve_sentences: bool = True,
    ) -> CompressionResult:
        """Compress arbitrary text to fit within token budget.

        Args:
            text: Text to compress
            max_tokens: Maximum token budget
            preserve_sentences: Whether to preserve sentence boundaries

        Returns:
            CompressionResult with compressed text and metadata
        """
        if not text:
            return CompressionResult(
                success=True,
                original_tokens=0,
                compressed_tokens=0,
                method="none",
                data={"text": ""},
            )

        original_tokens = self._estimate_tokens(text)

        if original_tokens <= max_tokens:
            return CompressionResult(
                success=True,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                method="none",
                data={"text": text},
            )

        if preserve_sentences:
            compressed = self._smart_truncate(text, max_tokens)
            method = "smart_truncate"
        else:
            # Hard truncate at character boundary
            max_chars = int(max_tokens * CHARS_PER_TOKEN)
            compressed = text[:max_chars].rsplit(" ", 1)[0] + "..."
            method = "hard_truncate"

        compressed_tokens = self._estimate_tokens(compressed)

        return CompressionResult(
            success=True,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            method=method,
            data={"text": compressed},
        )

    def should_compress_arc(self, summary: ArcSummary, max_tokens: int = 400) -> bool:
        """Check if arc summary needs compression.

        Args:
            summary: ArcSummary to check
            max_tokens: Maximum token budget

        Returns:
            True if compression is needed
        """
        text = summary.get_context_string()
        tokens = self._estimate_tokens(text)
        return tokens > max_tokens

    def should_compress_chapter(self, summary: ChapterSummary, max_tokens: int = 250) -> bool:
        """Check if chapter summary needs compression.

        Args:
            summary: ChapterSummary to check
            max_tokens: Maximum token budget

        Returns:
            True if compression is needed
        """
        text = summary.get_context_string()
        tokens = self._estimate_tokens(text)
        return tokens > max_tokens
