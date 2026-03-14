"""Tests for NLP state change detection."""

import re

from src.novel_agent.novel.continuity import ContinuityManager, StateChange


class TestStateDetection:
    """Test NLP state detection."""

    def test_patterns_initialized(self):
        """Test patterns are initialized."""
        manager = ContinuityManager()
        assert hasattr(manager, "_death_patterns")
        assert hasattr(manager, "_fusion_patterns")
        assert hasattr(manager, "_capture_patterns")
        assert hasattr(manager, "_location_patterns")
        assert all(isinstance(p, re.Pattern) for p in manager._death_patterns)

    def test_death_detection(self):
        """Test death detection."""
        manager = ContinuityManager()
        changes = manager._detect_state_changes("Kael died in battle.")
        assert len(changes) > 0
        assert any(c.new_state == "dead" for c in changes)

    def test_fusion_detection(self):
        """Test fusion detection."""
        manager = ContinuityManager()
        changes = manager._detect_state_changes("Aurelion fused with Kael.")
        assert len(changes) > 0
        fusion = [c for c in changes if c.new_state == "fused"]
        assert len(fusion) > 0

    def test_capture_detection(self):
        """Test capture detection."""
        manager = ContinuityManager()
        changes = manager._detect_state_changes("Lyra was captured.")
        assert len(changes) > 0
        assert any(c.new_state == "captured" for c in changes)

    def test_multiple_changes(self):
        """Test multiple changes in one content."""
        manager = ContinuityManager()
        content = "Kael died. Aurelion fused with Lyra. Sylas was captured."
        changes = manager._detect_state_changes(content)
        assert len(changes) >= 3

    def test_no_changes(self):
        """Test no changes detected."""
        manager = ContinuityManager()
        changes = manager._detect_state_changes("Kael walked through the forest.")
        assert len(changes) == 0

    def test_empty_content(self):
        """Test empty content."""
        manager = ContinuityManager()
        changes = manager._detect_state_changes("")
        assert changes == []

    def test_state_change_dataclass(self):
        """Test StateChange dataclass."""
        change = StateChange(
            character="Kael",
            old_state="alive",
            new_state="dead",
            evidence="Kael died."
        )
        assert change.character == "Kael"
        assert change.old_state == "alive"
        assert change.new_state == "dead"
