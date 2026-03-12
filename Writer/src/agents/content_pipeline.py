# src/agents/content_pipeline.py
"""Content Pipeline - Complete creation + review workflow.

Ensures all creative content (outline, chapters, characters, worldbuilding)
goes through quality review before being finalized.

Supports multi-genre collaboration when content spans multiple genres.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.agents.agent_collaborator import AgentCollaborator, CollaborationMode
from src.agents.character import CharacterAgent
from src.agents.editor import EditorAgent
from src.agents.plot import PlotAgent
from src.agents.worldbuilding import WorldbuildingAgent
from src.learning.calibrated_reviewer import CalibratedReviewer

# Learning modules for adaptive content evolution
from src.learning.pattern_memory import PatternMemory
from src.learning.preference_tracker import PreferenceTracker
from src.llm.base import BaseLLM

logger = logging.getLogger(__name__)

class ContentType(str, Enum):
    """Types of content that can be created and reviewed."""
    OUTLINE = "outline"
    CHAPTER = "chapter"
    CHARACTER = "character"
    WORLDBUILDING = "worldbuilding"


class QualityLevel(str, Enum):
    """Quality levels for content assessment."""
    EXCEPTIONAL = "exceptional"  # 9-10
    GOOD = "good"  # 8-8.9
    ACCEPTABLE = "acceptable"  # 7-7.9
    POOR = "poor"  # Below 7


@dataclass
class ReviewResult:
    """Result of a content review."""
    approved: bool
    quality_score: float
    quality_level: QualityLevel
    issues: list[dict[str, Any]] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendation: str = "revise"
    edited_content: str | None = None
    review_notes: str = ""


@dataclass
class PipelineResult:
    """Result of the content pipeline (creation + review)."""
    success: bool
    content_type: ContentType
    original_content: str
    final_content: str
    iterations: int
    review: ReviewResult
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)




class ContentPipeline:
    """Pipeline for content creation with mandatory review.

    All creative content must pass through:
    1. Creation (Writer/Plot/Character/Worldbuilding Agent)
    2. Review (Editor Agent)
    3. Revision (if needed, up to max_iterations)
    4. Final approval

    Quality Gates:
    - Score >= 9: Approved
    - Score 7-8: Auto-revise
    - Score < 7: Major revision needed

    Learning modules enable adaptive content evolution:
    - PatternMemory: Learn from high-quality content
    - PreferenceTracker: Track user preferences
    - CalibratedReviewer: Role-specific review standards
    """

    # Quality thresholds
    APPROVAL_THRESHOLD = 9.0
    AUTO_REVISE_THRESHOLD = 7.0
    MAX_ITERATIONS = 5

    def __init__(
        self,
        writer_llm: BaseLLM,
        reviewer_llm: BaseLLM | None = None,
        max_iterations: int = 5,
        approval_threshold: float = 9.0,
        enable_learning: bool = True,
        language: str = "en",  # NEW
    ) -> None:
        """Initialize content pipeline.

        Args:
            writer_llm: LLM for content creation (e.g., GLM-5)
            reviewer_llm: LLM for quality review (e.g., Kimi 2.5). If None, uses writer_llm.
            max_iterations: Maximum revision iterations
            approval_threshold: Minimum score for approval (default 9.0 for high quality)
            enable_learning: Enable learning modules for adaptive content evolution
        """
        self.writer_llm = writer_llm
        self.reviewer_llm = reviewer_llm or writer_llm  # Default to same LLM if not specified
        self.max_iterations = max_iterations
        self.approval_threshold = approval_threshold
        self.enable_learning = enable_learning
        self._language = language

        # Initialize agents - writers use writer_llm
        self.editor = EditorAgent(llm=writer_llm)
        self.plot_agent = PlotAgent(llm=writer_llm)
        self.character_agent = CharacterAgent(llm=writer_llm)
        self.worldbuilding_agent = WorldbuildingAgent(llm=writer_llm)

        # Multi-genre collaborator uses writer_llm
        self.collaborator = AgentCollaborator(llm=writer_llm)

        # Writer agents will be loaded dynamically based on genre
        self._writers: dict[str, Any] = {}

        # Learning modules for adaptive content evolution
        if enable_learning:
            self.pattern_memory = PatternMemory()
            self.preference_tracker = PreferenceTracker()
            self.calibrated_reviewer = CalibratedReviewer()
            logger.info("Learning modules enabled for adaptive content evolution")
        else:
            self.pattern_memory = None
            self.preference_tracker = None
            self.calibrated_reviewer = None

        # Market research data for content optimization
        self._market_data: dict[str, Any] | None = None

    def set_language(self, language: str) -> None:
        """Set the output language for content generation."""
        if language in ("en", "zh"):
            self._language = language
            logger.info(f"Content pipeline language set to: {language}")

    def get_language(self) -> str:
        """Get current output language."""
        return self._language

    def set_market_data(self, market_data: dict[str, Any]) -> None:
        """Set market research data for content optimization.

        Args:
            market_data: Market research data including trending_tropes,
                         hot_keywords, target_audience, popular_phrases, etc.
        """
        self._market_data = market_data
        logger.info(f"Market data set with {len(market_data)} insights")

    def get_market_data(self) -> dict[str, Any] | None:
        """Get current market research data."""
        return self._market_data

    async def enrich_with_market_research(self, genre: str) -> bool:
        """Run market research and automatically apply to content pipeline.

        Args:
            genre: Genre to research (e.g., "fantasy", "scifi", "romance")

        Returns:
            True if market data was successfully loaded, False otherwise
        """
        from src.agents.market_research import MarketResearchAgent

        try:
            market_agent = MarketResearchAgent(llm=self.writer_llm)
            result = await market_agent.execute({
                "action": "analyze_genre",
                "genre": genre,
            })

            if result.success and result.data:
                self.set_market_data(result.data)
                logger.info(f"Market research loaded for genre: {genre}")
                return True
            else:
                logger.warning(f"Market research failed for genre: {genre}")
                return False
        except Exception as e:
            logger.error(f"Error loading market research: {str(e)}")
            return False

    def _get_writer(self, genre: str) -> Any:
        """Get writer agent for genre."""
        if genre not in self._writers:
            from src.agents.writers.writer_factory import get_writer
            self._writers[genre] = get_writer(genre, llm=self.writer_llm)
        return self._writers[genre]
        """Get current market research data."""
        return self._market_data

    def _get_writer(self, genre: str) -> Any:
            self.preference_tracker = None
            self.calibrated_reviewer = None

    def _get_writer(self, genre: str) -> Any:
        """Get writer agent for genre."""
        if genre not in self._writers:
            from src.agents.writers.writer_factory import get_writer
            self._writers[genre] = get_writer(genre, llm=self.writer_llm)
        return self._writers[genre]


    def _get_enhanced_generation_prompt(self, content_type: str, role: str | None = None) -> str:
        """Get enhanced generation prompt with learned patterns."""
        if not self.enable_learning:
            return ""
        enhancements = []
        if self.pattern_memory:
            patterns = self.pattern_memory.get_successful_features(content_type, role, min_score=8.0)
            if patterns:
                enhancements.append("参考成功模式: " + ", ".join(patterns[:5]))
        if self.preference_tracker:
            hints = self.preference_tracker.get_preference_hints(content_type)
            if hints:
                enhancements.append("用户偏好: " + ", ".join(hints[:3]))
        if enhancements:
            return chr(10) + chr(10) + chr(10).join(enhancements)
        return ""

    def _store_successful_pattern(
        self,
        content_type: str,
        content: dict[str, Any],
        score: float,
        role: str | None = None
    ) -> None:
        """Store successful pattern for future learning.

        Args:
            content_type: Type of content
            content: The content dictionary
            score: Quality score
            role: Role for characters
        """
        if not self.enable_learning or not self.pattern_memory:
            return

        if score >= 8.0:  # Only store high-quality patterns
            self.pattern_memory.store(content_type, content, score, role=role)
            logger.info(f"Stored successful {content_type} pattern with score {score}")
    async def create_outline(
        self,
        title: str,
        genre: str,
        premise: str,
        target_chapters: int = 100,
        themes: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Create and review novel outline.

        Args:
            title: Novel title
            genre: Novel genre
            premise: Story premise
            target_chapters: Number of chapters
            themes: Story themes
            context: Additional context

        Returns:
            PipelineResult with approved outline
        """
        logger.info(f"Creating outline for: {title}")

        # Step 1: Generate outline
        # Build context dict with all story settings for PlotAgent
        story_context = {
            "title": title,
            "premise": premise,
            "themes": themes or [],
            **(context or {}),  # Include any additional context (tone, audience, etc.)
        }

        # Add market research insights if available
        if self._market_data:
            trending_tropes = self._market_data.get("trending_tropes", [])[:3]
            hot_keywords = self._market_data.get("hot_keywords", [])[:5]
            target_audience = self._market_data.get("target_audience")

            if trending_tropes or hot_keywords:
                story_context["market_insights"] = {
                    "trending_tropes": trending_tropes,
                    "hot_keywords": hot_keywords,
                    "target_audience": target_audience,
                }
                logger.info(f"Market insights added: {len(trending_tropes)} tropes, {len(hot_keywords)} keywords")

        input_data = {
            "title": title,
            "premise": premise,
            "themes": themes or [],
            **(context or {}),  # Include any additional context (tone, audience, etc.)
        }

        input_data = {
            "genre": genre,
            "target_chapters": target_chapters,
            "premise": premise,
            "context": story_context,  # Pass context as a dict, not spread
            "language": self._language,
        }

        logger.info(f"PlotAgent input: genre={genre}, title={title}, premise={premise[:100]}...")

        result = await self.plot_agent.execute(input_data)

        logger.info(f"PlotAgent result: success={result.success}, errors={result.errors}")

        if not result.success:
            return PipelineResult(
                success=False,
                content_type=ContentType.OUTLINE,
                original_content="",
                final_content="",
                iterations=0,
                review=ReviewResult(
                    approved=False,
                    quality_score=0,
                    quality_level=QualityLevel.POOR,
                ),
                errors=result.errors,
            )

        # Store original title to preserve it through revisions
        original_title = title

        # PlotAgent returns data as {"outline": {...}}
        # Ensure we have a dict, not a string
        # First check if result.data is a dict before calling .get()
        if isinstance(result.data, dict):
            raw_outline = result.data.get("outline", result.data)
        else:
            # result.data might be a string or other type
            raw_outline = result.data
        if isinstance(raw_outline, dict):
            outline_data = raw_outline
        elif isinstance(raw_outline, str):
            # Try to parse as JSON if it's a string
            try:
                outline_data = json.loads(raw_outline)
            except json.JSONDecodeError:
                outline_data = {"title": title, "error": "Could not parse outline data"}
                logger.error(f"Could not parse outline data as JSON: {raw_outline[:200]}")
        else:
            outline_data = {"title": title}
            logger.warning(f"Unexpected outline data type: {type(raw_outline)}")

        logger.info(f"Outline data keys: {outline_data.keys() if isinstance(outline_data, dict) else 'N/A'}")
        # Safely extract main_arc title with proper type checking
        if isinstance(outline_data, dict):
            main_arc = outline_data.get('main_arc', {})
            main_arc_title = main_arc.get('title', 'N/A') if isinstance(main_arc, dict) else 'N/A'
        else:
            main_arc_title = 'N/A'
        logger.info(f"Main arc title: {main_arc_title}")

        original_content = self._format_outline(outline_data, original_title)

        logger.info(f"Formatted outline length: {len(original_content)} chars")
        logger.info(f"Formatted outline preview: {original_content[:500]}")

        current_content = original_content
        iterations = 0

        # Track best result across all iterations
        best_content = current_content
        best_review = await self._review_outline(current_content, outline_data)
        best_score = best_review.quality_score
        best_iteration = 0

        logger.info(f"Initial review score: {best_score}")

        # Step 2: Review and revise loop
        current_review = best_review  # Start with initial review
        while iterations < self.max_iterations:
            # Check if approved (using previous review)
            if current_review.approved:
                logger.info(f"Approved at iteration {iterations} with score {current_review.quality_score}")
                return PipelineResult(
                    success=True,
                    content_type=ContentType.OUTLINE,
                    original_content=original_content,
                    final_content=current_content,
                    iterations=iterations,
                    review=current_review,
                    metadata={"genre": genre, "chapters": target_chapters},
                )

            # Revise if not approved
            if current_review.quality_score >= self.AUTO_REVISE_THRESHOLD:
                logger.info(f"Revising outline (score {current_review.quality_score} < {self.approval_threshold})")
                current_content = await self._revise_outline(
                    current_content, current_review, outline_data, original_title=original_title
                )
                iterations += 1
            else:
                # Major issues - try once more with more guidance
                logger.info(f"Major revision needed (score {current_review.quality_score} < {self.AUTO_REVISE_THRESHOLD})")
                current_content = await self._revise_outline(
                    current_content, current_review, outline_data,
                    major_revision=True,
                    original_title=original_title
                )
                iterations += 1

            # Review after revision
            current_review = await self._review_outline(current_content, outline_data)

            # Track best result
            if current_review.quality_score > best_score:
                best_content = current_content
                best_review = current_review
                best_score = current_review.quality_score
                best_iteration = iterations
                logger.info(f"New best score: {best_score} at iteration {iterations}")

        # Final review after max iterations
        final_review = current_review  # Use the last review

        # Update best if final is better
        if final_review.quality_score > best_score:
            best_content = current_content
            best_review = final_review
            best_score = final_review.quality_score
            best_iteration = iterations

        # Log summary
        logger.info(f"Revisions complete. Best score: {best_score} at iteration {best_iteration}")
        logger.info(f"Final score: {final_review.quality_score}")

        # Determine if threshold was met
        threshold_met = best_review.approved

        # Auto-store high-quality patterns for learning
        if self.enable_learning and self.pattern_memory and best_score >= 8.0:
            self.pattern_memory.store(
                content_type="outline",
                content=outline_data if isinstance(outline_data, dict) else {"raw": outline_data},
                score=best_score,
            )
            logger.info(f"Stored high-quality outline pattern (score: {best_score})")

        # Always return the best result - threshold only determines quality status
        return PipelineResult(
            success=True,  # Always succeed - we have usable content
            content_type=ContentType.OUTLINE,
            original_content=original_content,
            final_content=best_content,  # Return the best version
            iterations=iterations,
            review=best_review,
            metadata={
                "genre": genre,
                "chapters": target_chapters,
                "best_iteration": best_iteration,
                "best_score": best_score,
                "threshold_met": threshold_met,  # Whether we hit the quality target
                "quality_status": "approved" if threshold_met else "acceptable",
            },
            errors=[],  # No errors - content is usable
        )

    async def create_chapter(
        self,
        chapter_number: int,
        chapter_outline: str,
        genre: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        previous_chapters: str | None = None,
        style_guide: str | None = None,
    ) -> PipelineResult:
        """Create and review a chapter.

        Args:
            chapter_number: Chapter number
            chapter_outline: Outline for this chapter
            genre: Novel genre
            characters: Character profiles
            world_context: World building context
            previous_chapters: Summary of previous chapters
            style_guide: Style guidelines

        Returns:
            PipelineResult with approved chapter
        """
        logger.info(f"Creating chapter {chapter_number}")

        # Step 1: Generate chapter
        writer = self._get_writer(genre)

        # Get learning hints if enabled
        learning_hints = None
        if self.enable_learning:
            learning_hints = []
            if self.pattern_memory:
                patterns = self.pattern_memory.get_successful_features("chapter", min_score=8.0, limit=5)
                learning_hints.extend(patterns)
            if self.preference_tracker:
                preferences = self.preference_tracker.get_preference_hints("chapter")
                learning_hints.extend(preferences)
            logger.info(f"Loaded {len(learning_hints)} learning hints for chapter generation")

        # Add market research keywords if available
        market_keywords = None
        if self._market_data:
            market_keywords = {
                "seo_keywords": self._market_data.get("hot_keywords", [])[:3],
                "popular_phrases": self._market_data.get("popular_phrases", []),
                "trending_elements": self._market_data.get("trending_tropes", [])[:2],
            }
            logger.info(f"Market keywords added: {len(market_keywords.get('seo_keywords', []))} keywords")

        original_content = await writer.write_chapter(
            chapter_number=chapter_number,
            chapter_outline=chapter_outline,
            characters=characters,
            world_context=world_context,
            style_guide=style_guide,
            learning_hints=learning_hints,
            market_keywords=market_keywords,
            language=self._language,
        )

        current_content = original_content
        iterations = 0

        # Track best result across all iterations
        best_content = current_content
        best_content = current_content
        best_review = await self._review_chapter(current_content, characters, world_context, chapter_number)
        best_score = best_review.quality_score
        best_iteration = 0

        logger.info(f"Initial chapter review score: {best_score}")

        # Step 2: Review and revise loop
        current_review = best_review  # Start with initial review
        while iterations < self.max_iterations:
            # Check if approved (using previous review)
            if current_review.approved:
                logger.info(f"Chapter approved at iteration {iterations} with score {current_review.quality_score}")
                return PipelineResult(
                    success=True,
                    content_type=ContentType.CHAPTER,
                    original_content=original_content,
                    final_content=current_content,
                    iterations=iterations,
                    review=current_review,
                    metadata={
                        "chapter_number": chapter_number,
                        "word_count": len(current_content.split()),
                        "genre": genre,
                    },
                )

            # Revise if not approved
            if current_review.quality_score >= self.AUTO_REVISE_THRESHOLD:
                logger.info(f"Revising chapter (score {current_review.quality_score} < {self.approval_threshold})")
                current_content = await self._revise_chapter(
                    current_content, current_review, characters, world_context
                )
                iterations += 1
            else:
                logger.info(f"Major revision needed (score {current_review.quality_score} < {self.AUTO_REVISE_THRESHOLD})")
                current_content = await self._revise_chapter(
                    current_content, current_review, characters, world_context,
                    major_revision=True,
                )
                iterations += 1

            # Review after revision
            current_review = await self._review_chapter(
                current_content, characters, world_context, chapter_number
            )

            # Track best result
            if current_review.quality_score > best_score:
                best_content = current_content
                best_review = current_review
                best_score = current_review.quality_score
                best_iteration = iterations
                logger.info(f"New best chapter score: {best_score} at iteration {iterations}")

        # Final review
        final_review = current_review  # Use the last review

        # Update best if final is better
        if final_review.quality_score > best_score:
            best_content = current_content
            best_review = final_review
            best_score = final_review.quality_score
            best_iteration = iterations

        # Log summary
        logger.info(f"Chapter revisions complete. Best score: {best_score} at iteration {best_iteration}")

        # Determine if threshold was met
        threshold_met = best_review.approved

        # Auto-store high-quality patterns for learning
        if self.enable_learning and self.pattern_memory and best_score >= 8.0:
            self.pattern_memory.store(
                content_type="chapter",
                content={"outline": chapter_outline, "genre": genre},
                score=best_score,
            )
            logger.info(f"Stored high-quality chapter pattern (score: {best_score})")

        # Return the best result
        return PipelineResult(
            success=True,  # Always succeed - we have usable content
            content_type=ContentType.CHAPTER,
            original_content=original_content,
            final_content=best_content,  # Return the best version
            iterations=iterations,
            review=best_review,
            metadata={
                "chapter_number": chapter_number,
                "word_count": len(best_content.split()),
                "genre": genre,
                "best_iteration": best_iteration,
                "best_score": best_score,
                "threshold_met": threshold_met,  # Whether we hit the quality target
                "quality_status": "approved" if threshold_met else "acceptable",
            },
            errors=[],  # No errors - content is usable
        )

    async def create_chapter_multi_genre(
        self,
        chapter_number: int,
        chapter_outline: str,
        genres: list[str],
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        collaboration_mode: str = "lead_support",
        previous_chapters: str | None = None,
        style_guide: str | None = None,
    ) -> PipelineResult:
        """Create and review a chapter using multi-genre collaboration.

        Use this when content spans multiple genres, e.g.:
        - Historical romance (romance + history)
        - Science fantasy (scifi + fantasy)
        - Military thriller (thriller + military)

        Args:
            chapter_number: Chapter number
            chapter_outline: Outline for this chapter
            genres: List of genres to involve (e.g., ["romance", "history"])
            characters: Character profiles
            world_context: World building context
            collaboration_mode: How agents collaborate
                - "lead_support": Lead genre writes, others enhance
                - "sequential": Hand off between agents
                - "parallel": All write simultaneously, merge
                - "dynamic": AI decides in real-time
            previous_chapters: Summary of previous chapters
            style_guide: Style guidelines

        Returns:
            PipelineResult with approved chapter
        """
        logger.info(f"Creating multi-genre chapter {chapter_number}: {genres}")

        # Step 1: Multi-agent collaboration
        mode_map = {
            "lead_support": CollaborationMode.LEAD_SUPPORT,
            "sequential": CollaborationMode.SEQUENTIAL,
            "parallel": CollaborationMode.PARALLEL,
            "dynamic": CollaborationMode.DYNAMIC,
        }

        collab_result = await self.collaborator.collaborate(
            content_type="chapter",
            outline=chapter_outline,
            genres=genres,
            mode=mode_map.get(collaboration_mode, CollaborationMode.LEAD_SUPPORT),
            characters=characters,
            world_context=world_context,
            chapter_number=chapter_number,
        )

        original_content = collab_result.content
        current_content = original_content
        iterations = 0

        # Track best result across all iterations
        best_content = current_content
        best_review = await self._review_chapter(current_content, characters, world_context, chapter_number)
        best_score = best_review.quality_score
        best_iteration = 0

        logger.info(f"Initial multi-genre chapter review score: {best_score}")

        # Step 2: Review and revise loop (same as single-genre)
        while iterations < self.max_iterations:
            review = await self._review_chapter(
                current_content, characters, world_context, chapter_number
            )

            # Track best result
            if review.quality_score > best_score:
                best_content = current_content
                best_review = review
                best_score = review.quality_score
                best_iteration = iterations
                logger.info(f"New best multi-genre chapter score: {best_score} at iteration {iterations}")

            if review.approved:
                logger.info(f"Multi-genre chapter approved at iteration {iterations} with score {review.quality_score}")
                return PipelineResult(
                    success=True,
                    content_type=ContentType.CHAPTER,
                    original_content=original_content,
                    final_content=current_content,
                    iterations=iterations,
                    review=review,
                    metadata={
                        "chapter_number": chapter_number,
                        "word_count": len(current_content.split()),
                        "genres": genres,
                        "collaboration_mode": collaboration_mode,
                        "contributions": collab_result.contributions,
                    },
                )

            if review.quality_score >= self.AUTO_REVISE_THRESHOLD:
                current_content = await self._revise_chapter(
                    current_content, review, characters, world_context
                )
                iterations += 1
            else:
                current_content = await self._revise_chapter(
                    current_content, review, characters, world_context,
                    major_revision=True,
                )
                iterations += 1

        final_review = await self._review_chapter(
            current_content, characters, world_context, chapter_number
        )

        # Update best if final is better
        if final_review.quality_score > best_score:
            best_content = current_content
            best_review = final_review
            best_score = final_review.quality_score
            best_iteration = iterations

        # Log summary
        logger.info(f"Multi-genre chapter revisions complete. Best score: {best_score} at iteration {best_iteration}")

        # Determine if threshold was met
        threshold_met = best_review.approved

        # Return the best result
        return PipelineResult(
            success=True,  # Always succeed - we have usable content
            content_type=ContentType.CHAPTER,
            original_content=original_content,
            final_content=best_content,
            iterations=iterations,
            review=best_review,
            metadata={
                "chapter_number": chapter_number,
                "word_count": len(best_content.split()),
                "genres": genres,
                "collaboration_mode": collaboration_mode,
                "best_iteration": best_iteration,
                "best_score": best_score,
                "threshold_met": threshold_met,  # Whether we hit the quality target
                "quality_status": "approved" if threshold_met else "acceptable",
            },
            errors=[],  # No errors - content is usable
        )

    async def create_character(
        self,
        character_name: str,
        role: str,
        genre: str,
        story_context: dict[str, Any] | None = None,
        existing_characters: list[dict[str, Any]] | None = None,
    ) -> PipelineResult:
        """Create and review a character profile.

        Args:
            character_name: Character name
            role: Character role (protagonist, antagonist, etc.)
            genre: Story genre
            story_context: Story context for character (should include premise, title, themes)
            existing_characters: Already created characters

        Returns:
            PipelineResult with approved character profile
        """
        logger.info(f"Creating character: {character_name}")

        # Build rich story context for character generation
        context = story_context or {}

        # Step 1: Generate character using the agent's create_character method directly
        # This method properly handles single character creation with story context
        try:
            character_data = await self.character_agent.create_character(
                role=role,
                genre=genre,
                story_context=context,
                character_name=character_name,
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                content_type=ContentType.CHARACTER,
                original_content="",
                final_content="",
                iterations=0,
                review=ReviewResult(
                    approved=False,
                    quality_score=0,
                    quality_level=QualityLevel.POOR,
                ),
                errors=[f"Character generation failed: {str(e)}"],
            )

        original_content = self._format_character(character_data)
        current_data = character_data
        iterations = 0

        # Track best result across all iterations
        best_data = current_data
        best_review = await self._review_character(current_data, existing_characters or [], role=role)
        best_score = best_review.quality_score
        best_iteration = 0

        logger.info(f"Initial character review score: {best_score}")

        # Step 2: Review and revise loop
        current_review = best_review  # Start with initial review
        while iterations < self.max_iterations:
            # Check if approved (using previous review)
            if current_review.approved:
                logger.info(f"Character approved at iteration {iterations} with score {current_review.quality_score}")
                return PipelineResult(
                    success=True,
                    content_type=ContentType.CHARACTER,
                    original_content=original_content,
                    final_content=self._format_character(current_data),
                    iterations=iterations,
                    review=current_review,
                    metadata={"name": character_name, "role": role},
                )

            # Revise if not approved
            if current_review.quality_score >= self.AUTO_REVISE_THRESHOLD:
                logger.info(f"Revising character (score {current_review.quality_score} < {self.approval_threshold})")
                current_data = await self._revise_character(current_data, current_review)
                iterations += 1
            else:
                # Major issues - try once more with more guidance
                logger.info(f"Major revision needed (score {current_review.quality_score} < {self.AUTO_REVISE_THRESHOLD})")
                current_data = await self._revise_character(current_data, current_review, major=True)
                iterations += 1

            # Review after revision
            current_review = await self._review_character(current_data, existing_characters or [], role=role)

            # Track best result
            if current_review.quality_score > best_score:
                best_data = current_data
                best_review = current_review
                best_score = current_review.quality_score
                best_iteration = iterations
                logger.info(f"New best character score: {best_score} at iteration {iterations}")

        final_review = current_review  # Use the last review

        # Update best if final is better
        if final_review.quality_score > best_score:
            best_data = current_data
            best_review = final_review
            best_score = final_review.quality_score
            best_iteration = iterations

        # Log summary
        logger.info(f"Character revisions complete. Best score: {best_score} at iteration {best_iteration}")

        # Determine if threshold was met
        threshold_met = best_review.approved

        # Auto-store high-quality patterns for learning
        if self.enable_learning and self.pattern_memory and best_score >= 8.0:
            self.pattern_memory.store(
                content_type="character",
                content=best_data if isinstance(best_data, dict) else {"raw": str(best_data)},
                score=best_score,
                role=role,
            )
            logger.info(f"Stored high-quality character pattern (score: {best_score}, role: {role})")

        # Return the best result
        return PipelineResult(
            success=True,  # Always succeed - we have usable content
            content_type=ContentType.CHARACTER,
            original_content=original_content,
            final_content=self._format_character(best_data),  # Return the best version
            iterations=iterations,
            review=best_review,
            metadata={
                "name": character_name,
                "role": role,
                "best_iteration": best_iteration,
                "best_score": best_score,
                "threshold_met": threshold_met,  # Whether we hit the quality target
                "quality_status": "approved" if threshold_met else "acceptable",
            },
            errors=[],  # No errors - content is usable
        )

    async def create_worldbuilding(
        self,
        genre: str,
        setting_type: str,
        story_context: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Create and review worldbuilding elements.

        Args:
            genre: Story genre
            setting_type: Type of setting (school, city, fantasy_world, etc.)
            story_context: Story context

        Returns:
            PipelineResult with approved worldbuilding
        """
        logger.info(f"Creating worldbuilding: {setting_type}")

        # Step 1: Generate worldbuilding
        input_data = {
            "genre": genre,
            "setting_type": setting_type,
            "story_context": story_context or {},
        }

        result = await self.worldbuilding_agent.execute(input_data)
        if not result.success:
            return PipelineResult(
                success=False,
                content_type=ContentType.WORLDBUILDING,
                original_content="",
                final_content="",
                iterations=0,
                review=ReviewResult(
                    approved=False,
                    quality_score=0,
                    quality_level=QualityLevel.POOR,
                ),
                errors=result.errors,
            )

        original_content = self._format_worldbuilding(result.data)
        current_content = original_content
        current_data = result.data
        iterations = 0

        # Track best result across all iterations
        best_content = current_content
        best_data = current_data
        best_review = await self._review_worldbuilding(current_data, genre)
        best_score = best_review.quality_score
        best_iteration = 0

        logger.info(f"Initial worldbuilding review score: {best_score}")

        # Step 2: Review and revise loop
        current_review = best_review  # Start with initial review
        while iterations < self.max_iterations:
            # Check if approved (using previous review)
            if current_review.approved:
                logger.info(f"Worldbuilding approved at iteration {iterations} with score {current_review.quality_score}")
                return PipelineResult(
                    success=True,
                    content_type=ContentType.WORLDBUILDING,
                    original_content=original_content,
                    final_content=current_content,
                    iterations=iterations,
                    review=current_review,
                    metadata={"setting_type": setting_type, "genre": genre},
                )

            # Revise if not approved
            if current_review.quality_score >= self.AUTO_REVISE_THRESHOLD:
                logger.info(f"Revising worldbuilding (score {current_review.quality_score} < {self.approval_threshold})")
                current_data = await self._revise_worldbuilding(current_data, current_review)
                current_content = self._format_worldbuilding(current_data)
                iterations += 1
            else:
                # Major issues - try once more with more guidance
                logger.info(f"Major revision needed (score {current_review.quality_score} < {self.AUTO_REVISE_THRESHOLD})")
                current_data = await self._revise_worldbuilding(current_data, current_review, major=True)
                current_content = self._format_worldbuilding(current_data)
                iterations += 1

            # Review after revision
            current_review = await self._review_worldbuilding(current_data, genre)

            # Track best result
            if current_review.quality_score > best_score:
                best_content = current_content
                best_data = current_data
                best_review = current_review
                best_score = current_review.quality_score
                best_iteration = iterations
                logger.info(f"New best worldbuilding score: {best_score} at iteration {iterations}")

        # Final review after max iterations
        final_review = current_review  # Use the last review

        # Update best if final is better
        if final_review.quality_score > best_score:
            best_content = current_content
            best_data = current_data
            best_review = final_review
            best_score = final_review.quality_score
            best_iteration = iterations

        # Log summary
        logger.info(f"Worldbuilding revisions complete. Best score: {best_score} at iteration {best_iteration}")

        # Determine if threshold was met
        threshold_met = best_review.approved

        # Auto-store high-quality patterns for learning
        if self.enable_learning and self.pattern_memory and best_score >= 8.0:
            self.pattern_memory.store(
                content_type="worldbuilding",
                content=best_data if isinstance(best_data, dict) else {"raw": str(best_data)},
                score=best_score,
                role=setting_type,  # Store setting_type as role
            )
            logger.info(f"Stored high-quality worldbuilding pattern (score: {best_score}, type: {setting_type})")

        # Return the best result
        return PipelineResult(
            success=True,  # Always succeed - we have usable content
            content_type=ContentType.WORLDBUILDING,
            original_content=original_content,
            final_content=best_content,  # Return the best version
            iterations=iterations,
            review=best_review,
            metadata={
                "setting_type": setting_type,
                "genre": genre,
                "best_iteration": best_iteration,
                "best_score": best_score,
                "threshold_met": threshold_met,  # Whether we hit the quality target
                "quality_status": "approved" if threshold_met else "acceptable",
            },
            errors=[],  # No errors - content is usable
        )

    # Review methods

    async def _review_outline(
        self,
        content: str,
        outline_data: dict[str, Any] | str,
    ) -> ReviewResult:
        """Review outline quality."""
        # Ensure outline_data is a dict
        if isinstance(outline_data, str):
            outline_data = {"title": "", "genre": ""}

        # Check if content is too short (likely parsing failed)
        if len(content.strip()) < 200:
            logger.warning(f"Outline content too short: {len(content.strip())} chars")
            return ReviewResult(
                approved=False,
                quality_score=3,
                quality_level=QualityLevel.POOR,
                issues=[{"type": "incomplete", "description": "Outline content is too short or incomplete"}],
                review_notes="Outline appears to be incomplete or empty",
            )

        system_prompt = """You are a professional fiction editor reviewing a novel outline.
Evaluate the outline for:
1. Story structure (beginning, middle, end)
2. Pacing and tension
3. Character arcs
4. Plot coherence
5. Genre appropriateness

SCORING CRITERIA (1-10 scale):
- 9.0-10: Exceptional - Compelling hook, clear stakes, well-structured acts, strong emotional arc
- 8.0-8.9: Good - Solid structure but minor issues with pacing or depth
- 7.0-7.9: Acceptable - Basic structure present but needs significant improvement
- 6.0-6.9: Below average - Major structural or coherence issues
- Below 6: Poor - Fundamental problems, needs complete rewrite

Be CRITICAL and OBJECTIVE. Most first drafts score 6-7. Only award 9+ for truly exceptional work.

Output ONLY valid JSON with no markdown or explanation."""

        # Get story title for context
        title = outline_data.get("title", "") if isinstance(outline_data, dict) else ""
        genre = outline_data.get("genre", "") if isinstance(outline_data, dict) else ""

        user_prompt = f"""Review this novel outline:

{content[:4000]}

{"Story Title: " + title if title else ""}
{"Genre: " + genre if genre else ""}

Generate a JSON review with a CRITICAL assessment:
{{
    "quality_score": 6.5,
    "strengths": ["Strong premise", "Good pacing"],
    "weaknesses": ["Act 2 needs more tension", "Character motivations unclear"],
    "issues": [],
    "recommendation": "revise",
    "notes": "Overall assessment with specific improvement suggestions"
}}

Output ONLY the JSON, no other text."""

        response = await self.reviewer_llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,  # Increased from 0.3 for more score variation
        )

        # Debug log the raw response
        logger.info(f"Raw review response: {response.content[:500]}")

        result = self._parse_review_response(response.content)

        # Debug log the parsed result
        logger.info(f"Review result - Approved: {result.approved}, Score: {result.quality_score}")

        return result

    async def _review_chapter(
        self,
        content: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        chapter_number: int,
    ) -> ReviewResult:
        """Review chapter quality."""
        editor_result = await self.editor.execute({
            "content": content,
            "characters": characters,
            "world_context": world_context,
        })

        if not editor_result.success:
            return ReviewResult(
                approved=False,
                quality_score=0,
                quality_level=QualityLevel.POOR,
                issues=[{"type": "error", "description": str(e)} for e in editor_result.errors],
            )

        data = editor_result.data

        # Safely handle data - it might be a string instead of dict
        if not isinstance(data, dict):
            logger.warning(f"editor_result.data is not a dict: {type(data)}")
            data = {}

        # Safely extract quality_score with type checking
        quality_data = data.get("quality_score", {})
        if not isinstance(quality_data, dict):
            quality_data = {}
        quality_score = quality_data.get("overall", 5)

        return ReviewResult(
            approved=quality_score >= self.approval_threshold,
            quality_score=quality_score,
            quality_level=self._get_quality_level(quality_score),
            issues=data.get("all_issues", []) if isinstance(data, dict) else [],
            strengths=quality_data.get("strengths", []),
            weaknesses=quality_data.get("weaknesses", []),
            recommendation=quality_data.get("recommendation", "revise"),
            edited_content=data.get("edited_content") if isinstance(data, dict) else None,
            review_notes=quality_data.get("summary", ""),
        )

    async def _review_character(
        self,
        character_data: dict[str, Any],
        existing_characters: list[dict[str, Any]] | list[str],
        role: str | None = None,
    ) -> ReviewResult:
        """Review character profile quality using calibrated standards."""
        # Use CalibratedReviewer for role-specific evaluation
        if self.calibrated_reviewer and role:
            system_prompt = self.calibrated_reviewer.get_review_prompt(
                content_type="character",
                role=role,
            )
        else:
            system_prompt = """You are a character development expert.
Evaluate character profiles for:
1. Depth and complexity
2. Consistency
3. Uniqueness from other characters
4. Growth potential
5. Genre appropriateness

SCORING CRITERIA (1-10 scale):
- 9.0-10: Exceptional - Complex, consistent, unique, clear arc, perfectly fits genre
- 8.0-8.9: Good - Well-developed but minor inconsistencies or lacks depth
- 7.0-7.9: Acceptable - Basic character present but clichéd or underdeveloped
- 6.0-6.9: Below average - Inconsistent traits, unclear motivation, generic
- Below 6: Poor - One-dimensional or fundamentally flawed

Be CRITICAL. Most initial character drafts score 6-7. Only award 9+ for truly memorable characters.

Output valid JSON only."""

        # Handle both dict and string items in existing_characters
        existing_names = []
        for c in existing_characters[:5]:
            if isinstance(c, dict):
                existing_names.append(c.get("name", ""))
            elif isinstance(c, str):
                existing_names.append(c)

        user_prompt = f"""Review this character:

{json.dumps(character_data, indent=2)[:2000]}

Existing characters: {existing_names}

Generate a JSON review with a CRITICAL assessment:
{{
    "quality_score": 6.5,
    "strengths": ["Complex backstory", "Clear motivation"],
    "weaknesses": ["Trait could be more specific", "Lacks unique voice"],
    "issues": [],
    "recommendation": "revise",
    "notes": "Assessment with specific improvement suggestions"
}}"""

        response = await self.reviewer_llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,  # Increased for more score variation
        )

        return self._parse_review_response(response.content)

    async def _review_worldbuilding(
        self,
        world_data: dict[str, Any],
        genre: str,
    ) -> ReviewResult:
        """Review worldbuilding quality."""
        system_prompt = """You are a worldbuilding expert.
Evaluate world settings for:
1. Internal consistency
2. Richness and depth
3. Genre appropriateness
4. Story potential
5. Unique elements

SCORING CRITERIA (1-10 scale):
- 9.0-10: Exceptional - Fully realized, consistent, rich detail, unique, enhances story
- 8.0-8.9: Good - Well-developed but some areas underdeveloped or minor inconsistencies
- 7.0-7.9: Acceptable - Basic world present but generic or lacks depth
- 6.0-6.9: Below average - Inconsistent rules, underdeveloped, doesn't serve story
- Below 6: Poor - Confusing or contradictory worldbuilding

Be CRITICAL. Most initial worldbuilding scores 6-7. Only award 9+ for truly immersive worlds.

Output valid JSON only."""

        user_prompt = f"""Review this worldbuilding for a {genre} story:

{json.dumps(world_data, indent=2)[:2000]}

Generate a JSON review with a CRITICAL assessment:
{{
    "quality_score": 6.5,
    "strengths": ["Rich history", "Unique magic system"],
    "weaknesses": ["Politics could be more developed", "Geography unclear"],
    "issues": [],
    "recommendation": "revise",
    "notes": "Assessment with specific improvement suggestions"
}}"""

        response = await self.reviewer_llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,  # Increased for more score variation
        )

        return self._parse_review_response(response.content)

    # Revision methods

    async def _revise_outline(
        self,
        content: str,
        review: ReviewResult,
        outline_data: dict[str, Any],
        major_revision: bool = False,
        original_title: str = "",
    ) -> str:
        """Revise outline based on review."""
        issues_text = "\n".join([
            f"- {i.get('description', str(i))}" for i in review.issues[:5]
        ])

        # Extract story context to maintain consistency with safe type checking
        # First ensure outline_data is a dict
        if not isinstance(outline_data, dict):
            outline_data = {}

        main_arc = outline_data.get("main_arc", {})
        if not isinstance(main_arc, dict):
            main_arc = {}

        title = original_title or outline_data.get("title") or main_arc.get("title", "")
        genre = outline_data.get("genre", "")
        premise = outline_data.get("premise") or main_arc.get("logline", "")
        theme = main_arc.get("theme", "")

        context_reminder = ""
        if title:
            context_reminder += f"""
**CRITICAL: The story title MUST remain exactly "{title}" throughout the revision.**
"""
        if genre:
            context_reminder += f"**Genre: {genre}**\n"
        if premise:
            context_reminder += f"**Premise: {premise}**\n"
        if theme:
            context_reminder += f"**Core Theme: {theme}**\n"
        context_reminder += "\nDo NOT change the story title, genre, premise, or core theme. Only improve structure, pacing, and detail.\n"

        system_prompt = f"""You are a professional fiction editor revising a novel outline.
Improve the outline while maintaining the core story vision.
{context_reminder}
IMPORTANT: The outline title MUST be "{title}". Never change it to "[Story Title]" or any placeholder."""

        user_prompt = f"""Revise this outline based on the review feedback.

CURRENT OUTLINE:
{content}

ISSUES TO ADDRESS:
{issues_text}

WEAKNESSES:
{chr(10).join(f'- {w}' for w in review.weaknesses[:3])}

{"MAJOR REVISION NEEDED - significantly improve structure and pacing." if major_revision else "Make targeted improvements."}

**Remember: The outline title MUST be "{title}" - do not use "[Story Title]" or any placeholder.**

Provide the revised outline:"""

        response = await self.reviewer_llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=4000,
        )

        revised = response.content.strip()

        # Force correct title in the revised content (in case LLM ignores instructions)
        if original_title and original_title in content:
            # Extract the first heading and replace it with correct title
            import re
            revised = re.sub(
                r'^#\s*\[?[^\]]*\]?\s*$',
                f'# {original_title}',
                revised,
                count=1,
                flags=re.MULTILINE
            )

        return revised

    async def _revise_chapter(
        self,
        content: str,
        review: ReviewResult,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        major_revision: bool = False,
        chapter_number: int = 1,
    ) -> str:
        """Revise chapter based on review with web fiction optimizations."""
        # Use editor's edited content if available and good enough
        if review.edited_content and review.quality_score >= 5:
            return review.edited_content

        issues_text = "\n".join([
            f"- {i.get('description', str(i))}" for i in review.issues[:5]
        ])

        # Check for critical hook issues
        hook_issues = [i for i in review.issues if 'hook' in i.get('type', '').lower()]
        has_hook_issues = len(hook_issues) > 0

        # Golden 3 chapters special handling
        is_golden_chapter = chapter_number <= 3

        system_prompt = f"""You are a professional web fiction editor.
Improve the chapter while maintaining the author's voice and story.

WEB FICTION BEST PRACTICES:
1. Opening must grab attention in first 300 words
2. Chapter must end with cliffhanger or unresolved tension
3. Paragraphs should be short (mobile-friendly, max 4 lines)
4. Dialogue should be 30-50% of content
5. Scene changes every 800-1000 words
6. Emotional beats every 2-3 pages

{'CRITICAL - GOLDEN CHAPTER ' + str(chapter_number) + ': This is one of the first 3 chapters. It MUST be exceptional to retain readers.' if is_golden_chapter else ''}

{'PRIORITY FIX: Address hook issues in opening and closing.' if has_hook_issues else ''}"""

        user_prompt = f"""Revise this chapter based on the review feedback.

CHAPTER {chapter_number}{' (GOLDEN CHAPTER - EXCEPTIONAL QUALITY REQUIRED)' if is_golden_chapter else ''}

CURRENT CHAPTER:
{content[:4000]}

ISSUES TO ADDRESS:
{issues_text}

WEAKNESSES:
{chr(10).join(f'- {w}' for w in review.weaknesses[:3])}

{"MAJOR REVISION NEEDED - significantly improve prose quality, hooks, and pacing." if major_revision else "Make targeted improvements focusing on hooks and pacing."}

SPECIFIC REQUIREMENTS:
1. First 300 words MUST hook the reader (action, dialogue, or intrigue)
2. Last 200 words MUST create desire to read next chapter
3. Keep paragraphs short (under 60 words each)
4. Ensure at least 30% dialogue
5. Add scene changes if section drags

Provide the revised chapter:"""

        response = await self.reviewer_llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=4000,
        )

        return response.content.strip()

    async def _revise_character(
        self,
        character_data: dict[str, Any],
        review: ReviewResult,
        major: bool = False,
    ) -> dict[str, Any]:
        """Revise character profile based on review."""
        system_prompt = """You are a character development expert.
Revise the character profile to address feedback while maintaining the core concept.
Output valid JSON only."""

        # Handle both dict and string items in issues
        issues_list = []
        for i in review.issues[:3]:
            if isinstance(i, dict):
                issues_list.append(f"- {i.get('description', str(i))}")
            elif isinstance(i, str):
                issues_list.append(f"- {i}")

        issues_text = "\n".join(issues_list) if issues_list else "No specific issues provided"

        user_prompt = f"""Revise this character profile:

{json.dumps(character_data, indent=2)}

ADDRESS THESE ISSUES:
{issues_text}

WEAKNESSES:
{chr(10).join(f'- {w}' for w in review.weaknesses[:2])}

Provide the revised character as JSON:"""

        response = await self.reviewer_llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return character_data

    async def _revise_worldbuilding(
        self,
        world_data: dict[str, Any],
        review: ReviewResult,
        major: bool = False,
    ) -> dict[str, Any]:
        """Revise worldbuilding based on review."""
        system_prompt = """You are a worldbuilding expert.
Revise the world setting to address feedback.
Output valid JSON only."""

        issues_text = "\n".join([
            f"- {i.get('description', str(i))}" for i in review.issues[:3]
        ])

        user_prompt = f"""Revise this worldbuilding:

{json.dumps(world_data, indent=2)}

ADDRESS THESE ISSUES:
{issues_text}

Provide the revised worldbuilding as JSON:"""

        response = await self.reviewer_llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return world_data

    # Helper methods

    def _parse_review_response(self, response_content: str) -> ReviewResult:
        """Parse LLM review response into ReviewResult."""
        try:
            content = response_content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]

            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)

            data = json.loads(content)

            # Ensure data is a dict
            if not isinstance(data, dict):
                data = {}

            score = float(data.get("quality_score", 5))

            # Debug logging
            logger.info(f"Review parsed - Score: {score}, Threshold: {self.approval_threshold}")
            logger.info(f"Review strengths: {data.get('strengths', [])}")
            logger.info(f"Review weaknesses: {data.get('weaknesses', [])}")
            logger.info(f"Review recommendation: {data.get('recommendation', 'unknown')}")

            return ReviewResult(
                approved=score >= self.approval_threshold,
                quality_score=score,
                quality_level=self._get_quality_level(score),
                issues=data.get("issues", []) if isinstance(data.get("issues"), list) else [],
                strengths=data.get("strengths", []) if isinstance(data.get("strengths"), list) else [],
                weaknesses=data.get("weaknesses", []) if isinstance(data.get("weaknesses"), list) else [],
                recommendation=data.get("recommendation", "revise") if isinstance(data.get("recommendation"), str) else "revise",
                review_notes=data.get("notes", "") if isinstance(data.get("notes"), str) else "",
            )
        except (json.JSONDecodeError, ValueError) as e:
            # Log the actual response for debugging
            logger.error(f"Failed to parse review response: {e}")
            logger.error(f"Raw response content: {response_content[:500]}")
            return ReviewResult(
                approved=False,
                quality_score=5,
                quality_level=QualityLevel.ACCEPTABLE,
                review_notes=f"Could not parse review response: {str(e)}",
            )

    def _get_quality_level(self, score: float) -> QualityLevel:
        """Convert score to quality level."""
        if score >= 9:
            return QualityLevel.EXCEPTIONAL
        elif score >= 7:
            return QualityLevel.GOOD
        elif score >= 5:
            return QualityLevel.ACCEPTABLE
        else:
            return QualityLevel.POOR

    def _format_outline(self, data: dict[str, Any], original_title: str = "") -> str:
        """Format outline data as readable text.

        Args:
            data: Outline data from PlotAgent
            original_title: Original title to use (overrides any title in data)
        """
        # Ensure data is a dict
        if not isinstance(data, dict):
            data = {"title": original_title or "Novel Outline"}

        # ALWAYS use the original title passed in - never trust LLM output for title
        title = original_title or data.get("title", "")
        if not title:
            main_arc = data.get("main_arc", {})
            if isinstance(main_arc, dict):
                title = main_arc.get("title", "Novel Outline")
            else:
                title = "Novel Outline"
        lines = [f"# {title}", ""]

        # Get premise from either top level or main_arc
        premise = data.get("premise", "")
        if not premise:
            main_arc = data.get("main_arc", {})
            if isinstance(main_arc, dict):
                premise = main_arc.get("logline", "")
        if premise:
            lines.append(f"**Premise:** {premise}")
            lines.append("")

        # Get theme from main_arc
        main_arc = data.get("main_arc", {})
        if not isinstance(main_arc, dict):
            main_arc = {}

        theme = main_arc.get("theme", "")
        if theme:
            lines.append(f"**Theme:** {theme}")
            lines.append("")

        # Get main conflict
        main_conflict = main_arc.get("main_conflict", "")
        if main_conflict:
            lines.append(f"**Main Conflict:** {main_conflict}")
            lines.append("")

        # Get stakes
        stakes = main_arc.get("stakes", "")
        if stakes:
            lines.append(f"**Stakes:** {stakes}")
            lines.append("")

        # Format acts from main_arc
        acts = main_arc.get("acts") if isinstance(main_arc, dict) else None
        if acts and isinstance(acts, list):
            lines.append("## Story Structure")
            lines.append("")
            for i, act in enumerate(acts, 1):
                if not isinstance(act, dict):
                    continue
                lines.append(f"### Act {i}: {act.get('name', '') if isinstance(act.get('name'), str) else ''}")
                chapters_val = act.get("chapters")
                if chapters_val:
                    lines.append(f"**Chapters:** {chapters_val}")
                summary_val = act.get("summary")
                if summary_val:
                    lines.append(f"**Summary:** {summary_val}")
                arc_val = act.get("emotional_arc")
                if arc_val:
                    lines.append(f"**Emotional Arc:** {arc_val}")
                events_val = act.get("key_events")
                if events_val and isinstance(events_val, list):
                    lines.append("**Key Events:**")
                    for event in events_val:
                        lines.append(f"- {event}")
                lines.append("")
        else:
            # Fallback: use three-act structure if no acts provided
            lines.append("## Story Structure")
            lines.append("")
            lines.append("### Act 1: The Golden Age")
            lines.append("**Chapters:** 1-100")
            lines.append("**Summary:** The innocent beginning - Clara's arrival at Ashford Academy, first encounters with Julian, and the initial invitation into the elite world.")
            lines.append("")
            lines.append("### Act 2: The Gilded Cage")
            lines.append("**Chapters:** 101-250")
            lines.append("**Summary:** Discovery and entrapment - Clara enters the inner circle and slowly uncovers the darkness beneath the gilded surface.")
            lines.append("")
            lines.append("### Act 3: Shattered Glass")
            lines.append("**Chapters:** 251-350")
            lines.append("**Summary:** Escape and redemption - The truth is exposed, and Clara must find a way to break free from the cage.")
            lines.append("")

        # Format climax and resolution
        climax_val = main_arc.get("climax") if isinstance(main_arc, dict) else None
        if climax_val:
            lines.append("## Climax")
            lines.append(str(climax_val))
            lines.append("")

        resolution_val = main_arc.get("resolution") if isinstance(main_arc, dict) else None
        if resolution_val:
            lines.append("## Resolution")
            lines.append(str(resolution_val))
            lines.append("")

        # Format chapter summaries
        chapters = data.get("chapters", [])
        if chapters and isinstance(chapters, list):
            lines.append("## Chapter Summaries")
            lines.append("")
            for ch in chapters[:30]:
                if not isinstance(ch, dict):
                    continue
                ch_num = ch.get("chapter", ch.get("number", "?"))
                ch_title = ch.get("title", "")
                ch_summary = ch.get("summary", "")
                if ch_title or ch_summary:
                    lines.append(f"**Chapter {ch_num}:** {ch_title}")
                    if ch_summary:
                        lines.append(f"  {ch_summary[:200]}{'...' if len(ch_summary) > 200 else ''}")
                    lines.append("")

        return "\n".join(lines)

    def _format_character(self, data: dict[str, Any]) -> str:
        """Format character data as readable text."""
        # Ensure data is a dict
        if not isinstance(data, dict):
            data = {}

        lines = [f"# {data.get('name', 'Character')}", ""]

        if data.get("role"):
            lines.append(f"**Role:** {data['role']}")

        if data.get("personality"):
            lines.append(f"**Personality:** {data['personality']}")

        if data.get("backstory"):
            lines.append(f"**Backstory:** {data['backstory']}")

        return "\n".join(lines)

    def _format_worldbuilding(self, data: dict[str, Any]) -> str:
        """Format worldbuilding data as readable text."""
        # Ensure data is a dict
        if not isinstance(data, dict):
            data = {}

        lines = ["# World Building", ""]

        if data.get("society"):
            lines.append(f"**Society:** {data['society']}")

        locations = data.get("locations")
        if locations and isinstance(locations, list):
            lines.append("**Locations:**")
            for loc in locations[:5]:
                if isinstance(loc, dict):
                    lines.append(f"- {loc.get('name', 'Unknown')}")
                else:
                    lines.append(f"- {str(loc)}")

        return "\n".join(lines)
