"""Character-related Pydantic schemas for the API."""

from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    """Schema for creating a new character."""

    name: str = Field(..., min_length=1, max_length=100)
    aliases: list[str] = Field(default_factory=list)
    tier: int = Field(default=1, ge=1, le=5, description="Character tier (1=main, 5=background)")
    bio: str = ""
    persona: str = ""
    mbti: str = ""
    profession: str = ""
    relationships: dict[str, str] = Field(default_factory=dict)
    interested_topics: list[str] = Field(default_factory=list)


class CharacterUpdate(BaseModel):
    """Schema for updating a character (all fields optional for partial updates)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    aliases: list[str] | None = None
    tier: int | None = Field(None, ge=1, le=5)
    bio: str | None = None
    persona: str | None = None
    mbti: str | None = None
    profession: str | None = None
    relationships: dict[str, str] | None = None
    interested_topics: list[str] | None = None
    current_status: str | None = None


class CharacterResponse(BaseModel):
    """Schema for character response data."""

    name: str
    aliases: list[str] = Field(default_factory=list)
    birth_chapter: int | None = None
    death_chapter: int | None = None
    current_status: str = "alive"
    tier: int = 1
    bio: str = ""
    persona: str = ""
    mbti: str = ""
    profession: str = ""
    relationships: dict[str, str] = Field(default_factory=dict)
    interested_topics: list[str] = Field(default_factory=list)


class CharacterListResponse(BaseModel):
    """Schema for list of characters."""

    project_id: str
    characters: list[CharacterResponse]
    total_count: int
    main_characters: int
    supporting_characters: int
