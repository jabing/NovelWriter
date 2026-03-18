"""Transaction management for Knowledge Graph updates with version control.

Provides transactional semantics for KG updates, allowing atomic changes
with rollback capability and version tracking for the knowledge graph state.
"""

import logging
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TransactionState:
    """State of a KG transaction.

    Attributes:
        version: The version number at transaction start.
        in_transaction: Whether a transaction is currently active.
        snapshot: Deep copy of state at transaction start for rollback.
        changes: Changes to be applied on commit.
    """

    version: int = 0
    in_transaction: bool = False
    snapshot: dict[str, Any] = field(default_factory=dict)
    changes: dict[str, Any] = field(default_factory=dict)


class KGTransactionManager:
    """Manages transactional updates to Knowledge Graph with version control.

    This class provides ACID-like semantics for updating knowledge graph state:
    - Atomicity: Changes are applied all-or-nothing via commit/rollback
    - Consistency: Version tracking ensures state integrity
    - Isolation: Only one transaction can be active at a time

    Example:
        >>> manager = KGTransactionManager({"characters": []})
        >>> manager.begin_transaction()
        >>> # ... make changes ...
        >>> manager.commit()  # Version increments
        >>> manager.get_version()
        1
    """

    def __init__(self, initial_state: dict[str, Any] | None = None) -> None:
        """Initialize the transaction manager.

        Args:
            initial_state: Initial KG state. Defaults to empty dict if not provided.
        """
        self._state: dict[str, Any] = initial_state if initial_state is not None else {}
        self._transaction: TransactionState | None = None
        self._version: int = 0

    def get_version(self) -> int:
        """Return current KG version number.

        Version starts at 0 and increments on each successful commit.

        Returns:
            Current version number (non-negative integer).
        """
        return self._version

    def get_state(self) -> dict[str, Any]:
        """Return current KG state.

        Returns:
            Copy of the current state dictionary.
        """
        return self._state.copy()

    def begin_transaction(self) -> None:
        """Start a new transaction.

        Creates a snapshot of the current state for potential rollback.

        Raises:
            RuntimeError: If a transaction is already in progress.
        """
        if self._transaction is not None:
            raise RuntimeError("Transaction already in progress")

        self._transaction = TransactionState(
            version=self._version,
            snapshot=deepcopy(self._state),
            changes={},
        )
        self._transaction.in_transaction = True
        logger.debug(f"Transaction started at version {self._version}")

    def commit(self) -> None:
        """Commit the current transaction.

        Applies all pending changes to the state and increments the version.
        Clears the transaction after successful commit.

        Raises:
            RuntimeError: If no transaction is in progress.
        """
        if self._transaction is None:
            raise RuntimeError("No transaction in progress")

        # Apply changes to state
        self._state.update(self._transaction.changes)

        # Increment version
        self._version += 1

        logger.info(f"Transaction committed, new version: {self._version}")

        # Clear transaction
        self._transaction = None

    def rollback(self) -> None:
        """Rollback the current transaction.

        Restores the state to the snapshot taken at transaction start.
        Does not increment version.

        Raises:
            RuntimeError: If no transaction is in progress.
        """
        if self._transaction is None:
            raise RuntimeError("No transaction in progress")

        # Restore state from snapshot
        self._state = self._transaction.snapshot

        logger.warning(f"Transaction rolled back to version {self._transaction.version}")

        # Clear transaction
        self._transaction = None

    def update_with_transaction(
        self,
        updater: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> bool:
        """Execute an update operation within a transaction.

        This is a convenience method that wraps begin/commit/rollback
        into a single atomic operation.

        Args:
            updater: Function that takes the current state and returns
                    the updated state. The function should return a
                    dictionary with the changes to apply.

        Returns:
            True if transaction committed successfully, False if rolled back
            due to an exception.

        Example:
            >>> def add_character(state):
            ...     new_state = state.copy()
            ...     new_state["characters"] = new_state.get("characters", []) + ["Alice"]
            ...     return new_state
            >>> manager.update_with_transaction(add_character)
            True
        """
        self.begin_transaction()

        try:
            new_state = updater(self._state)
            # Store changes for commit
            if self._transaction is not None:
                self._transaction.changes = new_state
            self.commit()
            return True
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            self.rollback()
            return False

    def is_in_transaction(self) -> bool:
        """Check if a transaction is currently in progress.

        Returns:
            True if a transaction is active, False otherwise.
        """
        return self._transaction is not None and self._transaction.in_transaction

    def get_transaction_snapshot(self) -> dict[str, Any] | None:
        """Get the snapshot of the current transaction, if any.

        Returns:
            A copy of the transaction snapshot, or None if no transaction.
        """
        if self._transaction is None:
            return None
        return deepcopy(self._transaction.snapshot)


__all__ = [
    "TransactionState",
    "KGTransactionManager",
]
