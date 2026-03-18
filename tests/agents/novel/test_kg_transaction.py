"""Tests for KGTransactionManager class."""

from typing import Any

import pytest

from src.novel_agent.novel.kg_transaction import (
    KGTransactionManager,
    TransactionState,
)


class TestTransactionState:
    """Test TransactionState dataclass."""

    def test_default_initialization(self) -> None:
        """Test default initialization of TransactionState."""
        state = TransactionState()

        assert state.version == 0
        assert state.in_transaction is False
        assert state.snapshot == {}
        assert state.changes == {}

    def test_custom_initialization(self) -> None:
        """Test custom initialization of TransactionState."""
        state = TransactionState(
            version=5,
            in_transaction=True,
            snapshot={"key": "value"},
            changes={"key": "new_value"},
        )

        assert state.version == 5
        assert state.in_transaction is True
        assert state.snapshot == {"key": "value"}
        assert state.changes == {"key": "new_value"}


class TestKGTransactionManagerInit:
    """Test KGTransactionManager initialization."""

    def test_default_initialization(self) -> None:
        """Test initialization with no arguments."""
        manager = KGTransactionManager()

        assert manager.get_version() == 0
        assert manager.get_state() == {}
        assert manager.is_in_transaction() is False

    def test_initialization_with_state(self) -> None:
        """Test initialization with initial state."""
        initial_state = {"characters": ["Alice", "Bob"], "locations": ["Castle"]}
        manager = KGTransactionManager(initial_state)

        assert manager.get_version() == 0
        assert manager.get_state() == initial_state
        # Ensure state is a copy
        assert manager.get_state() is not initial_state

    def test_initialization_with_none(self) -> None:
        """Test initialization with None."""
        manager = KGTransactionManager(None)

        assert manager.get_version() == 0
        assert manager.get_state() == {}


class TestKGTransactionManagerBegin:
    """Test begin_transaction method."""

    def test_begin_transaction(self) -> None:
        """Test starting a transaction."""
        manager = KGTransactionManager({"key": "value"})

        manager.begin_transaction()

        assert manager.is_in_transaction() is True

    def test_begin_transaction_creates_snapshot(self) -> None:
        """Test that begin_transaction creates a snapshot."""
        initial_state = {"key": "value", "nested": {"a": 1}}
        manager = KGTransactionManager(initial_state)

        manager.begin_transaction()

        snapshot = manager.get_transaction_snapshot()
        assert snapshot == initial_state
        # Ensure it's a deep copy
        assert snapshot is not initial_state

    def test_cannot_start_nested_transaction(self) -> None:
        """Test that starting a nested transaction raises error."""
        manager = KGTransactionManager()
        manager.begin_transaction()

        with pytest.raises(RuntimeError, match="already in progress"):
            manager.begin_transaction()


class TestKGTransactionManagerCommit:
    """Test commit method."""

    @pytest.fixture
    def manager(self) -> KGTransactionManager:
        """Create a manager with initial state."""
        return KGTransactionManager({"key": "value"})

    def test_commit_increments_version(self, manager: KGTransactionManager) -> None:
        """Test that commit increments version."""
        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"key": "new_value"}
        manager.commit()

        assert manager.get_version() == 1

    def test_commit_applies_changes(self, manager: KGTransactionManager) -> None:
        """Test that commit applies pending changes."""
        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"key": "new_value", "new_key": "new_data"}
        manager.commit()

        assert manager.get_state()["key"] == "new_value"
        assert manager.get_state()["new_key"] == "new_data"

    def test_commit_clears_transaction(self, manager: KGTransactionManager) -> None:
        """Test that commit clears the transaction."""
        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"key": "updated"}
        manager.commit()

        assert manager.is_in_transaction() is False
        assert manager._transaction is None

    def test_cannot_commit_without_transaction(self) -> None:
        """Test that commit without transaction raises error."""
        manager = KGTransactionManager()

        with pytest.raises(RuntimeError, match="No transaction"):
            manager.commit()

    def test_multiple_commits_increment_version(self) -> None:
        """Test multiple commits increment version each time."""
        manager = KGTransactionManager({"count": 0})

        for i in range(1, 4):
            manager.begin_transaction()
            assert manager._transaction is not None
            manager._transaction.changes = {"count": i}
            manager.commit()
            assert manager.get_version() == i


class TestKGTransactionManagerRollback:
    """Test rollback method."""

    def test_rollback_does_not_increment_version(self) -> None:
        """Test that rollback does not increment version."""
        manager = KGTransactionManager({"key": "value"})

        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"key": "new_value"}
        manager.rollback()

        assert manager.get_version() == 0

    def test_rollback_restores_state(self) -> None:
        """Test that rollback restores original state."""
        original_state = {"key": "original", "nested": {"a": 1}}
        manager = KGTransactionManager(original_state)

        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"key": "modified", "nested": {"a": 2}}
        manager.rollback()

        assert manager.get_state() == original_state

    def test_rollback_clears_transaction(self) -> None:
        """Test that rollback clears the transaction."""
        manager = KGTransactionManager({"key": "value"})

        manager.begin_transaction()
        assert manager._transaction is not None
        manager.rollback()

        assert manager.is_in_transaction() is False
        assert manager._transaction is None

    def test_cannot_rollback_without_transaction(self) -> None:
        """Test that rollback without transaction raises error."""
        manager = KGTransactionManager()

        with pytest.raises(RuntimeError, match="No transaction"):
            manager.rollback()


class TestKGTransactionManagerUpdateWithTransaction:
    """Test update_with_transaction method."""

    def test_update_with_transaction_success(self) -> None:
        """Test successful update with transaction."""
        manager = KGTransactionManager({"count": 0})

        def increment(state: dict[str, Any]) -> dict[str, Any]:
            new_state = state.copy()
            new_state["count"] = state["count"] + 1
            return new_state

        result = manager.update_with_transaction(increment)

        assert result is True
        assert manager.get_state()["count"] == 1
        assert manager.get_version() == 1

    def test_update_with_transaction_failure(self) -> None:
        """Test update with transaction that raises exception."""
        manager = KGTransactionManager({"count": 0})

        def failing_update(state: dict[str, Any]) -> dict[str, Any]:
            raise ValueError("Update failed")

        result = manager.update_with_transaction(failing_update)

        assert result is False
        assert manager.get_state()["count"] == 0
        assert manager.get_version() == 0

    def test_update_with_transaction_preserves_state_on_failure(self) -> None:
        """Test that state is preserved when updater fails."""
        original_state: dict[str, Any] = {"items": ["a", "b"], "count": 2}
        manager = KGTransactionManager(original_state)

        def failing_update(state: dict[str, Any]) -> dict[str, Any]:
            # This change should not be applied
            return {"items": ["a", "b", "c"], "count": 3}

        # Manually fail after begin
        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"items": ["x"], "count": 999}
        manager.rollback()

        assert manager.get_state() == original_state

    def test_update_with_nested_state(self) -> None:
        """Test update with nested state structures."""
        manager = KGTransactionManager(
            {"characters": {"alice": {"status": "alive", "location": "home"}}}
        )

        def move_alice(state: dict[str, Any]) -> dict[str, Any]:
            new_state = state.copy()
            new_state["characters"] = {"alice": {"status": "alive", "location": "forest"}}
            return new_state

        result = manager.update_with_transaction(move_alice)

        assert result is True
        assert manager.get_state()["characters"]["alice"]["location"] == "forest"
        assert manager.get_version() == 1


class TestKGTransactionManagerIsInTransaction:
    """Test is_in_transaction method."""

    def test_not_in_transaction_initially(self) -> None:
        """Test that not in transaction initially."""
        manager = KGTransactionManager()

        assert manager.is_in_transaction() is False

    def test_in_transaction_after_begin(self) -> None:
        """Test in transaction after begin."""
        manager = KGTransactionManager()

        manager.begin_transaction()

        assert manager.is_in_transaction() is True

    def test_not_in_transaction_after_commit(self) -> None:
        """Test not in transaction after commit."""
        manager = KGTransactionManager({"key": "value"})

        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"key": "new"}
        manager.commit()

        assert manager.is_in_transaction() is False

    def test_not_in_transaction_after_rollback(self) -> None:
        """Test not in transaction after rollback."""
        manager = KGTransactionManager({"key": "value"})

        manager.begin_transaction()
        manager.rollback()

        assert manager.is_in_transaction() is False


class TestKGTransactionManagerGetTransactionSnapshot:
    """Test get_transaction_snapshot method."""

    def test_returns_none_without_transaction(self) -> None:
        """Test returns None when no transaction."""
        manager = KGTransactionManager()

        assert manager.get_transaction_snapshot() is None

    def test_returns_snapshot_during_transaction(self) -> None:
        """Test returns snapshot during active transaction."""
        initial_state = {"key": "value", "nested": {"a": 1}}
        manager = KGTransactionManager(initial_state)

        manager.begin_transaction()
        snapshot = manager.get_transaction_snapshot()

        assert snapshot == initial_state
        assert snapshot is not initial_state  # Should be a copy

    def test_snapshot_is_deep_copy(self) -> None:
        """Test that snapshot is a deep copy."""
        initial_state = {"nested": {"list": [1, 2, 3]}}
        manager = KGTransactionManager(initial_state)

        manager.begin_transaction()
        snapshot = manager.get_transaction_snapshot()

        assert snapshot is not None
        # Modify original state
        manager._state["nested"]["list"].append(4)

        # Snapshot should be unchanged
        assert snapshot["nested"]["list"] == [1, 2, 3]


class TestKGTransactionManagerGetState:
    """Test get_state method."""

    def test_returns_copy_of_state(self) -> None:
        """Test that get_state returns a copy."""
        manager = KGTransactionManager({"key": "value"})

        state1 = manager.get_state()
        state2 = manager.get_state()

        assert state1 == state2
        assert state1 is not state2  # Different objects

    def test_reflects_changes_after_commit(self) -> None:
        """Test that get_state reflects committed changes."""
        manager = KGTransactionManager({"key": "value"})

        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {"key": "updated", "new_key": "new_value"}
        manager.commit()

        state = manager.get_state()
        assert state["key"] == "updated"
        assert state["new_key"] == "new_value"


class TestKGTransactionManagerEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_multiple_transactions_sequence(self) -> None:
        """Test a sequence of multiple transactions."""
        manager = KGTransactionManager({"value": 0})

        # Transaction 1: success
        result1 = manager.update_with_transaction(lambda s: {"value": 1})
        assert result1 is True
        assert manager.get_version() == 1
        assert manager.get_state()["value"] == 1

        # Transaction 2: success
        result2 = manager.update_with_transaction(lambda s: {"value": 2})
        assert result2 is True
        assert manager.get_version() == 2
        assert manager.get_state()["value"] == 2

        # Transaction 3: failure
        result3 = manager.update_with_transaction(lambda s: (_ for _ in ()).throw(ValueError()))
        assert result3 is False
        assert manager.get_version() == 2  # Unchanged
        assert manager.get_state()["value"] == 2  # Unchanged

    def test_empty_changes_commit(self) -> None:
        """Test commit with empty changes."""
        manager = KGTransactionManager({"key": "value"})

        manager.begin_transaction()
        assert manager._transaction is not None
        manager._transaction.changes = {}  # Empty changes
        manager.commit()

        assert manager.get_version() == 1
        assert manager.get_state() == {"key": "value"}

    def test_updater_can_read_state(self) -> None:
        """Test that updater function can read current state."""
        manager = KGTransactionManager({"base": 10, "multiplier": 2})

        def compute(state: dict[str, Any]) -> dict[str, Any]:
            result = state["base"] * state["multiplier"]
            return {"base": state["base"], "multiplier": state["multiplier"], "result": result}

        manager.update_with_transaction(compute)

        assert manager.get_state()["result"] == 20

    def test_updater_replaces_state(self) -> None:
        """Test that updater's return value updates (replaces keys) in state."""
        manager = KGTransactionManager({"a": 1, "b": 2})

        def add_c(state: dict) -> dict:
            return {"c": 3}

        manager.update_with_transaction(add_c)

        # update() replaces keys, so 'a' and 'b' should still exist
        # but 'c' should be added
        state = manager.get_state()
        assert state["a"] == 1
        assert state["b"] == 2
        assert state["c"] == 3
