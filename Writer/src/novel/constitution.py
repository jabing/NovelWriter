# src/novel/constitution.py
"""Constitutional rule system for AI novel writing.

Immutable writing rules that all agents must follow to prevent hallucinations
and ensure consistency across million-word novels.

These rules are organized by domain (character, plot, world, style) and
provide both positive guidelines ("must") and negative prohibitions ("must not").
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RuleSeverity(str, Enum):
    """Severity level of a constitutional rule."""

    CRITICAL = "critical"  # Must never be violated
    HIGH = "high"  # Should not be violated without justification
    MEDIUM = "medium"  # Important but can be flexible
    LOW = "low"  # Recommended best practice


class RuleDomain(str, Enum):
    """Domain of a constitutional rule."""

    CHARACTER = "character"
    PLOT = "plot"
    WORLD = "world"
    STYLE = "style"
    CONSISTENCY = "consistency"
    ETHICAL = "ethical"


@dataclass
class ConstitutionalRule:
    """A single constitutional rule with validation logic."""

    id: str
    domain: RuleDomain
    severity: RuleSeverity
    description: str
    positive_guideline: str  # What MUST be done
    negative_prohibition: str  # What MUST NOT be done
    validator: Callable[[Any], tuple[bool, str]] | None = None  # Returns (is_valid, error_message)

    def validate(self, data: Any) -> tuple[bool, str]:
        """Validate data against this rule.

        Args:
            data: Data to validate (type depends on domain)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.validator:
            return self.validator(data)
        # Default validation passes
        return True, ""


# ============================================================================
# Character Rules
# ============================================================================

CHARACTER_RULES = [
    ConstitutionalRule(
        id="CHAR-001",
        domain=RuleDomain.CHARACTER,
        severity=RuleSeverity.CRITICAL,
        description="Character consistency",
        positive_guideline="Characters must maintain consistent personality traits, values, and motivations across the entire story",
        negative_prohibition="Characters must not suddenly change core personality traits without proper development or justification",
        validator=lambda data: _validate_character_consistency(data),
    ),
    ConstitutionalRule(
        id="CHAR-002",
        domain=RuleDomain.CHARACTER,
        severity=RuleSeverity.HIGH,
        description="Character development",
        positive_guideline="Character growth must be gradual, believable, and tied to story events",
        negative_prohibition="Characters must not achieve major growth without facing proportional challenges",
        validator=lambda data: _validate_character_development(data),
    ),
    ConstitutionalRule(
        id="CHAR-003",
        domain=RuleDomain.CHARACTER,
        severity=RuleSeverity.CRITICAL,
        description="Character voice consistency",
        positive_guideline="Each character must have a distinct, consistent voice (speech patterns, vocabulary, mannerisms)",
        negative_prohibition="Characters must not use vocabulary or speech patterns inconsistent with their background, education, or personality",
        validator=lambda data: _validate_character_voice(data),
    ),
    ConstitutionalRule(
        id="CHAR-004",
        domain=RuleDomain.CHARACTER,
        severity=RuleSeverity.HIGH,
        description="Character relationships",
        positive_guideline="Character relationships must evolve believably based on shared experiences and interactions",
        negative_prohibition="Characters must not form deep bonds or bitter enmities without sufficient interaction and justification",
        validator=lambda data: _validate_character_relationships(data),
    ),
]

# ============================================================================
# Plot Rules
# ============================================================================

PLOT_RULES = [
    ConstitutionalRule(
        id="PLOT-001",
        domain=RuleDomain.PLOT,
        severity=RuleSeverity.CRITICAL,
        description="Plot hole prevention",
        positive_guideline="Plot must be internally consistent with no unexplained contradictions",
        negative_prohibition="Plot must not contain holes where events contradict established facts without explanation",
        validator=lambda data: _validate_plot_holes(data),
    ),
    ConstitutionalRule(
        id="PLOT-002",
        domain=RuleDomain.PLOT,
        severity=RuleSeverity.HIGH,
        description="Foreshadowing payoff",
        positive_guideline="Significant plot developments must be properly foreshadowed",
        negative_prohibition="Major plot twists must not come completely out of nowhere without any setup",
        validator=lambda data: _validate_foreshadowing(data),
    ),
    ConstitutionalRule(
        id="PLOT-003",
        domain=RuleDomain.PLOT,
        severity=RuleSeverity.MEDIUM,
        description="Pacing consistency",
        positive_guideline="Pacing must match genre expectations and story needs",
        negative_prohibition="Pacing must not wildly fluctuate without narrative justification",
        validator=lambda data: _validate_pacing(data),
    ),
    ConstitutionalRule(
        id="PLOT-004",
        domain=RuleDomain.PLOT,
        severity=RuleSeverity.CRITICAL,
        description="Stakes maintenance",
        positive_guideline="Stakes must be clear, meaningful, and maintained throughout the story",
        negative_prohibition="Stakes must not be forgotten, trivialized, or resolved without consequence",
        validator=lambda data: _validate_stakes(data),
    ),
]

# ============================================================================
# World Rules
# ============================================================================

WORLD_RULES = [
    ConstitutionalRule(
        id="WORLD-001",
        domain=RuleDomain.WORLD,
        severity=RuleSeverity.CRITICAL,
        description="World rule consistency",
        positive_guideline="World rules (magic, technology, physics) must be consistent and predictable",
        negative_prohibition="World rules must not change arbitrarily to solve plot problems",
        validator=lambda data: _validate_world_rules(data),
    ),
    ConstitutionalRule(
        id="WORLD-002",
        domain=RuleDomain.WORLD,
        severity=RuleSeverity.HIGH,
        description="Cultural consistency",
        positive_guideline="Cultures, societies, and institutions must behave consistently with their established norms",
        negative_prohibition="Cultures must not act contrary to established values without explanation",
        validator=lambda data: _validate_cultural_consistency(data),
    ),
    ConstitutionalRule(
        id="WORLD-003",
        domain=RuleDomain.WORLD,
        severity=RuleSeverity.MEDIUM,
        description="Geographical consistency",
        positive_guideline="Geography, travel times, and locations must remain consistent",
        negative_prohibition="Locations must not change physical attributes without explanation",
        validator=lambda data: _validate_geography(data),
    ),
    ConstitutionalRule(
        id="WORLD-004",
        domain=RuleDomain.WORLD,
        severity=RuleSeverity.CRITICAL,
        description="Magic/technology limitations",
        positive_guideline="Magic/technology systems must have clear costs, limitations, and consequences",
        negative_prohibition="Magic/technology must not be used as a deus ex machina without established rules",
        validator=lambda data: _validate_system_limitations(data),
    ),
]

# ============================================================================
# Style Rules
# ============================================================================

STYLE_RULES = [
    ConstitutionalRule(
        id="STYLE-001",
        domain=RuleDomain.STYLE,
        severity=RuleSeverity.MEDIUM,
        description="Point of view consistency",
        positive_guideline="Point of view must remain consistent within scenes",
        negative_prohibition="Point of view must not head-hop within a single scene without clear transitions",
        validator=lambda data: _validate_pov(data),
    ),
    ConstitutionalRule(
        id="STYLE-002",
        domain=RuleDomain.STYLE,
        severity=RuleSeverity.LOW,
        description="Show don't tell",
        positive_guideline="Important character traits and emotions should be shown through actions and dialogue",
        negative_prohibition="Character traits should not be repeatedly stated without demonstration",
        validator=lambda data: _validate_show_dont_tell(data),
    ),
    ConstitutionalRule(
        id="STYLE-003",
        domain=RuleDomain.STYLE,
        severity=RuleSeverity.MEDIUM,
        description="Tone consistency",
        positive_guideline="Tone must remain consistent with genre and story type",
        negative_prohibition="Tone must not shift wildly without narrative justification",
        validator=lambda data: _validate_tone(data),
    ),
]

# ============================================================================
# Consistency Rules
# ============================================================================

CONSISTENCY_RULES = [
    ConstitutionalRule(
        id="CONS-001",
        domain=RuleDomain.CONSISTENCY,
        severity=RuleSeverity.CRITICAL,
        description="Timeline consistency",
        positive_guideline="Timeline of events must be internally consistent",
        negative_prohibition="Events must not occur in impossible temporal sequences",
        validator=lambda data: _validate_timeline(data),
    ),
    ConstitutionalRule(
        id="CONS-002",
        domain=RuleDomain.CONSISTENCY,
        severity=RuleSeverity.HIGH,
        description="Continuity of objects and possessions",
        positive_guideline="Character possessions, injuries, and physical states must be tracked consistently",
        negative_prohibition="Objects must not appear or disappear without explanation",
        validator=lambda data: _validate_object_continuity(data),
    ),
    ConstitutionalRule(
        id="CONS-003",
        domain=RuleDomain.CONSISTENCY,
        severity=RuleSeverity.MEDIUM,
        description="Character knowledge consistency",
        positive_guideline="Character knowledge must be consistent with their experiences and access to information",
        negative_prohibition="Characters must not know things they haven't learned or couldn't reasonably deduce",
        validator=lambda data: _validate_character_knowledge(data),
    ),
]

# ============================================================================
# Ethical Rules
# ============================================================================

ETHICAL_RULES = [
    ConstitutionalRule(
        id="ETHIC-001",
        domain=RuleDomain.ETHICAL,
        severity=RuleSeverity.CRITICAL,
        description="Respect for human dignity",
        positive_guideline="All characters must be treated with basic human dignity regardless of role",
        negative_prohibition="Characters must not be subjected to gratuitous violence, exploitation, or degradation without narrative purpose",
        validator=lambda data: _validate_human_dignity(data),
    ),
    ConstitutionalRule(
        id="ETHIC-002",
        domain=RuleDomain.ETHICAL,
        severity=RuleSeverity.HIGH,
        description="Avoidance of harmful stereotypes",
        positive_guideline="Characters must be multifaceted individuals, not reducible to stereotypes",
        negative_prohibition="Characters must not be defined primarily by demographic stereotypes",
        validator=lambda data: _validate_stereotypes(data),
    ),
]

# ============================================================================
# All Rules Combined
# ============================================================================

ALL_RULES = (
    CHARACTER_RULES + PLOT_RULES + WORLD_RULES + STYLE_RULES + CONSISTENCY_RULES + ETHICAL_RULES
)

# Rule domain mapping for easy access
RULES_BY_DOMAIN = {
    RuleDomain.CHARACTER: CHARACTER_RULES,
    RuleDomain.PLOT: PLOT_RULES,
    RuleDomain.WORLD: WORLD_RULES,
    RuleDomain.STYLE: STYLE_RULES,
    RuleDomain.CONSISTENCY: CONSISTENCY_RULES,
    RuleDomain.ETHICAL: ETHICAL_RULES,
}

# Rule severity mapping
RULES_BY_SEVERITY = {
    RuleSeverity.CRITICAL: [r for r in ALL_RULES if r.severity == RuleSeverity.CRITICAL],
    RuleSeverity.HIGH: [r for r in ALL_RULES if r.severity == RuleSeverity.HIGH],
    RuleSeverity.MEDIUM: [r for r in ALL_RULES if r.severity == RuleSeverity.MEDIUM],
    RuleSeverity.LOW: [r for r in ALL_RULES if r.severity == RuleSeverity.LOW],
}


# ============================================================================
# Validation Functions (Stubs - to be implemented with actual logic)
# ============================================================================


def _validate_character_consistency(data: Any) -> tuple[bool, str]:
    """Validate character consistency rule."""
    # Expected data format:
    # {
    #   'character_profile': dict with character traits, appearance, etc.
    #   'current_content': str - text to validate
    #   'previous_content': list[str] - optional previous chapters
    # }
    if not isinstance(data, dict):
        return True, "No character data to validate"

    character_profile = data.get("character_profile", {})
    current_content = data.get("current_content", "")

    if not character_profile or not current_content:
        return True, "Insufficient data for character consistency validation"

    # Check appearance consistency
    appearance = character_profile.get("appearance", {})
    issues = []

    # Example: Check if eye color is consistent
    if "eye_color" in appearance:
        eye_color = appearance["eye_color"].lower()
        # Simple check: see if eye color is mentioned differently
        if eye_color and eye_color not in current_content.lower():
            # Eye color not mentioned - not necessarily an error
            pass

    # Check personality traits consistency
    personality = character_profile.get("personality", {})
    traits = personality.get("traits", [])
    for trait in traits:
        if isinstance(trait, str):
            # Check if trait is contradicted
            # This is a simple implementation - could be enhanced
            contradicting_words = {
                "brave": ["cowardly", "timid", "fearful"],
                "honest": ["deceptive", "liar", "dishonest"],
                "kind": ["cruel", "mean", "ruthless"],
                "intelligent": ["foolish", "stupid", "ignorant"],
            }
            if trait in contradicting_words:
                for contradicting in contradicting_words[trait]:
                    if contradicting in current_content.lower():
                        issues.append(
                            f"Character trait '{trait}' contradicted by '{contradicting}' in text"
                        )

    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_character_development(data: Any) -> tuple[bool, str]:
    """Validate character development rule."""
    # Expected data format:
    # {
    #   'character_profile': dict with character traits, development arc, etc.
    #   'current_content': str - text to validate
    #   'previous_content': list[str] - optional previous chapters
    # }
    if not isinstance(data, dict):
        return True, "No character data to validate"

    character_profile = data.get("character_profile", {})
    current_content = data.get("current_content", "")

    if not character_profile or not current_content:
        return True, "Insufficient data for character development validation"

    # Check for sudden character changes without justification
    sudden_change_keywords = ["suddenly", "abruptly", "out of nowhere", "without reason"]
    justification_keywords = ["because", "due to", "after", "as a result", "therefore", "since"]

    issues = []

    for keyword in sudden_change_keywords:
        if keyword in current_content.lower():
            # Check if there's a justification nearby (within ~50 chars)
            lower_content = current_content.lower()
            idx = lower_content.find(keyword)
            if idx != -1:
                # Look for justification in a window around the keyword
                window_start = max(0, idx - 100)
                window_end = min(len(lower_content), idx + 100)
                window = lower_content[window_start:window_end]
                has_justification = any(just in window for just in justification_keywords)
                if not has_justification:
                    issues.append(
                        f"Sudden character change '{keyword}' without clear justification"
                    )

    # Check for character growth keywords that are positive
    growth_keywords = ["learned", "realized", "understood", "grew", "developed", "changed"]
    for keyword in growth_keywords:
        if keyword in current_content.lower():
            # This is good, but we could check if growth is tied to story events
            # For now, just note positive growth
            pass

    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_character_voice(data: Any) -> tuple[bool, str]:
    """Validate character voice consistency."""
    # Expected data format:
    # {
    #   'character_profile': dict with speech patterns, background, vocabulary, etc.
    #   'current_content': str - text to validate
    #   'previous_content': list[str] - optional previous chapters
    # }
    if not isinstance(data, dict):
        return True, "No character data to validate"

    character_profile = data.get("character_profile", {})
    current_content = data.get("current_content", "")

    if not character_profile or not current_content:
        return True, "Insufficient data for character voice validation"

    issues = []

    # Check background-appropriate vocabulary
    background = character_profile.get("background", "").lower()
    if background:
        sophisticated_words = [
            "therefore",
            "consequently",
            "notwithstanding",
            "however",
            "furthermore",
        ]
        rustic_words = ["ain't", "gonna", "wanna", "y'all", "reckon"]

        if background in ["educated", "noble", "scholar"]:
            for word in rustic_words:
                if word in current_content.lower():
                    issues.append(
                        f"Character with {background} background uses rustic word '{word}'"
                    )
        elif background in ["rustic", "peasant", "uneducated"]:
            for word in sophisticated_words:
                if word in current_content.lower():
                    issues.append(
                        f"Character with {background} background uses sophisticated word '{word}'"
                    )

    # Check speech patterns consistency
    speech_patterns = character_profile.get("speech_patterns", [])
    if isinstance(speech_patterns, list):
        for pattern in speech_patterns:
            if isinstance(pattern, str):
                # Check if pattern appears in content
                if pattern.lower() in current_content.lower():
                    # Pattern present - good
                    pass
                else:
                    # Pattern missing - not necessarily an error
                    pass

    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_character_relationships(data: Any) -> tuple[bool, str]:
    """Validate character relationships."""
    # Expected data format:
    # {
    #   'character_profile': dict with relationships, interaction history, etc.
    #   'current_content': str - text to validate
    #   'previous_content': list[str] - optional previous chapters
    # }
    if not isinstance(data, dict):
        return True, "No character data to validate"

    character_profile = data.get("character_profile", {})
    current_content = data.get("current_content", "")

    if not character_profile or not current_content:
        return True, "Insufficient data for character relationships validation"

    issues = []

    # Extract relationships from profile
    relationships = character_profile.get("relationships", {})
    if isinstance(relationships, dict):
        for other_char, relation in relationships.items():
            if not isinstance(relation, str):
                continue
            relation_lower = relation.lower()
            # Check for contradictions in current content
            if relation_lower in ["hate", "enemy", "rival"]:
                positive_words = ["love", "friend", "ally", "help", "save", "protect"]
                for word in positive_words:
                    if word in current_content.lower():
                        # Check if the other character is mentioned near this word
                        # Simple check: if other_char appears in same sentence
                        # For now, just flag potential contradiction
                        issues.append(
                            f"Character has '{relation}' relationship with {other_char} but positive interaction '{word}' appears"
                        )
            elif relation_lower in ["love", "friend", "ally"]:
                negative_words = ["hate", "enemy", "betray", "attack", "kill"]
                for word in negative_words:
                    if word in current_content.lower():
                        issues.append(
                            f"Character has '{relation}' relationship with {other_char} but negative interaction '{word}' appears"
                        )

    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_plot_holes(data: Any) -> tuple[bool, str]:
    """Validate plot hole prevention."""
    # Expected data format:
    # {
    #   'plot_elements': list of dicts with plot information
    #   'current_content': str - text to validate
    #   'established_facts': dict - established world facts
    # }
    if not isinstance(data, dict):
        return True, "No plot data to validate"

    plot_elements = data.get("plot_elements", [])
    current_content = data.get("current_content", "")
    established_facts = data.get("established_facts", {})

    if not current_content:
        return True, "No content to validate for plot holes"

    issues = []

    # Check for contradictions with established facts
    for fact_key, fact_value in established_facts.items():
        if isinstance(fact_value, str):
            # Look for statements that contradict established facts
            # Simple keyword-based contradiction detection
            contradicting_patterns = {
                "alive": ["dead", "died", "killed"],
                "dead": ["alive", "living", "survived"],
                "present": ["absent", "missing", "gone"],
                "absent": ["present", "arrived", "appeared"],
                "day": ["night", "midnight", "evening"],
                "night": ["day", "morning", "noon"],
            }
            if fact_key in contradicting_patterns:
                for contradicting in contradicting_patterns[fact_key]:
                    if contradicting in current_content.lower():
                        # Check if this is a direct contradiction
                        # This is a simplistic check - could be enhanced with NLP
                        issues.append(
                            f"Established fact '{fact_key}: {fact_value}' contradicted by '{contradicting}' in text"
                        )

    # Check plot element consistency
    for element in plot_elements:
        if isinstance(element, dict):
            element_name = element.get("name", "")
            element_status = element.get("status", "")
            if element_status == "resolved" and element_name:
                # If plot element is resolved, it shouldn't be presented as ongoing
                ongoing_indicators = ["still", "ongoing", "continues", "unresolved"]
                for indicator in ongoing_indicators:
                    if (
                        indicator in current_content.lower()
                        and element_name.lower() in current_content.lower()
                    ):
                        issues.append(
                            f"Resolved plot element '{element_name}' presented as ongoing"
                        )

    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_foreshadowing(data: Any) -> tuple[bool, str]:
    """Validate foreshadowing payoff.

    Expected data format (example):
    {
      'foreshadowing': [
          {'setup': 'Foreshadow about X', 'payoff': 'Reveal Y later'},
          {'setup': 'Hint about Z', 'payoff': 'Resolution in chapter 7'},
      ],
      'current_content': '...'
    }
    """
    if not isinstance(data, dict):
        return True, "No foreshadowing data to validate"

    foreshadowing = data.get("foreshadowing", [])
    current_content = data.get("current_content", "")

    if not isinstance(foreshadowing, list) or not foreshadowing:
        return True, ""

    issues: list[str] = []
    for idx, item in enumerate(foreshadowing, start=1):
        setup = ""
        payoff = ""
        if isinstance(item, dict):
            setup = str(item.get("setup", "")).strip()
            payoff = str(item.get("payoff", "")).strip()
        elif isinstance(item, str):
            setup = item.strip()

        if not setup and not payoff:
            issues.append(f"Foreshadowing #{idx} has no content")
            continue

        if payoff:
            # Simple check: if a payoff is declared, ensure the payoff text appears in the current content
            if payoff.lower() not in current_content.lower():
                issues.append(f"Foreshadowing payoff '{payoff}' not yet reflected in content")

    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_pacing(data: Any) -> tuple[bool, str]:
    """Validate pacing consistency."""
    # Expected data format:
    # {
    #   'current_content': str,
    #   'pacing': {
    #       'segments': [ { 'length': int|str, 'name': str }, ... ]
    #   }
    # }
    if not isinstance(data, dict):
        return True, "No pacing data to validate"
    current_content = data.get("current_content", "")
    pacing = data.get("pacing", {})
    if not isinstance(pacing, (dict, list)):
        return True, ""

    content = current_content.lower()
    issues: list[str] = []

    # Simple heuristic: flag if content describes both fast and slow pacing in the same piece
    fast_terms = ["fast", "rapid", "quick", "breathless", "brisk"]
    slow_terms = ["slow", "deliberate", "measured", "calm", "steady"]
    has_fast = any(t in content for t in fast_terms)
    has_slow = any(t in content for t in slow_terms)
    if has_fast and has_slow:
        issues.append("Contradictory pacing terms detected (fast and slow in same content)")

    # Optional: inspect segments if provided
    segments = []
    if isinstance(pacing, dict):
        segments = pacing.get("segments", []) or []
    elif isinstance(pacing, list):
        segments = pacing
    for seg in segments:
        if isinstance(seg, dict):
            length = seg.get("length")
            if isinstance(length, int):
                continue
            if isinstance(length, str) and length.lower() in {"short", "long"}:
                continue
    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_stakes(data: Any) -> tuple[bool, str]:
    """Validate stakes maintenance.

    Expected data format:
    {
      'stakes': {
          'objective': 'Protect the village',
          'threats': ['dragon', 'invaders'],
      },
      'current_content': '...'
    }
    """
    if not isinstance(data, dict):
        return True, "No stakes data to validate"
    stakes = data.get("stakes", {})
    current_content = data.get("current_content", "")
    if not isinstance(stakes, dict):
        return True, ""
    objective = stakes.get("objective")
    if objective is not None and isinstance(objective, str) and objective.strip():
        return True, ""
    # If content references stakes but objective is missing, flag it
    if current_content and "stake" in current_content.lower():
        return False, "Stakes objective is missing or unclear"
    return True, ""


def _validate_world_rules(data: Any) -> tuple[bool, str]:
    """Validate world rule consistency."""
    # Expected data format:
    # {
    #   'world_rules': dict with magic/technology rules
    #   'current_content': str - text to validate
    #   'rule_violations': list of known rule violations to check
    # }
    if not isinstance(data, dict):
        return True, "No world data to validate"

    world_rules = data.get("world_rules", {})
    current_content = data.get("current_content", "")
    rule_violations = data.get("rule_violations", [])

    if not current_content:
        return True, "No content to validate for world rule consistency"

    issues = []

    # Check magic/technology system rules
    magic_systems = world_rules.get("magic_systems", [])
    for system in magic_systems:
        if isinstance(system, dict):
            system_name = system.get("name", "")
            limitations = system.get("limitations", [])
            system.get("costs", [])

            # Check for rule violations
            for limitation in limitations:
                if isinstance(limitation, str):
                    # Look for violations of this limitation
                    # Example: if magic requires 'verbal component', check if spell is cast silently
                    violation_patterns = {
                        "requires verbal component": ["silently", "without words", "mute"],
                        "requires material component": ["without materials", "empty-handed"],
                        "limited uses per day": ["again and again", "repeatedly", "constantly"],
                        "exhausts the caster": ["effortlessly", "easily", "without fatigue"],
                    }
                    if limitation.lower() in violation_patterns:
                        for pattern in violation_patterns[limitation.lower()]:
                            if (
                                pattern in current_content.lower()
                                and system_name.lower() in current_content.lower()
                            ):
                                issues.append(
                                    f"Magic system '{system_name}' rule '{limitation}' violated: {pattern}"
                                )

    # Check predefined rule violations
    for violation in rule_violations:
        if isinstance(violation, dict):
            rule = violation.get("rule", "")
            description = violation.get("description", "")
            if rule and rule.lower() in current_content.lower():
                issues.append(f"World rule violation: {description}")

    # Check for common world rule issues
    common_issues = [
        ("winter thunder", "winter", ["thunder", "lightning", "storm"]),
        (
            "instant travel",
            ["teleported", "instantly arrived", "appeared instantly"],
            ["distance", "far", "miles"],
        ),
        ("unlimited power", ["limitless", "infinite", "unbounded"], ["magic", "power", "energy"]),
    ]

    for issue_name, triggers, contexts in common_issues:
        if isinstance(triggers, str):
            triggers = [triggers]
        for trigger in triggers:
            if trigger in current_content.lower():
                # Check if context is present
                context_found = False
                if isinstance(contexts, list):
                    for context in contexts:
                        if context in current_content.lower():
                            context_found = True
                            break
                if context_found:
                    issues.append(f"Potential world rule issue: {issue_name}")

    if issues:
        return False, "; ".join(issues[:3])  # Limit to first 3 issues
    return True, ""


def _validate_cultural_consistency(data: Any) -> tuple[bool, str]:
    """Validate cultural consistency."""
    if not isinstance(data, dict):
        return True, "No cultural data to validate"
    current_content = data.get("current_content", "")
    culture = data.get("culture", {})
    norms = []
    if isinstance(culture, dict):
        norms = culture.get("norms", []) or []
    if not norms:
        return True, ""
    content_lower = current_content.lower()
    missing = [n for n in norms if isinstance(n, str) and n.lower() not in content_lower]
    if missing:
        return False, f"Cultural norms not reflected: {', '.join(missing)}"
    return True, ""


def _validate_geography(data: Any) -> tuple[bool, str]:
    """Validate geographical consistency."""
    if not isinstance(data, dict):
        return True, "No geography data to validate"
    current_content = data.get("current_content", "")
    locations = data.get("locations", {})
    issues: list[str] = []
    if isinstance(locations, dict) and locations:
        location_names = [str(name).lower() for name in locations.keys()]
        if location_names:
            content = current_content.lower()
            # Require that at least one defined location is mentioned in content
            if not any(name in content for name in location_names):
                issues.append("Geographical locations defined but not described in content")
    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_system_limitations(data: Any) -> tuple[bool, str]:
    """Validate magic/technology limitations."""
    if not isinstance(data, dict):
        return True, "No system limitations data to validate"
    current_content = data.get("current_content", "")
    world_rules = data.get("world_rules", {}) or {}
    magic_systems = []
    if isinstance(world_rules, dict):
        magic_systems = world_rules.get("magic_systems", [])

    issues: list[str] = []
    content = current_content.lower()
    for system in magic_systems:
        if not isinstance(system, dict):
            continue
        name = str(system.get("name", "")).strip()
        limitations = system.get("limitations", []) or []
        for lim in limitations:
            if not isinstance(lim, str):
                continue
            lim_l = lim.lower()
            # If a limitation is mentioned, ensure there is some acknowledgement in content
            if (
                lim_l
                and (lim_l not in content)
                and ("cost" not in content)
                and ("limit" not in content)
            ):
                if name:
                    issues.append(f"System '{name}' limitation '{lim}' not reflected in content")
                else:
                    issues.append(f"System limitation '{lim}' not reflected in content")
    if issues:
        return False, "; ".join(issues[:3])
    return True, ""


def _validate_pov(data: Any) -> tuple[bool, str]:
    """Validate point of view consistency.

    Expected data format:
    {
      'pov': 'first-person' | 'third-person' | 'third-person-limited' | ...,
      'current_content': str
    }
    """
    if not isinstance(data, dict):
        return True, "No POV data to validate"
    pov = data.get("pov", "")
    current_content = data.get("current_content", "")
    valid = {"first-person", "second-person", "third-person", "third-person-limited", "thirdperson"}
    if pov:
        if str(pov).lower() not in valid:
            return False, f"Unrecognized point of view '{pov}'"
    # Basic check for head-hopping: ensure content isn't obviously switching POV indicators in a single clip
    if current_content:
        # naive heuristic: if multiple POV pronouns appear in a single paragraph, flag
        lower = current_content.lower()
        pronouns = ["i", "me", "my", "we", "us", "our", "you", "your"]
        if sum(1 for p in pronouns if p in lower) > 50:
            # too many pronouns could indicate head-hopping; keep permissive due to simplicity
            pass
    return True, ""


def _validate_show_dont_tell(data: Any) -> tuple[bool, str]:
    """Validate show don't tell."""
    if not isinstance(data, dict):
        return True, "No show/don't tell data to validate"
    current_content = data.get("current_content", "")
    if not isinstance(current_content, str) or not current_content:
        return True, ""
    content = current_content.lower()
    # Simple heuristic: flag obvious 'to be' state verbs with no supporting action
    tell_triggers = [
        " is ",
        " are ",
        " was ",
        " were ",
        " felt ",
        " seemed ",
        " appeared ",
        " knew ",
        " believed ",
    ]
    issues: list[str] = []
    if any(t in content for t in tell_triggers):
        issues.append(
            "Show, don't tell: consider replacing state verbs with actions or dialogue to reveal emotions or traits"
        )
    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_tone(data: Any) -> tuple[bool, str]:
    """Validate tone consistency."""
    if not isinstance(data, dict):
        return True, "No tone data to validate"
    current_content = data.get("current_content", "")
    tone = data.get("tone", "")
    allowed = {
        "dark",
        "hopeful",
        "grim",
        "whimsical",
        "serious",
        "light",
        "epic",
        "intimate",
        "mystical",
    }
    if tone:
        if str(tone).lower() not in allowed:
            return False, f"Unrecognized tone '{tone}'"
    if current_content:
        content = current_content.lower()
        # Detect dramatic tonal drift by comparing two contrasting adjectives
        if ("dark" in content and "light" in content) or (
            "grim" in content and "hopeful" in content
        ):
            return False, "Tone drift detected within content"
    return True, ""


def _validate_timeline(data: Any) -> tuple[bool, str]:
    """Validate timeline consistency."""
    # Expected data format:
    # {
    #   'timeline_events': list of dicts with event timestamps
    #   'current_content': str - text to validate
    #   'current_chapter_time': str - current time in story
    # }
    if not isinstance(data, dict):
        return True, "No timeline data to validate"

    timeline_events = data.get("timeline_events", [])
    current_content = data.get("current_content", "")
    current_chapter_time = data.get("current_chapter_time", "")

    if not current_content:
        return True, "No content to validate for timeline consistency"

    issues = []

    # Check for time-related contradictions
    time_indicators = {
        "morning": ["dawn", "sunrise", "early morning"],
        "afternoon": ["midday", "noon", "early afternoon"],
        "evening": ["dusk", "sunset", "twilight"],
        "night": ["midnight", "late night", "dark"],
        "day": ["sunlight", "daytime"],
        "winter": ["cold", "snow", "freezing"],
        "summer": ["hot", "warm", "sunny"],
    }

    # Check current chapter time consistency
    if current_chapter_time:
        current_time_lower = current_chapter_time.lower()
        for time_period, indicators in time_indicators.items():
            if time_period in current_time_lower:
                # Check for contradictions
                for indicator in indicators:
                    if indicator in current_content.lower():
                        # This is consistent
                        break
                else:
                    # No matching indicator found - potential issue
                    # But not necessarily an error, so just note
                    pass

    # Check timeline event order
    sorted(
        [e for e in timeline_events if isinstance(e, dict) and e.get("timestamp")],
        key=lambda x: x.get("timestamp", ""),
    )

    # Look for references to past/future events
    time_references = {
        "yesterday": -1,
        "last week": -7,
        "last month": -30,
        "last year": -365,
        "tomorrow": 1,
        "next week": 7,
        "next month": 30,
        "next year": 365,
    }

    for ref_text, _days in time_references.items():
        if ref_text in current_content.lower():
            # Found a time reference - could check consistency with timeline
            # Simple check: if referring to future event that already happened
            pass

    # Check for impossible time sequences
    impossible_patterns = [
        ("before", "after"),  # "before he arrived, after he left"
        ("earlier", "later"),
        ("first", "then", "previously"),
    ]

    for pattern in impossible_patterns:
        pattern_count = 0
        for word in pattern:
            if word in current_content.lower():
                pattern_count += 1
        if pattern_count > 1:
            # Multiple time sequence words - potential issue
            issues.append(f"Potential confusing time sequence: {pattern}")

    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_object_continuity(data: Any) -> tuple[bool, str]:
    """Validate object continuity."""
    if not isinstance(data, dict):
        return True, "No continuity data to validate"
    current_content = data.get("current_content", "")
    objects = data.get("objects", []) or []
    if not isinstance(objects, list):
        return True, ""
    issues: list[str] = []
    content = current_content.lower()
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        name = str(obj.get("name", "")).lower()
        state = str(obj.get("state", "")).lower()
        if not name:
            continue
        if name in content:
            # simple contradiction checks using common state deltas
            contradictions = {
                "damaged": ["repaired", "intact", "good"],
                "broken": ["fixed", "repaired", "intact"],
                "missing": ["present", "found", "here"],
            }
            if state in contradictions:
                for alt in contradictions[state]:
                    if alt in content:
                        issues.append(
                            f"Object '{name}' state '{state}' contradicts current narrative (mentions '{alt}')"
                        )
    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_character_knowledge(data: Any) -> tuple[bool, str]:
    """Validate character knowledge consistency."""
    if not isinstance(data, dict):
        return True, "No knowledge data to validate"
    current_content = data.get("current_content", "")
    knowledge = data.get("knowledge", {})
    if not isinstance(knowledge, dict) or not knowledge:
        return True, ""
    content = current_content.lower()
    issues: list[str] = []
    for _char, facts in knowledge.items():
        if isinstance(facts, (list, tuple)):
            for fact in facts:
                if isinstance(fact, str) and fact.lower() in content:
                    # content mentions a fact; assume character would know it if provided
                    continue
        elif isinstance(facts, str):
            if facts.lower() in content:
                continue
    # Basic no-op pass; in-depth checks would require NLP beyond scope
    if issues:
        return False, "; ".join(issues)
    return True, ""


def _validate_human_dignity(data: Any) -> tuple[bool, str]:
    """Validate respect for human dignity."""
    if not isinstance(data, dict):
        return True, "No ethics data to validate"
    current_content = data.get("current_content", "")
    if not isinstance(current_content, str) or not current_content:
        return True, ""
    content = current_content.lower()
    # Very simple guard against gratuitous degradation or exploitation terms
    forbidden = [
        "gratuitous violence",
        "humiliation",
        "demeaning",
        "exploitation",
        "slavery",
        "genocide",
    ]
    for term in forbidden:
        if term in content:
            return False, f"Content violates human dignity: {term}"
    return True, ""


def _validate_stereotypes(data: Any) -> tuple[bool, str]:
    """Validate avoidance of harmful stereotypes."""
    if not isinstance(data, dict):
        return True, "No stereotypes data to validate"
    current_content = data.get("current_content", "")
    if not isinstance(current_content, str) or not current_content:
        return True, ""
    content = current_content.lower()
    issues: list[str] = []
    # Simple keyword-based detector for common stereotypes
    stereotype_groups = [
        "women",
        "men",
        "disabled",
        "elderly",
        "youth",
        "latino",
        "latinos",
        "asian",
        "asians",
        "black",
        "blacks",
        "white",
        "nerd",
        "jock",
        "slacker",
        "immigrant",
    ]
    import re

    for group in stereotype_groups:
        # look for generic "X are/is ..." patterns
        pattern = rf"\b{re.escape(group)}\b\s+(are|is|was|were)"
        if re.search(pattern, content):
            issues.append(f"Harmful stereotype detected for group: {group}")
            break
    if issues:
        return False, "; ".join(issues)
    return True, ""


# ============================================================================
# Public API
# ============================================================================


class ConstitutionValidator:
    """Validator for constitutional rules."""

    def __init__(self, rules: list[ConstitutionalRule] | None = None):
        """Initialize validator.

        Args:
            rules: Optional custom rule set. Uses ALL_RULES by default.
        """
        self.rules = rules or ALL_RULES

    def validate_all(self, data: dict[str, Any]) -> dict[str, list[tuple[str, bool, str]]]:
        """Validate data against all rules.

        Args:
            data: Dictionary with domain keys ('character', 'plot', 'world', etc.)

        Returns:
            Dictionary mapping domain to list of (rule_id, is_valid, error_message)
        """
        results = {}
        for rule in self.rules:
            domain = rule.domain.value
            if domain not in results:
                results[domain] = []
            # Get appropriate data for this domain
            rule_data = data.get(domain, data)
            is_valid, error = rule.validate(rule_data)
            results[domain].append((rule.id, is_valid, error))
        return results

    def validate_domain(self, domain: RuleDomain, data: Any) -> list[tuple[str, bool, str]]:
        """Validate data against rules for a specific domain.

        Args:
            domain: Domain to validate
            data: Data to validate

        Returns:
            List of (rule_id, is_valid, error_message)
        """
        results = []
        for rule in self.rules:
            if rule.domain == domain:
                is_valid, error = rule.validate(data)
                results.append((rule.id, is_valid, error))
        return results

    def get_critical_violations(
        self, validation_results: dict[str, list[tuple[str, bool, str]]]
    ) -> list[str]:
        """Get all critical rule violations from validation results.

        Args:
            validation_results: Results from validate_all()

        Returns:
            List of violation descriptions
        """
        violations = []
        for _domain, results in validation_results.items():
            for rule_id, is_valid, error in results:
                if not is_valid:
                    # Find rule severity
                    for rule in self.rules:
                        if rule.id == rule_id and rule.severity == RuleSeverity.CRITICAL:
                            violations.append(f"{rule_id}: {error}")
        return violations


def get_constitution_summary() -> str:
    """Get a human-readable summary of all constitutional rules."""
    lines = ["# Novel Writing Constitution", ""]

    for domain in RuleDomain:
        lines.append(f"## {domain.value.upper()} RULES")
        lines.append("")
        for rule in RULES_BY_DOMAIN[domain]:
            lines.append(f"### {rule.id} - {rule.severity.value.upper()}")
            lines.append(f"**{rule.description}**")
            lines.append(f"✓ {rule.positive_guideline}")
            lines.append(f"✗ {rule.negative_prohibition}")
            lines.append("")

    return "\n".join(lines)


# Default validator instance
validator = ConstitutionValidator()
