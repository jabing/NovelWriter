# src/studio/core/settings.py
"""Settings management for Writer Studio.

Provides configurable parameters for content generation pipeline,
including iteration counts, quality thresholds, and preset modes.

Usage:
    from src.novel_agent.studio.core.settings import get_settings_manager

    manager = get_settings_manager()
    settings = manager.get_settings()

    # Apply preset mode
    manager.apply_preset('fast')  # Quick generation

    # Or update individual settings
    manager.update_settings(iterations=3)
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Preset modes for different use cases
QUALITY_PRESETS: dict[str, dict[str, Any]] = {
    "fast": {
        "iterations": 1,
        "approval_threshold": 7.0,
        "auto_revise_threshold": 5.0,
        "enable_learning": False,
        "description": "快速生成模式 - 适合测试和低质量故事",
    },
    "balanced": {
        "iterations": 3,
        "approval_threshold": 8.0,
        "auto_revise_threshold": 6.0,
        "enable_learning": True,
        "description": "平衡模式 - 速度与质量兼顾",
    },
    "high": {
        "iterations": 5,
        "approval_threshold": 9.0,
        "auto_revise_threshold": 7.0,
        "enable_learning": True,
        "description": "高质量模式 - 多次迭代确保质量",
    },
    "ultra": {
        "iterations": 10,
        "approval_threshold": 9.5,
        "auto_revise_threshold": 8.0,
        "enable_learning": True,
        "description": "极致质量模式 - 最多次迭代",
    },
}


@dataclass
class StudioSettings:
    """Studio settings for content generation.

    Attributes:
        iterations: Maximum revision iterations (1-10)
        approval_threshold: Minimum score for approval (7.0-10.0)
        auto_revise_threshold: Minimum score for auto-revision (5.0-9.0)
        enable_learning: Enable learning modules for adaptive content
        quality_mode: Current quality mode preset (fast/balanced/high/ultra)
    """

    iterations: int = 5
    approval_threshold: float = 9.0
    auto_revise_threshold: float = 7.0
    enable_learning: bool = True
    quality_mode: str = "balanced"
    ui_language: str = "en"  # "en" or "zh"
    author_name: str = "AI Writer"  # Author name for exports

    def validate(self) -> None:
        """Validate settings are within acceptable ranges.

        Raises:
            ValueError: If any setting is out of range
        """
        errors: list[str] = []

        # Check iterations
        if not (1 <= self.iterations <= 10):
            errors.append(f"iterations must be 1-10, got {self.iterations}")

        # Check approval_threshold
        if not (7.0 <= self.approval_threshold <= 10.0):
            errors.append(f"approval_threshold must be 7.0-10.0, got {self.approval_threshold}")

        # Check auto_revise_threshold
        if not (5.0 <= self.auto_revise_threshold <= 9.0):
            errors.append(
                f"auto_revise_threshold must be 5.0-9.0, got {self.auto_revise_threshold}"
            )

        # Check auto_revise < approval
        if self.auto_revise_threshold >= self.approval_threshold:
            errors.append(
                f"auto_revise_threshold ({self.auto_revise_threshold}) must be < "
                f"approval_threshold ({self.approval_threshold})"
            )

        # Check quality_mode
        valid_modes = list(QUALITY_PRESETS.keys())
        if self.quality_mode not in valid_modes:
            errors.append(f"quality_mode must be one of {valid_modes}, got {self.quality_mode}")

        if errors:
            raise ValueError("\n".join(errors))

    def apply_preset(self, mode: str) -> str:
        """Apply a preset quality mode.

        Args:
            mode: Preset mode name (fast/balanced/high/ultra)

        Returns:
            Description of the applied mode

        Raises:
            ValueError: If mode is not recognized
        """
        if mode not in QUALITY_PRESETS:
            valid = list(QUALITY_PRESETS.keys())
            raise ValueError(f"Unknown mode '{mode}'. Valid modes: {valid}")

        preset = QUALITY_PRESETS[mode]
        self.iterations = preset["iterations"]
        self.approval_threshold = preset["approval_threshold"]
        self.auto_revise_threshold = preset["auto_revise_threshold"]
        self.enable_learning = preset["enable_learning"]
        self.quality_mode = mode

        return preset["description"]

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "iterations": self.iterations,
            "approval_threshold": self.approval_threshold,
            "auto_revise_threshold": self.auto_revise_threshold,
            "enable_learning": self.enable_learning,
            "quality_mode": self.quality_mode,
            "ui_language": self.ui_language,
            "author_name": self.author_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StudioSettings":
        """Create settings from dictionary.

        Args:
            data: Dictionary with settings values

        Returns:
            StudioSettings instance
        """
        return cls(
            iterations=data.get("iterations", 5),
            approval_threshold=data.get("approval_threshold", 9.0),
            auto_revise_threshold=data.get("auto_revise_threshold", 7.0),
            enable_learning=data.get("enable_learning", True),
            quality_mode=data.get("quality_mode", "balanced"),
            ui_language=data.get("ui_language", "en"),
            author_name=data.get("author_name", "AI Writer"),
        )


class SettingsManager:
    """Manager for studio settings with persistence.

    Handles loading, saving, and updating settings with automatic
    persistence to a JSON file.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize settings manager.

        Args:
            data_dir: Directory to store settings file
        """
        self.data_dir = data_dir or Path("data/studio")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._settings = self._load_settings()

    def _settings_file(self) -> Path:
        """Get settings file path."""
        return self.data_dir / "settings.json"

    def _load_settings(self) -> StudioSettings:
        """Load settings from disk.

        Returns:
            StudioSettings instance (defaults if file not found)
        """
        settings_file = self._settings_file()

        if settings_file.exists():
            try:
                with open(settings_file, encoding="utf-8") as f:
                    data = json.load(f)
                settings = StudioSettings.from_dict(data)
                logger.info(f"Loaded settings from {settings_file}")
                return settings
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}. Using defaults.")

        return StudioSettings()

    def _save_settings(self) -> None:
        """Save settings to disk."""
        settings_file = self._settings_file()

        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings.to_dict(), f, indent=2)
            logger.info(f"Saved settings to {settings_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get_settings(self) -> StudioSettings:
        """Get current settings.

        Returns:
            Current StudioSettings instance
        """
        return self._settings

    def update_settings(self, **kwargs: Any) -> StudioSettings:
        """Update settings and save.

        Args:
            **kwargs: Settings to update

        Returns:
            Updated StudioSettings instance

        Raises:
            ValueError: If any setting is invalid
        """
        # Map of parameter names to aliases (for natural language support)
        aliases = {
            "iter": "iterations",
            "iteration": "iterations",
            "max_iterations": "iterations",
            "threshold": "approval_threshold",
            "approval": "approval_threshold",
            "revise_threshold": "auto_revise_threshold",
            "auto_revise": "auto_revise_threshold",
            "learning": "enable_learning",
        }

        # Apply aliases
        resolved: dict[str, Any] = {}
        for key, value in kwargs.items():
            resolved_key = aliases.get(key, key)
            resolved[resolved_key] = value

        # Update settings
        for key, value in resolved.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
            else:
                logger.warning(f"Unknown setting: {key}")

        # Validate
        self._settings.validate()

        # Save
        self._save_settings()

        logger.info(f"Updated settings: {resolved}")
        return self._settings

    def apply_preset(self, mode: str) -> str:
        """Apply a preset quality mode and save.

        Args:
            mode: Preset mode name (fast/balanced/high/ultra)

        Returns:
            Description of the applied mode
        """
        description = self._settings.apply_preset(mode)
        self._save_settings()
        logger.info(f"Applied preset mode: {mode}")
        return description

    def get_available_presets(self) -> dict[str, dict[str, Any]]:
        """Get all available preset modes.

        Returns:
            Dictionary of preset names to their configurations
        """
        return QUALITY_PRESETS.copy()

    def reset_to_defaults(self) -> StudioSettings:
        """Reset settings to defaults.

        Returns:
            Reset StudioSettings instance
        """
        self._settings = StudioSettings()
        self._save_settings()
        logger.info("Reset settings to defaults")
        return self._settings


# Global settings manager instance
_settings_manager: SettingsManager | None = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager.

    Returns:
        SettingsManager singleton instance
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_settings() -> StudioSettings:
    """Convenience function to get current settings.

    Returns:
        Current StudioSettings instance
    """
    return get_settings_manager().get_settings()
