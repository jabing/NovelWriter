"""Chapter summarization for hierarchical story state.

This module provides LLM-driven summarization of chapter content to create
structured ChapterSummary objects used in the hierarchical memory system.
"""

import json
import logging
import re
from typing import Any

from src.llm.base import BaseLLM
from src.novel.summaries import ChapterSummary

logger = logging.getLogger(__name__)

# Prompt templates for chapter summarization
SUMMARY_SYSTEM_PROMPT = """你是一个专业的小说编辑，擅长分析和总结章节内容。
请根据给定的章节内容，提取关键信息并生成结构化的摘要。

你的任务：
1. 生成约200字的章节摘要
2. 提取3-5个关键事件
3. 识别角色状态变化
4. 确定主要场景位置
5. 追踪剧情线进展
6. 分析整体情感基调

请用JSON格式返回结果。"""

SUMMARY_USER_PROMPT_TEMPLATE = """请分析以下章节内容并生成摘要：

【章节标题】{title}
【章节内容】
{content}

请返回JSON格式：
{{
    "summary": "约200字的章节摘要",
    "key_events": ["关键事件1", "关键事件2", ...],
    "character_changes": {{"角色名": "变化描述", ...}},
    "location": "主要场景位置",
    "plot_threads_advanced": ["推进的剧情线1", ...],
    "plot_threads_resolved": ["解决的剧情线1", ...],
    "sentiment": "情感基调(positive/negative/neutral/tense/hopeful/dark)"
}}"""


class ChapterSummarizer:
    """LLM-driven chapter summarizer for hierarchical memory.

    This class uses an LLM to analyze chapter content and extract
    structured information for the hierarchical story state system.

    Attributes:
        llm: LLM instance for text generation
        max_summary_length: Maximum characters for summary text
    """

    def __init__(
        self,
        llm: BaseLLM,
        max_summary_length: int = 400,
    ) -> None:
        """Initialize the chapter summarizer.

        Args:
            llm: LLM instance for generating summaries
            max_summary_length: Maximum characters for summary (default 400)
        """
        self.llm = llm
        self.max_summary_length = max_summary_length

    async def summarize(
        self,
        chapter_number: int,
        title: str,
        content: str,
        word_count: int | None = None,
    ) -> ChapterSummary:
        """Generate a structured summary of chapter content.

        Args:
            chapter_number: Chapter number (1-indexed)
            title: Chapter title
            content: Full chapter text content
            word_count: Optional word count (calculated if not provided)

        Returns:
            ChapterSummary with extracted information
        """
        # Calculate word count if not provided
        if word_count is None:
            word_count = len(content.split())

        # Truncate content if too long (keep first and last portions)
        truncated_content = self._truncate_content(content, max_chars=8000)

        # Generate summary using LLM
        user_prompt = SUMMARY_USER_PROMPT_TEMPLATE.format(
            title=title,
            content=truncated_content,
        )

        try:
            response = await self.llm.generate_with_system(
                system_prompt=SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=1000,
            )

            # Parse LLM response
            summary_data = self._parse_llm_response(response.content)

            # Create ChapterSummary
            return ChapterSummary(
                chapter_number=chapter_number,
                title=title,
                summary=self._truncate_summary(summary_data.get("summary", "")),
                key_events=summary_data.get("key_events", []),
                character_changes=summary_data.get("character_changes", {}),
                location=summary_data.get("location", ""),
                plot_threads_advanced=summary_data.get("plot_threads_advanced", []),
                plot_threads_resolved=summary_data.get("plot_threads_resolved", []),
                sentiment=summary_data.get("sentiment", "neutral"),
                word_count=word_count,
            )

        except Exception as e:
            logger.error(f"Failed to summarize chapter {chapter_number}: {e}")
            # Return a minimal summary on failure
            return ChapterSummary(
                chapter_number=chapter_number,
                title=title,
                summary=self._fallback_summary(content),
                key_events=[],
                character_changes={},
                location="",
                plot_threads_advanced=[],
                plot_threads_resolved=[],
                sentiment="neutral",
                word_count=word_count,
            )

    def _truncate_content(self, content: str, max_chars: int = 8000) -> str:
        """Truncate content to fit within token limits.

        Keeps the beginning and end of the content to capture
        opening and closing scenes.

        Args:
            content: Full chapter content
            max_chars: Maximum characters to keep

        Returns:
            Truncated content string
        """
        if len(content) <= max_chars:
            return content

        # Keep first 60% and last 40%
        first_part = int(max_chars * 0.6)
        last_part = max_chars - first_part

        truncated = content[:first_part] + "\n\n... [中间部分省略] ...\n\n" + content[-last_part:]
        return truncated

    def _truncate_summary(self, summary: str) -> str:
        """Truncate summary to maximum length.

        Args:
            summary: Generated summary text

        Returns:
            Truncated summary
        """
        if len(summary) <= self.max_summary_length:
            return summary
        return summary[: self.max_summary_length - 3] + "..."

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse JSON response from LLM.

        Handles various formats the LLM might return:
        - Clean JSON
        - JSON in code blocks
        - JSON with extra text

        Args:
            response: Raw LLM response

        Returns:
            Parsed dictionary
        """
        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
        match = re.search(code_block_pattern, response)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in response
        json_pattern = r"\{[\s\S]*\}"
        match = re.search(json_pattern, response)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Return empty dict on failure
        logger.warning(f"Failed to parse LLM response as JSON: {response[:200]}")
        return {}

    def _fallback_summary(self, content: str) -> str:
        """Generate a simple fallback summary when LLM fails.

        Uses the first few sentences of the content.

        Args:
            content: Chapter content

        Returns:
            Simple summary string
        """
        # Get first 300 characters, ending at sentence boundary
        text = content[:500]
        # Try to end at a sentence
        last_period = text.rfind("。")
        last_exclaim = text.rfind("！")
        last_question = text.rfind("？")
        end_pos = max(last_period, last_exclaim, last_question)

        if end_pos > 100:
            return text[: end_pos + 1]
        return text[:300] + "..."


class ArcSummarizer:
    """LLM-driven arc summarizer for combining chapter summaries.

    Creates higher-level arc summaries from multiple chapter summaries.
    """

    ARC_SUMMARY_SYSTEM_PROMPT = """你是一个专业的小说编辑，擅长总结故事弧线。
请根据给定的章节摘要，生成一个综合的故事弧线摘要。

你的任务：
1. 生成约500字的弧线摘要
2. 提取重大事件
3. 总结角色成长弧线
4. 描述世界观变化
5. 追踪剧情线状态

请用JSON格式返回结果。"""

    ARC_SUMMARY_USER_TEMPLATE = """请根据以下章节摘要生成故事弧线总结：

【弧线信息】
第{arc_number}卷：章节 {start_chapter} - {end_chapter}

【章节摘要】
{chapter_summaries}

请返回JSON格式：
{{
    "title": "弧线标题",
    "summary": "约500字的弧线摘要",
    "major_events": ["重大事件1", "重大事件2", ...],
    "character_arcs": {{"角色名": "成长弧线描述", ...}},
    "world_changes": ["世界观变化1", ...],
    "plot_threads_status": {{"剧情线名": "状态(active/resolved)", ...}},
    "themes": ["主题1", "主题2", ...]
}}"""

    def __init__(self, llm: BaseLLM) -> None:
        """Initialize the arc summarizer.

        Args:
            llm: LLM instance for generating summaries
        """
        self.llm = llm

    async def summarize_arc(
        self,
        arc_number: int,
        start_chapter: int,
        end_chapter: int,
        chapter_summaries: list[ChapterSummary],
    ) -> dict[str, Any]:
        """Generate an arc summary from chapter summaries.

        Args:
            arc_number: Arc number (1-indexed)
            start_chapter: First chapter in arc
            end_chapter: Last chapter in arc
            chapter_summaries: List of chapter summaries in this arc

        Returns:
            Dictionary with arc summary data
        """
        # Format chapter summaries for LLM
        summaries_text = "\n\n".join(
            f"第{cs.chapter_number}章《{cs.title}》：{cs.summary}" for cs in chapter_summaries
        )

        user_prompt = self.ARC_SUMMARY_USER_TEMPLATE.format(
            arc_number=arc_number,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            chapter_summaries=summaries_text,
        )

        try:
            response = await self.llm.generate_with_system(
                system_prompt=self.ARC_SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2000,
            )

            # Parse response
            return self._parse_llm_response(response.content)

        except Exception as e:
            logger.error(f"Failed to summarize arc {arc_number}: {e}")
            return self._fallback_arc_data(arc_number, start_chapter, end_chapter)

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse JSON response from LLM."""
        # Same logic as ChapterSummarizer
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
        match = re.search(code_block_pattern, response)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        json_pattern = r"\{[\s\S]*\}"
        match = re.search(json_pattern, response)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse arc summary response: {response[:200]}")
        return {}

    def _fallback_arc_data(
        self, arc_number: int, start_chapter: int, end_chapter: int
    ) -> dict[str, Any]:
        """Generate fallback arc data when LLM fails."""
        return {
            "title": f"第{arc_number}卷",
            "summary": f"故事弧线涵盖第{start_chapter}章至第{end_chapter}章。",
            "major_events": [],
            "character_arcs": {},
            "world_changes": [],
            "plot_threads_status": {},
            "themes": [],
        }
