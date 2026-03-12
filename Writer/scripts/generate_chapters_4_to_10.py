#!/usr/bin/env python3
"""
Generate chapters 4-10 for user_novel_001 (Time-travel Chinese novel)
Uses real DeepSeek API for generation
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.deepseek import DeepSeekLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Novel configuration
NOVEL_ID = "user_novel_001"
OUTPUT_DIR = Path(f"data/novels/{NOVEL_ID}/chapters")

# Chapter outlines for 4-10
CHAPTERS = [
    {
        "number": 4,
        "title": "破局",
        "summary": "林晚开始主动调查落水真相。她发现府中眼线众多,决定以退为进。通过翠竹的帮助,她找到了落水当日的一些线索,同时发现了原主留下的密信。老夫人的态度出现微妙变化。",
        "characters": ["林晚", "翠竹", "老夫人", "林婉儿", "林月"],
        "location": "丞相府",
    },
    {
        "number": 5,
        "title": "暗流",
        "summary": "林晚继续深入调查,发现'凤星临世'预言背后的秘密。她与三皇子萧景辰再次相遇,两人之间的张力增加。府中势力开始明争暗斗,林晚需要在夹缝中求生存。",
        "characters": ["林晚", "萧景辰", "翠竹", "林婉儿", "林星"],
        "location": "丞相府/城外青云观",
    },
    {
        "number": 6,
        "title": "道长之谜",
        "summary": "林晚前往青云观寻找玄清道长,得知关于穿越和'凤星临世'的惊人真相。道长暗示她的到来并非偶然,而是命运使然。同时,有人暗中跟踪林晚。",
        "characters": ["林晚", "玄清道长", "翠竹", "神秘跟踪者"],
        "location": "城外青云观",
    },
    {
        "number": 7,
        "title": "丞相归府",
        "summary": "丞相林正清从边疆归来,府中气氛骤然紧张。林晚第一次见到这个名义上的父亲,却发现他对自己态度冷淡。丞相似乎对'凤星临世'的预言也有所耳闻。",
        "characters": ["林晚", "林正清(丞相)", "老夫人", "大夫人", "林婉儿", "林月", "林星"],
        "location": "丞相府",
    },
    {
        "number": 8,
        "title": "真相初现",
        "summary": "通过一系列调查,林晚终于发现落水真相——幕后黑手竟然是...。她收集到关键证据,但同时也暴露了自己的行动。危机与机遇并存。",
        "characters": ["林晚", "翠竹", "林婉儿", "大夫人", "萧景辰"],
        "location": "丞相府",
    },
    {
        "number": 9,
        "title": "反转",
        "summary": "林晚实施反击计划,在丞相面前揭露真相。局势逆转,原本陷害她的人反而陷入困境。然而,新的威胁也随之而来,三皇子萧景辰的真实目的令人捉摸不透。",
        "characters": ["林晚", "林正清", "林婉儿", "大夫人", "老夫人", "萧景辰"],
        "location": "丞相府/皇宫",
    },
    {
        "number": 10,
        "title": "新生",
        "summary": "第一卷终章。林晚在府中地位得到提升,初步建立了自己的势力。她与萧景辰的关系进入新阶段,同时对于如何回现代也有了新的线索。故事留下悬念,为后续发展埋下伏笔。",
        "characters": ["林晚", "翠竹", "老夫人", "萧景辰", "林正清", "玄清道长"],
        "location": "丞相府",
    },
]

# Story context from chapters 1-3
STORY_CONTEXT = """
【故事背景】
- 朝代: 景朝永和二十三年(架空王朝,类似唐宋时期)
- 地点: 丞相府及京城
- 主角: 林晚,现代职场女性穿越成丞相府嫡女

【主要人物】
- 林晚: 丞相府嫡女,原主性格孤僻,现由现代女性穿越而来,冷静聪慧
- 翠竹: 林晚的贴身丫鬟,忠诚
- 老夫人: 丞相府实际掌权者,林晚的祖母
- 丞相: 林正清,林晚的父亲,长期在外
- 大夫人: 继室,林婉儿和林星的生母
- 林婉儿: 二小姐,庶女,表面温柔实则心机深沉
- 林月: 三小姐,性格直爽
- 林星: 四小姐,善于察言观色
- 萧景辰: 三皇子,风流表象下深不可测

【已发生事件】
第1章: 林晚穿越苏醒,发现原主落水并非意外,而是被庶妹的丫鬟推入水中
第2章: 林晚开始了解府中势力分布,向老夫人请安时谨慎应对试探
第3章: 诗会上林婉儿故意刁难,林晚凭借一首荷花诗惊艳全场,扭转形象,引起丞相和三皇子注意

【悬念线索】
- '凤星临世'预言与丞相府有关
- 原主留下的神秘纸条指向青云观玄清道长
- 有人暗中监视林晚
- 林晚偷听到萧景辰与神秘人对话
"""


async def generate_chapter(
    llm: DeepSeekLLM, chapter_spec: dict, previous_summary: str = ""
) -> tuple[str, int]:
    """Generate a single chapter using DeepSeek API."""

    # Build the prompt
    system_prompt = f"""你是一位专业的中文穿越小说作家,擅长描写古代宫廷宅斗、女性成长和悬疑推理。

{STORY_CONTEXT}

【写作要求】
1. 使用优美流畅的中文,符合架空古风小说的文风
2. 章节约2500字左右
3. 注重人物心理描写和细节刻画
4. 推进剧情发展,埋设伏笔
5. 保持人物性格一致
6. 加入适当的悬念和冲突"""

    user_prompt = f"""请撰写第{chapter_spec["number"]}章: {chapter_spec["title"]}

【章节大纲】
{chapter_spec["summary"]}

【出场人物】
{", ".join(chapter_spec["characters"])}

【场景】
{chapter_spec["location"]}

{"【前章提要】" + chr(10) + previous_summary if previous_summary else ""}

请开始撰写本章内容,标题格式为:
# 第{chapter_spec["number"]}章 {chapter_spec["title"]}"""

    # Call the API
    response = await llm.generate_with_system(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=4000,
    )

    content = response.content
    tokens_used = response.tokens_used if hasattr(response, "tokens_used") else 0

    return content, tokens_used


async def main():
    """Generate chapters 4-10."""
    print("\n" + "=" * 60)
    print("📚 生成小说章节 4-10")
    print(f"   小说ID: {NOVEL_ID}")
    print("   使用: DeepSeek API (实时生成)")
    print("=" * 60 + "\n")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize LLM
    try:
        llm = DeepSeekLLM(
            model="deepseek-chat",
            temperature=0.8,
            max_tokens=4000,
        )
        logger.info("✓ DeepSeek LLM initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        return 1

    # Track statistics
    total_words = 0
    total_tokens = 0
    start_time = time.time()

    # Generate each chapter
    for chapter_spec in CHAPTERS:
        chapter_num = chapter_spec["number"]
        chapter_title = chapter_spec["title"]

        print(f"\n{'─' * 60}")
        print(f"✍️  正在生成第 {chapter_num} 章: {chapter_title}")
        print(f"{'─' * 60}")

        try:
            # Load previous chapter summary if exists
            previous_summary = ""
            prev_chapter_path = OUTPUT_DIR / f"chapter_{chapter_num - 1:03d}.md"
            if prev_chapter_path.exists():
                with open(prev_chapter_path, encoding="utf-8") as f:
                    prev_content = f.read()
                    # Extract first 300 characters as summary
                    lines = prev_content.split("\n")
                    content_lines = [l for l in lines if l.strip() and not l.startswith("#")]
                    if content_lines:
                        previous_summary = "".join(content_lines[:10])[:500] + "..."

            # Generate chapter
            chapter_start = time.time()
            content, tokens = await generate_chapter(llm, chapter_spec, previous_summary)
            chapter_elapsed = time.time() - chapter_start

            # Count words (Chinese characters)
            word_count = len(content.replace("\n", "").replace(" ", ""))

            # Save chapter as markdown
            md_path = OUTPUT_DIR / f"chapter_{chapter_num:03d}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.write("\n\n---\n")
                f.write(
                    f"*字数：{word_count} | 生成时间：{chapter_elapsed:.1f}秒 | Token消耗：{tokens}*\n"
                )

            # Save chapter metadata as JSON
            json_path = OUTPUT_DIR / f"chapter_{chapter_num:03d}.json"
            metadata = {
                "chapter_number": chapter_num,
                "title": chapter_title,
                "summary": chapter_spec["summary"],
                "key_events": [],
                "character_changes": {},
                "location": chapter_spec["location"],
                "plot_threads_advanced": [],
                "plot_threads_resolved": [],
                "sentiment": "tense",
                "word_count": word_count,
                "created_at": datetime.now().isoformat(),
            }
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # Update statistics
            total_words += word_count
            total_tokens += tokens

            # Print progress
            print(f"✓ 第 {chapter_num} 章完成!")
            print(f"  字数: {word_count:,}")
            print(f"  耗时: {chapter_elapsed:.1f}秒")
            print(f"  Tokens: {tokens:,}")
            print(f"  保存至: {md_path.name}")

            # Small delay between chapters
            if chapter_num < 10:
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Failed to generate chapter {chapter_num}: {e}")
            import traceback

            traceback.print_exc()
            continue

    # Print final summary
    total_elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print("🎉 章节生成完成!")
    print(f"{'=' * 60}")
    print(f"📖 小说ID: {NOVEL_ID}")
    print("📝 生成章节: 4-10 (共7章)")
    print(f"📊 总字数: {total_words:,}")
    print(f"⚡ Token消耗: {total_tokens:,}")
    print(f"⏱️  总耗时: {total_elapsed:.1f}秒")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
