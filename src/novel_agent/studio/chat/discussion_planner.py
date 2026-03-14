# src/studio/chat/discussion_planner.py
"""Interactive discussion-based project planner with multi-round dialogue."""

import json
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Any

from src.novel_agent.llm.base import BaseLLM
from src.novel_agent.studio.chat.creative_cache import DiscussionCache
from src.novel_agent.studio.chat.streaming_progress import (
    GenerationStage,
    ProgressUpdate,
)
from src.novel_agent.studio.core.state import NovelProject, ProjectStatus, StudioState

logger = logging.getLogger(__name__)


@dataclass
class DiscussionContext:
    """Tracks the creative discussion state."""

    user_ideas: list[str] = field(default_factory=list)
    ai_questions: list[str] = field(default_factory=list)
    clarifications: dict[str, str] = field(default_factory=dict)
    current_stage: str = "initial"  # initial, questioning, preview, refining, confirmed
    accumulated_context: str = ""  # Combined context from all exchanges
    generated_outline: str | None = None
    generated_characters: list[dict[str, Any]] = field(default_factory=list)
    user_feedback: list[str] = field(default_factory=list)
    round_count: int = 0  # Track discussion rounds

    # Truncation tracking
    truncation_count: int = 0
    original_context_length: int = 0
    truncated_context_length: int = 0


class DiscussionPlanner:
    """Multi-round discussion planner for creative projects."""

    def __init__(
        self,
        llm: BaseLLM,
        state: StudioState,
        enable_cache: bool = True,
        max_context_tokens: int = 6000,
        truncation_strategy: str = "summarize"
    ):
        self.llm = llm
        self.state = state
        self.context = DiscussionContext()
        self.cache = DiscussionCache() if enable_cache else None
        self.max_context_tokens = max_context_tokens
        self.truncation_strategy = truncation_strategy
        self.llm = llm
        self.state = state
        self.context = DiscussionContext()
        self.cache = DiscussionCache() if enable_cache else None

    async def start_discussion(self, initial_idea: str) -> dict[str, Any]:
        """Start a new creative discussion."""
        self.context = DiscussionContext()
        self.context.user_ideas.append(initial_idea)
        self.context.current_stage = "initial"
        self.context.round_count = 1

        # Analyze initial idea and generate clarifying questions
        response = await self._generate_questions(initial_idea)

        return {
            "stage": "questioning",
            "message": response["message"],
            "questions": response["questions"],
            "suggestions": response.get("suggestions", []),
            "creative_prompts": response.get("creative_prompts", []),
        }

    async def continue_discussion(self, user_input: str) -> dict[str, Any]:
        """Continue an ongoing discussion with user input."""
        self.context.round_count += 1

        # Check if user wants to generate
        if any(
            keyword in user_input.lower()
            for keyword in ["生成", "create", "开始", "start", "满意", "ok", "好"]
        ):
            if self.context.current_stage == "preview":
                return await self.confirm_and_create()
            else:
                # Check if we have enough info
                if await self._check_minimum_info():
                    return await self._generate_preview()
                else:
                    return await self._generate_followup_questions()

        # Check if user wants to generate cover from preview
        if self.context.current_stage == "preview" and "封面" in user_input:
            cover_result = await self.generate_cover_suggestion()
            if cover_result.get("success"):
                return {
                    "stage": "cover_preview",
                    "message": "🎨 封面设计建议：\n\n"
                    f"标题：{cover_result.get('title')}\n"
                    f"风格：{cover_result.get('recommended_style')}\n"
                    f"提示词：{cover_result.get('suggestion', 'N/A')[:200]}...\n\n"
                    "输入 `确认生成` 生成实际封面，或继续讨论修改想法。",
                    "cover_suggestion": cover_result,
                }
            else:
                return {
                    "stage": "cover_preview",
                    "message": "⚠️ 无法生成封面建议。请确保已设置 ZHIPUAI_API_KEY。",
                }

        # Check if user is providing clarifications or asking for modifications
        if self.context.current_stage == "preview":
            # User is giving feedback on the preview
            return await self.refine_plan(user_input)
        else:
            # User is providing clarifications
            clarifications = self._parse_clarifications(user_input)
            return await self.provide_clarifications(clarifications)

    async def provide_clarifications(self, answers: dict[str, str]) -> dict[str, Any]:
        """Process user answers to clarifying questions."""
        self.context.clarifications.update(answers)

        # Check if we have enough information to generate preview
        has_minimum_info = await self._check_minimum_info()

        if has_minimum_info:
            # Generate detailed preview
            return await self._generate_preview()
        else:
            # Ask more questions
            return await self._generate_followup_questions()

    async def refine_plan(self, feedback: str) -> dict[str, Any]:
        """Handle user feedback and refine the plan."""
        self.context.user_feedback.append(feedback)
        self.context.current_stage = "refining"

        # Parse what needs to be changed
        changes = await self._parse_feedback(feedback)

        # Regenerate with modifications
        return await self._regenerate_with_changes(changes)

    async def confirm_and_create(self) -> dict[str, Any]:
        """Confirm plan and create project with all content."""
        self.context.current_stage = "confirmed"

        try:
            # Create project
            project = await self._create_project()

            # Save detailed outline
            await self._save_detailed_outline(project.id)

            # Save all characters
            await self._save_all_characters(project.id)

            chapter_count = (
                self.context.generated_outline.count("Chapter")
                if self.context.generated_outline
                else 0
            )

            return {
                "success": True,
                "project_id": project.id,
                "project": project,
                "outline_chapters": chapter_count,
                "character_count": len(self.context.generated_characters),
                "message": f"✅ 项目 '{project.title}' 创建成功！\n"
                f"📚 包含 {chapter_count} 章详细大纲\n"
                f"👥 {len(self.context.generated_characters)} 个角色设定\n"
                f"\n接下来可以使用：\n"
                f"• `/write chapter 1` 开始写作\n"
                f"• `/outline view` 查看完整大纲\n"
                f"• `/character list` 查看角色列表",
            }
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
            }

    async def _generate_questions(self, idea: str) -> dict[str, Any]:
        """Generate clarifying questions based on initial idea."""
        system_prompt = """你是「创意炼金术士」——一位专业的故事创意顾问。
你的任务是通过深度对话，帮助作者将碎片化的想法打磨成完整的创作蓝图。

【核心能力】
1. 敏锐洞察：从简短描述中捕捉创作意图
2. 精准提问：提出能激发思考的关键问题
3. 创意引导：提供选项帮助用户明确方向
4. 结构化思维：将混沌的想法组织成创作要素

【输出要求】
必须输出有效的 JSON 格式：
{
    "message": "问候和分析（2-3句话）",
    "questions": ["问题1", "问题2", "问题3", "问题4", "问题5"],
    "suggestions": ["设计建议1", "设计建议2"],
    "creative_prompts": ["激发灵感的提问1", "激发灵感的提问2"]
}

【提问策略】
- 问题要开放但聚焦
- 避免是/否问题
- 每次深入一个维度
- 用括号提供选项示例"""

        user_prompt = f"""用户的故事创意：
{idea}

请分析这个想法，并提出5个关键问题来帮助完善它。
记住：你是创意炼金术士，要激发用户的创作热情！"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            return {
                "message": "让我们深入探讨一下你的想法！",
                "questions": [
                    "主角是谁？（年龄、性别、职业、核心特质）",
                    "故事的基调是什么？（轻松/黑暗/悬疑/浪漫等）",
                    "主要冲突是什么？（主角想要什么，什么在阻止TA？）",
                    "发生在什么世界？（现代/古代/科幻/奇幻等）",
                    "有什么特别想探索的主题吗？",
                ],
                "suggestions": [
                    "考虑加入一个独特的新鲜元素",
                    "思考主角最明显的缺点是什么",
                ],
                "creative_prompts": [
                    "如果主角的秘密被最信任的人发现，会发生什么？",
                    "什么会让主角放弃一切？",
                ],
            }

    async def _generate_followup_questions(self) -> dict[str, Any]:
        """Generate follow-up questions based on current context."""
        system_prompt = """基于已收集的信息，生成深入的追问。
输出JSON：
{
    "message": "总结当前进度",
    "questions": ["追问1", "追问2", "追问3"],
    "progress": "已确定/还需确定",
    "estimated_rounds": 2
}"""

        context = self._build_full_context()

        user_prompt = f"""当前讨论进度：
{context}

还需要什么信息才能生成完整方案？请提出追问。"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(content)

            return {
                "stage": "questioning",
                "message": result.get("message", "让我们继续完善："),
                "questions": result.get("questions", []),
            }
        except Exception as e:
            logger.error(f"Failed to generate followup: {e}")
            return {
                "stage": "questioning",
                "message": "让我们继续完善创意：",
                "questions": [
                    "能详细描述一下主角的外貌和性格吗？",
                    "故事的起点是什么？（主角的日常如何被打破？）",
                    "主角最终要达到什么目标？",
                ],
            }

    async def _check_minimum_info(self) -> bool:
        """Check if we have minimum required information using LLM."""
        if len(self.context.clarifications) < 3:
            return False

        system_prompt = """评估是否已收集足够信息生成完整大纲。
需要：主角、类型/基调、核心冲突。
输出JSON：{"sufficient": true/false, "missing": ["缺少什么"], "reason": "原因"}"""

        context = self._build_full_context()

        user_prompt = f"""已收集的信息：
{context}

是否足够生成完整小说大纲？"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(content)
            return result.get("sufficient", False)
        except Exception as e:
            logger.error(f"Failed to check minimum info: {e}")
            # Fallback: check basic length
            return len(self.context.clarifications) >= 5

    async def _generate_preview(self) -> dict[str, Any]:
        """Generate detailed outline and character preview (without progress)."""
        return await self.generate_preview_with_progress(progress_callback=None)

    async def generate_preview_with_progress(
        self, progress_callback: Callable[[ProgressUpdate], None] | None = None
    ) -> dict[str, Any]:
        """Generate preview with streaming progress updates.

        Args:
            progress_callback: Optional callback to receive progress updates

        Returns:
            Same as _generate_preview but with progress reporting
        """
        self.context.current_stage = "preview"

        # Combine all context
        full_context = self._build_full_context()

        # Check cache first
        if self.cache:
            cached_outline = self.cache.get_outline(full_context)
            if cached_outline:
                logger.info("Using cached outline")
                outline = cached_outline
                if progress_callback:
                    progress_callback(
                        ProgressUpdate(
                            stage=GenerationStage.OUTLINE_STRUCTURE,
                            message="📐 使用缓存的大纲",
                            progress_percent=25,
                            detail="从缓存加载大纲结构",
                        )
                    )
            else:
                # Report outline generation start
                if progress_callback:
                    progress_callback(
                        ProgressUpdate(
                            stage=GenerationStage.OUTLINE_STRUCTURE,
                            message="📐 构建故事结构框架...",
                            progress_percent=10,
                            detail="设计三幕结构：建置、对抗、解决",
                        )
                    )

                # Generate outline
                outline = await self._generate_detailed_outline(full_context)
                # Cache the result
                if self.cache:
                    self.cache.set_outline(full_context, outline)
        else:
            # Report outline generation start
            if progress_callback:
                progress_callback(
                    ProgressUpdate(
                        stage=GenerationStage.OUTLINE_STRUCTURE,
                        message="📐 构建故事结构框架...",
                        progress_percent=10,
                        detail="设计三幕结构：建置、对抗、解决",
                    )
                )

            # Generate outline
            outline = await self._generate_detailed_outline(full_context)

        self.context.generated_outline = outline

        # Report outline completion
        if progress_callback:
            chapter_count = outline.count("Chapter") if outline else 0
            progress_callback(
                ProgressUpdate(
                    stage=GenerationStage.OUTLINE_CHAPTERS,
                    message="✨ 大纲主体生成完成",
                    progress_percent=50,
                    detail=f"共 {chapter_count} 章详细大纲",
                )
            )

        # Check cache for characters
        if self.cache:
            cached_characters = self.cache.get_characters(full_context, outline)
            if cached_characters:
                logger.info("Using cached characters")
                characters = cached_characters
                if progress_callback:
                    progress_callback(
                        ProgressUpdate(
                            stage=GenerationStage.CHARACTERS_CONCEPT,
                            message="👤 使用缓存的角色设定",
                            progress_percent=75,
                            detail=f"从缓存加载 {len(characters)} 个角色",
                        )
                    )
            else:
                # Report character generation start
                if progress_callback:
                    progress_callback(
                        ProgressUpdate(
                            stage=GenerationStage.CHARACTERS_CONCEPT,
                            message="👤 开始构思角色阵容...",
                            progress_percent=60,
                            detail="基于大纲分析角色需求",
                        )
                    )

                # Generate characters
                characters = await self._generate_rich_characters(full_context, outline)
                # Cache the result
                if self.cache:
                    self.cache.set_characters(full_context, outline, characters)
        else:
            # Report character generation start
            if progress_callback:
                progress_callback(
                    ProgressUpdate(
                        stage=GenerationStage.CHARACTERS_CONCEPT,
                        message="👤 开始构思角色阵容...",
                        progress_percent=60,
                        detail="基于大纲分析角色需求",
                    )
                )

            # Generate characters
            characters = await self._generate_rich_characters(full_context, outline)

        self.context.generated_characters = characters

        # Report completion
        if progress_callback:
            progress_callback(
                ProgressUpdate(
                    stage=GenerationStage.COMPLETE,
                    message="✅ 方案生成完成！",
                    progress_percent=100,
                    detail=f"共生成 {outline.count('Chapter') if outline else 0} 章大纲，{len(characters)} 个角色",
                )
            )

        # Extract summary for display
        outline_summary = self._extract_outline_summary(outline)

        # Generate cover suggestion
        cover_suggestion = await self.generate_cover_suggestion()

        return {
            "stage": "preview",
            "message": "✨ 基于我们的讨论，我为你生成了完整方案：",
            "outline_preview": outline_summary,
            "outline_full": outline,
            "characters": characters[:5],
            "outline_stats": {
                "total_chapters": outline.count("Chapter"),
                "estimated_words": outline.count("Chapter") * 2500,
            },
            "cover_suggestion": cover_suggestion if cover_suggestion.get("success") else None,
            "next_actions": [
                "输入「满意，创建项目」- 开始创建",
                "输入修改意见 - 例如：「主角再强势一点」",
                "输入「显示完整大纲」- 查看全部内容",
                "输入「生成封面」- 生成书籍封面",
            ],
        }

    async def _generate_detailed_outline(self, context: str) -> str:
        """Generate a very detailed outline with full chapter breakdowns."""
        system_prompt = """你是「架构大师」——专业的小说结构设计师。

【任务】
基于完整的创意讨论，生成一本可立即执行写作的长篇小说大纲。

【输出要求】
1. 必须是可直接用于创作的详细大纲
2. 每章包含：标题、300字摘要、情节点、情感转折、角色出场、悬念设置
3. 三幕结构清晰：第一幕(建置25%)、第二幕(对抗50%)、第三幕(解决25%)
4. 使用专业理论：Save the Cat节拍表、英雄之旅、情节点、情感节拍

【详细大纲格式】
# 《小说标题》

## 核心设定
**一句话梗概：**
**主题：**
**基调：**
**目标读者：**

## 世界观速览
**时间、地点、规则、社会结构**

## 角色阵容
**主角：** 姓名 + 一句话描述 + 核心欲望 + 核心恐惧
**反派：** 姓名 + 动机 + 与主角的关系
**重要配角：** 每个配角的姓名、功能、与主角的关系

## 第一幕：标题（Setup）Chapters 1-12
**功能、情绪弧线、关键情节点**

#### Chapter 1: 章节标题
**功能定位、字数、场景、角色出场**
**摘要：**（300字详细摘要）
**情节点：** 场景1→场景2→场景3
**情感节拍：** 开场情绪→转折→结尾情绪
**关键对话：**（1-2句标志性对话）
**伏笔：**（为后续章节埋下的伏笔）
**悬念：**（章末钩子）

[Chapter 2-12 同样详细...]

## 第二幕A：标题（Rising Action）Chapters 13-24
[同样详细...]

## 第二幕B：标题（Dark Night）Chapters 25-36
[同样详细...]

## 第三幕：标题（Climax）Chapters 37-48
[同样详细...]

【质量标准】
- 每章必须有明确的情感转折
- 每章结尾必须有悬念
- 角色动机必须在情节中体现
- 主题必须通过情节和对话展现"""

        user_prompt = f"""基于以下完整的创意讨论，请生成专业级详细大纲：

{context}

要求：
1. 生成48章的详细大纲（中长篇小说标准）
2. 每章300字以上摘要
3. 包含完整的三幕结构
4. 详细列出情节点、情感转折、悬念
5. 明确角色出场安排
6. 确保章节间有连贯性和递进感

请开始创作："""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000,
            )

            return response.content
        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            return f"# 生成失败\n\n错误：{str(e)}\n\n请重试。"

    async def _generate_rich_characters(self, context: str, outline: str) -> list[dict[str, Any]]:
        """Generate rich character profiles (main + supporting)."""
        system_prompt = """你是「灵魂雕塑家」——传奇的角色设计师。

【任务】
基于故事大纲和创意讨论，生成完整的角色阵容。
必须包含：主角1人、反派1人、重要配角3-5人。

【每个角色的详细设定】
{
    "name": "角色全名",
    "role": "主角/反派/导师/盟友/对手",
    "importance": "主要/次要",
    "basic_info": {"age": 25, "gender": "", "occupation": "", "social_status": ""},
    "appearance": {
        "height": "", "build": "", "hair": "", "eyes": "",
        "distinctive_features": "", "first_impression": ""
    },
    "personality": {
        "mbti": "", "enneagram": "",
        "core_traits": [], "strengths": [], "weaknesses": [],
        "fears": [], "desires": [], "values": [],
        "speech_pattern": "", "humor": ""
    },
    "backstory": {"origin": "", "childhood": "", "traumas": "", "triumphs": ""},
    "story_role": {
        "function": "", "arc": "",
        "goals": {"external": "", "internal": ""},
        "motivation": "", "conflict": "", "transformation": ""
    },
    "relationships": [{"with": "", "type": "", "dynamic": ""}],
    "abilities": {"initial": [], "mid": [], "final": [], "weaknesses": []},
    "voice": {"sample_dialogue": ["", "", ""]}
}

【生成策略】
1. 主角必须令人共情，有明确缺陷和成长空间
2. 反派必须有合理动机，不能脸谱化
3. 配角必须有独立故事线
4. 所有角色关系必须复杂有层次
5. 角色设计必须服务于主题"""

        user_prompt = f"""基于故事大纲和创意讨论，生成完整角色阵容。

创意背景：
{context}

故事大纲（节选）：
{outline[:2000]}

请生成5-8个完整角色的详细设定，用JSON格式输出数组。"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=4000,
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]

            characters = json.loads(content)

            # Ensure we have the required fields
            if not isinstance(characters, list):
                characters = [characters]

            return characters

        except Exception as e:
            logger.error(f"Failed to generate characters: {e}")
            # Fallback: create basic characters
            return [
                {
                    "name": "主角（待命名）",
                    "role": "主角",
                    "age": 17,
                    "appearance": "待完善",
                    "personality": {"traits": ["勇敢", "好奇"], "strengths": [], "weaknesses": []},
                    "backstory": "待完善",
                    "goals": "实现目标",
                    "arc": "成长弧线",
                },
                {
                    "name": "反派（待命名）",
                    "role": "反派",
                    "age": 35,
                    "appearance": "待完善",
                    "personality": {
                        "traits": ["野心勃勃", "复杂"],
                        "strengths": [],
                        "weaknesses": [],
                    },
                    "backstory": "待完善",
                    "goals": "阻止主角",
                    "arc": "悲剧弧线",
                },
            ]

    def _parse_clarifications(self, user_input: str) -> dict[str, str]:
        """Parse clarifications from user input."""
        # Simple implementation: treat the whole input as one clarification
        # In a more advanced version, this could use LLM to parse structured answers
        key = f"clarification_{len(self.context.clarifications) + 1}"
        return {key: user_input}

    def _build_full_context(self) -> str:
        """Build complete context from discussion."""
        context_parts = [
            "=== 用户的创意想法 ===",
            "\n".join(self.context.user_ideas),
            "",
            "=== 澄清的问题和答案 ===",
        ]

        for question, answer in self.context.clarifications.items():
            context_parts.append(f"Q: {question}")
            context_parts.append(f"A: {answer}")
            context_parts.append("")

        if self.context.user_feedback:
            context_parts.extend(
                [
                    "",
                    "=== 用户的修改反馈 ===",
                    "\n".join(self.context.user_feedback),
                ]
            )

        full_context = "\n".join(context_parts)

        # Apply truncation if needed
        return self._truncate_context(full_context)

    def _extract_outline_summary(self, outline: str) -> str:
        """Extract a summary of the outline for display."""
        lines = outline.split("\n")
        summary_lines = []

        # Get title
        for line in lines[:20]:
            if line.startswith("# 《") or line.startswith("# "):
                summary_lines.append(line)
                break

        # Get core concept
        summary_lines.append("")
        summary_lines.append("## 核心设定")
        for line in lines:
            if "一句话梗概" in line or "主题" in line or "基调" in line:
                summary_lines.append(line)

        # Get first few chapters
        summary_lines.append("")
        summary_lines.append("## 前几章预览")
        chapter_count = 0
        for line in lines:
            if line.startswith("#### Chapter"):
                if chapter_count < 3:
                    summary_lines.append(line)
                    chapter_count += 1
                else:
                    summary_lines.append("...")
                    break
            elif chapter_count > 0 and line.startswith("**摘要**"):
                summary_lines.append(line[:200] + "..." if len(line) > 200 else line)

        return "\n".join(summary_lines[:50])  # Limit length

    async def _parse_feedback(self, feedback: str) -> dict[str, Any]:
        """Parse user feedback to understand what needs changing."""
        system_prompt = """你是「创意翻译官」——擅长理解模糊的修改意见。

分析用户的反馈，输出JSON：
{
    "understanding": "对用户意图的解读",
    "changes": [{"target": "修改对象", "aspect": "具体方面", "current": "当前", "requested": "用户要求", "priority": "high/medium/low"}],
    "clarification_needed": false,
    "clarification_question": "如果需要澄清"
}"""

        current_outline = (
            self.context.generated_outline[:1000] if self.context.generated_outline else "暂无"
        )

        user_prompt = f"""用户反馈：{feedback}

当前大纲预览：{current_outline}

请分析用户想要修改什么。"""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse feedback: {e}")
            return {
                "understanding": feedback,
                "changes": [{"target": "整体", "aspect": "待分析", "priority": "medium"}],
                "clarification_needed": False,
            }

    async def _regenerate_with_changes(self, changes: dict[str, Any]) -> dict[str, Any]:
        """Regenerate outline and characters with requested changes."""
        # Add changes to context
        changes_text = json.dumps(changes, ensure_ascii=False, indent=2)
        self.context.user_ideas.append(f"修改要求: {changes_text}")

        # Generate message about what was understood
        understanding = changes.get("understanding", "已收到修改意见")

        return {
            "stage": "refining",
            "message": f"🔄 {understanding}\n\n正在根据您的要求重新生成方案...",
            "changes": changes.get("changes", []),
        }

    async def _create_project(self) -> NovelProject:
        """Create the actual project."""
        import uuid

        # Extract info from generated content
        title = self._extract_title() or "未命名项目"
        genre = self._extract_genre() or "general"
        premise = self.context.user_ideas[0][:200] if self.context.user_ideas else ""

        # Count chapters
        chapter_count = 0
        if self.context.generated_outline:
            chapter_count = self.context.generated_outline.count("Chapter")
            chapter_count = max(chapter_count, self.context.generated_outline.count("章"))

        if chapter_count == 0:
            chapter_count = 20  # Default

        # Extract themes from characters or use defaults
        themes = self._extract_themes()

        project = NovelProject(
            id=f"novel_{uuid.uuid4().hex[:8]}",
            title=title,
            genre=genre,
            target_chapters=chapter_count,
            target_words=chapter_count * 2500,
            status=ProjectStatus.PLANNING,
            premise=premise,
            themes=themes,
        )

        self.state.add_project(project)
        self.state.set_current_project(project.id)

        return project

    async def _save_detailed_outline(self, project_id: str):
        """Save the detailed outline to file."""
        from pathlib import Path

        outline_dir = Path(f"data/openviking/memory/novels/{project_id}")
        outline_dir.mkdir(parents=True, exist_ok=True)

        with open(outline_dir / "outline.md", "w", encoding="utf-8") as f:
            f.write(self.context.generated_outline or "# 大纲\n\n暂无详细大纲。")

    async def _save_all_characters(self, project_id: str):
        """Save all characters to file."""
        from pathlib import Path

        char_dir = Path(f"data/openviking/memory/novels/{project_id}")
        char_dir.mkdir(parents=True, exist_ok=True)

        with open(char_dir / "characters.json", "w", encoding="utf-8") as f:
            json.dump(self.context.generated_characters or [], f, ensure_ascii=False, indent=2)

    def _extract_title(self) -> str | None:
        """Extract title from generated outline."""
        if not self.context.generated_outline:
            return None

        lines = self.context.generated_outline.split("\n")
        for line in lines[:20]:
            if line.startswith("# 《"):
                return line.replace("# 《", "").replace("》", "").strip()
            elif line.startswith("# "):
                return line.replace("# ", "").strip()
            elif line.startswith("Title:"):
                return line.replace("Title:", "").strip()
        return None

    def _extract_genre(self) -> str | None:
        """Extract genre from context."""
        # Try to infer from clarifications
        combined = str(self.context.clarifications).lower()
        genres = [
            "fantasy",
            "scifi",
            "romance",
            "thriller",
            "mystery",
            "horror",
            "奇幻",
            "科幻",
            "言情",
            "悬疑",
            "恐怖",
        ]

        for genre in genres:
            if genre in combined:
                return genre

        # Check outline
        if self.context.generated_outline:
            outline_lower = self.context.generated_outline.lower()
            for genre in genres:
                if genre in outline_lower:
                    return genre

        return "general"

    def _extract_themes(self) -> list[str]:
        """Extract themes from context."""
        # Simple extraction - could be improved with LLM
        combined = str(self.context.clarifications).lower()

        themes = []
        theme_keywords = {
            "identity": ["身份", "认同", "自我", "identity"],
            "growth": ["成长", "成熟", "成长", "growth"],
            "love": ["爱情", "爱", "感情", "love"],
            "sacrifice": ["牺牲", "奉献", "sacrifice"],
            "power": ["权力", "力量", "力量", "power"],
            "destiny": ["命运", "宿命", "destiny"],
            "freedom": ["自由", "freedom"],
            "revenge": ["复仇", "报复", "revenge"],
            "redemption": ["救赎", "redemption"],
        }

        for theme, keywords in theme_keywords.items():
            if any(kw in combined for kw in keywords):
                themes.append(theme)

        if not themes:
            themes = ["identity", "growth"]

        return themes[:5]  # Limit to 5 themes

    async def confirm_and_create_with_cover(
        self,
        generate_cover: bool = False,
    ) -> dict[str, Any]:
        """Confirm plan, create project, and optionally generate cover.

        Args:
            generate_cover: Whether to automatically generate cover

        Returns:
            Dict with project info, cover generation status, and message
        """
        # First, create the project
        result = await self.confirm_and_create()

        if not result.get("success"):
            return result

        project = result.get("project")
        cover_result = None

        # Generate cover if requested
        if generate_cover and project:
            try:
                from src.novel_agent.studio.chat.cover_integration import CoverIntegration

                cover_integration = CoverIntegration()

                if cover_integration.is_available():
                    # Build discussion context for better cover
                    discussion_context = {
                        "main_character": next(
                            (
                                c.get("name")
                                for c in self.context.generated_characters
                                if c.get("role") == "主角"
                            ),
                            None,
                        ),
                        "setting": self._extract_setting(),
                    }

                    cover_result = await cover_integration.generate_cover_from_discussion(
                        project=project,
                        discussion_context=discussion_context,
                    )

                    if cover_result.get("success"):
                        # Update result message
                        result["message"] += f"\n🎨 {cover_result['message']}"
                        result["cover_generated"] = True
                        result["cover_path"] = cover_result.get("cover_path")
                    else:
                        result["message"] += f"\n⚠️ {cover_result['message']}"
                        result["cover_generated"] = False
                else:
                    result["message"] += (
                        "\n\n🎨 **封面生成**"
                        "\n封面生成功能不可用。如需生成封面："
                        "\n1. 设置 ZHIPUAI_API_KEY"
                        "\n2. 使用 `/cover generate` 命令"
                    )
                    result["cover_generated"] = False

            except Exception as e:
                logger.error(f"Cover generation failed: {e}")
                result["message"] += f"\n⚠️ 封面生成失败: {e}"
                result["cover_generated"] = False

        return result

    def _extract_setting(self) -> str | None:
        """Extract setting information from outline."""
        if not self.context.generated_outline:
            return None

        # Look for setting-related keywords in outline
        outline = self.context.generated_outline

        # Try to extract setting from "世界观速览" or "地点" sections
        if "地点" in outline or "Location" in outline:
            lines = outline.split("\n")
            for i, line in enumerate(lines):
                if "地点" in line or "Location" in line or "Setting" in line:
                    # Return next non-empty line
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip() and not lines[j].startswith("#"):
                            return lines[j].strip()

        return None

    async def generate_cover_suggestion(self) -> dict[str, Any]:
        """Generate a cover design suggestion for user review.

        This can be called during the preview stage to show the user
        what kind of cover would be generated.

        Returns:
            Dict with cover suggestion and preview
        """
        try:
            from src.novel_agent.studio.chat.cover_integration import CoverIntegration

            cover_integration = CoverIntegration()

            # Extract project info from discussion
            title = self._extract_title() or "未命名项目"
            genre = self._extract_genre() or "general"
            premise = self.context.user_ideas[0][:200] if self.context.user_ideas else ""
            themes = self._extract_themes()

            # Generate suggestion
            suggestion = cover_integration.generate_cover_prompt_suggestion(
                title=title,
                genre=genre,
                premise=premise,
                themes=themes,
            )

            return {
                "success": True,
                "suggestion": suggestion,
                "title": title,
                "genre": genre,
                "recommended_style": cover_integration.get_style_for_genre(genre),
            }

        except Exception as e:
            logger.error(f"Failed to generate cover suggestion: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # Cache management methods
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.get_stats()
        return {"memory_entries": 0, "file_entries": 0, "total_size_mb": 0, "cache_dir": "N/A"}

    def clear_cache(self, content_type: str | None = None) -> int:
        """Clear cached entries.

        Args:
            content_type: Type to clear (outline, characters), or None for all

        Returns:
            Number of entries cleared
        """
        if self.cache:
            return self.cache.invalidate(content_type)
        return 0

    def clear_old_cache(self, max_age_hours: int = 24) -> int:
        """Clear cache entries older than specified hours.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of entries cleared
        """
        return 0

    # ========== Context Truncation Methods ==========

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text.

        Rough estimation:
        - English: ~1.3 tokens per word
        - Chinese: ~1 token per char
        """
        chinese_chars = sum(1 for c in text if '\\u4e00' <= c <= '\\u9fff')
        english_words = len([w for w in text.split() if any(c.isalnum() for c in w)])
        return int(chinese_chars + english_words * 1.3)

    def _truncate_context(self, context: str) -> str:
        """Truncate or summarize context if it exceeds max length."""
        token_count = self._estimate_tokens(context)

        if token_count <= self.max_context_tokens:
            return context

        self.context.original_context_length = token_count

        if self.truncation_strategy == "truncate":
            truncated = self._truncate_by_keep_recent(context)
        else:
            truncated = self._truncate_by_summarize_old(context)

        self.context.truncated_context_length = self._estimate_tokens(truncated)
        self.context.truncation_count += 1

        logger.info(
            f"Context truncated: {self.context.original_context_length} -> "
            f"{self.context.truncated_context_length} tokens"
        )

        return truncated

    def _truncate_by_keep_recent(self, context: str) -> str:
        """Keep only the most recent discussion rounds."""
        lines = context.split('\\n')

        initial_section = []
        qa_section = []
        feedback_section = []

        current_section = "initial"
        for line in lines:
            if "=== 澄清的问题和答案 ===" in line:
                current_section = "qa"
            elif "=== 用户的修改反馈 ===" in line:
                current_section = "feedback"

            if current_section == "initial":
                initial_section.append(line)
            elif current_section == "qa":
                qa_section.append(line)
            else:
                feedback_section.append(line)

        # Parse Q&A pairs
        qa_pairs = []
        current_qa = []
        for line in qa_section:
            if line.startswith("Q:") and current_qa:
                qa_pairs.append('\\n'.join(current_qa))
                current_qa = [line]
            else:
                current_qa.append(line)
        if current_qa:
            qa_pairs.append('\\n'.join(current_qa))

        # Keep only recent Q&A pairs
        max_qa_tokens = int(self.max_context_tokens * 0.6)
        kept_qa = []
        current_tokens = 0

        for qa in reversed(qa_pairs):
            qa_tokens = self._estimate_tokens(qa)
            if current_tokens + qa_tokens <= max_qa_tokens:
                kept_qa.insert(0, qa)
                current_tokens += qa_tokens
            else:
                break

        notice = f"\\n[... {len(qa_pairs) - len(kept_qa)} earlier Q&A pairs truncated ...]\\n" if len(qa_pairs) > len(kept_qa) else ""

        result = '\\n'.join(initial_section) + '\\n' + notice + '\\n'.join(kept_qa)
        if feedback_section:
            result += '\\n' + '\\n'.join(feedback_section)

        return result

    def _truncate_by_summarize_old(self, context: str) -> str:
        """Summarize older discussions, keep recent ones detailed."""
        lines = context.split('\\n')

        initial_idea = []
        qa_pairs = []
        feedback = []

        current_section = "initial"
        current_qa = []

        for line in lines:
            if "=== 澄清的问题和答案 ===" in line:
                current_section = "qa"
                continue
            elif "=== 用户的修改反馈 ===" in line:
                if current_qa:
                    qa_pairs.append(current_qa)
                current_section = "feedback"
                continue

            if current_section == "initial":
                initial_idea.append(line)
            elif current_section == "qa":
                if line.startswith("Q:") and current_qa:
                    qa_pairs.append(current_qa)
                    current_qa = [line]
                else:
                    current_qa.append(line)
            else:
                feedback.append(line)

        if current_qa:
            qa_pairs.append(current_qa)

        # Keep recent Q&A pairs in full, summarize older ones
        if len(qa_pairs) > 3:
            older_pairs = qa_pairs[:-3]
            summary_lines = ["[Earlier discussions summarized:]"]

            themes = set()
            for pair in older_pairs:
                for line in pair:
                    if line.startswith("Q:"):
                        themes.add(line.replace("Q:", "").strip()[:50])

            summary_lines.append(f"讨论主题: {', '.join(list(themes)[:5])}")

            recent_pairs = qa_pairs[-3:]
            result_lines = initial_idea + [""] + summary_lines

            for pair in recent_pairs:
                result_lines.extend(pair)
                result_lines.append("")

            if feedback:
                result_lines.extend(feedback)

            return '\\n'.join(result_lines)
        else:
            return context

    # ========== Streaming Output Method ==========

    async def generate_preview_streaming(
        self
    ) -> AsyncIterator[dict[str, Any] | ProgressUpdate]:
        """Generate preview with streaming updates."""
        self.context.current_stage = "preview"

        full_context = self._build_full_context()

        yield ProgressUpdate(
            stage=GenerationStage.STARTING,
            message="🎨 开始生成创意方案...",
            progress_percent=0,
            detail="分析讨论内容，准备生成大纲和角色",
        )

        if self.context.truncation_count > 0:
            yield ProgressUpdate(
                stage=GenerationStage.STARTING,
                message="📝 对话历史已优化",
                progress_percent=2,
                detail=f"原始 {self.context.original_context_length} tokens -> "
                       f"优化后 {self.context.truncated_context_length} tokens",
            )

        yield ProgressUpdate(
            stage=GenerationStage.OUTLINE_STRUCTURE,
            message="📐 构建故事结构框架...",
            progress_percent=10,
            detail="设计三幕结构：建置、对抗、解决",
        )

        if self.cache:
            cached_outline = self.cache.get_outline(full_context)
            if cached_outline:
                yield ProgressUpdate(
                    stage=GenerationStage.OUTLINE_STRUCTURE,
                    message="📐 使用缓存的大纲",
                    progress_percent=25,
                    detail="从缓存加载大纲结构",
                )
                outline = cached_outline
            else:
                yield ProgressUpdate(
                    stage=GenerationStage.OUTLINE_CHAPTERS,
                    message="📖 正在生成48章详细大纲...",
                    progress_percent=25,
                    detail="第1-12章：第一幕 - 建置",
                )
                outline = await self._generate_detailed_outline(full_context)
                self.cache.set_outline(full_context, outline)
        else:
            yield ProgressUpdate(
                stage=GenerationStage.OUTLINE_CHAPTERS,
                message="📖 正在生成48章详细大纲...",
                progress_percent=25,
                detail="第1-12章：第一幕 - 建置",
            )
            outline = await self._generate_detailed_outline(full_context)

        self.context.generated_outline = outline
        chapter_count = outline.count("Chapter") if outline else 0

        yield ProgressUpdate(
            stage=GenerationStage.OUTLINE_CHAPTERS,
            message="✨ 大纲主体生成完成",
            progress_percent=50,
            detail=f"共 {chapter_count} 章详细大纲",
        )

        yield ProgressUpdate(
            stage=GenerationStage.CHARACTERS_CONCEPT,
            message="👤 开始构思角色阵容...",
            progress_percent=60,
            detail="基于大纲分析角色需求",
        )

        if self.cache:
            cached_characters = self.cache.get_characters(full_context, outline)
            if cached_characters:
                yield ProgressUpdate(
                    stage=GenerationStage.CHARACTERS_CONCEPT,
                    message="👤 使用缓存的角色设定",
                    progress_percent=75,
                    detail=f"从缓存加载 {len(cached_characters)} 个角色",
                )
                characters = cached_characters
            else:
                yield ProgressUpdate(
                    stage=GenerationStage.CHARACTERS_DETAIL,
                    message="🎭 完善角色详细设定...",
                    progress_percent=70,
                    detail="生成外貌、性格、背景故事",
                )
                characters = await self._generate_rich_characters(full_context, outline)
                self.cache.set_characters(full_context, outline, characters)
        else:
            yield ProgressUpdate(
                stage=GenerationStage.CHARACTERS_DETAIL,
                message="🎭 完善角色详细设定...",
                progress_percent=70,
                detail="生成外貌、性格、背景故事",
            )
            characters = await self._generate_rich_characters(full_context, outline)

        self.context.generated_characters = characters

        yield ProgressUpdate(
            stage=GenerationStage.CHARACTERS_RELATIONSHIPS,
            message=f"✨ 已生成 {len(characters)} 个角色",
            progress_percent=85,
            detail="包括主角、反派和重要配角",
        )

        yield ProgressUpdate(
            stage=GenerationStage.FINALIZING,
            message="📝 最终调整方案...",
            progress_percent=95,
            detail="整合大纲和角色设定",
        )

        cover_suggestion = await self.generate_cover_suggestion()

        yield ProgressUpdate(
            stage=GenerationStage.COMPLETE,
            message="✅ 方案生成完成！",
            progress_percent=100,
            detail=f"共生成 {chapter_count} 章大纲，{len(characters)} 个角色",
        )

        outline_summary = self._extract_outline_summary(outline)

        yield {
            "stage": "preview",
            "message": "✨ 基于我们的讨论，我为你生成了完整方案：",
            "outline_preview": outline_summary,
            "outline_full": outline,
            "characters": characters[:5],
            "outline_stats": {
                "total_chapters": chapter_count,
                "estimated_words": chapter_count * 2500,
            },
            "cover_suggestion": cover_suggestion if cover_suggestion.get("success") else None,
            "next_actions": [
                "输入「满意，创建项目」- 开始创建",
                "输入修改意见 - 例如：「主角再强势一点」",
                "输入「显示完整大纲」- 查看全部内容",
                "输入「生成封面」- 生成书籍封面",
            ],
            "truncation_info": {
                "truncated": self.context.truncation_count > 0,
                "original_tokens": self.context.original_context_length,
                "final_tokens": self.context.truncated_context_length,
            } if self.context.truncation_count > 0 else None,
        }

    async def _generate_character_arcs(
        self,
        outline: str
    ) -> list[dict]:
        """Generate character arcs based on the detailed outline.

        Args:
            outline: Detailed outline with chapter specifications

        Returns:
            List of character arc information
        """
        character_arcs = {}

        # Parse chapters from outline to extract character appearances
        # This is a simplified implementation
        lines = outline.split('\n')
        current_chapter = 0

        for line in lines:
            if 'Chapter' in line and ':' in line:
                try:
                    # Extract chapter number
                    chapter_part = line.split(':')[0]
                    current_chapter = int(''.join(filter(str.isdigit, chapter_part)))
                except (ValueError, IndexError):
                    continue

            # Look for character mentions
            if '角色出场' in line or 'Characters' in line:
                # Extract character names (simplified)
                import re
                char_names = re.findall(r'[A-Z][a-z]+', line)

                for char_name in char_names:
                    if char_name not in character_arcs:
                        character_arcs[char_name] = {
                            "name": char_name,
                            "first_appearance": current_chapter,
                            "last_appearance": current_chapter,
                            "chapters": [],
                            "status_changes": []
                        }

                    if char_name in character_arcs:
                        character_arcs[char_name]["chapters"].append(current_chapter)
                        character_arcs[char_name]["last_appearance"] = current_chapter

        return list(character_arcs.values())

    def _validate_outline_continuity(
        self,
        outline: str
    ) -> list[str]:
        """Validate outline for continuity issues.

        Args:
            outline: Detailed outline with chapter specifications

        Returns:
            List of validation errors/warnings
        """
        errors = []

        # Parse outline to extract chapter information
        lines = outline.split('\n')
        chapter_numbers = []

        for line in lines:
            if 'Chapter' in line:
                try:
                    chapter_num = int(''.join(filter(str.isdigit, line.split(':')[0])))
                    chapter_numbers.append(chapter_num)
                except (ValueError, IndexError):
                    continue

        # Check 1: All chapters numbered sequentially
        if chapter_numbers:
            expected_numbers = list(range(1, max(chapter_numbers) + 1))
            missing = set(expected_numbers) - set(chapter_numbers)
            if missing:
                errors.append(f"Missing chapters: {sorted(missing)}")

        # Check 2: No duplicate chapter numbers
        duplicates = [num for num in set(chapter_numbers) if chapter_numbers.count(num) > 1]
        if duplicates:
            errors.append(f"Duplicate chapter numbers: {duplicates}")

        return errors
