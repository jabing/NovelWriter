# src/agents/review.py
"""Review Agent - Specialized logic contradiction checking and comprehensive validation.

Performs deep analysis of story consistency across multiple dimensions:
- Character consistency and development arcs
- Plot logic and hole detection
- World-building rule adherence
- Timeline and object continuity
- Ethical compliance
- Cross-chapter contradiction detection
"""

import json
import logging
from typing import Any

try:
    from typing import override
except ImportError:
    from typing_extensions import override

from src.novel_agent.agents.base import AgentResult, BaseAgent
from src.novel_agent.novel.constitution import ConstitutionValidator, RuleDomain, get_constitution_summary
from src.novel_agent.novel.glossary import TermStatus
from src.novel_agent.novel.structured_input import StructuredInputSystem

logger = logging.getLogger(__name__)


class ReviewAgent(BaseAgent):
    """Agent for specialized logic contradiction checking and comprehensive validation.

    Uses constitutional rules, glossary, and structured input to perform deep
    consistency analysis across the entire novel writing process.
    """
    constitution_validator: ConstitutionValidator | None
    structured_input: StructuredInputSystem
    _validation_cache: dict[str, Any]

    def __init__(self, name: str = "Review Agent", **kwargs: Any) -> None:
        """Initialize the Review Agent.

        Args:
            name: Agent name
            **kwargs: Passed to BaseAgent (llm, memory, constitution_validator, glossary)
        """
        super().__init__(name=name, **kwargs)

        # Initialize constitution validator if not provided
        if self.constitution_validator is None:
            self.constitution_validator = ConstitutionValidator()

        # Initialize structured input system
        self.structured_input = StructuredInputSystem()

        # Cache for validation results
        self._validation_cache = {}

    @override
    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute comprehensive review and contradiction checking.

        Args:
            input_data: Must contain:
                - content: str (chapter or scene content)
                - chapter_number: int (optional)
                - context: dict with:
                    - characters: list[dict] (character profiles)
                    - plot_elements: list[dict] (plot points)
                    - world_context: dict (world rules, locations, etc.)
                    - timeline_events: list[dict] (timeline data)
                    - objects: list[dict] (object continuity)
                    - foreshadowing: list[dict] (foreshadowing setup/payoff)
                - validation_level: str (optional: 'basic', 'comprehensive', 'deep')

        Returns:
            AgentResult with comprehensive review report
        """
        try:
            content = input_data.get("content", "")
            chapter_number = input_data.get("chapter_number", 1)
            context = input_data.get("context", {})
            validation_level = input_data.get("validation_level", "comprehensive")

            if not content:
                return AgentResult(
                    success=False, data={}, errors=["No content provided for review"]
                )

            logger.info(
                f"ReviewAgent starting review of chapter {chapter_number} with validation level: {validation_level}"
            )

            # 1. Run constitutional rule validation
            constitution_report = await self._run_constitutional_validation(
                content, context, validation_level
            )

            # 2. Perform deep logical analysis (cross-referencing)
            logical_analysis = await self._perform_logical_analysis(
                content, context, validation_level
            )

            # 3. Check glossary consistency
            glossary_report = await self._check_glossary_consistency(content, context)

            # 4. Generate structured task for any issues found
            structured_tasks = await self._generate_structured_tasks(
                constitution_report, logical_analysis, glossary_report
            )

            # 5. Calculate overall consistency score
            overall_score = self._calculate_consistency_score(
                constitution_report, logical_analysis, glossary_report
            )

            # 6. Identify critical contradictions
            critical_contradictions = self._identify_critical_contradictions(
                constitution_report, logical_analysis
            )

            report = {
                "chapter_number": chapter_number,
                "validation_level": validation_level,
                "overall_consistency_score": overall_score,
                "constitution_report": constitution_report,
                "logical_analysis": logical_analysis,
                "glossary_report": glossary_report,
                "critical_contradictions": critical_contradictions,
                "structured_tasks": structured_tasks,
                "recommendations": self._generate_recommendations(
                    constitution_report, logical_analysis, glossary_report
                ),
                "summary": self._generate_summary(overall_score, critical_contradictions),
            }

            logger.info(f"ReviewAgent completed review. Score: {overall_score}/100")

            return AgentResult(
                success=True,
                data=report,
                warnings=[] if overall_score >= 70 else ["Consistency score below threshold (70)"],
            )

        except Exception as e:
            logger.error(f"ReviewAgent execution failed: {e}", exc_info=True)
            return AgentResult(success=False, data={}, errors=[f"Review failed: {str(e)}"])

    async def _run_constitutional_validation(
        self, content: str, context: dict[str, Any], validation_level: str
    ) -> dict[str, Any]:
        """Run validation against all constitutional rules.

        Args:
            content: Chapter content
            context: Story context (characters, plot, world, etc.)
            validation_level: Level of validation detail

        Returns:
            Dictionary with validation results by domain
        """
        if self.constitution_validator is None:
            return {"error": "No constitution validator available"}

        # Prepare data for each domain
        validation_data = {
            "character": {
                "character_profile": context.get("characters", [{}])[0]
                if context.get("characters")
                else {},
                "current_content": content,
                "previous_content": context.get("previous_content", []),
            },
            "plot": {
                "plot_elements": context.get("plot_elements", []),
                "current_content": content,
                "established_facts": context.get("established_facts", {}),
                "foreshadowing": context.get("foreshadowing", []),
            },
            "world": {
                "world_rules": context.get("world_context", {}).get("rules", {}),
                "current_content": content,
                "rule_violations": context.get("rule_violations", []),
                "culture": context.get("world_context", {}).get("culture", {}),
                "locations": context.get("world_context", {}).get("locations", {}),
                "magic_systems": context.get("world_context", {}).get("magic_systems", []),
            },
            "style": {
                "current_content": content,
                "pov": context.get("point_of_view", ""),
                "tone": context.get("tone", ""),
            },
            "consistency": {
                "current_content": content,
                "timeline_events": context.get("timeline_events", []),
                "current_chapter_time": context.get("current_chapter_time", ""),
                "objects": context.get("objects", []),
                "knowledge": context.get("character_knowledge", {}),
            },
            "ethical": {
                "current_content": content,
            },
        }

        # Run validation
        results = self.constitution_validator.validate_all(validation_data)

        # Extract critical violations
        critical_violations = self.constitution_validator.get_critical_violations(results)

        # Calculate domain scores
        domain_scores = {}
        for domain, domain_results in results.items():
            total = len(domain_results)
            passed = sum(1 for _, is_valid, _ in domain_results if is_valid)
            domain_scores[domain] = (passed / total * 100) if total > 0 else 100

        overall_constitution_score = (
            sum(domain_scores.values()) / len(domain_scores) if domain_scores else 100
        )

        return {
            "domain_results": results,
            "domain_scores": domain_scores,
            "overall_score": overall_constitution_score,
            "critical_violations": critical_violations,
            "validation_data_summary": {
                domain: {k: type(v).__name__ for k, v in data.items()}
                for domain, data in validation_data.items()
            },
        }

    async def _perform_logical_analysis(
        self, content: str, context: dict[str, Any], validation_level: str
    ) -> dict[str, Any]:
        """Perform deep logical analysis using LLM.

        Args:
            content: Chapter content
            context: Story context
            validation_level: Level of analysis detail

        Returns:
            Dictionary with logical analysis results
        """
        if self.llm is None:
            return {"error": "No LLM available for logical analysis"}

        # Extract key information from context
        characters = context.get("characters", [])
        plot_elements = context.get("plot_elements", [])
        world_rules = context.get("world_context", {}).get("rules", {})
        timeline = context.get("timeline_events", [])

        system_prompt = """You are a logical consistency expert for novel writing.
        Analyze the given content and context for logical contradictions, plot holes,
        character motivation inconsistencies, and world-building rule violations.

        Focus on:
        1. Logical contradictions within the content
        2. Inconsistencies with established facts
        3. Character actions that contradict established personality or motivations
        4. Plot developments that don't follow from previous events
        5. World-building rule violations
        6. Timeline inconsistencies
        7. Object continuity issues

        Be precise and evidence-based. Reference specific lines or facts.
        Output valid JSON only."""

        user_prompt = f"""Analyze this content for logical consistency:

        CONTENT (Chapter excerpt):
        {content[:2000]}{"..." if len(content) > 2000 else ""}

        CONTEXT:
        - Characters: {json.dumps([c.get("name", "Unknown") for c in characters[:3]], indent=2)}
        - Plot Elements: {len(plot_elements)} elements
        - World Rules: {len(world_rules)} rules
        - Timeline Events: {len(timeline)} events

        Validation Level: {validation_level}

        Generate a JSON report with:
        {{
            "logical_contradictions": [
                {{
                    "type": "character/motivation/plot/world/timeline/object",
                    "description": "Description of contradiction",
                    "evidence": "Specific text or fact evidence",
                    "severity": "critical/high/medium/low",
                    "suggestion": "How to fix"
                }}
            ],
            "plot_holes": [
                {{
                    "description": "Description of plot hole",
                    "evidence": "What's missing or contradictory",
                    "severity": "critical/high/medium/low",
                    "suggestion": "How to fill"
                }}
            ],
            "character_inconsistencies": [
                {{
                    "character": "Character name",
                    "inconsistency": "Description of inconsistency",
                    "evidence": "Evidence from text or profile",
                    "severity": "critical/high/medium/low",
                    "suggestion": "How to fix"
                }}
            ],
            "world_building_issues": [
                {{
                    "rule": "Rule violated",
                    "description": "Description of violation",
                    "evidence": "Evidence from text",
                    "severity": "critical/high/medium/low",
                    "suggestion": "How to fix"
                }}
            ],
            "timeline_issues": [
                {{
                    "issue": "Description of timeline issue",
                    "evidence": "Evidence from timeline or content",
                    "severity": "critical/high/medium/low",
                    "suggestion": "How to fix"
                }}
            ],
            "overall_logical_consistency": "excellent/good/fair/poor",
            "summary": "Brief summary of logical issues found"
        }}

        Only output valid JSON."""

        try:
            response = await self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2000,
            )

            content_response = response.content.strip()
            if content_response.startswith("```"):
                content_response = content_response.split("\n", 1)[1]
                content_response = content_response.rsplit("```", 1)[0]

            analysis = json.loads(content_response)

            # Calculate logical consistency score
            score = self._calculate_logical_score(analysis)
            analysis["logical_consistency_score"] = score

            return analysis

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Logical analysis failed: {e}")
            return {
                "error": f"Logical analysis failed: {str(e)}",
                "logical_contradictions": [],
                "plot_holes": [],
                "character_inconsistencies": [],
                "world_building_issues": [],
                "timeline_issues": [],
                "overall_logical_consistency": "unknown",
                "summary": "Analysis failed",
                "logical_consistency_score": 0,
            }

    async def _check_glossary_consistency(
        self, content: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Check consistency with glossary terms.

        Args:
            content: Chapter content
            context: Story context

        Returns:
            Dictionary with glossary consistency report
        """
        if self.glossary is None:
            return {"error": "No glossary available"}

        try:
            # Get all approved terms from glossary
            all_terms = await self.glossary.get_all_terms(status=TermStatus.APPROVED)

            # Check for undefined terms (simple implementation)
            words = content.lower().split()
            defined_terms = set()
            for term in all_terms:
                defined_terms.add(term.term.lower())
                defined_terms.update(alias.lower() for alias in term.aliases)

            undefined_terms = []
            for word in words:
                clean_word = "".join(c for c in word if c.isalnum())
                if len(clean_word) > 3 and clean_word not in defined_terms:
                    # Check if it's a proper noun (capitalized in original content)
                    # Simple check: if word appears capitalized in content
                    if word.capitalize() in content:
                        undefined_terms.append(word)

            # Check for term usage consistency
            term_usage = {}
            for term in all_terms:
                term_lower = term.term.lower()
                count = content.lower().count(term_lower)
                if count > 0:
                    term_usage[term.term] = {
                        "count": count,
                        "type": term.type.value,
                        "definition": term.definition[:100] + "..."
                        if len(term.definition) > 100
                        else term.definition,
                    }

            # Check for term definition violations (if term used incorrectly)
            # This would require more sophisticated NLP - placeholder for now
            definition_violations = []

            return {
                "total_terms": len(all_terms),
                "terms_used": len(term_usage),
                "term_usage": term_usage,
                "undefined_terms": undefined_terms[:20],  # Limit output
                "definition_violations": definition_violations,
                "glossary_consistency_score": self._calculate_glossary_score(
                    len(all_terms), len(term_usage), len(undefined_terms)
                ),
            }

        except Exception as e:
            logger.warning(f"Glossary consistency check failed: {e}")
            return {
                "error": f"Glossary check failed: {str(e)}",
                "total_terms": 0,
                "terms_used": 0,
                "term_usage": {},
                "undefined_terms": [],
                "definition_violations": [],
                "glossary_consistency_score": 0,
            }

    async def _generate_structured_tasks(
        self,
        constitution_report: dict[str, Any],
        logical_analysis: dict[str, Any],
        glossary_report: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate structured tasks for fixing identified issues.

        Args:
            constitution_report: Constitution validation report
            logical_analysis: Logical analysis report
            glossary_report: Glossary consistency report

        Returns:
            List of structured tasks
        """
        tasks = []

        # Generate tasks from constitution violations
        critical_violations = constitution_report.get("critical_violations", [])
        for violation in critical_violations[:5]:  # Limit to top 5
            tasks.append(
                {
                    "type": "constitution_fix",
                    "priority": "critical",
                    "description": violation,
                    "action": "Review and fix constitutional rule violation",
                    "estimated_effort": "medium",
                }
            )

        # Generate tasks from logical contradictions
        contradictions = logical_analysis.get("logical_contradictions", [])
        for contradiction in contradictions[:5]:
            if contradiction.get("severity") in ["critical", "high"]:
                tasks.append(
                    {
                        "type": "logic_fix",
                        "priority": contradiction["severity"],
                        "description": contradiction["description"],
                        "action": contradiction.get("suggestion", "Review logical consistency"),
                        "estimated_effort": "high"
                        if contradiction["severity"] == "critical"
                        else "medium",
                    }
                )

        # Generate tasks from glossary issues
        undefined_terms = glossary_report.get("undefined_terms", [])
        for term in undefined_terms[:10]:
            tasks.append(
                {
                    "type": "glossary_addition",
                    "priority": "low",
                    "description": f"Undefined term: {term}",
                    "action": f"Add '{term}' to glossary with definition",
                    "estimated_effort": "low",
                }
            )

        # Limit total tasks
        return tasks[:15]

    def _calculate_consistency_score(
        self,
        constitution_report: dict[str, Any],
        logical_analysis: dict[str, Any],
        glossary_report: dict[str, Any],
    ) -> float:
        """Calculate overall consistency score.

        Args:
            constitution_report: Constitution validation report
            logical_analysis: Logical analysis report
            glossary_report: Glossary consistency report

        Returns:
            Overall consistency score (0-100)
        """
        constitution_score = constitution_report.get("overall_score", 100)
        logical_score = logical_analysis.get("logical_consistency_score", 100)
        glossary_score = glossary_report.get("glossary_consistency_score", 100)

        # Weighted average: constitution 40%, logical 40%, glossary 20%
        weights = {"constitution": 0.4, "logical": 0.4, "glossary": 0.2}

        # Apply penalties for critical issues
        penalty = 0

        # Penalty for critical constitution violations
        critical_violations = len(constitution_report.get("critical_violations", []))
        penalty += critical_violations * 5

        # Penalty for critical logical contradictions
        contradictions = logical_analysis.get("logical_contradictions", [])
        critical_contradictions = sum(1 for c in contradictions if c.get("severity") == "critical")
        penalty += critical_contradictions * 10

        # Calculate weighted score
        weighted_score = (
            constitution_score * weights["constitution"]
            + logical_score * weights["logical"]
            + glossary_score * weights["glossary"]
        )

        # Apply penalty (capped at 50% reduction)
        final_score = max(0, weighted_score - penalty)

        return round(final_score, 1)

    def _calculate_logical_score(self, analysis: dict[str, Any]) -> float:
        """Calculate logical consistency score from analysis.

        Args:
            analysis: Logical analysis results

        Returns:
            Logical consistency score (0-100)
        """
        contradictions = analysis.get("logical_contradictions", [])
        plot_holes = analysis.get("plot_holes", [])
        char_inconsistencies = analysis.get("character_inconsistencies", [])
        world_issues = analysis.get("world_building_issues", [])
        timeline_issues = analysis.get("timeline_issues", [])

        # Count issues by severity
        issue_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue_list in [
            contradictions,
            plot_holes,
            char_inconsistencies,
            world_issues,
            timeline_issues,
        ]:
            for issue in issue_list:
                severity = issue.get("severity", "medium")
                issue_counts[severity] += 1

        # Calculate penalty
        penalty = (
            issue_counts["critical"] * 20
            + issue_counts["high"] * 10
            + issue_counts["medium"] * 5
            + issue_counts["low"] * 2
        )

        # Start from 100, subtract penalty
        score = max(0, 100 - penalty)

        return score

    def _calculate_glossary_score(
        self, total_terms: int, terms_used: int, undefined_terms: int
    ) -> float:
        """Calculate glossary consistency score.

        Args:
            total_terms: Total glossary terms
            terms_used: Number of terms used in content
            undefined_terms: Number of undefined terms in content

        Returns:
            Glossary consistency score (0-100)
        """
        if total_terms == 0:
            return 100  # No glossary, no penalty

        # Score based on term usage ratio
        usage_ratio = terms_used / total_terms if total_terms > 0 else 1

        # Penalty for undefined terms
        undefined_penalty = min(30, undefined_terms * 5)

        # Calculate score
        score = usage_ratio * 70 + (100 - undefined_penalty) * 0.3

        return min(100, max(0, score))

    def _identify_critical_contradictions(
        self, constitution_report: dict[str, Any], logical_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Identify and prioritize critical contradictions.

        Args:
            constitution_report: Constitution validation report
            logical_analysis: Logical analysis report

        Returns:
            List of critical contradictions with priority
        """
        critical_issues = []

        # Add critical constitution violations
        for violation in constitution_report.get("critical_violations", []):
            critical_issues.append(
                {
                    "source": "constitution",
                    "type": "rule_violation",
                    "description": violation,
                    "priority": "critical",
                }
            )

        # Add critical logical contradictions
        contradictions = logical_analysis.get("logical_contradictions", [])
        for contradiction in contradictions:
            if contradiction.get("severity") == "critical":
                critical_issues.append(
                    {
                        "source": "logical_analysis",
                        "type": contradiction.get("type", "contradiction"),
                        "description": contradiction.get("description", ""),
                        "priority": "critical",
                        "suggestion": contradiction.get("suggestion", ""),
                    }
                )

        # Add plot holes
        plot_holes = logical_analysis.get("plot_holes", [])
        for hole in plot_holes:
            if hole.get("severity") == "critical":
                critical_issues.append(
                    {
                        "source": "logical_analysis",
                        "type": "plot_hole",
                        "description": hole.get("description", ""),
                        "priority": "critical",
                        "suggestion": hole.get("suggestion", ""),
                    }
                )

        # Deduplicate and limit
        seen = set()
        unique_issues = []
        for issue in critical_issues:
            key = issue["description"][:100]
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        return unique_issues[:10]

    def _generate_recommendations(
        self,
        constitution_report: dict[str, Any],
        logical_analysis: dict[str, Any],
        glossary_report: dict[str, Any],
    ) -> list[str]:
        """Generate actionable recommendations.

        Args:
            constitution_report: Constitution validation report
            logical_analysis: Logical analysis report
            glossary_report: Glossary consistency report

        Returns:
            List of recommendations
        """
        recommendations = []

        # Constitution-based recommendations
        domain_scores = constitution_report.get("domain_scores", {})
        for domain, score in domain_scores.items():
            if score < 70:
                recommendations.append(
                    f"Improve {domain} consistency (current score: {score:.1f}/100)"
                )

        # Logical analysis recommendations
        contradictions = logical_analysis.get("logical_contradictions", [])
        if contradictions:
            recommendations.append(f"Address {len(contradictions)} logical contradiction(s)")

        plot_holes = logical_analysis.get("plot_holes", [])
        if plot_holes:
            recommendations.append(f"Fill {len(plot_holes)} plot hole(s)")

        # Glossary recommendations
        undefined_terms = glossary_report.get("undefined_terms", [])
        if undefined_terms:
            recommendations.append(f"Define {len(undefined_terms)} undefined term(s) in glossary")

        # General recommendations based on score
        overall_score = self._calculate_consistency_score(
            constitution_report, logical_analysis, glossary_report
        )

        if overall_score < 50:
            recommendations.append("Major revision needed: significant consistency issues found")
        elif overall_score < 70:
            recommendations.append("Moderate revision needed: address critical issues")
        elif overall_score < 85:
            recommendations.append("Minor revision needed: polish consistency")
        else:
            recommendations.append("Good consistency: minor tweaks only")

        return recommendations[:10]

    def _generate_summary(
        self, overall_score: float, critical_contradictions: list[dict[str, Any]]
    ) -> str:
        """Generate human-readable summary.

        Args:
            overall_score: Overall consistency score
            critical_contradictions: List of critical contradictions

        Returns:
            Summary text
        """
        if overall_score >= 85:
            rating = "Excellent"
        elif overall_score >= 70:
            rating = "Good"
        elif overall_score >= 50:
            rating = "Fair"
        else:
            rating = "Poor"

        critical_count = len(critical_contradictions)

        summary = (
            f"Consistency Review: {rating} ({overall_score}/100)\n"
            f"Critical Issues: {critical_count}\n"
        )

        if critical_count > 0:
            summary += "\nTop Critical Issues:\n"
            for i, issue in enumerate(critical_contradictions[:3], 1):
                summary += f"{i}. {issue['description'][:100]}...\n"

        return summary

    async def get_constitution_summary(self) -> str:
        """Get human-readable summary of all constitutional rules.

        Returns:
            Constitution summary text
        """
        return get_constitution_summary()

    async def validate_single_domain(
        self, domain: RuleDomain, data: Any
    ) -> list[tuple[str, bool, str]]:
        """Validate data against a single constitutional domain.

        Args:
            domain: Rule domain to validate against
            data: Data to validate

        Returns:
            List of (rule_id, is_valid, error_message) tuples
        """
        if self.constitution_validator is None:
            return []

        return self.constitution_validator.validate_domain(domain, data)

    async def batch_validate_chapters(
        self, chapters: list[dict[str, Any]], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform batch validation across multiple chapters.

        Args:
            chapters: List of chapter data (content, chapter_number, etc.)
            context: Shared context across chapters

        Returns:
            Cross-chapter validation report
        """
        reports = []
        for chapter in chapters:
            chapter_context = {**context, **chapter.get("context", {})}
            input_data = {
                "content": chapter.get("content", ""),
                "chapter_number": chapter.get("chapter_number", 0),
                "context": chapter_context,
                "validation_level": "comprehensive",
            }

            result = await self.execute(input_data)
            if result.success:
                reports.append(result.data)

        # Analyze cross-chapter consistency
        cross_chapter_issues = await self._analyze_cross_chapter_consistency(reports)

        return {
            "chapter_reports": reports,
            "cross_chapter_issues": cross_chapter_issues,
            "total_chapters": len(reports),
            "average_score": sum(r.get("overall_consistency_score", 0) for r in reports)
            / len(reports)
            if reports
            else 0,
        }

    async def _analyze_cross_chapter_consistency(
        self, chapter_reports: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Analyze consistency across multiple chapters.

        Args:
            chapter_reports: List of chapter review reports

        Returns:
            List of cross-chapter consistency issues
        """
        # This is a simplified implementation
        # In a full implementation, this would compare character development,
        # plot progression, timeline consistency, etc. across chapters

        issues = []

        if len(chapter_reports) < 2:
            return issues

        # Check for significant score drops
        scores = [r.get("overall_consistency_score", 0) for r in chapter_reports]
        for i in range(1, len(scores)):
            if scores[i] < scores[i - 1] - 20:  # Significant drop
                issues.append(
                    {
                        "type": "consistency_drop",
                        "description": f"Significant consistency drop from chapter {i} to {i + 1}",
                        "severity": "high",
                        "suggestion": "Review chapter transition for continuity issues",
                    }
                )

        return issues


# Factory function for easy instantiation
def create_review_agent(
    llm: Any,
    memory: Any | None = None,
    constitution_validator: Any | None = None,
    glossary: Any | None = None,
    name: str = "Review Agent",
) -> ReviewAgent:
    """Create a ReviewAgent instance.

    Args:
        llm: LLM instance
        memory: Memory system (optional)
        constitution_validator: Constitution validator (optional)
        glossary: Glossary manager (optional)
        name: Agent name

    Returns:
        ReviewAgent instance
    """
    return ReviewAgent(
        name=name,
        llm=llm,
        memory=memory,
        constitution_validator=constitution_validator,
        glossary=glossary,
    )
