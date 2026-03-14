"""Vector store optimization benchmarking tests.

Tests measure query latency and throughput to verify optimization targets:
- Query latency: < 15ms (optimized from < 20ms)
- Batch insert throughput: > 1000 vectors/s
- Delete performance: < 100ms/100 vectors
"""

import sys
import time
import tempfile

import pytest

# Skip tests if chromadb is not installed or incompatible with Python version
# ChromaDB depends on pydantic.v1 which is incompatible with Python 3.14+
chromadb_error = None
if sys.version_info >= (3, 14):
    try:
        import chromadb  # noqa: F401
    except Exception as e:
        chromadb_error = e
        pytest.skip(
            f"ChromaDB not compatible with Python {sys.version_info.major}.{sys.version_info.minor}: {e}\n"
            f"NOTE: Run tests with Python 3.10-3.13 for ChromaDB support",
            allow_module_level=True
        )
else:
    try:
        pytest.importorskip("chromadb", reason="chromadb not installed, skipping optimization tests")
    except Exception as e:
        chromadb_error = e
        pytest.skip(f"ChromaDB not installed: {e}", allow_module_level=True)

from src.novel_agent.db.chroma_client import ChromaVectorStore


class TestVectorStoreOptimization:
    """Vector store optimization benchmarking tests.

    All tests use temporary collections to avoid conflicts with production data.
    Tests verify optimized performance targets.
    """

    @pytest.fixture
    async def chroma_store(self):
        """Create a temporary ChromaVectorStore for testing.

        Uses a temporary directory to avoid conflicts with production data.
        Collection is cleaned up after test completion.
        """
        # Create temporary directory for test data
        temp_dir = tempfile.mkdtemp(prefix="chroma_opt_test_")
        test_collection = f"test_optimization_{id(self)}"

        # Create store
        store = ChromaVectorStore(
            persist_path=temp_dir,
            collection_name=test_collection,
        )

        yield store

        # Cleanup: Delete the collection
        try:
            store.client.delete_collection(name=test_collection)
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_query_latency_optimized(self, chroma_store: ChromaVectorStore) -> None:
        """Test that optimized query latency is < 15ms.

        Measures the time for a single similarity query after data is inserted.
        This test includes embedding generation time.

        Performance target: < 15ms per query (optimized from < 20ms).
        """
        # Insert test data first
        _ = await chroma_store.upsert_vectors(
            ids=["opt_test_1", "opt_test_2", "opt_test_3"],
            texts=[
                "Alice is a brilliant scientist working at SETI",
                "Bob is Alice's colleague who studies astrophysics",
                "The anomaly appeared suddenly in the data",
            ],
            metadatas=[
                {"chapter": 1, "character": "Alice"},
                {"chapter": 1, "character": "Bob"},
                {"chapter": 1, "type": "event"},
            ],
        )

        # Warm up the model cache with a preliminary query
        _ = await chroma_store.query_similar("warmup query", n_results=1)

        # Measure query latency
        start = time.time()
        results = await chroma_store.query_similar("scientist working at SETI", n_results=10)
        latency_ms = (time.time() - start) * 1000

        # Assertions
        assert len(results) > 0, "Query should return at least one result"
        assert latency_ms < 15, f"Query latency {latency_ms:.2f}ms exceeds threshold 15ms"

    @pytest.mark.asyncio
    async def test_batch_insert_throughput(self, chroma_store: ChromaVectorStore) -> None:
        """Test that batch insert throughput is > 1000 vectors/s.

        Measures the time to insert 1000 vectors in a single batch operation.
        This includes embedding generation time.

        Performance target: > 1000 vectors/s.
        """
        # Prepare test data
        batch_size = 1000
        ids = [f"opt_batch_{i}" for i in range(batch_size)]
        texts = [f"Optimized test document number {i} with sample text for performance testing" for i in range(batch_size)]
        metadatas = [{"batch": i // 100, "test_type": "optimization"} for i in range(batch_size)]

        # Measure insert throughput
        start = time.time()
        _ = await chroma_store.upsert_vectors(ids=ids, texts=texts, metadatas=metadatas)
        duration = time.time() - start

        # Calculate throughput
        throughput = batch_size / duration

        # Verify data was inserted
        stats = await chroma_store.get_stats()
        assert stats["count"] >= batch_size, f"Expected at least {batch_size} vectors, got {stats['count']}"

        # Assertions
        assert throughput > 1000, f"Throughput {throughput:.2f} vectors/s below threshold 1000"

    @pytest.mark.asyncio
    async def test_delete_performance(self, chroma_store: ChromaVectorStore) -> None:
        """Test vector deletion performance.

        Measures the time to delete 100 vectors.
        Delete operations should be fast as they only remove IDs from the index.

        Performance target: < 100ms for 100 vectors.
        """
        # Insert test data
        delete_count = 100
        ids_to_delete = [f"opt_delete_{i}" for i in range(delete_count)]

        # Insert vectors to delete
        _ = await chroma_store.upsert_vectors(
            ids=ids_to_delete,
            texts=[f"Optimized text to delete {i}" for i in range(delete_count)],
            metadatas=[{"to_delete": True, "test_type": "optimization"} for _ in range(delete_count)],
        )

        # Insert additional vectors that should remain
        _ = await chroma_store.upsert_vectors(
            ids=["opt_keep_1", "opt_keep_2"],
            texts=["Keep this optimized document", "Keep this one too"],
            metadatas=[{"to_delete": False}, {"to_delete": False}],
        )

        # Verify initial count
        stats_before = await chroma_store.get_stats()
        initial_count = stats_before["count"]
        assert initial_count >= delete_count, f"Expected at least {delete_count} vectors before deletion"

        # Measure delete latency
        start = time.time()
        _ = await chroma_store.delete_vectors(ids=ids_to_delete)
        delete_latency_ms = (time.time() - start) * 1000

        # Verify deletion
        stats_after = await chroma_store.get_stats()
        expected_count = initial_count - delete_count
        assert stats_after["count"] == expected_count, f"Expected {expected_count} vectors after deletion, got {stats_after['count']}"

        # Assertions
        assert delete_latency_ms < 100, f"Delete latency {delete_latency_ms:.2f}ms exceeds threshold 100ms for {delete_count} vectors"

    @pytest.mark.asyncio
    async def test_query_latency_with_large_dataset(self, chroma_store: ChromaVectorStore) -> None:
        """Test query latency with large dataset (1000+ vectors).

        Verifies that query performance remains acceptable even with
        a substantial number of vectors in the collection.

        Performance target: < 15ms per query with 1000 vectors.
        """
        # Insert 1000 vectors
        batch_size = 1000
        ids = [f"opt_large_{i}" for i in range(batch_size)]
        texts = [f"Large dataset test document {i} for performance benchmarking" for i in range(batch_size)]
        metadatas = [{"index": i, "test_type": "large_dataset"} for i in range(batch_size)]

        await chroma_store.upsert_vectors(ids=ids, texts=texts, metadatas=metadatas)

        # Warm up cache
        _ = await chroma_store.query_similar("warmup", n_results=1)

        # Measure query latency
        start = time.time()
        results = await chroma_store.query_similar("performance test document", n_results=10)
        latency_ms = (time.time() - start) * 1000

        # Assertions
        assert len(results) == 10, "Query should return 10 results"
        assert latency_ms < 15, f"Query latency {latency_ms:.2f}ms exceeds threshold 15ms with large dataset"

    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, chroma_store: ChromaVectorStore) -> None:
        """Test concurrent query performance.

        Measures performance when executing multiple queries concurrently.
        Verifies that the vector store can handle concurrent load efficiently.

        Performance target: Average latency < 15ms per query under concurrent load.
        """
        import asyncio

        # Insert test data
        _ = await chroma_store.upsert_vectors(
            ids=[f"opt_concurrent_{i}" for i in range(50)],
            texts=[f"Concurrent test document {i} for load testing" for i in range(50)],
            metadatas=[{"test_type": "concurrent"} for _ in range(50)],
        )

        # Warm up cache
        _ = await chroma_store.query_similar("warmup", n_results=1)

        # Execute 10 concurrent queries
        async def query_task(query_text: str) -> float:
            start = time.time()
            _ = await chroma_store.query_similar(query_text, n_results=5)
            return (time.time() - start) * 1000

        queries = [f"concurrent query {i}" for i in range(10)]
        latencies = await asyncio.gather(*[query_task(q) for q in queries])

        # Calculate average latency
        avg_latency = sum(latencies) / len(latencies)

        # Assertions
        assert avg_latency < 15, f"Average concurrent query latency {avg_latency:.2f}ms exceeds threshold 15ms"
        assert all(lat < 50 for lat in latencies), f"Some queries exceeded 50ms: {max(latencies):.2f}ms"
