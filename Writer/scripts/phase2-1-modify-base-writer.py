"""Script to modify base_writer.py for Phase 2.1."""

# Read the file
with open("src/agents/writers/base_writer.py", encoding="utf-8") as f:
    content = f.read()

# Add imports after line 5
import_line = 6
imports_to_add = """from src.novel.continuity import StoryState
from src.novel.outline_manager import ChapterSpec
"""
lines = content.split("\n")
lines[import_line:import_line] = imports_to_add + "\n" + lines[import_line:import_line]

# Find write_chapter method and modify its signature
found_write_chapter = False
for i, line in enumerate(lines):
    if "async def write_chapter(" in line:
        method_start = i
        found_write_chapter = True
        # Find the closing parenthesis
        for j in range(i, len(lines)):
            if ")" in lines[j] and "chapter_outline: str" in lines[j]:
                method_end = j
                break
        break

if found_write_chapter:
    # Modify the signature to add new parameters
    signature_line = lines[method_end]
    old_sig = "chapter_outline: str,\n"
    new_params = """story_state: StoryState | None = None,
            previous_chapter_summary: str | None = None,"""
    lines[method_end] = signature_line.replace(old_sig, new_params)

    # Find position after write_chapter method (around line 72)
    for i in range(method_end, len(lines)):
        if (
            lines[i].strip()
            and not lines[i].strip().startswith("async def")
            and not lines[i].strip().startswith("#")
        ):
            insert_after = i
            break

    # Add new methods
    new_methods = """
    
    async def write_chapter_with_context(
        self,
        chapter_spec: ChapterSpec,
        story_state: StoryState,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
        previous_chapter_summary: str | None = None,
        **kwargs,
    ) -> str:
        \"\"\"Write a chapter with full continuity context.
        
        This method wraps write_chapter with additional context from
        story state and chapter specification.
        
        Args:
            chapter_spec: Chapter specification
            story_state: Current story state
            characters: List of character profiles
            world_context: World-building context
            previous_chapter_summary: Summary of previous chapter
            **kwargs: Additional arguments passed to write_chapter
            
        Returns:
            Written chapter content
        \"\"\"
        # Build continuity prompt
        continuity_prompt = self._build_continuity_prompt(
            story_state=story_state,
            previous_summary=previous_chapter_summary or \"\",
            chapter_number=chapter_spec.number,
        )
        
        # Combine chapter summary with continuity prompt
        enhanced_outline = f\"{chapter_spec.summary}\\n{continuity_prompt}\\n\"
        
        # Call write_chapter with continuity info
        return await self.write_chapter(
            chapter_number=chapter_spec.number,
            chapter_outline=enhanced_outline,
            characters=characters,
            world_context=world_context,
            story_state=story_state,
            previous_chapter_summary=previous_chapter_summary,
            **kwargs,
        )

    def _build_continuity_prompt(
        self,
        story_state: StoryState | None,
        previous_summary: str,
        chapter_number: int,
    ) -> str:
        \"\"\"Build a continuity prompt from story state.
        
        Args:
            story_state: Current story state
            previous_summary: Summary of previous chapter
            chapter_number: Current chapter number
            
        Returns:
            Continuity prompt string
        \"\"\"
        if story_state is None:
            return \"\"
        
        prompt_parts = [
            f\"\\n【连续性上下文 - 第{chapter_number}章】\\n\",
            f\"当前地点：{story_state.location}\\n\",
            f\"在场角色：{', '.join(story_state.active_characters)}\\n\",
        ]
        
        if previous_summary:
            prompt_parts.append(f\"\\n前一章总结：\\n{previous_summary}\\n\")
        
        # Add character states
        if story_state.character_states:
            prompt_parts.append(\"\\n角色状态：\\n\")
            for name, state in story_state.character_states.items():
                status_text = f\"- {name}: {state.status}\"
                prompt_parts.append(status_text + \"\\n\")
        
        return \"\".join(prompt_parts)
"""
    lines[insert_after:insert_after] = new_methods + "\n" + lines[insert_after:insert_after]
else:
    print("ERROR: Could not find write_chapter method")

# Write back
with open("src/agents/writers/base_writer.py", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("✅ Successfully modified src/agents/writers/base_writer.py")
