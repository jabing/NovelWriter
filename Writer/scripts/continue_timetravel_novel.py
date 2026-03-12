#!/usr/bin/env python3
"""
Generate chapters 4-10 for time-travel novel.
Simple script without knowledge graph complexity.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm.deepseek import DeepSeekLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        ],
)
logger = logging.getLogger(__name__)


# Novel metadata
NOVEL_ID = "user_novel_001"
NOVEL_TITLE = "千年之约：穿越之恋"
GENRE = "穿越"
LANGUAGE = "zh"  # Chinese

CHAPTERS = [
    {
        "number": 4,
        "title": "暗流涌动",
        "summary": "皇后设宴，丞相府全员入宫。林晚在宫中与三皇子萧景辰首次正面相遇，两人言语交锋。大夫人暗中设计，想要在宴会上让林晚出丑。",
        "characters": ["林晚", "萧景辰", "皇后", "大夫人", "太子"],
        "location": "皇宫",
    },
    {
        "number": 5,
        "title": "明月寄情",
        "summary": "中秋节到来，林晚与萧景辰在月下偶遇。两人深入交谈,萧景辰试探林晚身份。两人心中都留下疑问",
        "characters": ["林晚", "萧景辰", "翠竹"],
        "location": "丞相府·月下亭",
    },
    {
        "number": 6,
        "title": "风雨欲来",
        "summary": "边境传来急报，林晚凭借历史知识分析局势，向丞相提出独特见解",
        "characters": ["林晚", "萧景辰", "太子", "丞相"],
        "location": "丞相府·书房",
    },
    {
        "number": 7,
        "title": "身份之危",
        "summary": "有人开始暗中调查林晚的来历。萧景辰暗中保护林晚",
        "characters": ["林晚", "萧景辰", "大夫人", "林婉儿"],
        "location": "丞相府",
    },
    {
        "number": 8,
        "title": "生死与共",
        "summary": "林晚遭遇刺杀，萧景辰舍身相救。被困城外山庄一夜",
    },
    {
        "number": 9,
        "title": "真相大白",
        "summary": "萧景辰查到刺杀主使是太子，同时发现回现代的方法",
        "characters": ["林晚", "萧景辰", "太子", "翠竹"],
        "location": "三皇子府",
    },
    {
        "number": 10,
        "title": "千年之约",
        "summary": "林晚面临最终抉择，选择留下与萧景辰",
        "characters": ["林晚", "萧景辰", "太子", "丞相", "老夫人", "翠竹"],
        "location": "城外古庙·月下",
    },
]

# Character profiles
CHARACTERS = {
    "林晚": {
        "name": "林晚",
        "role": "protagonist",
        "personality": "现代女大学生，穿越后性格坚韧，聪明机智",
        "background": "丞相府不受宠的嫡女",
    },
    "萧景辰": {
        "name": "萧景辰",
        "role": "male_lead",
        "personality": "三皇子，表面风流不实则深沉",
        "background": "皇帝第三子，野心勃勃",
    },
    "翠竹": {
        "name": "翠竹",
        "role": "maid",
        "personality": "忠心耿耿，心思细腻",
        "background": "林晚的贴身丫鬟",
    },
    "林婉儿": {
        "name": "林婉儿",
        "role": "antagonist",
        "personality": "表面温柔，内心嫉妒",
        "background": "丞相府二小姐",
    },
    "大夫人": {
        "name": "大夫人",
        "role": "antagonist",
        "personality": "尖酸刻薄，善于算计",
        "background": "丞相正妻",
    },
    "太子": {
        "name": "太子",
        "role": "antagonist",
        "personality": "野心勃勃，表面仁义",
        "background": "皇后长子",
    },
    "丞相": {
        "name": "丞相",
        "role": "supporting",
        "personality": "政治老手，重视家族",
        "background": "林晚的父亲",
    },
    "皇后": {
        "name": "皇后",
        "role": "supporting",
        "personality": "精明强干，掌控后宫",
        "background": "太子之母",
    },
}


async def generate_chapter(llm: DeepSeekLLM, chapter_info: dict) -> str:
    """Generate a single chapter using DeepSeek LLM."""

    # Build the prompt
    system_prompt = f"""你是一位畅销穿越小说作家，擅长写中国古代言情穿越小说。

小说特点：
1. 情节紧凑，节奏明快
2. 人物对话生动自然
3. 情感细腻真挚
4. 古风氛围浓厚
5. 适合手机阅读（段落简短）

写作风格：
- 使用古风语言但不过分生涩
- 对话活泼，符合人物性格
- 情节有张力，悬念设置得当
- 描写细腻，有画面感

请写第 {chapter_info['number']}章： {chapter_info['title']}
"""

    # Build user prompt
    user_prompt = f"""
【章节信息】
章节号: {chapter_info['number']}
标题: {chapter_info['title']}
摘要: {chapter_info['summary']}
出场人物: {', '.join(chapter_info['characters'])}
地点: {chapter_info['location']}

【已有角色档案】
"""

    # Add character profiles
    for char_name in chapter_info['characters']:
        if char_name in CHARACTERS:
            char_data = CHARACTERS[char_name]
            user_prompt += f"""
{char_name}：
- 身份： {char_data['role']}
- 性格: {char_data['personality']}
- 背景: {char_data['background']}
"""

    user_prompt += """
【写作要求】
1. 字数: 2000-2500字
2. 必须使用中文写作
3. 必须符合穿越小说风格
4. 必须设置章节结尾悬念
5. 对话要生动，符合古风

6. 情节要有转折和张力

请直接输出章节正文内容，不要包含标题。
"""

    # Generate content
    start_time = time.time()
    response = await llm.generate_with_system(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.8,
        max_tokens=3000,
    )

    elapsed = time.time() - start_time
    content = response.content
    tokens_used = response.tokens_used

    logger.info(f"Chapter {chapter_info['number']} generated in {elapsed:.1f}s ({tokens_used} tokens)")

    return content, elapsed, tokens_used


async def main():
    """Generate all remaining chapters."""
    print(f"\n{'='*60}")
    print("📚 继续生成穿越小说第4-10章")
    print(f"{'='*60}\n")

    # Initialize DeepSeek LLM
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 未设置DEEPSEEK_API_KEY环境变量")
        sys.exit(1)

    print("初始化 DeepSeek LLM...")
    llm = DeepSeekLLM(
        api_key=api_key,
        model="deepseek-chat",
        temperature=0.8,
        max_tokens=4096,
    )

    # Create output directory
    output_dir = project_root / "data" / "novels" / NOVEL_ID / "chapters"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track metrics
    total_words = 0
    total_tokens = 0
    chapter_times = {}
    chapter_tokens = {}
    chapter_words = {}

    # Generate each chapter
    for chapter_info in CHAPTERS:
        print(f"\n{'─'*60}")
        print(f"生成第 {chapter_info['number']} 章: {chapter_info['title']}")
        print(f"{'─'*60}")

        try:
            content, elapsed, tokens = await generate_chapter(llm, chapter_info)

            # Save chapter
            chapter_filename = f"chapter_{chapter_info['number']:03d}.md"
            chapter_path = output_dir / chapter_filename

            with open(chapter_path, "w", encoding="utf-8") as f:
                f.write(f"# 第{chapter_info['number']}章 {chapter_info['title']}\n\n")
                f.write(content)
                f.write("\n\n---\n")
                f.write(f"*字数: {len(content.replace(' ', '').replace(chr(10), ''))}字 | ")
                f.write(f"生成时间: {elapsed:.1f}秒 | Token消耗: {tokens}*\n")

            # Track metrics
            word_count = len(content.replace(" ", "").replace("\n", ""))
            total_words += word_count
            total_tokens += tokens
            chapter_times[chapter_info['number']] = elapsed
            chapter_tokens[chapter_info['number']] = tokens
            chapter_words[chapter_info['number']] = word_count

            print(f"\n✓ 第 {chapter_info['number']} 章完成: {chapter_info['title']}")
            print(f"  字数: {word_count} | 耗时: {elapsed:.1f}秒 | Tokens: {tokens}")
            print(f"  已保存到: {chapter_path}")

        except Exception as e:
            print(f"\n✗ 第 {chapter_info['number']} 章生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # Continue with next chapter
            continue

    # Save generation report
    report = {
        "novel_id": NOVEL_ID,
        "title": NOVEL_TITLE,
        "genre": GENRE,
        "language": LANGUAGE,
        "generation_time": datetime.now().isoformat(),
        "total_chapters": len(CHAPTERS),
        "total_words": total_words,
        "total_tokens": total_tokens,
        "chapter_times": chapter_times,
        "chapter_tokens": chapter_tokens,
        "chapter_words": chapter_words,
    }

    report_path = output_dir.parent / "continuation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print final summary
    print(f"\n{'='*60}")
    print("🎉 续写生成完成!")
    print(f"{'='*60}")
    print(f"📖 书名: {NOVEL_TITLE}")
    print(f"📝 生成章节: 4-10 (共{len(CHAPTERS)}章)")
    print(f"📊 总字数: {total_words}")
    print(f"⚡ Token消耗: {total_tokens}")
    print(f"📁 输出目录: {output_dir.parent}")
    print(f"📄 报告路径: {report_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
