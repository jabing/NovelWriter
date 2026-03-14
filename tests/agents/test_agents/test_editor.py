# tests/test_agents/test_editor.py
"""Tests for Editor Agent."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.base import AgentResult
from src.agents.editor import EditorAgent


class TestEditorAgent:
    """Tests for Editor Agent."""

    @pytest.fixture
    def editor(self) -> EditorAgent:
        """Create Editor Agent with mock LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(
            return_value=MagicMock(content='{"overall": 7, "issues": []}')
        )
        return EditorAgent(name="Test Editor", llm=mock_llm)

    def test_initialization(self, editor: EditorAgent) -> None:
        """Test editor initializes correctly."""
        assert editor.name == "Test Editor"
        assert len(editor.STYLE_ISSUES) > 0

    def test_style_issues_defined(self, editor: EditorAgent) -> None:
        """Test that style issues patterns are defined."""
        # Check for expected style issue types
        issue_types = [issue[1] for issue in editor.STYLE_ISSUES]
        assert "Weak modifier" in issue_types
        assert "Passive voice" in issue_types
        assert "Word repetition" in issue_types


class TestStyleChecks:
    """Tests for style checking methods."""

    @pytest.fixture
    def editor(self) -> EditorAgent:
        """Create Editor Agent with mock LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock(
            return_value=MagicMock(content='{"overall": 7, "issues": []}')
        )
        return EditorAgent(name="Test Editor", llm=mock_llm)

    def test_check_style_detects_weak_modifiers(self, editor: EditorAgent) -> None:
        """Test detection of weak modifiers."""
        content = "She was very tired and really hungry."
        issues = editor._check_style(content)

        weak_modifier_issues = [i for i in issues if i["type"] == "Weak modifier"]
        assert len(weak_modifier_issues) >= 2  # "very" and "really"

    def test_check_style_detects_passive_voice(self, editor: EditorAgent) -> None:
        """Test detection of passive voice."""
        content = "The door was opened by John."
        issues = editor._check_style(content)

        passive_issues = [i for i in issues if i["type"] == "Passive voice"]
        assert len(passive_issues) >= 1

    def test_check_style_detects_word_repetition(self, editor: EditorAgent) -> None:
        """Test detection of word repetition."""
        content = "The the door was open."
        issues = editor._check_style(content)

        repetition_issues = [i for i in issues if i["type"] == "Word repetition"]
        assert len(repetition_issues) >= 1

    def test_check_style_detects_multiple_punctuation(self, editor: EditorAgent) -> None:
        """Test detection of multiple punctuation."""
        content = "What?! That's amazing!!"
        issues = editor._check_style(content)

        punctuation_issues = [i for i in issues if i["type"] == "Multiple punctuation"]
        assert len(punctuation_issues) >= 1

    def test_check_style_detects_long_sentences(self, editor: EditorAgent) -> None:
        """Test detection of overly long sentences."""
        # Create a sentence with 50+ words
        long_sentence = " ".join(["word"] * 50) + "."
        issues = editor._check_style(long_sentence)

        long_sentence_issues = [i for i in issues if i["type"] == "Long sentence"]
        assert len(long_sentence_issues) >= 1

    def test_check_style_detects_long_paragraphs(self, editor: EditorAgent) -> None:
        """Test detection of overly long paragraphs."""
        # Create a paragraph with 350+ words
        long_paragraph = " ".join(["word"] * 350)
        issues = editor._check_style(long_paragraph)

        long_para_issues = [i for i in issues if i["type"] == "Long paragraph"]
        assert len(long_para_issues) >= 1

    def test_check_style_clean_content(self, editor: EditorAgent) -> None:
        """Test that clean content has minimal issues."""
        content = "She walked to the store. The sun was bright. Birds sang in the trees."
        issues = editor._check_style(content)

        # Clean content should have very few or no issues
        critical_issues = [i for i in issues if i["type"] in
                          ["Multiple punctuation", "Word repetition"]]
        assert len(critical_issues) == 0

    def test_check_style_returns_list_with_structure(self, editor: EditorAgent) -> None:
        """Test that style issues have proper structure."""
        content = "She was very tired."
        issues = editor._check_style(content)

        assert isinstance(issues, list)
        if issues:  # If any issues found
            issue = issues[0]
            assert "type" in issue
            assert "text" in issue
            assert "suggestion" in issue


class TestConsistencyChecks:
    """Tests for consistency checking methods."""

    @pytest.fixture
    def editor_with_mock_response(self) -> EditorAgent:
        """Create Editor Agent with customizable mock response."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock()
        return EditorAgent(name="Test Editor", llm=mock_llm)

    @pytest.mark.asyncio
    async def test_check_consistency_returns_report(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that consistency check returns proper report."""
        consistency_json = json.dumps({
            "issues": [],
            "character_appearances": ["Alice"],
            "overall_consistency": "good",
            "summary": "No issues found"
        })
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content=consistency_json
        )

        result = await editor_with_mock_response._check_consistency(
            content="Alice walked to the store.",
            characters=[{"name": "Alice", "role": "protagonist"}],
            world_context={}
        )

        assert result["overall_consistency"] == "good"
        assert "Alice" in result["character_appearances"]

    @pytest.mark.asyncio
    async def test_check_consistency_detects_issues(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that consistency check can detect issues."""
        consistency_json = json.dumps({
            "issues": [{
                "type": "character",
                "severity": "high",
                "description": "Character acts out of character",
                "location": "Paragraph 3",
                "suggestion": "Revise to match established personality"
            }],
            "character_appearances": ["Alice"],
            "overall_consistency": "fair",
            "summary": "One consistency issue found"
        })
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content=consistency_json
        )

        result = await editor_with_mock_response._check_consistency(
            content="Alice was suddenly cruel and mean.",
            characters=[{"name": "Alice", "personality": {"traits": ["kind", "gentle"]}}],
            world_context={}
        )

        assert result["overall_consistency"] == "fair"
        assert len(result["issues"]) == 1
        assert result["issues"][0]["type"] == "character"

    @pytest.mark.asyncio
    async def test_check_consistency_handles_markdown(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that consistency check handles markdown-wrapped JSON."""
        consistency_json = json.dumps({
            "issues": [],
            "character_appearances": [],
            "overall_consistency": "good",
            "summary": "Clean"
        })
        markdown_response = f"```json\n{consistency_json}\n```"
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content=markdown_response
        )

        result = await editor_with_mock_response._check_consistency(
            content="Some content",
            characters=[],
            world_context={}
        )

        assert result["overall_consistency"] == "good"

    @pytest.mark.asyncio
    async def test_check_consistency_handles_invalid_json(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that consistency check handles invalid JSON gracefully."""
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content="This is not valid JSON"
        )

        result = await editor_with_mock_response._check_consistency(
            content="Some content",
            characters=[],
            world_context={}
        )

        assert result["overall_consistency"] == "unknown"
        assert "Could not parse" in result["summary"]


class TestQualityScoring:
    """Tests for quality scoring methods."""

    @pytest.fixture
    def editor_with_mock_response(self) -> EditorAgent:
        """Create Editor Agent with customizable mock response."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock()
        return EditorAgent(name="Test Editor", llm=mock_llm)

    @pytest.mark.asyncio
    async def test_score_content_returns_score(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that scoring returns proper score structure."""
        score_json = json.dumps({
            "overall": 8,
            "breakdown": {
                "prose_quality": 8,
                "dialogue": 7,
                "pacing": 8,
                "character_development": 9,
                "world_building": 8,
                "emotional_impact": 8
            },
            "strengths": ["Strong character development", "Good pacing"],
            "weaknesses": ["Dialogue could be sharper"],
            "recommendation": "publish"
        })
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content=score_json
        )

        result = await editor_with_mock_response._score_content_web_fiction("Sample content", chapter_number=1)

        assert result["overall"] == 8
        assert result["recommendation"] == "publish"
        assert len(result["strengths"]) > 0
        assert len(result["weaknesses"]) > 0

    @pytest.mark.asyncio
    async def test_score_content_handles_invalid_json(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that scoring handles invalid JSON gracefully."""
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content="Not JSON at all"
        )

        result = await editor_with_mock_response._score_content_web_fiction("Sample content", chapter_number=1)

        # Should return default values
        assert result["overall"] == 5
        assert result["recommendation"] == "revise"

    @pytest.mark.asyncio
    async def test_score_content_handles_markdown(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that scoring handles markdown-wrapped JSON."""
        score_json = json.dumps({
            "overall": 7,
            "breakdown": {},
            "strengths": [],
            "weaknesses": [],
            "recommendation": "revise"
        })
        markdown_response = f"```json\n{score_json}\n```"
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content=markdown_response
        )

        result = await editor_with_mock_response._score_content_web_fiction("Sample content", chapter_number=1)

        assert result["overall"] == 7


class TestContentEditing:
    """Tests for content editing methods."""

    @pytest.fixture
    def editor_with_mock_response(self) -> EditorAgent:
        """Create Editor Agent with customizable mock response."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock()
        return EditorAgent(name="Test Editor", llm=mock_llm)

    @pytest.mark.asyncio
    async def test_edit_content_returns_original_when_good(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that good content is returned unchanged."""
        content = "This is clean content without issues."

        result = await editor_with_mock_response._edit_content(
            content=content,
            style_issues=[],  # No style issues
            consistency_report={"overall_consistency": "good", "issues": []}
        )

        # Should return original if no issues
        assert result == content

    @pytest.mark.asyncio
    async def test_edit_content_edits_when_issues(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test that content with issues gets edited."""
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content="This is the edited and improved content."
        )

        # Create many style issues to trigger editing
        style_issues = [{"type": "test", "text": "test"} for _ in range(6)]

        result = await editor_with_mock_response._edit_content(
            content="Original content with issues.",
            style_issues=style_issues,
            consistency_report={"overall_consistency": "fair", "issues": []}
        )

        assert result == "This is the edited and improved content."


class TestExecute:
    """Tests for the main execute method."""

    @pytest.fixture
    def editor(self) -> EditorAgent:
        """Create Editor Agent with mock LLM."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock()
        return EditorAgent(name="Test Editor", llm=mock_llm)

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, editor: EditorAgent) -> None:
        """Test that execute returns AgentResult."""
        consistency_json = json.dumps({
            "issues": [],
            "character_appearances": [],
            "overall_consistency": "good",
            "summary": "Good"
        })
        score_json = json.dumps({
            "overall": 7,
            "breakdown": {},
            "strengths": [],
            "weaknesses": [],
            "recommendation": "publish"
        })
        edited_content = "Alice walked to the store."  # No changes needed

        editor.llm.generate_with_system.side_effect = [
            MagicMock(content=consistency_json),  # consistency check
            MagicMock(content=score_json),  # scoring
            MagicMock(content=edited_content),  # editing
        ]

        result = await editor.execute({
            "content": "Alice walked to the store.",
            "characters": [{"name": "Alice"}],
            "world_context": {}
        })

        assert isinstance(result, AgentResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_includes_all_data(self, editor: EditorAgent) -> None:
        """Test that execute includes all expected data."""
        consistency_json = json.dumps({
            "issues": [],
            "character_appearances": ["Alice"],
            "overall_consistency": "good",
            "summary": "Good"
        })
        score_json = json.dumps({
            "overall": 7,
            "breakdown": {"prose_quality": 7},
            "strengths": ["Good flow"],
            "weaknesses": [],
            "recommendation": "publish"
        })
        edited_content = "Alice walked to the store."

        editor.llm.generate_with_system.side_effect = [
            MagicMock(content=consistency_json),
            MagicMock(content=score_json),
            MagicMock(content=edited_content),
        ]

        result = await editor.execute({
            "content": "Alice walked to the store.",
            "characters": [{"name": "Alice"}],
            "world_context": {}
        })

        assert result.success is True
        assert "original_content" in result.data
        assert "edited_content" in result.data
        assert "style_issues" in result.data
        assert "consistency_report" in result.data
        assert "quality_score" in result.data
        assert "word_count" in result.data

    @pytest.mark.asyncio
    async def test_execute_handles_error(self, editor: EditorAgent) -> None:
        """Test that execute handles errors gracefully."""
        editor.llm.generate_with_system.side_effect = Exception("API Error")

        result = await editor.execute({
            "content": "Test content",
            "characters": [],
            "world_context": {}
        })

        assert result.success is False
        assert len(result.errors) > 0
        assert "Editing failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_execute_word_count(self, editor: EditorAgent) -> None:
        """Test that execute calculates word count."""
        consistency_json = json.dumps({
            "issues": [],
            "character_appearances": [],
            "overall_consistency": "good",
            "summary": ""
        })
        score_json = json.dumps({
            "overall": 7,
            "breakdown": {},
            "strengths": [],
            "weaknesses": [],
            "recommendation": "publish"
        })
        edited_content = "One two three four five."

        editor.llm.generate_with_system.side_effect = [
            MagicMock(content=consistency_json),
            MagicMock(content=score_json),
            MagicMock(content=edited_content),
        ]

        result = await editor.execute({
            "content": "One two three four five.",
            "characters": [],
            "world_context": {}
        })

        assert result.success is True
        assert result.data["word_count"] == 5


class TestCharacterConsistency:
    """Tests for character-specific consistency checking."""

    @pytest.fixture
    def editor_with_mock_response(self) -> EditorAgent:
        """Create Editor Agent with customizable mock response."""
        mock_llm = MagicMock()
        mock_llm.generate_with_system = AsyncMock()
        return EditorAgent(name="Test Editor", llm=mock_llm)

    @pytest.mark.asyncio
    async def test_check_character_consistency(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test character consistency check."""
        char_json = json.dumps({
            "character": "Alice",
            "consistent": True,
            "issues": [],
            "traits_shown": ["brave", "intelligent"],
            "traits_missing": [],
            "dialogue_quality": "natural",
            "recommendation": "Character is well portrayed"
        })
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content=char_json
        )

        result = await editor_with_mock_response.check_character_consistency(
            content="Alice bravely faced the challenge.",
            character_name="Alice",
            character_profile={"name": "Alice", "personality": {"traits": ["brave", "intelligent"]}}
        )

        assert result["consistent"] is True
        assert result["character"] == "Alice"
        assert "brave" in result["traits_shown"]

    @pytest.mark.asyncio
    async def test_check_character_consistency_handles_invalid_json(
        self, editor_with_mock_response: EditorAgent
    ) -> None:
        """Test character consistency handles invalid JSON."""
        editor_with_mock_response.llm.generate_with_system.return_value = MagicMock(
            content="Not JSON"
        )

        result = await editor_with_mock_response.check_character_consistency(
            content="Some content",
            character_name="Alice",
            character_profile={}
        )

        # Should return safe default
        assert result["consistent"] is True
        assert result["issues"] == []
