"""
Outline Parser Module

Parses novel outline structure, extracting chapters, plot threads,
character appearances, and timeline information.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

jieba: Any = None
_jieba_available: bool

try:
    import jieba as _jieba
    jieba = _jieba
    _jieba_available = True
except ImportError:
    _jieba_available = False

if TYPE_CHECKING:
    from collections.abc import Sequence


# Chapter title patterns - match at line start only
CHAPTER_PATTERNS = [
    r"^第[一二三四五六七八九十百千万零]+章[^\n]*",  # Chinese numerals
    r"^第\d+章[^\n]*",  # Arabic numerals
    r"^Chapter\s+\d+[^\n]*",  # English
    r"^第[一二三四五六七八九十零]+节[^\n]*",  # Sections
    r"^CHAPTER\s+\d+[^\n]*",  # English uppercase
]

# Plot thread keywords and their types
PLOT_KEYWORDS = {
    "主线": "main",
    "支线": "side",
    "伏笔": "foreshadowing",
    "悬念": "suspense",
    "冲突": "conflict",
    "高潮": "climax",
    "结局": "ending",
    "转折": "twist",
}

# Timeline patterns
TIME_PATTERNS = [
    r"\d{1,4}年\d{1,2}月\d{1,2}日?",  # 2024年3月9日
    r"[一二三四五六七八九十零]+年[一二三四五六七八九十零]+月[一二三四五六七八九十零]+日?",  # 三年三月九日
    r"[一二三四五六七八九十零]+月[一二三四五六七八九十零]+日",  # 三月九日 (no year)
    r"第[一二三四五六七八九十百千万零\d]+天",
    r"次日", r"当夜", r"当晚",
    r"[一二三四五六七八九十百千万零\d]+天后",
    r"[一二三四五六七八九十百千万零\d]+周后",
    r"当天", r"今夜", r"今晚",
    r"翌日", r"隔日",
]


@dataclass
class ChapterInfo:
    """Information about a chapter."""
    number: int
    title: str
    content: str
    start_position: int = 0
    end_position: int = 0


@dataclass
class PlotThread:
    """Information about a plot thread."""
    thread_type: str
    content: str
    chapter: int | None = None
    position: int = 0


@dataclass
class TimelineEvent:
    """Information about a timeline event."""
    event: str
    time: str | None
    chapter: int | None = None
    position: int = 0


@dataclass
class CharacterAppearance:
    """Information about a character appearance."""
    character_name: str
    position: int
    context: str
    chapter: int | None = None


class OutlineParser:
    """
    Parser for novel outlines.
    
    Parses outline structure including chapters, plot threads,
    character appearances, and timeline information.
    
    Uses jieba for Chinese text segmentation when available.
    """
    
    def __init__(self) -> None:
        """Initialize the outline parser."""
        self._jieba_initialized = False
    
    def _ensure_jieba(self) -> None:
        """Ensure jieba is initialized."""
        if _jieba_available and not self._jieba_initialized:
            if jieba is not None:
                jieba.initialize()
            self._jieba_initialized = True
    
    def segment_text(self, text: str) -> list[str]:
        """
        Segment Chinese text using jieba.
        
        Falls back to simple character-based segmentation if jieba
        is not available.
        
        Args:
            text: Chinese text to segment
            
        Returns:
            List of word segments
        """
        if not text:
            return []
        
        if _jieba_available and jieba is not None:
            self._ensure_jieba()
            return list(jieba.cut(text))
        
        # Fallback: simple character segmentation for CJK
        # and whitespace-based for other text
        segments: list[str] = []
        current_segment = ""
        
        for char in text:
            # Check if character is CJK
            if "\u4e00" <= char <= "\u9fff":
                if current_segment:
                    segments.append(current_segment)
                    current_segment = ""
                segments.append(char)
            elif char.isspace():
                if current_segment:
                    segments.append(current_segment)
                    current_segment = ""
            else:
                current_segment += char
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def extract_chapter_titles(self, text: str) -> list[dict[str, Any]]:
        """
        Extract chapter titles from text.
        
        Args:
            text: Text to search for chapter titles
            
        Returns:
            List of chapter information dictionaries with:
            - number: chapter number
            - title: chapter title (text after "第X章")
            - position: position in text
        """
        chapters: list[dict[str, Any]] = []
        
        for pattern in CHAPTER_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                full_match = match.group()
                position = match.start()
                
                # Extract chapter number
                number = self._extract_chapter_number(full_match)
                
                # Extract title (text after the chapter marker)
                title = self._extract_chapter_title(full_match)
                
                chapters.append({
                    "number": number,
                    "title": title,
                    "position": position,
                    "full_match": full_match,
                })
        
        # Sort by position and remove duplicates
        chapters.sort(key=lambda x: (x["position"], x["number"]))
        
        # Remove duplicates (keep first occurrence)
        seen_positions: set[int] = set()
        unique_chapters: list[dict[str, Any]] = []
        for chapter in chapters:
            if chapter["position"] not in seen_positions:
                seen_positions.add(chapter["position"])
                unique_chapters.append(chapter)
        
        return unique_chapters
    
    def _extract_chapter_number(self, title_text: str) -> int:
        """Extract chapter number from title text."""
        # Try Arabic numerals first
        arabic_match = re.search(r"第(\d+)", title_text)
        if arabic_match:
            return int(arabic_match.group(1))
        
        # Try Chinese numerals
        chinese_match = re.search(r"第([一二三四五六七八九十百千万零]+)", title_text)
        if chinese_match:
            return self._chinese_to_int(chinese_match.group(1))
        
        # Try English
        english_match = re.search(r"Chapter\s+(\d+)", title_text, re.IGNORECASE)
        if english_match:
            return int(english_match.group(1))
        
        return 0
    
    def _extract_chapter_title(self, full_match: str) -> str:
        """Extract the title part from a chapter heading."""
        # Remove the chapter number part
        title = re.sub(r"第[一二三四五六七八九十百千万零\d]+章\s*", "", full_match)
        title = re.sub(r"第[一二三四五六七八九十零\d]+节\s*", "", title)
        title = re.sub(r"Chapter\s+\d+\s*", "", title, flags=re.IGNORECASE)
        return title.strip()
    
    def _chinese_to_int(self, chinese_num: str) -> int:
        """Convert Chinese numeral to integer."""
        mapping = {
            "零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
            "十": 10, "百": 100, "千": 1000, "万": 10000,
        }
        
        if not chinese_num:
            return 0
        
        # Simple conversion for common cases
        if len(chinese_num) == 1:
            return mapping.get(chinese_num, 0)
        
        result = 0
        temp = 0
        
        for char in chinese_num:
            value = mapping.get(char, 0)
            if value >= 10:
                if temp == 0:
                    temp = 1
                result += temp * value
                temp = 0
            else:
                temp = value
        
        result += temp
        return result
    
    def extract_plot_threads(self, text: str) -> list[dict[str, Any]]:
        """
        Extract plot thread descriptions from text.
        
        Args:
            text: Text to search for plot threads
            
        Returns:
            List of plot thread dictionaries with:
            - type: thread type (main, side, foreshadowing, etc.)
            - keyword: the keyword matched
            - content: the plot description
            - position: position in text
        """
        threads: list[dict[str, Any]] = []
        
        # Build pattern to match keywords followed by content
        keyword_pattern = "|".join(re.escape(kw) for kw in PLOT_KEYWORDS)
        pattern = rf"({keyword_pattern})[：:]\s*([^\n]+)"
        
        for match in re.finditer(pattern, text):
            keyword = match.group(1)
            content = match.group(2).strip()
            position = match.start()
            
            thread_type = PLOT_KEYWORDS.get(keyword, "unknown")
            
            threads.append({
                "type": thread_type,
                "keyword": keyword,
                "content": content,
                "position": position,
            })
        
        return threads
    
    def detect_character_appearances(
        self,
        text: str,
        character_names: Sequence[str],
    ) -> list[dict[str, Any]]:
        """
        Detect where characters appear in text.
        
        Args:
            text: Text to search for character appearances
            character_names: List of character names to search for
            
        Returns:
            List of character appearance dictionaries with:
            - character_name: the character found
            - position: position in text
            - context: surrounding text (up to 50 chars before/after)
        """
        appearances: list[dict[str, Any]] = []
        
        if not character_names:
            return appearances
        
        # Sort by length (longest first) to match compound names first
        sorted_names = sorted(character_names, key=len, reverse=True)
        
        # Track occupied positions to avoid overlapping matches
        occupied: set[tuple[int, int]] = set()
        
        for name in sorted_names:
            start = 0
            while True:
                pos = text.find(name, start)
                if pos == -1:
                    break
                
                # Check if this position overlaps with an already matched name
                name_range = (pos, pos + len(name))
                overlaps = any(
                    not (name_range[1] <= occ[0] or name_range[0] >= occ[1])
                    for occ in occupied
                )
                
                if not overlaps:
                    # Get context (50 chars before and after)
                    context_start = max(0, pos - 50)
                    context_end = min(len(text), pos + len(name) + 50)
                    context = text[context_start:context_end]
                    
                    appearances.append({
                        "character_name": name,
                        "position": pos,
                        "context": context,
                    })
                    occupied.add(name_range)
                
                start = pos + 1
        
        # Sort by position
        appearances.sort(key=lambda x: x["position"])
        
        return appearances
    
    def extract_timeline_events(self, text: str) -> list[dict[str, Any]]:
        """
        Extract timeline events from text.
        
        Args:
            text: Text to search for timeline events
            
        Returns:
            List of timeline event dictionaries with:
            - time: the time marker found (or None)
            - event: the event description
            - position: position in text
        """
        events: list[dict[str, Any]] = []
        
        # Build time pattern
        time_pattern = "|".join(TIME_PATTERNS)
        
        # Find all time markers
        time_matches: list[tuple[int, int, str]] = []
        for match in re.finditer(time_pattern, text):
            time_matches.append((match.start(), match.end(), match.group()))
        
        # If no time markers, the whole text is events without time
        if not time_matches:
            # Split by sentences
            sentences = re.split(r"[。！？\n]+", text)
            position = 0
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    events.append({
                        "time": None,
                        "event": sentence,
                        "position": position,
                    })
                    position += len(sentence) + 1
            return events
        
        # Process text between time markers
        prev_end = 0
        for start, end, time_marker in time_matches:
            # Events between previous marker and current marker
            if prev_end < start:
                intermediate_text = text[prev_end:start]
                sentences = re.split(r"[。！？\n]+", intermediate_text)
                pos = prev_end
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence:
                        events.append({
                            "time": None,
                            "event": sentence,
                            "position": pos,
                        })
                        pos += len(sentence) + 1
            
            # Event at this time marker
            next_time_start = len(text)
            for next_start, _, _ in time_matches:
                if next_start > end:
                    next_time_start = next_start
                    break
            
            event_text = text[end:next_time_start].strip()
            # Get first sentence as the event
            first_sentence_match = re.match(r"^([^。！？\n]+)", event_text)
            if first_sentence_match:
                event = first_sentence_match.group(1).strip()
            else:
                event = event_text[:100] if event_text else ""
            
            if event:
                events.append({
                    "time": time_marker,
                    "event": event,
                    "position": start,
                })
            
            prev_end = end
        
        return events
    
    def parse_outline(self, outline_text: str) -> dict[str, Any]:
        """
        Parse outline text and return structured data.
        
        Args:
            outline_text: Full outline text to parse
            
        Returns:
            Dictionary containing:
            - chapters: list of chapter information
            - plot_threads: list of plot threads
            - timeline: list of timeline events
            - raw_text: the original text
        """
        # Extract chapters
        chapter_titles = self.extract_chapter_titles(outline_text)
        
        # Build chapter content
        chapters: list[dict[str, Any]] = []
        for i, chapter_info in enumerate(chapter_titles):
            start_pos = chapter_info["position"]
            end_pos = (
                chapter_titles[i + 1]["position"]
                if i + 1 < len(chapter_titles)
                else len(outline_text)
            )
            content = outline_text[start_pos:end_pos]
            
            chapters.append({
                "number": chapter_info["number"],
                "title": chapter_info["title"],
                "content": content,
                "start_position": start_pos,
                "end_position": end_pos,
            })
        
        # Extract plot threads
        plot_threads = self.extract_plot_threads(outline_text)
        
        # Assign chapters to plot threads
        for thread in plot_threads:
            thread_chapter = self._find_chapter_for_position(
                thread["position"], chapters
            )
            thread["chapter"] = thread_chapter
        
        # Extract timeline events
        timeline = self.extract_timeline_events(outline_text)
        
        # Assign chapters to timeline events
        for event in timeline:
            event_chapter = self._find_chapter_for_position(
                event["position"], chapters
            )
            event["chapter"] = event_chapter
        
        return {
            "chapters": chapters,
            "plot_threads": plot_threads,
            "timeline": timeline,
            "raw_text": outline_text,
        }
    
    def _find_chapter_for_position(
        self,
        position: int,
        chapters: list[dict[str, Any]],
    ) -> int | None:
        """Find the chapter number for a given position in text."""
        for chapter in chapters:
            if chapter["start_position"] <= position < chapter["end_position"]:
                return chapter["number"]
        return None
    
    def get_chapter_content(
        self,
        outline_text: str,
        chapter_number: int,
    ) -> str | None:
        """
        Get content for a specific chapter.
        
        Args:
            outline_text: Full outline text
            chapter_number: Chapter number to retrieve
            
        Returns:
            Chapter content or None if not found
        """
        chapters = self.extract_chapter_titles(outline_text)
        
        for i, chapter in enumerate(chapters):
            if chapter["number"] == chapter_number:
                start_pos = chapter["position"]
                end_pos = (
                    chapters[i + 1]["position"]
                    if i + 1 < len(chapters)
                    else len(outline_text)
                )
                return outline_text[start_pos:end_pos]
        
        return None
    
    def find_plot_threads_by_type(
        self,
        plot_threads: list[dict[str, Any]],
        thread_type: str,
    ) -> list[dict[str, Any]]:
        """
        Filter plot threads by type.
        
        Args:
            plot_threads: List of plot threads
            thread_type: Type to filter by (main, side, etc.)
            
        Returns:
            Filtered list of plot threads
        """
        return [
            thread
            for thread in plot_threads
            if thread.get("type") == thread_type
        ]
    
    def get_chapter_plot_threads(
        self,
        plot_threads: list[dict[str, Any]],
        chapter_number: int,
    ) -> list[dict[str, Any]]:
        """
        Get plot threads for a specific chapter.
        
        Args:
            plot_threads: List of plot threads
            chapter_number: Chapter number to filter by
            
        Returns:
            Plot threads belonging to the chapter
        """
        return [
            thread
            for thread in plot_threads
            if thread.get("chapter") == chapter_number
        ]
