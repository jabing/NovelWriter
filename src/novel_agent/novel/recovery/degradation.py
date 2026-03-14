"""Graceful degradation system for handling system stress.

This module provides graceful degradation capabilities that allow the
generation system to continue operating under stress by trading quality
for availability.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DegradationLevel(str, Enum):
    """Levels of degradation for graceful fallback.

    Each level represents a trade-off between quality and availability:
    - FULL: Normal operation, all features enabled
    - REDUCED: Fewer iterations, lower thresholds, reduced features
    - MINIMAL: Basic generation only, minimal validation
    - EMERGENCY: Skeleton content with placeholders
    """

    FULL_QUALITY = "full"
    REDUCED_QUALITY = "reduced"
    MINIMAL_QUALITY = "minimal"
    EMERGENCY = "emergency"


@dataclass
class DegradationConfig:
    """Configuration for a degradation level.

    Attributes:
        level: The degradation level
        max_iterations: Maximum generation iterations
        quality_threshold: Minimum quality score threshold
        enable_learning: Whether learning modules are active
        enable_market_research: Whether market research is used
        token_budget: Maximum tokens for context
        enable_reference_validation: Whether to validate references
        enable_cross_chapter_checks: Whether cross-chapter validation is active
    """

    level: DegradationLevel
    max_iterations: int
    quality_threshold: float
    enable_learning: bool
    enable_market_research: bool
    token_budget: int
    enable_reference_validation: bool = True
    enable_cross_chapter_checks: bool = True


# Default configurations for each degradation level
DEGRADATION_CONFIGS: dict[DegradationLevel, DegradationConfig] = {
    DegradationLevel.FULL_QUALITY: DegradationConfig(
        level=DegradationLevel.FULL_QUALITY,
        max_iterations=5,
        quality_threshold=9.0,
        enable_learning=True,
        enable_market_research=True,
        token_budget=16000,
        enable_reference_validation=True,
        enable_cross_chapter_checks=True,
    ),
    DegradationLevel.REDUCED_QUALITY: DegradationConfig(
        level=DegradationLevel.REDUCED_QUALITY,
        max_iterations=3,
        quality_threshold=7.5,
        enable_learning=True,
        enable_market_research=False,
        token_budget=12000,
        enable_reference_validation=True,
        enable_cross_chapter_checks=False,
    ),
    DegradationLevel.MINIMAL_QUALITY: DegradationConfig(
        level=DegradationLevel.MINIMAL_QUALITY,
        max_iterations=2,
        quality_threshold=6.0,
        enable_learning=False,
        enable_market_research=False,
        token_budget=8000,
        enable_reference_validation=False,
        enable_cross_chapter_checks=False,
    ),
    DegradationLevel.EMERGENCY: DegradationConfig(
        level=DegradationLevel.EMERGENCY,
        max_iterations=1,
        quality_threshold=5.0,
        enable_learning=False,
        enable_market_research=False,
        token_budget=4000,
        enable_reference_validation=False,
        enable_cross_chapter_checks=False,
    ),
}


class GracefulDegradation:
    """Manages graceful degradation of generation quality.

    This class monitors system health and automatically adjusts
    generation parameters to maintain availability under stress.

    Degradation triggers:
    - High failure rate (>30%)
    - Rate limiting from LLM API
    - Timeout patterns
    - Memory pressure

    Recovery triggers:
    - Consecutive successful generations
    - Reduced error rate
    - Manual reset

    Example:
        >>> degradation = GracefulDegradation()
        >>> config = degradation.get_config()
        >>> # Use config.max_iterations, config.quality_threshold, etc.

        >>> # On failure:
        >>> new_level = degradation.record_failure("rate_limit")
        >>> if new_level != DegradationLevel.FULL_QUALITY:
        ...     logger.warning(f"Degraded to {new_level.value}")
    """

    # Thresholds for degradation and recovery
    DEGRADATION_FAILURE_RATE = 0.3  # 30% failure rate triggers degradation
    RECOVERY_SUCCESS_COUNT = 5  # 5 consecutive successes trigger recovery
    DEGRADATION_WINDOW_SIZE = 10  # Look at last 10 operations

    def __init__(
        self,
        custom_configs: dict[DegradationLevel, DegradationConfig] | None = None,
    ):
        """Initialize the degradation manager.

        Args:
            custom_configs: Optional custom configurations per level
        """
        self.configs = custom_configs or DEGRADATION_CONFIGS
        self.current_level = DegradationLevel.FULL_QUALITY

        # Tracking counters
        self.failure_count = 0
        self.success_count = 0
        self.consecutive_successes = 0

        # History for rate calculation
        self._recent_results: list[bool] = []  # True = success, False = failure

        # Degradation history
        self._degradation_events: list[dict[str, Any]] = []

        logger.info("GracefulDegradation initialized at FULL_QUALITY level")

    @property
    def level(self) -> DegradationLevel:
        """Current degradation level."""
        return self.current_level

    def get_config(self) -> DegradationConfig:
        """Get current degradation configuration.

        Returns:
            DegradationConfig for current level
        """
        return self.configs[self.current_level]

    def record_failure(self, error_type: str) -> DegradationLevel:
        """Record a failure and potentially degrade.

        Args:
            error_type: Type of error that occurred

        Returns:
            New degradation level (may be same as before)
        """
        self.failure_count += 1
        self.consecutive_successes = 0
        self._recent_results.append(False)

        # Trim history
        if len(self._recent_results) > self.DEGRADATION_WINDOW_SIZE:
            self._recent_results = self._recent_results[-self.DEGRADATION_WINDOW_SIZE :]

        # Calculate failure rate
        failure_rate = self._calculate_failure_rate()

        # Check for degradation
        if failure_rate > self.DEGRADATION_FAILURE_RATE:
            new_level = self._degrade(error_type)
            if new_level != self.current_level:
                return new_level

        # Immediate degradation for certain error types
        if (
            error_type in ("rate_limit", "service_unavailable")
            and self.current_level == DegradationLevel.FULL_QUALITY
        ):
            return self._degrade(error_type)

        return self.current_level

    def record_success(self) -> DegradationLevel:
        """Record a success and potentially recover.

        Returns:
            New degradation level (may be same as before)
        """
        self.success_count += 1
        self.consecutive_successes += 1
        self._recent_results.append(True)

        # Trim history
        if len(self._recent_results) > self.DEGRADATION_WINDOW_SIZE:
            self._recent_results = self._recent_results[-self.DEGRADATION_WINDOW_SIZE :]

        # Check for recovery
        if (
            self.consecutive_successes >= self.RECOVERY_SUCCESS_COUNT
            and self.current_level != DegradationLevel.FULL_QUALITY
        ):
            return self._recover()

        return self.current_level

    def force_degrade(self, reason: str) -> DegradationLevel:
        """Force degradation to next level.

        Args:
            reason: Reason for forced degradation

        Returns:
            New degradation level
        """
        return self._degrade(reason)

    def force_recover(self, reason: str) -> DegradationLevel:
        """Force recovery to previous level.

        Args:
            reason: Reason for forced recovery

        Returns:
            New degradation level
        """
        return self._recover(reason)

    def reset(self) -> None:
        """Reset to full quality and clear counters."""
        self.current_level = DegradationLevel.FULL_QUALITY
        self.failure_count = 0
        self.success_count = 0
        self.consecutive_successes = 0
        self._recent_results.clear()
        logger.info("GracefulDegradation reset to FULL_QUALITY")

    def get_stats(self) -> dict[str, Any]:
        """Get degradation statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "current_level": self.current_level.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "consecutive_successes": self.consecutive_successes,
            "failure_rate": self._calculate_failure_rate(),
            "degradation_events": len(self._degradation_events),
        }

    def _calculate_failure_rate(self) -> float:
        """Calculate recent failure rate.

        Returns:
            Failure rate (0.0 - 1.0)
        """
        if not self._recent_results:
            return 0.0

        failures = sum(1 for r in self._recent_results if not r)
        return failures / len(self._recent_results)

    def _degrade(self, reason: str) -> DegradationLevel:
        """Move to next degradation level.

        Args:
            reason: Reason for degradation

        Returns:
            New degradation level
        """
        levels = list(DegradationLevel)
        current_idx = levels.index(self.current_level)

        if current_idx < len(levels) - 1:
            old_level = self.current_level
            self.current_level = levels[current_idx + 1]

            # Reset success counter
            self.consecutive_successes = 0

            # Record event
            self._degradation_events.append(
                {
                    "type": "degrade",
                    "from_level": old_level.value,
                    "to_level": self.current_level.value,
                    "reason": reason,
                }
            )

            logger.warning(
                f"Degraded from {old_level.value} to {self.current_level.value}: {reason}"
            )

            return self.current_level

        return self.current_level

    def _recover(self, reason: str = "consecutive successes") -> DegradationLevel:
        """Move to previous degradation level.

        Args:
            reason: Reason for recovery

        Returns:
            New degradation level
        """
        levels = list(DegradationLevel)
        current_idx = levels.index(self.current_level)

        if current_idx > 0:
            old_level = self.current_level
            self.current_level = levels[current_idx - 1]

            # Reset success counter
            self.consecutive_successes = 0

            # Record event
            self._degradation_events.append(
                {
                    "type": "recover",
                    "from_level": old_level.value,
                    "to_level": self.current_level.value,
                    "reason": reason,
                }
            )

            logger.info(f"Recovered from {old_level.value} to {self.current_level.value}: {reason}")

            return self.current_level

        return self.current_level
