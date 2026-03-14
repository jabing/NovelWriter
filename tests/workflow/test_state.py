"""Tests for workflow state management."""

import json

from src.novel_agent.workflow.state import (
    WorkflowCheckpoint,
    WorkflowState,
    create_checkpoint,
)


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""

    def test_default_values(self) -> None:
        """Test that default values are correctly set."""
        state = WorkflowState()
        assert state.planning_complete is False
        assert state.last_generated_chapter == 0
        assert state.validation_enabled is True
        assert state.volume_count == 0

    def test_custom_values(self) -> None:
        """Test that custom values are correctly set."""
        state = WorkflowState(
            planning_complete=True,
            last_generated_chapter=5,
            validation_enabled=False,
            volume_count=2,
        )
        assert state.planning_complete is True
        assert state.last_generated_chapter == 5
        assert state.validation_enabled is False
        assert state.volume_count == 2

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        state = WorkflowState(
            planning_complete=True,
            last_generated_chapter=3,
            validation_enabled=False,
            volume_count=1,
        )
        result = state.to_dict()

        assert result["planning_complete"] is True
        assert result["last_generated_chapter"] == 3
        assert result["validation_enabled"] is False
        assert result["volume_count"] == 1

    def test_to_dict_roundtrip(self) -> None:
        """Test that from_dict can reconstruct from to_dict output."""
        original = WorkflowState(
            planning_complete=True,
            last_generated_chapter=7,
            validation_enabled=False,
            volume_count=3,
        )
        dict_repr = original.to_dict()
        restored = WorkflowState.from_dict(dict_repr)

        assert restored.planning_complete == original.planning_complete
        assert restored.last_generated_chapter == original.last_generated_chapter
        assert restored.validation_enabled == original.validation_enabled
        assert restored.volume_count == original.volume_count

    def test_from_dict_with_missing_fields(self) -> None:
        """Test from_dict with partial data uses defaults."""
        data = {"planning_complete": True}
        state = WorkflowState.from_dict(data)

        assert state.planning_complete is True
        assert state.last_generated_chapter == 0
        assert state.validation_enabled is True
        assert state.volume_count == 0

    def test_from_dict_empty(self) -> None:
        """Test from_dict with empty dictionary uses all defaults."""
        state = WorkflowState.from_dict({})
        assert state.planning_complete is False
        assert state.last_generated_chapter == 0
        assert state.validation_enabled is True
        assert state.volume_count == 0


class TestWorkflowCheckpoint:
    """Tests for WorkflowCheckpoint dataclass."""

    def test_initialization(self) -> None:
        """Test that checkpoint initializes correctly."""
        checkpoint = WorkflowCheckpoint(
            chapter_number=1,
            content="Chapter content here",
            timestamp="2024-01-01T00:00:00",
            project_id="test-project",
        )

        assert checkpoint.chapter_number == 1
        assert checkpoint.content == "Chapter content here"
        assert checkpoint.timestamp == "2024-01-01T00:00:00"
        assert checkpoint.project_id == "test-project"

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        checkpoint = WorkflowCheckpoint(
            chapter_number=5,
            content="Some content",
            timestamp="2024-01-01T12:00:00",
            project_id="proj-123",
        )
        result = checkpoint.to_dict()

        assert result["chapter_number"] == 5
        assert result["content"] == "Some content"
        assert result["timestamp"] == "2024-01-01T12:00:00"
        assert result["project_id"] == "proj-123"

    def test_to_dict_roundtrip(self) -> None:
        """Test that from_dict can reconstruct from to_dict output."""
        original = WorkflowCheckpoint(
            chapter_number=10,
            content="Full chapter content",
            timestamp="2024-06-15T08:30:00",
            project_id="my-novel",
        )
        dict_repr = original.to_dict()
        restored = WorkflowCheckpoint.from_dict(dict_repr)

        assert restored.chapter_number == original.chapter_number
        assert restored.content == original.content
        assert restored.timestamp == original.timestamp
        assert restored.project_id == original.project_id

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data = {
            "chapter_number": 3,
            "content": "Test content",
            "timestamp": "2024-03-01T10:00:00",
            "project_id": "project-456",
        }
        checkpoint = WorkflowCheckpoint.from_dict(data)

        assert checkpoint.chapter_number == 3
        assert checkpoint.content == "Test content"
        assert checkpoint.timestamp == "2024-03-01T10:00:00"
        assert checkpoint.project_id == "project-456"


class TestCreateCheckpoint:
    """Tests for create_checkpoint factory function."""

    def test_creates_checkpoint(self) -> None:
        """Test that create_checkpoint returns a checkpoint."""
        checkpoint = create_checkpoint(
            chapter_number=1,
            content="New chapter",
            project_id="test-project",
        )

        assert checkpoint.chapter_number == 1
        assert checkpoint.content == "New chapter"
        assert checkpoint.project_id == "test-project"
        assert checkpoint.timestamp is not None

    def test_timestamp_is_isoformat(self) -> None:
        """Test that timestamp is in ISO format."""
        checkpoint = create_checkpoint(
            chapter_number=2,
            content="Content",
            project_id="proj",
        )

        # Check timestamp is parseable ISO format
        from datetime import datetime

        parsed = datetime.fromisoformat(checkpoint.timestamp)
        assert parsed is not None

    def test_timestamp_changes_each_call(self) -> None:
        """Test that each call gets a unique timestamp."""
        checkpoint1 = create_checkpoint(1, "A", "p1")
        import time

        time.sleep(0.01)  # Small delay to ensure different timestamp
        checkpoint2 = create_checkpoint(1, "A", "p1")

        assert checkpoint1.timestamp != checkpoint2.timestamp


class TestJsonSerialization:
    """Tests for JSON serialization compatibility."""

    def test_workflow_state_json_roundtrip(self) -> None:
        """Test JSON serialization roundtrip for WorkflowState."""
        original = WorkflowState(
            planning_complete=True,
            last_generated_chapter=5,
            validation_enabled=False,
            volume_count=2,
        )

        json_str = json.dumps(original.to_dict())
        restored_data = json.loads(json_str)
        restored = WorkflowState.from_dict(restored_data)

        assert restored.planning_complete == original.planning_complete
        assert restored.last_generated_chapter == original.last_generated_chapter
        assert restored.volume_count == original.volume_count

    def test_workflow_checkpoint_json_roundtrip(self) -> None:
        """Test JSON serialization roundtrip for WorkflowCheckpoint."""
        original = WorkflowCheckpoint(
            chapter_number=1,
            content="Chapter content",
            timestamp="2024-01-01T00:00:00",
            project_id="test-project",
        )

        json_str = json.dumps(original.to_dict())
        restored_data = json.loads(json_str)
        restored = WorkflowCheckpoint.from_dict(restored_data)

        assert restored.chapter_number == original.chapter_number
        assert restored.content == original.content
        assert restored.project_id == original.project_id
