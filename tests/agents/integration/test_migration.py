"""Integration tests for JSON to Neo4j migration.

Tests verify:
- Neo4jClient operations
- Migration script functionality
- Data integrity verification
- Rollback mechanisms
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.novel_agent.db.neo4j_client import (
    Neo4jClient,
    Neo4jConfig,
    QueryResult,
)


class MockNeo4jDriver:
    """Mock Neo4j driver for testing without actual Neo4j instance."""

    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.relationships: dict[str, dict] = {}
        self._closed = False

    async def verify_connectivity(self) -> None:
        pass

    async def close(self) -> None:
        self._closed = True

    def session(self, database: str = "neo4j"):
        return MockSession(self)


class MockSession:
    """Mock Neo4j session."""

    def __init__(self, driver: MockNeo4jDriver) -> None:
        self.driver = driver

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def run(self, query: str, parameters: dict = None):
        return MockResult(self.driver, query, parameters or {})


class MockResult:
    """Mock Neo4j query result."""

    def __init__(self, driver: MockNeo4jDriver, query: str, params: dict) -> None:
        self.driver = driver
        self.query = query
        self.params = params
        self._records = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._records:
            return self._records.pop(0)
        raise StopAsyncIteration

    async def consume(self):
        return MagicMock(query_type="w", counters=MagicMock())


@pytest.fixture
def mock_driver():
    """Create a mock Neo4j driver."""
    return MockNeo4jDriver()


@pytest.fixture
def neo4j_config():
    """Create Neo4j configuration."""
    return Neo4jConfig(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test_password",
        database="neo4j",
    )


@pytest.fixture
def temp_json_storage(tmp_path):
    """Create temporary JSON storage with test data."""
    storage_path = tmp_path / "knowledge_graphs" / "test_novel"
    storage_path.mkdir(parents=True)

    nodes = [
        {
            "node_id": "char_1",
            "node_type": "character",
            "properties": {"name": "Alice", "age": 25},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
        {
            "node_id": "char_2",
            "node_type": "character",
            "properties": {"name": "Bob", "age": 30},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
        {
            "node_id": "loc_1",
            "node_type": "location",
            "properties": {"name": "City A"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        },
    ]

    edges = [
        {
            "edge_id": "rel_1",
            "source_id": "char_1",
            "target_id": "char_2",
            "relationship_type": "KNOWS",
            "weight": 1.0,
            "properties": {"since": "2020"},
            "created_at": "2024-01-01T00:00:00",
        },
        {
            "edge_id": "rel_2",
            "source_id": "char_1",
            "target_id": "loc_1",
            "relationship_type": "LOCATED_AT",
            "weight": 1.0,
            "properties": {},
            "created_at": "2024-01-01T00:00:00",
        },
    ]

    with open(storage_path / "nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=2)

    with open(storage_path / "edges.json", "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2)

    return storage_path


class TestNeo4jClient:
    """Test Neo4jClient operations."""

    @pytest.mark.asyncio
    async def test_connect_success(self, neo4j_config):
        """Test successful connection to Neo4j."""
        client = Neo4jClient(neo4j_config)

        with patch("src.novel_agent.db.neo4j_client.AsyncGraphDatabase") as mock_db:
            mock_driver = MagicMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_db.driver.return_value = mock_driver

            result = await client.connect()

            assert result is True
            assert client._connected is True

    @pytest.mark.asyncio
    async def test_connect_import_error(self, neo4j_config):
        """Test connection failure when neo4j package not installed."""
        client = Neo4jClient(neo4j_config)

        with patch.dict("sys.modules", {"neo4j": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                result = await client.connect()

                assert result is False
                assert client._connected is False

    @pytest.mark.asyncio
    async def test_close(self, neo4j_config):
        """Test closing Neo4j connection."""
        client = Neo4jClient(neo4j_config)
        client._driver = AsyncMock()
        client._connected = True

        await client.close()

        client._driver.close.assert_called_once()
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self, neo4j_config):
        """Test query execution when not connected."""
        client = Neo4jClient(neo4j_config)

        result = await client.execute_query("RETURN 1")

        assert result.success is False
        assert "Not connected" in result.error

    @pytest.mark.asyncio
    async def test_create_node_success(self, neo4j_config, mock_driver):
        """Test successful node creation."""
        client = Neo4jClient(neo4j_config)
        client._driver = mock_driver
        client._connected = True

        with patch.object(client, "execute_query") as mock_query:
            mock_query.return_value = QueryResult(
                success=True,
                records=[{"n": {"node_id": "test_node"}}],
            )

            result = await client.create_node(
                "Character",
                {"name": "Alice", "age": 25},
                "test_node",
            )

            assert result.success is True
            assert result.node_id == "test_node"

    @pytest.mark.asyncio
    async def test_create_relationship_success(self, neo4j_config, mock_driver):
        """Test successful relationship creation."""
        client = Neo4jClient(neo4j_config)
        client._driver = mock_driver
        client._connected = True

        with patch.object(client, "execute_query") as mock_query:
            mock_query.return_value = QueryResult(
                success=True,
                records=[{"r": {"rel_id": "test_rel"}}],
            )

            result = await client.create_relationship(
                "node_1",
                "node_2",
                "KNOWS",
                {"since": "2020"},
            )

            assert result.success is True
            assert result.rel_id is not None

    @pytest.mark.asyncio
    async def test_get_node_count(self, neo4j_config, mock_driver):
        """Test getting node count."""
        client = Neo4jClient(neo4j_config)
        client._driver = mock_driver
        client._connected = True

        with patch.object(client, "execute_query") as mock_query:
            mock_query.return_value = QueryResult(
                success=True,
                records=[{"count": 42}],
            )

            count = await client.get_node_count()

            assert count == 42

    @pytest.mark.asyncio
    async def test_health_check(self, neo4j_config, mock_driver):
        """Test health check."""
        client = Neo4jClient(neo4j_config)
        client._driver = mock_driver
        client._connected = True

        with patch.object(client, "get_node_count", return_value=100):
            with patch.object(client, "get_relationship_count", return_value=50):
                health = await client.health_check()

                assert health["connected"] is True
                assert health["healthy"] is True
                assert health["node_count"] == 100
                assert health["relationship_count"] == 50


class TestJSONDataLoader:
    """Test JSON data loading functionality."""

    def test_load_nodes(self, temp_json_storage):
        """Test loading nodes from JSON."""
        from scripts.migrate_to_neo4j import JSONDataLoader

        loader = JSONDataLoader(temp_json_storage)
        nodes = loader.load_nodes()

        assert len(nodes) == 3
        assert nodes[0]["node_id"] == "char_1"
        assert nodes[0]["node_type"] == "character"

    def test_load_edges(self, temp_json_storage):
        """Test loading edges from JSON."""
        from scripts.migrate_to_neo4j import JSONDataLoader

        loader = JSONDataLoader(temp_json_storage)
        edges = loader.load_edges()

        assert len(edges) == 2
        assert edges[0]["relationship_type"] == "KNOWS"

    def test_count_records(self, temp_json_storage):
        """Test counting records."""
        from scripts.migrate_to_neo4j import JSONDataLoader

        loader = JSONDataLoader(temp_json_storage)
        node_count, edge_count = loader.count_records()

        assert node_count == 3
        assert edge_count == 2

    def test_nonexistent_path(self, tmp_path):
        """Test loading from nonexistent path."""
        from scripts.migrate_to_neo4j import JSONDataLoader

        loader = JSONDataLoader(tmp_path / "nonexistent")

        assert loader.exists() is False
        assert loader.load_nodes() == []
        assert loader.load_edges() == []


class TestMigrationBackup:
    """Test backup functionality."""

    def test_create_backup(self, temp_json_storage, tmp_path):
        """Test creating backup."""
        from scripts.migrate_to_neo4j import MigrationBackup

        backup_dir = tmp_path / "backups"
        backup = MigrationBackup(backup_dir)

        backup_path = backup.create_backup(temp_json_storage, "test_novel")

        assert backup_path is not None
        assert (backup_path / "nodes.json").exists()
        assert (backup_path / "edges.json").exists()
        assert (backup_path / "manifest.json").exists()

    def test_restore_backup(self, temp_json_storage, tmp_path):
        """Test restoring from backup."""
        from scripts.migrate_to_neo4j import MigrationBackup

        backup_dir = tmp_path / "backups"
        restore_dir = tmp_path / "restored"

        backup = MigrationBackup(backup_dir)
        backup_path = backup.create_backup(temp_json_storage, "test_novel")

        result = backup.restore_backup(backup_path, restore_dir)

        assert result is True
        assert (restore_dir / "nodes.json").exists()
        assert (restore_dir / "edges.json").exists()


class TestKnowledgeGraphMigrator:
    """Test migration process."""

    def test_map_node_to_neo4j(self, temp_json_storage):
        """Test node mapping."""
        from scripts.migrate_to_neo4j import (
            KnowledgeGraphMigrator,
            MigrationConfig,
        )

        config = MigrationConfig(
            novel_id="test",
            json_storage_path=temp_json_storage,
        )
        migrator = KnowledgeGraphMigrator(config)

        node_data = {
            "node_id": "test_node",
            "node_type": "character",
            "properties": {"name": "Alice", "age": 25},
            "created_at": "2024-01-01T00:00:00",
        }

        label, properties = migrator.map_node_to_neo4j(node_data)

        assert label == "character"
        assert properties["node_id"] == "test_node"
        assert properties["name"] == "Alice"

    def test_map_edge_to_neo4j(self, temp_json_storage):
        """Test edge mapping."""
        from scripts.migrate_to_neo4j import (
            KnowledgeGraphMigrator,
            MigrationConfig,
        )

        config = MigrationConfig(
            novel_id="test",
            json_storage_path=temp_json_storage,
        )
        migrator = KnowledgeGraphMigrator(config)

        edge_data = {
            "edge_id": "test_rel",
            "source_id": "node_1",
            "target_id": "node_2",
            "relationship_type": "KNOWS",
            "weight": 1.0,
            "properties": {"since": "2020"},
        }

        source_id, target_id, rel_type, properties = migrator.map_edge_to_neo4j(
            edge_data
        )

        assert source_id == "node_1"
        assert target_id == "node_2"
        assert rel_type == "KNOWS"
        assert properties["since"] == "2020"

    def test_validate_node_data(self, temp_json_storage):
        """Test node data validation."""
        from scripts.migrate_to_neo4j import (
            KnowledgeGraphMigrator,
            MigrationConfig,
        )

        config = MigrationConfig(
            novel_id="test",
            json_storage_path=temp_json_storage,
        )
        migrator = KnowledgeGraphMigrator(config)

        valid_node = {"node_id": "test", "node_type": "character"}
        is_valid, error = migrator.validate_node_data(valid_node)
        assert is_valid is True

        invalid_node = {"node_id": "test"}
        is_valid, error = migrator.validate_node_data(invalid_node)
        assert is_valid is False
        assert "node_type" in error.lower()

    def test_validate_edge_data(self, temp_json_storage):
        """Test edge data validation."""
        from scripts.migrate_to_neo4j import (
            KnowledgeGraphMigrator,
            MigrationConfig,
        )

        config = MigrationConfig(
            novel_id="test",
            json_storage_path=temp_json_storage,
        )
        migrator = KnowledgeGraphMigrator(config)

        valid_edge = {
            "edge_id": "rel_1",
            "source_id": "s1",
            "target_id": "t1",
            "relationship_type": "KNOWS",
        }
        is_valid, error = migrator.validate_edge_data(valid_edge)
        assert is_valid is True

        invalid_edge = {"edge_id": "rel_1"}
        is_valid, error = migrator.validate_edge_data(invalid_edge)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_dry_run(self, temp_json_storage):
        """Test dry run mode."""
        from scripts.migrate_to_neo4j import (
            KnowledgeGraphMigrator,
            MigrationConfig,
        )

        config = MigrationConfig(
            novel_id="test_novel",
            json_storage_path=temp_json_storage,
            dry_run=True,
        )
        migrator = KnowledgeGraphMigrator(config)

        stats = await migrator.run()

        assert stats.total_nodes == 3
        assert stats.total_edges == 2
        assert stats.migrated_nodes == 3
        assert stats.migrated_edges == 2


class TestMigrationStats:
    """Test migration statistics."""

    def test_duration_seconds(self):
        """Test duration calculation."""
        from scripts.migrate_to_neo4j import MigrationStats

        stats = MigrationStats(
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 0, 30),
        )

        assert stats.duration_seconds() == 30.0

    def test_success_rate(self):
        """Test success rate calculation."""
        from scripts.migrate_to_neo4j import MigrationStats

        stats = MigrationStats(
            total_nodes=100,
            total_edges=50,
            migrated_nodes=98,
            migrated_edges=50,
        )

        node_rate, edge_rate = stats.success_rate()

        assert node_rate == 98.0
        assert edge_rate == 100.0


class TestVerification:
    """Test verification functionality."""

    def test_verification_result(self):
        """Test verification result dataclass."""
        from scripts.verify_migration import VerificationResult

        result = VerificationResult(
            name="Test",
            passed=True,
            expected=100,
            actual=100,
            message="All good",
        )

        assert result.passed is True
        assert result.expected == 100

    def test_verification_report(self):
        """Test verification report."""
        from scripts.verify_migration import (
            VerificationReport,
            VerificationResult,
        )

        report = VerificationReport(
            novel_id="test",
            timestamp=datetime.now(),
        )

        report.add_result(
            VerificationResult(name="Check 1", passed=True, expected=1, actual=1)
        )
        report.add_result(
            VerificationResult(name="Check 2", passed=False, expected=2, actual=1)
        )

        assert report.total_checks == 2
        assert report.passed_checks == 1
        assert report.failed_checks == 1
        assert report.success_rate() == 50.0
        assert report.is_complete_success() is False


class TestEndToEndMigration:
    """End-to-end migration tests."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires running Neo4j instance")
    async def test_full_migration_with_neo4j(self, temp_json_storage):
        """Test full migration with actual Neo4j."""
        pass

    @pytest.mark.asyncio
    async def test_migration_with_mock_neo4j(self, temp_json_storage):
        """Test migration with mocked Neo4j."""
        from scripts.migrate_to_neo4j import (
            KnowledgeGraphMigrator,
            MigrationConfig,
        )

        config = MigrationConfig(
            novel_id="test_novel",
            json_storage_path=temp_json_storage,
        )
        migrator = KnowledgeGraphMigrator(config)

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(return_value=True)
        mock_client.close = AsyncMock()
        mock_client.batch_create_nodes = AsyncMock(return_value=(3, []))
        mock_client.batch_create_relationships = AsyncMock(return_value=(2, []))
        mock_client._connected = True

        migrator._neo4j_client = mock_client

        stats = await migrator.run()

        assert stats.total_nodes == 3
        assert stats.total_edges == 2
        assert stats.migrated_nodes == 3
        assert stats.migrated_edges == 2
