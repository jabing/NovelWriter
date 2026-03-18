"""Continuity management system for novel generation.

This module provides classes for tracking story state, character states,
and ensuring continuity across chapters.
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# Key Events Configuration
MAX_KEY_EVENTS = 100  # Maximum number of key events to keep (increased for 50-chapter support)
CLIMAX_THRESHOLD = 0.5  # If >50% recent events are critical, we're in climax

# Patterns for detecting critical events (should never be pruned)
CRITICAL_EVENT_PATTERNS = [
    r"(?i)\b(died|killed|murdered|sacrificed|slain)\b",
    r"(?i)\b(revealed|discovered|learned the truth|uncovered)\b",
    r"(?i)\b(married|betrayed|allied with|became enemies|fell in love)\b",
    r"(?i)\b(crowned|promoted|exiled|imprisoned|freed)\b",
    r"(?i)\b(obtained|found|claimed|inherited|stole)\s+(the\s+)?[A-Z]",
]


def is_critical_event(event: str) -> bool:
    """Check if an event matches critical patterns.

    Critical events should never be pruned as they are essential
    for plot coherence.

    Args:
        event: Event description to check.

    Returns:
        True if event is critical, False otherwise.
    """
    return any(re.search(pattern, event) for pattern in CRITICAL_EVENT_PATTERNS)


@dataclass
class CharacterState:
    """State of a character in the story.

    Attributes:
        name: Character's name
        status: Current status (alive, dead, injured, captured, fused)
        location: Character's current location
        physical_form: Character's physical form (human, spirit, dragon, etc.)
        relationships: Dictionary mapping other character names to relationship types
        role_id: Optional unique identifier linking to CharacterRegistry entry
    """

    name: str
    status: str  # alive, dead, injured, captured, fused
    location: str
    physical_form: str
    relationships: dict[str, str] = field(default_factory=dict)
    role_id: str | None = None

    def is_alive(self) -> bool:
        """Check if character is alive."""
        return self.status == "alive"

    def is_dead(self) -> bool:
        """Check if character is dead."""
        return self.status == "dead"

    def is_fused(self) -> bool:
        """Check if character is fused with another."""
        return self.status == "fused"

    def has_physical_form(self) -> bool:
        """Check if character has a physical form."""
        return self.physical_form not in ["None", "spirit", "ghost", "memory"]


@dataclass
class PlotThread:
    """A plot thread in the story.

    Attributes:
        name: Name of the plot thread
        status: Current status (active, resolved, pending)
    """

    name: str
    status: str  # active, resolved, pending

    def is_active(self) -> bool:
        """Check if plot thread is active."""
        return self.status == "active"

    def is_resolved(self) -> bool:
        """Check if plot thread is resolved."""
        return self.status == "resolved"


@dataclass
class StoryState:
    """Overall state of the story at a specific chapter.

    Attributes:
        chapter: Current chapter number
        location: Current story location
        active_characters: List of character names currently present
        character_states: Dictionary mapping character names to their states
        plot_threads: List of active plot threads
        key_events: List of key events that have occurred
    """

    chapter: int
    location: str
    active_characters: list[str] = field(default_factory=list)
    character_states: dict[str, CharacterState] = field(default_factory=dict)
    plot_threads: list[PlotThread] = field(default_factory=list)
    key_events: list[str] = field(default_factory=list)

    def get_character_state(self, name: str) -> CharacterState | None:
        """Get state of a specific character."""
        return self.character_states.get(name)

    def is_character_active(self, name: str) -> bool:
        """Check if character is currently active/present."""
        return name in self.active_characters

    def get_active_plot_threads(self) -> list[PlotThread]:
        """Get all active plot threads."""
        return [thread for thread in self.plot_threads if thread.is_active()]

    def prune_key_events(self, max_events: int = MAX_KEY_EVENTS) -> tuple[int, bool]:
        """Prune key_events to max_events, preserving plot-critical events.

        Priority:
        1. Critical events (never remove)
        2. Recent events (keep last N)

        Args:
            max_events: Maximum number of events to keep. Defaults to MAX_KEY_EVENTS.

        Returns:
            Tuple of (number of events removed, was_climax_detected).
        """
        if len(self.key_events) <= max_events:
            return 0, False

        # Detect climax - if >50% of recent events are critical
        recent_window = min(15, len(self.key_events))
        recent_events = self.key_events[-recent_window:]
        critical_count = sum(1 for e in recent_events if is_critical_event(e))
        is_climax = (
            (critical_count / recent_window) > CLIMAX_THRESHOLD if recent_window > 0 else False
        )

        # Increase limit during climax
        effective_max = int(max_events * 1.5) if is_climax else max_events

        if len(self.key_events) <= effective_max:
            return 0, is_climax

        # Step 1: Classify events
        critical_events = [e for e in self.key_events if is_critical_event(e)]
        non_critical = [e for e in self.key_events if not is_critical_event(e)]

        # Step 2: Keep all critical events
        remaining_budget = effective_max - len(critical_events)

        # Step 3: Keep most recent non-critical events
        recent_non_critical = non_critical[-remaining_budget:] if remaining_budget > 0 else []

        # Step 4: Combine and maintain order
        original_count = len(self.key_events)
        self.key_events = critical_events + recent_non_critical
        removed_count = original_count - len(self.key_events)

        # Log pruning action
        if removed_count > 0:
            logger.info(
                f"Pruned {removed_count} events (kept {len(self.key_events)}, "
                f"critical={len(critical_events)}, climax={is_climax})"
            )

        return removed_count, is_climax

    def ensure_character_continuity(self, all_events: list[str]) -> None:
        """Ensure at least one event per known character is preserved.

        This handles the edge case where a character not mentioned for many
        chapters suddenly returns.

        Args:
            all_events: Complete list of events before pruning.
        """
        for char_name in self.character_states.keys():
            # Check if character is mentioned in current key_events
            if not any(char_name in e for e in self.key_events):
                # Find the character's most important event
                char_events = [e for e in all_events if char_name in e]
                if char_events:
                    # Add most recent event for this character
                    self.key_events.append(char_events[-1])
                    logger.debug(f"Preserved continuity event for {char_name}")


@dataclass
class StateChange:
    """Detected state change for a character.

    Attributes:
        character: Character name whose state changed
        old_state: Previous state value
        new_state: New state value
        evidence: Text evidence from content showing the change
    """

    character: str
    old_state: str
    new_state: str
    evidence: str


class ContinuityManager:
    """Manager for story continuity tracking and validation.

    This class provides methods to load, save, update, and validate story states,
    as well as generate context prompts for chapter generation.
    """

    def __init__(self) -> None:
        """Initialize the continuity manager."""
        self._character_name_pattern = re.compile(r"\b([A-Z][a-z]+)\b")

        # State detection patterns
        self._death_patterns = [
            re.compile(r"\b([A-Z][a-z]+)\s+died\b", re.IGNORECASE),
            re.compile(r"\b([A-Z][a-z]+)\s+was\s+killed\b", re.IGNORECASE),
            re.compile(r"\b([A-Z][a-z]+)\s+fell\b", re.IGNORECASE),
            re.compile(r"\b([A-Z][a-z]+)\s+perished\b", re.IGNORECASE),
            re.compile(r"\b([A-Z][a-z]+)\s+sacrificed\b", re.IGNORECASE),
        ]
        self._fusion_patterns = [
            re.compile(r"\b([A-Z][a-z]+)\s+fused\s+with\s+([A-Z][a-z]+)\b", re.IGNORECASE),
            re.compile(r"\b([A-Z][a-z]+)\s+merged\s+with\s+([A-Z][a-z]+)\b", re.IGNORECASE),
            re.compile(r"\b([A-Z][a-z]+)\s+became\s+one\s+with\s+([A-Z][a-z]+)\b", re.IGNORECASE),
        ]
        self._capture_patterns = [
            re.compile(r"\b([A-Z][a-z]+)\s+was\s+captured\b", re.IGNORECASE),
            re.compile(r"\b([A-Z][a-z]+)\s+was\s+taken\s+prisoner\b", re.IGNORECASE),
        ]
        self._location_patterns = [
            re.compile(
                r"\b([A-Z][a-z]+)\s+arrived\s+(?:at|in)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b([A-Z][a-z]+)\s+traveled\s+(?:to|into)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
                re.IGNORECASE,
            ),
        ]

    def load(self, state_dict: dict[str, Any]) -> StoryState:
        """Load StoryState from dictionary.

        Args:
            state_dict: Dictionary representation of story state

        Returns:
            StoryState object
        """
        # Convert character states
        character_states = {}
        for name, char_dict in state_dict.get("character_states", {}).items():
            # Handle missing role_id for backward compatibility
            char_dict.setdefault("role_id", None)
            character_states[name] = CharacterState(**char_dict)

        # Convert plot threads
        plot_threads = []
        for thread_dict in state_dict.get("plot_threads", []):
            plot_threads.append(PlotThread(**thread_dict))

        # Create story state
        return StoryState(
            chapter=state_dict["chapter"],
            location=state_dict["location"],
            active_characters=state_dict.get("active_characters", []),
            character_states=character_states,
            plot_threads=plot_threads,
            key_events=state_dict.get("key_events", []),
        )

    def save(self, state: StoryState) -> dict[str, Any]:
        """Save StoryState to dictionary.

        Args:
            state: StoryState object

        Returns:
            Dictionary representation of story state
        """
        # Convert character states to dicts
        character_states = {}
        for name, char_state in state.character_states.items():
            character_states[name] = asdict(char_state)

        # Convert plot threads to dicts
        plot_threads = [asdict(thread) for thread in state.plot_threads]

        return {
            "chapter": state.chapter,
            "location": state.location,
            "active_characters": state.active_characters,
            "character_states": character_states,
            "plot_threads": plot_threads,
            "key_events": state.key_events,
        }

    def update_from_chapter(
        self,
        state: StoryState,
        chapter_content: str,
        chapter_number: int,
        known_characters: list[str] | None = None,
    ) -> StoryState:
        """Update story state based on chapter content.

        Args:
            state: Current story state
            chapter_content: Content of the chapter
            chapter_number: Chapter number
            known_characters: Optional list of known character names from outline.
                            If provided, only these characters will be tracked.

        Returns:
            Updated story state
        """
        # Create a copy of the state
        updated_state = StoryState(
            chapter=chapter_number,
            location=state.location,
            active_characters=state.active_characters.copy(),
            character_states={
                name: CharacterState(
                    name=char.name,
                    status=char.status,
                    location=char.location,
                    physical_form=char.physical_form,
                    relationships=char.relationships.copy(),
                    role_id=char.role_id,
                )
                for name, char in state.character_states.items()
            },
            plot_threads=[
                PlotThread(name=thread.name, status=thread.status) for thread in state.plot_threads
            ],
            key_events=state.key_events.copy(),
        )

        # Extract character names from content
        character_names = self._extract_character_names(chapter_content)

        # Filter against known characters if provided (from outline)
        if known_characters:
            # Only keep characters that are in the known list
            character_names = [name for name in character_names if name in known_characters]
            # Also ensure all known characters are in the state (even if not detected)
            for known_name in known_characters:
                if known_name not in updated_state.character_states:
                    updated_state.character_states[known_name] = CharacterState(
                        name=known_name,
                        status="alive",
                        location=updated_state.location,
                        physical_form="human",
                        relationships={},
                    )

        # Update active characters
        updated_state.active_characters = list(set(character_names))
        # Add new characters to state if not present
        for name in character_names:
            if name not in updated_state.character_states:
                updated_state.character_states[name] = CharacterState(
                    name=name,
                    status="alive",
                    location=updated_state.location,
                    physical_form="human",
                    relationships={},
                )

        # Extract location (simple heuristic - look for location indicators)
        location = self._extract_location(chapter_content)
        if location:
            updated_state.location = location

        # Detect and apply state changes
        state_changes = self._detect_state_changes(chapter_content)
        for change in state_changes:
            if change.character in updated_state.character_states:
                char_state = updated_state.character_states[change.character]
                # For status changes (death, capture, fusion)
                if change.old_state in ["alive", "dead", "captured", "fused", "injured"]:
                    char_state.status = change.new_state
                # For location changes
                elif change.old_state == "location":
                    char_state.location = change.new_state

        return updated_state

    def validate_for_chapter(self, state: StoryState, chapter_number: int) -> list[str]:
        """Validate story state for generating a specific chapter.

        Args:
            state: Current story state
            chapter_number: Chapter number to validate for

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check 1: Dead characters should not be in active_characters
        for char_name in state.active_characters:
            char_state = state.get_character_state(char_name)
            if char_state and char_state.is_dead():
                errors.append(
                    f"Character '{char_name}' is marked as dead but is in active_characters list"
                )

        # Check 2: Fused characters should not have independent physical form
        for char_name, char_state in state.character_states.items():
            if char_state.is_fused() and char_name in state.active_characters:
                if char_state.has_physical_form() and char_state.physical_form != "spirit":
                    errors.append(
                        f"Character '{char_name}' is fused but appears with physical form '{char_state.physical_form}'"
                    )

        # Check 3: Active characters should be in character_states
        for char_name in state.active_characters:
            if char_name not in state.character_states:
                errors.append(
                    f"Character '{char_name}' is in active_characters but not in character_states"
                )

        return errors

    def generate_context_prompt(self, state: StoryState, chapter_spec) -> str:
        """Generate a continuity context prompt for chapter generation.

        Args:
            state: Current story state
            chapter_spec: Chapter specification

        Returns:
            Prompt string with continuity information
        """
        prompt_parts = [
            "【连续性规则 - 必须严格遵守】\n",
            f"故事当前状态（第{state.chapter}章）：\n",
            f"- 地点：{state.location}\n",
            f"- 在场角色：{', '.join(state.active_characters)}\n",
        ]

        # Add active plot threads
        active_threads = state.get_active_plot_threads()
        if active_threads:
            prompt_parts.append(f"- 活跃剧情线索：{', '.join(t.name for t in active_threads)}\n")

        # Add recent key events (last 3)
        if state.key_events:
            recent_events = state.key_events[-3:]
            prompt_parts.append(f"- 最近关键事件：{'; '.join(recent_events)}\n")

        # Add character status checks
        prompt_parts.append("\n角色状态检查：\n")
        for char_name in state.active_characters:
            char_state = state.get_character_state(char_name)
            if char_state:
                status_text = f"{char_name}: {char_state.status}"
                if char_state.location != state.location:
                    status_text += f" (位置: {char_state.location})"
                prompt_parts.append(f"- {status_text}\n")

        # Add character states for tracking
        prompt_parts.append("\n所有角色状态：\n")
        for char_name, char_state in state.character_states.items():
            prompt_parts.append(
                f"- {char_name}: {char_state.status}, 形态: {char_state.physical_form}\n"
            )

        # Add chapter requirements
        prompt_parts.append("\n【本章要求】\n")
        prompt_parts.append(f"- 章节号：{chapter_spec.number}\n")
        prompt_parts.append(f"- 标题：{chapter_spec.title}\n")
        prompt_parts.append(f"- 地点：{chapter_spec.location}\n")

        if chapter_spec.characters:
            prompt_parts.append(f"- 必须包含的角色：{', '.join(chapter_spec.characters)}\n")

        if chapter_spec.key_events:
            prompt_parts.append(f"- 关键事件：{', '.join(chapter_spec.key_events)}\n")

        # Add writing rules
        prompt_parts.append("\n【写作要求】\n")
        prompt_parts.append("1. 必须尊重所有角色当前状态\n")
        prompt_parts.append("2. 角色对话和行为必须符合其性格和当前处境\n")
        prompt_parts.append("3. 地点描述必须与当前设置一致\n")
        prompt_parts.append("4. 任何角色状态变化必须在本章中有明确描写\n")
        prompt_parts.append("5. 死去的角色不能以活着的身份出现\n")
        prompt_parts.append("6. 融合的角色不能有独立的物理形态\n")

        return "".join(prompt_parts)

    def _extract_character_names(self, content: str) -> list[str]:
        """Extract character names from content.

        This is a simple heuristic - looks for capitalized words that appear
        multiple times (likely names).

        Args:
            content: Chapter content

        Returns:
            List of likely character names
        """
        # Find all capitalized words
        words = self._character_name_pattern.findall(content)

        # Common words to skip (expanded list)
        skip_words = {
            # Articles and determiners
            "the",
            "this",
            "that",
            "these",
            "those",
            "a",
            "an",
            # Verbs
            "is",
            "was",
            "are",
            "were",
            "have",
            "had",
            "has",
            "will",
            "would",
            "could",
            "should",
            "do",
            "does",
            "did",
            "can",
            "may",
            "might",
            "must",
            # Pronouns
            "he",
            "she",
            "it",
            "they",
            "you",
            "i",
            "we",
            "his",
            "her",
            "their",
            "my",
            "your",
            # Conjunctions and prepositions
            "and",
            "but",
            "or",
            "nor",
            "for",
            "yet",
            "so",
            "in",
            "on",
            "at",
            "to",
            "from",
            "by",
            "with",
            "of",
            "as",
            "when",
            "where",
            "while",
            "if",
            "then",
            "than",
            # Common adjectives/adverbs
            "all",
            "no",
            "not",
            "now",
            "here",
            "there",
            "how",
            "why",
            "each",
            "every",
            "any",
            "some",
            "most",
            "many",
            "few",
            "more",
            "less",
            # Time expressions
            "today",
            "tonight",
            "yesterday",
            "tomorrow",
            "soon",
            "once",
            # Common sentence starters
            "suddenly",
            "finally",
            "slowly",
            "quickly",
            "carefully",
            "silently",
            # Fantasy/common words that aren't names
            "master",
            "dragon",
            "dragons",
            "magic",
            "mage",
            "mages",
            "inquisitor",
            "inquisitors",
            "chapter",
            "scene",
            "hook",
            "opening",
            "closing",
        }

        # Count occurrences
        word_counts = {}
        for word in words:
            if word.lower() in skip_words:
                continue
            # Skip short words (likely not names)
            if len(word) < 3:
                continue
            word_counts[word] = word_counts.get(word, 0) + 1

        # Return words that appear at least 3 times (more likely to be names)
        # Also include words that appear at the start of dialogue ("Name said")
        likely_names = []
        for word, count in word_counts.items():
            if count >= 3:
                likely_names.append(word)
            elif count >= 2:
                # Check if word appears before dialogue verbs
                dialogue_pattern = (
                    rf"\b{re.escape(word)}\s+(said|asked|replied|whispered|shouted|cried)\b"
                )
                if re.search(dialogue_pattern, content, re.IGNORECASE):
                    likely_names.append(word)

        return likely_names

    def _detect_state_changes(self, content: str) -> list[StateChange]:
        """Detect character state changes from chapter content.

        Uses regex patterns to identify state changes like death, fusion,
        capture, and location changes.

        Args:
            content: Chapter content

        Returns:
            List of StateChange objects describing detected changes
        """
        changes: list[StateChange] = []

        # Detect death patterns
        for pattern in self._death_patterns:
            for match in pattern.finditer(content):
                character = match.group(1)
                changes.append(
                    StateChange(
                        character=character,
                        old_state="alive",
                        new_state="dead",
                        evidence=match.group(0),
                    )
                )

        # Detect fusion patterns
        for pattern in self._fusion_patterns:
            for match in pattern.finditer(content):
                character1 = match.group(1)
                character2 = match.group(2)
                changes.append(
                    StateChange(
                        character=character1,
                        old_state="alive",
                        new_state="fused",
                        evidence=match.group(0),
                    )
                )
                changes.append(
                    StateChange(
                        character=character2,
                        old_state="alive",
                        new_state="fused",
                        evidence=match.group(0),
                    )
                )

        # Detect capture patterns
        for pattern in self._capture_patterns:
            for match in pattern.finditer(content):
                character = match.group(1)
                changes.append(
                    StateChange(
                        character=character,
                        old_state="alive",
                        new_state="captured",
                        evidence=match.group(0),
                    )
                )

        # Detect location patterns
        for pattern in self._location_patterns:
            for match in pattern.finditer(content):
                character = match.group(1)
                new_location = match.group(2)
                changes.append(
                    StateChange(
                        character=character,
                        old_state="location",
                        new_state=new_location,
                        evidence=match.group(0),
                    )
                )

        return changes

    def _extract_location(self, content: str) -> str | None:
        """Extract location from content.

        This is a simple heuristic - looks for common location indicators.

        Args:
            content: Chapter content

        Returns:
            Location string or None
        """
        # Look for common location patterns
        location_patterns = [
            r"(?:at|in|the|from) (?:the )?([A-Z][a-z]+(?:\\s+(?:of|the|and|in|on|at|to|from|by|with)?\\s*[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?: Hall| Room| Library| Garden| Academy)",
        ]

        for pattern in location_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Return the most common match
                from collections import Counter

                counter = Counter(matches)
                return counter.most_common(1)[0][0].strip()

        return None
