# src/studio/chat/agents.py
"""Agent management for chat interface."""

from dataclasses import dataclass
from enum import Enum


class AgentType(str, Enum):
    """Available agent types."""
    ROMANCE = "romance"
    SCIFI = "scifi"
    FANTASY = "fantasy"
    HISTORY = "history"
    MILITARY = "military"
    EDITOR = "editor"
    RESEARCH = "research"
    PUBLISHER = "publisher"
    ORCHESTRATOR = "orchestrator"
    ILLUSTRATOR = "illustrator"


@dataclass
class AgentInfo:
    """Information about an agent."""
    type: AgentType
    name: str
    icon: str
    description: str
    capabilities: list[str]

    def to_display(self) -> str:
        """Format for display."""
        return f"{self.icon} {self.name}"


# Agent definitions
AGENTS: dict[AgentType, AgentInfo] = {
    AgentType.ROMANCE: AgentInfo(
        type=AgentType.ROMANCE,
        name="Romance Writer",
        icon="✍️",
        description="Expert in romance and relationship-driven stories",
        capabilities=[
            "Write romantic scenes",
            "Develop character chemistry",
            "Create emotional arcs",
            "Dialogue optimization",
        ],
    ),
    AgentType.SCIFI: AgentInfo(
        type=AgentType.SCIFI,
        name="Sci-Fi Writer",
        icon="🚀",
        description="Expert in science fiction and futuristic worlds",
        capabilities=[
            "World-building",
            "Technology concepts",
            "Space opera",
            "Hard/soft sci-fi",
        ],
    ),
    AgentType.FANTASY: AgentInfo(
        type=AgentType.FANTASY,
        name="Fantasy Writer",
        icon="🔮",
        description="Expert in fantasy and magical worlds",
        capabilities=[
            "Magic systems",
            "Fantasy world-building",
            "Mythical creatures",
            "Epic quests",
        ],
    ),
    AgentType.HISTORY: AgentInfo(
        type=AgentType.HISTORY,
        name="History Writer",
        icon="📜",
        description="Expert in historical fiction",
        capabilities=[
            "Historical accuracy",
            "Period dialogue",
            "Historical events",
            "Cultural context",
        ],
    ),
    AgentType.MILITARY: AgentInfo(
        type=AgentType.MILITARY,
        name="Military Writer",
        icon="⚔️",
        description="Expert in military and war stories",
        capabilities=[
            "Battle scenes",
            "Military strategy",
            "War drama",
            "Tactical descriptions",
        ],
    ),
    AgentType.EDITOR: AgentInfo(
        type=AgentType.EDITOR,
        name="Editor",
        icon="📖",
        description="Review and improve content quality",
        capabilities=[
            "Grammar check",
            "Style consistency",
            "Pacing review",
            "Character consistency",
        ],
    ),
    AgentType.RESEARCH: AgentInfo(
        type=AgentType.RESEARCH,
        name="Market Research",
        icon="📊",
        description="Analyze market trends and competition",
        capabilities=[
            "Trend analysis",
            "Competitor research",
            "Tag optimization",
            "Audience insights",
        ],
    ),
    AgentType.PUBLISHER: AgentInfo(
        type=AgentType.PUBLISHER,
        name="Publisher",
        icon="📤",
        description="Manage publishing to platforms",
        capabilities=[
            "Multi-platform publishing",
            "Scheduling",
            "Status tracking",
            "Error recovery",
        ],
    ),
    AgentType.ORCHESTRATOR: AgentInfo(
        type=AgentType.ORCHESTRATOR,
        name="Orchestrator",
        icon="🎯",
        description="Coordinate all agents and workflows",
        capabilities=[
            "Project planning",
            "Task delegation",
            "Progress tracking",
            "Workflow optimization",
        ],
    ),
    AgentType.ILLUSTRATOR: AgentInfo(
        type=AgentType.ILLUSTRATOR,
        name="Illustrator",
        icon="🎨",
        description="Generate cover art and illustrations with AI",
        capabilities=[
            "Cover design prompts",
            "Character illustration",
            "Scene visualization",
            "AI image generation (GLM-4V)",
        ],
    ),
}


class AgentManager:
    """Manages agent selection and switching."""

    def __init__(self) -> None:
        self._current_agent: AgentType = AgentType.ROMANCE
        self._agents = list(AGENTS.keys())
        self._current_index = 0

    @property
    def current(self) -> AgentInfo:
        """Get current agent info."""
        return AGENTS[self._current_agent]

    @property
    def current_type(self) -> AgentType:
        """Get current agent type."""
        return self._current_agent

    def switch_to(self, agent_type: str | AgentType) -> AgentInfo:
        """Switch to a specific agent."""
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type.lower())
            except ValueError:
                # Try partial match
                for at in AgentType:
                    if at.value.startswith(agent_type.lower()):
                        agent_type = at
                        break
                else:
                    raise ValueError(f"Unknown agent: {agent_type}")

        self._current_agent = agent_type
        self._current_index = self._agents.index(agent_type)
        return self.current

    def next_agent(self) -> AgentInfo:
        """Switch to next agent (Tab forward)."""
        self._current_index = (self._current_index + 1) % len(self._agents)
        self._current_agent = self._agents[self._current_index]
        return self.current

    def prev_agent(self) -> AgentInfo:
        """Switch to previous agent (Tab backward)."""
        self._current_index = (self._current_index - 1) % len(self._agents)
        self._current_agent = self._agents[self._current_index]
        return self.current

    def list_agents(self) -> list[AgentInfo]:
        """List all agents."""
        return list(AGENTS.values())

    def get_agent_by_genre(self, genre: str) -> AgentInfo:
        """Get appropriate agent for a genre."""
        genre_map = {
            "romance": AgentType.ROMANCE,
            "scifi": AgentType.SCIFI,
            "fantasy": AgentType.FANTASY,
            "history": AgentType.HISTORY,
            "military": AgentType.MILITARY,
        }
        agent_type = genre_map.get(genre.lower(), AgentType.ROMANCE)
        return AGENTS[agent_type]

    def get_agent_display(self) -> str:
        """Get display string for current agent."""
        agent = self.current
        return f"[{agent.icon} {agent.name}]"

    def get_agent_matrix(self) -> str:
        """Get agent selection matrix like OpenCode's atlas."""
        lines = ["🤖 **Agent Selection**", ""]
        lines.append("| Agent | Description |")
        lines.append("|-------|-------------|")

        for agent in self.list_agents():
            current = "→" if agent.type == self._current_agent else " "
            lines.append(f"| {current} {agent.icon} **{agent.name}** | {agent.description} |")

        lines.append("")
        lines.append("💡 Press Tab to cycle agents, or /agent switch <name>")

        return "\n".join(lines)
