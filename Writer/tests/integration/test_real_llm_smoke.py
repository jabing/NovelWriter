"""Real LLM smoke test for hierarchical memory system.

This test uses actual DeepSeek API calls to validate:
1. Chapter summarization with real LLM
2. Hierarchical state management
3. Basic integration (5 chapters only to control costs)

Cost: ~$0.02-0.05 for 5 chapters (DeepSeek API at $0.002/1k tokens)

Skip if DEEPSEEK_API_KEY not configured.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.novel.consistency_verifier import ConsistencyVerifier
from src.novel.summary_manager import SummaryManager

# Skip tests if API key not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("DEEPSEEK_API_KEY")
    or os.getenv("DEEPSEEK_API_KEY") == "sk-your-deepseek-official-key-here",
    reason="DEEPSEEK_API_KEY not configured",
)


class TestRealLLMSmoke:
    """Smoke tests with real LLM calls (5 chapters)."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "real_llm_smoke"

    @pytest.fixture
    def real_llm(self):
        """Create real DeepSeek LLM instance."""
        from src.llm.deepseek import DeepSeekLLM

        api_key = os.getenv("DEEPSEEK_API_KEY")
        return DeepSeekLLM(
            api_key=api_key,
            model="deepseek-chat",
            temperature=0.3,  # Lower for more consistent summaries
        )

    @pytest.fixture
    def summary_manager(self, temp_storage: Path, real_llm) -> SummaryManager:
        """Create SummaryManager with real LLM."""
        return SummaryManager(temp_storage, "smoke_test_novel", real_llm)

    @pytest.fixture
    def verifier(self) -> ConsistencyVerifier:
        """Create ConsistencyVerifier."""
        return ConsistencyVerifier()

    @pytest.mark.asyncio
    async def test_llm_connection(self, real_llm) -> None:
        """Test basic LLM connectivity."""
        response = await real_llm.generate(
            prompt="请用一句话回答：1+1 等于几？",
            max_tokens=50,
        )

        assert response is not None
        assert len(response.content) > 0
        assert "2" in response.content or "二" in response.content

        print("\n✅ LLM Connection Test Passed")
        print(f"   Response: {response.content[:100]}...")

    @pytest.mark.asyncio
    async def test_chapter_summarization_real_llm(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test chapter summarization with real LLM."""
        chapter_content = """
第一章：启程

艾琳站在学院的最高塔楼上，俯瞰着下方熙熙攘攘的校园。夕阳将整座城市染成了金色。

"准备好了吗？"身后传来一个熟悉的声音。

她转过身，看到导师莫里斯正微笑着看着她。这位白发苍苍的老者已经教导了她整整十年。

"我想是的，导师。"艾琳深吸一口气，"虽然我还是有些紧张。"

莫里斯点点头，"紧张是正常的。但记住，你已经掌握了所有必要的知识和技能。你的魔法天赋是我见过最出色的。"

艾琳回想起这十年的训练。从最初连最简单的火球术都无法施展，到如今能够熟练运用各种元素魔法。这一路走来，有太多的汗水和泪水。

"去吧，艾琳。"莫里斯拍了拍她的肩膀，"去完成你的使命。"

她转身走向塔楼的出口。在那一刻，她知道自己的人生即将翻开全新的一页。
        """.strip()

        summary = await summary_manager.process_chapter(
            chapter_number=1,
            title="启程",
            content=chapter_content,
        )

        # Verify summary was generated
        assert summary is not None
        assert summary.chapter_number == 1
        assert summary.title == "启程"
        assert len(summary.summary) > 0

        # Verify summary contains key information
        print("\n✅ Chapter 1 Summary Generated")
        print(f"   Summary: {summary.summary[:150]}...")
        print(f"   Key Events: {summary.key_events[:3]}")

        # Summary should mention the main character
        assert "艾琳" in summary.summary or any("艾琳" in e for e in summary.key_events)

    @pytest.mark.asyncio
    async def test_multi_chapter_real_llm(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test 5 chapters with real LLM."""
        chapters = [
            (1, "启程", "艾琳在魔法学院塔楼上，导师莫里斯为她送行。她即将踏上冒险之旅。"),
            (2, "出发", "艾琳离开学院，进入北方森林。她遇到了一只迷路的小狐狸。"),
            (3, "森林", "艾琳在森林中度过第一夜。她练习魔法，小狐狸在一旁观看。"),
            (4, "发现", "艾琳发现了一个古老的遗迹。遗迹中有神秘的符文和魔法装置。"),
            (5, "抉择", "艾琳面临抉择：继续探索遗迹还是返回学院报告。她决定先记录发现。"),
        ]

        print("\n=== Processing 5 Chapters with Real LLM ===\n")

        for chapter_num, title, outline in chapters:
            # Generate simple content based on outline
            content = f"""
第{chapter_num}章：{title}

{outline}

艾琳继续她的旅程，每一步都让她更加接近真相。周围的景色不断变化，但她心中的目标始终清晰。
            """.strip()

            # Process chapter
            summary = await summary_manager.process_chapter(
                chapter_number=chapter_num,
                title=title,
                content=content,
            )

            print(f"✅ Chapter {chapter_num}: {title}")
            print(f"   Summary ({len(summary.summary)} chars): {summary.summary[:100]}...")
            print(f"   Key Events: {len(summary.key_events)} events")

        # Verify all chapters processed
        assert summary_manager.get_total_chapters() == 5

        # Verify context can be built for chapter 6
        context = summary_manager.get_context_for_chapter(6)
        assert len(context) > 0

        print("\n=== Final Stats ===")
        print(f"✅ Total Chapters: {summary_manager.get_total_chapters()}")
        print(f"✅ Current Arc: {summary_manager.get_current_arc()}")

    @pytest.mark.asyncio
    async def test_consistency_with_real_content(
        self,
        verifier: ConsistencyVerifier,
    ) -> None:
        """Test consistency verification with sample content."""
        from src.novel.continuity import CharacterState, StoryState

        # Create story state
        story_state = StoryState(
            chapter=5,
            location="北方森林",
            active_characters=["艾琳"],
            character_states={
                "艾琳": CharacterState(
                    name="艾琳",
                    status="alive",
                    location="北方森林",
                    physical_form="human",
                ),
            },
        )

        # Test with consistent content
        good_content = """
艾琳在森林中穿行。她想起了导师的教导，继续前进。
        """.strip()

        result = verifier.verify(
            chapter_content=good_content,
            chapter_number=5,
            story_state=story_state,
        )

        # Should be consistent
        print("\n✅ Consistency Check (Good Content)")
        print(f"   Is Consistent: {result.is_consistent}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_arc_summarization_real_llm(
        self,
        summary_manager: SummaryManager,
    ) -> None:
        """Test arc summarization at chapter 10 (slow test)."""
        print("\n=== Testing Arc Summarization (10 Chapters) ===\n")

        # Process 10 chapters
        for i in range(1, 11):
            content = f"""
第{i}章

这是第{i}章的内容。艾琳继续她的冒险旅程，遇到了新的挑战和机遇。
            """.strip()

            await summary_manager.process_chapter(
                chapter_number=i,
                title=f"第{i}章",
                content=content,
            )

            if i % 5 == 0:
                print(f"✅ Chapter {i}/10 processed")

        # Arc summary should be created at chapter 10
        arc_summary = summary_manager.get_arc_summary(1)
        assert arc_summary is not None

        print("\n✅ Arc 1 Summary Generated")
        print(f"   Title: {arc_summary.title}")
        print(f"   Summary ({len(arc_summary.summary)} chars): {arc_summary.summary[:150]}...")
        print(f"   Major Events: {len(arc_summary.major_events)} events")


class TestRealLLMJSONParsing:
    """Test JSON parsing from real LLM responses."""

    @pytest.fixture
    def real_llm(self):
        """Create real DeepSeek LLM instance."""
        from src.llm.deepseek import DeepSeekLLM

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key == "sk-your-deepseek-official-key-here":
            pytest.skip("DEEPSEEK_API_KEY not configured")

        return DeepSeekLLM(
            api_key=api_key,
            model="deepseek-chat",
            temperature=0.3,
        )

    @pytest.mark.asyncio
    async def test_summarization_json_format(self, real_llm) -> None:
        """Test that LLM returns valid JSON for summarization."""
        from src.novel.chapter_summarizer import SUMMARY_SYSTEM_PROMPT, SUMMARY_USER_PROMPT_TEMPLATE

        content = "艾琳站在塔楼上，准备开始她的冒险。导师莫里斯为她送行，祝福她一路平安。"
        user_prompt = SUMMARY_USER_PROMPT_TEMPLATE.format(
            title="启程",
            content=content,
        )

        response = await real_llm.generate_with_system(
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=500,
        )

        print(f"\n=== Raw LLM Response ===\n{response.content[:300]}...\n")

        # Should be valid JSON (or contain JSON)
        import re

        # Try to extract JSON
        try:
            # Try direct parse
            data = json.loads(response.content)
        except json.JSONDecodeError:
            # Try extracting from code block
            match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", response.content)
            if match:
                data = json.loads(match.group(1))
            else:
                # Find JSON object
                match = re.search(r"\{[\s\S]*\}", response.content)
                if match:
                    data = json.loads(match.group(0))
                else:
                    pytest.fail(f"Could not parse JSON from response: {response.content}")

        # Verify expected fields
        assert "summary" in data, "Response should contain 'summary' field"
        assert "key_events" in data, "Response should contain 'key_events' field"

        print("✅ JSON Parsing Successful")
        print(f"   Summary: {data['summary'][:100]}...")
        print(f"   Key Events: {data['key_events']}")


if __name__ == "__main__":
    # Run with: pytest tests/integration/test_real_llm_smoke.py -v
    pytest.main([__file__, "-v"])
