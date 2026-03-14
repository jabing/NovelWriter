"""200章性能基准测试."""

import time
import tracemalloc

import pytest

from src.novel_agent.novel.summary_manager import SummaryManager
from tests.integration.test_100_chapter_hierarchical import MockLLM


class TestPerformanceBenchmarks:
    """性能基准测试."""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_context_generation_performance(self, tmp_path):
        """测试不同章节的上下文生成时间.

        测量点: 第1, 50, 100, 150, 200章
        目标: 所有章节 < 1秒
        """
        storage = tmp_path / "perf_test"
        mock_llm = MockLLM(delay=0.001)
        manager = SummaryManager(
            storage, "perf", mock_llm, use_auto_fix=True, use_knowledge_graph=True
        )

        # 先生成到200章
        for i in range(1, 201):
            await manager.process_chapter_with_autofix(
                i, f"Chapter {i}", f"Content for chapter {i}..."
            )

        # 测量关键章节的上下文生成时间
        chapters_to_test = [1, 50, 100, 150, 200]
        results = {}

        for ch in chapters_to_test:
            start = time.time()
            context = manager.hierarchical_state.get_context_for_chapter(ch + 1)
            elapsed = time.time() - start
            results[ch] = {
                "time": elapsed,
                "tokens": len(context) // 4,  # 粗略估算
                "length": len(context),
            }

            # 断言: 必须 < 1秒
            assert elapsed < 1.0, f"Chapter {ch} context generation too slow: {elapsed:.2f}s"

        # 保存结果
        print("\nPerformance Results:")
        for ch, data in results.items():
            print(f"  Chapter {ch}: {data['time'] * 1000:.1f}ms, ~{data['tokens']} tokens")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_usage_by_chapter(self, tmp_path):
        """测试不同章节的内存使用.

        目标: 200章时 < 20MB
        """
        storage = tmp_path / "memory_test"
        mock_llm = MockLLM(delay=0.001)
        manager = SummaryManager(storage, "mem", mock_llm)

        tracemalloc.start()

        memory_snapshots = {}
        for i in range(1, 201):
            await manager.process_chapter_with_autofix(i, f"Ch{i}", "Content...")

            if i in [1, 50, 100, 150, 200]:
                current, peak = tracemalloc.get_traced_memory()
                memory_snapshots[i] = current / 1024 / 1024  # MB

        tracemalloc.stop()

        # 断言: 200章必须 < 20MB
        final_memory = memory_snapshots[200]
        assert final_memory < 20, f"Memory too high at chapter 200: {final_memory:.1f}MB"

        print("\nMemory Usage:")
        for ch, mem in memory_snapshots.items():
            print(f"  Chapter {ch}: {mem:.1f}MB")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_knowledge_graph_growth(self, tmp_path):
        """测试知识图谱增长趋势."""
        storage = tmp_path / "kg_growth"
        mock_llm = MockLLM(delay=0.001)
        manager = SummaryManager(storage, "kg", mock_llm, use_knowledge_graph=True)

        kg_sizes = {}

        for i in range(1, 101):  # 测试100章
            content = f"第{i}章: 张三和李四在京城讨论大事。"
            await manager.process_chapter_with_autofix(i, f"第{i}章", content)

            if i in [1, 10, 25, 50, 75, 100]:
                nodes = len(manager.knowledge_graph.get_all_nodes())
                edges = len(manager.knowledge_graph._edges)
                kg_sizes[i] = {"nodes": nodes, "edges": edges}

        print("\nKnowledge Graph Growth:")
        for ch, data in kg_sizes.items():
            print(f"  Chapter {ch}: {data['nodes']} nodes, {data['edges']} edges")
