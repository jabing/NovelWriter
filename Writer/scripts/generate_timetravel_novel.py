#!/usr/bin/env python3
"""Generate a 10-chapter Chinese time-travel novel using real DeepSeek API.

This script demonstrates the complete novel generation workflow:
1. Creates a time-travel novel outline
2. Uses SummaryManager for chapter processing
3. Tracks knowledge graph entities
4. Saves all outputs to data/novels/
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.writers.base_writer import BaseWriter, get_language_instruction
from src.llm.deepseek import DeepSeekLLM
from src.novel.continuity import StoryState
from src.novel.outline_manager import ChapterSpec, DetailedOutline
from src.novel.summary_manager import SummaryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "novel_generation.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================
# Time-Travel Writer Agent
# ============================================================


@dataclass
class GenerationReport:
    """Report tracking the generation process."""

    novel_id: str
    title: str
    genre: str
    language: str
    start_time: str
    end_time: str = ""
    total_chapters: int = 0
    total_words: int = 0
    total_tokens: int = 0
    chapter_times: dict[int, float] = field(default_factory=dict)
    chapter_tokens: dict[int, int] = field(default_factory=dict)
    chapter_words: dict[int, int] = field(default_factory=dict)
    entities_extracted: int = 0
    relations_inferred: int = 0
    errors: list[str] = field(default_factory=list)


class TimeTravelWriter(BaseWriter):
    """Writer specialized for Chinese time-travel (穿越) novels."""

    GENRE = "timetravel"
    DOMAIN_KNOWLEDGE = """
时间穿越小说写作知识：
- 现代人穿越到古代的适应过程
- 历史知识的运用与局限
- 现代思维与古代环境的冲突
- 身份认同与角色转换
- 命运改变与蝴蝶效应
- 宿命与自由意志的探讨

穿越小说核心要素：
1. 穿越机制要合理或有悬念
2. 主角的现代知识与古代智慧的碰撞
3. 情感线的自然发展
4. 历史背景的真实感
5. 人物成长与命运改变
"""

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
        story_state: StoryState | None = None,
        previous_chapter_summary: str | None = None,
    ) -> str:
        """Write a time-travel chapter in Chinese."""
        prompt_parts = []

        # Add language instruction
        language_instruction = get_language_instruction("zh")
        prompt_parts.append(language_instruction)

        # Add domain knowledge
        prompt_parts.append(self.DOMAIN_KNOWLEDGE)

        # Add style guide
        if style_guide:
            prompt_parts.append(f"\n【风格指南】\n{style_guide}")

        # Add chapter outline
        prompt_parts.append(f"\n【本章大纲】\n{chapter_outline}")

        # Add continuity context
        if story_state:
            continuity_prompt = self._build_continuity_prompt(
                story_state=story_state,
                previous_summary=previous_chapter_summary or "",
                chapter_number=chapter_number,
            )
            prompt_parts.append(continuity_prompt)

        # Add character profiles
        prompt_parts.append("\n【角色档案】")
        for char in characters:
            prompt_parts.append(f"\n{char.get('name', '未知')}:")
            if char.get("personality"):
                prompt_parts.append(f"  性格：{char['personality']}")
            if char.get("background"):
                prompt_parts.append(f"  背景：{char['background']}")
            if char.get("status"):
                prompt_parts.append(f"  当前状态：{char['status']}")

        # Add world context
        if world_context:
            prompt_parts.append("\n【世界观背景】")
            for key, value in world_context.items():
                prompt_parts.append(f"- {key}: {value}")

        full_prompt = "\n".join(prompt_parts)
        system_message = self._get_system_prompt()

        response = await self.llm.generate_with_system(
            system_prompt=system_message,
            user_prompt=full_prompt,
            max_tokens=3000,
            temperature=0.8,
        )

        return response.content

    def _get_system_prompt(self) -> str:
        """Get the system prompt for time-travel writing."""
        return """你是一位畅销穿越小说作家，擅长创作引人入胜的穿越故事。

你的写作风格特点：
1. 开篇即吸引读者，前300字必须有悬念或冲突
2. 对话自然流畅，占内容的30-50%
3. 段落简短，适合手机阅读
4. 情节紧凑，每章都有明确的进展
5. 情感描写细腻真实
6. 穿越设定合理，前后一致

穿越小说特有的写作要点：
- 主角的现代思维与古代环境形成有趣对比
- 展现主角适应新环境的心理变化
- 历史细节要考究但不过度堆砌
- 感情线要自然发展，避免突兀
- 结尾留有悬念，吸引读者继续阅读

每章结尾必须有：
- 情感悬念（感情变化/未说的话）
- 情节悬念（突发情况/新发现）
- 人物悬念（身份揭露/秘密暴露）

请直接输出章节正文内容，不要包含章节标题或序号。"""


# ============================================================
# Novel Outline Creation
# ============================================================


def create_timetravel_outline() -> DetailedOutline:
    """Create a detailed 20-chapter outline for the time-travel novel."""
    chapters = [
        ChapterSpec(
            number=1,
            title="异世初醒",
            summary="现代女孩林晚意外车祸后醒来，发现自己穿越到了古代王朝，成为了丞相府不受宠的嫡女。初到异世的她惊恐不安，必须快速适应新身份，同时隐藏自己的真实来历。",
            characters=["林晚", "翠竹", "大夫人", "林婉儿"],
            location="丞相府",
            key_events=[
                "林晚穿越醒来",
                "发现自己身处古代",
                "了解原主身份和处境",
                "初次面对家人的冷眼",
            ],
            plot_threads_started=["身份危机", "家族斗争"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "惊恐、困惑、努力适应",
                "翠竹": "忠诚侍女",
                "大夫人": "冷漠、轻蔑",
                "林婉儿": "嫉妒、敌意",
            },
        ),
        ChapterSpec(
            number=2,
            title="步步为营",
            summary="林晚开始熟悉这个陌生的世界，她谨慎地观察府中的人际关系。通过丫鬟翠竹，她了解到原主被欺负的真相。她决定改变自己的处境，但必须小心行事。",
            characters=["林晚", "翠竹", "二小姐林芸", "老夫人"],
            location="丞相府",
            key_events=[
                "了解原主过往",
                "遇见善良的二小姐林芸",
                "首次面对老夫人的试探",
                "展现与众不同的气质",
            ],
            plot_threads_started=["姐妹情深"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "冷静、观察、谋划",
                "林芸": "善良、好奇",
                "老夫人": "审视、思考",
            },
        ),
        ChapterSpec(
            number=3,
            title="初露锋芒",
            summary="府中举办诗会，林晚被设计羞辱。凭借现代知识，她巧妙化解危机并惊艳众人。三皇子萧景辰在暗处目睹一切，对这个传闻中懦弱的嫡女产生了兴趣。",
            characters=["林晚", "林婉儿", "萧景辰", "丞相"],
            location="丞相府·花园",
            key_events=[
                "诗会上的暗中较劲",
                "林婉儿设下陷阱",
                "林晚凭借现代诗词脱困",
                "三皇子暗中关注",
            ],
            plot_threads_started=["与三皇子的缘分"],
            plot_threads_resolved=["诗会风波"],
            character_states={
                "林晚": "从容、聪慧",
                "林婉儿": "嫉妒、愤怒",
                "萧景辰": "好奇、欣赏",
                "丞相": "惊讶、重新审视",
            },
        ),
        ChapterSpec(
            number=4,
            title="暗流涌动",
            summary="皇后设宴，丞相府全员入宫。林晚在宫中与三皇子萧景辰首次正面相遇，两人言语交锋。大夫人暗中设计，想要在宴会上让林晚出丑。",
            characters=["林晚", "萧景辰", "皇后", "大夫人", "太子"],
            location="皇宫",
            key_events=[
                "入宫赴宴",
                "与三皇子正面相遇",
                "皇后的试探",
                "化解大夫人的阴谋",
                "太子对林晚产生兴趣",
            ],
            plot_threads_started=["宫廷风云", "三角关系萌芽"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "警惕、机智",
                "萧景辰": "玩味、暗中保护",
                "皇后": "精明、算计",
                "太子": "惊艳、有意",
            },
        ),
        ChapterSpec(
            number=5,
            title="明月寄情",
            summary="中秋节到来，林晚与萧景辰在月下偶遇。两人的对话中，萧景辰发现了林晚的不凡之处。林晚也开始对这个看似风流实则深沉的皇子产生了好奇。",
            characters=["林晚", "萧景辰", "翠竹", "暗卫"],
            location="丞相府·月下亭",
            key_events=[
                "月下偶遇",
                "深入交谈",
                "萧景辰试探林晚身份",
                "两人心中都留下了疑问",
                "暗卫发现可疑人物",
            ],
            plot_threads_started=["感情萌芽", "神秘威胁"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "好奇、警觉、一丝心动",
                "萧景辰": "欣赏、疑惑、保护欲",
            },
        ),
        ChapterSpec(
            number=6,
            title="风雨欲来",
            summary="边境传来急报，北方蛮族入侵。太子主战，三皇子主和，朝堂之上针锋相对。林晚凭借历史知识，向丞相提出独特的见解，影响了朝堂决策。",
            characters=["林晚", "萧景辰", "太子", "丞相", "皇帝"],
            location="丞相府·书房",
            key_events=[
                "边境危机消息传来",
                "林晚分析局势",
                "暗中影响丞相决策",
                "萧景辰察觉异常",
                "太子对林晚更加关注",
            ],
            plot_threads_started=["边关危机", "身份疑云加深"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "焦虑、理智、冒险",
                "萧景辰": "怀疑、保护",
                "太子": "野心、觊觎",
                "丞相": "震惊、骄傲",
            },
        ),
        ChapterSpec(
            number=7,
            title="身份之危",
            summary="有人开始在暗中调查林晚的来历。萧景辰的暗卫发现了一些可疑的线索。大夫人和林婉儿趁机散播谣言，说林晚是被妖邪附身。林晚陷入危机。",
            characters=["林晚", "萧景辰", "大夫人", "林婉儿", "神秘调查者"],
            location="丞相府",
            key_events=[
                "谣言四起",
                "神秘人调查林晚",
                "萧景辰暗中保护",
                "林晚差点暴露身份",
                "老夫人出面维护",
            ],
            plot_threads_started=["身份危机加剧"],
            plot_threads_resolved=["谣言风波（暂时平息）"],
            character_states={
                "林晚": "恐惧、不安、信任萧景辰",
                "萧景辰": "担忧、决心、更深的好奇",
                "大夫人": "得意、不罢休",
            },
        ),
        ChapterSpec(
            number=8,
            title="生死与共",
            summary="林晚外出时遭遇刺杀，萧景辰及时赶到救了她。两人被困在城外山庄，共度一夜。这一夜，两人的心更近了一步，林晚也决定相信萧景辰。",
            characters=["林晚", "萧景辰", "刺客", "暗卫"],
            location="城外山庄",
            key_events=[
                "遭遇刺杀",
                "萧景辰舍身相救",
                "被困山庄",
                "深夜倾心交谈",
                "林晚决定信任萧景辰",
            ],
            plot_threads_started=["感情升温", "刺杀真相调查"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "感动、信任、爱意萌生",
                "萧景辰": "心疼、珍惜、确定心意",
            },
        ),
        ChapterSpec(
            number=9,
            title="真相大白",
            summary="萧景辰查到了刺杀的幕后主使——太子。太子觊觎林晚的才智，想要将她收入府中。萧景辰决定向林晚表明身份，并承诺会保护她。同时，林晚也发现了回到现代的方法。",
            characters=["林晚", "萧景辰", "太子", "翠竹", "暗卫首领"],
            location="三皇子府",
            key_events=[
                "揭露刺杀真相",
                "萧景辰表白心迹",
                "林晚发现回现代的线索",
                "两人面临选择",
                "太子的最后通牒",
            ],
            plot_threads_started=["回归抉择"],
            plot_threads_resolved=["刺杀主谋查明"],
            character_states={
                "林晚": "纠结、深爱、难以抉择",
                "萧景辰": "深情、尊重她的选择",
                "太子": "疯狂、不甘",
            },
        ),
        ChapterSpec(
            number=10,
            title="千年之约",
            summary="林晚面临最后的抉择：是回到现代继续自己的人生，还是留在古代与萧景辰相守。在最后的时刻，她做出了选择——为了爱情，她选择留下。两人携手面对未来的挑战，共许千年之约。",
            characters=["林晚", "萧景辰", "太子", "丞相", "老夫人", "翠竹"],
            location="城外古庙·月下",
            key_events=[
                "林晚面对穿越之门",
                "与萧景辰的最后对话",
                "林晚做出选择——留下",
                "两人确定心意",
                "共同面对太子的威胁",
                "许下千年之约",
            ],
            plot_threads_started=["新的开始"],
            plot_threads_resolved=["穿越悬念", "感情归属"],
            character_states={
                "林晚": "坚定、深爱、无悔",
                "萧景辰": "感动、珍惜、承诺一生",
                "太子": "绝望、不甘",
            },
        ),
        ChapterSpec(
            number=11,
            title="边疆风云",
            summary="边境战事告急，萧景辰主动请缨出征。林晚担心他的安危，决定用自己的方式支持他。她利用现代知识设计了改良的医疗方案和防御工事，暗中帮助军队。",
            characters=["林晚", "萧景辰", "丞相", "将军", "军医"],
            location="京城·三皇子府",
            key_events=[
                "萧景辰请命出征",
                "两人依依不舍分别",
                "林晚设计医疗方案",
                "改良防御工事图纸",
                "暗中派人送往边关",
            ],
            plot_threads_started=["边关支援", "分离之苦"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "担忧、坚强、运筹帷幄",
                "萧景辰": "不舍、坚定、期待归来",
            },
        ),
        ChapterSpec(
            number=12,
            title="深宫暗流",
            summary="萧景辰出征后，太子在朝中不断排挤丞相府势力。林晚意识到必须在朝堂上站稳脚跟，才能保护自己和家人。她开始暗中布局，拉拢被太子打压的官员。",
            characters=["林晚", "老夫人", "丞相", "被打压官员", "太子党羽"],
            location="丞相府·密室",
            key_events=[
                "太子打压异己",
                "林晚分析朝局",
                "暗中联络受排挤官员",
                "老夫人暗中支持",
                "丞相开始重视林晚",
            ],
            plot_threads_started=["朝堂布局"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "冷静、智慧、步步为营",
                "老夫人": "欣慰、全力支持",
                "丞相": "刮目相看、倚重",
            },
        ),
        ChapterSpec(
            number=13,
            title="瘟疫突袭",
            summary="京城突发瘟疫，人心惶惶。太子党羽趁机散播谣言，称瘟疫是林晚带来的不祥之兆。林晚不顾安危，挺身而出，用现代医学知识控制疫情，赢得了民心。",
            characters=["林晚", "太医院院正", "染病百姓", "太子", "皇帝"],
            location="京城·疫区",
            key_events=[
                "瘟疫爆发",
                "谣言中伤林晚",
                "林晚主动请缨抗疫",
                "推行隔离和卫生措施",
                "疫情得到控制",
            ],
            plot_threads_started=["民心所向", "抗疫之战"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "勇敢、无私、医术高明",
                "皇帝": "赞赏、信任",
                "太子": "阴谋失败、愤怒",
            },
        ),
        ChapterSpec(
            number=14,
            title="边关捷报",
            summary="萧景辰在边关取得大捷，班师回朝。林晚的医疗方案和防御工事起到了关键作用。两人重逢，深情相拥。萧景辰在朝堂上的威望大增，太子的地位受到威胁。",
            characters=["林晚", "萧景辰", "皇帝", "太子", "百官"],
            location="京城·城门",
            key_events=[
                "边关大捷消息传来",
                "萧景辰班师回朝",
                "两人深情重逢",
                "萧景辰提及林晚的贡献",
                "皇帝重赏萧景辰",
            ],
            plot_threads_started=["战功赫赫", "太子地位动摇"],
            plot_threads_resolved=["分离之苦"],
            character_states={
                "林晚": "喜悦、自豪",
                "萧景辰": "意气风发、深爱林晚",
                "太子": "恐惧、加紧阴谋",
            },
        ),
        ChapterSpec(
            number=15,
            title="赐婚风波",
            summary="皇帝为萧景辰和林晚赐婚，太子暗中破坏。他设计让林晚卷入一场命案，试图毁了她的名声。萧景辰相信林晚的清白，全力为她洗刷冤屈。",
            characters=["林晚", "萧景辰", "皇帝", "太子", "死者家属"],
            location="京城·大理寺",
            key_events=[
                "皇帝赐婚",
                "太子设计陷害",
                "林晚蒙冤入狱",
                "萧景辰全力营救",
                "真相大白，太子阴谋败露",
            ],
            plot_threads_started=["赐婚", "冤案"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "委屈、坚定",
                "萧景辰": "信任、愤怒、保护欲",
                "皇帝": "失望、对太子不满",
            },
        ),
        ChapterSpec(
            number=16,
            title="东宫易主",
            summary="太子的阴谋接连败露，皇帝终于下定决心废黜太子。萧景辰被立为新太子，林晚成为太子妃。权力更迭之际，前朝余孽暗中作乱，林晚协助萧景辰稳定局势。",
            characters=["林晚", "萧景辰", "皇帝", "废太子", "前朝余孽"],
            location="皇宫·东宫",
            key_events=[
                "废黜太子",
                "萧景辰被立为新太子",
                "林晚入主东宫",
                "前朝余孽作乱",
                "两人联手平乱",
            ],
            plot_threads_started=["东宫易主", "平乱"],
            plot_threads_resolved=["冤案"],
            character_states={
                "林晚": "太子妃、稳重、有智谋",
                "萧景辰": "新太子、意气风发",
                "废太子": "被囚、不甘心",
            },
        ),
        ChapterSpec(
            number=17,
            title="帝王之路",
            summary="皇帝病重，萧景辰开始监国。废太子在旧部支持下发动兵变，围困皇宫。林晚临危不乱，用现代战术知识协助萧景辰平定叛乱。最终，萧景辰登基为帝。",
            characters=["林晚", "萧景辰", "病重皇帝", "废太子", "禁军统领"],
            location="皇宫·太和殿",
            key_events=[
                "皇帝病重",
                "萧景辰监国",
                "废太子兵变",
                "林晚出谋划策",
                "平定叛乱，萧景辰登基",
            ],
            plot_threads_started=["登基", "兵变"],
            plot_threads_resolved=["平乱"],
            character_states={
                "林晚": "冷静、智慧、中流砥柱",
                "萧景辰": "新帝、威严、感激",
                "废太子": "兵败、自尽",
            },
        ),
        ChapterSpec(
            number=18,
            title="母仪天下",
            summary="萧景辰登基后，林晚被立为皇后。她推行一系列改革，改善民生，建立新式学堂，引进现代知识。朝中保守派反对她的改革，林晚用智慧和成果说服了他们。",
            characters=["林晚", "萧景辰", "保守派大臣", "新派官员", "百姓"],
            location="京城·皇宫",
            key_events=[
                "林晚被立为皇后",
                "推行民生改革",
                "建立新式学堂",
                "保守派反对",
                "用成果说服众人",
            ],
            plot_threads_started=["改革", "保守派反对"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "皇后、贤明、有远见",
                "萧景辰": "皇帝、支持、信任",
                "保守派": "从反对到敬佩",
            },
        ),
        ChapterSpec(
            number=19,
            title="时空涟漪",
            summary="林晚发现时空出现异常，穿越之门再次出现。她面临最后的抉择：是回到现代见家人最后一面，还是永远留在这个时代。萧景辰表示尊重她的任何选择。",
            characters=["林晚", "萧景辰", "时空异象", "幻象中的家人"],
            location="京城·皇宫·观星台",
            key_events=[
                "时空异常出现",
                "穿越之门重现",
                "林晚看到现代家人",
                "萧景辰尊重她的选择",
                "林晚内心挣扎",
            ],
            plot_threads_started=["最终抉择"],
            plot_threads_resolved=[],
            character_states={
                "林晚": "纠结、思念家人、深爱萧景辰",
                "萧景辰": "不舍、尊重、信任",
            },
        ),
        ChapterSpec(
            number=20,
            title="盛世华章",
            summary="林晚最终选择留下，但她通过时空之门给现代家人留下了一封信，告诉他们自己很幸福。萧景辰和林晚共同开创了一个盛世，景朝成为当时最强大的王朝。两人相守一生，实现了千年之约。",
            characters=["林晚", "萧景辰", "皇子公主", "百官", "百姓"],
            location="京城·皇宫·太和殿",
            key_events=[
                "林晚给现代家人留信",
                "选择永远留在古代",
                "两人开创盛世",
                "儿女双全",
                "白首偕老，实现千年之约",
            ],
            plot_threads_started=["盛世"],
            plot_threads_resolved=["最终抉择", "改革", "保守派反对"],
            character_states={
                "林晚": "幸福、满足、无憾",
                "萧景辰": "深爱、感激、圆满",
            },
        ),
    ]

    return DetailedOutline(chapters=chapters)


# ============================================================
# Main Generation Function
# ============================================================


async def generate_novel(
    novel_id: str = "user_novel_001",
    title: str = "千年之约：穿越之恋",
    output_dir: Path | None = None,
) -> GenerationReport:
    """Generate the complete novel with all chapters."""

    # Initialize report
    report = GenerationReport(
        novel_id=novel_id,
        title=title,
        genre="穿越",
        language="中文",
        start_time=datetime.now().isoformat(),
        total_chapters=10,
    )

    # Set up output directory
    if output_dir is None:
        output_dir = project_root / "data" / "novels" / novel_id / "chapters"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Also ensure log directory exists
    (project_root / "logs").mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting novel generation: {title}")
    logger.info(f"Novel ID: {novel_id}")
    logger.info(f"Output directory: {output_dir}")

    # Initialize DeepSeek LLM (real API)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        error_msg = "DEEPSEEK_API_KEY environment variable not set!"
        logger.error(error_msg)
        report.errors.append(error_msg)
        return report

    logger.info("Initializing DeepSeek LLM...")
    llm = DeepSeekLLM(
        api_key=api_key,
        model="deepseek-chat",
        temperature=0.8,
        max_tokens=4096,
    )

    # Initialize writer
    writer = TimeTravelWriter(name="TimeTravelWriter", llm=llm)

    # Initialize SummaryManager with knowledge graph
    storage_path = project_root / "data" / "novels"
    summary_manager = SummaryManager(
        storage_path=storage_path,
        novel_id=novel_id,
        llm=llm,
        use_auto_fix=True,
        use_knowledge_graph=True,
    )

    # Create outline
    logger.info("Creating novel outline...")
    outline = create_timetravel_outline()
    report.total_chapters = len(outline.chapters)

    # Define characters with full profiles
    characters_db: dict[str, dict[str, Any]] = {
        "林晚": {
            "name": "林晚",
            "role": "protagonist",
            "personality": "聪慧、冷静、独立、适应力强",
            "background": "现代都市白领，意外穿越到古代，成为丞相府嫡女",
            "status": "穿越者，正在适应古代生活",
        },
        "萧景辰": {
            "name": "萧景辰",
            "role": "male_lead",
            "personality": "深沉、智慧、表面风流实则城府极深",
            "background": "三皇子，不受宠但有野心，暗中培养势力",
            "status": "对林晚产生兴趣",
        },
        "翠竹": {
            "name": "翠竹",
            "role": "supporting",
            "personality": "忠心、善良、有些天真",
            "background": "林晚的贴身丫鬟，从小服侍原主",
            "status": "林晚的可靠助力",
        },
        "林婉儿": {
            "name": "林婉儿",
            "role": "antagonist",
            "personality": "嫉妒、心机、表面温柔",
            "background": "丞相府庶女，大夫人的女儿",
            "status": "视林晚为眼中钉",
        },
        "大夫人": {
            "name": "大夫人",
            "role": "antagonist",
            "personality": "势利、刻薄、心机深重",
            "background": "丞相正室，林婉儿的母亲",
            "status": "打压林晚",
        },
        "太子": {
            "name": "太子",
            "role": "antagonist",
            "personality": "野心勃勃、不择手段、表面温文尔雅",
            "background": "当朝太子，觊觎林晚的才智",
            "status": "对林晚有企图",
        },
        "林芸": {
            "name": "林芸",
            "role": "supporting",
            "personality": "善良、温柔、单纯",
            "background": "丞相府二小姐，不受宠",
            "status": "林晚在府中的唯一真心姐妹",
        },
        "老夫人": {
            "name": "老夫人",
            "role": "supporting",
            "personality": "睿智、公正、疼爱孙辈",
            "background": "丞相府老夫人",
            "status": "暗中观察林晚",
        },
        "丞相": {
            "name": "丞相",
            "role": "supporting",
            "personality": "政治家、重视人才、有些冷漠",
            "background": "当朝丞相，林晚的父亲",
            "status": "重新审视林晚",
        },
    }

    # World context
    world_context: dict[str, Any] = {
        "朝代": "架空王朝-景朝",
        "时代背景": "类似于唐宋时期的文化与政治",
        "主要势力": "皇帝、太子党、三皇子党、世家大族",
        "社会风气": "重文轻武，诗词歌赋流行",
        "特殊设定": "穿越是真实存在的，但极为罕见",
    }

    # Generate each chapter
    for chapter_spec in outline.chapters:
        chapter_num = chapter_spec.number
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Generating Chapter {chapter_num}: {chapter_spec.title}")
        logger.info(f"{'=' * 60}")

        start_time = time.time()

        try:
            # Get characters for this chapter
            chapter_characters = [
                characters_db.get(name, {"name": name, "role": "unknown"})
                for name in chapter_spec.characters
                if name in characters_db
            ]

            # Get context from summary manager
            context = summary_manager.get_context_for_chapter(chapter_num)
            previous_summary = None
            if chapter_num > 1:
                prev_summary_obj = summary_manager.get_chapter_summary(chapter_num - 1)
                if prev_summary_obj:
                    previous_summary = prev_summary_obj.summary

            # Get story state from summary manager
            story_state = summary_manager._build_story_state()

            # Generate chapter content
            content = await writer.write_chapter(
                chapter_number=chapter_num,
                chapter_outline=chapter_spec.summary,
                characters=chapter_characters,
                world_context=world_context,
                story_state=story_state,
                previous_chapter_summary=previous_summary,
                language="zh",
            )

            # Count words (Chinese characters)
            word_count = len(content.replace(" ", "").replace("\n", ""))

            # Process chapter with summary manager
            (
                chapter_summary,
                verification,
                auto_fix_result,
            ) = await summary_manager.process_chapter_with_autofix(
                chapter_number=chapter_num,
                title=chapter_spec.title,
                content=content,
                max_fix_iterations=2,
            )

            # Track timing
            elapsed = time.time() - start_time
            report.chapter_times[chapter_num] = elapsed
            report.chapter_words[chapter_num] = word_count
            report.total_words += word_count

            # Track tokens
            tokens_used = llm._total_tokens_used - report.total_tokens
            report.chapter_tokens[chapter_num] = tokens_used
            report.total_tokens = llm._total_tokens_used

            # Save chapter to file
            chapter_filename = f"chapter_{chapter_num:03d}.md"
            chapter_filepath = output_dir / chapter_filename

            with open(chapter_filepath, "w", encoding="utf-8") as f:
                f.write(f"# 第{chapter_num}章 {chapter_spec.title}\n\n")
                f.write(content)
                f.write("\n\n---\n")
                f.write(
                    f"*字数：{word_count}字 | 生成时间：{elapsed:.1f}秒 | Token消耗：{tokens_used}*\n"
                )

            logger.info(f"✓ Chapter {chapter_num} completed in {elapsed:.1f}s")
            logger.info(f"  - Words: {word_count}")
            logger.info(f"  - Tokens: {tokens_used}")
            logger.info(f"  - Saved to: {chapter_filepath}")

            # Print progress
            print(f"\n{'─' * 60}")
            print(f"✓ 第{chapter_num}章完成: {chapter_spec.title}")
            print(f"  字数: {word_count} | 耗时: {elapsed:.1f}秒 | Tokens: {tokens_used}")
            print(f"{'─' * 60}\n")

        except Exception as e:
            error_msg = f"Chapter {chapter_num} failed: {str(e)}"
            logger.error(error_msg)
            report.errors.append(error_msg)
            import traceback

            traceback.print_exc()

    # Get knowledge graph statistics
    if summary_manager.knowledge_graph:
        try:
            kg_stats = summary_manager.knowledge_graph.get_statistics()
            report.entities_extracted = kg_stats.get("total_entities", 0)
            report.relations_inferred = kg_stats.get("total_relations", 0)
            logger.info("\nKnowledge Graph Statistics:")
            logger.info(f"  - Entities: {report.entities_extracted}")
            logger.info(f"  - Relations: {report.relations_inferred}")
        except Exception as e:
            logger.warning(f"Failed to get KG statistics: {e}")

    # Finalize report
    report.end_time = datetime.now().isoformat()

    # Save generation report
    report_path = output_dir.parent / "generation_report.json"
    report_data = {
        "novel_id": report.novel_id,
        "title": report.title,
        "genre": report.genre,
        "language": report.language,
        "start_time": report.start_time,
        "end_time": report.end_time,
        "total_chapters": report.total_chapters,
        "total_words": report.total_words,
        "total_tokens": report.total_tokens,
        "chapter_times": report.chapter_times,
        "chapter_tokens": report.chapter_tokens,
        "chapter_words": report.chapter_words,
        "entities_extracted": report.entities_extracted,
        "relations_inferred": report.relations_inferred,
        "errors": report.errors,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'=' * 60}")
    logger.info("NOVEL GENERATION COMPLETE!")
    logger.info(f"{'=' * 60}")
    logger.info(f"Total chapters: {report.total_chapters}")
    logger.info(f"Total words: {report.total_words}")
    logger.info(f"Total tokens: {report.total_tokens}")
    logger.info(f"Output directory: {output_dir.parent}")
    logger.info(f"Report saved to: {report_path}")

    # Print final summary
    print(f"\n{'=' * 60}")
    print("🎉 小说生成完成!")
    print(f"{'=' * 60}")
    print(f"📖 书名: {title}")
    print(f"📝 章节数: {report.total_chapters}")
    print(f"📊 总字数: {report.total_words}")
    print(f"⚡ Token消耗: {report.total_tokens}")
    print(f"👤 实体数量: {report.entities_extracted}")
    print(f"🔗 关系数量: {report.relations_inferred}")
    print(f"📁 输出目录: {output_dir.parent}")
    if report.errors:
        print(f"⚠️ 错误数: {len(report.errors)}")
    print(f"{'=' * 60}\n")

    return report


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📚 中文穿越小说生成器")
    print("   使用 DeepSeek API 实时生成")
    print("=" * 60 + "\n")

    # Run generation
    report = asyncio.run(generate_novel())

    # Exit with error code if there were failures
    sys.exit(0 if not report.errors else 1)
