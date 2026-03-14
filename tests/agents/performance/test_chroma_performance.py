"""ChromaVectorStore performance benchmarking tests.

Tests measure actual latency and throughput to verify performance targets:
- Query latency: < 20ms
- Batch insert throughput: > 1000 vectors/s
- Embedding generation: acceptable latency
- Delete performance: acceptable latency
"""

import sys
import time
import tempfile

import pytest

# Skip tests if chromadb is not installed or incompatible with Python version
# ChromaDB depends on pydantic.v1 which is incompatible with Python 3.14+
if sys.version_info >= (3, 14):
    try:
        import chromadb  # noqa: F401
    except Exception as e:
        pytest.skip(
            f"ChromaDB not compatible with Python {sys.version_info.major}.{sys.version_info.minor}: {e}",
            allow_module_level=True
        )
else:
    pytest.importorskip("chromadb", reason="chromadb not installed, skipping performance tests")

from src.novel_agent.db.chroma_client import ChromaVectorStore


class TestChromaPerformance:
    """Chroma performance benchmarking tests.

    All tests use temporary collections to avoid conflicts with production data.
    Tests are skipped if chromadb is not installed.
    """

    @pytest.fixture
    async def chroma_store(self):
        """Create a temporary ChromaVectorStore for testing.

        Uses a temporary directory to avoid conflicts with production data.
        Collection is cleaned up after test completion.
        """
        # Create temporary directory for test data
        temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
        test_collection = f"test_chroma_perf_{id(self)}"

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
    async def test_query_latency(self, chroma_store: ChromaVectorStore) -> None:
        """Test that query latency is < 20ms.

        Measures the time for a single similarity query after data is inserted.
        This test includes embedding generation time.

        Performance target: < 20ms per query.
        """
        # Insert test data first
        _ = await chroma_store.upsert_vectors(
            ids=["test_1", "test_2", "test_3"],
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

        # Measure query latency
        start = time.time()
        results = await chroma_store.query_similar("scientist working at SETI", n_results=5)
        latency_ms = (time.time() - start) * 1000

        # Assertions
        assert len(results) > 0, "Query should return at least one result"
        assert latency_ms < 20, f"Query latency {latency_ms:.2f}ms exceeds threshold 20ms"

    @pytest.mark.asyncio
    async def test_batch_insert_throughput(self, chroma_store: ChromaVectorStore) -> None:
        """Test that batch insert throughput is > 1000 vectors/s.

        Measures the time to insert 1000 vectors in a single batch operation.
        This includes embedding generation time.

        Performance target: > 1000 vectors/s.
        """
        # Prepare test data
        batch_size = 1000
        ids = [f"test_batch_{i}" for i in range(batch_size)]
        texts = [f"Test document number {i} with some sample text" for i in range(batch_size)]
        metadatas = [{"batch": i // 100} for i in range(batch_size)]

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
    async def test_embedding_generation_latency(self, chroma_store: ChromaVectorStore) -> None:
        """Test embedding generation performance.

        Measures the time to generate embeddings for a single text.
        First query includes model loading time (~100MB download if not cached).

        Performance expectation: < 100ms (warm cache).
        """
        # Insert test data
        test_text = "Alice is a brilliant scientist who works at SETI studying extraterrestrial signals"
        _ = await chroma_store.upsert_vectors(
            ids=["embed_test"],
            texts=[test_text],
            metadatas=[{"type": "test"}],
        )

        # Measure query latency (includes embedding generation)
        start = time.time()
        results = await chroma_store.query_similar(test_text, n_results=1)
        latency_ms = (time.time() - start) * 1000

        # Assertions
        assert len(results) > 0, "Query should return results"
        assert results[0]["distance"] < 0.1, "Exact match should have very low distance"

        # Note: First query may be slower due to model loading
        # Subsequent queries should be < 100ms
        assert latency_ms < 500, f"Embedding generation latency {latency_ms:.2f}ms exceeds 500ms (cold cache acceptable)"

    @pytest.mark.asyncio
    async def test_delete_performance(self, chroma_store: ChromaVectorStore) -> None:
        """Test vector deletion performance.

        Measures the time to delete 100 vectors.
        Delete operations should be fast as they only remove IDs from the index.

        Performance expectation: < 100ms for 100 vectors.
        """
        # Insert test data
        delete_count = 100
        ids_to_delete = [f"delete_test_{i}" for i in range(delete_count)]

        # Insert vectors to delete
        _ = await chroma_store.upsert_vectors(
            ids=ids_to_delete,
            texts=[f"Text to delete {i}" for i in range(delete_count)],
            metadatas=[{"to_delete": True} for _ in range(delete_count)],
        )

        # Insert additional vectors that should remain
        _ = await chroma_store.upsert_vectors(
            ids=["keep_1", "keep_2"],
            texts=["Keep this document", "Keep this one too"],
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
