"""Search API router for global search functionality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_state
from src.studio.core.state import StudioState

router = APIRouter(prefix="/api", tags=["search"], redirect_slashes=False)


def _search_projects(query: str, state: StudioState) -> list[dict]:
    """Search projects by title, genre, or premise."""
    results = []
    query_lower = query.lower()
    
    for project in state.get_projects():
        matched = False
        match_reason = []
        
        if query_lower in project.title.lower():
            matched = True
            match_reason.append("title")
        if project.genre and query_lower in project.genre.lower():
            matched = True
            match_reason.append("genre")
        if project.premise and query_lower in project.premise.lower():
            matched = True
            match_reason.append("premise")
        
        if matched:
            results.append({
                "id": project.id,
                "title": project.title,
                "type": "project",
                "genre": project.genre,
                "status": project.status.value,
                "progress": f"{project.completed_chapters}/{project.target_chapters} chapters",
                "match_reason": match_reason,
                "url": f"/projects/{project.id}",
            })
    
    return results


def _search_chapters(query: str, novel_id: str | None = None) -> list[dict]:
    """Search chapters by title or content."""
    results = []
    query_lower = query.lower()
    
    # Get all novels to search
    novels_dir = Path("data/openviking/memory/novels")
    if not novels_dir.exists():
        return results
    
    novel_dirs = [novels_dir / novel_id] if novel_id else [d for d in novels_dir.iterdir() if d.is_dir()]
    
    for novel_dir in novel_dirs:
        if not novel_dir.exists():
            continue
        
        # Load novel metadata
        novel_data = {}
        novel_info_path = novel_dir / "novel_info.json"
        if novel_info_path.exists():
            with open(novel_info_path, encoding="utf-8") as f:
                novel_data = json.load(f)
        
        novel_title = novel_data.get("title", novel_dir.name)
        
        # Search chapters
        chapters_dir = novel_dir / "chapters"
        if not chapters_dir.exists():
            continue
        
        for chapter_file in sorted(chapters_dir.glob("chapter_*.json")):
            try:
                with open(chapter_file, encoding="utf-8") as f:
                    chapter_data = json.load(f)
                
                chapter_title = chapter_data.get("title", f"Chapter {chapter_data.get('number', '?')}")
                chapter_content = chapter_data.get("content", "")
                
                matched = False
                match_reason = []
                
                if query_lower in chapter_title.lower():
                    matched = True
                    match_reason.append("title")
                if query_lower in chapter_content.lower():
                    matched = True
                    match_reason.append("content")
                
                if matched:
                    # Truncate content for preview
                    preview_start = chapter_content.lower().find(query_lower)
                    if preview_start > 0:
                        preview_start = max(0, preview_start - 50)
                        preview_end = min(len(chapter_content), preview_start + 200)
                        preview = chapter_content[preview_start:preview_end]
                        if preview_start > 0:
                            preview = "..." + preview
                        if preview_end < len(chapter_content):
                            preview = preview + "..."
                    else:
                        preview = chapter_content[:200] + "..." if len(chapter_content) > 200 else chapter_content
                    
                    results.append({
                        "id": f"{novel_dir.name}/{chapter_file.stem}",
                        "title": chapter_title,
                        "type": "chapter",
                        "novel_id": novel_dir.name,
                        "novel_title": novel_title,
                        "chapter_number": chapter_data.get("number"),
                        "preview": preview,
                        "match_reason": match_reason,
                        "url": f"/writing?novel={novel_dir.name}&chapter={chapter_data.get('number', '')}",
                    })
            except Exception:
                continue
    
    return results


def _search_characters(query: str, novel_id: str | None = None) -> list[dict]:
    """Search characters by name, aliases, bio, or persona."""
    results = []
    query_lower = query.lower()
    
    # Get all novels to search
    novels_dir = Path("data/openviking/memory/novels")
    if not novels_dir.exists():
        return results
    
    novel_dirs = [novels_dir / novel_id] if novel_id else [d for d in novels_dir.iterdir() if d.is_dir()]
    
    for novel_dir in novel_dirs:
        if not novel_dir.exists():
            continue
        
        # Load novel metadata
        novel_data = {}
        novel_info_path = novel_dir / "novel_info.json"
        if novel_info_path.exists():
            with open(novel_info_path, encoding="utf-8") as f:
                novel_data = json.load(f)
        
        novel_title = novel_data.get("title", novel_dir.name)
        
        # Search characters
        characters_dir = novel_dir / "characters"
        if not characters_dir.exists():
            continue
        
        for char_file in sorted(characters_dir.glob("*.json")):
            try:
                with open(char_file, encoding="utf-8") as f:
                    char_data = json.load(f)
                
                char_name = char_data.get("name", char_file.stem)
                char_aliases = char_data.get("aliases", [])
                char_bio = char_data.get("bio", "")
                char_persona = char_data.get("persona", "")
                char_profession = char_data.get("profession", "")
                
                matched = False
                match_reason = []
                
                if query_lower in char_name.lower():
                    matched = True
                    match_reason.append("name")
                
                for alias in char_aliases:
                    if query_lower in alias.lower():
                        matched = True
                        match_reason.append("alias")
                        break
                
                if char_profession and query_lower in char_profession.lower():
                    matched = True
                    match_reason.append("profession")
                
                if char_bio and query_lower in char_bio.lower():
                    matched = True
                    match_reason.append("bio")
                
                if char_persona and query_lower in char_persona.lower():
                    matched = True
                    match_reason.append("persona")
                
                if matched:
                    results.append({
                        "id": f"{novel_dir.name}/{char_file.stem}",
                        "name": char_name,
                        "type": "character",
                        "novel_id": novel_dir.name,
                        "novel_title": novel_title,
                        "tier": char_data.get("tier", 1),
                        "profession": char_profession,
                        "bio_preview": char_bio[:100] + "..." if len(char_bio) > 100 else char_bio,
                        "match_reason": match_reason,
                        "url": f"/characters?novel={novel_dir.name}&character={char_file.stem}",
                    })
            except Exception:
                continue
    
    return results


@router.get("/search", response_model=dict)
def search(
    state: Annotated[StudioState, Depends(get_state)],
    q: str = Query(..., min_length=1, description="Search query"),
    type: str | None = Query(None, description="Filter by type: project, chapter, character, or all"),
    novel_id: str | None = Query(None, description="Filter by novel ID"),
) -> dict:
    """
    Global search across projects, chapters, and characters.
    
    Args:
        q: Search query string (minimum 1 character)
        type: Optional filter by type (project, chapter, character, or all)
        novel_id: Optional filter by specific novel ID
    
    Returns:
        Dictionary with search results organized by type
    """
    results = {
        "query": q,
        "total_results": 0,
        "projects": [],
        "chapters": [],
        "characters": [],
    }
    
    try:
        # Search projects (always search if type is 'project' or 'all' or not specified)
        if type in [None, "all", "project"]:
            if state:
                results["projects"] = _search_projects(q, state)
        
        # Search chapters
        if type in [None, "all", "chapter"]:
            results["chapters"] = _search_chapters(q, novel_id)
        
        # Search characters
        if type in [None, "all", "character"]:
            results["characters"] = _search_characters(q, novel_id)
        
        # Calculate total
        results["total_results"] = (
            len(results["projects"]) + len(results["chapters"]) + len(results["characters"])
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
