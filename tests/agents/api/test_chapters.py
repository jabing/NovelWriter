"""Tests for chapters router."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import StudioState


class TestListChapters:
    """Tests for GET /api/novels/{novel_id}/chapters endpoint."""

    def test_list_chapters_not_found(self, client: TestClient):
        """Test listing chapters for non-existent novel."""
        response = client.get("/api/novels/nonexistent-novel/chapters")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_list_chapters_empty(self, client: TestClient):
        """Test listing chapters when directory exists but is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters")
                
                assert response.status_code == 200
                data = response.json()
                assert data["project_id"] == "test-novel"
                assert data["chapters"] == []
                assert data["total_count"] == 0
                assert data["completed_count"] == 0

    def test_list_chapters_with_json(self, client: TestClient):
        """Test listing chapters from JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            # Create JSON chapter
            chapter_data = {
                "number": 1,
                "title": "The Beginning",
                "content": "Once upon a time " * 20,
                "author_notes": "Chapter 1 summary."
            }
            with open(novel_dir / "chapter_001.json", "w") as f:
                json.dump(chapter_data, f)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters")
                
                assert response.status_code == 200
                data = response.json()
                assert data["project_id"] == "test-novel"
                assert len(data["chapters"]) == 1
                assert data["chapters"][0]["chapter_number"] == 1
                assert data["chapters"][0]["title"] == "The Beginning"
                assert data["chapters"][0]["status"] == "published"
                assert data["chapters"][0]["summary"] == "Chapter 1 summary."

    def test_list_chapters_multiple(self, client: TestClient):
        """Test listing multiple chapters from JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            # Create multiple JSON chapters
            for i in [1, 3]:
                chapter_data = {
                    "number": i,
                    "title": f"Chapter {i}",
                    "content": f"Content for chapter {i}. " * 30,
                }
                with open(novel_dir / f"chapter_{i:03d}.json", "w") as f:
                    json.dump(chapter_data, f)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters")
                
                assert response.status_code == 200
                data = response.json()
                assert data["total_count"] == 2
                assert len(data["chapters"]) == 2

                # Chapters should be sorted by number
                numbers = [c["chapter_number"] for c in data["chapters"]]
                assert numbers == [1, 3]

    def test_list_chapters_with_markdown(self, client: TestClient):
        """Test listing chapters from Markdown files when JSON doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            # Create MD chapter
            md_content = "# Chapter One\n\nThe first chapter content."
            with open(novel_dir / "chapter_001.md", "w") as f:
                f.write(md_content)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters")
                
                assert response.status_code == 200
                data = response.json()
                assert data["total_count"] == 1
                assert data["chapters"][0]["title"] == "Chapter One"

    def test_list_chapters_json_over_md(self, client: TestClient):
        """Test that JSON chapters take precedence over MD chapters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            # Create JSON chapter
            json_data = {
                "number": 1,
                "title": "JSON Chapter",
                "content": "JSON content here",
            }
            with open(novel_dir / "chapter_001.json", "w") as f:
                json.dump(json_data, f)

            # Create MD chapter with different data
            md_content = "# Chapter One\n\nThis is from MD file."
            with open(novel_dir / "chapter_001.md", "w") as f:
                f.write(md_content)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters")
                
                assert response.status_code == 200
                data = response.json()
                # JSON chapter should be used, not MD
                assert data["chapters"][0]["title"] == "JSON Chapter"


class TestGetChapter:
    """Tests for GET /api/novels/{novel_id}/chapters/{num} endpoint."""

    def test_get_chapter_not_found(self, client: TestClient):
        """Test getting non-existent chapter."""
        response = client.get("/api/novels/nonexistent-novel/chapters/1")
        
        assert response.status_code == 404

    def test_get_chapter_from_json(self, client: TestClient):
        """Test getting chapter from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            chapter_data = {
                "number": 5,
                "title": "The Climax",
                "content": "The hero faces the ultimate challenge. " * 50,
                "author_notes": "The final showdown.",
            }
            with open(novel_dir / "chapter_005.json", "w") as f:
                json.dump(chapter_data, f)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters/5")
                
                assert response.status_code == 200
                data = response.json()
                assert data["chapter_number"] == 5
                assert data["title"] == "The Climax"
                assert data["status"] == "published"
                assert data["summary"] == "The final showdown."

    def test_get_chapter_from_markdown(self, client: TestClient):
        """Test getting chapter from Markdown file when JSON doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            md_content = "# Chapter Seven\n\nContent for chapter 7."
            with open(novel_dir / "chapter_007.md", "w") as f:
                f.write(md_content)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters/7")
                
                assert response.status_code == 200
                data = response.json()
                assert data["chapter_number"] == 7
                assert data["title"] == "Chapter Seven"

    def test_get_chapter_without_number_in_json(self, client: TestClient):
        """Test getting chapter when JSON has no number field (uses filename)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)
            
            # Create chapter without number field
            chapter_data = {
                "title": "Mystery Chapter",
                "content": "Some content here.",
            }
            with open(novel_dir / "chapter_010.json", "w") as f:
                json.dump(chapter_data, f)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters/10")
                
                assert response.status_code == 200
                data = response.json()
                # Should extract number from filename
                assert data["chapter_number"] == 10
                assert data["title"] == "Mystery Chapter"

    def test_get_chapter_specific_not_found(self, client: TestClient):
        """Test getting specific chapter that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel" / "chapters"
            novel_dir.mkdir(parents=True)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                
                response = client.get("/api/novels/test-novel/chapters/999")
                
                assert response.status_code == 404


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_extract_chapter_number_from_filename_valid(self):
        """Test extracting chapter number from valid filename."""
        from src.novel_agent.api.routers.chapters import _extract_chapter_number_from_filename

        result = _extract_chapter_number_from_filename(Path("chapter_042.json"))
        assert result == 42

        result = _extract_chapter_number_from_filename(Path("chapter_001.json"))
        assert result == 1

    def test_extract_chapter_number_from_filename_invalid(self):
        """Test extracting chapter number from invalid filename."""
        from src.novel_agent.api.routers.chapters import _extract_chapter_number_from_filename

        result = _extract_chapter_number_from_filename(Path("invalid.json"))
        assert result is None

        result = _extract_chapter_number_from_filename(Path("no_number_here.txt"))
        assert result is None


class TestCreateChapter:
    """Tests for POST /api/novels/{novel_id}/chapters endpoint."""

    def test_create_chapter_success(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test creating a new chapter successfully."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        # Create a test novel project
        project = NovelProject(
            id="test-novel",
            title="Test Novel",
            genre="Fantasy",
            language="en",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        # Create chapter payload
        chapter_data = {
            "title": "第一章 初入江湖",
            "content": "内容...",
            "order": 1,
            "status": "draft",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel"
            novel_dir.mkdir(parents=True)

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = novel_dir
                mock_path_instance = MagicMock()
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance

                response = client.post(
                    "/api/novels/test-novel/chapters",
                    json=chapter_data,
                )

                assert response.status_code == 201
                data = response.json()
                assert data["chapter_number"] == 1
                assert data["title"] == "第一章 初入江湖"
                assert data["content"] == "内容..."
                assert data["status"] == "draft"
                assert data["word_count"] == 1
                assert data["created_at"] is not None
                assert data["updated_at"] is not None

    def test_create_chapter_novel_not_found(self, client: TestClient):
        """Test creating chapter for non-existent novel."""
        chapter_data = {
            "title": "New Chapter",
            "content": "Content",
            "order": 1,
        }

        response = client.post(
            "/api/novels/nonexistent-novel/chapters",
            json=chapter_data,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_create_chapter_multiple_sequential(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test creating multiple chapters sequentially."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        # Create a test novel project
        project = NovelProject(
            id="test-novel-2",
            title="Test Novel 2",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel-2"
            chapters_dir = novel_dir / "chapters"
            chapters_dir.mkdir(parents=True)

            # Create first chapter
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.__truediv__.return_value = chapters_dir

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = mock_path_instance
                mock_path_instance.glob.side_effect = lambda pattern: []

                response = client.post(
                    "/api/novels/test-novel-2/chapters",
                    json={"title": "Chapter 1", "content": "Content 1", "order": 1},
                )

                assert response.status_code == 201
                assert response.json()["chapter_number"] == 1

                # Simulate first chapter file exists
                mock_path_instance.glob.side_effect = lambda pattern: [
                    chapters_dir / "chapter_001.json"
                ] if "json" in pattern else []

                # Create second chapter
                response = client.post(
                    "/api/novels/test-novel-2/chapters",
                    json={"title": "Chapter 2", "content": "Content 2", "order": 2},
                )

                assert response.status_code == 201
                assert response.json()["chapter_number"] == 2

    def test_create_chapter_with_empty_content(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test creating chapter with empty content."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel-3",
            title="Test Novel 3",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel-3"
            novel_dir.mkdir(parents=True)

            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = mock_path_instance
                mock_path_instance.glob.return_value = []

                response = client.post(
                    "/api/novels/test-novel-3/chapters",
                    json={"title": "Empty Chapter", "content": "", "order": 0},
                )

                assert response.status_code == 201
                data = response.json()
                assert data["word_count"] == 0
                assert data["content"] == ""

    def test_create_chapter_default_values(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test creating chapter with default values."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel-4",
            title="Test Novel 4",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel-4"
            novel_dir.mkdir(parents=True)

            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True

            with patch("src.novel_agent.api.routers.chapters.Path") as mock_path:
                mock_path.return_value = mock_path_instance
                mock_path_instance.glob.return_value = []

                # Only provide title, let other fields use defaults
                response = client.post(
                    "/api/novels/test-novel-4/chapters",
                    json={"title": "Minimal Chapter"},
                )

                assert response.status_code == 201
                data = response.json()
                assert data["title"] == "Minimal Chapter"
                assert data["status"] == "draft"
                assert data["word_count"] == 0


class TestUpdateChapter:
    """Tests for PUT /api/novels/{novel_id}/chapters/{chapter_id} endpoint."""

    def test_update_chapter(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test updating a chapter with partial data."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel",
            title="Test Novel",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel"
            chapters_dir = novel_dir / "chapters"
            chapters_dir.mkdir(parents=True)

            chapter_file = chapters_dir / "chapter_001.json"
            chapter_data = {
                "number": 1,
                "title": "Chapter 1",
                "content": "Original content",
                "order": 1,
                "status": "draft",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
            with open(chapter_file, "w", encoding="utf-8") as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)

            # Mock Path to redirect data directory to temp directory
            def path_side_effect(path_str, *args, **kwargs):
                path_str = str(path_str)
                if "data/openviking/memory/novels/test-novel" in path_str:
                    path_str = path_str.replace("data/openviking/memory/novels/test-novel", str(novel_dir))
                return Path(path_str, *args, **kwargs)

            with patch("src.novel_agent.api.routers.chapters.Path", side_effect=path_side_effect):
                update_data = {
                    "title": "第一章 修改后",
                    "content": "新内容...",
                }

                response = client.put("/api/novels/test-novel/chapters/chapter-1", json=update_data)

                assert response.status_code == 200
                data = response.json()

                assert data["chapter_number"] == 1
                assert data["title"] == "第一章 修改后"
                assert data["content"] == "新内容..."
                assert data["status"] == "draft"
                assert "updated_at" in data
                assert data["updated_at"] != "2024-01-01T00:00:00"

    def test_update_chapter_partial(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test updating only title (partial update)."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel",
            title="Test Novel",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel"
            chapters_dir = novel_dir / "chapters"
            chapters_dir.mkdir(parents=True)

            chapter_file = chapters_dir / "chapter_001.json"
            chapter_data = {
                "number": 1,
                "title": "Chapter 1",
                "content": "Original content",
                "order": 1,
                "status": "draft",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
            with open(chapter_file, "w", encoding="utf-8") as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)

            # Mock Path to redirect data directory to temp directory
            def path_side_effect(path_str, *args, **kwargs):
                path_str = str(path_str)
                if "data/openviking/memory/novels/test-novel" in path_str:
                    path_str = path_str.replace("data/openviking/memory/novels/test-novel", str(novel_dir))
                return Path(path_str, *args, **kwargs)

            with patch("src.novel_agent.api.routers.chapters.Path", side_effect=path_side_effect):
                update_data = {"title": "Updated Title Only"}

                response = client.put("/api/novels/test-novel/chapters/1", json=update_data)

                assert response.status_code == 200
                data = response.json()

                assert data["title"] == "Updated Title Only"
                assert data["content"] == "Original content"
                assert data["status"] == "draft"

    def test_update_chapter_status(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test updating chapter status."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel",
            title="Test Novel",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel"
            chapters_dir = novel_dir / "chapters"
            chapters_dir.mkdir(parents=True)

            chapter_file = chapters_dir / "chapter_001.json"
            chapter_data = {
                "number": 1,
                "title": "Chapter 1",
                "content": "Original content",
                "order": 1,
                "status": "draft",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
            with open(chapter_file, "w", encoding="utf-8") as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)

            # Mock Path to redirect data directory to temp directory
            def path_side_effect(path_str, *args, **kwargs):
                path_str = str(path_str)
                if "data/openviking/memory/novels/test-novel" in path_str:
                    path_str = path_str.replace("data/openviking/memory/novels/test-novel", str(novel_dir))
                return Path(path_str, *args, **kwargs)

            with patch("src.novel_agent.api.routers.chapters.Path", side_effect=path_side_effect):
                update_data = {"status": "published"}

                response = client.put("/api/novels/test-novel/chapters/chapter-1", json=update_data)

                assert response.status_code == 200
                data = response.json()

                assert data["status"] == "published"

    def test_update_chapter_order(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test updating chapter order."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel",
            title="Test Novel",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel"
            chapters_dir = novel_dir / "chapters"
            chapters_dir.mkdir(parents=True)

            chapter_file = chapters_dir / "chapter_001.json"
            chapter_data = {
                "number": 1,
                "title": "Chapter 1",
                "content": "Original content",
                "order": 1,
                "status": "draft",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
            with open(chapter_file, "w", encoding="utf-8") as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)

            # Mock Path to redirect data directory to temp directory
            def path_side_effect(path_str, *args, **kwargs):
                path_str = str(path_str)
                if "data/openviking/memory/novels/test-novel" in path_str:
                    path_str = path_str.replace("data/openviking/memory/novels/test-novel", str(novel_dir))
                return Path(path_str, *args, **kwargs)

            with patch("src.novel_agent.api.routers.chapters.Path", side_effect=path_side_effect):
                update_data = {"order": 5}

                response = client.put("/api/novels/test-novel/chapters/chapter-1", json=update_data)

                assert response.status_code == 200

    def test_update_chapter_not_found(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test updating non-existent chapter returns 404."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel",
            title="Test Novel",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel"
            chapters_dir = novel_dir / "chapters"
            chapters_dir.mkdir(parents=True)

            # Mock Path to redirect data directory to temp directory
            def path_side_effect(path_str, *args, **kwargs):
                path_str = str(path_str)
                if "data/openviking/memory/novels/test-novel" in path_str:
                    path_str = path_str.replace("data/openviking/memory/novels/test-novel", str(novel_dir))
                return Path(path_str, *args, **kwargs)

            with patch("src.novel_agent.api.routers.chapters.Path", side_effect=path_side_effect):
                update_data = {"title": "New Title"}

                response = client.put("/api/novels/test-novel/chapters/chapter-999", json=update_data)

                assert response.status_code == 404

    def test_update_chapter_novel_not_found(self, client: TestClient):
        """Test updating chapter for non-existent novel returns 404."""
        update_data = {"title": "New Title"}

        response = client.put("/api/novels/non-existent-novel/chapters/chapter-1", json=update_data)

        assert response.status_code == 404

    def test_update_chapter_invalid_id(self, client: TestClient, mock_studio_state: "StudioState"):
        """Test updating chapter with invalid ID format."""
        from src.novel_agent.studio.core.state import NovelProject, ProjectStatus

        project = NovelProject(
            id="test-novel",
            title="Test Novel",
            genre="Fantasy",
            status=ProjectStatus.PLANNING,
        )
        mock_studio_state.add_project(project)

        with tempfile.TemporaryDirectory() as tmpdir:
            novel_dir = Path(tmpdir) / "test-novel"
            chapters_dir = novel_dir / "chapters"
            chapters_dir.mkdir(parents=True)

            # Mock Path to redirect data directory to temp directory
            def path_side_effect(path_str, *args, **kwargs):
                path_str = str(path_str)
                if "data/openviking/memory/novels/test-novel" in path_str:
                    path_str = path_str.replace("data/openviking/memory/novels/test-novel", str(novel_dir))
                return Path(path_str, *args, **kwargs)

            with patch("src.novel_agent.api.routers.chapters.Path", side_effect=path_side_effect):
                update_data = {"title": "New Title"}

                response = client.put("/api/novels/test-novel/chapters/invalid-id", json=update_data)

                assert response.status_code == 400
