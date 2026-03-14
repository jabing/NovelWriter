"""Unit tests for Neo4j client.

Tests cover:
- Configuration
- Connection handling
- Basic operations (with mocked driver)
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.novel_agent.db.neo4j_client import Neo4jClient, Neo4jConfig, QueryResult


class TestNeo4jConfig:
    """Test Neo4j configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = Neo4jConfig()
        assert config.uri == "bolt://localhost:7687"
        assert config.user == "neo4j"
        assert config.database == "neo4j"
        assert config.max_connection_pool_size == 50
        assert config.connection_timeout == 30.0
        assert config.max_retry_attempts == 3

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = Neo4jConfig(
            uri="bolt://custom:7687",
            user="admin",
            password="secret",
            database="test",
            max_connection_pool_size=100,
        )
        assert config.uri == "bolt://custom:7687"
        assert config.user == "admin"
        assert config.password == "secret"
        assert config.database == "test"
        assert config.max_connection_pool_size == 100


class TestNeo4jClientInit:
    """Test Neo4j client initialization."""

    def test_init_with_config(self) -> None:
        """Test client initialization with config."""
        config = Neo4jConfig(uri="bolt://test:7687")
        client = Neo4jClient(config=config)
        assert client.config.uri == "bolt://test:7687"
        assert client._driver is None
        assert client._connected is False

    def test_init_without_config(self) -> None:
        """Test client initialization with default config."""
        client = Neo4jClient()
        assert client.config.uri == "bolt://localhost:7687"
        assert client._driver is None
        assert client._connected is False


class TestNeo4jClientConnect:
    """Test Neo4j client connection."""

    @pytest.mark.asyncio
    async def test_connect_success(self) -> None:
        """Test successful connection."""
        client = Neo4jClient()

        mock_driver = AsyncMock()
        mock_driver.verify_connectivity = AsyncMock()

        with patch("neo4j.AsyncGraphDatabase.driver", return_value=mock_driver):
            result = await client.connect()

        assert result is True
        assert client._connected is True

    @pytest.mark.asyncio
    async def test_connect_failure(self) -> None:
        """Test connection failure."""
        client = Neo4jClient()

        with patch(
            "neo4j.AsyncGraphDatabase.driver",
            side_effect=Exception("Connection failed"),
        ):
            result = await client.connect()

        assert result is False
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_connect_import_error(self) -> None:
        """Test connection when neo4j package not installed."""
        client = Neo4jClient()

        with patch.dict("sys.modules", {"neo4j": None}):
            result = await client.connect()

        assert result is False


class TestNeo4jClientClose:
    """Test Neo4j client close."""

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test closing connection."""
        client = Neo4jClient()
        mock_driver = AsyncMock()
        client._driver = mock_driver
        client._connected = True

        await client.close()

        mock_driver.close.assert_called_once()
        assert client._driver is None
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_close_without_driver(self) -> None:
        """Test closing when no driver exists."""
        client = Neo4jClient()
        client._driver = None
        client._connected = False

        await client.close()

        assert client._driver is None
        assert client._connected is False


class TestNeo4jClientExecuteQuery:
    """Test Neo4j client query execution."""

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self) -> None:
        """Test query execution when not connected."""
        client = Neo4jClient()
        client._connected = False

        result = await client.execute_query("MATCH (n) RETURN n")

        assert result.success is False
        assert "Not connected" in result.error

    @pytest.mark.asyncio
    async def test_execute_query_success(self) -> None:
        """Test successful query execution."""
        client = Neo4jClient()
        client._connected = True

        mock_driver = AsyncMock()
        client._driver = mock_driver

        with patch.object(client, "execute_query", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = QueryResult(
                success=True,
                records=[{"name": "Alice"}],
                summary={"query_type": "r"},
            )
            result = await client.execute_query("MATCH (n) RETURN n")

        assert result.success is True


class TestNeo4jClientCreateNode:
    """Test Neo4j client node creation."""

    @pytest.mark.asyncio
    async def test_create_node_not_connected(self) -> None:
        """Test node creation when not connected."""
        client = Neo4jClient()
        client._connected = False

        result = await client.create_node("Character", {"name": "Alice"})

        assert result.success is False
        assert "Not connected" in result.error


class TestNeo4jClientSession:
    """Test Neo4j client session management."""

    @pytest.mark.asyncio
    async def test_session_not_connected(self) -> None:
        """Test session when not connected."""
        client = Neo4jClient()
        client._connected = False

        with pytest.raises(RuntimeError, match="Not connected"):
            async with client.session():
                pass
