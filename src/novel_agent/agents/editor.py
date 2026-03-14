# src/agents/editor.py
"""Editor Agent - Content review and quality control."""

import json
import re
from typing import Any

from src.novel_agent.agents.base import AgentResult, BaseAgent


class EditorAgent(BaseAgent):
    """Agent responsible for content review and quality control.

    Performs:
    - Grammar and spelling checks
    - Style consistency
    - Character consistency verification
    - Plot logic verification
    - Quality scoring
    - Web fiction specific checks (hooks, pacing, mobile optimization)
    """

    # Common issues to check
    STYLE_ISSUES = [
        (r"\b(very|really|quite|somewhat|rather)\s+\w+", "Weak modifier"),
        (r"\b(is|are|was|were)\s+\w+ed\b", "Passive voice"),
        (r"\b(\w+)\s+\1\b", "Word repetition"),
        (r"[!?]{2,}", "Multiple punctuation"),
        (r"\.{4,}", "Ellipsis overuse"),
    ]

    # Web fiction specific thresholds
    MAX_PARAGRAPH_WORDS = 60  # Mobile-friendly
    MIN_DIALOGUE_RATIO = 0.30  # At least 30% dialogue for web fiction
    TARGET_OPENING_WORDS = 300  # Hook must be in first 300 words
    TARGET_CLOSING_WORDS = 200  # Closing hook in last 200 words

    def __init__(self, name: str = "Editor Agent", **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute editing.

        Args:
            input_data: Must contain:
                - content: str (chapter content)
                - characters: list (for consistency check)
                - world_context: dict (for consistency check)
                - chapter_number: int (optional, for golden 3 chapters check)

        Returns:
            AgentResult with edited content and issues
        """
        try:
            content = input_data.get("content", "")
            characters = input_data.get("characters", [])
            world_context = input_data.get("world_context", {})
            chapter_number = input_data.get("chapter_number", 1)

            # Run style checks
            style_issues = self._check_style(content)

            # Run web fiction specific checks
            web_fiction_issues = self._check_web_fiction_quality(content, chapter_number)

            # Run consistency checks with LLM
            consistency_report = await self._check_consistency(content, characters, world_context)

            # Score the content (web fiction specific scoring)
            quality_score = await self._score_content_web_fiction(content, chapter_number)

            # Generate improved version (optional)
            edited_content = await self._edit_content(
                content, style_issues + web_fiction_issues, consistency_report
            )

            issues = style_issues + web_fiction_issues + consistency_report.get("issues", [])

            return AgentResult(
                success=True,
                data={
                    "original_content": content,
                    "edited_content": edited_content,
                    "style_issues": style_issues,
                    "web_fiction_issues": web_fiction_issues,
                    "consistency_report": consistency_report,
                    "quality_score": quality_score,
                    "all_issues": issues,
                    "word_count": len(content.split()),
                    "dialogue_ratio": self._calculate_dialogue_ratio(content),
                    "hook_analysis": self._analyze_hooks(content),
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Editing failed: {str(e)}"],
            )

    def _check_style(self, content: str) -> list[dict[str, Any]]:
        """Check for common style issues.

        Args:
            content: Chapter content

        Returns:
            List of style issues found
        """
        issues = []

        for pattern, issue_type in self.STYLE_ISSUES:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append(
                    {
                        "type": issue_type,
                        "text": match.group(),
                        "position": match.start(),
                        "suggestion": f"Consider revising: {match.group()}",
                    }
                )

        # Check sentence length
        sentences = re.split(r"[.!?]+", content)
        for sentence in sentences:
            words = sentence.split()
            if len(words) > 40:
                issues.append(
                    {
                        "type": "Long sentence",
                        "text": sentence[:100] + "...",
                        "suggestion": "Consider breaking into shorter sentences",
                    }
                )

        # Check paragraph length
        paragraphs = content.split("\n\n")
        for para in paragraphs:
            words = para.split()
            if len(words) > 300:
                issues.append(
                    {
                        "type": "Long paragraph",
                        "text": f"Paragraph with {len(words)} words",
                        "suggestion": "Consider breaking into smaller paragraphs",
                    }
                )

        return issues

    def _check_web_fiction_quality(self, content: str, chapter_number: int) -> list[dict[str, Any]]:
        """Check web fiction specific quality issues.

        Args:
            content: Chapter content
            chapter_number: Chapter number for special handling

        Returns:
            List of web fiction specific issues
        """
        issues = []
        words = content.split()
        word_count = len(words)

        # 1. Check opening hook (first 300 words)
        opening = " ".join(words[: min(300, word_count)])
        opening_issues = self._analyze_opening_hook(opening, chapter_number)
        issues.extend(opening_issues)

        # 2. Check closing hook (last 200 words)
        closing = " ".join(words[max(0, word_count - 200) :])
        closing_issues = self._analyze_closing_hook(closing, chapter_number)
        issues.extend(closing_issues)

        # 3. Check dialogue ratio
        dialogue_ratio = self._calculate_dialogue_ratio(content)
        if dialogue_ratio < self.MIN_DIALOGUE_RATIO:
            issues.append(
                {
                    "type": "Low dialogue ratio",
                    "severity": "medium",
                    "description": f"Only {dialogue_ratio:.1%} dialogue. Web fiction needs at least {self.MIN_DIALOGUE_RATIO:.0%}.",
                    "suggestion": "Add more dialogue to increase engagement",
                }
            )

        # 4. Check paragraph length (mobile optimization)
        paragraphs = content.split("\n\n")
        long_paragraphs = 0
        for i, para in enumerate(paragraphs):
            para_words = len(para.split())
            if para_words > self.MAX_PARAGRAPH_WORDS:
                long_paragraphs += 1
                if long_paragraphs <= 3:  # Only report first 3
                    issues.append(
                        {
                            "type": "Long paragraph",
                            "severity": "medium",
                            "description": f"Paragraph {i + 1} has {para_words} words (max {self.MAX_PARAGRAPH_WORDS} for mobile)",
                            "suggestion": "Break into shorter paragraphs for mobile readers",
                        }
                    )

        if long_paragraphs > len(paragraphs) * 0.3:
            issues.append(
                {
                    "type": "Mobile readability",
                    "severity": "high",
                    "description": f"{long_paragraphs}/{len(paragraphs)} paragraphs too long for mobile",
                    "suggestion": "Restructure content with mobile readers in mind",
                }
            )

        # 5. Check sentence variety
        sentence_issues = self._check_sentence_variety(content)
        issues.extend(sentence_issues)

        # 6. Golden 3 chapters special checks
        if chapter_number <= 3:
            golden_issues = self._check_golden_chapters(content, chapter_number)
            issues.extend(golden_issues)

        # 7. Check pacing (scene changes)
        pacing_issues = self._check_pacing(content)
        issues.extend(pacing_issues)

        return issues

    def _analyze_opening_hook(self, opening: str, chapter_number: int) -> list[dict[str, Any]]:
        """Analyze the strength of opening hook."""
        issues = []
        opening_lower = opening.lower()

        # Check for weak opening patterns
        weak_starts = [
            ("it was", "Starts with 'It was' - too generic"),
            ("the day", "Starts with 'The day' - slow start"),
            ("once upon", "Fairy tale opening - not suitable for web fiction"),
            ("in the", "Starts with 'In the' - consider starting with action"),
            ("a long time", "Cliché opening"),
            ("there was", "Expository opening - too passive"),
        ]

        for pattern, description in weak_starts:
            if opening_lower.startswith(pattern):
                issues.append(
                    {
                        "type": "Weak opening",
                        "severity": "high" if chapter_number == 1 else "medium",
                        "description": description,
                        "suggestion": "Start with dialogue, action, or intriguing statement",
                    }
                )
                break

        # Check for exposition dump
        if opening.count(".") > 5 and '"' not in opening[:200]:
            issues.append(
                {
                    "type": "Exposition heavy opening",
                    "severity": "high",
                    "description": "First 200 words are all narration - no dialogue or action",
                    "suggestion": "Start with character interaction or immediate conflict",
                }
            )

        # Check for hook indicators
        hook_elements = ['"', "!", "?", "...", "suddenly", "impossible", "never", "always"]
        if not any(elem in opening_lower for elem in hook_elements):
            issues.append(
                {
                    "type": "Missing hook",
                    "severity": "high",
                    "description": "Opening lacks hook elements (dialogue, emotion, intrigue)",
                    "suggestion": "Add dialogue, strong emotion, or mysterious element",
                }
            )

        return issues

    def _analyze_closing_hook(self, closing: str, chapter_number: int) -> list[dict[str, Any]]:
        """Analyze the strength of closing hook."""
        issues = []
        closing_lower = closing.lower()

        # Check for weak endings
        weak_endings = [
            ("the end", "Explicitly states 'the end' - no hook"),
            ("to be continued", "Cliché ending"),
            ("and so", "Tie-up ending - no forward momentum"),
        ]

        for pattern, description in weak_endings:
            if pattern in closing_lower:
                issues.append(
                    {
                        "type": "Weak ending",
                        "severity": "high",
                        "description": description,
                        "suggestion": "End with unresolved tension or new question",
                    }
                )

        # Check for hook indicators in last 100 words
        last_100 = " ".join(closing.split()[-100:])
        hook_indicators = [
            "?",
            "!",
            "...",
            "what",
            "who",
            "how",
            "why",
            "wait",
            "know",
            "truth",
            "secret",
            "realized",
            "suddenly",
            "door",
            "voice",
        ]

        if not any(indicator in last_100.lower() for indicator in hook_indicators):
            issues.append(
                {
                    "type": "No closing hook",
                    "severity": "critical",
                    "description": "Chapter ending doesn't create desire to read next chapter",
                    "suggestion": "Add cliffhanger, unanswered question, or emotional peak",
                }
            )

        # Check if ends on resolution
        resolution_words = ["happily", "finally", "resolved", "peace", "calm", "safe"]
        if any(word in closing_lower[-50:] for word in resolution_words):
            issues.append(
                {
                    "type": "Ending on resolution",
                    "severity": "medium",
                    "description": "Chapter ends on note of resolution - no forward momentum",
                    "suggestion": "End before resolution, or introduce new complication",
                }
            )

        return issues

    def _calculate_dialogue_ratio(self, content: str) -> float:
        """Calculate the ratio of dialogue to total content."""
        # Count dialogue (text between quotes)
        dialogue_pattern = r'"[^"]*"'
        dialogue_matches = re.findall(dialogue_pattern, content)
        dialogue_words = sum(len(match.split()) for match in dialogue_matches)

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        return dialogue_words / total_words

    def _check_sentence_variety(self, content: str) -> list[dict[str, Any]]:
        """Check for sentence variety and rhythm."""
        issues = []
        sentences = re.split(r"[.!?]+", content)

        # Filter out empty strings
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 3:
            return issues

        # Check sentence lengths
        lengths = [len(s.split()) for s in sentences]

        # Check for repetitive patterns
        short_sentences = sum(1 for length in lengths if length < 5)
        long_sentences = sum(1 for length in lengths if length > 30)

        if short_sentences > len(sentences) * 0.5:
            issues.append(
                {
                    "type": "Choppy writing",
                    "severity": "low",
                    "description": f"{short_sentences}/{len(sentences)} sentences are very short",
                    "suggestion": "Combine some short sentences for better flow",
                }
            )

        if long_sentences > len(sentences) * 0.3:
            issues.append(
                {
                    "type": "Complex sentences",
                    "severity": "low",
                    "description": f"{long_sentences}/{len(sentences)} sentences are very long",
                    "suggestion": "Break some long sentences into shorter ones",
                }
            )

        return issues

    def _check_golden_chapters(self, content: str, chapter_number: int) -> list[dict[str, Any]]:
        """Special checks for first 3 chapters (golden chapters)."""
        issues = []

        if chapter_number == 1:
            # Chapter 1: Must establish conflict and protagonist
            if content.lower().count("i ") < 5 and content.lower().count("he ") < 5:
                issues.append(
                    {
                        "type": "Golden Chapter 1",
                        "severity": "critical",
                        "description": "Chapter 1 doesn't establish clear protagonist perspective",
                        "suggestion": "Ensure clear POV and character introduction in first chapter",
                    }
                )

            # Check for immediate conflict
            conflict_indicators = [
                "conflict",
                "problem",
                "trouble",
                "threat",
                "danger",
                "refused",
                "rejected",
                "fought",
                "argued",
                "stolen",
            ]
            if not any(indicator in content.lower() for indicator in conflict_indicators):
                issues.append(
                    {
                        "type": "Golden Chapter 1 - No conflict",
                        "severity": "critical",
                        "description": "Chapter 1 lacks clear conflict or problem",
                        "suggestion": "Introduce conflict within first chapter to hook readers",
                    }
                )

        elif chapter_number == 2:
            # Chapter 2: Build on chapter 1, raise stakes
            issues.append(
                {
                    "type": "Golden Chapter 2",
                    "severity": "info",
                    "description": "Chapter 2 should escalate tension from chapter 1",
                    "suggestion": "Ensure stakes are raised and plot moves forward",
                }
            )

        elif chapter_number == 3:
            # Chapter 3: Major hook or plot turn
            issues.append(
                {
                    "type": "Golden Chapter 3",
                    "severity": "info",
                    "description": "Chapter 3 should have major plot development or revelation",
                    "suggestion": "Include significant event that commits protagonist to journey",
                }
            )

        return issues

    def _check_pacing(self, content: str) -> list[dict[str, Any]]:
        """Check pacing through scene changes and emotional beats."""
        issues = []
        words = content.split()
        word_count = len(words)

        # Estimate scene changes (rough heuristic: look for time/location transitions)
        scene_indicators = [
            "meanwhile",
            "later",
            "hours later",
            "the next day",
            "that evening",
            "morning came",
            "back at",
        ]
        scene_changes = sum(content.lower().count(indicator) for indicator in scene_indicators)

        # Web fiction: Scene change every 800-1000 words
        expected_scenes = word_count / 900
        if scene_changes < expected_scenes * 0.5:
            issues.append(
                {
                    "type": "Pacing - Few scene changes",
                    "severity": "medium",
                    "description": f"Only ~{scene_changes} scene changes in {word_count} words",
                    "suggestion": "Add more scene transitions or location/time changes",
                }
            )

        return issues

    def _analyze_hooks(self, content: str) -> dict[str, Any]:
        """Analyze hook strength in content."""
        words = content.split()

        # Opening analysis
        opening = " ".join(words[:100])
        opening_score = 5

        if any(c in opening for c in ['"', "!", "?"]):
            opening_score += 2
        if any(word in opening.lower() for word in ["suddenly", "impossible", "never"]):
            opening_score += 1
        if opening.lower().startswith(("the ", "it ", "a ", "in ")):
            opening_score -= 2

        # Closing analysis
        closing = " ".join(words[-100:])
        closing_score = 5

        if any(c in closing for c in ["?", "!", "..."]):
            closing_score += 2
        if any(
            word in closing.lower() for word in ["what", "who", "how", "why", "truth", "secret"]
        ):
            closing_score += 2
        if any(word in closing.lower() for word in ["finally", "happily", "peace"]):
            closing_score -= 3

        return {
            "opening_score": max(0, min(10, opening_score)),
            "closing_score": max(0, min(10, closing_score)),
            "overall": (opening_score + closing_score) / 2,
        }

    async def _check_consistency(
        self,
        content: str,
        characters: list[dict[str, Any]],
        world_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Check content consistency using LLM.

        Args:
            content: Chapter content
            characters: List of character profiles
            world_context: World context

        Returns:
            Consistency report
        """
        char_names = [c.get("name", "") for c in characters[:5]]

        system_prompt = """You are a professional fiction editor.
Analyze content for consistency issues with characters and world-building.
Your output must be valid JSON."""

        user_prompt = f"""Analyze this chapter for consistency issues.

CHARACTERS TO CHECK:
{json.dumps(char_names, indent=2)}

CHAPTER CONTENT (first 2000 chars):
{content[:2000]}

Check for:
1. Character name consistency
2. Personality consistency (actions match established traits)
3. World-building consistency
4. Plot logic issues

Generate a JSON report:
{{
    "issues": [
        {{
            "type": "character/worldbuilding/plot",
            "severity": "high/medium/low",
            "description": "Description of the issue",
            "location": "Where in text",
            "suggestion": "How to fix"
        }}
    ],
    "character_appearances": ["Alice", "Bob"],
    "overall_consistency": "good/fair/poor",
    "summary": "Brief summary of issues"
}}

Only output valid JSON, no other text."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        try:
            content_response = response.content.strip()
            if content_response.startswith("```"):
                content_response = content_response.split("\n", 1)[1]
                content_response = content_response.rsplit("```", 1)[0]
            return json.loads(content_response)
        except json.JSONDecodeError:
            return {
                "issues": [],
                "character_appearances": [],
                "overall_consistency": "unknown",
                "summary": "Could not parse consistency report",
            }

    async def _score_content_web_fiction(self, content: str, chapter_number: int) -> dict[str, Any]:
        """Score content specifically for web fiction quality criteria.

        Args:
            content: Chapter content
            chapter_number: Chapter number for context

        Returns:
            Detailed quality score breakdown
        """
        system_prompt = """You are a web fiction quality expert.
Score this chapter on web fiction specific criteria (1-10 scale).

SCORING CRITERIA:
1. HOOK STRENGTH (0-10)
   - Opening grabs attention immediately (first 300 words)
   - Creates curiosity and "need to know"
   - No slow exposition or info-dumping

2. EMOTIONAL ENGAGEMENT (0-10)
   - Readers can connect with characters
   - Emotional beats are well-placed and earned
   - Creates emotional investment

3. PACING & RHYTHM (0-10)
   - Appropriate mix of action and reflection
   - No dragging sections
   - Scene changes at good intervals (~800-1000 words)
   - Chapter ends with forward momentum

4. CLIFFHANGER POTENTIAL (0-10)
   - Ending creates desire to read next chapter
   - Unresolved tension or new question
   - "Just one more chapter" feeling

5. DIALOGUE QUALITY (0-10)
   - Dialogue reveals character
   - Natural and engaging
   - Good balance with narration (30-50%)
   - Each character has distinct voice

6. MOBILE READABILITY (0-10)
   - Short paragraphs (mobile-friendly)
   - Sentence variety
   - Easy to read on phone screen

7. GENRE TROPE EXECUTION (0-10)
   - Uses popular tropes effectively
   - Brings fresh twist to familiar elements
   - Meets reader expectations

SCORING GUIDE:
- 9-10: Exceptional, bestseller quality
- 7-8: Good, engaging with minor issues
- 5-6: Acceptable but needs improvement
- Below 5: Significant problems

Be CRITICAL. Most chapters score 5-7. Only award 9+ for truly exceptional work.

Output valid JSON only."""

        user_prompt = f"""Score this web novel chapter (Chapter {chapter_number}):

{content[:2000]}...

Generate detailed JSON score:
{{
    "overall": 7.5,
    "breakdown": {{
        "hook_strength": 8,
        "emotional_engagement": 7,
        "pacing_rhythm": 6,
        "cliffhanger_potential": 9,
        "dialogue_quality": 7,
        "mobile_readability": 8,
        "trope_execution": 7
    }},
    "critical_issues": [],
    "strengths": ["Strong opening", "Good cliffhanger"],
    "weaknesses": ["Pacing drags in middle"],
    "reader_retention_prediction": "high/medium/low",
    "recommendation": "publish/revise/major_revision"
}}

SCORE BELOW 7 IN ANY CATEGORY = chapter needs revision in that area.

Output ONLY valid JSON, no explanation."""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.4,  # Lower for more consistent scoring
                max_tokens=1000,
            )

            content_response = response.content.strip()
            if content_response.startswith("```"):
                content_response = content_response.split("\n", 1)[1]
                content_response = content_response.rsplit("```", 1)[0]

            score_data = json.loads(content_response)

            # Ensure all required fields
            if "breakdown" not in score_data:
                score_data["breakdown"] = {}

            # Calculate overall from breakdown if not present
            if "overall" not in score_data:
                breakdown = score_data.get("breakdown", {})
                if breakdown:
                    score_data["overall"] = sum(breakdown.values()) / len(breakdown)
                else:
                    score_data["overall"] = 5

            # Add web fiction specific flag
            score_data["is_web_fiction_score"] = True
            score_data["chapter_number"] = chapter_number

            return score_data

        except Exception as e:
            # Fallback scoring
            return {
                "overall": 5,
                "breakdown": {
                    "hook_strength": 5,
                    "emotional_engagement": 5,
                    "pacing_rhythm": 5,
                    "cliffhanger_potential": 5,
                    "dialogue_quality": 5,
                    "mobile_readability": 5,
                    "trope_execution": 5,
                },
                "critical_issues": [f"Scoring error: {str(e)}"],
                "strengths": [],
                "weaknesses": ["Could not properly analyze"],
                "reader_retention_prediction": "unknown",
                "recommendation": "revise",
                "is_web_fiction_score": True,
                "chapter_number": chapter_number,
            }

    async def _edit_content(
        self,
        content: str,
        style_issues: list[dict[str, Any]],
        consistency_report: dict[str, Any],
    ) -> str:
        """Generate improved version of content.

        Args:
            content: Original content
            style_issues: List of style issues
            consistency_report: Consistency report

        Returns:
            Edited content
        """
        # Only edit if there are significant issues
        if len(style_issues) < 5 and consistency_report.get("overall_consistency") == "good":
            return content  # Return original if mostly good

        system_prompt = """You are a professional fiction editor.
Improve the given content while maintaining the author's voice.
Focus on clarity, flow, and engagement."""

        # Create summary of issues
        issues_summary = f"Style issues: {len(style_issues)}"
        if consistency_report.get("issues"):
            issues_summary += f", Consistency issues: {len(consistency_report['issues'])}"

        user_prompt = f"""Edit this chapter to improve quality.

CONTENT TO EDIT:
{content}

ISSUES TO ADDRESS:
{issues_summary}

Make these improvements:
1. Fix awkward phrasing
2. Improve sentence flow
3. Enhance descriptions
4. Sharpen dialogue
5. Maintain the author's voice and story

Return the edited chapter:"""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=4000,
        )

        return response.content.strip()

    async def check_character_consistency(
        self,
        content: str,
        character_name: str,
        character_profile: dict[str, Any],
    ) -> dict[str, Any]:
        """Check consistency for a specific character.

        Args:
            content: Chapter content
            character_name: Name of character to check
            character_profile: Character's profile

        Returns:
            Consistency report for this character
        """
        system_prompt = """You are a character consistency expert.
Analyze how a character is portrayed in text.
Your output must be valid JSON."""

        user_prompt = f"""Check if this character is portrayed consistently.

CHARACTER PROFILE:
{json.dumps(character_profile, indent=2)[:1000]}

CHAPTER CONTENT:
{content}

Generate a JSON report:
{{
    "character": "{character_name}",
    "consistent": true/false,
    "issues": ["Issue 1", "Issue 2"],
    "traits_shown": ["trait observed in text"],
    "traits_missing": ["expected traits not shown"],
    "dialogue_quality": "natural/forced/mixed",
    "recommendation": "Character portrayal suggestions"
}}

Only output valid JSON."""

        response = await self.llm.generate_with_system(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        try:
            content_response = response.content.strip()
            if content_response.startswith("```"):
                content_response = content_response.split("\n", 1)[1]
                content_response = content_response.rsplit("```", 1)[0]
            return json.loads(content_response)
        except json.JSONDecodeError:
            return {
                "character": character_name,
                "consistent": True,
                "issues": [],
            }
