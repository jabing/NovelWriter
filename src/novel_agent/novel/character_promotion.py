"""Character tier promotion and demotion system.

This module provides the CharacterPromotion class for managing character
tier transitions based on appearance frequency and plot involvement.

Tiers (importance hierarchy):
- Tier 0 (核心主角): Most important - complete persona with full cognitive graph
- Tier 1 (重要配角): Important supporting - detailed persona with full cognitive graph
- Tier 2 (普通配角): Regular supporting - simplified persona with partial cognitive graph
- Tier 3 (社会公众): Background/Extras - minimal persona with no cognitive graph

Promotion: Tier 3 → 2 → 1 → 0 (increasing importance)
Demotion: Tier 0 → 1 → 2 → 3 (decreasing importance)

Usage:
    from src.novel_agent.novel.character_promotion import CharacterPromotion

    cp = CharacterPromotion()

    # Check if should promote
    should_promote = cp.check_promotion(
        character_data={"id": "char1", "tier": 2},
        chapter_appearances=6,
        plot_involvement=True
    )

    # Promote character
    result = cp.promote("char1", from_tier=2, to_tier=1)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.novel_agent.novel.tier_template import TierTemplate

logger = logging.getLogger(__name__)


# === Promotion Rules ===
# Conditions for promoting a character to a higher importance tier
# Promotion: Tier 3 → 2 → 1 → 0 (tier number decreases = more important)
PROMOTION_RULES: dict[tuple[int, int], dict[str, Any]] = {
    # Tier 3 → 2: Character appears 3+ times with dialogue
    (3, 2): {
        "min_appearances": 3,
        "min_dialogues": 2,
        "description": "社会公众 → 普通配角: 出场3次以上，对话2次以上",
    },
    # Tier 2 → 1: Character appears 5+ times with significant plot involvement
    (2, 1): {
        "min_appearances": 5,
        "min_plot_involvement": 1,
        "description": "普通配角 → 重要配角: 出场5次以上，参与重要剧情",
    },
    # Tier 1 → 0: Character becomes central to plot, appears 10+ times
    (1, 0): {
        "min_appearances": 10,
        "plot_central": True,
        "description": "重要配角 → 核心主角: 出场10次以上，核心剧情人物",
    },
}


# === Demotion Rules ===
# Conditions for demoting a character to a lower importance tier
# Demotion: Tier 0 → 1 → 2 → 3 (tier number increases = less important)
DEMOTION_RULES: dict[tuple[int, int], dict[str, Any]] = {
    # Tier 0 → 1: Character absent for 5+ chapters
    (0, 1): {
        "absent_chapters": 5,
        "description": "核心主角 → 重要配角: 连续缺席5章以上",
    },
    # Tier 1 → 2: Character absent for 3+ chapters
    (1, 2): {
        "absent_chapters": 3,
        "description": "重要配角 → 普通配角: 连续缺席3章以上",
    },
    # Tier 2 → 3: Character absent for 2+ chapters
    (2, 3): {
        "absent_chapters": 2,
        "description": "普通配角 → 社会公众: 连续缺席2章以上",
    },
}


class TransitionType(str, Enum):
    """Types of tier transitions."""

    PROMOTION = "promotion"  # Tier number decreases (more important)
    DEMOTION = "demotion"  # Tier number increases (less important)
    INVALID = "invalid"  # Invalid transition (e.g., skip tier)


@dataclass
class TierTransition:
    """Records a tier transition event.

    Attributes:
        character_id: Unique identifier for the character
        from_tier: Original tier
        to_tier: New tier
        transition_type: Type of transition (promotion/demotion)
        reason: Reason for the transition
        timestamp: When the transition occurred
        metadata: Additional metadata about the transition
    """

    character_id: str
    from_tier: int
    to_tier: int
    transition_type: TransitionType
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Determine transition type based on tier change."""
        # Auto-detect transition type based on tier change direction
        # Promotion: tier number decreases (3→2→1→0)
        if self.to_tier < self.from_tier:
            self.transition_type = TransitionType.PROMOTION
        # Demotion: tier number increases (0→1→2→3)
        elif self.to_tier > self.from_tier:
            self.transition_type = TransitionType.DEMOTION
        else:
            self.transition_type = TransitionType.INVALID

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "character_id": self.character_id,
            "from_tier": self.from_tier,
            "to_tier": self.to_tier,
            "transition_type": self.transition_type.value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TierTransition:
        """Create from dictionary."""
        timestamp = datetime.now()
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"])
            except (ValueError, TypeError):
                pass

        return cls(
            character_id=data["character_id"],
            from_tier=data["from_tier"],
            to_tier=data["to_tier"],
            transition_type=TransitionType(data.get("transition_type", "invalid")),
            reason=data.get("reason", ""),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
        )


@dataclass
class PromotionCheckResult:
    """Result of a promotion check.

    Attributes:
        can_promote: Whether the character can be promoted
        current_tier: Current tier of the character
        target_tier: Target tier for promotion
        missing_requirements: List of unmet requirements
        met_requirements: List of met requirements
        reason: Explanation of the result
    """

    can_promote: bool
    current_tier: int
    target_tier: int | None
    missing_requirements: list[str] = field(default_factory=list)
    met_requirements: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class DemotionCheckResult:
    """Result of a demotion check.

    Attributes:
        should_demote: Whether the character should be demoted
        current_tier: Current tier of the character
        target_tier: Target tier for demotion
        reason: Explanation of the result
    """

    should_demote: bool
    current_tier: int
    target_tier: int | None
    reason: str = ""


class CharacterPromotion:
    """Manages character tier promotion and demotion.

    This class provides methods to:
    - Check if a character should be promoted or demoted
    - Execute tier transitions
    - Track transition history
    - Apply template switches when tier changes

    Attributes:
        promotion_rules: Rules for promoting characters
        demotion_rules: Rules for demoting characters
        transition_history: List of all recorded transitions
    """

    def __init__(self) -> None:
        """Initialize the CharacterPromotion system."""
        self._promotion_rules = PROMOTION_RULES
        self._demotion_rules = DEMOTION_RULES
        self._transition_history: list[TierTransition] = []
        self._tier_template = TierTemplate()

        logger.info("CharacterPromotion initialized")

    def get_promotion_rules(self) -> dict[tuple[int, int], dict[str, Any]]:
        """Get all promotion rules.

        Returns:
            Dictionary mapping (from_tier, to_tier) to rule requirements.
        """
        return self._promotion_rules.copy()

    def get_demotion_rules(self) -> dict[tuple[int, int], dict[str, Any]]:
        """Get all demotion rules.

        Returns:
            Dictionary mapping (from_tier, to_tier) to rule requirements.
        """
        return self._demotion_rules.copy()

    def get_transition_rules(self) -> dict[str, dict[tuple[int, int], dict[str, Any]]]:
        """Get all transition rules (promotion and demotion).

        Returns:
            Dictionary with 'promotion' and 'demotion' keys, each containing
            the respective rules.
        """
        return {
            "promotion": self.get_promotion_rules(),
            "demotion": self.get_demotion_rules(),
        }

    def check_promotion(
        self,
        character_data: dict[str, Any],
        chapter_appearances: int,
        dialogue_count: int = 0,
        plot_involvement: bool = False,
        plot_central: bool = False,
    ) -> PromotionCheckResult:
        """Check if a character should be promoted.

        Promotion is moving from higher tier number to lower (3→2→1→0).

        Args:
            character_data: Character data dictionary, must contain 'tier' key
            chapter_appearances: Number of chapters the character has appeared in
            dialogue_count: Number of dialogues the character has had
            plot_involvement: Whether the character has significant plot involvement
            plot_central: Whether the character is central to the plot

        Returns:
            PromotionCheckResult with promotion eligibility and details.
        """
        current_tier = character_data.get("tier", 3)

        # Tier 0 characters cannot be promoted further
        if current_tier == 0:
            return PromotionCheckResult(
                can_promote=False,
                current_tier=current_tier,
                target_tier=None,
                reason="Tier 0 (核心主角) is the highest tier, cannot promote further",
            )

        target_tier = current_tier - 1
        rule_key = (current_tier, target_tier)

        # Check if there's a valid promotion rule
        if rule_key not in self._promotion_rules:
            return PromotionCheckResult(
                can_promote=False,
                current_tier=current_tier,
                target_tier=None,
                reason=f"No promotion rule from tier {current_tier} to tier {target_tier}",
            )

        rule = self._promotion_rules[rule_key]
        missing: list[str] = []
        met: list[str] = []

        # Check min_appearances requirement
        min_appearances = rule.get("min_appearances", 0)
        if chapter_appearances >= min_appearances:
            met.append(f"出场次数: {chapter_appearances}/{min_appearances}")
        else:
            missing.append(f"出场次数不足: {chapter_appearances}/{min_appearances}")

        # Check min_dialogues requirement
        min_dialogues = rule.get("min_dialogues", 0)
        if min_dialogues > 0:
            if dialogue_count >= min_dialogues:
                met.append(f"对话次数: {dialogue_count}/{min_dialogues}")
            else:
                missing.append(f"对话次数不足: {dialogue_count}/{min_dialogues}")

        # Check plot_involvement requirement
        if rule.get("min_plot_involvement"):
            if plot_involvement:
                met.append("参与重要剧情: 是")
            else:
                missing.append("未参与重要剧情")

        # Check plot_central requirement
        if rule.get("plot_central"):
            if plot_central:
                met.append("核心剧情人物: 是")
            else:
                missing.append("非核心剧情人物")

        can_promote = len(missing) == 0
        reason = rule.get("description", "")

        return PromotionCheckResult(
            can_promote=can_promote,
            current_tier=current_tier,
            target_tier=target_tier if can_promote else None,
            missing_requirements=missing,
            met_requirements=met,
            reason=reason if can_promote else f"未满足晋升条件: {', '.join(missing)}",
        )

    def check_demotion(
        self,
        character_data: dict[str, Any],
        chapter_absence: int,
    ) -> DemotionCheckResult:
        """Check if a character should be demoted.

        Demotion is moving from lower tier number to higher (0→1→2→3).

        Args:
            character_data: Character data dictionary, must contain 'tier' key
            chapter_absence: Number of consecutive chapters the character has been absent

        Returns:
            DemotionCheckResult with demotion recommendation and details.
        """
        current_tier = character_data.get("tier", 3)

        # Tier 3 characters cannot be demoted further
        if current_tier == 3:
            return DemotionCheckResult(
                should_demote=False,
                current_tier=current_tier,
                target_tier=None,
                reason="Tier 3 (社会公众) is the lowest tier, cannot demote further",
            )

        target_tier = current_tier + 1
        rule_key = (current_tier, target_tier)

        # Check if there's a valid demotion rule
        if rule_key not in self._demotion_rules:
            return DemotionCheckResult(
                should_demote=False,
                current_tier=current_tier,
                target_tier=None,
                reason=f"No demotion rule from tier {current_tier} to tier {target_tier}",
            )

        rule = self._demotion_rules[rule_key]
        required_absence = rule.get("absent_chapters", 0)

        should_demote = chapter_absence >= required_absence
        reason = rule.get("description", "")

        return DemotionCheckResult(
            should_demote=should_demote,
            current_tier=current_tier,
            target_tier=target_tier if should_demote else None,
            reason=reason
            if should_demote
            else f"缺席章节数不足: {chapter_absence}/{required_absence}",
        )

    def promote(
        self,
        character_id: str,
        from_tier: int,
        to_tier: int,
        reason: str = "",
    ) -> dict[str, Any]:
        """Promote a character to a higher importance tier.

        Args:
            character_id: Unique identifier for the character
            from_tier: Current tier of the character
            to_tier: Target tier (must be lower number than from_tier)
            reason: Reason for the promotion

        Returns:
            Dictionary with success status, transition details, and any errors.

        Raises:
            ValueError: If the transition is invalid (e.g., skip tier, wrong direction)
        """
        # Validate tier range
        if not 0 <= from_tier <= 3:
            raise ValueError(f"Invalid from_tier: {from_tier}. Must be 0-3.")
        if not 0 <= to_tier <= 3:
            raise ValueError(f"Invalid to_tier: {to_tier}. Must be 0-3.")

        # Validate promotion direction
        if to_tier >= from_tier:
            raise ValueError(
                f"Promotion requires to_tier < from_tier. "
                f"Got to_tier={to_tier}, from_tier={from_tier}"
            )

        # Validate single-tier promotion (no skipping)
        if to_tier != from_tier - 1:
            raise ValueError(
                f"Cannot skip tiers. Promotion must be from tier {from_tier} to "
                f"tier {from_tier - 1}, not to tier {to_tier}"
            )

        # Check if promotion rule exists
        rule_key = (from_tier, to_tier)
        if rule_key not in self._promotion_rules:
            raise ValueError(
                f"No promotion rule defined for transition {from_tier} → {to_tier}"
            )

        # Create transition record
        transition = TierTransition(
            character_id=character_id,
            from_tier=from_tier,
            to_tier=to_tier,
            transition_type=TransitionType.PROMOTION,
            reason=reason or self._promotion_rules[rule_key].get("description", ""),
            metadata={"rule": self._promotion_rules[rule_key]},
        )

        # Record transition
        self._transition_history.append(transition)
        logger.info(f"Promoted character {character_id}: tier {from_tier} → {to_tier}")

        # Apply template switch
        template_result = self.apply_template_switch(character_id, to_tier)

        return {
            "success": True,
            "character_id": character_id,
            "from_tier": from_tier,
            "to_tier": to_tier,
            "transition": transition.to_dict(),
            "template_switch": template_result,
        }

    def demote(
        self,
        character_id: str,
        from_tier: int,
        to_tier: int,
        reason: str = "",
    ) -> dict[str, Any]:
        """Demote a character to a lower importance tier.

        Args:
            character_id: Unique identifier for the character
            from_tier: Current tier of the character
            to_tier: Target tier (must be higher number than from_tier)
            reason: Reason for the demotion

        Returns:
            Dictionary with success status, transition details, and any errors.

        Raises:
            ValueError: If the transition is invalid (e.g., skip tier, wrong direction)
        """
        # Validate tier range
        if not 0 <= from_tier <= 3:
            raise ValueError(f"Invalid from_tier: {from_tier}. Must be 0-3.")
        if not 0 <= to_tier <= 3:
            raise ValueError(f"Invalid to_tier: {to_tier}. Must be 0-3.")

        # Validate demotion direction
        if to_tier <= from_tier:
            raise ValueError(
                f"Demotion requires to_tier > from_tier. "
                f"Got to_tier={to_tier}, from_tier={from_tier}"
            )

        # Validate single-tier demotion (no skipping)
        if to_tier != from_tier + 1:
            raise ValueError(
                f"Cannot skip tiers. Demotion must be from tier {from_tier} to "
                f"tier {from_tier + 1}, not to tier {to_tier}"
            )

        # Check if demotion rule exists
        rule_key = (from_tier, to_tier)
        if rule_key not in self._demotion_rules:
            raise ValueError(
                f"No demotion rule defined for transition {from_tier} → {to_tier}"
            )

        # Create transition record
        transition = TierTransition(
            character_id=character_id,
            from_tier=from_tier,
            to_tier=to_tier,
            transition_type=TransitionType.DEMOTION,
            reason=reason or self._demotion_rules[rule_key].get("description", ""),
            metadata={"rule": self._demotion_rules[rule_key]},
        )

        # Record transition
        self._transition_history.append(transition)
        logger.info(f"Demoted character {character_id}: tier {from_tier} → {to_tier}")

        # Apply template switch
        template_result = self.apply_template_switch(character_id, to_tier)

        return {
            "success": True,
            "character_id": character_id,
            "from_tier": from_tier,
            "to_tier": to_tier,
            "transition": transition.to_dict(),
            "template_switch": template_result,
        }

    def apply_template_switch(
        self,
        character_id: str,
        new_tier: int,
    ) -> dict[str, Any]:
        """Apply a new tier template to a character.

        This method returns template information for the new tier.
        The actual data migration should be handled by the caller.

        Args:
            character_id: Unique identifier for the character
            new_tier: The new tier to apply

        Returns:
            Dictionary with template information for the new tier.
        """
        try:
            template = self._tier_template.get_template(new_tier)

            return {
                "success": True,
                "character_id": character_id,
                "new_tier": new_tier,
                "template": template,
                "required_fields": self._tier_template.get_required_fields(new_tier),
                "optional_fields": self._tier_template.get_optional_fields(new_tier),
                "token_budget": self._tier_template.get_token_budget(new_tier),
                "has_cognitive_graph": self._tier_template.has_cognitive_graph(new_tier),
            }
        except Exception as e:
            logger.error(f"Failed to apply template switch for {character_id}: {e}")
            return {
                "success": False,
                "character_id": character_id,
                "new_tier": new_tier,
                "error": str(e),
            }

    def get_transition_history(
        self,
        character_id: str | None = None,
        limit: int = 100,
    ) -> list[TierTransition]:
        """Get transition history for a character or all characters.

        Args:
            character_id: Optional character ID to filter by
            limit: Maximum number of records to return

        Returns:
            List of TierTransition records, most recent first.
        """
        history = self._transition_history

        if character_id:
            history = [t for t in history if t.character_id == character_id]

        # Sort by timestamp (most recent first) and limit
        history = sorted(history, key=lambda t: t.timestamp, reverse=True)
        return history[:limit]

    def get_character_tier_history(
        self,
        character_id: str,
    ) -> list[dict[str, Any]]:
        """Get the complete tier history for a specific character.

        Args:
            character_id: Unique identifier for the character

        Returns:
            List of transition dictionaries for the character.
        """
        history = [
            t.to_dict()
            for t in self._transition_history
            if t.character_id == character_id
        ]
        return sorted(history, key=lambda t: t["timestamp"])

    def clear_history(self) -> int:
        """Clear all transition history.

        Returns:
            Number of records cleared.
        """
        count = len(self._transition_history)
        self._transition_history.clear()
        logger.info(f"Cleared {count} transition history records")
        return count

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about tier transitions.

        Returns:
            Dictionary with transition statistics.
        """
        total = len(self._transition_history)
        promotions = sum(
            1 for t in self._transition_history if t.transition_type == TransitionType.PROMOTION
        )
        demotions = sum(
            1 for t in self._transition_history if t.transition_type == TransitionType.DEMOTION
        )

        # Group by character
        character_counts: dict[str, int] = {}
        for t in self._transition_history:
            character_counts[t.character_id] = character_counts.get(t.character_id, 0) + 1

        return {
            "total_transitions": total,
            "promotions": promotions,
            "demotions": demotions,
            "unique_characters": len(character_counts),
            "characters_with_multiple_transitions": sum(1 for c in character_counts.values() if c > 1),
        }


__all__ = [
    "CharacterPromotion",
    "TierTransition",
    "TransitionType",
    "PromotionCheckResult",
    "DemotionCheckResult",
    "PROMOTION_RULES",
    "DEMOTION_RULES",
]
