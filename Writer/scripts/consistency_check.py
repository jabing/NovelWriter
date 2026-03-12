"""Consistency check script for novel writing system.

Runs comprehensive validation across all consistency systems:
- Constitutional rule validation
- Timeline temporal consistency
- Knowledge graph connectivity
- Review agent logical analysis
- Continuity validator checking

Uses HealthMonitor pattern for unified reporting.
"""

import asyncio
import logging
from typing import Any

from src.agents.review import ReviewAgent
from src.monitoring.health import HealthCheckResult, HealthMonitor, HealthStatus
from src.novel.constitution import ConstitutionValidator
from src.novel.knowledge_graph import KnowledgeGraph
from src.novel.timeline_manager import TemporalRelation, TimelineManager, TimeUnit
from src.novel.validators import ContinuityValidator

logger = logging.getLogger(__name__)


async def check_constitution() -> HealthCheckResult:
    """Check constitutional rule validation system."""
    try:
        validator = ConstitutionValidator()

        # Sample test data for each domain
        test_data = {
            "character": {
                "character_profile": {
                    "name": "Test Character",
                    "traits": ["brave", "honest"],
                    "appearance": {"eye_color": "blue"},
                    "background": "educated",
                },
                "current_content": "The brave hero faced the dragon.",
            },
            "plot": {
                "plot_elements": [{"id": "p1", "description": "Test plot"}],
                "current_content": "The hero embarked on a journey.",
            },
            "world": {
                "world_rules": {"magic_cost": "high"},
                "current_content": "The wizard cast a spell.",
            },
            "style": {
                "current_content": "The sun set over the mountains.",
                "pov": "third_person",
            },
            "consistency": {
                "current_content": "The hero traveled to the castle.",
                "timeline_events": [],
            },
            "ethical": {
                "current_content": "The hero helped the villagers.",
            },
        }

        results = validator.validate_all(test_data)

        # Check for critical violations
        critical_violations = validator.get_critical_violations(results)

        if critical_violations:
            return HealthCheckResult(
                name="constitution",
                status=HealthStatus.UNHEALTHY,
                message=f"Found {len(critical_violations)} critical constitutional violations",
                details={
                    "critical_violations": critical_violations,
                    "domain_results": {
                        domain: len(results.get(domain, [])) for domain in test_data
                    },
                },
            )

        # Calculate overall pass rate
        total_rules = 0
        passed_rules = 0
        for domain, domain_results in results.items():
            for rule_id, is_valid, error in domain_results:
                total_rules += 1
                if is_valid:
                    passed_rules += 1

        pass_rate = (passed_rules / total_rules * 100) if total_rules > 0 else 100

        if pass_rate < 80:
            return HealthCheckResult(
                name="constitution",
                status=HealthStatus.DEGRADED,
                message=f"Constitutional validation pass rate: {pass_rate:.1f}%",
                details={
                    "pass_rate": pass_rate,
                    "total_rules": total_rules,
                    "passed_rules": passed_rules,
                },
            )

        return HealthCheckResult(
            name="constitution",
            status=HealthStatus.HEALTHY,
            message=f"Constitutional validation healthy: {pass_rate:.1f}% pass rate",
            details={
                "pass_rate": pass_rate,
                "total_rules": total_rules,
                "passed_rules": passed_rules,
            },
        )

    except Exception as e:
        logger.exception("Constitution check failed")
        return HealthCheckResult(
            name="constitution",
            status=HealthStatus.UNHEALTHY,
            message=f"Constitution validation failed: {e}",
        )


async def check_timeline() -> HealthCheckResult:
    """Check timeline manager temporal consistency."""
    try:
        manager = TimelineManager()

        # Add sample events using manager.add_event (not TimelineEvent constructor)
        manager.add_event(
            event_id="event_001",
            timestamp="Day 1, Morning",
            description="Hero departs from village",
            start_order=1,
            end_order=2,
            time_unit=TimeUnit.DAY,
        )
        manager.add_event(
            event_id="event_002",
            timestamp="Day 2, Afternoon",
            description="Hero encounters dragon",
            start_order=3,
            end_order=4,
            time_unit=TimeUnit.DAY,
        )

        # Add temporal relation
        manager.add_relation(
            relation_id="rel_001",
            source_id="event_001",
            target_id="event_002",
            relation_type=TemporalRelation.BEFORE,
        )

        # Validate consistency
        issues = manager.validate_temporal_consistency()

        if issues:
            return HealthCheckResult(
                name="timeline",
                status=HealthStatus.UNHEALTHY,
                message=f"Timeline consistency issues: {len(issues)}",
                details={"issues": issues},
            )

        # Test query functionality
        events = manager.find_events_by_type("generic")
        if len(events) != 2:
            return HealthCheckResult(
                name="timeline",
                status=HealthStatus.DEGRADED,
                message=f"Expected 2 events, found {len(events)}",
                details={"events_found": len(events)},
            )

        return HealthCheckResult(
            name="timeline",
            status=HealthStatus.HEALTHY,
            message="Timeline manager healthy",
            details={
                "event_count": len(manager._events),
                "relation_count": len(manager._relations),
            },
        )

    except Exception as e:
        logger.exception("Timeline check failed")
        return HealthCheckResult(
            name="timeline",
            status=HealthStatus.UNHEALTHY,
            message=f"Timeline validation failed: {e}",
        )


async def check_knowledge_graph() -> HealthCheckResult:
    """Check knowledge graph connectivity and query capabilities."""
    try:
        # Create a temporary knowledge graph
        kg = KnowledgeGraph(storage_path=None)  # In-memory

        # Add sample nodes
        kg.add_node(
            node_id="char_001",
            node_type="character",
            properties={"name": "Hero", "traits": ["brave", "strong"]},
        )
        kg.add_node(
            node_id="loc_001",
            node_type="location",
            properties={"name": "Forest", "type": "wilderness"},
        )
        kg.add_node(
            node_id="item_001",
            node_type="object",
            properties={"name": "Sword", "material": "steel"},
        )

        # Add edges
        kg.add_edge(
            edge_id="edge_001",
            source_id="char_001",
            target_id="loc_001",
            relationship_type="located_at",
            properties={"since": "Day 1"},
        )
        kg.add_edge(
            edge_id="edge_002",
            source_id="char_001",
            target_id="item_001",
            relationship_type="owns",
            properties={"acquired": "Day 1"},
        )

        # Test queries
        character_nodes = kg.find_nodes_by_type(node_type="character")
        if len(character_nodes) != 1:
            return HealthCheckResult(
                name="knowledge_graph",
                status=HealthStatus.DEGRADED,
                message=f"Expected 1 character node, found {len(character_nodes)}",
                details={"character_nodes": len(character_nodes)},
            )

        # Test path finding
        paths = kg.find_shortest_path(source_id="char_001", target_id="item_001", max_depth=2)
        if paths is None:
            return HealthCheckResult(
                name="knowledge_graph",
                status=HealthStatus.DEGRADED,
                message="No path found between character and item",
                details={"node_count": len(kg._nodes), "edge_count": len(kg._edges)},
            )

        return HealthCheckResult(
            name="knowledge_graph",
            status=HealthStatus.HEALTHY,
            message="Knowledge graph healthy",
            details={
                "node_count": len(kg._nodes),
                "edge_count": len(kg._edges),
                "path_found": True,
            },
        )

    except Exception as e:
        logger.exception("Knowledge graph check failed")
        return HealthCheckResult(
            name="knowledge_graph",
            status=HealthStatus.UNHEALTHY,
            message=f"Knowledge graph validation failed: {e}",
        )


async def check_review_agent() -> HealthCheckResult:
    """Check review agent logical analysis capabilities."""
    try:
        # Try to import LLM - if not available, skip with degraded status
        try:
            from src.llm.deepseek import DeepSeekLLM

            llm = DeepSeekLLM()
            has_llm = True
        except Exception:
            llm = None
            has_llm = False

        if not has_llm:
            return HealthCheckResult(
                name="review_agent",
                status=HealthStatus.DEGRADED,
                message="Review agent check skipped (no LLM available)",
                details={"llm_available": False},
            )

        # Create review agent with mock LLM (using actual LLM for now)
        agent = ReviewAgent(name="Consistency Checker", llm=llm)

        # Test with simple content
        test_content = "The hero drew his sword and faced the dragon. The dragon breathed fire."
        test_context = {
            "characters": [{"name": "hero", "traits": ["brave"]}],
            "plot_elements": [{"id": "p1", "description": "hero vs dragon"}],
            "world_context": {"rules": {"dragons_breathe_fire": True}},
            "timeline_events": [],
            "objects": [{"name": "sword", "owner": "hero"}],
        }

        result = await agent.execute(
            {
                "content": test_content,
                "chapter_number": 1,
                "context": test_context,
                "validation_level": "basic",
            }
        )

        if not result.success:
            return HealthCheckResult(
                name="review_agent",
                status=HealthStatus.UNHEALTHY,
                message=f"Review agent execution failed: {result.errors}",
                details={"errors": result.errors},
            )

        # Check for critical contradictions
        critical_contradictions = result.data.get("critical_contradictions", [])
        consistency_score = result.data.get("overall_consistency_score", 0)

        if critical_contradictions:
            return HealthCheckResult(
                name="review_agent",
                status=HealthStatus.UNHEALTHY,
                message=f"Found {len(critical_contradictions)} critical contradictions",
                details={
                    "critical_contradictions": critical_contradictions,
                    "consistency_score": consistency_score,
                },
            )

        if consistency_score < 70:
            return HealthCheckResult(
                name="review_agent",
                status=HealthStatus.DEGRADED,
                message=f"Review agent consistency score low: {consistency_score}/100",
                details={"consistency_score": consistency_score},
            )

        return HealthCheckResult(
            name="review_agent",
            status=HealthStatus.HEALTHY,
            message=f"Review agent healthy, consistency score: {consistency_score}/100",
            details={
                "consistency_score": consistency_score,
                "has_constitution_report": "constitution_report" in result.data,
            },
        )

    except Exception as e:
        logger.exception("Review agent check failed")
        return HealthCheckResult(
            name="review_agent",
            status=HealthStatus.UNHEALTHY,
            message=f"Review agent validation failed: {e}",
        )


async def check_continuity_validator() -> HealthCheckResult:
    """Check continuity validator for chapter content."""
    try:
        validator = ContinuityValidator()

        # Sample story state
        from src.novel.continuity import CharacterState, StoryState

        story_state = StoryState(
            chapter=5,
            location="Forest",
            active_characters=["hero"],
            character_states={
                "hero": CharacterState(
                    name="hero",
                    status="alive",
                    location="Forest",
                    physical_form="human",
                    relationships={},
                ),
                "villain": CharacterState(
                    name="villain",
                    status="dead",
                    location="Castle",
                    physical_form="human",
                    relationships={},
                ),
            },
            plot_threads=[],
            key_events=[],
        )

        # Test chapter content
        chapter_content = (
            "The hero walked through the forest. He remembered the villain who died last chapter."
        )
        chapter_number = 6

        result = validator.validate_chapter(
            chapter_content=chapter_content,
            chapter_number=chapter_number,
            story_state=story_state,
            chapter_spec=None,
        )

        if not result.is_valid:
            return HealthCheckResult(
                name="continuity_validator",
                status=HealthStatus.UNHEALTHY,
                message=f"Continuity validation failed with {len(result.errors)} errors",
                details={
                    "errors": [e.message for e in result.errors],
                    "warnings": [w.message for w in result.warnings],
                },
            )

        if result.warnings:
            return HealthCheckResult(
                name="continuity_validator",
                status=HealthStatus.DEGRADED,
                message=f"Continuity validation has {len(result.warnings)} warnings",
                details={
                    "warnings": [w.message for w in result.warnings],
                    "error_count": len(result.errors),
                },
            )

        return HealthCheckResult(
            name="continuity_validator",
            status=HealthStatus.HEALTHY,
            message="Continuity validator healthy",
            details={
                "error_count": len(result.errors),
                "warning_count": len(result.warnings),
            },
        )

    except Exception as e:
        logger.exception("Continuity validator check failed")
        return HealthCheckResult(
            name="continuity_validator",
            status=HealthStatus.UNHEALTHY,
            message=f"Continuity validator failed: {e}",
        )


async def check_placeholders() -> HealthCheckResult:
    """Check for unresolved placeholder markers in text."""
    try:
        import re
        # Sample text with placeholder
        test_content = "The hero met [TODO: check character name] at the castle."
        # Pattern: [TODO: ...]
        pattern = r"\[TODO:[^\]]+\]"
        matches = re.findall(pattern, test_content)

        if matches:
            return HealthCheckResult(
                name="placeholders",
                status=HealthStatus.DEGRADED,
                message=f"Found {len(matches)} unresolved placeholder(s)",
                details={"placeholders": matches},
            )

        # Additional test: no placeholders in clean text
        clean_content = "The hero met Arthur at the castle."
        clean_matches = re.findall(pattern, clean_content)
        if clean_matches:
            return HealthCheckResult(
                name="placeholders",
                status=HealthStatus.UNHEALTHY,
                message="Placeholder detection incorrectly flagged clean text",
                details={"matches": clean_matches},
            )

        return HealthCheckResult(
            name="placeholders",
            status=HealthStatus.HEALTHY,
            message="Placeholder detection working correctly",
            details={"tested": True},
        )

    except Exception as e:
        logger.exception("Placeholder check failed")
        return HealthCheckResult(
            name="placeholders",
            status=HealthStatus.UNHEALTHY,
            message=f"Placeholder validation failed: {e}",
        )

async def run_all_checks() -> dict[str, Any]:
    """Run all consistency checks and return results."""
    monitor = HealthMonitor()

    # Register all checks
    monitor.register_check("constitution", check_constitution)
    monitor.register_check("timeline", check_timeline)
    monitor.register_check("knowledge_graph", check_knowledge_graph)
    monitor.register_check("review_agent", check_review_agent)
    monitor.register_check("continuity_validator", check_continuity_validator)
    monitor.register_check("placeholders", check_placeholders)

    results = await monitor.run_all_checks()

    return {
        "results": {name: result.to_dict() for name, result in results.items()},
        "summary": monitor.get_status_summary(),
        "overall_status": monitor.get_overall_status().value,
    }


async def main() -> None:
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)

    print("Running consistency checks for novel writing system...")
    print("=" * 60)

    try:
        results = await run_all_checks()

        # Print results
        for name, result_dict in results["results"].items():
            status = result_dict["status"]
            message = result_dict["message"]
            status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
            print(f"{status_icon} {name}: {message}")

        print("\n" + "=" * 60)
        print("SUMMARY:")
        summary = results["summary"]
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Checks Registered: {summary['checks_registered']}")
        print(f"Healthy: {summary['healthy_count']}")
        print(f"Degraded: {summary['degraded_count']}")
        print(f"Unhealthy: {summary['unhealthy_count']}")

        # Print any unhealthy or degraded details
        for name, result_dict in results["results"].items():
            status = result_dict["status"]
            if status in ["unhealthy", "degraded"]:
                print(f"\nDetails for {name}:")
                if result_dict.get("details"):
                    for key, value in result_dict["details"].items():
                        print(f"  {key}: {value}")

        # Exit with appropriate code
        if results["overall_status"] == "unhealthy":
            print("\n❌ System is UNHEALTHY - immediate attention required")
            exit(1)
        elif results["overall_status"] == "degraded":
            print("\n⚠️ System is DEGRADED - some checks failed")
            exit(0)  # Warning but not critical
        else:
            print("\n✅ All systems healthy")
            exit(0)

    except Exception as e:
        print(f"\n❌ Consistency check failed with error: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
