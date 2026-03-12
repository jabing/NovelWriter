# tests/db/test_pinecone_client.py
"""Unit tests for Pinecone vector database client and embedding generator."""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Skip tests if pinecone not installed
pytest.importorskip("pinecone")

from src.db.embedding_generator import EmbeddingGenerator
from src.db.pinecone_client import VectorSearchResult, VectorStore, VectorUpsertResult


class TestEmbeddingGenerator:
    """Tests for EmbeddingGenerator class."""

    def test_init_default_values(self, tmp_path: Path) -> None:
        """Test initialization with default values."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        assert gen.model_name == EmbeddingGenerator.DEFAULT_MODEL
        assert gen.enable_cache is True
        assert gen.get_vector_dimension() == 384

    def test_init_cache_disabled(self) -> None:
        """Test initialization with caching disabled."""
        gen = EmbeddingGenerator(enable_cache=False)

        assert gen.enable_cache is False
        assert gen._cache == {}

    def test_get_text_hash(self, tmp_path: Path) -> None:
        """Test text hashing produces consistent results."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        text = "Test text for hashing"
        hash1 = gen._get_text_hash(text)
        hash2 = gen._get_text_hash(text)

        # Same text should produce same hash
        assert hash1 == hash2
        # Should be SHA256 hex digest
        assert len(hash1) == 64
        # Should match direct SHA256
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert hash1 == expected

    def test_embed_text_empty(self, tmp_path: Path) -> None:
        """Test embedding empty text returns zero vector."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        vector = gen.embed_text("")

        assert len(vector) == 384
        assert all(v == 0.0 for v in vector)

    def test_embed_text_whitespace(self, tmp_path: Path) -> None:
        """Test embedding whitespace-only text returns zero vector."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        vector = gen.embed_text("   \n\t  ")

        assert len(vector) == 384
        assert all(v == 0.0 for v in vector)

    def test_embed_text_produces_vector(self, tmp_path: Path) -> None:
        """Test embedding text produces valid vector."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        vector = gen.embed_text("This is a test sentence for embedding.")

        assert len(vector) == 384
        assert all(isinstance(v, float) for v in vector)
        # Vector should not be all zeros for real text
        assert not all(v == 0.0 for v in vector)

    def test_embed_batch_empty_list(self, tmp_path: Path) -> None:
        """Test embedding empty list returns empty list."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        vectors = gen.embed_batch([])

        assert vectors == []

    def test_embed_batch_multiple_texts(self, tmp_path: Path) -> None:
        """Test embedding multiple texts at once."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence.",
        ]
        vectors = gen.embed_batch(texts)

        assert len(vectors) == 3
        for vector in vectors:
            assert len(vector) == 384

    def test_cache_persistence(self, tmp_path: Path) -> None:
        """Test that embeddings are cached to disk."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        text = "Text to be cached"
        vector1 = gen.embed_text(text)

        # Create new generator with same cache dir
        gen2 = EmbeddingGenerator(cache_dir=cache_dir)
        vector2 = gen2.embed_text(text)

        # Should get same result from cache
        assert vector1 == vector2

    def test_clear_cache(self, tmp_path: Path) -> None:
        """Test clearing the cache."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        gen.embed_text("Some text to cache")
        assert len(gen._cache) > 0

        gen.clear_cache()

        assert len(gen._cache) == 0

    def test_get_cache_stats(self, tmp_path: Path) -> None:
        """Test getting cache statistics."""
        cache_dir = str(tmp_path / "cache")
        gen = EmbeddingGenerator(cache_dir=cache_dir)

        gen.embed_text("Text one")
        gen.embed_text("Text two")

        stats = gen.get_cache_stats()

        assert stats["cached_embeddings"] == 2
        assert stats["cache_enabled"] is True
        assert stats["model_name"] == EmbeddingGenerator.DEFAULT_MODEL
        assert stats["vector_dimension"] == 384


class TestVectorStore:
    """Tests for VectorStore class."""

    @pytest.fixture
    def mock_embedding_generator(self) -> MagicMock:
        """Create mock embedding generator."""
        mock = MagicMock(spec=EmbeddingGenerator)
        mock.VECTOR_DIMENSION = 384
        mock.embed_text = MagicMock(return_value=[0.1] * 384)
        mock.embed_batch = MagicMock(return_value=[[0.1] * 384, [0.2] * 384])
        return mock

    @pytest.fixture
    def mock_pinecone(self) -> MagicMock:
        """Create mock Pinecone client."""
        with patch("src.db.pinecone_client.Pinecone") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            # Mock index
            mock_index = MagicMock()
            mock_instance.Index.return_value = mock_index
            mock_instance.list_indexes.return_value = []

            # Mock describe_index_stats
            mock_index.describe_index_stats.return_value = MagicMock(
                dimension=384, index_fullness=0.0, total_vector_count=0, namespaces={}
            )

            yield mock

    def test_init_valid_index_name(self, mock_embedding_generator: MagicMock) -> None:
        """Test initialization with valid index name."""
        with patch("src.db.pinecone_client.Pinecone"):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="valid-index-name",
                embedding_generator=mock_embedding_generator,
            )

            assert vs.index_name == "valid-index-name"
            assert vs.namespace == VectorStore.DEFAULT_NAMESPACE

    def test_init_invalid_index_name_raises(self, mock_embedding_generator: MagicMock) -> None:
        """Test initialization with invalid index name raises ValueError."""
        with patch("src.db.pinecone_client.Pinecone"):
            with pytest.raises(ValueError, match="Invalid index name"):
                VectorStore(
                    api_key="test-api-key",
                    index_name="Invalid_Index_Name",
                    embedding_generator=mock_embedding_generator,
                )

    def test_init_index_name_with_spaces_raises(self, mock_embedding_generator: MagicMock) -> None:
        """Test initialization with spaces in index name raises ValueError."""
        with patch("src.db.pinecone_client.Pinecone"):
            with pytest.raises(ValueError, match="Invalid index name"):
                VectorStore(
                    api_key="test-api-key",
                    index_name="index with spaces",
                    embedding_generator=mock_embedding_generator,
                )

    @pytest.mark.asyncio
    async def test_embed_text_async(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test async text embedding."""
        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            result = await vs.embed_text("test text")

            assert len(result) == 384
            mock_embedding_generator.embed_text.assert_called_once_with("test text")

    @pytest.mark.asyncio
    async def test_embed_batch_async(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test async batch embedding."""
        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            texts = ["text one", "text two"]
            result = await vs.embed_batch(texts)

            assert len(result) == 2
            mock_embedding_generator.embed_batch.assert_called_once_with(texts)

    @pytest.mark.asyncio
    async def test_upsert_vectors_success(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test successful vector upsert."""
        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            # Access index to trigger lazy load
            _ = vs.index

            results = await vs.upsert_vectors(
                ids=["id1", "id2"],
                texts=["text one", "text two"],
                metadata=[{"type": "fact"}, {"type": "setting"}],
            )

            assert len(results) == 2
            assert all(r.success for r in results)
            assert results[0].id == "id1"
            assert results[1].id == "id2"

    @pytest.mark.asyncio
    async def test_upsert_vectors_mismatched_lengths_raises(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test upsert with mismatched lengths raises ValueError."""
        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            with pytest.raises(ValueError, match="same length"):
                await vs.upsert_vectors(
                    ids=["id1"],
                    texts=["text one", "text two"],
                )

    @pytest.mark.asyncio
    async def test_upsert_single(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test single vector upsert."""
        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            _ = vs.index  # Trigger lazy load

            result = await vs.upsert_single(
                id="single-id",
                text="single text",
                metadata={"category": "test"},
            )

            assert result.success is True
            assert result.id == "single-id"

    @pytest.mark.asyncio
    async def test_query_similar(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test similar vector query."""
        mock_match = MagicMock()
        mock_match.id = "similar-id"
        mock_match.score = 0.95
        mock_match.metadata = {"text": "similar text"}

        mock_response = MagicMock()
        mock_response.matches = [mock_match]

        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            vs.index.query.return_value = mock_response

            results = await vs.query_similar(
                query_text="query text",
                top_k=5,
            )

            assert len(results) == 1
            assert results[0].id == "similar-id"
            assert results[0].score == 0.95

    @pytest.mark.asyncio
    async def test_query_similar_no_results(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test query with no results."""
        mock_response = MagicMock()
        mock_response.matches = []

        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            vs.index.query.return_value = mock_response

            results = await vs.query_similar("query text")

            assert results == []

    @pytest.mark.asyncio
    async def test_query_by_vector(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test query using pre-computed vector."""
        mock_match = MagicMock()
        mock_match.id = "vector-id"
        mock_match.score = 0.88
        mock_match.metadata = {}

        mock_response = MagicMock()
        mock_response.matches = [mock_match]

        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            vs.index.query.return_value = mock_response

            query_vector = [0.1] * 384
            results = await vs.query_by_vector(query_vector, top_k=3)

            assert len(results) == 1
            assert results[0].id == "vector-id"

    @pytest.mark.asyncio
    async def test_delete_vectors(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test vector deletion."""
        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            _ = vs.index

            result = await vs.delete_vectors(["id1", "id2"])

            assert result is True
            vs.index.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_all(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test deleting all vectors in namespace."""
        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            _ = vs.index

            result = await vs.delete_all()

            assert result is True
            vs.index.delete.assert_called_once_with(delete_all=True, namespace=vs.namespace)

    @pytest.mark.asyncio
    async def test_fetch_vectors(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test fetching vectors by IDs."""
        mock_vector = MagicMock()
        mock_vector.values = [0.1] * 384
        mock_vector.metadata = {"key": "value"}

        mock_response = MagicMock()
        mock_response.vectors = {"fetch-id": mock_vector}

        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            vs.index.fetch.return_value = mock_response

            results = await vs.fetch_vectors(["fetch-id"])

            assert "fetch-id" in results
            assert len(results["fetch-id"]["values"]) == 384

    @pytest.mark.asyncio
    async def test_get_index_stats(
        self, mock_embedding_generator: MagicMock, mock_pinecone: MagicMock
    ) -> None:
        """Test getting index statistics."""
        mock_stats = MagicMock()
        mock_stats.dimension = 384
        mock_stats.index_fullness = 0.5
        mock_stats.total_vector_count = 100
        mock_stats.namespaces = {"default": MagicMock(vector_count=100)}

        with patch("src.db.pinecone_client.Pinecone", mock_pinecone):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            vs.index.describe_index_stats.return_value = mock_stats

            stats = await vs.get_index_stats()

            assert stats["dimension"] == 384
            assert stats["total_vector_count"] == 100

    def test_set_namespace(self, mock_embedding_generator: MagicMock) -> None:
        """Test changing namespace."""
        with patch("src.db.pinecone_client.Pinecone"):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            vs.set_namespace("new-namespace")

            assert vs.namespace == "new-namespace"

    def test_close(self, mock_embedding_generator: MagicMock) -> None:
        """Test closing client connection."""
        with patch("src.db.pinecone_client.Pinecone"):
            vs = VectorStore(
                api_key="test-api-key",
                index_name="test-index",
                embedding_generator=mock_embedding_generator,
            )

            # Trigger lazy load
            _ = vs.pc
            _ = vs.index

            vs.close()

            assert vs._pc is None
            assert vs._index is None


class TestVectorSearchResult:
    """Tests for VectorSearchResult dataclass."""

    def test_create_result(self) -> None:
        """Test creating a search result."""
        result = VectorSearchResult(
            id="test-id",
            score=0.95,
            metadata={"key": "value"},
        )

        assert result.id == "test-id"
        assert result.score == 0.95
        assert result.metadata == {"key": "value"}

    def test_default_metadata(self) -> None:
        """Test default empty metadata."""
        result = VectorSearchResult(id="test-id", score=0.5)

        assert result.metadata == {}


class TestVectorUpsertResult:
    """Tests for VectorUpsertResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful upsert result."""
        result = VectorUpsertResult(id="test-id", success=True)

        assert result.id == "test-id"
        assert result.success is True
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test failed upsert result."""
        result = VectorUpsertResult(
            id="test-id",
            success=False,
            error="Connection failed",
        )

        assert result.success is False
        assert result.error == "Connection failed"
