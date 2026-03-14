"""Tests for RepairHistoryStore - persistent storage for repair history tracking."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.novel_agent.novel.auto_fixer import RepairAttempt, RepairHistory
from src.novel_agent.novel.repair_history import RepairHistoryStore


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_repair_attempt() -> RepairAttempt:
    """Create a sample repair attempt."""
    return RepairAttempt(
        attempt_number=1,
        timestamp=datetime.now().isoformat(),
        issues_before=[
            {"inconsistency_type": "location_mismatch", "severity": 3, "description": "Test issue"}
        ],
        issues_after=[],
        strategy_used="llm_regeneration",
        llm_prompt="Fix the issue",
        success=True,
    )


@pytest.fixture
def sample_repair_history(sample_repair_attempt: RepairAttempt) -> RepairHistory:
    """Create a sample repair history."""
    history = RepairHistory(
        chapter_number=1,
        started_at=datetime.now().isoformat(),
        validators_used=["ConsistencyVerifier"],
        total_issues_found=1,
    )
    history.add_attempt(sample_repair_attempt)
    history.final_status = "success"
    history.issues_fixed = 1
    history.completed_at = datetime.now().isoformat()
    return history


@pytest.fixture
def store(temp_dir: Path) -> RepairHistoryStore:
    """Create a store with temporary save path."""
    return RepairHistoryStore(
        save_path=str(temp_dir / "repair_history.json"),
        auto_save=False,
        backup_count=3,
    )


class TestRepairHistoryStoreAddHistory:
    """Tests for add_history method."""

    def test_add_single_history(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
    ) -> None:
        store.add_history(sample_repair_history)

        result = store.get_history(1)
        assert result is not None
        assert result.chapter_number == 1
        assert result.final_status == "success"

    def test_add_multiple_histories(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
    ) -> None:
        history2 = RepairHistory(
            chapter_number=2,
            started_at=datetime.now().isoformat(),
            final_status="partial",
        )

        store.add_history(sample_repair_history)
        store.add_history(history2)

        all_histories = store.get_all_histories()
        assert len(all_histories) == 2
        assert 1 in all_histories
        assert 2 in all_histories

    def test_add_replaces_existing(
        self,
        store: RepairHistoryStore,
    ) -> None:
        history1 = RepairHistory(
            chapter_number=1,
            started_at="2024-01-01T00:00:00",
            final_status="failed",
        )
        history2 = RepairHistory(
            chapter_number=1,
            started_at="2024-01-02T00:00:00",
            final_status="success",
        )

        store.add_history(history1)
        store.add_history(history2)

        result = store.get_history(1)
        assert result is not None
        assert result.final_status == "success"
        assert result.started_at == "2024-01-02T00:00:00"

    def test_add_enforces_max_stored_limit(self, temp_dir: Path) -> None:
        limited_store = RepairHistoryStore(
            max_stored=2,
            save_path=str(temp_dir / "limited.json"),
            auto_save=False,
        )

        for i in range(5):
            history = RepairHistory(
                chapter_number=i,
                started_at=f"2024-01-0{i}T00:00:00",
                final_status="success",
            )
            limited_store.add_history(history)

        all_histories = limited_store.get_all_histories()
        assert len(all_histories) == 2
        # Should keep the most recent ones (chapters 3 and 4)
        assert 0 not in all_histories
        assert 1 not in all_histories


class TestRepairHistoryStoreGetHistory:
    """Tests for get_history method."""

    def test_get_existing_history(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
    ) -> None:
        store.add_history(sample_repair_history)

        result = store.get_history(1)
        assert result is not None
        assert result.chapter_number == 1

    def test_get_nonexistent_history(self, store: RepairHistoryStore) -> None:
        result = store.get_history(999)
        assert result is None

    def test_get_all_histories_returns_copy(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
    ) -> None:
        store.add_history(sample_repair_history)

        all_histories = store.get_all_histories()
        all_histories[999] = RepairHistory(
            chapter_number=999,
            started_at="2024-01-01T00:00:00",
        )

        # Original store should not be affected
        result = store.get_history(999)
        assert result is None


class TestRepairHistoryStoreStatistics:
    """Tests for get_statistics method."""

    def test_empty_statistics(self, store: RepairHistoryStore) -> None:
        stats = store.get_statistics()

        assert stats["total_chapters"] == 0
        assert stats["total_attempts"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["fix_rate"] == 0.0

    def test_statistics_with_single_success(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
    ) -> None:
        store.add_history(sample_repair_history)

        stats = store.get_statistics()

        assert stats["total_chapters"] == 1
        assert stats["total_attempts"] == 1
        assert stats["successful_repairs"] == 1
        assert stats["success_rate"] == 1.0

    def test_statistics_with_multiple_statuses(self, store: RepairHistoryStore) -> None:
        histories = [
            RepairHistory(
                chapter_number=i,
                started_at=f"2024-01-0{i}T00:00:00",
                final_status=status,
                total_issues_found=5,
                issues_fixed=fixed,
                issues_remaining=remaining,
                validators_used=["ConsistencyVerifier", "TimelineValidator"],
            )
            for i, (status, fixed, remaining) in enumerate(
                [
                    ("success", 5, 0),
                    ("failed", 0, 5),
                    ("partial", 3, 2),
                    ("manual_review", 1, 4),
                ]
            )
        ]

        for history in histories:
            store.add_history(history)

        stats = store.get_statistics()

        assert stats["total_chapters"] == 4
        assert stats["successful_repairs"] == 1
        assert stats["failed_repairs"] == 1
        assert stats["partial_repairs"] == 1
        assert stats["manual_reviews"] == 1
        assert stats["success_rate"] == 0.25
        assert stats["total_issues_found"] == 20
        assert stats["total_issues_fixed"] == 9
        assert stats["total_issues_remaining"] == 11
        assert stats["fix_rate"] == 0.45

    def test_statistics_validator_usage(self, store: RepairHistoryStore) -> None:
        history1 = RepairHistory(
            chapter_number=1,
            started_at="2024-01-01T00:00:00",
            validators_used=["ConsistencyVerifier", "TimelineValidator"],
        )
        history2 = RepairHistory(
            chapter_number=2,
            started_at="2024-01-02T00:00:00",
            validators_used=["ConsistencyVerifier", "HallucinationDetector"],
        )

        store.add_history(history1)
        store.add_history(history2)

        stats = store.get_statistics()

        assert stats["validator_usage"]["ConsistencyVerifier"] == 2
        assert stats["validator_usage"]["TimelineValidator"] == 1
        assert stats["validator_usage"]["HallucinationDetector"] == 1


class TestRepairHistoryStoreSaveLoad:
    """Tests for save_to_file and load_from_file methods."""

    def test_save_and_load(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
        temp_dir: Path,
    ) -> None:
        store.add_history(sample_repair_history)
        save_path = str(temp_dir / "test_save.json")

        store.save_to_file(save_path)

        assert os.path.exists(save_path)

        new_store = RepairHistoryStore(save_path=save_path, auto_save=False)
        new_store.load_from_file(save_path)

        result = new_store.get_history(1)
        assert result is not None
        assert result.chapter_number == 1
        assert result.final_status == "success"

    def test_save_creates_directory(self, store: RepairHistoryStore, temp_dir: Path) -> None:
        nested_path = str(temp_dir / "nested" / "dir" / "history.json")
        history = RepairHistory(chapter_number=1, started_at="2024-01-01T00:00:00")
        store.add_history(history)

        store.save_to_file(nested_path)

        assert os.path.exists(nested_path)

    def test_save_file_format(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
        temp_dir: Path,
    ) -> None:
        store.add_history(sample_repair_history)
        save_path = str(temp_dir / "format_test.json")

        store.save_to_file(save_path)

        with open(save_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "version" in data
        assert "saved_at" in data
        assert "histories" in data
        assert "1" in data["histories"]

    def test_load_nonexistent_file(self, store: RepairHistoryStore, temp_dir: Path) -> None:
        load_path = str(temp_dir / "nonexistent.json")

        store.load_from_file(load_path)

        assert len(store.get_all_histories()) == 0

    def test_atomic_write(self, store: RepairHistoryStore, temp_dir: Path) -> None:
        save_path = str(temp_dir / "atomic_test.json")
        history = RepairHistory(chapter_number=1, started_at="2024-01-01T00:00:00")
        store.add_history(history)

        store.save_to_file(save_path)

        assert os.path.exists(save_path)
        temp_files = list(temp_dir.glob(".tmp_*"))
        assert len(temp_files) == 0


class TestRepairHistoryStoreBackup:
    """Tests for backup rotation."""

    def test_backup_rotation(self, temp_dir: Path) -> None:
        save_path = str(temp_dir / "backup_test.json")
        store = RepairHistoryStore(
            save_path=save_path,
            auto_save=True,
            backup_count=3,
        )

        for i in range(5):
            history = RepairHistory(
                chapter_number=i,
                started_at=f"2024-01-0{i}T00:00:00",
            )
            store.add_history(history)

        assert os.path.exists(save_path)
        assert os.path.exists(f"{save_path}.bak_1")
        assert os.path.exists(f"{save_path}.bak_2")
        assert os.path.exists(f"{save_path}.bak_3")
        assert not os.path.exists(f"{save_path}.bak_4")

    def test_backup_disabled(self, temp_dir: Path) -> None:
        save_path = str(temp_dir / "no_backup.json")
        store = RepairHistoryStore(
            save_path=save_path,
            auto_save=True,
            backup_count=0,
        )

        history = RepairHistory(chapter_number=1, started_at="2024-01-01T00:00:00")
        store.add_history(history)

        assert os.path.exists(save_path)
        assert not os.path.exists(f"{save_path}.bak_1")


class TestRepairHistoryStoreClear:
    """Tests for clear method."""

    def test_clear_removes_all_histories(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
    ) -> None:
        store.add_history(sample_repair_history)

        store.clear()

        assert len(store.get_all_histories()) == 0

    def test_clear_with_auto_save(self, temp_dir: Path) -> None:
        save_path = str(temp_dir / "clear_test.json")
        store = RepairHistoryStore(save_path=save_path, auto_save=True)

        history = RepairHistory(chapter_number=1, started_at="2024-01-01T00:00:00")
        store.add_history(history)

        store.clear()

        store.load_from_file()
        assert len(store.get_all_histories()) == 0


class TestRepairHistoryStoreChapterFilters:
    """Tests for chapter filtering methods."""

    @pytest.fixture
    def store_with_mixed_statuses(self, store: RepairHistoryStore) -> RepairHistoryStore:
        statuses = ["success", "failed", "partial", "manual_review", "success"]
        for i, status in enumerate(statuses):
            history = RepairHistory(
                chapter_number=i,
                started_at=f"2024-01-0{i}T00:00:00",
                final_status=status,
            )
            store.add_history(history)
        return store

    def test_get_failed_chapters(self, store_with_mixed_statuses: RepairHistoryStore) -> None:
        failed = store_with_mixed_statuses.get_failed_chapters()
        assert failed == [1]

    def test_get_successful_chapters(self, store_with_mixed_statuses: RepairHistoryStore) -> None:
        successful = store_with_mixed_statuses.get_successful_chapters()
        assert set(successful) == {0, 4}

    def test_get_manual_review_chapters(
        self,
        store_with_mixed_statuses: RepairHistoryStore,
    ) -> None:
        manual = store_with_mixed_statuses.get_manual_review_chapters()
        assert manual == [3]

    def test_get_chapters_by_status(
        self,
        store_with_mixed_statuses: RepairHistoryStore,
    ) -> None:
        partial = store_with_mixed_statuses.get_chapters_by_status("partial")
        assert partial == [2]


class TestRepairHistoryStoreExport:
    """Tests for export_summary method."""

    def test_export_summary(
        self,
        store: RepairHistoryStore,
        sample_repair_history: RepairHistory,
        temp_dir: Path,
    ) -> None:
        store.add_history(sample_repair_history)
        export_path = str(temp_dir / "summary.txt")

        store.export_summary(export_path)

        assert os.path.exists(export_path)
        with open(export_path, encoding="utf-8") as f:
            content = f.read()
        assert "REPAIR HISTORY SUMMARY" in content
        assert "Total Chapters: 1" in content

    def test_export_empty_summary(self, store: RepairHistoryStore, temp_dir: Path) -> None:
        export_path = str(temp_dir / "empty_summary.txt")

        store.export_summary(export_path)

        with open(export_path, encoding="utf-8") as f:
            content = f.read()
        assert "Total Chapters: 0" in content


class TestRepairHistoryStoreThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_adds(self, store: RepairHistoryStore) -> None:
        import threading

        errors: list[Exception] = []

        def add_history(chapter: int) -> None:
            try:
                history = RepairHistory(
                    chapter_number=chapter,
                    started_at=f"2024-01-{chapter:02d}T00:00:00",
                )
                store.add_history(history)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_history, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        all_histories = store.get_all_histories()
        assert len(all_histories) == 10


class TestRepairHistoryStoreEdgeCases:
    """Tests for edge cases."""

    def test_deserialize_history_with_missing_fields(self, temp_dir: Path) -> None:
        save_path = str(temp_dir / "minimal.json")
        minimal_data = {
            "version": "1.0",
            "histories": {"1": {"chapter_number": 1, "started_at": "2024-01-01T00:00:00"}},
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(minimal_data, f)

        store = RepairHistoryStore(save_path=save_path, auto_save=False)
        store.load_from_file()

        result = store.get_history(1)
        assert result is not None
        assert result.chapter_number == 1
        assert result.final_status == "in_progress"
        assert result.attempts == []

    def test_auto_save_flag(self, temp_dir: Path) -> None:
        save_path = str(temp_dir / "autosave.json")
        store = RepairHistoryStore(save_path=save_path, auto_save=True)

        history = RepairHistory(chapter_number=1, started_at="2024-01-01T00:00:00")
        store.add_history(history)

        assert os.path.exists(save_path)

    def test_max_stored_zero(self, temp_dir: Path) -> None:
        store = RepairHistoryStore(
            max_stored=0,
            save_path=str(temp_dir / "zero_limit.json"),
            auto_save=False,
        )

        history = RepairHistory(chapter_number=1, started_at="2024-01-01T00:00:00")
        store.add_history(history)

        # With max_stored=0, should still add first item
        result = store.get_history(1)
        assert result is not None
