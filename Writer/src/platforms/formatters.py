# src/platforms/formatters.py
"""Format conversion utilities for different publishing platforms."""

import re
from typing import Any


class PlatformFormatter:
    """Format content for different publishing platforms.

    Each platform has specific formatting requirements:
    - Wattpad: HTML with specific styling
    - Royal Road: BBCode format
    - Kindle/KDP: Clean HTML with specific structure
    """

    # Standard chapter break markers
    CHAPTER_BREAK_MARKERS = [
        "***",
        "---",
        "* * *",
        "~ * ~",
        "• • •",
    ]

    @staticmethod
    def format_for_wattpad(content: str, **kwargs: Any) -> str:
        """Format content for Wattpad platform.

        Wattpad uses HTML with specific styling. It supports:
        - Basic HTML tags (p, b, i, u, em, strong)
        - Line breaks with <br>
        - Horizontal rules with <hr>

        Args:
            content: Raw chapter content
            **kwargs: Additional options (title, etc.)

        Returns:
            HTML-formatted content for Wattpad
        """
        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Escape any existing HTML to prevent issues
        content = PlatformFormatter._escape_html_preserve_structure(content)

        # Convert markdown-style formatting
        content = PlatformFormatter._convert_markdown_to_html(content)

        # Handle chapter breaks
        content = PlatformFormatter._format_chapter_breaks_html(content)

        # Wrap paragraphs
        paragraphs = content.split("\n\n")
        formatted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # Handle single line breaks within paragraphs
            para = para.replace("\n", "<br>\n")
            formatted_paragraphs.append(f"<p>{para}</p>")

        result = "\n\n".join(formatted_paragraphs)

        # Add title if provided
        title = kwargs.get("title")
        if title:
            result = f"<h2>{title}</h2>\n\n{result}"

        return result

    @staticmethod
    def format_for_royalroad(content: str, **kwargs: Any) -> str:
        """Format content for Royal Road platform.

        Royal Road uses BBCode format. It supports:
        - [b], [i], [u] for bold, italic, underline
        - [hr] for horizontal rules
        - [quote] for quotes
        - [center] for centered text

        Args:
            content: Raw chapter content
            **kwargs: Additional options (title, etc.)

        Returns:
            BBCode-formatted content for Royal Road
        """
        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Convert markdown-style formatting to BBCode
        content = PlatformFormatter._convert_markdown_to_bbcode(content)

        # Handle chapter breaks
        content = PlatformFormatter._format_chapter_breaks_bbcode(content)

        # Preserve line breaks with double newlines
        paragraphs = content.split("\n\n")
        formatted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            formatted_paragraphs.append(para)

        result = "\n\n".join(formatted_paragraphs)

        # Add title if provided
        title = kwargs.get("title")
        if title:
            result = f"[center][b]{title}[/b][/center]\n\n[hr]\n\n{result}"

        return result

    @staticmethod
    def format_for_kindle(content: str, **kwargs: Any) -> str:
        """Format content for Kindle/KDP platform.

        KDP prefers clean, semantic HTML:
        - Proper paragraph structure
        - CSS classes for styling
        - Page breaks between chapters
        - Proper heading hierarchy

        Args:
            content: Raw chapter content
            **kwargs: Additional options (title, chapter_number, etc.)

        Returns:
            Clean HTML formatted for KDP
        """
        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Escape HTML
        content = PlatformFormatter._escape_html_preserve_structure(content)

        # Convert markdown-style formatting
        content = PlatformFormatter._convert_markdown_to_html(content)

        # Handle chapter breaks
        content = PlatformFormatter._format_chapter_breaks_html(content)

        # Build structured HTML
        paragraphs = content.split("\n\n")
        formatted_paragraphs = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # Single line breaks become space
            para = para.replace("\n", " ")
            formatted_paragraphs.append(f"<p>{para}</p>")

        body = "\n".join(formatted_paragraphs)

        # Add title if provided
        title = kwargs.get("title")
        chapter_number = kwargs.get("chapter_number", "")

        if title or chapter_number:
            heading = ""
            if chapter_number:
                heading = f'<h1 class="chapter-title">Chapter {chapter_number}</h1>\n'
            if title:
                heading += f'<h2 class="chapter-subtitle">{title}</h2>\n'
            body = heading + body

        # Wrap in proper HTML structure for KDP
        html = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{title or 'Chapter'}</title>
    <style type="text/css">
        body {{ font-family: serif; margin: 1em; line-height: 1.5; }}
        p {{ text-indent: 1.5em; margin: 0; }}
        p:first-of-type {{ text-indent: 0; }}
        h1 {{ text-align: center; margin-top: 2em; }}
        h2 {{ text-align: center; font-style: italic; }}
        hr {{ margin: 2em 0; }}
        .center {{ text-align: center; }}
    </style>
</head>
<body>
{body}
</body>
</html>"""

        return html

    @staticmethod
    def add_chapter_breaks(content: str, marker: str = "***") -> str:
        """Standardize chapter breaks in content.

        Replaces various break patterns with a consistent marker.

        Args:
            content: Chapter content with potential breaks
            marker: Marker to use for breaks (default: ***)

        Returns:
            Content with standardized chapter breaks
        """
        # Pattern to match various break styles
        break_patterns = [
            r'\n\s*\*{3,}\s*\n',  # ***
            r'\n\s*-{3,}\s*\n',  # ---
            r'\n\s*\* \* \*\s*\n',  # * * *
            r'\n\s*~ \* ~\s*\n',  # ~ * ~
            r'\n\s*• • •\s*\n',  # • • •
        ]

        result = content
        for pattern in break_patterns:
            result = re.sub(pattern, f"\n\n{marker}\n\n", result)

        return result

    @staticmethod
    def strip_formatting(content: str) -> str:
        """Remove all formatting and return plain text.

        Args:
            content: Formatted content (HTML, BBCode, etc.)

        Returns:
            Plain text content
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)

        # Remove BBCode tags
        text = re.sub(r'\[/?[a-z]+(?:=[^\]]+)?\]', '', text)

        # Remove markdown formatting
        text = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', text)  # bold/italic
        text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)  # bold/italic
        text = re.sub(r'~~([^~]+)~~', r'\1', text)  # strikethrough

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    @staticmethod
    def _escape_html_preserve_structure(content: str) -> str:
        """Escape HTML characters while preserving structure.

        Args:
            content: Raw content

        Returns:
            Content with escaped HTML
        """
        # Only escape special characters, not existing tags we want to keep
        # This is a simple approach - for production, consider using html.escape
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
        }

        # Don't double-escape
        for char, entity in replacements.items():
            content = content.replace(entity, char)  # Unescape first
            content = content.replace(char, entity)  # Then escape

        return content

    @staticmethod
    def _convert_markdown_to_html(content: str) -> str:
        """Convert markdown formatting to HTML.

        Args:
            content: Content with markdown formatting

        Returns:
            Content with HTML formatting
        """
        # Bold: **text** or __text__
        content = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', content)

        # Italic: *text* or _text_
        content = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', content)
        content = re.sub(r'_([^_]+)_', r'<em>\1</em>', content)

        # Strikethrough: ~~text~~
        content = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', content)

        # Code: `code`
        content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)

        return content

    @staticmethod
    def _convert_markdown_to_bbcode(content: str) -> str:
        """Convert markdown formatting to BBCode.

        Args:
            content: Content with markdown formatting

        Returns:
            Content with BBCode formatting
        """
        # Bold: **text** or __text__
        content = re.sub(r'\*\*([^\*]+)\*\*', r'[b]\1[/b]', content)
        content = re.sub(r'__([^_]+)__', r'[b]\1[/b]', content)

        # Italic: *text* or _text_
        content = re.sub(r'\*([^\*]+)\*', r'[i]\1[/i]', content)
        content = re.sub(r'_([^_]+)_', r'[i]\1[/i]', content)

        # Strikethrough: ~~text~~
        content = re.sub(r'~~([^~]+)~~', r'[s]\1[/s]', content)

        # Code: `code`
        content = re.sub(r'`([^`]+)`', r'[code]\1[/code]', content)

        return content

    @staticmethod
    def _format_chapter_breaks_html(content: str) -> str:
        """Format chapter breaks as HTML horizontal rules.

        Args:
            content: Content with potential chapter breaks

        Returns:
            Content with formatted breaks
        """
        # Replace standalone breaks with <hr>
        for marker in PlatformFormatter.CHAPTER_BREAK_MARKERS:
            content = content.replace(f"\n\n{marker}\n\n", "\n\n<hr>\n\n")
            content = content.replace(f"\n{marker}\n", "\n\n<hr>\n\n")

        return content

    @staticmethod
    def _format_chapter_breaks_bbcode(content: str) -> str:
        """Format chapter breaks as BBCode horizontal rules.

        Args:
            content: Content with potential chapter breaks

        Returns:
            Content with formatted breaks
        """
        # Replace standalone breaks with [hr]
        for marker in PlatformFormatter.CHAPTER_BREAK_MARKERS:
            content = content.replace(f"\n\n{marker}\n\n", "\n\n[hr]\n\n")
            content = content.replace(f"\n{marker}\n", "\n\n[hr]\n\n")

        return content
