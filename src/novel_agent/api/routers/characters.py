"""Characters API router for character management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.novel_agent.api.dependencies import get_state
from src.novel_agent.api.schemas.characters import (
    CharacterCreate,
    CharacterListResponse,
    CharacterResponse,
    CharacterUpdate,
)
from src.novel_agent.studio.core.state import StudioState

router = APIRouter(prefix="/api/novels", tags=["characters"], redirect_slashes=False)


def _get_characters_dir(novel_id: str) -> Path:
    return Path(f"data/openviking/memory/novels/{novel_id}/characters")


def _load_character_file(char_path: Path) -> CharacterResponse | None:
    if not char_path.exists():
        return None

    if char_path.suffix == ".json":
        try:
            with open(char_path, encoding="utf-8") as f:
                data = json.load(f)
            return CharacterResponse(
                name=data.get("name", char_path.stem),
                aliases=data.get("aliases", []),
                birth_chapter=data.get("birth_chapter"),
                death_chapter=data.get("death_chapter"),
                current_status=data.get("current_status", "alive"),
                tier=data.get("tier", 1),
                bio=data.get("bio", ""),
                persona=data.get("persona", ""),
                mbti=data.get("mbti", ""),
                profession=data.get("profession", ""),
                relationships=data.get("relationships", {}),
                interested_topics=data.get("interested_topics", []),
            )
        except Exception:
            return None

    return None


@router.get("/{novel_id}/characters", response_model=CharacterListResponse)
def list_characters(
    novel_id: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> CharacterListResponse:
    characters_dir = _get_characters_dir(novel_id)
    characters: list[CharacterResponse] = []

    if characters_dir.exists():
        for char_file in sorted(characters_dir.glob("*.json")):
            char = _load_character_file(char_file)
            if char:
                characters.append(char)

    main_count = sum(1 for c in characters if c.tier == 1)
    supporting_count = sum(1 for c in characters if c.tier > 1)

    return CharacterListResponse(
        project_id=novel_id,
        characters=characters,
        total_count=len(characters),
        main_characters=main_count,
        supporting_characters=supporting_count,
    )


@router.get("/{novel_id}/characters/{name}", response_model=CharacterResponse)
def get_character(
    novel_id: str,
    name: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> CharacterResponse:
    characters_dir = _get_characters_dir(novel_id)

    for ext in [".json", ".md"]:
        char_path = characters_dir / f"{name}{ext}"
        if char_path.exists():
            char = _load_character_file(char_path)
            if char:
                return char

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Character '{name}' not found for novel {novel_id}",
    )


@router.post(
    "/{novel_id}/characters",
    response_model=CharacterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_character(
    novel_id: str,
    character_data: CharacterCreate,
    state: Annotated[StudioState, Depends(get_state)],
) -> CharacterResponse:
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )

    characters_dir = _get_characters_dir(novel_id)
    characters_dir.mkdir(parents=True, exist_ok=True)

    char_path = characters_dir / f"{character_data.name}.json"
    if char_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Character '{character_data.name}' already exists",
        )

    char_data = {
        "name": character_data.name,
        "aliases": character_data.aliases,
        "tier": character_data.tier,
        "bio": character_data.bio,
        "persona": character_data.persona,
        "mbti": character_data.mbti,
        "profession": character_data.profession,
        "relationships": character_data.relationships,
        "interested_topics": character_data.interested_topics,
        "current_status": "alive",
    }

    with open(char_path, "w", encoding="utf-8") as f:
        json.dump(char_data, f, indent=2, ensure_ascii=False)

    return CharacterResponse(
        name=character_data.name,
        aliases=character_data.aliases,
        birth_chapter=None,
        death_chapter=None,
        current_status="alive",
        tier=character_data.tier,
        bio=character_data.bio,
        persona=character_data.persona,
        mbti=character_data.mbti,
        profession=character_data.profession,
        relationships=character_data.relationships,
        interested_topics=character_data.interested_topics,
    )


@router.put(
    "/{novel_id}/characters/{character_id}",
    response_model=CharacterResponse,
)
def update_character(
    novel_id: str,
    character_id: str,
    character_data: CharacterUpdate,
    state: Annotated[StudioState, Depends(get_state)],
) -> CharacterResponse:
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )

    characters_dir = _get_characters_dir(novel_id)
    char_path = characters_dir / f"{character_id}.json"

    if not char_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character '{character_id}' not found for novel {novel_id}",
        )

    with open(char_path, encoding="utf-8") as f:
        existing_data = json.load(f)

    update_data = character_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if value is not None:
            existing_data[key] = value

    existing_data["updated_at"] = __import__("datetime").datetime.now().isoformat()

    with open(char_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    return CharacterResponse(
        name=existing_data.get("name", character_id),
        aliases=existing_data.get("aliases", []),
        birth_chapter=existing_data.get("birth_chapter"),
        death_chapter=existing_data.get("death_chapter"),
        current_status=existing_data.get("current_status", "alive"),
        tier=existing_data.get("tier", 1),
        bio=existing_data.get("bio", ""),
        persona=existing_data.get("persona", ""),
        mbti=existing_data.get("mbti", ""),
        profession=existing_data.get("profession", ""),
        relationships=existing_data.get("relationships", {}),
        interested_topics=existing_data.get("interested_topics", []),
    )


@router.delete(
    "/{novel_id}/characters/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_character(
    novel_id: str,
    character_id: str,
    state: Annotated[StudioState, Depends(get_state)],
) -> None:
    project = state.get_project(novel_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Novel {novel_id} not found",
        )

    characters_dir = _get_characters_dir(novel_id)
    char_path = characters_dir / f"{character_id}.json"

    if not char_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character '{character_id}' not found for novel {novel_id}",
        )

    with open(char_path, encoding="utf-8") as f:
        deleted_char = json.load(f)

    deleted_name = deleted_char.get("name", character_id)
    deleted_aliases = deleted_char.get("aliases", [])

    if characters_dir.exists():
        for other_char_file in characters_dir.glob("*.json"):
            if other_char_file == char_path:
                continue

            with open(other_char_file, encoding="utf-8") as f:
                other_data = json.load(f)

            relationships = other_data.get("relationships", {})
            updated = False

            if deleted_name in relationships:
                del relationships[deleted_name]
                updated = True

            for alias in deleted_aliases:
                if alias in relationships:
                    del relationships[alias]
                    updated = True

            if updated:
                other_data["relationships"] = relationships
                with open(other_char_file, "w", encoding="utf-8") as f:
                    json.dump(other_data, f, indent=2, ensure_ascii=False)

    char_path.unlink()
