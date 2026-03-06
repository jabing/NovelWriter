"""
NovelWriter LSP - Validator Agent

Checks for consistency issues in the novel content:
- Character status consistency (e.g., dead characters appearing alive)
- Timeline consistency
- Event detail consistency
"""

import re
from typing import override
from .base import BaseAgent, AgentResult


class ValidatorAgent(BaseAgent):
    """Agent for validating novel content consistency."""

    def __init__(self) -> None:
        super().__init__(name="ValidatorAgent")

    @override
    async def execute(self, input_data: dict[str, object]) -> AgentResult:
        uri = str(input_data.get("uri", ""))
        content = str(input_data.get("content", ""))
        return await self.validate(uri, content)

    async def validate(self, uri: str, content: str) -> AgentResult:
        errors: list[str] = []
        warnings: list[str] = []

        # Rule 1: Dead characters should not appear alive
        if self._check_dead_character_alive(content):
            errors.append("Dead character appears alive in content")

        # Rule 2: Check for timeline inconsistencies (duplicate dates)
        timeline_errors = self._check_timeline_consistency(content)
        errors.extend(timeline_errors)

        # Rule 3: Check for missing event details
        event_warnings = self._check_event_details(content)
        warnings.extend(event_warnings)

        # Rule 4: Check for character age inconsistencies
        age_errors = self._check_age_consistency(content)
        errors.extend(age_errors)

        return AgentResult(
            success=len(errors) == 0,
            data={"uri": uri},
            errors=errors,
            warnings=warnings,
        )

    def _check_dead_character_alive(self, content: str) -> bool:
        """Check if a character marked dead appears alive."""
        # Look for patterns like "@Character: Name { status: \"dead\" }" and later mentions of the character being alive
        dead_char_pattern = re.compile(
            r'@Character:\s*([\w\s]+)\s*\{[^}]*status\s*:\s*["\']dead["\'][^}]*\}', re.IGNORECASE
        )
        dead_chars = dead_char_pattern.findall(content)
        for char in dead_chars:
            # Check if the character is mentioned with "alive" or similar terms
            char_lower = char.strip().lower()
            alive_pattern = re.compile(
                rf"\b{re.escape(char_lower)}\b.*\b(alive|walking|talking|speaking|moving)\b",
                re.IGNORECASE,
            )
            if alive_pattern.search(content):
                return True
        return False

    def _check_timeline_consistency(self, content: str) -> list[str]:
        """Check for timeline inconsistencies (duplicate event times)."""
        errors: list[str] = []
        # Look for @Event definitions with time
        event_time_pattern = re.compile(
            r'@Event:\s*([\w\s]+)\s*\{[^}]*time\s*:\s*["\']([^"\']+)["\'][^}]*\}', re.IGNORECASE
        )
        time_to_events: dict[str, list[str]] = {}
        for match in event_time_pattern.finditer(content):
            event_name = match.group(1).strip()
            event_time = match.group(2).strip()
            if event_time not in time_to_events:
                time_to_events[event_time] = []
            time_to_events[event_time].append(event_name)

        for time, events in time_to_events.items():
            if len(events) > 1:
                errors.append(f"Multiple events at the same time '{time}': {', '.join(events)}")
        return errors

    def _check_event_details(self, content: str) -> list[str]:
        """Check for events missing important details (location, participants)."""
        warnings: list[str] = []
        event_pattern = re.compile(r"@Event:\s*([\w\s]+)\s*\{([^}]*)\}", re.IGNORECASE)
        for match in event_pattern.finditer(content):
            event_name = match.group(1).strip()
            event_details = match.group(2)
            missing: list[str] = []
            if "location" not in event_details.lower():
                missing.append("location")
            if "participants" not in event_details.lower():
                missing.append("participants")
            if missing:
                warnings.append(f"Event '{event_name}' missing details: {', '.join(missing)}")
        return warnings

    def _check_age_consistency(self, content: str) -> list[str]:
        """Check for character age inconsistencies (multiple different ages)."""
        errors: list[str] = []
        age_pattern = re.compile(
            r"@Character:\s*([\w\s]+)\s*\{[^}]*age\s*:\s*(\d+)[^}]*\}", re.IGNORECASE
        )
        char_to_ages: dict[str, list[int]] = {}
        for match in age_pattern.finditer(content):
            char_name = match.group(1).strip()
            age = int(match.group(2))
            if char_name not in char_to_ages:
                char_to_ages[char_name] = []
            char_to_ages[char_name].append(age)

        for char, ages in char_to_ages.items():
            unique_ages = list(set(ages))
            if len(unique_ages) > 1:
                errors.append(
                    f"Character '{char}' has conflicting ages: {', '.join(map(str, unique_ages))}"
                )
        return errors
