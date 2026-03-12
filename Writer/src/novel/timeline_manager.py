"""Timeline manager for macro/micro timeline consistency.

Manages story events at multiple scales (arc, chapter, scene) and ensures
temporal consistency across the narrative.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TimeUnit(str, Enum):
    """Units of time measurement."""

    SCENE = "scene"
    CHAPTER = "chapter"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ARC = "arc"
    EPOCH = "epoch"


class TemporalRelation(str, Enum):
    """Temporal relationships between events."""

    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    SIMULTANEOUS = "simultaneous"
    OVERLAPS = "overlaps"
    MEETS = "meets"
    STARTS = "starts"
    FINISHES = "finishes"


class TimelineEvent:
    """Represents a single event in the timeline."""

    def __init__(
        self,
        event_id: str,
        timestamp: str,
        description: str,
        event_type: str = "generic",
        metadata: dict[str, Any] | None = None,
        start_order: int | None = None,
        end_order: int | None = None,
        time_unit: TimeUnit = TimeUnit.SCENE,
    ) -> None:
        """Initialize a timeline event.

        Args:
            event_id: Unique event identifier
            timestamp: Human-readable timestamp (e.g., "Day 5, Morning")
            description: Description of the event
            event_type: Type of event (battle, dialogue, travel, etc.)
            metadata: Additional event properties
            start_order: Numeric order for timeline sorting (optional)
            end_order: For events with duration (optional)
            time_unit: Unit of time for this event
        """
        self.event_id = event_id
        self.timestamp = timestamp
        self.description = description
        self.event_type = event_type
        self.metadata = metadata or {}
        self.start_order = start_order
        self.end_order = end_order
        self.time_unit = time_unit
        self.created_at = datetime.now()
        self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "description": self.description,
            "event_type": self.event_type,
            "metadata": self.metadata,
            "start_order": self.start_order,
            "end_order": self.end_order,
            "time_unit": self.time_unit.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimelineEvent":
        """Create event from dictionary."""
        event = cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            description=data["description"],
            event_type=data.get("event_type", "generic"),
            metadata=data.get("metadata", {}),
            start_order=data.get("start_order"),
            end_order=data.get("end_order"),
            time_unit=TimeUnit(data.get("time_unit", TimeUnit.SCENE.value)),
        )
        # Restore timestamps
        if "created_at" in data:
            event.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            event.updated_at = datetime.fromisoformat(data["updated_at"])
        return event


class TimelineManager:
    """Manages timeline events and temporal relationships."""

    def __init__(self, timeline_id: str = "default", storage_path: Path | None = None) -> None:
        """Initialize timeline manager.

        Args:
            timeline_id: Unique identifier for this timeline
            storage_path: Optional path for persistent storage
        """
        self.timeline_id = timeline_id
        self.storage_path = storage_path

        # In-memory storage
        self._events: dict[str, TimelineEvent] = {}
        self._relations: dict[
            str, tuple[str, str, TemporalRelation]
        ] = {}  # relation_id -> (source_id, target_id, relation)

        # Indexes
        self._event_type_index: dict[str, set[str]] = {}
        self._timestamp_index: dict[str, set[str]] = {}  # timestamp -> event_ids
        self._time_unit_index: dict[TimeUnit, set[str]] = {}

        # Load from storage if path exists
        if storage_path and storage_path.exists():
            self._load_from_storage()

        logger.info(
            f"TimelineManager '{timeline_id}' initialized with {len(self._events)} events, "
            f"{len(self._relations)} relations"
        )

    def _load_from_storage(self) -> None:
        """Load timeline from storage path."""
        if not self.storage_path:
            return

        try:
            events_file = self.storage_path / "events.json"
            relations_file = self.storage_path / "relations.json"

            if events_file.exists():
                with open(events_file, encoding="utf-8") as f:
                    events_data = json.load(f)

                for event_data in events_data:
                    event = TimelineEvent.from_dict(event_data)
                    self._add_event_to_indexes(event)

            if relations_file.exists():
                with open(relations_file, encoding="utf-8") as f:
                    relations_data = json.load(f)

                for rel_data in relations_data:
                    self._relations[rel_data["relation_id"]] = (
                        rel_data["source_id"],
                        rel_data["target_id"],
                        TemporalRelation(rel_data["relation_type"]),
                    )

            logger.info(f"Loaded timeline from {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to load timeline from {self.storage_path}: {e}")

    def _save_to_storage(self) -> None:
        """Save timeline to storage path."""
        if not self.storage_path:
            return

        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Save events
            events_data = [event.to_dict() for event in self._events.values()]
            events_file = self.storage_path / "events.json"
            with open(events_file, "w", encoding="utf-8") as f:
                json.dump(events_data, f, indent=2, ensure_ascii=False)

            # Save relations
            relations_data = []
            for rel_id, (source_id, target_id, relation) in self._relations.items():
                relations_data.append(
                    {
                        "relation_id": rel_id,
                        "source_id": source_id,
                        "target_id": target_id,
                        "relation_type": relation.value,
                    }
                )

            relations_file = self.storage_path / "relations.json"
            with open(relations_file, "w", encoding="utf-8") as f:
                json.dump(relations_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved timeline to {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to save timeline to {self.storage_path}: {e}")

    def _add_event_to_indexes(self, event: TimelineEvent) -> None:
        """Add event to all indexes."""
        self._events[event.event_id] = event

        # Update type index
        if event.event_type not in self._event_type_index:
            self._event_type_index[event.event_type] = set()
        self._event_type_index[event.event_type].add(event.event_id)

        # Update timestamp index
        if event.timestamp not in self._timestamp_index:
            self._timestamp_index[event.timestamp] = set()
        self._timestamp_index[event.timestamp].add(event.event_id)

        # Update time unit index
        if event.time_unit not in self._time_unit_index:
            self._time_unit_index[event.time_unit] = set()
        self._time_unit_index[event.time_unit].add(event.event_id)

    def _remove_event_from_indexes(self, event_id: str) -> None:
        """Remove event from all indexes."""
        if event_id not in self._events:
            return

        event = self._events[event_id]

        # Remove from type index
        if event.event_type in self._event_type_index:
            self._event_type_index[event.event_type].discard(event_id)
            if not self._event_type_index[event.event_type]:
                del self._event_type_index[event.event_type]

        # Remove from timestamp index
        if event.timestamp in self._timestamp_index:
            self._timestamp_index[event.timestamp].discard(event_id)
            if not self._timestamp_index[event.timestamp]:
                del self._timestamp_index[event.timestamp]

        # Remove from time unit index
        if event.time_unit in self._time_unit_index:
            self._time_unit_index[event.time_unit].discard(event_id)
            if not self._time_unit_index[event.time_unit]:
                del self._time_unit_index[event.time_unit]

        # Remove the event
        del self._events[event_id]

    def add_event(
        self,
        event_id: str,
        timestamp: str,
        description: str,
        event_type: str = "generic",
        metadata: dict[str, Any] | None = None,
        start_order: int | None = None,
        end_order: int | None = None,
        time_unit: TimeUnit = TimeUnit.SCENE,
    ) -> TimelineEvent:
        """Add an event to the timeline.

        Args:
            event_id: Unique event identifier
            timestamp: Human-readable timestamp
            description: Event description
            event_type: Type of event
            metadata: Additional properties
            start_order: Numeric order for sorting
            end_order: For events with duration
            time_unit: Unit of time

        Returns:
            The created event

        Raises:
            ValueError: If event with same ID already exists
        """
        if event_id in self._events:
            raise ValueError(f"Event with ID '{event_id}' already exists")

        event = TimelineEvent(
            event_id=event_id,
            timestamp=timestamp,
            description=description,
            event_type=event_type,
            metadata=metadata,
            start_order=start_order,
            end_order=end_order,
            time_unit=time_unit,
        )

        self._add_event_to_indexes(event)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Added event: {event_id} ({timestamp}, {event_type})")
        return event

    def update_event(
        self,
        event_id: str,
        timestamp: str | None = None,
        description: str | None = None,
        event_type: str | None = None,
        metadata: dict[str, Any] | None = None,
        merge_metadata: bool = True,
        start_order: int | None = None,
        end_order: int | None = None,
        time_unit: TimeUnit | None = None,
    ) -> TimelineEvent | None:
        """Update an existing event.

        Args:
            event_id: Event identifier
            timestamp: New timestamp (None to keep existing)
            description: New description (None to keep existing)
            event_type: New event type (None to keep existing)
            metadata: New metadata (None to keep existing)
            merge_metadata: If True, merge with existing metadata
            start_order: New start order (None to keep existing)
            end_order: New end order (None to keep existing)
            time_unit: New time unit (None to keep existing)

        Returns:
            Updated event or None if event not found
        """
        if event_id not in self._events:
            logger.warning(f"Cannot update non-existent event: {event_id}")
            return None

        event = self._events[event_id]

        # Remove from indexes before updating
        self._remove_event_from_indexes(event_id)

        # Update fields
        if timestamp is not None:
            event.timestamp = timestamp
        if description is not None:
            event.description = description
        if event_type is not None:
            event.event_type = event_type
        if metadata is not None:
            if merge_metadata:
                event.metadata.update(metadata)
            else:
                event.metadata = metadata
        if start_order is not None:
            event.start_order = start_order
        if end_order is not None:
            event.end_order = end_order
        if time_unit is not None:
            event.time_unit = time_unit

        event.updated_at = datetime.now()

        # Add back to indexes
        self._add_event_to_indexes(event)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Updated event: {event_id}")
        return event

    def get_event(self, event_id: str) -> TimelineEvent | None:
        """Get an event by ID."""
        return self._events.get(event_id)

    def delete_event(self, event_id: str, cascade: bool = True) -> bool:
        """Delete an event from the timeline.

        Args:
            event_id: Event identifier
            cascade: If True, also delete all relations involving this event

        Returns:
            True if event was deleted
        """
        if event_id not in self._events:
            return False

        # Delete related relations if cascading
        if cascade:
            relations_to_delete = []
            for rel_id, (source_id, target_id, _) in self._relations.items():
                if source_id == event_id or target_id == event_id:
                    relations_to_delete.append(rel_id)

            for rel_id in relations_to_delete:
                del self._relations[rel_id]

        # Delete the event
        self._remove_event_from_indexes(event_id)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Deleted event: {event_id} (cascade={cascade})")
        return True

    def add_relation(
        self,
        relation_id: str,
        source_id: str,
        target_id: str,
        relation_type: TemporalRelation,
    ) -> tuple[str, str, TemporalRelation]:
        """Add a temporal relation between events.

        Args:
            relation_id: Unique relation identifier
            source_id: Source event ID
            target_id: Target event ID
            relation_type: Type of temporal relation

        Returns:
            The created relation tuple

        Raises:
            ValueError: If relation ID already exists or events don't exist
        """
        if relation_id in self._relations:
            raise ValueError(f"Relation with ID '{relation_id}' already exists")

        if source_id not in self._events:
            raise ValueError(f"Source event '{source_id}' not found")

        if target_id not in self._events:
            raise ValueError(f"Target event '{target_id}' not found")

        self._relations[relation_id] = (source_id, target_id, relation_type)

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(
            f"Added relation: {relation_id} ({source_id} {relation_type.value} {target_id})"
        )
        return self._relations[relation_id]

    def delete_relation(self, relation_id: str) -> bool:
        """Delete a relation from the timeline.

        Returns:
            True if relation was deleted
        """
        if relation_id not in self._relations:
            return False

        del self._relations[relation_id]

        # Auto-save if storage path is configured
        if self.storage_path:
            self._save_to_storage()

        logger.debug(f"Deleted relation: {relation_id}")
        return True

    def get_relations(
        self, event_id: str | None = None
    ) -> list[tuple[str, str, TemporalRelation]]:
        """Get relations matching criteria.

        Args:
            event_id: Optional event ID to filter relations involving this event

        Returns:
            List of matching relations
        """
        if event_id is None:
            return list(self._relations.values())

        relations = []
        for source_id, target_id, relation_type in self._relations.values():
            if source_id == event_id or target_id == event_id:
                relations.append((source_id, target_id, relation_type))

        return relations

    def find_events_by_type(self, event_type: str) -> list[TimelineEvent]:
        """Find all events of a specific type."""
        if event_type not in self._event_type_index:
            return []

        event_ids = self._event_type_index[event_type]
        return [self._events[eid] for eid in event_ids]

    def find_events_by_timestamp(self, timestamp: str) -> list[TimelineEvent]:
        """Find all events with a specific timestamp."""
        if timestamp not in self._timestamp_index:
            return []

        event_ids = self._timestamp_index[timestamp]
        return [self._events[eid] for eid in event_ids]

    def find_events_by_time_unit(self, time_unit: TimeUnit) -> list[TimelineEvent]:
        """Find all events with a specific time unit."""
        if time_unit not in self._time_unit_index:
            return []

        event_ids = self._time_unit_index[time_unit]
        return [self._events[eid] for eid in event_ids]

    def get_events_in_order(self, ascending: bool = True) -> list[TimelineEvent]:
        """Get all events sorted by start_order (if available) or timestamp.

        Events without start_order are placed at the end.
        """
        events_with_order = []
        events_without_order = []

        for event in self._events.values():
            if event.start_order is not None:
                events_with_order.append(event)
            else:
                events_without_order.append(event)

        # Sort by start_order
        events_with_order.sort(key=lambda e: e.start_order, reverse=not ascending)

        # Combine
        return events_with_order + events_without_order

    def validate_temporal_consistency(self) -> list[str]:
        """Validate temporal consistency of events and relations.

        Checks for:
        - Cycles in temporal relations
        - Conflicting relations (A before B and B before A)
        - Events with invalid start/end order (end < start)

        Returns:
            List of consistency issues
        """
        issues = []

        # Check for cycles using DFS
        graph: dict[str, list[str]] = {}
        for source_id, target_id, relation in self._relations.values():
            if relation in (
                TemporalRelation.BEFORE,
                TemporalRelation.STARTS,
                TemporalRelation.MEETS,
            ):
                # source happens before target
                if source_id not in graph:
                    graph[source_id] = []
                graph[source_id].append(target_id)

        # Simple cycle detection (not exhaustive)
        visited = set()

        def dfs(node: str, path: set[str]) -> None:
            if node in path:
                issues.append(f"Cycle detected involving event: {node}")
                return
            if node in visited:
                return

            visited.add(node)
            path.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path.copy())

        for node in graph:
            if node not in visited:
                dfs(node, set())

        # Check for conflicting relations
        relation_map: dict[tuple[str, str], TemporalRelation] = {}
        for source_id, target_id, relation in self._relations.values():
            key = (source_id, target_id)
            if key in relation_map:
                existing = relation_map[key]
                if existing != relation:
                    issues.append(
                        f"Conflicting relations between {source_id} and {target_id}: "
                        f"{existing.value} vs {relation.value}"
                    )
            else:
                relation_map[key] = relation

        # Check start/end order consistency
        for event in self._events.values():
            if event.start_order is not None and event.end_order is not None:
                if event.end_order < event.start_order:
                    issues.append(
                        f"Event {event.event_id} has end_order ({event.end_order}) "
                        f"before start_order ({event.start_order})"
                    )

        return issues

    def export_to_dict(self) -> dict[str, Any]:
        """Export timeline to dictionary representation."""
        return {
            "timeline_id": self.timeline_id,
            "events": [event.to_dict() for event in self._events.values()],
            "relations": [
                {
                    "relation_id": rel_id,
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": relation_type.value,
                }
                for rel_id, (source_id, target_id, relation_type) in self._relations.items()
            ],
            "statistics": {
                "total_events": len(self._events),
                "total_relations": len(self._relations),
                "event_types": {et: len(ids) for et, ids in self._event_type_index.items()},
                "time_units": {tu.value: len(ids) for tu, ids in self._time_unit_index.items()},
            },
        }

    def clear(self) -> None:
        """Clear all events and relations from the timeline."""
        self._events.clear()
        self._relations.clear()
        self._event_type_index.clear()
        self._timestamp_index.clear()
        self._time_unit_index.clear()

        logger.info(f"Cleared timeline '{self.timeline_id}'")

    def stats(self) -> dict[str, Any]:
        """Get timeline statistics."""
        return {
            "total_events": len(self._events),
            "total_relations": len(self._relations),
            "event_types": {et: len(ids) for et, ids in self._event_type_index.items()},
            "time_units": {tu.value: len(ids) for tu, ids in self._time_unit_index.items()},
        }


# Factory function
def create_timeline_manager(
    timeline_id: str = "default",
    storage_path: Path | None = None,
) -> TimelineManager:
    """Create a timeline manager.

    Args:
        timeline_id: Unique identifier for the timeline
        storage_path: Optional storage path (default: data/timelines/{timeline_id})

    Returns:
        Initialized TimelineManager
    """
    if storage_path is None:
        # Default to data/timelines in project root
        project_root = Path(__file__).parent.parent.parent
        storage_path = project_root / "data" / "timelines" / timeline_id

    return TimelineManager(timeline_id, storage_path)


__all__ = [
    "TimelineManager",
    "TimelineEvent",
    "TimeUnit",
    "TemporalRelation",
    "create_timeline_manager",
]
