"""Summary management for rolling summary updates.

This module provides the SummaryManager class that coordinates
chapter and arc summarization with the hierarchical story state.
"""

import logging
from pathlib import Path
from typing import Any

from src.llm.base import BaseLLM
from src.novel.auto_fixer import AutoFixer, AutoFixResult
from src.novel.chapter_summarizer import ArcSummarizer, ChapterSummarizer
from src.novel.consistency_verifier import VerificationResult
from src.novel.entity_extractor import EntityExtractor
from src.novel.hierarchical_state import CHAPTERS_PER_ARC, HierarchicalStoryState
from src.novel.knowledge_graph import KnowledgeGraph
from src.novel.continuity import ContinuityManager, StoryState
from src.novel.relation_inference import RelationInference
from src.novel.summaries import ArcSummary, ChapterSummary

logger = logging.getLogger(__name__)


class SummaryManager:
    """Manages rolling summary updates for hierarchical story state.

    This class coordinates:
    - Chapter summarization after each chapter is generated
    - Arc summarization every CHAPTERS_PER_ARC chapters
    - Global state updates as needed

    Attributes:
        hierarchical_state: HierarchicalStoryState instance
        chapter_summarizer: ChapterSummarizer instance
        arc_summarizer: ArcSummarizer instance
    """

    def __init__(
        self,
        storage_path: Path,
        novel_id: str,
        llm: BaseLLM,
        use_auto_fix: bool = True,
        entity_extractor: EntityExtractor | None = None,
        use_knowledge_graph: bool = True,
    ) -> None:
        """Initialize the summary manager.

        Args:
            storage_path: Base directory for storing state
            novel_id: Unique identifier for the novel
            llm: LLM instance for summarization
            use_auto_fix: Whether to enable automatic inconsistency fixing
            use_knowledge_graph: Whether to enable knowledge graph integration
        """
        self.hierarchical_state = HierarchicalStoryState(storage_path, novel_id)
        self.chapter_summarizer = ChapterSummarizer(llm)
        self.arc_summarizer = ArcSummarizer(llm)
        self._pending_arc_summarization: bool = False
        self.use_auto_fix = use_auto_fix
        self.entity_extractor = entity_extractor
        self._last_chapter_spec: Any | None = None
        self.continuity_manager = ContinuityManager()
        self._current_story_state: StoryState | None = None

        # T2-5: Initialize knowledge graph support
        self.use_knowledge_graph = use_knowledge_graph
        self.knowledge_graph: KnowledgeGraph | None = None
        self.relation_inference: RelationInference | None = None

        if use_auto_fix:
            self.auto_fixer = AutoFixer(llm=llm)
        else:
            self.auto_fixer = None  # type: ignore

        # T2-5: Initialize knowledge graph components if enabled
        if use_knowledge_graph:
            kg_storage_path = storage_path / "knowledge_graphs" / novel_id
            self.knowledge_graph = KnowledgeGraph(novel_id, kg_storage_path)
            self.entity_extractor = EntityExtractor(self.knowledge_graph, llm)
            self.relation_inference = RelationInference(self.knowledge_graph, llm)

    async def process_chapter(
        self,
        chapter_number: int,
        title: str,
        content: str,
        word_count: int | None = None,
    ) -> ChapterSummary:
        """Process a newly generated chapter.

        This method:
        1. Generates a chapter summary
        2. Updates the hierarchical state
        3. Triggers arc summarization if needed

        Args:
            chapter_number: Chapter number (1-indexed)
            title: Chapter title
            content: Full chapter text
            word_count: Optional word count

        Returns:
            Generated ChapterSummary
        """
        logger.info(f"Processing chapter {chapter_number}: {title}")

        # Generate chapter summary
        chapter_summary = await self.chapter_summarizer.summarize(
            chapter_number=chapter_number,
            title=title,
            content=content,
            word_count=word_count,
        )

        # Update hierarchical state
        self.hierarchical_state.update_after_chapter(chapter_number, chapter_summary)

        # Check if arc summarization is needed
        if self._should_summarize_arc(chapter_number):
            await self._summarize_current_arc(chapter_number)

        return chapter_summary

    async def process_chapter_with_autofix(
        self,
        chapter_number: int,
        title: str,
        content: str,
        max_fix_iterations: int = 3,
    ) -> tuple[ChapterSummary, VerificationResult, AutoFixResult | None]:
        """Process chapter with automatic consistency fixing.

        This method:
        1. Verifies content for inconsistencies
        2. If issues found and auto-fix enabled, attempts to fix them
        3. Re-verifies fixed content
        4. Generates chapter summary with (potentially fixed) content
        5. Updates hierarchical state

        Args:
            chapter_number: Chapter number (1-indexed)
            title: Chapter title
            content: Full chapter text
            max_fix_iterations: Maximum fix attempts (default: 3)

        Returns:
            Tuple of (summary, verification_result, auto_fix_result)
        """

        # 1. Verify content
        story_state = self._build_story_state()
        verification = self.auto_fixer.verify(
            content=content,
            chapter_number=chapter_number,
            story_state=story_state,
        )

        fixed_content = content
        auto_fix_result = None

        # 2. If issues and auto-fix enabled, try to fix
        if not verification.is_consistent and self.use_auto_fix:
            auto_fix_result = await self.auto_fixer.fix_and_regenerate(
                content=content,
                verification_result=verification,
                max_iterations=max_fix_iterations,
            )
            fixed_content = auto_fix_result.final_content

            # Re-verify fixed content
            if auto_fix_result.success:
                verification = self.auto_fixer.verify(
                    content=fixed_content,
                    chapter_number=chapter_number,
                    story_state=story_state,
                )

        # 3. Generate summary with (potentially fixed) content
        summary = await self.process_chapter(
            chapter_number=chapter_number,
            title=title,
            content=fixed_content,
        )
        # 4. Extract entities to knowledge graph (T2-5)
        if self.use_knowledge_graph and self.entity_extractor:
            try:
                extraction_result = await self.entity_extractor.extract_from_chapter(
                    chapter_num=chapter_number,
                    content=fixed_content,
                )

                # Infer relations (T2-5)
                relations = []
                if self.relation_inference and extraction_result.entities:
                    relations = self.relation_inference.infer_relations(
                        content=fixed_content,
                        entities=extraction_result.entities,
                        chapter=chapter_number,
                    )
                    # Add relations to knowledge graph
                    self.relation_inference.add_relations_to_knowledge_graph(relations)

                logger.info(
                    f"KG: Extracted {len(extraction_result.entities)} entities, "
                    f"{len(relations)} relations from chapter {chapter_number}"
                )
            except Exception as e:
                logger.warning(f"KG extraction failed for chapter {chapter_number}: {e}")

        # Update continuity manager with chapter content
        try:
            # Initialize story state if needed
            if self._current_story_state is None:
                self._current_story_state = StoryState(
                    chapter=0,
                    location="",
                    active_characters=[],
                    character_states={},
                    plot_threads=[],
                    key_events=[],
                )
            # Update story state
            self._current_story_state = self.continuity_manager.update_from_chapter(
                state=self._current_story_state,
                chapter_content=fixed_content,
                chapter_number=chapter_number,
            )
            logger.info(f"Updated continuity manager for chapter {chapter_number}")
        except Exception as e:
            logger.warning(f"Continuity update failed for chapter {chapter_number}: {e}")

        return summary, verification, auto_fix_result

    def _build_story_state(self) -> "StoryState | None":
        """Build StoryState from hierarchical state.

        Returns:
            StoryState if global state exists, None otherwise
        """
        from src.novel.continuity import StoryState

        if not self.hierarchical_state.global_state:
            return None

        gs = self.hierarchical_state.global_state

        key_events = []
        current_chapter = self.hierarchical_state.current_chapter
        for ch in range(max(1, current_chapter - 2), current_chapter + 1):
            summary = self.hierarchical_state.get_chapter_summary(ch)
            if summary and hasattr(summary, "key_events"):
                key_events.extend(summary.key_events)

        location = ""
        if hasattr(self, "_last_chapter_spec") and self._last_chapter_spec:
            location = getattr(self._last_chapter_spec, "location", "")

        return StoryState(
            chapter=self.hierarchical_state.current_chapter,
            location=location,
            active_characters=list(gs.main_characters.keys()),
            character_states=gs.main_characters,
            plot_threads=gs.main_plot_threads,
            key_events=key_events[-10:],
        )

    def _should_summarize_arc(self, chapter_number: int) -> bool:
        """Check if arc summarization should be triggered.

        Arc summarization happens:
        - Every CHAPTERS_PER_ARC chapters (at arc boundaries)
        - When an arc is complete

        Args:
            chapter_number: Current chapter number

        Returns:
            True if arc should be summarized
        """
        # Check if this chapter ends an arc
        return chapter_number % CHAPTERS_PER_ARC == 0

    async def _summarize_current_arc(self, current_chapter: int) -> None:
        """Summarize the current arc from its chapter summaries.

        Args:
            current_chapter: The chapter that triggered this summarization
        """
        arc_number = self.hierarchical_state.get_arc_number(current_chapter)
        start_chapter = (arc_number - 1) * CHAPTERS_PER_ARC + 1
        end_chapter = arc_number * CHAPTERS_PER_ARC

        logger.info(f"Summarizing arc {arc_number} (chapters {start_chapter}-{end_chapter})")

        # Collect all chapter summaries in this arc
        chapter_summaries: list[ChapterSummary] = []
        for ch in range(start_chapter, end_chapter + 1):
            summary = self.hierarchical_state.get_chapter_summary(ch)
            if summary is not None:
                chapter_summaries.append(summary)

        if not chapter_summaries:
            logger.warning(f"No chapter summaries found for arc {arc_number}")
            return

        # Generate arc summary
        arc_data = await self.arc_summarizer.summarize_arc(
            arc_number=arc_number,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            chapter_summaries=chapter_summaries,
        )

        # Create ArcSummary object
        arc_summary = ArcSummary(
            arc_number=arc_number,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            title=arc_data.get("title", f"第{arc_number}卷"),
            summary=arc_data.get("summary", ""),
            major_events=arc_data.get("major_events", []),
            character_arcs=arc_data.get("character_arcs", {}),
            world_changes=arc_data.get("world_changes", []),
            plot_threads_status=arc_data.get("plot_threads_status", {}),
            themes=arc_data.get("themes", []),
        )

        # Save to hierarchical state
        self.hierarchical_state.save_arc_summary(arc_summary)
        logger.info(f"Saved arc {arc_number} summary")

    def get_context_for_chapter(self, chapter: int) -> str:
        """Get hierarchical context for generating a chapter.

        Args:
            chapter: Chapter number to generate context for

        Returns:
            Context string for LLM
        """
        return self.hierarchical_state.get_context_for_chapter(chapter)

    def get_chapter_summary(self, chapter: int) -> ChapterSummary | None:
        """Get a specific chapter summary.

        Args:
            chapter: Chapter number

        Returns:
            ChapterSummary if exists, None otherwise
        """
        return self.hierarchical_state.get_chapter_summary(chapter)

    def get_arc_summary(self, arc_number: int) -> ArcSummary | None:
        """Get a specific arc summary.

        Args:
            arc_number: Arc number

        Returns:
            ArcSummary if exists, None otherwise
        """
        return self.hierarchical_state.get_arc_summary(arc_number)

    def update_global_characters(
        self,
        characters: dict[str, Any],
    ) -> None:
        """Update global character states.

        Args:
            characters: Dictionary of character states
        """
        if self.hierarchical_state.global_state is None:
            return

        from src.novel.continuity import CharacterState

        for name, state_dict in characters.items():
            if isinstance(state_dict, CharacterState):
                self.hierarchical_state.global_state.main_characters[name] = state_dict
            elif isinstance(state_dict, dict):
                self.hierarchical_state.global_state.main_characters[name] = CharacterState(
                    **state_dict
                )

        self.hierarchical_state.save_global_state()

    def update_global_plot_threads(
        self,
        plot_threads: list[Any],
    ) -> None:
        """Update global plot threads.

        Args:
            plot_threads: List of plot thread data
        """
        if self.hierarchical_state.global_state is None:
            return

        from src.novel.continuity import PlotThread

        self.hierarchical_state.global_state.main_plot_threads = []
        for pt in plot_threads:
            if isinstance(pt, PlotThread):
                self.hierarchical_state.global_state.main_plot_threads.append(pt)
            elif isinstance(pt, dict):
                self.hierarchical_state.global_state.main_plot_threads.append(PlotThread(**pt))

        self.hierarchical_state.save_global_state()

    def get_total_chapters(self) -> int:
        """Get total chapters written so far.

        Returns:
            Total chapter count
        """
        if self.hierarchical_state.global_state is None:
            return 0
        return self.hierarchical_state.global_state.total_chapters

    def get_current_arc(self) -> int:
        """Get current arc number.

        Returns:
            Current arc number (1-indexed)
        """
        if self.hierarchical_state.global_state is None:
            return 1
        return self.hierarchical_state.global_state.current_arc

    def get_related_characters(self, character_name: str, max_depth: int = 2) -> list[str]:
        """Query characters related to the specified character.

        Use case: "Chapter 200, want to know all characters related to the protagonist"

        Args:
            character_name: Character name to search for
            max_depth: Maximum relationship depth to traverse

        Returns:
            List of related character names
        """
        if not self.use_knowledge_graph or not self.knowledge_graph:
            return []

        entity = self.knowledge_graph.get_entity_by_name(character_name)
        if not entity:
            return []

        related = self.knowledge_graph.query_related_entities(entity.node_id, max_depth=max_depth)
        return [e.properties.get("name", e.node_id) for e in related if e.node_type == "character"]

    def get_character_timeline(self, character_name: str) -> list[dict[str, Any]]:
        """Get the complete timeline for a character.

        Args:
            character_name: Character name to get timeline for

        Returns:
            List of timeline events (chapter, event_type, description, details)
        """
        if not self.use_knowledge_graph or not self.knowledge_graph:
            return []

        entity = self.knowledge_graph.get_entity_by_name(character_name)
        if not entity:
            return []

        return self.knowledge_graph.get_entity_timeline(entity.node_id)
