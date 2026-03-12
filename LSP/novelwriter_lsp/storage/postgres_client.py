import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from novelwriter_lsp.types import BaseSymbol, SymbolType

logger = logging.getLogger(__name__)


@dataclass
class PostgresConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "novelwriter"
    user: str = "postgres"
    password: str = ""
    max_pool_size: int = 10
    connection_timeout: float = 30.0
    max_retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class SymbolResult:
    success: bool
    symbol: BaseSymbol | None = None
    error: str | None = None


@dataclass
class QueryResult:
    success: bool
    records: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


class PostgresClient:
    def __init__(self, config: PostgresConfig | None = None) -> None:
        self.config = config or PostgresConfig()
        self._pool = None
        self._connected = False

    async def connect(self) -> bool:
        try:
            from asyncpg import create_pool

            self._pool = await create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=1,
                max_size=self.config.max_pool_size,
                timeout=self.config.connection_timeout,
            )

            await self._execute_simple("SELECT 1")
            self._connected = True
            logger.info(
                f"Connected to PostgreSQL at {self.config.host}:{self.config.port}/{self.config.database}"
            )
            return True

        except ImportError:
            logger.error("asyncpg package not installed. Install with: pip install asyncpg>=0.29.0")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self._connected = False
            return False

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._connected = False
            logger.info("PostgreSQL connection closed")

    @asynccontextmanager
    async def connection(self):
        if not self._connected or not self._pool:
            raise RuntimeError("Not connected to PostgreSQL. Call connect() first.")

        async with self._pool.acquire() as conn:
            yield conn

    async def _execute_simple(self, query: str) -> None:
        if not self._pool:
            raise RuntimeError("Not connected to PostgreSQL. Call connect() first.")

        async with self._pool.acquire() as conn:
            await conn.execute(query)

    async def execute_query(
        self,
        query: str,
        parameters: list[Any] | None = None,
    ) -> QueryResult:
        if not self._connected:
            return QueryResult(success=False, error="Not connected to PostgreSQL")

        params = parameters or []
        attempts = 0

        while attempts < self.config.max_retry_attempts:
            try:
                async with self.connection() as conn:
                    records = []
                    rows = await conn.fetch(query, *params)
                    for row in rows:
                        records.append(dict(row))

                    return QueryResult(success=True, records=records)

            except Exception as e:
                attempts += 1
                if attempts >= self.config.max_retry_attempts:
                    logger.error(f"Query failed after {attempts} attempts: {e}")
                    return QueryResult(success=False, error=str(e))

                await asyncio.sleep(self.config.retry_delay)
                logger.warning(
                    f"Query failed, retrying ({attempts}/{self.config.max_retry_attempts}): {e}"
                )

        return QueryResult(success=False, error="Max retry attempts exceeded")

    async def save_symbol(self, symbol: BaseSymbol) -> SymbolResult:
        if not self._connected:
            return SymbolResult(success=False, error="Not connected to PostgreSQL")

        try:
            def_uri = symbol.definition_uri
            def_line = symbol.definition_range.get("line") if symbol.definition_range else None
            def_start = (
                symbol.definition_range.get("start_char") if symbol.definition_range else None
            )
            def_end = symbol.definition_range.get("end_char") if symbol.definition_range else None

            metadata_json = json.dumps(symbol.metadata)

            query = """
            INSERT INTO symbols (
                id, type, name, novel_id, definition_uri,
                definition_line, definition_start_char, definition_end_char,
                metadata, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (id) DO UPDATE SET
                type = EXCLUDED.type,
                name = EXCLUDED.name,
                novel_id = EXCLUDED.novel_id,
                definition_uri = EXCLUDED.definition_uri,
                definition_line = EXCLUDED.definition_line,
                definition_start_char = EXCLUDED.definition_start_char,
                definition_end_char = EXCLUDED.definition_end_char,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at
            """

            now = datetime.now()
            params = [
                symbol.id,
                symbol.type.value,
                symbol.name,
                symbol.novel_id,
                def_uri,
                def_line,
                def_start,
                def_end,
                metadata_json,
                now,
                now,
            ]

            async with self.connection() as conn:
                await conn.execute(query, *params)

            return SymbolResult(success=True, symbol=symbol)

        except Exception as e:
            logger.error(f"Failed to save symbol {symbol.id}: {e}")
            return SymbolResult(success=False, error=str(e))

    async def load_symbol_by_id(self, symbol_id: str) -> SymbolResult:
        if not self._connected:
            return SymbolResult(success=False, error="Not connected to PostgreSQL")

        try:
            query = "SELECT * FROM symbols WHERE id = $1"
            result = await self.execute_query(query, [symbol_id])

            if not result.success or not result.records:
                return SymbolResult(success=True, symbol=None)

            record = result.records[0]
            symbol = self._record_to_symbol(record)
            return SymbolResult(success=True, symbol=symbol)

        except Exception as e:
            logger.error(f"Failed to load symbol {symbol_id}: {e}")
            return SymbolResult(success=False, error=str(e))

    async def find_symbols_by_novel(self, novel_id: str) -> list[BaseSymbol]:
        if not self._connected:
            return []

        try:
            query = "SELECT * FROM symbols WHERE novel_id = $1 ORDER BY type, name"
            result = await self.execute_query(query, [novel_id])

            if not result.success:
                return []

            symbols = []
            for record in result.records:
                symbol = self._record_to_symbol(record)
                if symbol:
                    symbols.append(symbol)

            return symbols

        except Exception as e:
            logger.error(f"Failed to find symbols for novel {novel_id}: {e}")
            return []

    async def update_symbol(self, symbol: BaseSymbol) -> SymbolResult:
        return await self.save_symbol(symbol)

    async def delete_symbol(self, symbol_id: str) -> bool:
        if not self._connected:
            return False

        try:
            query = "DELETE FROM symbols WHERE id = $1"
            async with self.connection() as conn:
                result = await conn.execute(query, symbol_id)
                return "DELETE 1" in result or "DELETE 0" in result

        except Exception as e:
            logger.error(f"Failed to delete symbol {symbol_id}: {e}")
            return False

    async def ensure_tables_exist(self) -> bool:
        if not self._connected:
            return False

        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS symbols (
                id VARCHAR(255) PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                novel_id VARCHAR(255) NOT NULL,
                definition_uri VARCHAR(500),
                definition_line INTEGER,
                definition_start_char INTEGER,
                definition_end_char INTEGER,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            create_index_queries = [
                "CREATE INDEX IF NOT EXISTS idx_symbols_novel ON symbols(novel_id)",
                "CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type)",
                "CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)",
                "CREATE INDEX IF NOT EXISTS idx_symbols_metadata ON symbols USING GIN(metadata)",
            ]

            async with self.connection() as conn:
                await conn.execute(create_table_query)
                for idx_query in create_index_queries:
                    await conn.execute(idx_query)

            logger.info("Ensured symbols table and indexes exist")
            return True

        except Exception as e:
            logger.error(f"Failed to ensure tables exist: {e}")
            return False

    def _record_to_symbol(self, record: dict[str, Any]) -> BaseSymbol | None:
        try:
            symbol_type = SymbolType(record["type"])

            metadata = {}
            if record.get("metadata"):
                if isinstance(record["metadata"], str):
                    metadata = json.loads(record["metadata"])
                else:
                    metadata = record["metadata"]

            definition_range = {}
            if record.get("definition_line") is not None:
                definition_range["line"] = record["definition_line"]
            if record.get("definition_start_char") is not None:
                definition_range["start_char"] = record["definition_start_char"]
            if record.get("definition_end_char") is not None:
                definition_range["end_char"] = record["definition_end_char"]

            return BaseSymbol(
                id=record["id"],
                type=symbol_type,
                name=record["name"],
                novel_id=record["novel_id"],
                definition_uri=record.get("definition_uri", ""),
                definition_range=definition_range,
                references=[],
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Failed to convert record to symbol: {e}")
            return None

    async def health_check(self) -> dict[str, Any]:
        try:
            await self._execute_simple("SELECT 1")

            count_result = await self.execute_query("SELECT COUNT(*) AS count FROM symbols", [])
            symbol_count = 0
            if count_result.success and count_result.records:
                symbol_count = count_result.records[0].get("count", 0)

            return {
                "connected": self._connected,
                "healthy": True,
                "symbol_count": symbol_count,
                "database": self.config.database,
                "host": self.config.host,
                "port": self.config.port,
            }
        except Exception as e:
            return {
                "connected": False,
                "healthy": False,
                "error": str(e),
            }
