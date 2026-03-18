"""Continuity verification tests for fact injection system.

Tests verify:
- Critical facts (IMMUTABLE, SECRET) are retained across chapters
- Early facts remain visible in later chapters
- Dynamic fact count integration works correctly
"""

from pathlib import Path

import pytest

from src.novel_agent.novel.fact_database import (
    Fact,
    FactType,
    ProtectedFactCategory,
)
from src.novel_agent.novel.fact_injector import (
    RelevanceScorer,
    RelevantFactInjector,
    calculate_max_facts,
)


class TestCriticalFactsRetention:
    """Test that critical facts (IMMUTABLE, SECRET) are always retained."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def injector(self, temp_storage: Path) -> RelevantFactInjector:
        """Create injector with low max_facts to test filtering pressure."""
        return RelevantFactInjector(
            temp_storage,
            "test_critical_facts",
            max_facts=10,  # Low limit to force filtering
        )

    @pytest.fixture
    def populated_injector(self, injector: RelevantFactInjector) -> RelevantFactInjector:
        """Create injector populated with various fact types."""
        # Add regular facts that would normally fill up the limit
        for i in range(20):
            _ = injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"常规事件 {i}: 某个普通的事情发生了",
                chapter_origin=1,
                importance=0.5,
                entities=["配角甲", "配角乙"],
            )

        # Add critical IMMUTABLE facts
        injector.fact_database.facts["imm-death"] = Fact(
            id="imm-death",
            fact_type=FactType.EVENT,
            content="主角的父亲在第5章死亡",
            chapter_origin=5,
            importance=0.95,
            entities=["主角", "父亲"],
            protected_category=ProtectedFactCategory.IMMUTABLE,
        )

        injector.fact_database.facts["imm-transform"] = Fact(
            id="imm-transform",
            fact_type=FactType.CHARACTER,
            content="反派在第三章永久失去了左臂",
            chapter_origin=3,
            importance=0.9,
            entities=["反派"],
            protected_category=ProtectedFactCategory.IMMUTABLE,
        )

        # Add critical SECRET facts
        injector.fact_database.facts["sec-identity"] = Fact(
            id="sec-identity",
            fact_type=FactType.CHARACTER,
            content="女主角的真实身份是公主",
            chapter_origin=3,
            importance=0.95,
            entities=["女主角"],
            protected_category=ProtectedFactCategory.SECRET,
        )

        injector.fact_database.facts["sec-conspiracy"] = Fact(
            id="sec-conspiracy",
            fact_type=FactType.EVENT,
            content="国王实际上被大臣控制",
            chapter_origin=7,
            importance=0.9,
            entities=["国王", "大臣"],
            protected_category=ProtectedFactCategory.SECRET,
        )

        # Add PROMISE facts
        injector.fact_database.facts["promise-oath"] = Fact(
            id="promise-oath",
            fact_type=FactType.EVENT,
            content="主角承诺在满月之前找到治愈之法",
            chapter_origin=10,
            importance=0.85,
            entities=["主角"],
            protected_category=ProtectedFactCategory.PROMISE,
        )

        injector.fact_database.save()
        return injector

    def test_immutable_facts_retained_in_results(
        self, populated_injector: RelevantFactInjector
    ) -> None:
        """Test that IMMUTABLE facts appear in get_relevant_facts results."""
        facts = populated_injector.get_relevant_facts(current_chapter=25)

        fact_ids = [f.id for f, _ in facts]

        # IMMUTABLE facts must be present
        assert "imm-death" in fact_ids, "IMMUTABLE fact (father's death) should be retained"
        assert "imm-transform" in fact_ids, "IMMUTABLE fact (villain's lost arm) should be retained"

    def test_secret_facts_retained_in_results(
        self, populated_injector: RelevantFactInjector
    ) -> None:
        """Test that SECRET facts appear in get_relevant_facts results."""
        facts = populated_injector.get_relevant_facts(current_chapter=25)

        fact_ids = [f.id for f, _ in facts]

        # SECRET facts must be present
        assert "sec-identity" in fact_ids, "SECRET fact (heroine's identity) should be retained"
        assert "sec-conspiracy" in fact_ids, "SECRET fact (king controlled) should be retained"

    def test_promise_facts_retained_in_results(
        self, populated_injector: RelevantFactInjector
    ) -> None:
        """Test that PROMISE facts appear in get_relevant_facts results."""
        facts = populated_injector.get_relevant_facts(current_chapter=25)

        fact_ids = [f.id for f, _ in facts]

        # PROMISE facts must be present
        assert "promise-oath" in fact_ids, "PROMISE fact (protagonist's oath) should be retained"

    def test_all_protected_categories_have_reserved_slots(
        self, populated_injector: RelevantFactInjector
    ) -> None:
        """Test that protected facts fill reserved slots before regular facts."""
        facts = populated_injector.get_relevant_facts(current_chapter=25)

        protected_facts = [f for f, _ in facts if f.protected_category is not None]

        # Protected facts should be included even with low max_facts limit
        assert len(protected_facts) >= 5, "Should have at least 5 protected facts"

        # Total should not exceed max_facts
        assert len(facts) <= populated_injector.max_facts

    def test_protected_facts_survive_high_chapter_numbers(
        self, populated_injector: RelevantFactInjector
    ) -> None:
        """Test that protected facts are retained even at very late chapters."""
        # Chapter 100 - long after facts were introduced
        facts = populated_injector.get_relevant_facts(current_chapter=100)

        fact_ids = [f.id for f, _ in facts]

        # Even at chapter 100, critical facts should still be present
        assert "imm-death" in fact_ids, "IMMUTABLE fact should survive to chapter 100"
        assert "sec-identity" in fact_ids, "SECRET fact should survive to chapter 100"

    def test_protected_facts_not_filtered_by_score_threshold(self, temp_storage: Path) -> None:
        """Test that protected facts bypass score filtering."""
        # Create injector with high min_score to filter out most facts
        injector = RelevantFactInjector(
            temp_storage,
            "test_score_threshold",
            max_facts=10,
            min_score=0.8,  # High threshold
        )

        # Add regular fact with low importance
        injector.add_fact(
            fact_type=FactType.EVENT,
            content="普通事件",
            chapter_origin=1,
            importance=0.3,  # Below threshold
        )

        # Add IMMUTABLE fact with low importance
        injector.fact_database.facts["imm-low-importance"] = Fact(
            id="imm-low-importance",
            fact_type=FactType.EVENT,
            content="某个不可变但重要性低的事实",
            chapter_origin=1,
            importance=0.3,
            protected_category=ProtectedFactCategory.IMMUTABLE,
        )
        injector.fact_database.save()

        facts = injector.get_relevant_facts(current_chapter=10)

        fact_ids = [f.id for f, _ in facts]

        # Regular low-importance fact should be filtered
        # Protected fact should be retained despite low importance
        assert "imm-low-importance" in fact_ids, "IMMUTABLE fact should bypass score threshold"


class TestEarlyFactsVisibility:
    """Test that early chapter facts remain visible in later chapters."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def injector(self, temp_storage: Path) -> RelevantFactInjector:
        """Create injector for early facts visibility tests."""
        return RelevantFactInjector(
            temp_storage,
            "test_early_facts",
            max_facts=30,
        )

    @pytest.fixture
    def novel_with_early_facts(self, injector: RelevantFactInjector) -> RelevantFactInjector:
        """Create injector with facts spread across early and late chapters."""
        # Chapter 1 - Very early facts (key plot points)
        injector.add_fact(
            fact_type=FactType.ITEM,
            content="主角获得了神秘玉佩",
            chapter_origin=1,
            importance=0.9,
            entities=["主角", "玉佩"],
        )
        injector.add_fact(
            fact_type=FactType.CHARACTER,
            content="主角的父母在他幼年时失踪",
            chapter_origin=1,
            importance=0.85,
            entities=["主角", "父母"],
        )
        injector.add_fact(
            fact_type=FactType.LOCATION,
            content="故事开始于青云村",
            chapter_origin=1,
            importance=0.7,
            entities=["青云村"],
        )

        # Chapter 5 - Early story facts
        injector.add_fact(
            fact_type=FactType.EVENT,
            content="主角拜入天剑宗门下",
            chapter_origin=5,
            importance=0.8,
            entities=["主角", "天剑宗"],
        )
        injector.add_fact(
            fact_type=FactType.RELATIONSHIP,
            content="主角与师姐建立了深厚友谊",
            chapter_origin=5,
            importance=0.75,
            entities=["主角", "师姐"],
        )

        # Chapter 10 - Mid-story facts
        injector.add_fact(
            fact_type=FactType.EVENT,
            content="主角在宗门大比中获得第一名",
            chapter_origin=10,
            importance=0.8,
            entities=["主角", "宗门"],
        )

        # Chapter 15 - Later facts
        injector.add_fact(
            fact_type=FactType.EVENT,
            content="主角发现了宗门的秘密",
            chapter_origin=15,
            importance=0.85,
            entities=["主角", "宗门"],
        )

        # Chapter 20 - Late facts
        injector.add_fact(
            fact_type=FactType.EVENT,
            content="主角离开宗门开始历练",
            chapter_origin=20,
            importance=0.75,
            entities=["主角"],
        )

        # Add filler facts to simulate a full novel
        for i in range(50):
            chapter = (i % 20) + 1
            injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"填充事件 {i}: 某个普通事情",
                chapter_origin=chapter,
                importance=0.3 + (i % 5) * 0.1,
                entities=[f"角色{i % 10}"],
            )

        return injector

    def test_chapter_1_facts_visible_at_chapter_25(
        self, novel_with_early_facts: RelevantFactInjector
    ) -> None:
        """Test that facts from chapter 1 are still visible when generating chapter 25."""
        facts = novel_with_early_facts.get_relevant_facts(current_chapter=25)

        fact_contents = [f.content for f, _ in facts]

        # Chapter 1 facts should still be visible
        assert any("神秘玉佩" in c for c in fact_contents), (
            "Chapter 1 fact (jade pendant) should be visible at chapter 25"
        )
        assert any("父母" in c and "失踪" in c for c in fact_contents), (
            "Chapter 1 fact (parents missing) should be visible at chapter 25"
        )

    def test_early_high_importance_facts_prioritized(
        self, novel_with_early_facts: RelevantFactInjector
    ) -> None:
        """Test that early high-importance facts are prioritized over later low-importance facts."""
        facts = novel_with_early_facts.get_relevant_facts(current_chapter=25)

        # Get early facts (chapter <= 5) and their scores
        early_facts = [(f, s) for f, s in facts if f.chapter_origin <= 5]

        # There should be some early facts included
        assert len(early_facts) > 0, "Should include early chapter facts"

        # Check that high-importance early facts are included
        early_contents = [f.content for f, _ in early_facts]
        assert any("玉佩" in c or "天剑宗" in c for c in early_contents), (
            "High-importance early facts should be included"
        )

    def test_facts_from_multiple_chapters_visible(
        self, novel_with_early_facts: RelevantFactInjector
    ) -> None:
        """Test that facts from multiple chapters are all visible."""
        facts = novel_with_early_facts.get_relevant_facts(current_chapter=25)

        chapter_origins = set(f.chapter_origin for f, _ in facts)

        # Should have facts from multiple chapters
        assert len(chapter_origins) >= 3, "Should have facts from at least 3 different chapters"

    def test_early_facts_with_high_importance_outscore_late_low_importance(
        self, novel_with_early_facts: RelevantFactInjector
    ) -> None:
        """Test scoring algorithm favors high-importance early facts over low-importance late facts."""
        facts = novel_with_early_facts.get_relevant_facts(current_chapter=25)

        # Get the jade pendant fact (high importance, early chapter)
        jade_fact = None
        for f, s in facts:
            if "玉佩" in f.content:
                jade_fact = (f, s)
                break

        assert jade_fact is not None, "Jade pendant fact should be in results"

        # Its importance should be preserved
        assert jade_fact[0].importance >= 0.8, "High importance fact should retain importance"

    def test_visible_facts_count_respects_max(
        self, novel_with_early_facts: RelevantFactInjector
    ) -> None:
        """Test that returned facts don't exceed max_facts."""
        facts = novel_with_early_facts.get_relevant_facts(current_chapter=25)

        assert len(facts) <= novel_with_early_facts.max_facts, (
            f"Returned {len(facts)} facts but max is {novel_with_early_facts.max_facts}"
        )

    def test_early_protected_facts_always_visible(self, temp_storage: Path) -> None:
        """Test that early protected facts are always visible regardless of chapter distance."""
        injector = RelevantFactInjector(
            temp_storage,
            "test_early_protected",
            max_facts=20,
        )

        # Add early IMMUTABLE fact
        injector.fact_database.facts["early-imm"] = Fact(
            id="early-imm",
            fact_type=FactType.EVENT,
            content="第一章发生的不可改变的事件",
            chapter_origin=1,
            importance=0.95,
            protected_category=ProtectedFactCategory.IMMUTABLE,
        )

        # Add many regular facts from later chapters
        for i in range(30):
            injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"后期事件 {i}",
                chapter_origin=20 + i,
                importance=0.6,
            )
        injector.fact_database.save()

        # Query at chapter 50
        facts = injector.get_relevant_facts(current_chapter=50)

        fact_ids = [f.id for f, _ in facts]
        assert "early-imm" in fact_ids, "Early IMMUTABLE fact should be visible at chapter 50"


class TestDynamicFactCountIntegration:
    """Test dynamic fact count calculation integration."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    def test_30_chapters_returns_45_facts_max(self, temp_storage: Path) -> None:
        """Test that 30 chapters results in max_facts of 45."""
        # Verify the calculation function
        assert calculate_max_facts(30) == 45

        # Create injector with chapter_count
        injector = RelevantFactInjector(
            temp_storage,
            "test_30_chapters",
            chapter_count=30,
        )

        assert injector.max_facts == 45, f"Expected max_facts=45, got {injector.max_facts}"

    def test_10_chapters_returns_30_facts_min(self, temp_storage: Path) -> None:
        """Test that 10 chapters results in minimum max_facts of 30."""
        # Verify the calculation function
        assert calculate_max_facts(10) == 30

        # Create injector with chapter_count
        injector = RelevantFactInjector(
            temp_storage,
            "test_10_chapters",
            chapter_count=10,
        )

        assert injector.max_facts == 30, f"Expected max_facts=30, got {injector.max_facts}"

    def test_100_chapters_returns_50_facts_max(self, temp_storage: Path) -> None:
        """Test that 100 chapters results in max_facts capped at 50."""
        # Verify the calculation function
        assert calculate_max_facts(100) == 50

        # Create injector with chapter_count
        injector = RelevantFactInjector(
            temp_storage,
            "test_100_chapters",
            chapter_count=100,
        )

        assert injector.max_facts == 50, f"Expected max_facts=50, got {injector.max_facts}"

    def test_explicit_max_facts_overrides_chapter_count(self, temp_storage: Path) -> None:
        """Test that explicit max_facts takes priority over chapter_count calculation."""
        injector = RelevantFactInjector(
            temp_storage,
            "test_explicit_max",
            max_facts=35,  # Explicit value
            chapter_count=30,  # Would calculate to 45
        )

        # Explicit max_facts should override calculation
        assert injector.max_facts == 35

    def test_default_max_facts_without_chapter_count(self, temp_storage: Path) -> None:
        """Test default max_facts when neither parameter is provided."""
        injector = RelevantFactInjector(
            temp_storage,
            "test_default_max",
        )

        # Default should be 20
        assert injector.max_facts == 20

    def test_get_relevant_facts_respects_dynamic_limit(self, temp_storage: Path) -> None:
        """Test that get_relevant_facts respects the dynamically calculated limit."""
        injector = RelevantFactInjector(
            temp_storage,
            "test_dynamic_limit",
            chapter_count=30,  # max_facts = 45
        )

        # Add many facts
        for i in range(100):
            injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"事件 {i}",
                chapter_origin=1,
                importance=0.5 + (i % 10) * 0.05,
            )

        facts = injector.get_relevant_facts(current_chapter=10)

        # Should respect the 45 limit
        assert len(facts) <= 45, f"Expected at most 45 facts, got {len(facts)}"

    def test_protected_slots_available_with_dynamic_limit(self, temp_storage: Path) -> None:
        """Test that protected slots are available even with dynamic fact limits."""
        # Small novel: 15 chapters -> max_facts = 30
        injector = RelevantFactInjector(
            temp_storage,
            "test_protected_slots",
            chapter_count=15,
        )

        assert injector.max_facts == 30

        # Protected slots should still be 14 total
        total_protected = sum(injector.PROTECTED_SLOTS.values())
        assert total_protected == 14

        # Protected slots should not exceed max_facts
        assert total_protected < injector.max_facts


class TestScoringFavorsProtectedCategories:
    """Test that the scoring algorithm favors protected categories."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    @pytest.fixture
    def scorer(self) -> RelevanceScorer:
        """Create a RelevanceScorer instance."""
        return RelevanceScorer()

    def test_protected_facts_have_dedicated_slots(self, temp_storage: Path) -> None:
        """Test that protected facts fill dedicated slots separate from regular scoring."""
        injector = RelevantFactInjector(
            temp_storage,
            "test_protected_scoring",
            max_facts=20,
        )

        # Add protected facts with lower importance
        for i in range(5):
            injector.fact_database.facts[f"imm-{i}"] = Fact(
                id=f"imm-{i}",
                fact_type=FactType.EVENT,
                content=f"不可变事实 {i}",
                chapter_origin=1,
                importance=0.4,  # Lower importance
                protected_category=ProtectedFactCategory.IMMUTABLE,
            )

        # Add regular facts with higher importance
        for i in range(30):
            injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"高重要性常规事实 {i}",
                chapter_origin=1,
                importance=0.9,  # Higher importance
            )
        injector.fact_database.save()

        facts = injector.get_relevant_facts(current_chapter=10)

        # Protected facts should be included despite lower importance
        protected_count = sum(1 for f, _ in facts if f.protected_category is not None)
        assert protected_count >= 3, "Should include protected facts in dedicated slots"

    def test_protected_fact_appearance_guaranteed(self, temp_storage: Path) -> None:
        """Test that protected facts appear regardless of recency or other factors."""
        injector = RelevantFactInjector(
            temp_storage,
            "test_appearance_guaranteed",
            max_facts=15,
        )

        # Old protected fact from chapter 1
        injector.fact_database.facts["old-secret"] = Fact(
            id="old-secret",
            fact_type=FactType.CHARACTER,
            content="古老秘密",
            chapter_origin=1,
            importance=0.5,
            protected_category=ProtectedFactCategory.SECRET,
        )

        # Many recent high-importance regular facts
        for i in range(40):
            injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"近期事件 {i}",
                chapter_origin=25,
                importance=0.9,
            )
        injector.fact_database.save()

        # Query at chapter 30
        facts = injector.get_relevant_facts(current_chapter=30)

        fact_ids = [f.id for f, _ in facts]

        # Old protected fact should appear despite age and competition
        assert "old-secret" in fact_ids, "Old SECRET fact should appear due to protected status"

    def test_multiple_protected_categories_all_represented(self, temp_storage: Path) -> None:
        """Test that all protected categories can have representation."""
        injector = RelevantFactInjector(
            temp_storage,
            "test_all_categories",
            max_facts=20,
        )

        # Add one fact for each protected category
        injector.fact_database.facts["imm-1"] = Fact(
            id="imm-1",
            fact_type=FactType.EVENT,
            content="不可变事件",
            chapter_origin=1,
            importance=0.8,
            protected_category=ProtectedFactCategory.IMMUTABLE,
        )
        injector.fact_database.facts["sec-1"] = Fact(
            id="sec-1",
            fact_type=FactType.CHARACTER,
            content="秘密身份",
            chapter_origin=1,
            importance=0.8,
            protected_category=ProtectedFactCategory.SECRET,
        )
        injector.fact_database.facts["prom-1"] = Fact(
            id="prom-1",
            fact_type=FactType.EVENT,
            content="重要承诺",
            chapter_origin=1,
            importance=0.8,
            protected_category=ProtectedFactCategory.PROMISE,
        )
        injector.fact_database.facts["world-1"] = Fact(
            id="world-1",
            fact_type=FactType.WORLD_RULE,
            content="世界规则",
            chapter_origin=1,
            importance=0.8,
            protected_category=ProtectedFactCategory.WORLD_RULE,
        )
        injector.fact_database.facts["fore-1"] = Fact(
            id="fore-1",
            fact_type=FactType.EVENT,
            content="伏笔事件",
            chapter_origin=1,
            importance=0.8,
            protected_category=ProtectedFactCategory.FORESHADOW,
        )
        injector.fact_database.save()

        facts = injector.get_relevant_facts(current_chapter=10)

        # Check representation of protected categories
        categories_found = set()
        for f, _ in facts:
            if f.protected_category:
                categories_found.add(f.protected_category)

        # Should have at least some protected categories represented
        assert len(categories_found) >= 3, (
            f"Expected at least 3 protected categories, found {len(categories_found)}: {categories_found}"
        )


class TestRealisticNovelScenario:
    """Test continuity with realistic novel data."""

    @pytest.fixture
    def temp_storage(self, tmp_path: Path) -> Path:
        """Create temporary storage directory."""
        return tmp_path / "novels"

    def test_xianxia_novel_continuity(self, temp_storage: Path) -> None:
        """Test continuity for a realistic Xianxia novel scenario."""
        injector = RelevantFactInjector(
            temp_storage,
            "xianxia_novel",
            chapter_count=30,  # 30 chapters -> 45 facts
        )

        # Core plot facts (should always appear)
        core_facts = [
            # IMMUTABLE
            Fact(
                id="imm-master-death",
                fact_type=FactType.EVENT,
                content="师父在第三章为保护主角而死",
                chapter_origin=3,
                importance=0.98,
                entities=["师父", "主角"],
                protected_category=ProtectedFactCategory.IMMUTABLE,
            ),
            # SECRET
            Fact(
                id="sec-bloodline",
                fact_type=FactType.CHARACTER,
                content="主角拥有上古神族血脉",
                chapter_origin=1,
                importance=0.95,
                entities=["主角"],
                protected_category=ProtectedFactCategory.SECRET,
            ),
            # PROMISE
            Fact(
                id="prom-revenge",
                fact_type=FactType.EVENT,
                content="主角发誓要为师父报仇",
                chapter_origin=4,
                importance=0.9,
                entities=["主角", "师父"],
                protected_category=ProtectedFactCategory.PROMISE,
            ),
            # WORLD_RULE
            Fact(
                id="world-cultivation",
                fact_type=FactType.WORLD_RULE,
                content="修炼需要天地灵气，境界分为炼气、筑基、金丹等",
                chapter_origin=1,
                importance=0.85,
                protected_category=ProtectedFactCategory.WORLD_RULE,
            ),
            # FORESHADOW
            Fact(
                id="fore-prophecy",
                fact_type=FactType.EVENT,
                content="预言说天选之人将在百年后觉醒",
                chapter_origin=5,
                importance=0.8,
                protected_category=ProtectedFactCategory.FORESHADOW,
            ),
        ]

        # Add core facts
        for fact in core_facts:
            injector.fact_database.facts[fact.id] = fact

        # Add supporting facts from various chapters
        supporting_facts = [
            (FactType.CHARACTER, "主角名叫李云，来自青云村", 1, 0.7, ["李云", "青云村"]),
            (FactType.LOCATION, "青云宗是主角所在的门派", 2, 0.6, ["青云宗"]),
            (FactType.RELATIONSHIP, "主角与小师妹关系密切", 3, 0.65, ["主角", "小师妹"]),
            (FactType.ITEM, "主角获得了神秘玉佩", 1, 0.75, ["主角", "玉佩"]),
            (FactType.EVENT, "主角在宗门大比中获胜", 8, 0.7, ["主角", "宗门"]),
            (FactType.EVENT, "主角发现宗门有内奸", 12, 0.75, ["主角", "宗门"]),
            (FactType.CHARACTER, "内奸是主角的师兄", 15, 0.8, ["内奸", "师兄"]),
            (FactType.EVENT, "主角突破到筑基期", 18, 0.75, ["主角"]),
            (FactType.EVENT, "主角离开宗门历练", 22, 0.7, ["主角"]),
            (FactType.LOCATION, "主角来到神秘禁地", 25, 0.65, ["主角", "禁地"]),
        ]

        for i, (ftype, content, chapter, importance, entities) in enumerate(supporting_facts):
            injector.add_fact(
                fact_type=ftype,
                content=content,
                chapter_origin=chapter,
                importance=importance,
                entities=entities,
            )

        # Add filler facts
        for i in range(80):
            chapter = (i % 25) + 1
            injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"普通事件 {i}",
                chapter_origin=chapter,
                importance=0.3 + (i % 5) * 0.05,
            )

        injector.fact_database.save()

        # Query at chapter 30
        facts = injector.get_relevant_facts(current_chapter=30)

        fact_ids = [f.id for f, _ in facts]
        fact_contents = [f.content for f, _ in facts]

        # Core protected facts must be present
        assert "imm-master-death" in fact_ids, "Master's death (IMMUTABLE) must be retained"
        assert "sec-bloodline" in fact_ids, "Bloodline secret (SECRET) must be retained"
        assert "prom-revenge" in fact_ids, "Revenge promise (PROMISE) must be retained"
        assert "world-cultivation" in fact_ids, "World rule must be retained"
        assert "fore-prophecy" in fact_ids, "Prophecy foreshadowing must be retained"

        # Early chapter 1 fact should be visible
        assert any("玉佩" in c for c in fact_contents), (
            "Jade pendant from chapter 1 should be visible"
        )

        # Total should not exceed max_facts
        assert len(facts) <= injector.max_facts, (
            f"Got {len(facts)} facts, max is {injector.max_facts}"
        )

    def test_death_fact_never_disappears(self, temp_storage: Path) -> None:
        """Test that death facts (IMMUTABLE) never disappear across all chapters."""
        injector = RelevantFactInjector(
            temp_storage,
            "death_fact_test",
            chapter_count=50,
        )

        # Add a death fact
        injector.fact_database.facts["death-key"] = Fact(
            id="death-key",
            fact_type=FactType.EVENT,
            content="关键角色王明在第五章死亡",
            chapter_origin=5,
            importance=0.95,
            entities=["王明"],
            protected_category=ProtectedFactCategory.IMMUTABLE,
        )

        # Add many competing facts
        for i in range(100):
            injector.add_fact(
                fact_type=FactType.EVENT,
                content=f"竞争事件 {i}",
                chapter_origin=10 + (i % 40),
                importance=0.7,
            )
        injector.fact_database.save()

        # Check at various chapter numbers
        for chapter in [6, 10, 20, 30, 40, 50]:
            facts = injector.get_relevant_facts(current_chapter=chapter)
            fact_ids = [f.id for f, _ in facts]
            assert "death-key" in fact_ids, f"Death fact should be present at chapter {chapter}"

    def test_secret_until_revealed(self, temp_storage: Path) -> None:
        """Test that SECRET facts are retained until they would logically be revealed."""
        injector = RelevantFactInjector(
            temp_storage,
            "secret_until_revealed",
            chapter_count=30,
        )

        # Add a secret that will be revealed
        injector.fact_database.facts["secret-identity"] = Fact(
            id="secret-identity",
            fact_type=FactType.CHARACTER,
            content="神秘商人实际上是主角失踪的父亲",
            chapter_origin=3,
            importance=0.9,
            entities=["神秘商人", "主角", "父亲"],
            protected_category=ProtectedFactCategory.SECRET,
        )
        injector.fact_database.save()

        # Secret should be retained at various chapters
        for chapter in [5, 10, 15, 20, 25, 30]:
            facts = injector.get_relevant_facts(current_chapter=chapter)
            fact_ids = [f.id for f, _ in facts]
            assert "secret-identity" in fact_ids, (
                f"Secret fact should be retained at chapter {chapter}"
            )
