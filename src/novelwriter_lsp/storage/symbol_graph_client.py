"""
Symbol Graph Client - LSP-focused Neo4j interface for symbol management.

Provides a simplified, type-safe interface specifically designed for
the LSP SymbolIndex workflow. Extends the base Neo4jClient with
LSP-specific operations.
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any

from novelwriter_lsp.storage.neo4j_client import Neo4jClient, Neo4jConfig, NodeResult
from novelwriter_lsp.types import BaseSymbol, SymbolType

logger = logging.getLogger(__name__)


class SymbolGraphClient:
    """
    LSP-focused graph client for symbol management.

    Provides a simplified interface specifically for the SymbolIndex workflow,
    with type-safe methods for storing and retrieving symbols in Neo4j.

    Attributes:
        client: Underlying Neo4j client instance
    """

    client: Neo4jClient

    def __init__(self, config: Neo4jConfig | None = None) -> None:
        """
        Initialize the SymbolGraphClient.

        Args:
            config: Optional Neo4j configuration. Uses defaults if not provided.
        """
        self.client = Neo4jClient(config)

    async def connect(self) -> bool:
        """
        Establish connection to Neo4j database.

        Returns:
            True if connection successful, False otherwise
        """
        return await self.client.connect()

    async def close(self) -> None:
        """Close the Neo4j connection."""
        await self.client.close()

    def _symbol_to_properties(self, symbol: BaseSymbol) -> dict[str, Any]:
        props = asdict(symbol)

        if isinstance(props.get("type"), SymbolType):
            props["type"] = props["type"].value

        props["updated_at"] = datetime.now().isoformat()

        return props

    def _properties_to_symbol(self, props: dict[str, Any]) -> BaseSymbol:
        symbol_props = dict(props)

        if "type" in symbol_props and isinstance(symbol_props["type"], str):
            try:
                symbol_props["type"] = SymbolType(symbol_props["type"])
            except ValueError:
                logger.warning(f"Unknown symbol type: {symbol_props['type']}")

        symbol_props.pop("node_id", None)
        symbol_props.pop("created_at", None)
        symbol_props.pop("updated_at", None)

        return BaseSymbol(**symbol_props)

    async def index_symbol(self, symbol: BaseSymbol) -> NodeResult:
        """
        Index a single symbol in the graph database.

        Uses MERGE to either create a new node or update an existing one.

        Args:
            symbol: The symbol to index

        Returns:
            NodeResult with operation status and symbol info
        """
        label = symbol.type.value.capitalize()
        properties = self._symbol_to_properties(symbol)

        result = await self.client.create_node(
            label=label, properties=properties, node_id=symbol.id
        )

        if result.success:
            logger.debug(f"Indexed symbol: {symbol.name} (ID: {symbol.id})")
        else:
            logger.error(f"Failed to index symbol {symbol.name}: {result.error}")

        return result

    async def get_symbol_by_id(self, symbol_id: str) -> BaseSymbol | None:
        """
        Retrieve a symbol by its unique ID.

        Args:
            symbol_id: The unique identifier of the symbol

        Returns:
            The symbol if found, None otherwise
        """
        node_props = await self.client.get_node(symbol_id)

        if node_props:
            try:
                return self._properties_to_symbol(node_props)
            except Exception as e:
                logger.error(f"Failed to reconstruct symbol from node: {e}")
                return None

        return None

    async def find_symbol_by_name(
        self, name: str, symbol_type: SymbolType | None = None
    ) -> list[BaseSymbol]:
        """
        Search for symbols by name (case-insensitive partial match).

        Args:
            name: The name or partial name to search for
            symbol_type: Optional filter by symbol type

        Returns:
            List of matching symbols
        """
        if symbol_type:
            label = symbol_type.value.capitalize()
            query = f"""
            MATCH (n:{label})
            WHERE n.name CONTAINS $name
            RETURN n
            """
        else:
            query = """
            MATCH (n)
            WHERE n.name CONTAINS $name
            AND n.type IS NOT NULL
            RETURN n
            """

        result = await self.client.execute_query(query, {"name": name})

        symbols = []
        if result.success and result.records:
            for record in result.records:
                node = record.get("n")
                if node:
                    try:
                        symbol = self._properties_to_symbol(dict(node))
                        symbols.append(symbol)
                    except Exception as e:
                        logger.warning(f"Failed to process node: {e}")

        return symbols

    async def get_references(self, symbol_id: str) -> list[dict[str, Any]]:
        """
        Get all references to a symbol.

        Note: This is a placeholder implementation. In a full implementation,
        this would query relationships in the graph. For now, it extracts
        references from the symbol's own references list.

        Args:
            symbol_id: The ID of the symbol to get references for

        Returns:
            List of reference locations
        """
        symbol = await self.get_symbol_by_id(symbol_id)
        if symbol:
            return symbol.references
        return []

    async def update_symbol(self, symbol: BaseSymbol) -> NodeResult:
        """
        Update an existing symbol in the database.

        This is actually the same as index_symbol since we use MERGE,
        but provided as a separate method for clarity in the API.

        Args:
            symbol: The symbol with updated data

        Returns:
            NodeResult with operation status
        """
        return await self.index_symbol(symbol)

    async def delete_symbol(self, symbol_id: str) -> bool:
        """
        Delete a symbol from the database by ID.

        Args:
            symbol_id: The ID of the symbol to delete

        Returns:
            True if deletion was successful
        """
        query = """
        MATCH (n {node_id: $symbol_id})
        DETACH DELETE n
        """

        result = await self.client.execute_query(query, {"symbol_id": symbol_id})

        if result.success:
            logger.debug(f"Deleted symbol: {symbol_id}")
            return True

        logger.error(f"Failed to delete symbol {symbol_id}: {result.error}")
        return False

    async def get_all_symbols(
        self, symbol_type: SymbolType | None = None, novel_id: str | None = None
    ) -> list[BaseSymbol]:
        """
        Get all symbols, optionally filtered by type or novel.

        Args:
            symbol_type: Optional filter by symbol type
            novel_id: Optional filter by novel ID

        Returns:
            List of symbols
        """
        conditions = []
        params = {}

        if symbol_type:
            label = symbol_type.value.capitalize()
            match_clause = f"MATCH (n:{label})"
        else:
            match_clause = "MATCH (n) WHERE n.type IS NOT NULL"

        if novel_id:
            conditions.append("n.novel_id = $novel_id")
            params["novel_id"] = novel_id

        where_clause = " AND ".join(conditions)
        if where_clause:
            if symbol_type:
                query = f"{match_clause} WHERE {where_clause} RETURN n"
            else:
                query = f"{match_clause} AND {where_clause} RETURN n"
        else:
            query = f"{match_clause} RETURN n"

        result = await self.client.execute_query(query, params)

        symbols = []
        if result.success and result.records:
            for record in result.records:
                node = record.get("n")
                if node:
                    try:
                        symbol = self._properties_to_symbol(dict(node))
                        symbols.append(symbol)
                    except Exception as e:
                        logger.warning(f"Failed to process node: {e}")

        return symbols

    async def clear_all_symbols(self) -> bool:
        """
        Clear all symbol nodes from the database.

        WARNING: This is destructive!

        Returns:
            True if successful
        """
        query = """
        MATCH (n)
        WHERE n.type IS NOT NULL
        DETACH DELETE n
        """

        result = await self.client.execute_query(query)
        return result.success
