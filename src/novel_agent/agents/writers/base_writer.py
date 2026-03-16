# src/agents/writers/base_writer.py
"""Base class for genre-specific writer agents."""

import logging
from abc import abstractmethod
from typing import Any

from src.novel_agent.agents.base import AgentResult, BaseAgent
from src.novel_agent.novel.continuity import StoryState
from src.novel_agent.novel.outline_manager import ChapterSpec
from src.novel_agent.utils.token_budget import TokenBudgetConfig, TokenBudgetManager

logger = logging.getLogger(__name__)


def get_language_instruction(language: str | None) -> str:
    """Return a language instruction block to append to prompts.

    If language is Chinese ('zh'), return a block that enforces Chinese
    writing. Otherwise, return an empty string for default English behavior.
    """
    if language == "zh":
        return """
【语言要求】
- 必须使用中文写作
- 所有叙述、对话、描写都用中文
- 保持中文文学风格
- 避免翻译腔
"""
    return ""


class BaseWriter(BaseAgent):
    """Base class for specialized writer agents.

    Each genre-specific writer (Sci-Fi, Fantasy, Romance, History, Military)
    should inherit from this class and provide:
    - Domain-specific knowledge prompts
    - Genre-appropriate writing style
    - Specialized validation rules
    - Learning system integration for improved quality
    """

    # Subclasses should define their genre
    GENRE: str = "general"

    # Subclasses should define domain knowledge
    DOMAIN_KNOWLEDGE: str = ""

    # Default token budget configuration
    DEFAULT_TOKEN_BUDGET: int = 11000  # ~11k tokens for context (leaving room for system/response)

    def __init__(
        self,
        name: str,
        llm: Any,
        memory: Any | None = None,
        constitution_validator: Any | None = None,
        glossary: Any | None = None,
        token_budget_manager: TokenBudgetManager | None = None,
        token_budget_config: TokenBudgetConfig | None = None,
        fact_injector: Any | None = None,
    ) -> None:
        """Initialize the writer.

        Args:
            name: Human-readable name for the writer
            llm: LLM instance for text generation
            memory: Memory system for context storage (optional)
            constitution_validator: Constitutional rules validator (optional)
            glossary: Glossary manager for terminology (optional)
            token_budget_manager: TokenBudgetManager instance (optional)
            token_budget_config: Configuration for token budget (optional)
            fact_injector: RelevantFactInjector instance (optional)
        """
        # Call parent init (BaseAgent)
        super().__init__(
            name=name,
            llm=llm,
            memory=memory,
            constitution_validator=constitution_validator,
            glossary=glossary,
        )

        # Initialize token budget manager
        if token_budget_manager is not None:
            self._token_budget = token_budget_manager
        else:
            config = token_budget_config or TokenBudgetConfig(
                max_context_tokens=16000,  # Default for most models
                system_prompt_reserve=500,
                response_reserve=4096,
                safety_margin=100,
            )
            self._token_budget = TokenBudgetManager(config)

        # Initialize fact injector (optional)
        self._fact_injector = fact_injector

    @abstractmethod
    async def write_chapter(
        self,
        chapter_number: int,
        chapter_outline: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        style_guide: str | None = None,
        learning_hints: list[str] | None = None,
        market_keywords: dict[str, Any] | None = None,
        language: str | None = None,
        # NEW continuity parameters
        story_state: StoryState | None = None,
        previous_chapter_summary: str | None = None,
        # NEW context parameters
        relationships: list[dict[str, Any]] | None = None,
        full_outline: dict[str, Any] | None = None,
        world_settings: dict[str, Any] | None = None,
    ) -> str:
        """Write a chapter.

        Args:
            chapter_number: Chapter number being written
            chapter_outline: Outline for this chapter
            characters: List of character profiles appearing in this chapter
            world_context: Relevant world-building context
            style_guide: Optional style guidelines
            learning_hints: Optional learned patterns from successful chapters
            market_keywords: Optional market research keywords (seo_keywords, popular_phrases, trending_elements)
            language: Optional language hint for content generation (e.g., 'en', 'zh')
            story_state: Optional story state for continuity tracking
            previous_chapter_summary: Optional summary of the previous chapter
            relationships: Optional character relationship context
            full_outline: Optional complete novel outline for context
            world_settings: Optional detailed world settings

        Returns:
            Written chapter content
        """
        pass

    async def write_chapter_with_context(
        self,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        previous_chapter_summary: str | None = None,
        relationships: list[dict[str, Any]] | None = None,
        full_outline: dict[str, Any] | None = None,
        world_settings: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """Write a chapter with full continuity context.

        This method wraps write_chapter with additional context from
        the story state and chapter specification.

        Args:
            chapter_spec: Chapter specification
            story_state: Current story state
            characters: List of character profiles
            world_context: World-building context
            previous_chapter_summary: Summary of previous chapter
            **kwargs: Additional arguments passed to write_chapter

        Returns:
            Written chapter content
        """
        # Build continuity prompt
        continuity_prompt = self._build_continuity_prompt(
            story_state=story_state,
            previous_summary=previous_chapter_summary or "",
            chapter_number=chapter_spec.number,
        )

        # Combine chapter summary with continuity prompt
        enhanced_outline = f"{chapter_spec.summary}\n{continuity_prompt}"

        # Call write_chapter with continuity info
        return await self.write_chapter(
            chapter_number=chapter_spec.number,
            chapter_outline=enhanced_outline,
            characters=characters,
            world_context=world_context,
            story_state=story_state,
            previous_chapter_summary=previous_chapter_summary,
            relationships=relationships,
            full_outline=full_outline,
            world_settings=world_settings,
            **kwargs,
        )

    def _build_continuity_prompt(
        self,
        story_state: StoryState | None,
        previous_summary: str,
        chapter_number: int,
        max_tokens: int | None = None,
    ) -> str:
        """Build a continuity prompt from story state with token budget enforcement.

        Args:
            story_state: Current story state
            previous_summary: Summary of previous chapter
            chapter_number: Current chapter number
            max_tokens: Maximum tokens for the prompt (uses default if None)

        Returns:
            Continuity prompt string, enforced to token budget
        """
        # 总是构建连续性提示词，即使story_state是空的或最小的
        parts = ["【连续性上下文】"]

        if chapter_number > 1:
            parts.append(f"当前章节: 第{chapter_number}章")
            parts.append(f"前序章节: 第1-{chapter_number - 1}章")

        # Always add previous chapter summary if available
        if previous_summary:
            parts.append(f"\n【前章概要】\n{previous_summary}")

        # Add story state if available
        if story_state:
            max_tokens = max_tokens or self.DEFAULT_TOKEN_BUDGET

            # Build context dictionary for token budget enforcement
            context: dict[str, Any] = {
                "header": f"【连续性上下文 - 第{chapter_number}章】",
                "location": f"当前地点：{story_state.location}",
                "active_characters": f"在场角色：{', '.join(story_state.active_characters)}",
            }

            # Add character states as a list for better truncation handling
            if story_state.character_states:
                character_state_lines = []
                for name, state in story_state.character_states.items():
                    status_text = f"- {name}: {state.status}"
                    if state.status == "dead":
                        status_text += " (此角色已死亡，不能出现)"
                    elif state.status == "fused":
                        status_text += f" (此角色已与{state.location}融合)"
                    character_state_lines.append(status_text)
                context["character_states"] = "\n角色状态：\n" + "\n".join(character_state_lines)

            # Define truncation priority - first items are truncated first
            # Essential info (header, location, active_characters) should not be truncated
            truncation_priority = ["previous_summary", "character_states"]

            # Apply token budget enforcement
            enforced_context, token_count = self._token_budget.enforce_budget(
                context, max_tokens=max_tokens, truncation_priority=truncation_priority
            )
            # Log token usage for monitoring (T5: context budget logging)
            logger.info(
                f"[TokenBudget] Chapter {chapter_number}: "
                f"{token_count.total} tokens used, "
                f"budget={max_tokens}, "
                f"truncated={token_count.truncated}, "
                f"sections={list(token_count.by_section.keys())}"
            )

            # Reconstruct prompt from enforced context and add to parts
            if "header" in enforced_context:
                parts.append("\n" + enforced_context["header"])
            if "location" in enforced_context:
                parts.append(enforced_context["location"])
            if "active_characters" in enforced_context:
                parts.append(enforced_context["active_characters"])
            if "character_states" in enforced_context:
                parts.append(enforced_context["character_states"])

        # Add consistency reminder
        parts.append("""
【一致性提醒】
1. 人物名字、称呼要保持一致（不要一会儿大小姐一会儿二小姐）
2. 重要剧情事件需要在前面章节有铺垫
3. 角色头衔、身份要保持一致
4. 丫鬟等配角名字要统一
""")

        return "\n".join(parts)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute writing task.

        Args:
            input_data: Must contain:
                - chapter_number: int
                - chapter_outline: str
                - characters: list
                - world_context: dict
                Optional:
                - style_guide: str
                - learning_hints: list[str]
                - market_keywords: dict
                - language: str
                - story_state: StoryState
                - previous_chapter_summary: str
                - relationships: list[dict[str, Any]]
                - full_outline: dict[str, Any]
                - world_settings: dict[str, Any]

        Returns:
            AgentResult with chapter content in data['content']
        """
        try:
            content = await self.write_chapter(
                chapter_number=input_data["chapter_number"],
                chapter_outline=input_data["chapter_outline"],
                characters=input_data.get("characters", []),
                world_context=input_data.get("world_context", {}),
                style_guide=input_data.get("style_guide"),
                learning_hints=input_data.get("learning_hints"),
                market_keywords=input_data.get("market_keywords"),
                language=input_data.get("language"),
                # NEW: pass continuity params
                story_state=input_data.get("story_state"),
                previous_chapter_summary=input_data.get("previous_chapter_summary"),
                # NEW: pass context params
                relationships=input_data.get("relationships"),
                full_outline=input_data.get("full_outline"),
                world_settings=input_data.get("world_settings"),
            )

            return AgentResult(
                success=True,
                data={"content": content, "chapter_number": input_data["chapter_number"]},
            )
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Writing failed: {str(e)}"],
            )

    def get_fact_context(
        self,
        chapter_number: int,
        active_entities: list[str] | None = None,
    ) -> str:
        """Get relevant fact context for chapter generation.

        This method retrieves relevant facts from the fact injector
        if one is configured.

        Args:
            chapter_number: Current chapter number
            active_entities: Entities currently in the scene

        Returns:
            Fact context string, or empty string if no injector
        """
        if self._fact_injector is None:
            return ""

        return self._fact_injector.get_context_string(
            current_chapter=chapter_number,
            active_entities=active_entities,
        )
