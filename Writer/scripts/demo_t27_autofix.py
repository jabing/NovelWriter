#!/usr/bin/env python
"""Demonstration of T27 Auto-Fix Loop.

This script demonstrates the automatic consistency fixing feature
by creating a chapter with a dead character error and showing
the auto-fix loop detecting and repairing it.
"""

import asyncio

# Setup paths
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.base import BaseLLM, LLMResponse
from src.novel.continuity import CharacterState
from src.novel.summary_manager import SummaryManager


class DemoMockLLM(BaseLLM):
    """Mock LLM that simulates fixing content."""

    def __init__(self, delay: float = 0.01, **kwargs):
        super().__init__(**kwargs)
        self.delay = delay

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        await asyncio.sleep(self.delay)
        return LLMResponse(content="Generated content", tokens_used=100, model="demo-mock")

    async def generate_with_system(self, system_prompt: str = "", user_prompt: str = "", **kwargs):
        await asyncio.sleep(self.delay)

        # Handle both naming conventions (base class uses system_prompt/user_prompt,
        # but auto_fixer uses system/prompt)
        system = kwargs.get("system") or system_prompt
        prompt = kwargs.get("prompt") or user_prompt

        # If this is a fix request, simulate fixing
        if "请修改以下内容以修复以下问题" in system or "fixing inconsistencies" in system.lower():
            # Extract original content and return "fixed" version
            if "Villain说：我回来了" in prompt or "Villain说" in prompt:
                # Simulate fix: change active behavior to reference
                return LLMResponse(
                    content="众人回想起Villain生前的往事，他虽然已经离世，但他的精神依然影响着大家。",
                    tokens_used=150,
                    model="demo-mock-fixed",
                )

        # Default response for summarization
        return LLMResponse(content="Summary of chapter content", tokens_used=100, model="demo-mock")
        await asyncio.sleep(self.delay)

        # If this is a fix request, simulate fixing
        if (
            "请修改以下内容以修复以下问题" in system_prompt
            or "fixing inconsistencies" in system_prompt.lower()
        ):
            # Extract original content and return "fixed" version
            if "Villain说：我回来了" in user_prompt or "Villain说" in user_prompt:
                # Simulate fix: change active behavior to reference
                return LLMResponse(
                    content="众人回想起Villain生前的往事，他虽然已经离世，但他的精神依然影响着大家。",
                    tokens_used=150,
                    model="demo-mock-fixed",
                )

        # Default response for summarization
        return LLMResponse(content="Summary of chapter content", tokens_used=100, model="demo-mock")


async def demo_autofix():
    """Demonstrate T27 auto-fix loop."""
    print("=" * 70)
    print("T27 Auto-Fix Loop Demonstration")
    print("=" * 70)

    with TemporaryDirectory() as tmpdir:
        # Setup
        storage = Path(tmpdir)
        mock_llm = DemoMockLLM(delay=0.01)

        # Create manager with auto-fix enabled
        manager = SummaryManager(
            storage_path=storage, novel_id="demo_novel", llm=mock_llm, use_auto_fix=True
        )

        # Setup story state with a dead character
        manager.hierarchical_state.global_state.main_characters["Villain"] = CharacterState(
            name="Villain", status="dead", location="grave", physical_form="none"
        )
        manager.hierarchical_state.save_global_state()

        print("\n1. Setup complete")
        print("   - Story: demo_novel")
        print("   - Character 'Villain' status: DEAD")

        # Create problematic content
        problematic_content = "Villain说：我回来了！这次我要复仇。"
        print("\n2. Original content (with dead character error):")
        print(f"   {problematic_content}")

        # Process with auto-fix
        print("\n3. Processing with auto-fix enabled...")
        summary, verification, auto_fix = await manager.process_chapter_with_autofix(
            chapter_number=5,
            title="第五章：复仇",
            content=problematic_content,
            max_fix_iterations=3,
        )

        # Show results
        print("\n4. Results:")
        print(f"   - Verification consistent: {verification.is_consistent}")
        print(f"   - Issues found: {len(verification.inconsistencies)}")

        if auto_fix:
            print(f"   - Auto-fix iterations: {auto_fix.iteration_count}")
            print(f"   - Auto-fix success: {auto_fix.success}")
            print(f"   - Manual review needed: {auto_fix.manual_review_required}")

            if auto_fix.final_content != problematic_content:
                print("\n5. Fixed content:")
                print(f"   {auto_fix.final_content}")
                print("\n✅ T27 successfully detected and fixed the dead character issue!")
            else:
                print("\n⚠️  Content unchanged (verification may have passed)")
        else:
            print("   - No auto-fix attempted (no issues or disabled)")
            print("\n✅ Content passed verification - no fixes needed!")


if __name__ == "__main__":
    asyncio.run(demo_autofix())
