"""
NovelWriter LSP - Updater Agent

Extracts structured information from novel content:
- Events (@Event definitions)
- Character state updates
- Relationship changes
"""

import re

try:
    from typing import override
except ImportError:
    from typing_extensions import override
from .base import BaseAgent, AgentResult


class UpdaterAgent(BaseAgent):
    """Agent for extracting structured information from novel content."""

    def __init__(self) -> None:
        super().__init__(name="UpdaterAgent")

    @override
    async def execute(self, input_data: dict[str, object]) -> AgentResult:
        uri = str(input_data.get("uri", ""))
        content = str(input_data.get("content", ""))
        return await self.extract_and_update(uri, content)

    async def extract_and_update(self, uri: str, content: str) -> AgentResult:
        _ = uri  # Mark as used to avoid linter warning
        extracted: dict[str, object] = {
            "new_events": self._extract_events(content),
            "character_updates": self._extract_character_updates(content),
            "relationship_changes": self._extract_relationships(content),
        }

        return AgentResult(
            success=True,
            data=extracted,
            warnings=[],
        )

    def _extract_events(self, content: str) -> list[dict[str, str]]:
        """Extract @Event definitions from content."""
        events: list[dict[str, str]] = []
        event_pattern = re.compile(r"@Event:\s*([\w\s]+)\s*\{([^}]*)\}", re.IGNORECASE)
        for match in event_pattern.finditer(content):
            event_name = match.group(1).strip()
            event_details = match.group(2)
            event: dict[str, str] = {"name": event_name}
            # Parse key-value pairs from details
            detail_pattern = re.compile(r"(\w+)\s*:\s*['\"]([^'\"]+)['\"]")
            for detail_match in detail_pattern.finditer(event_details):
                key = detail_match.group(1).strip()
                value = detail_match.group(2).strip()
                event[key] = value
            events.append(event)
        return events

    def _extract_character_updates(self, content: str) -> list[dict[str, str]]:
        """Extract character state updates from content."""
        updates: list[dict[str, str]] = []
        # Look for @Character definitions with status changes
        char_pattern = re.compile(r"@Character:\s*([\w\s]+)\s*\{([^}]*)\}", re.IGNORECASE)
        for match in char_pattern.finditer(content):
            char_name = match.group(1).strip()
            char_details = match.group(2)
            update: dict[str, str] = {"character": char_name}
            # Parse key-value pairs
            detail_pattern = re.compile(r"(\w+)\s*:\s*['\"]([^'\"]+)['\"]")
            for detail_match in detail_pattern.finditer(char_details):
                key = detail_match.group(1).strip()
                value = detail_match.group(2).strip()
                update[key] = value
            if len(update) > 1:  # Only add if there's more than just the character name
                updates.append(update)
        return updates

    def _extract_relationships(self, content: str) -> list[dict[str, str]]:
        """Extract relationship changes from content."""
        relations: list[dict[str, str]] = []
        # Look for @Relationship definitions
        rel_pattern = re.compile(
            r"@Relationship:\s*([\w\s]+)\s*&\s*([\w\s]+)\s*\{([^}]*)\}", re.IGNORECASE
        )
        for match in rel_pattern.finditer(content):
            char1 = match.group(1).strip()
            char2 = match.group(2).strip()
            rel_details = match.group(3)
            relation: dict[str, str] = {"character1": char1, "character2": char2}
            # Parse key-value pairs
            detail_pattern = re.compile(r"(\w+)\s*:\s*['\"]([^'\"]+)['\"]")
            for detail_match in detail_pattern.finditer(rel_details):
                key = detail_match.group(1).strip()
                value = detail_match.group(2).strip()
                relation[key] = value
            relations.append(relation)
        return relations
