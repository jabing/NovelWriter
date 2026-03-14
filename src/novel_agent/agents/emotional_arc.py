# src/agents/emotional_arc.py
"""Emotional Arc Planner - Controls emotional pacing for web fiction."""

from dataclasses import dataclass
from typing import Any

from src.novel_agent.agents.base import AgentResult, BaseAgent


@dataclass
class EmotionalBeat:
    """A single emotional beat in a chapter."""
    position: float  # 0.0 to 1.0 (start to end of chapter)
    emotion: str  # e.g., "tension", "joy", "sadness", "anger", "fear", "hope"
    intensity: int  # 1-10
    trigger: str  # What triggers this emotion
    description: str  # Brief description of the scene


@dataclass
class ChapterEmotionalArc:
    """Emotional arc for a single chapter."""
    chapter_number: int
    dominant_emotion: str
    arc_type: str  # "rising", "falling", "wave", "plateau"
    beats: list[EmotionalBeat]
    target_intensity_start: int  # 1-10
    target_intensity_end: int  # 1-10
    notes: str


@dataclass
class StoryEmotionalJourney:
    """Complete emotional journey for the story."""
    acts: dict[str, list[ChapterEmotionalArc]]
    emotional_themes: list[str]
    catharsis_points: list[int]  # Chapter numbers where emotional release occurs
    tension_peaks: list[int]  # Chapter numbers of highest tension


class EmotionalArcPlanner(BaseAgent):
    """Agent that plans emotional arcs for web fiction.

    Web fiction requires careful emotional pacing:
    - Hook chapters need high emotional intensity
    - Mid-story needs variety to prevent fatigue
    - Cliffhangers should peak emotions
    - Catharsis points needed for emotional release
    """

    # Standard emotional arcs by chapter position
    ARC_TEMPLATES = {
        "golden_1": {
            "dominant_emotion": "curiosity",
            "arc_type": "rising",
            "beats": [
                EmotionalBeat(0.0, "intrigue", 7, "Opening mystery", "Hook reader immediately"),
                EmotionalBeat(0.3, "curiosity", 6, "Character introduction", "Build investment"),
                EmotionalBeat(0.6, "tension", 8, "First conflict", "Raise stakes"),
                EmotionalBeat(0.9, "shock", 9, "Cliffhanger", "Must read next"),
            ],
            "start": 7,
            "end": 9,
        },
        "golden_2": {
            "dominant_emotion": "tension",
            "arc_type": "rising",
            "beats": [
                EmotionalBeat(0.0, "urgency", 8, "From previous cliffhanger", "Immediate continuation"),
                EmotionalBeat(0.4, "frustration", 7, "Obstacles appear", "Build conflict"),
                EmotionalBeat(0.8, "hope", 6, "Possible solution", "Brief relief"),
                EmotionalBeat(0.95, "dread", 9, "New threat", "Worse than before"),
            ],
            "start": 8,
            "end": 9,
        },
        "golden_3": {
            "dominant_emotion": "excitement",
            "arc_type": "rising",
            "beats": [
                EmotionalBeat(0.0, "determination", 8, "Character commits", "Point of no return"),
                EmotionalBeat(0.3, "tension", 7, "Complications arise", "Not so easy"),
                EmotionalBeat(0.6, "triumph", 8, "Partial victory", "But at cost"),
                EmotionalBeat(0.9, "revelation", 9, "Truth revealed", "Changes everything"),
            ],
            "start": 8,
            "end": 9,
        },
        "standard_rising": {
            "dominant_emotion": "tension",
            "arc_type": "rising",
            "beats": [
                EmotionalBeat(0.1, "curiosity", 5, "Chapter begins", "Setup"),
                EmotionalBeat(0.4, "intrigue", 6, "Plot develops", "Build interest"),
                EmotionalBeat(0.7, "tension", 7, "Conflict escalates", "Raise stakes"),
                EmotionalBeat(0.95, "urgency", 8, "Cliffhanger", "Hook for next"),
            ],
            "start": 5,
            "end": 8,
        },
        "standard_wave": {
            "dominant_emotion": "variety",
            "arc_type": "wave",
            "beats": [
                EmotionalBeat(0.1, "calm", 4, "Brief respite", "Let reader breathe"),
                EmotionalBeat(0.3, "humor", 5, "Light moment", "Character interaction"),
                EmotionalBeat(0.5, "tension", 7, "Conflict", "Drive plot"),
                EmotionalBeat(0.7, "hope", 6, "Progress made", "Emotional reward"),
                EmotionalBeat(0.95, "suspense", 8, "New complication", "Forward momentum"),
            ],
            "start": 4,
            "end": 8,
        },
        "climax_chapter": {
            "dominant_emotion": "excitement",
            "arc_type": "rising",
            "beats": [
                EmotionalBeat(0.0, "tension", 9, "Immediate high stakes", "No warmup"),
                EmotionalBeat(0.3, "struggle", 9, "Peak conflict", "Maximum effort"),
                EmotionalBeat(0.6, "desperation", 10, "All seems lost", "Darkest moment"),
                EmotionalBeat(0.8, "triumph", 9, "Victory", "Hard won"),
                EmotionalBeat(0.95, "relief", 7, "Resolution begins", "But questions remain"),
            ],
            "start": 9,
            "end": 7,
        },
        "emotional_catharsis": {
            "dominant_emotion": "release",
            "arc_type": "falling",
            "beats": [
                EmotionalBeat(0.1, "tension", 8, "Carryover stress", "High starting point"),
                EmotionalBeat(0.4, "vulnerability", 7, "Emotional reveal", "Character depth"),
                EmotionalBeat(0.7, "catharsis", 6, "Emotional release", "Tears or joy"),
                EmotionalBeat(0.95, "hope", 7, "Forward looking", "But new challenge hinted"),
            ],
            "start": 8,
            "end": 7,
        },
    }

    def __init__(self, name: str = "Emotional Arc Planner", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Plan emotional arcs for chapters.

        Args:
            input_data: Must contain:
                - total_chapters: int
                - genre: str
                - tone: str (optional)
                - key_moments: list[int] (chapters with special emotional needs)

        Returns:
            AgentResult with StoryEmotionalJourney
        """
        try:
            total_chapters = input_data.get("total_chapters", 50)
            genre = input_data.get("genre", "fantasy")
            tone = input_data.get("tone", "balanced")
            key_moments = input_data.get("key_moments", {})

            # Generate emotional journey
            journey = self._plan_emotional_journey(
                total_chapters, genre, tone, key_moments
            )

            return AgentResult(
                success=True,
                data={
                    "emotional_journey": journey,
                    "chapter_arcs": self._serialize_journey(journey),
                }
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Emotional arc planning failed: {str(e)}"]
            )

    def _plan_emotional_journey(
        self,
        total_chapters: int,
        genre: str,
        tone: str,
        key_moments: dict[str, list[int]]
    ) -> StoryEmotionalJourney:
        """Plan complete emotional journey."""

        acts = {
            "act_1": [],  # Chapters 1-25%
            "act_2a": [],  # Chapters 25-50%
            "act_2b": [],  # Chapters 50-75%
            "act_3": [],  # Chapters 75-100%
        }

        catharsis_points = []
        tension_peaks = []

        # Map chapters to acts
        act_1_end = int(total_chapters * 0.25)
        act_2a_end = int(total_chapters * 0.50)
        act_2b_end = int(total_chapters * 0.75)

        for ch in range(1, total_chapters + 1):
            arc = self._assign_arc_to_chapter(
                ch, total_chapters, tone, key_moments
            )

            # Assign to act
            if ch <= act_1_end:
                acts["act_1"].append(arc)
            elif ch <= act_2a_end:
                acts["act_2a"].append(arc)
            elif ch <= act_2b_end:
                acts["act_2b"].append(arc)
            else:
                acts["act_3"].append(arc)

            # Track special points
            if arc.arc_type == "falling":
                catharsis_points.append(ch)
            if arc.target_intensity_end >= 9:
                tension_peaks.append(ch)

        return StoryEmotionalJourney(
            acts=acts,
            emotional_themes=self._get_genre_emotions(genre),
            catharsis_points=catharsis_points,
            tension_peaks=tension_peaks,
        )

    def _assign_arc_to_chapter(
        self,
        chapter_number: int,
        total_chapters: int,
        tone: str,
        key_moments: dict[str, list[int]]
    ) -> ChapterEmotionalArc:
        """Assign appropriate emotional arc to a chapter."""

        # Golden 3 chapters
        if chapter_number == 1:
            template = self.ARC_TEMPLATES["golden_1"]
        elif chapter_number == 2:
            template = self.ARC_TEMPLATES["golden_2"]
        elif chapter_number == 3:
            template = self.ARC_TEMPLATES["golden_3"]
        # Key moments
        elif chapter_number in key_moments.get("climax", []):
            template = self.ARC_TEMPLATES["climax_chapter"]
        elif chapter_number in key_moments.get("catharsis", []):
            template = self.ARC_TEMPLATES["emotional_catharsis"]
        # Standard chapters - vary for rhythm
        elif chapter_number % 5 == 0:  # Every 5th chapter has high stakes
            template = self.ARC_TEMPLATES["standard_rising"]
        else:
            # Alternate between rising and wave for variety
            template = self.ARC_TEMPLATES["standard_wave"] if chapter_number % 2 == 0 else self.ARC_TEMPLATES["standard_rising"]

        # Adjust for tone
        beats = self._adjust_beats_for_tone(template["beats"], tone)

        return ChapterEmotionalArc(
            chapter_number=chapter_number,
            dominant_emotion=template["dominant_emotion"],
            arc_type=template["arc_type"],
            beats=beats,
            target_intensity_start=template["start"],
            target_intensity_end=template["end"],
            notes=self._generate_chapter_notes(chapter_number, template["arc_type"]),
        )

    def _adjust_beats_for_tone(
        self, beats: list[EmotionalBeat], tone: str
    ) -> list[EmotionalBeat]:
        """Adjust emotional beats based on story tone."""
        adjusted = []

        for beat in beats:
            intensity = beat.intensity

            if tone == "dark":
                # Increase negative emotions, decrease positive
                if beat.emotion in ["joy", "hope", "triumph"]:
                    intensity = max(1, intensity - 2)
                elif beat.emotion in ["fear", "dread", "sadness"]:
                    intensity = min(10, intensity + 1)
            elif tone == "light":
                # Decrease negative emotions
                if beat.emotion in ["fear", "dread", "sadness"]:
                    intensity = max(1, intensity - 2)
                elif beat.emotion in ["joy", "humor", "hope"]:
                    intensity = min(10, intensity + 1)

            adjusted.append(EmotionalBeat(
                position=beat.position,
                emotion=beat.emotion,
                intensity=intensity,
                trigger=beat.trigger,
                description=beat.description,
            ))

        return adjusted

    def _get_genre_emotions(self, genre: str) -> list[str]:
        """Get typical emotional themes for genre."""
        genre_emotions = {
            "romance": ["longing", "passion", "heartbreak", "hope", "jealousy", "devotion"],
            "fantasy": ["wonder", "courage", "fear", "determination", "sacrifice", "discovery"],
            "scifi": ["curiosity", "isolation", "awe", "paranoia", "determination", "revelation"],
            "history": ["nostalgia", "tragedy", "resilience", "honor", "loss", "triumph"],
            "military": ["camaraderie", "fear", "duty", "grief", "determination", "survival"],
        }
        return genre_emotions.get(genre.lower(), ["hope", "fear", "determination"])

    def _generate_chapter_notes(self, chapter_number: int, arc_type: str) -> str:
        """Generate guidance notes for chapter."""
        notes = []

        if chapter_number <= 3:
            notes.append("GOLDEN CHAPTER: Exceptional emotional intensity required")

        if arc_type == "rising":
            notes.append("Build tension progressively - end stronger than you begin")
        elif arc_type == "wave":
            notes.append("Vary emotional intensity - give readers moments to breathe")
        elif arc_type == "falling":
            notes.append("Catharsis chapter - allow emotional release and recovery")

        return "; ".join(notes)

    def _serialize_journey(self, journey: StoryEmotionalJourney) -> dict[str, Any]:
        """Convert journey to serializable dict."""
        return {
            "acts": {
                act_name: [
                    {
                        "chapter_number": arc.chapter_number,
                        "dominant_emotion": arc.dominant_emotion,
                        "arc_type": arc.arc_type,
                        "target_intensity_start": arc.target_intensity_start,
                        "target_intensity_end": arc.target_intensity_end,
                        "notes": arc.notes,
                        "beats": [
                            {
                                "position": b.position,
                                "emotion": b.emotion,
                                "intensity": b.intensity,
                                "trigger": b.trigger,
                            }
                            for b in arc.beats
                        ],
                    }
                    for arc in act_arcs
                ]
                for act_name, act_arcs in journey.acts.items()
            },
            "emotional_themes": journey.emotional_themes,
            "catharsis_points": journey.catharsis_points,
            "tension_peaks": journey.tension_peaks,
        }

    async def get_chapter_emotional_guidance(
        self, chapter_number: int, journey: StoryEmotionalJourney
    ) -> dict[str, Any]:
        """Get specific emotional guidance for a chapter."""
        # Find the chapter arc
        arc = None
        for act_arcs in journey.acts.values():
            for chapter_arc in act_arcs:
                if chapter_arc.chapter_number == chapter_number:
                    arc = chapter_arc
                    break
            if arc:
                break

        if not arc:
            return {"error": f"Chapter {chapter_number} not found in journey"}

        return {
            "chapter_number": chapter_number,
            "dominant_emotion": arc.dominant_emotion,
            "arc_type": arc.arc_type,
            "intensity_range": f"{arc.target_intensity_start} → {arc.target_intensity_end}",
            "key_beats": [
                f"{int(b.position * 100)}%: {b.emotion} (intensity {b.intensity}) - {b.trigger}"
                for b in arc.beats
            ],
            "writer_guidance": self._generate_writer_guidance(arc),
        }

    def _generate_writer_guidance(self, arc: ChapterEmotionalArc) -> str:
        """Generate specific writing guidance."""
        guidance = []

        guidance.append(f"Dominant emotion: {arc.dominant_emotion.upper()}")
        guidance.append(f"Arc type: {arc.arc_type} (intensity {arc.target_intensity_start} → {arc.target_intensity_end})")

        guidance.append("\nKey emotional beats:")
        for i, beat in enumerate(arc.beats, 1):
            guidance.append(f"  {i}. At {int(beat.position * 100)}%: {beat.emotion} (level {beat.intensity}/10)")
            guidance.append(f"     Trigger: {beat.trigger}")

        guidance.append(f"\nNotes: {arc.notes}")

        return "\n".join(guidance)
