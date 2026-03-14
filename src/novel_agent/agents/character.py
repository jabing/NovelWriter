# src/agents/character.py
"""Character Agent - Character creation and management."""

import json
from typing import Any

from src.novel_agent.agents.base import AgentResult, BaseAgent
from src.novel_agent.agents.writers.base_writer import get_language_instruction
from src.novel_agent.llm.prompts import GENRE_PROMPTS


class CharacterAgent(BaseAgent):
    """Agent responsible for character creation and management.

    Creates:
    - Character profiles
    - Personality traits
    - Relationship maps
    - Development arcs
    """

    # Character archetypes by genre
    ARCHETYPES = {
        "scifi": ["explorer", "scientist", "pilot", "ai", "rebel", "diplomat"],
        "fantasy": ["warrior", "mage", "rogue", "healer", "ruler", "chosen"],
        "romance": ["hero", "heroine", "rival", "friend", "mentor", "ex"],
        "history": ["noble", "soldier", "scholar", "merchant", "peasant", "spy"],
        "military": ["commander", "soldier", "medic", "sniper", "pilot", "spy"],
    }

    def __init__(self, name: str = "Character Agent", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute character creation.

        Args:
            input_data: Must contain:
                - genre: str
                - outline: dict (from Plot Agent)
                - num_main_characters: int (optional, default 3)
                - num_supporting: int (optional, default 5)

        Returns:
            AgentResult with characters in data['characters']
        """
        try:
            genre = input_data.get("genre", "fantasy")
            outline = input_data.get("outline", {})
            num_main = input_data.get("num_main_characters", 3)
            num_supporting = input_data.get("num_supporting", 5)

            main_arc = outline.get("main_arc", {})
            language = input_data.get("language")

            # Generate main characters
            main_characters = []
            for i in range(num_main):
                role = "protagonist" if i == 0 else ("antagonist" if i == 1 else "main")
                char = await self.create_character(role, genre, main_arc, language=language)
                char["is_main"] = True
                main_characters.append(char)

            # Generate supporting characters
            supporting_characters = []
            for _i in range(num_supporting):
                char = await self.create_character("supporting", genre, main_arc, language=language)
                char["is_main"] = False
                supporting_characters.append(char)

            # Generate relationship map
            relationships = await self.generate_relationships(
                main_characters + supporting_characters
            )

            all_characters = main_characters + supporting_characters

            # Store to memory if available
            if self.memory:
                for char in all_characters:
                    await self.memory.store(
                        f"/memory/characters/{'main' if char['is_main'] else 'supporting'}/{char['id']}",
                        char,
                    )

            return AgentResult(
                success=True,
                data={
                    "characters": all_characters,
                    "main_characters": main_characters,
                    "supporting_characters": supporting_characters,
                    "relationships": relationships,
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Character generation failed: {str(e)}"],
            )

    async def create_character(
        self,
        role: str,
        genre: str,
        story_context: dict[str, Any],
        character_name: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Create a single character using LLM.

        Args:
            role: Character role (protagonist, antagonist, supporting, etc.)
            genre: Story genre
            story_context: Story context for consistency (should include title, premise, themes, tone)
            character_name: Optional specific name for the character

        Returns:
            Character profile
        """
        genre_prompt = GENRE_PROMPTS.get(genre, "")
        archetypes = self.ARCHETYPES.get(genre, [])

        system_prompt = f"""You are a character creation specialist for {genre} fiction.
{genre_prompt}

Create memorable, complex characters that drive story forward.
Your output must be valid JSON."""

        # Build rich context string
        context_parts = []
        if story_context.get("title"):
            context_parts.append(f"Story Title: {story_context['title']}")
        if story_context.get("premise"):
            context_parts.append(f"Premise: {story_context['premise']}")
        if story_context.get("themes"):
            context_parts.append(f"Themes: {', '.join(story_context['themes'])}")
        if story_context.get("tone"):
            context_parts.append(f"Tone: {story_context['tone']}")
        if story_context.get("target_audience"):
            context_parts.append(f"Target Audience: {story_context['target_audience']}")
        if story_context.get("content_rating"):
            context_parts.append(f"Content Rating: {story_context['content_rating']}")

        context_str = (
            "\n".join(context_parts)
            if context_parts
            else json.dumps(story_context, indent=2)[:1000]
        )

        # Build name instruction if provided
        name_instruction = (
            f"\nThe character's name MUST be: {character_name}" if character_name else ""
        )
        language_instruction = get_language_instruction(language)

        user_prompt = f"""Create a {role} character for a {genre} novel.
{language_instruction}
Story Context:
{context_str}
{name_instruction}

Genre archetypes: {", ".join(archetypes)}

Generate a JSON character profile with this structure:
{{
    "id": "char_xxx_001",
    "name": "Full Name",
    "role": "{role}",
    "age": 25,
    "occupation": "Character's job/role in world",
    "appearance": {{
        "height": "5'10\"",
        "build": "athletic",
        "hair": "brown, short",
        "eyes": "green",
        "distinctive_features": ["scar on left cheek", "always wears a specific ring"]
    }},
    "personality": {{
        "traits": ["brave", "curious", "stubborn"],
        "strengths": ["problem-solving", "empathy"],
        "weaknesses": ["impulsive", "trusts too easily"],
        "fears": ["failure", "abandonment"],
        "desires": ["purpose", "connection"]
    }},
    "background": "A paragraph describing their history and formative experiences",
    "goals": ["primary goal", "secondary goal"],
    "secrets": ["a secret they keep"],
    "mannerisms": ["habitual behaviors"],
    "voice": "Description of how they speak/communicate"
}}

Only output valid JSON, no other text."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            char = json.loads(content)
            # Ensure required fields
            char.setdefault("id", f"char_{role}_{hash(char.get('name', 'unknown')) % 10000:04d}")
            char.setdefault("role", role)
            # Override name if explicitly provided
            if character_name:
                char["name"] = character_name
            # Validate with constitution
            validation_results = await self.validate_with_constitution("character", char)
            for rule_id, is_valid, error in validation_results:
                if not is_valid:
                    # Log warning for now
                    print(
                        f"Constitution violation {rule_id} for character {char.get('name', 'unknown')}: {error}"
                    )
            # Register character name in glossary
            if char.get("name"):
                await self.register_with_glossary(
                    term=char["name"],
                    term_type="character",
                    definition=f"Character: {char.get('role', 'unknown')}. {char.get('background', '')[:200]}",
                    metadata={"character_id": char["id"]},
                )
            return char
        except json.JSONDecodeError:
            return {
                "id": f"char_{role}_001",
                "name": character_name or f"{role.title()} Character",
                "role": role,
                "personality": {"traits": [], "strengths": [], "weaknesses": []},
                "background": "To be developed",
                "_raw": response.content,
            }

    async def generate_relationships(
        self,
        characters: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate relationship map between characters.

        Args:
            characters: List of character profiles

        Returns:
            List of relationships
        """
        if len(characters) < 2:
            return []

        char_names = [c.get("name", c.get("id", "Unknown")) for c in characters]

        system_prompt = """You are a relationship dynamics expert.
Create meaningful, complex relationships that drive story conflict and growth.
Your output must be valid JSON."""

        user_prompt = f"""Generate relationships between these characters:
{json.dumps(char_names, indent=2)}

Create 5-10 relationships as a JSON array:
[
    {{
        "character1": "Character Name",
        "character2": "Other Character Name",
        "relationship_type": "family/friend/rival/romantic/mentor/etc",
        "dynamic": "Description of their dynamic",
        "tension": "Source of conflict or tension (if any)",
        "development": "How relationship might evolve"
    }}
]

Only output valid JSON, no other text."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return []

    async def create_development_arc(
        self,
        character: dict[str, Any],
        story_arc: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a character development arc.

        Args:
            character: Character profile
            story_arc: Main story arc

        Returns:
            Development arc for the character
        """
        system_prompt = """You are a character arc specialist.
Create satisfying character growth that parallels and enhances the main plot.
Your output must be valid JSON."""

        user_prompt = f"""Create a development arc for this character:
{json.dumps(character, indent=2)[:1000]}

Story arc:
{json.dumps(story_arc, indent=2)[:1000]}

Generate a JSON development arc:
{{
    "starting_point": "Where the character begins emotionally/psychologically",
    "internal_conflict": "Core internal struggle",
    "growth_moments": [
        {{"chapter": 5, "event": "What challenges their beliefs", "growth": "What they learn"}}
    ],
    "turning_point": "The moment of transformation",
    "ending_point": "Where the character ends up",
    "lessons_learned": ["Key lessons from their journey"]
}}

Only output valid JSON, no other text."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
