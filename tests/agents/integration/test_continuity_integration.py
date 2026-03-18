"""Integration tests for continuity checking in chapter generation workflow.

Tests end-to-end chapter generation with continuity validation:
- Full flow success scenarios
- Strict mode failure handling
- Retry mechanisms
- Knowledge graph failure handling
- OFF mode validation skipping
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from src.novel_agent.workflow.generate_workflow import (
    ChapterGenerateWorkflow,
    GenerateResult,
    GeneratedChapter,
)
from src.novel_agent.novel.continuity_config import ContinuityConfig, ContinuityStrictness
from src.novel_agent.novel.continuity import StoryState
from src.novel_agent.llm.base import BaseLLM


class TestContinuityIntegration:
    """End-to-end integration tests for continuity checking."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM with configurable responses."""
        llm = MagicMock(spec=BaseLLM)
        llm.generate = AsyncMock(return_value=MagicMock(content="Test content"))
        llm.generate_with_system = AsyncMock(return_value=MagicMock(content="Test content"))
        return llm

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary directory for storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def project_with_outline(self, temp_storage):
        """Create a test project with valid outline."""
        project_id = "test_novel"
        project_dir = temp_storage / "novels" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        outline_data = {
            "genre": "fantasy",
            "chapters": [
                {
                    "chapter": 1,
                    "number": 1,
                    "title": "The Beginning",
                    "summary": "The hero begins their journey",
                    "characters": ["Alice"],
                    "location": "Starting Village",
                    "key_events": ["Hero receives quest"],
                },
                {
                    "chapter": 2,
                    "number": 2,
                    "title": "The Journey",
                    "summary": "The hero travels to distant lands",
                    "characters": ["Alice", "Bob"],
                    "location": "Forest Path",
                    "key_events": ["Meeting the guide"],
                },
                {
                    "chapter": 3,
                    "number": 3,
                    "title": "The Challenge",
                    "summary": "The hero faces their first challenge",
                    "characters": ["Alice", "Bob"],
                    "location": "Dark Cave",
                    "key_events": ["Battle with monster"],
                },
            ],
        }

        import json

        with open(project_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(outline_data, f)

        return project_id

    def _create_valid_chapter_content(self, chapter_num: int, title: str) -> str:
        """Create valid chapter content that passes validation (800+ words, title, ending)."""
        # Create content with title, sufficient words, and ending marker
        # Need enough content to pass 500 character/word minimum check
        paragraphs = []
        for i in range(15):
            paragraphs.append(
                f"Paragraph {i + 1}: This is the story of adventure and discovery. "
                f"The hero embarks on a journey through distant lands. "
                f"Along the way, many challenges are faced and overcome. "
                f"Friends are made and enemies are encountered. "
                f"The path forward is never clear but determination guides the way."
            )
        content = f"Chapter {chapter_num}: {title}\n\n" + "\n\n".join(paragraphs) + "\n\nTBC"
        return content

    def _create_short_chapter_content(self, chapter_num: int, title: str) -> str:
        """Create short chapter content that fails validation (100 words, no ending)."""
        content = f"Chapter {chapter_num}: {title}\n\n" + "Short content. " * 10
        return content

    @pytest.mark.asyncio
    async def test_full_flow_success(self, mock_llm, temp_storage, project_with_outline):
        """Test successful generation of multiple chapters with all validations passing.

        Mock LLM returns valid chapter content (800+ words with proper ending).
        Generate 3 chapters.
        Assert all 3 chapters generated successfully.
        Assert all chapters have validation_passed = True.
        Assert validation_issues is empty for each chapter.
        """
        # Setup: Create workflow with default STRICT mode
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            continuity_config=ContinuityConfig(strictness=ContinuityStrictness.STRICT),
        )

        # Mock the writer to return valid content for all chapters
        valid_contents = [
            self._create_valid_chapter_content(i + 1, f"Chapter {i + 1}") for i in range(3)
        ]
        call_count = 0

        async def mock_write_chapter(*args, **kwargs):
            nonlocal call_count
            content = valid_contents[call_count % len(valid_contents)]
            call_count += 1
            return content

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(side_effect=mock_write_chapter)

        # Execute: Generate 3 chapters
        result = await workflow.execute(
            project_id=project_with_outline,
            start_chapter=1,
            count=3,
            storage_path=temp_storage,
        )

        # Assert: All 3 chapters generated successfully
        assert result.success is True
        assert result.chapters_generated == 3
        assert len(result.chapters) == 3

        # Assert: All chapters have validation_passed = True
        for chapter in result.chapters:
            assert chapter.validation_passed is True, (
                f"Chapter {chapter.chapter_number} should have passed validation"
            )

        # Assert: All chapters have empty validation_issues
        for chapter in result.chapters:
            assert chapter.validation_issues == [], (
                f"Chapter {chapter.chapter_number} should have no validation issues, "
                f"got: {chapter.validation_issues}"
            )

    @pytest.mark.asyncio
    async def test_strict_mode_stops_on_failure(self, mock_llm, temp_storage, project_with_outline):
        """Test that STRICT mode stops generation when a chapter fails.

        Use ContinuityConfig(strictness=ContinuityStrictness.STRICT).
        Mock LLM to fail on chapter 2 (raise exception).
        Request 3 chapters.
        Assert only 1 chapter generated (chapter 1).
        Assert result.success = False.
        Assert error message contains 'Failed to generate chapter 2'.
        """
        # Setup: Create workflow with STRICT mode
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            continuity_config=ContinuityConfig(strictness=ContinuityStrictness.STRICT),
        )

        call_count = 0

        async def mock_write_chapter_fails_on_second(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return self._create_valid_chapter_content(1, "The Beginning")
            else:
                # Simulate failure on chapter 2
                raise RuntimeError("LLM generation failed")

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(
            side_effect=mock_write_chapter_fails_on_second
        )

        # Execute: Request 3 chapters
        result = await workflow.execute(
            project_id=project_with_outline,
            start_chapter=1,
            count=3,
            storage_path=temp_storage,
        )

        # Assert: Only 1 chapter generated (chapter 1)
        assert result.chapters_generated == 1
        assert len(result.chapters) == 1
        assert result.chapters[0].chapter_number == 1

        # Assert: result.success = False
        assert result.success is False

        # Assert: Error message contains expected text
        assert any(
            "Failed to generate chapter 2" in error or "chapter 2" in error.lower()
            for error in result.errors
        ), f"Expected error about chapter 2, got: {result.errors}"

    @pytest.mark.asyncio
    async def test_retry_then_success(self, mock_llm, temp_storage, project_with_outline):
        """Test that retry mechanism works and eventually succeeds.

        Mock LLM to fail twice, then succeed on 3rd attempt.
        Use default STRICT mode.
        Request 1 chapter.
        Assert chapter generated successfully.
        Assert retry_manager.get_retry_count() == 2.
        """
        # Setup: Create workflow with STRICT mode
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            continuity_config=ContinuityConfig(strictness=ContinuityStrictness.STRICT),
        )

        attempt_count = 0

        async def mock_write_with_retries(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                # Fail on first 2 attempts
                raise RuntimeError(f"Attempt {attempt_count} failed")
            # Succeed on 3rd attempt
            return self._create_valid_chapter_content(1, "The Beginning")

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(side_effect=mock_write_with_retries)

        # Execute: Request 1 chapter
        result = await workflow.execute(
            project_id=project_with_outline,
            start_chapter=1,
            count=1,
            storage_path=temp_storage,
        )

        # Assert: Chapter generated successfully
        assert result.success is True
        assert result.chapters_generated == 1
        assert len(result.chapters) == 1
        assert result.chapters[0].validation_passed is True

        # Assert: Retry count should be 2 (2 retries before success)
        assert workflow._retry_manager.get_retry_count() == 2, (
            f"Expected 2 retries, got {workflow._retry_manager.get_retry_count()}"
        )

    @pytest.mark.asyncio
    async def test_kg_failure_handling(self, mock_llm, temp_storage, project_with_outline):
        """Test that KG failures are handled correctly in STRICT mode.

        Mock continuity_manager.update_from_chapter to raise exception.
        Use STRICT mode.
        Request 1 chapter.
        Assert validation_passed = False (due to KG failure).
        """
        # Setup: Create workflow with STRICT mode
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            continuity_config=ContinuityConfig(strictness=ContinuityStrictness.STRICT),
        )

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(
            return_value=self._create_valid_chapter_content(1, "The Beginning")
        )

        # Mock KG failure by patching the continuity manager's update_from_chapter
        with patch(
            "src.novel_agent.workflow.generate_workflow.ContinuityManager"
        ) as MockContinuityManager:
            mock_continuity = MagicMock()
            mock_continuity.update_from_chapter.side_effect = RuntimeError("KG transaction failed")
            MockContinuityManager.return_value = mock_continuity

            # Re-initialize to use the mocked continuity manager
            workflow._initialize_components(project_with_outline, temp_storage)
            workflow._continuity_manager = mock_continuity
            workflow._story_state = StoryState(
                chapter=0,
                location="",
                active_characters=[],
                character_states={},
                plot_threads=[],
                key_events=[],
            )

            # Execute: Request 1 chapter
            result = await workflow.execute(
                project_id=project_with_outline,
                start_chapter=1,
                count=1,
                storage_path=temp_storage,
            )

            # Assert: Chapter was generated but validation_passed = False due to KG failure
            assert result.success is True
            assert len(result.chapters) == 1
            assert result.chapters[0].validation_passed is False, (
                "Validation should fail due to KG error in STRICT mode"
            )

    @pytest.mark.asyncio
    async def test_off_mode_skips_validation(self, mock_llm, temp_storage, project_with_outline):
        """Test that OFF mode skips all validation checks.

        Use ContinuityConfig(strictness=ContinuityStrictness.OFF).
        Mock LLM returns short content (100 words, no ending marker).
        Request 1 chapter.
        Assert chapter generated.
        Assert validation_passed = True (OFF mode ignores validation).
        """
        # Setup: Create workflow with OFF mode
        workflow = ChapterGenerateWorkflow(
            name="test_workflow",
            llm=mock_llm,
            genre="fantasy",
            continuity_config=ContinuityConfig(strictness=ContinuityStrictness.OFF),
        )

        workflow.writer = MagicMock()
        workflow.writer.write_chapter_with_context = AsyncMock(
            return_value=self._create_short_chapter_content(1, "The Beginning")
        )

        # Execute: Request 1 chapter
        result = await workflow.execute(
            project_id=project_with_outline,
            start_chapter=1,
            count=1,
            storage_path=temp_storage,
        )

        # Assert: Chapter was generated
        assert result.success is True
        assert result.chapters_generated == 1
        assert len(result.chapters) == 1

        # Assert: validation_passed = True (OFF mode ignores validation)
        assert result.chapters[0].validation_passed is True, (
            "OFF mode should skip validation and return True"
        )

        # Assert: Content is the short content we provided
        assert len(result.chapters[0].content.split()) < 200, (
            "Content should be short (< 200 words)"
        )
