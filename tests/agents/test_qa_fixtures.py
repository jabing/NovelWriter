"""Test that QA fixtures are correctly configured."""

import pytest

from tests.agents.fixtures.qa_fixtures import (
    ALL_QA_FIXTURES,
    INVALID_NOVEL_DEAD_CHARACTER,
    VALID_NOVEL_DATA,
)
from tests.agents.utils.test_data_generator import (
    generate_test_character,
    generate_test_novel,
)


class TestQAFixtures:
    """Test that QA fixtures work correctly."""

    def test_sample_character_profile(self, sample_character_profile: dict) -> None:
        """Test that sample character profile fixture works."""
        assert "id" in sample_character_profile
        assert "name" in sample_character_profile
        assert sample_character_profile["name"] == "测试角色"
        assert sample_character_profile["status"] == "alive"

    def test_sample_chapter_content(self, sample_chapter_content: str) -> None:
        """Test that sample chapter content fixture works."""
        assert isinstance(sample_chapter_content, str)
        assert "第1章" in sample_chapter_content
        assert "测试角色" in sample_chapter_content

    def test_generate_test_character(self) -> None:
        """Test that test data generator creates valid characters."""
        char = generate_test_character(name="测试", role="protagonist")
        assert char["name"] == "测试"
        assert char["role"] == "protagonist"
        assert char["status"] == "alive"
        assert "id" in char

    def test_generate_test_novel(self) -> None:
        """Test that test data generator creates valid novels."""
        novel = generate_test_novel(chapters=5)
        assert novel["total_chapters"] == 5
        assert len(novel["chapters"]) == 5
        assert len(novel["characters"]) >= 1

    def test_valid_novel_fixture(self) -> None:
        """Test that valid novel fixture is correct."""
        assert VALID_NOVEL_DATA["novel_id"] == "valid_novel_001"
        assert len(VALID_NOVEL_DATA["characters"]) == 2
        assert VALID_NOVEL_DATA["characters"][0]["status"] == "alive"

    def test_invalid_novel_fixture(self) -> None:
        """Test that invalid novel fixture has expected issues."""
        char = INVALID_NOVEL_DEAD_CHARACTER["characters"][0]
        assert char["status"] == "deceased"
        assert char["death_chapter"] == 10
        # Chapter 15 should reference this deceased character
        assert "char_invalid_001" in INVALID_NOVEL_DEAD_CHARACTER["chapters"][0]["characters_present"]

    def test_all_qa_fixtures_structure(self) -> None:
        """Test that ALL_QA_FIXTURES has all expected sections."""
        assert "valid" in ALL_QA_FIXTURES
        assert "invalid" in ALL_QA_FIXTURES
        assert "edge_cases" in ALL_QA_FIXTURES
        assert "scenarios" in ALL_QA_FIXTURES
        assert "expected_results" in ALL_QA_FIXTURES
        assert "knowledge_graph" in ALL_QA_FIXTURES


@pytest.mark.asyncio
class TestAsyncQAFixtures:
    """Test async QA fixtures."""

    async def test_neo4j_client_fixture(self, neo4j_client) -> None:
        """Test that Neo4j client fixture works."""
        # Fixture should be a mock with async methods
        assert neo4j_client.connect.called
        assert neo4j_client.close.called

    async def test_postgres_session_fixture(self, postgres_session) -> None:
        """Test that PostgreSQL session fixture works."""
        # Session should have expected methods
        assert hasattr(postgres_session, "execute")
        assert hasattr(postgres_session, "commit")
        assert hasattr(postgres_session, "close")

    async def test_pinecone_client_fixture(self, pinecone_client) -> None:
        """Test that Pinecone client fixture works."""
        # Client should have vector operations
        assert hasattr(pinecone_client, "upsert")
        assert hasattr(pinecone_client, "query")
        assert hasattr(pinecone_client, "delete")
