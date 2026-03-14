"""Tests for CheckpointManager class."""

import json
from datetime import datetime, timedelta

import pytest

from src.novel.checkpointing import (
    CHECKPOINT_INTERVAL_WORDS,
    MAX_CHECKPOINT_AGE_DAYS,
    MAX_CHECKPOINT_SIZE_MB,
    MAX_CHECKPOINTS_PER_CHAPTER,
    Checkpoint,
    CheckpointManager,
    create_checkpoint_manager,
)


class TestCheckpointConstants:
    """Test configuration constants."""

    def test_checkpoint_interval_words_default(self):
        assert CHECKPOINT_INTERVAL_WORDS == 500

    def test_max_checkpoint_age_days_default(self):
        assert MAX_CHECKPOINT_AGE_DAYS == 7

    def test_max_checkpoint_size_mb_default(self):
        assert MAX_CHECKPOINT_SIZE_MB == 10

    def test_max_checkpoints_per_chapter_default(self):
        assert MAX_CHECKPOINTS_PER_CHAPTER == 20


class TestCheckpointDataclass:
    """Test Checkpoint dataclass."""

    def test_checkpoint_creation(self):
        checkpoint = Checkpoint(
            checkpoint_id="test_checkpoint",
            chapter_number=1,
            word_count=500,
            content="Test content",
            state_snapshot={"test": "data"},
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            checksum="abc123",
        )

        assert checkpoint.checkpoint_id == "test_checkpoint"
        assert checkpoint.chapter_number == 1
        assert checkpoint.word_count == 500
        assert checkpoint.content == "Test content"
        assert checkpoint.state_snapshot == {"test": "data"}
        assert checkpoint.metadata == {}

    def test_checkpoint_to_dict(self):
        checkpoint = Checkpoint(
            checkpoint_id="test",
            chapter_number=2,
            word_count=1000,
            content="Content",
            state_snapshot={"key": "value"},
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            checksum="xyz",
            metadata={"extra": "info"},
        )

        data = checkpoint.to_dict()

        assert data["checkpoint_id"] == "test"
        assert data["chapter_number"] == 2
        assert data["word_count"] == 1000
        assert data["content"] == "Content"
        assert data["checksum"] == "xyz"
        assert data["metadata"] == {"extra": "info"}

    def test_checkpoint_from_dict(self):
        data = {
            "checkpoint_id": "restored",
            "chapter_number": 3,
            "word_count": 1500,
            "content": "Restored content",
            "state_snapshot": {"restored": True},
            "created_at": "2025-01-01T12:00:00",
            "checksum": "def456",
            "metadata": {"restored": True},
        }

        checkpoint = Checkpoint.from_dict(data)

        assert checkpoint.checkpoint_id == "restored"
        assert checkpoint.chapter_number == 3
        assert checkpoint.word_count == 1500
        assert checkpoint.content == "Restored content"
        assert checkpoint.checksum == "def456"

    def test_checkpoint_serialization_roundtrip(self):
        original = Checkpoint(
            checkpoint_id="roundtrip",
            chapter_number=5,
            word_count=2000,
            content="Round trip test",
            state_snapshot={"test": "roundtrip"},
            created_at=datetime(2025, 3, 1, 10, 30, 0),
            checksum="ghi789",
            metadata={"round": "trip"},
        )

        data = original.to_dict()
        restored = Checkpoint.from_dict(data)

        assert restored.checkpoint_id == original.checkpoint_id
        assert restored.chapter_number == original.chapter_number
        assert restored.word_count == original.word_count
        assert restored.content == original.content
        assert restored.checksum == original.checksum


class TestCheckpointManagerInit:
    """Test CheckpointManager initialization."""

    def test_default_initialization(self, tmp_path):
        manager = CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

        assert manager.checkpoint_dir.exists()
        assert manager.interval_words == CHECKPOINT_INTERVAL_WORDS
        assert manager.max_age_days == MAX_CHECKPOINT_AGE_DAYS

    def test_custom_parameters(self, tmp_path):
        manager = CheckpointManager(
            checkpoint_dir=tmp_path / "custom",
            interval_words=250,
            max_age_days=14,
            max_checkpoints_per_chapter=10,
        )

        assert manager.interval_words == 250
        assert manager.max_age_days == 14
        assert manager.max_checkpoints_per_chapter == 10

    def test_directory_created_if_not_exists(self, tmp_path):
        checkpoint_dir = tmp_path / "new_dir" / "checkpoints"
        assert not checkpoint_dir.exists()

        CheckpointManager(checkpoint_dir=checkpoint_dir)

        assert checkpoint_dir.exists()


class TestCheckpointManagerCreate:
    """Test checkpoint creation."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

    def test_create_checkpoint_basic(self, manager):
        checkpoint = manager.create_checkpoint(
            chapter_number=1,
            word_count=500,
            content="Test content for checkpoint",
            state_snapshot={"chapter": 1, "events": []},
        )

        assert checkpoint is not None
        assert checkpoint.chapter_number == 1
        assert checkpoint.word_count == 500
        assert "chapter1" in checkpoint.checkpoint_id

    def test_create_checkpoint_saves_to_file(self, manager):
        checkpoint = manager.create_checkpoint(
            chapter_number=1,
            word_count=0,
            content="Initial content",
            state_snapshot={},
        )

        assert checkpoint is not None
        checkpoint_file = manager.checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
        assert checkpoint_file.exists()

    def test_create_checkpoint_with_metadata(self, manager):
        checkpoint = manager.create_checkpoint(
            chapter_number=1,
            word_count=100,
            content="Content",
            state_snapshot={},
            metadata={"author": "test", "version": "1.0"},
        )

        assert checkpoint is not None
        assert checkpoint.metadata["author"] == "test"
        assert checkpoint.metadata["version"] == "1.0"

    def test_create_checkpoint_generates_checksum(self, manager):
        checkpoint = manager.create_checkpoint(
            chapter_number=1,
            word_count=50,
            content="Test",
            state_snapshot={"key": "value"},
        )

        assert checkpoint is not None
        assert len(checkpoint.checksum) == 16  # Truncated SHA256

    def test_create_multiple_checkpoints_same_chapter(self, manager):
        cp1 = manager.create_checkpoint(
            chapter_number=1, word_count=0, content="Start", state_snapshot={}
        )
        cp2 = manager.create_checkpoint(
            chapter_number=1, word_count=500, content="More content", state_snapshot={}
        )
        cp3 = manager.create_checkpoint(
            chapter_number=1, word_count=1000, content="Even more", state_snapshot={}
        )

        assert cp1 is not None
        assert cp2 is not None
        assert cp3 is not None
        assert cp1.checkpoint_id != cp2.checkpoint_id
        assert cp2.checkpoint_id != cp3.checkpoint_id

    def test_create_checkpoint_tracks_current_chapter(self, manager):
        manager.create_checkpoint(chapter_number=1, word_count=0, content="Ch1", state_snapshot={})
        assert manager._current_chapter == 1

        manager.create_checkpoint(chapter_number=2, word_count=0, content="Ch2", state_snapshot={})
        assert manager._current_chapter == 2


class TestCheckpointManagerShouldCreate:
    """Test should_create_checkpoint logic."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(
            checkpoint_dir=tmp_path / "checkpoints",
            interval_words=500,
        )

    def test_should_create_at_chapter_start(self, manager):
        assert manager.should_create_checkpoint(chapter_number=1, word_count=0) is True

    def test_should_create_after_interval(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=0, content="Start", state_snapshot={}
        )

        assert manager.should_create_checkpoint(chapter_number=1, word_count=250) is False
        assert manager.should_create_checkpoint(chapter_number=1, word_count=500) is True
        assert manager.should_create_checkpoint(chapter_number=1, word_count=1000) is True

    def test_should_create_at_chapter_change(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=1000, content="Ch1", state_snapshot={}
        )

        assert manager.should_create_checkpoint(chapter_number=2, word_count=0) is True

    def test_should_create_detects_chapter_change(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=1000, content="Ch1 done", state_snapshot={}
        )

        assert manager._current_chapter == 1
        assert manager._last_checkpoint_words == 1000

        # should_create returns True for new chapter but doesn't reset tracking
        # The reset happens when create_checkpoint is called
        assert manager.should_create_checkpoint(chapter_number=2, word_count=0) is True
        assert manager._current_chapter == 1  # Not changed yet

        # Creating checkpoint for new chapter resets tracking
        manager.create_checkpoint(
            chapter_number=2, word_count=0, content="Ch2 start", state_snapshot={}
        )
        assert manager._current_chapter == 2
        assert manager._last_checkpoint_words == 0


class TestCheckpointManagerLoad:
    """Test checkpoint loading."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

    def test_load_existing_checkpoint(self, manager):
        created = manager.create_checkpoint(
            chapter_number=1,
            word_count=500,
            content="Test content",
            state_snapshot={"key": "value"},
        )

        assert created is not None
        loaded = manager.load_checkpoint(created.checkpoint_id)

        assert loaded is not None
        assert loaded.checkpoint_id == created.checkpoint_id
        assert loaded.content == "Test content"
        assert loaded.state_snapshot == {"key": "value"}

    def test_load_nonexistent_checkpoint(self, manager):
        loaded = manager.load_checkpoint("nonexistent_checkpoint")

        assert loaded is None

    def test_load_validates_checksum(self, manager):
        created = manager.create_checkpoint(
            chapter_number=1, word_count=100, content="Original", state_snapshot={}
        )

        assert created is not None
        checkpoint_path = manager.checkpoint_dir / f"{created.checkpoint_id}.json"

        with open(checkpoint_path, encoding="utf-8") as f:
            data = json.load(f)

        data["content"] = "Tampered content"

        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        loaded = manager.load_checkpoint(created.checkpoint_id)

        assert loaded is None


class TestCheckpointManagerGetLatest:
    """Test getting latest checkpoint."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

    def test_get_latest_returns_most_recent(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=0, content="First", state_snapshot={}
        )
        manager.create_checkpoint(
            chapter_number=1, word_count=500, content="Second", state_snapshot={}
        )
        manager.create_checkpoint(
            chapter_number=1, word_count=1000, content="Third", state_snapshot={}
        )

        latest = manager.get_latest_checkpoint()

        assert latest is not None
        assert latest.word_count == 1000

    def test_get_latest_for_specific_chapter(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=1000, content="Ch1", state_snapshot={}
        )
        manager.create_checkpoint(
            chapter_number=2, word_count=500, content="Ch2", state_snapshot={}
        )
        manager.create_checkpoint(
            chapter_number=3, word_count=100, content="Ch3", state_snapshot={}
        )

        latest_ch1 = manager.get_latest_checkpoint(chapter_number=1)
        latest_ch2 = manager.get_latest_checkpoint(chapter_number=2)

        assert latest_ch1 is not None
        assert latest_ch1.chapter_number == 1
        assert latest_ch2 is not None
        assert latest_ch2.chapter_number == 2

    def test_get_latest_returns_none_when_empty(self, manager):
        latest = manager.get_latest_checkpoint()

        assert latest is None


class TestCheckpointManagerList:
    """Test listing checkpoints."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

    def test_list_checkpoints_empty(self, manager):
        checkpoints = manager.list_checkpoints()

        assert checkpoints == []

    def test_list_checkpoints_returns_all(self, manager):
        manager.create_checkpoint(chapter_number=1, word_count=0, content="C1", state_snapshot={})
        manager.create_checkpoint(chapter_number=1, word_count=500, content="C2", state_snapshot={})

        checkpoints = manager.list_checkpoints()

        assert len(checkpoints) == 2

    def test_list_checkpoints_filtered_by_chapter(self, manager):
        manager.create_checkpoint(chapter_number=1, word_count=0, content="C1", state_snapshot={})
        manager.create_checkpoint(chapter_number=2, word_count=0, content="C2", state_snapshot={})
        manager.create_checkpoint(chapter_number=1, word_count=500, content="C3", state_snapshot={})

        ch1_checkpoints = manager.list_checkpoints(chapter_number=1)
        ch2_checkpoints = manager.list_checkpoints(chapter_number=2)

        assert len(ch1_checkpoints) == 2
        assert len(ch2_checkpoints) == 1

    def test_list_checkpoints_includes_metadata(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=500, content="Test", state_snapshot={}
        )

        checkpoints = manager.list_checkpoints()

        assert len(checkpoints) == 1
        assert "checkpoint_id" in checkpoints[0]
        assert "chapter_number" in checkpoints[0]
        assert "word_count" in checkpoints[0]
        assert "size_bytes" in checkpoints[0]


class TestCheckpointManagerCleanup:
    """Test cleanup functionality."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(
            checkpoint_dir=tmp_path / "checkpoints",
            max_age_days=7,
        )

    def test_cleanup_removes_old_checkpoints(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=0, content="Recent", state_snapshot={}
        )

        old_checkpoint = Checkpoint(
            checkpoint_id="chapter1_words0_old",
            chapter_number=1,
            word_count=0,
            content="Old",
            state_snapshot={},
            created_at=datetime.now() - timedelta(days=10),
            checksum="old123",
        )

        old_path = manager.checkpoint_dir / "chapter1_words0_old.json"
        with open(old_path, "w", encoding="utf-8") as f:
            json.dump(old_checkpoint.to_dict(), f)

        removed = manager.cleanup_old_checkpoints()

        assert removed == 1
        assert not old_path.exists()
        assert manager.checkpoint_dir.exists()

    def test_cleanup_keeps_recent_checkpoints(self, manager):
        manager.create_checkpoint(
            chapter_number=1, word_count=0, content="Recent", state_snapshot={}
        )

        removed = manager.cleanup_old_checkpoints()

        assert removed == 0
        assert len(manager.list_checkpoints()) == 1

    def test_cleanup_returns_count(self, manager):
        for i in range(3):
            old_checkpoint = Checkpoint(
                checkpoint_id=f"chapter1_words{i*100}_old{i}",
                chapter_number=1,
                word_count=i * 100,
                content=f"Content {i}",
                state_snapshot={},
                created_at=datetime.now() - timedelta(days=10 + i),
                checksum=f"checksum_{i}",
            )
            old_path = manager.checkpoint_dir / f"chapter1_words{i*100}_old{i}.json"
            with open(old_path, "w", encoding="utf-8") as f:
                json.dump(old_checkpoint.to_dict(), f)

        removed = manager.cleanup_old_checkpoints()

        assert removed == 3


class TestCheckpointManagerDelete:
    """Test checkpoint deletion."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

    def test_delete_existing_checkpoint(self, manager):
        checkpoint = manager.create_checkpoint(
            chapter_number=1, word_count=0, content="To delete", state_snapshot={}
        )

        assert checkpoint is not None
        result = manager.delete_checkpoint(checkpoint.checkpoint_id)

        assert result is True
        assert manager.load_checkpoint(checkpoint.checkpoint_id) is None

    def test_delete_nonexistent_checkpoint(self, manager):
        result = manager.delete_checkpoint("nonexistent")

        assert result is False


class TestCheckpointManagerStats:
    """Test statistics functionality."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(checkpoint_dir=tmp_path / "checkpoints")

    def test_stats_empty(self, manager):
        stats = manager.get_stats()

        assert stats["total_checkpoints"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["chapters_with_checkpoints"] == 0

    def test_stats_with_checkpoints(self, manager):
        manager.create_checkpoint(chapter_number=1, word_count=0, content="Ch1", state_snapshot={})
        manager.create_checkpoint(chapter_number=2, word_count=0, content="Ch2", state_snapshot={})

        stats = manager.get_stats()

        assert stats["total_checkpoints"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["chapters_with_checkpoints"] == 2

    def test_stats_includes_size(self, manager):
        manager.create_checkpoint(
            chapter_number=1,
            word_count=0,
            content="A" * 1000,
            state_snapshot={"data": "x" * 100},
        )

        stats = manager.get_stats()

        assert stats["total_size_mb"] > 0


class TestCheckpointManagerLimit:
    """Test checkpoint limit enforcement."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(
            checkpoint_dir=tmp_path / "checkpoints",
            max_checkpoints_per_chapter=5,
        )

    def test_enforces_max_checkpoints_per_chapter(self, manager):
        for i in range(10):
            manager.create_checkpoint(
                chapter_number=1,
                word_count=i * 100,
                content=f"Content {i}",
                state_snapshot={},
            )

        checkpoints = manager.list_checkpoints(chapter_number=1)

        assert len(checkpoints) <= 5

    def test_keeps_most_recent_checkpoints(self, manager):
        for i in range(10):
            manager.create_checkpoint(
                chapter_number=1,
                word_count=i * 100,
                content=f"Content {i}",
                state_snapshot={},
            )

        checkpoints = manager.list_checkpoints(chapter_number=1)

        word_counts = [c["word_count"] for c in checkpoints]
        assert max(word_counts) >= 500


class TestFactoryFunction:
    """Test create_checkpoint_manager factory."""

    def test_factory_creates_manager(self, tmp_path):
        manager = create_checkpoint_manager(checkpoint_dir=tmp_path)

        assert isinstance(manager, CheckpointManager)
        assert manager.checkpoint_dir == tmp_path

    def test_factory_uses_default_path(self):
        manager = create_checkpoint_manager()

        assert isinstance(manager, CheckpointManager)
        assert "data" in str(manager.checkpoint_dir)
        assert "checkpoints" in str(manager.checkpoint_dir)


class TestCheckpointManagerIntegration:
    """Integration tests for checkpoint workflow."""

    @pytest.fixture
    def manager(self, tmp_path):
        return CheckpointManager(
            checkpoint_dir=tmp_path / "checkpoints",
            interval_words=100,
        )

    def test_chapter_generation_workflow(self, manager):
        chapter_num = 1
        content = ""
        state = {"chapter": 1, "events": []}

        for word_count in range(0, 501, 50):
            content += " " + ("word " * 50)
            state["events"].append(f"event_{word_count}")

            if manager.should_create_checkpoint(chapter_num, word_count):
                manager.create_checkpoint(
                    chapter_number=chapter_num,
                    word_count=word_count,
                    content=content,
                    state_snapshot=state,
                )

        checkpoints = manager.list_checkpoints(chapter_number=1)

        assert len(checkpoints) >= 5

    def test_recovery_from_checkpoint(self, manager):
        state = {"chapter": 1, "characters": ["Alice", "Bob"]}

        manager.create_checkpoint(
            chapter_number=1,
            word_count=500,
            content="Halfway through chapter 1",
            state_snapshot=state,
        )

        latest = manager.get_latest_checkpoint(chapter_number=1)

        assert latest is not None
        assert latest.content == "Halfway through chapter 1"
        assert latest.state_snapshot["characters"] == ["Alice", "Bob"]

    def test_multi_chapter_workflow(self, manager):
        for chapter in range(1, 4):
            for words in [0, 250, 500, 750]:
                if manager.should_create_checkpoint(chapter, words):
                    manager.create_checkpoint(
                        chapter_number=chapter,
                        word_count=words,
                        content=f"Chapter {chapter} at {words} words",
                        state_snapshot={"chapter": chapter},
                    )

        stats = manager.get_stats()

        assert stats["chapters_with_checkpoints"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
