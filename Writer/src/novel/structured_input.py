"""Structured input system for AI novel writing.

Provides code-based interfaces for specifying writing tasks with clear
parameters, constraints, and expected outputs. This system enables
deterministic, repeatable novel generation by treating writing as
a structured data transformation rather than free-form text generation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SceneType(str, Enum):
    """Type of scene."""

    DIALOGUE = "dialogue"
    ACTION = "action"
    DESCRIPTION = "description"
    TRANSITION = "transition"
    FLASHBACK = "flashback"
    INTROSPECTION = "introspection"
    CLIMAX = "climax"
    RESOLUTION = "resolution"


class EmotionalTone(str, Enum):
    """Emotional tone for a scene."""

    JOYFUL = "joyful"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    NEUTRAL = "neutral"
    SUSPENSEFUL = "suspenseful"
    ROMANTIC = "romantic"
    HOPEFUL = "hopeful"
    DESPAIRING = "despairing"
    TRIUMPHANT = "triumphant"


class Pacing(str, Enum):
    """Pacing for a scene."""

    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    VARIED = "varied"


@dataclass
class CharacterInScene:
    """Character specification for a scene."""

    name: str
    emotional_state: str = "neutral"
    goal: str | None = None
    relationship_to_others: dict[str, str] = field(default_factory=dict)
    physical_state: str = "normal"
    hidden_motivation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "emotional_state": self.emotional_state,
            "goal": self.goal,
            "relationship_to_others": self.relationship_to_others,
            "physical_state": self.physical_state,
            "hidden_motivation": self.hidden_motivation,
        }


@dataclass
class LocationSpec:
    """Location specification for a scene."""

    name: str
    description: str
    mood: str = "neutral"
    sensory_details: dict[str, str] = field(default_factory=dict)
    significant_objects: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "mood": self.mood,
            "sensory_details": self.sensory_details,
            "significant_objects": self.significant_objects,
        }


@dataclass
class StructuredTask:
    """Structured writing task specification."""

    # Core identification
    task_id: str
    chapter_number: int
    scene_number: int
    scene_type: SceneType

    # Content specification
    location: LocationSpec
    characters: list[CharacterInScene] = field(default_factory=list)

    # Narrative elements
    core_conflict: str = ""
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    pacing: Pacing = Pacing.MEDIUM

    # Constraints and requirements
    required_details: list[str] = field(default_factory=list)
    forbidden_elements: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)

    # Continuity tracking
    previous_scene_summary: str = ""
    next_scene_hint: str = ""

    # Metadata
    word_count_target: int = 800
    time_constraint: str | None = None

    def to_prompt(self) -> str:
        """Convert to LLM prompt."""
        prompt_parts = [
            "【STRUCTURED WRITING TASK】",
            f"TASK ID: {self.task_id}",
            f"CHAPTER: {self.chapter_number}, SCENE: {self.scene_number} ({self.scene_type.value})",
            "",
            "【LOCATION】",
            f"Name: {self.location.name}",
            f"Description: {self.location.description}",
        ]

        if self.location.mood != "neutral":
            prompt_parts.append(f"Mood: {self.location.mood}")

        if self.location.sensory_details:
            sensory_text = ", ".join(f"{k}: {v}" for k, v in self.location.sensory_details.items())
            prompt_parts.append(f"Sensory details: {sensory_text}")

        if self.location.significant_objects:
            prompt_parts.append(
                f"Significant objects: {', '.join(self.location.significant_objects)}"
            )

        prompt_parts.append("")

        if self.characters:
            prompt_parts.append("【CHARACTERS】")
            for char in self.characters:
                char_desc = f"- {char.name} ({char.emotional_state})"
                if char.goal:
                    char_desc += f" | Goal: {char.goal}"
                if char.physical_state != "normal":
                    char_desc += f" | Physical: {char.physical_state}"
                prompt_parts.append(char_desc)

            # Add relationships if specified
            relationships = []
            for char in self.characters:
                for other, relation in char.relationship_to_others.items():
                    relationships.append(f"{char.name} ↔ {other}: {relation}")

            if relationships:
                prompt_parts.append("")
                prompt_parts.append("Relationships:")
                for rel in relationships:
                    prompt_parts.append(f"  {rel}")

            prompt_parts.append("")

        if self.core_conflict:
            prompt_parts.append("【CORE CONFLICT】")
            prompt_parts.append(self.core_conflict)
            prompt_parts.append("")

        prompt_parts.append(f"【EMOTIONAL TONE】 {self.emotional_tone.value}")
        prompt_parts.append(f"【PACING】 {self.pacing.value}")

        if self.required_details:
            prompt_parts.append("")
            prompt_parts.append("【REQUIRED DETAILS】")
            for detail in self.required_details:
                prompt_parts.append(f"- {detail}")

        if self.must_include:
            prompt_parts.append("")
            prompt_parts.append("【MUST INCLUDE】")
            for item in self.must_include:
                prompt_parts.append(f"- {item}")

        if self.forbidden_elements:
            prompt_parts.append("")
            prompt_parts.append("【FORBIDDEN】")
            for item in self.forbidden_elements:
                prompt_parts.append(f"- {item}")

        if self.previous_scene_summary:
            prompt_parts.append("")
            prompt_parts.append("【PREVIOUS SCENE】")
            prompt_parts.append(self.previous_scene_summary)

        if self.next_scene_hint:
            prompt_parts.append("")
            prompt_parts.append("【NEXT SCENE HINT】")
            prompt_parts.append(self.next_scene_hint)

        prompt_parts.append("")
        prompt_parts.append(f"【WORD COUNT TARGET】 {self.word_count_target} words")

        if self.time_constraint:
            prompt_parts.append(f"【TIME CONSTRAINT】 {self.time_constraint}")

        return "\n".join(prompt_parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "chapter_number": self.chapter_number,
            "scene_number": self.scene_number,
            "scene_type": self.scene_type.value,
            "location": self.location.to_dict(),
            "characters": [char.to_dict() for char in self.characters],
            "core_conflict": self.core_conflict,
            "emotional_tone": self.emotional_tone.value,
            "pacing": self.pacing.value,
            "required_details": self.required_details,
            "forbidden_elements": self.forbidden_elements,
            "must_include": self.must_include,
            "previous_scene_summary": self.previous_scene_summary,
            "next_scene_hint": self.next_scene_hint,
            "word_count_target": self.word_count_target,
            "time_constraint": self.time_constraint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredTask":
        """Create from dictionary."""
        # Convert nested objects
        location_data = data.get("location", {})
        location = LocationSpec(
            name=location_data.get("name", ""),
            description=location_data.get("description", ""),
            mood=location_data.get("mood", "neutral"),
            sensory_details=location_data.get("sensory_details", {}),
            significant_objects=location_data.get("significant_objects", []),
        )

        characters = []
        for char_data in data.get("characters", []):
            character = CharacterInScene(
                name=char_data.get("name", ""),
                emotional_state=char_data.get("emotional_state", "neutral"),
                goal=char_data.get("goal"),
                relationship_to_others=char_data.get("relationship_to_others", {}),
                physical_state=char_data.get("physical_state", "normal"),
                hidden_motivation=char_data.get("hidden_motivation"),
            )
            characters.append(character)

        return cls(
            task_id=data["task_id"],
            chapter_number=data["chapter_number"],
            scene_number=data["scene_number"],
            scene_type=SceneType(data.get("scene_type", "action")),
            location=location,
            characters=characters,
            core_conflict=data.get("core_conflict", ""),
            emotional_tone=EmotionalTone(data.get("emotional_tone", "neutral")),
            pacing=Pacing(data.get("pacing", "medium")),
            required_details=data.get("required_details", []),
            forbidden_elements=data.get("forbidden_elements", []),
            must_include=data.get("must_include", []),
            previous_scene_summary=data.get("previous_scene_summary", ""),
            next_scene_hint=data.get("next_scene_hint", ""),
            word_count_target=data.get("word_count_target", 800),
            time_constraint=data.get("time_constraint"),
        )


class StructuredInputSystem:
    """System for managing structured writing tasks."""

    def __init__(self):
        self.tasks: dict[str, StructuredTask] = {}

    def create_task(
        self,
        chapter_number: int,
        scene_number: int,
        scene_type: SceneType,
        location: LocationSpec,
        characters: list[CharacterInScene] | None = None,
        **kwargs,
    ) -> StructuredTask:
        """Create a new structured task."""
        task_id = f"ch{chapter_number:03d}_sc{scene_number:03d}_{scene_type.value}"

        task = StructuredTask(
            task_id=task_id,
            chapter_number=chapter_number,
            scene_number=scene_number,
            scene_type=scene_type,
            location=location,
            characters=characters or [],
            **kwargs,
        )

        self.tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> StructuredTask | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def save_task(self, task: StructuredTask, filepath: str) -> None:
        """Save task to JSON file."""
        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)

    def load_task(self, filepath: str) -> StructuredTask:
        """Load task from JSON file."""
        import json

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        return StructuredTask.from_dict(data)

    def validate_task(self, task: StructuredTask) -> list[str]:
        """Validate a task for completeness and consistency."""
        issues = []

        # Check required fields
        if not task.location.name:
            issues.append("Location name is required")

        if not task.characters:
            issues.append("At least one character is required")
        else:
            for i, char in enumerate(task.characters):
                if not char.name:
                    issues.append(f"Character {i + 1} has no name")

        # Check word count target
        if task.word_count_target < 100:
            issues.append(f"Word count target ({task.word_count_target}) is too low")
        elif task.word_count_target > 5000:
            issues.append(f"Word count target ({task.word_count_target}) is too high")

        # Check scene type compatibility
        if task.scene_type == SceneType.DIALOGUE and not task.characters:
            issues.append("Dialogue scene requires characters")

        if task.scene_type == SceneType.ACTION and task.pacing == Pacing.SLOW:
            issues.append("Action scene with slow pacing may be inconsistent")

        return issues


# Example usage function
def create_example_task() -> StructuredTask:
    """Create an example structured task for testing."""
    location = LocationSpec(
        name="Ancient Forest Clearing",
        description="A circular clearing surrounded by towering ancient trees. Moonlight filters through the canopy, creating dappled patterns on the mossy ground.",
        mood="mysterious",
        sensory_details={
            "smell": "damp earth and pine",
            "sound": "distant owl hoots and rustling leaves",
            "sight": "moonlight through trees",
            "touch": "cool, damp air",
        },
        significant_objects=["stone altar", "carved runes", "broken sword"],
    )

    characters = [
        CharacterInScene(
            name="Kael",
            emotional_state="determined",
            goal="Retrieve the lost artifact",
            physical_state="injured but persistent",
            relationship_to_others={"Elara": "protector"},
        ),
        CharacterInScene(
            name="Elara",
            emotional_state="concerned",
            goal="Protect Kael",
            physical_state="alert and ready",
            relationship_to_others={"Kael": "ward"},
        ),
    ]

    task = StructuredTask(
        task_id="ch001_sc001_action",
        chapter_number=1,
        scene_number=1,
        scene_type=SceneType.ACTION,
        location=location,
        characters=characters,
        core_conflict="Kael and Elara must retrieve the artifact before the cultists arrive",
        emotional_tone=EmotionalTone.SUSPENSEFUL,
        pacing=Pacing.FAST,
        required_details=[
            "Kael's injury should affect his movements",
            "Elara should use her archery skills",
            "The stone altar should be described in detail",
        ],
        forbidden_elements=[
            "Modern technology",
            "Explicit gore",
            "Deus ex machina solutions",
        ],
        previous_scene_summary="After escaping the village guards, Kael and Elara fled into the ancient forest.",
        next_scene_hint="The artifact's power will be revealed, attracting unwanted attention.",
        word_count_target=1200,
    )

    return task


if __name__ == "__main__":
    # Example usage
    task = create_example_task()
    print(task.to_prompt())
    print("\n" + "=" * 50 + "\n")

    # Validate the task
    system = StructuredInputSystem()
    issues = system.validate_task(task)
    if issues:
        print("Validation issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Task is valid!")
