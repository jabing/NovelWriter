# src/agents/worldbuilding.py
"""Worldbuilding Agent - World creation and consistency."""

import json
from typing import Any

from src.agents.base import AgentResult, BaseAgent
from src.llm.prompts import GENRE_PROMPTS


class WorldbuildingAgent(BaseAgent):
    """Agent responsible for world creation and maintenance.

    Creates:
    - World rules and laws
    - Geography and locations
    - Technology/magic systems
    - Social structures
    """

    # World elements by genre
    WORLD_ELEMENTS = {
        "scifi": ["technology", "space", "aliens", "governments", "corporations"],
        "fantasy": ["magic", "races", "gods", "geography", "history"],
        "romance": ["society", "culture", "economics", "locations"],
        "history": ["politics", "military", "culture", "economics", "geography"],
        "military": ["military", "politics", "technology", "geography", "logistics"],
    }

    def __init__(self, name: str = "Worldbuilding Agent", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute worldbuilding.

        Args:
            input_data: Must contain:
                - genre: str
                - outline: dict (from Plot Agent)

        Returns:
            AgentResult with world settings in data['world']
        """
        try:
            genre = input_data.get("genre", "fantasy")
            outline = input_data.get("outline", {})
            main_arc = outline.get("main_arc", {})

            # Generate core world rules
            rules = await self.create_world_rules(genre, main_arc)

            # Generate locations
            locations = await self.generate_locations(genre, main_arc)

            # Generate social structures
            society = await self.generate_society(genre, main_arc)

            # Generate history/timeline
            history = await self.generate_history(genre, main_arc)

            world = {
                "genre": genre,
                "rules": rules,
                "locations": locations,
                "society": society,
                "history": history,
            }

            # Store to memory if available
            if self.memory:
                await self.memory.store("/memory/world/rules", rules)
                await self.memory.store("/memory/world/locations", locations)
                await self.memory.store("/memory/world/society", society)
                await self.memory.store("/memory/world/history", history)

            return AgentResult(
                success=True,
                data={"world": world},
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Worldbuilding failed: {str(e)}"],
            )

    async def create_world_rules(
        self,
        genre: str,
        story_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Create world rules and systems using LLM.

        Args:
            genre: Story genre
            story_context: Story context

        Returns:
            World rules
        """
        genre_prompt = GENRE_PROMPTS.get(genre, "")
        elements = self.WORLD_ELEMENTS.get(genre, [])

        system_prompt = f"""You are a worldbuilding expert for {genre} fiction.
{genre_prompt}

Create consistent, believable world systems that serve the story.
Your output must be valid JSON."""

        context_str = json.dumps(story_context, indent=2)[:1000]

        # Genre-specific prompts
        genre_focus = {
            "scifi": "technology levels, physics limitations, space travel rules",
            "fantasy": "magic system rules, costs, limitations, sources",
            "romance": "social conventions, economic systems, cultural norms",
            "history": "historical accuracy, political systems, period details",
            "military": "military organization, technology, logistics, command structure",
        }

        user_prompt = f"""Create the core rules/systems for a {genre} world.

Story Context:
{context_str}

Focus on: {genre_focus.get(genre, 'general world rules')}
Key elements: {', '.join(elements)}

Generate a JSON world rules structure:
{{
    "name": "World/Setting Name",
    "time_period": "When this takes place",
    "technology_level": "Level of technology",
    "core_rules": [
        {{
            "rule": "Name of rule/system",
            "description": "How it works",
            "limitations": "What it cannot do",
            "consequences": "Impact on society/story"
        }}
    ],
    "taboos": ["What is forbidden in this world"],
    "opportunities": ["What is possible in this world"],
    "constraints": ["What limits characters in this world"]
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
            world_rules = json.loads(content)
            # Validate with constitution
            validation_results = await self.validate_with_constitution("world", world_rules)
            for rule_id, is_valid, error in validation_results:
                if not is_valid:
                    print(f"Constitution violation {rule_id} for world rules: {error}")
            # Register world name in glossary
            if world_rules.get('name'):
                await self.register_with_glossary(
                    term=world_rules['name'],
                    term_type="location",
                    definition=f"World setting for {genre} story.",
                    metadata={"genre": genre, "time_period": world_rules.get('time_period', 'unknown')}
                )
            return world_rules
        except json.JSONDecodeError:
            return {
                "name": f"{genre.title()} World",
                "core_rules": [],
                "_raw": response.content,
            }

    async def generate_locations(
        self,
        genre: str,
        story_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate key locations for the story.

        Args:
            genre: Story genre
            story_context: Story context

        Returns:
            List of location descriptions
        """
        system_prompt = """You are a location design specialist.
Create vivid, functional locations that serve the story's needs.
Your output must be valid JSON."""

        context_str = json.dumps(story_context, indent=2)[:800]

        user_prompt = f"""Create 5-8 key locations for a {genre} story.

Story Context:
{context_str}

Generate a JSON array of locations:
[
    {{
        "id": "loc_001",
        "name": "Location Name",
        "type": "city/ship/forest/etc",
        "description": "Visual and atmospheric description",
        "significance": "Why this location matters to the story",
        "inhabitants": "Who lives/works here",
        "secrets": "Hidden aspects of this location",
        "atmosphere": "Mood and feeling of the place"
    }}
]

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
            locations = json.loads(content)
            # Validate with constitution
            if locations:
                validation_results = await self.validate_with_constitution("world", locations[0])
                for rule_id, is_valid, error in validation_results:
                    if not is_valid:
                        print(f"Constitution violation {rule_id} for location: {error}")
                # Register location names in glossary
                for loc in locations:
                    if loc.get('name'):
                        await self.register_with_glossary(
                            term=loc['name'],
                            term_type="location",
                            definition=f"{loc.get('type', 'location')}: {loc.get('description', '')[:200]}",
                            metadata={"genre": genre, "location_id": loc.get('id', '')}
                        )
            return locations
        except json.JSONDecodeError:
            return []

    async def generate_society(
        self,
        genre: str,
        story_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate social structures.

        Args:
            genre: Story genre
            story_context: Story context

        Returns:
            Society structure
        """
        system_prompt = """You are a society and culture design expert.
Create believable social structures that create story opportunities.
Your output must be valid JSON."""

        user_prompt = f"""Create the society structure for a {genre} world.

Generate a JSON society structure:
{{
    "government": {{
        "type": "Form of government",
        "power_structure": "How power is distributed",
        "key_figures": ["Important leaders/factions"]
    }},
    "social_classes": [
        {{
            "name": "Class name",
            "description": "Who they are",
            "privileges": "What they have",
            "restrictions": "What they cannot do"
        }}
    ],
    "economy": {{
        "type": "Economic system",
        "key_resources": ["Important resources"],
        "trade": "How commerce works"
    }},
    "culture": {{
        "values": ["What society values"],
        "traditions": ["Important customs"],
        "taboos": ["What is forbidden"]
    }},
    "conflicts": ["Sources of social tension"]
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
            society = json.loads(content)
            # Validate with constitution
            validation_results = await self.validate_with_constitution("world", society)
            for rule_id, is_valid, error in validation_results:
                if not is_valid:
                    print(f"Constitution violation {rule_id} for society: {error}")
            return society
        except json.JSONDecodeError:
            return {}

    async def generate_history(
        self,
        genre: str,
        story_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate world history/timeline.

        Args:
            genre: Story genre
            story_context: Story context

        Returns:
            History structure
        """
        system_prompt = """You are a history and timeline expert.
Create compelling backstories that add depth to the world.
Your output must be valid JSON."""

        user_prompt = f"""Create a brief history for a {genre} world.

Generate a JSON history structure:
{{
    "ancient_history": "Brief overview of distant past",
    "recent_history": "Events in the last generation",
    "key_events": [
        {{
            "name": "Event name",
            "when": "When it happened",
            "description": "What happened",
            "consequences": "How it shaped the present"
        }}
    ],
    "legends": ["Myths and stories people tell"],
    "ongoing_tensions": ["Unresolved historical conflicts"]
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
            history = json.loads(content)
            # Validate with constitution
            validation_results = await self.validate_with_constitution("world", history)
            for rule_id, is_valid, error in validation_results:
                if not is_valid:
                    print(f"Constitution violation {rule_id} for history: {error}")
            return history
        except json.JSONDecodeError:
            return {}
