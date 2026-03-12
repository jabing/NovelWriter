# src/novel/recovery/__init__.py
"""Error recovery components for robust generation."""

from src.novel.recovery.degradation import (
    DegradationConfig,
    DegradationLevel,
    GracefulDegradation,
)
from src.novel.recovery.retry_handler import (
    RetryConfig,
    RetryHandler,
    RetryResult,
)
from src.novel.recovery.rollback import (
    RollbackManager,
    RollbackPoint,
)
from src.novel.recovery.state_checkpoint import (
    GenerationState,
    StateCheckpointManager,
)

__all__ = [
    "RetryConfig",
    "RetryHandler",
    "RetryResult",
    "DegradationConfig",
    "DegradationLevel",
    "GracefulDegradation",
    "GenerationState",
    "StateCheckpointManager",
    "RollbackManager",
    "RollbackPoint",
]
