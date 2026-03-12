"""
NovelWriter LSP - Diagnostics Handler

This module provides real-time diagnostics validation using:
- Local ValidatorAgent for text-based validation
- Shared models (CharacterProfile, TimelineConflict) for semantic validation
- WriterAPI integration for accessing character data (optional)
"""

import logging
from typing import TYPE_CHECKING

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from novelwriter_lsp.agents import ValidatorAgent
from novelwriter_lsp.index import SymbolIndex

if TYPE_CHECKING:
    from novelwriter_lsp.server import NovelWriterLSP
    from novelwriter_shared.api import WriterAPI
    from novelwriter_shared.models import (
        CharacterProfile,
        CharacterStatus,
        EventType,
        TimelineConflict,
        ConflictType,
        CharacterTimelineEvent,
    )

logger = logging.getLogger(__name__)


def register_diagnostics(
    server: "NovelWriterLSP", 
    index: SymbolIndex,
    writer_api: "WriterAPI | None" = None,
) -> None:
    """
    Register the diagnostics feature with the LSP server.

    Args:
        server: The LSP server instance
        index: The symbol index (used for document tracking)
        writer_api: Optional WriterAPI for character data access
    """
    validator = ValidatorAgent()

    async def validate_document(uri: str, content: str) -> None:
        """
        Validate document and publish diagnostics.

        Args:
            uri: Document URI
            content: Document content
        """
        try:
            result = await validator.validate(uri, content)

            diagnostics = []

            for error in result.errors:
                diagnostic = types.Diagnostic(
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=0, character=1),
                    ),
                    message=error,
                    severity=types.DiagnosticSeverity.Error,
                    source="NovelWriter LSP",
                )
                diagnostics.append(diagnostic)

            for warning in result.warnings:
                diagnostic = types.Diagnostic(
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=0, character=1),
                    ),
                    message=warning,
                    severity=types.DiagnosticSeverity.Warning,
                    source="NovelWriter LSP",
                )
                diagnostics.append(diagnostic)

            if writer_api:
                semantic_diagnostics = await _validate_with_writer_api(content, writer_api)
                diagnostics.extend(semantic_diagnostics)

            server.publish_diagnostics(uri, diagnostics)
            logger.debug(f"Published {len(diagnostics)} diagnostics for {uri}")

        except Exception as e:
            logger.error(f"Error processing diagnostics for {uri}: {e}")
            server.publish_diagnostics(uri, [])

    server._custom_state["validate_document"] = validate_document


async def _validate_with_writer_api(
    content: str, 
    writer_api: "WriterAPI",
) -> list[types.Diagnostic]:
    """
    Validate content using WriterAPI and shared models.

    Performs semantic validation:
    - Timeline consistency using TimelineConflict detection
    - Character status consistency (alive/dead)
    - Birth/death chapter ordering

    Args:
        content: Document content
        writer_api: WriterAPI instance for accessing character data

    Returns:
        List of Diagnostic objects
    """
    diagnostics = []
    
    try:
        characters = await writer_api.list_characters()
        
        for profile in characters:
            conflicts = _detect_timeline_conflicts(profile)
            for conflict in conflicts:
                diagnostic = types.Diagnostic(
                    range=_estimate_conflict_range(conflict),
                    message=conflict.description,
                    severity=_get_severity(conflict.severity),
                    source="NovelWriter LSP (Timeline)",
                )
                diagnostics.append(diagnostic)
            
            status_issues = _check_status_consistency(profile)
            for issue in status_issues:
                diagnostic = types.Diagnostic(
                    range=types.Range(
                        start=types.Position(line=0, character=0),
                        end=types.Position(line=0, character=1),
                    ),
                    message=issue,
                    severity=types.DiagnosticSeverity.Warning,
                    source="NovelWriter LSP (Status)",
                )
                diagnostics.append(diagnostic)
                
    except Exception as e:
        logger.debug(f"WriterAPI validation failed: {e}")
    
    return diagnostics


def _detect_timeline_conflicts(profile: CharacterProfile) -> list[TimelineConflict]:
    """
    Detect timeline conflicts in a character's history.

    Checks for:
    - Multiple death events
    - Actions after death
    - Temporal paradoxes

    Args:
        profile: Character profile to check

    Returns:
        List of detected conflicts
    """
    conflicts = []
    
    death_events = profile.get_death_events()
    if len(death_events) > 1:
        conflicts.append(TimelineConflict(
            conflict_type=ConflictType.MULTIPLE_DEATHS,
            character_name=profile.name,
            event1=death_events[0],
            event2=death_events[1],
            description=f"Character '{profile.name}' has multiple death events in chapters {death_events[0].chapter} and {death_events[1].chapter}",
            severity="critical",
            suggested_resolution="Remove or correct duplicate death events",
        ))
    
    if profile.death_chapter:
        for event in profile.timeline:
            if event.chapter > profile.death_chapter and event.event_type not in [
                EventType.DEATH,
                EventType.MAJOR_EVENT,
            ]:
                conflicts.append(TimelineConflict(
                    conflict_type=ConflictType.ACTION_AFTER_DEATH,
                    character_name=profile.name,
                    event1=death_events[0] if death_events else profile.timeline[0],
                    event2=event,
                    description=f"Character '{profile.name}' has events after death (chapter {event.chapter} > death chapter {profile.death_chapter})",
                    severity="major",
                    suggested_resolution="Review timeline for post-death events",
                ))
    
    if profile.birth_chapter and profile.death_chapter:
        if profile.birth_chapter > profile.death_chapter:
            conflicts.append(TimelineConflict(
                conflict_type=ConflictType.TEMPORAL_PARADOX,
                character_name=profile.name,
                event1=CharacterTimelineEvent(
                    chapter=profile.birth_chapter,
                    event_type=EventType.BIRTH,
                    description=f"Birth at chapter {profile.birth_chapter}",
                ),
                event2=CharacterTimelineEvent(
                    chapter=profile.death_chapter,
                    event_type=EventType.DEATH,
                    description=f"Death at chapter {profile.death_chapter}",
                ),
                description=f"Character '{profile.name}' birth (chapter {profile.birth_chapter}) occurs after death (chapter {profile.death_chapter})",
                severity="critical",
                suggested_resolution="Correct birth/death chapter ordering",
            ))
    
    return conflicts


def _check_status_consistency(profile: CharacterProfile) -> list[str]:
    """
    Check character status consistency.

    Args:
        profile: Character profile to check

    Returns:
        List of warning messages
    """
    warnings = []
    
    if profile.current_status == CharacterStatus.DECEASED:
        if not profile.death_chapter and not profile.get_death_events():
            warnings.append(
                f"Character '{profile.name}' is marked as deceased but has no death chapter or death events"
            )
    
    if profile.current_status == CharacterStatus.ALIVE:
        if profile.death_chapter:
            warnings.append(
                f"Character '{profile.name}' is marked as alive but has a death chapter ({profile.death_chapter})"
            )
        death_events = profile.get_death_events()
        if death_events:
            warnings.append(
                f"Character '{profile.name}' is marked as alive but has death events"
            )
    
    return warnings


def _estimate_conflict_range(conflict: TimelineConflict) -> types.Range:
    """
    Estimate the range for a timeline conflict diagnostic.

    Args:
        conflict: The timeline conflict

    Returns:
        Estimated Range for the diagnostic
    """
    line = max(0, min(conflict.event1.chapter, conflict.event2.chapter))
    return types.Range(
        start=types.Position(line=line, character=0),
        end=types.Position(line=line, character=80),
    )


def _get_severity(severity_str: str) -> types.DiagnosticSeverity:
    """
    Map severity string to DiagnosticSeverity enum.

    Args:
        severity_str: Severity string ("critical", "major", "minor")

    Returns:
        Corresponding DiagnosticSeverity
    """
    mapping = {
        "critical": types.DiagnosticSeverity.Error,
        "major": types.DiagnosticSeverity.Warning,
        "minor": types.DiagnosticSeverity.Information,
    }
    return mapping.get(severity_str, types.DiagnosticSeverity.Warning)

