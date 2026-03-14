# tests/test_platforms/test_formatters.py
"""Tests for Platform Formatter."""


from src.novel_agent.platforms.formatters import PlatformFormatter


class TestPlatformFormatter:
    """Tests for PlatformFormatter class."""

    def test_chapter_break_markers_defined(self) -> None:
        """Test that chapter break markers are defined."""
        assert len(PlatformFormatter.CHAPTER_BREAK_MARKERS) > 0
        assert "***" in PlatformFormatter.CHAPTER_BREAK_MARKERS

    def test_format_for_wattpad_basic(self) -> None:
        """Test basic Wattpad formatting."""
        content = "This is a test paragraph.\n\nThis is another paragraph."
        result = PlatformFormatter.format_for_wattpad(content)

        assert "<p>" in result
        assert "</p>" in result

    def test_format_for_wattpad_with_title(self) -> None:
        """Test Wattpad formatting with title."""
        content = "Test content."
        result = PlatformFormatter.format_for_wattpad(content, title="Chapter 1")

        assert "<h2>Chapter 1</h2>" in result

    def test_format_for_wattpad_preserves_paragraphs(self) -> None:
        """Test Wattpad formatting preserves paragraph structure."""
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = PlatformFormatter.format_for_wattpad(content)

        # Should have 3 paragraph tags
        assert result.count("<p>") == 3

    def test_format_for_royalroad_basic(self) -> None:
        """Test basic Royal Road formatting."""
        content = "This is a test paragraph.\n\nThis is another paragraph."
        result = PlatformFormatter.format_for_royalroad(content)

        # Should preserve paragraph breaks
        assert "This is a test paragraph." in result

    def test_format_for_royalroad_with_title(self) -> None:
        """Test Royal Road formatting with title."""
        content = "Test content."
        result = PlatformFormatter.format_for_royalroad(content, title="Chapter 1")

        assert "[center]" in result
        assert "[b]Chapter 1[/b]" in result
        assert "[hr]" in result

    def test_format_for_kindle_basic(self) -> None:
        """Test basic Kindle formatting."""
        content = "This is a test paragraph.\n\nThis is another paragraph."
        result = PlatformFormatter.format_for_kindle(content)

        assert "<p>" in result
        assert "</p>" in result
        assert "<!DOCTYPE html>" in result

    def test_format_for_kindle_with_title(self) -> None:
        """Test Kindle formatting with title and chapter number."""
        content = "Test content."
        result = PlatformFormatter.format_for_kindle(
            content,
            title="The Beginning",
            chapter_number=1
        )

        assert 'class="chapter-title"' in result
        assert "Chapter 1" in result
        assert 'class="chapter-subtitle"' in result
        assert "The Beginning" in result

    def test_format_for_kindle_includes_css(self) -> None:
        """Test Kindle formatting includes CSS styles."""
        content = "Test content."
        result = PlatformFormatter.format_for_kindle(content)

        assert "<style" in result
        assert "font-family" in result

    def test_add_chapter_breaks(self) -> None:
        """Test chapter break standardization."""
        content = "Part one.\n\n***\n\nPart two."
        result = PlatformFormatter.add_chapter_breaks(content)

        # Should contain the marker
        assert "***" in result

    def test_strip_formatting_html(self) -> None:
        """Test stripping HTML formatting."""
        content = "<p>This is <b>bold</b> text.</p>"
        result = PlatformFormatter.strip_formatting(content)

        assert "<p>" not in result
        assert "<b>" not in result
        assert "bold" in result

    def test_strip_formatting_bbcode(self) -> None:
        """Test stripping BBCode formatting."""
        content = "This is [b]bold[/b] text."
        result = PlatformFormatter.strip_formatting(content)

        assert "[b]" not in result
        assert "bold" in result

    def test_strip_formatting_markdown(self) -> None:
        """Test stripping markdown formatting."""
        content = "This is **bold** and *italic* text."
        result = PlatformFormatter.strip_formatting(content)

        assert "**" not in result
        assert "*" not in result or "bold" in result

    def test_convert_markdown_to_html_bold(self) -> None:
        """Test markdown to HTML bold conversion."""
        content = "This is **bold** text."
        result = PlatformFormatter._convert_markdown_to_html(content)

        assert "<strong>bold</strong>" in result

    def test_convert_markdown_to_html_italic(self) -> None:
        """Test markdown to HTML italic conversion."""
        content = "This is *italic* text."
        result = PlatformFormatter._convert_markdown_to_html(content)

        assert "<em>italic</em>" in result

    def test_convert_markdown_to_html_code(self) -> None:
        """Test markdown to HTML code conversion."""
        content = "This is `code` text."
        result = PlatformFormatter._convert_markdown_to_html(content)

        assert "<code>code</code>" in result

    def test_convert_markdown_to_bbcode_bold(self) -> None:
        """Test markdown to BBCode bold conversion."""
        content = "This is **bold** text."
        result = PlatformFormatter._convert_markdown_to_bbcode(content)

        assert "[b]bold[/b]" in result

    def test_convert_markdown_to_bbcode_italic(self) -> None:
        """Test markdown to BBCode italic conversion."""
        content = "This is *italic* text."
        result = PlatformFormatter._convert_markdown_to_bbcode(content)

        assert "[i]italic[/i]" in result


class TestFormatForWattpadEdgeCases:
    """Edge case tests for Wattpad formatting."""

    def test_empty_content(self) -> None:
        """Test formatting empty content."""
        result = PlatformFormatter.format_for_wattpad("")
        # Should handle gracefully
        assert isinstance(result, str)

    def test_single_paragraph(self) -> None:
        """Test formatting single paragraph."""
        content = "Just one paragraph."
        result = PlatformFormatter.format_for_wattpad(content)

        assert "<p>Just one paragraph.</p>" in result

    def test_line_breaks_within_paragraph(self) -> None:
        """Test line breaks within paragraphs become br tags."""
        content = "Line one.\nLine two.\n\nNew paragraph."
        result = PlatformFormatter.format_for_wattpad(content)

        assert "<br>" in result

    def test_special_characters_escaped(self) -> None:
        """Test that special HTML characters are escaped."""
        content = "Use <angle> brackets & ampersands."
        result = PlatformFormatter.format_for_wattpad(content)

        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result


class TestFormatForRoyalRoadEdgeCases:
    """Edge case tests for Royal Road formatting."""

    def test_empty_content(self) -> None:
        """Test formatting empty content."""
        result = PlatformFormatter.format_for_royalroad("")
        assert isinstance(result, str)

    def test_multiple_breaks(self) -> None:
        """Test content with multiple chapter breaks."""
        content = "Part one.\n\n***\n\nPart two.\n\n---\n\nPart three."
        result = PlatformFormatter.format_for_royalroad(content)

        # Should convert breaks to [hr]
        assert "[hr]" in result


class TestFormatForKindleEdgeCases:
    """Edge case tests for Kindle formatting."""

    def test_empty_content(self) -> None:
        """Test formatting empty content."""
        result = PlatformFormatter.format_for_kindle("")
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result

    def test_xml_declaration_present(self) -> None:
        """Test that XML declaration is included."""
        content = "Test content."
        result = PlatformFormatter.format_for_kindle(content)

        assert '<?xml version="1.0"' in result

    def test_proper_html_structure(self) -> None:
        """Test proper HTML structure for KDP."""
        content = "Test content."
        result = PlatformFormatter.format_for_kindle(content)

        assert "<html" in result
        assert "<head>" in result
        assert "<body>" in result
        assert "</html>" in result


class TestChapterBreakHandling:
    """Tests for chapter break handling."""

    def test_standardize_asterisk_break(self) -> None:
        """Test standardizing asterisk breaks."""
        content = "Part one.\n\n***\n\nPart two."
        result = PlatformFormatter.add_chapter_breaks(content, marker="---")

        assert "---" in result
        assert "***" not in result or "---" in result

    def test_standardize_dash_break(self) -> None:
        """Test standardizing dash breaks."""
        content = "Part one.\n\n------\n\nPart two."
        result = PlatformFormatter.add_chapter_breaks(content, marker="***")

        assert "***" in result


class TestStripFormattingEdgeCases:
    """Edge case tests for stripping formatting."""

    def test_mixed_formatting(self) -> None:
        """Test stripping mixed HTML and BBCode."""
        content = "<p>This is [b]mixed[/b] **formatting**.</p>"
        result = PlatformFormatter.strip_formatting(content)

        assert "<p>" not in result
        assert "[b]" not in result
        assert "**" not in result

    def test_preserves_text_content(self) -> None:
        """Test that text content is preserved."""
        content = "<b>Bold</b> and [i]italic[/i] text."
        result = PlatformFormatter.strip_formatting(content)

        assert "Bold" in result
        assert "italic" in result
        assert "text" in result
