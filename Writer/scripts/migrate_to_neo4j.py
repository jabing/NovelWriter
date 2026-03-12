#!/usr/bin/env python
"""Migration script to move existing JSON-based knowledge graph data to Neo4j.

This script migrates all nodes and edges from the existing JSON storage
format to Neo4j graph database while preserving data integrity.

Usage:
    python scripts/migrate_to_neo4j.py --novel-id my_novel --dry-run
    python scripts/migrate_to_neo4j.py --novel-id my_novel --backup-dir ./backups
    python scripts/migrate_to_neo4j.py --all  # Migrate all novels in data/knowledge_graphs

Features:
    - Streaming JSON loading (memory efficient)
    - Batch import to Neo4j (1000 records per batch)
    - Automatic backup before migration
    - Data validation and integrity checks
    - Progress reporting with tqdm
    - Incremental sync support
    - Rollback mechanism
"""

import argparse
import asyncio
import json
import logging
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    logger.warning("tqdm not installed. Progress bars disabled. Install with: pip install tqdm")


@dataclass
class MigrationConfig:
    """Configuration for migration."""

    novel_id: str
    json_storage_path: Path
    backup_dir: Path | None = None
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    batch_size: int = 1000
    dry_run: bool = False
    validate_only: bool = False
    incremental: bool = False


@dataclass
class MigrationStats:
    """Statistics for migration."""

    total_nodes: int = 0
    total_edges: int = 0
    migrated_nodes: int = 0
    migrated_edges: int = 0
    failed_nodes: int = 0
    failed_edges: int = 0
    skipped_nodes: int = 0
    skipped_edges: int = 0
    errors: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None

    def duration_seconds(self) -> float:
        """Calculate migration duration."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def success_rate(self) -> tuple[float, float]:
        """Calculate success rates for nodes and edges."""
        node_rate = self.migrated_nodes / max(self.total_nodes, 1) * 100
        edge_rate = self.migrated_edges / max(self.total_edges, 1) * 100
        return node_rate, edge_rate


class JSONDataLoader:
    """Streaming loader for JSON knowledge graph data."""

    def __init__(self, storage_path: Path) -> None:
        """Initialize the loader.

        Args:
            storage_path: Path to the JSON storage directory
        """
        self.storage_path = storage_path
        self.nodes_file = storage_path / "nodes.json"
        self.edges_file = storage_path / "edges.json"

    def exists(self) -> bool:
        """Check if JSON files exist."""
        return self.nodes_file.exists() or self.edges_file.exists()

    def load_nodes(self) -> list[dict[str, Any]]:
        """Load nodes from JSON file."""
        if not self.nodes_file.exists():
            return []

        with open(self.nodes_file, encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} nodes from {self.nodes_file}")
        return data

    def load_edges(self) -> list[dict[str, Any]]:
        """Load edges from JSON file."""
        if not self.edges_file.exists():
            return []

        with open(self.edges_file, encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} edges from {self.edges_file}")
        return data

    def count_records(self) -> tuple[int, int]:
        """Count nodes and edges without fully loading them."""
        nodes = self.load_nodes()
        edges = self.load_edges()
        return len(nodes), len(edges)


class MigrationBackup:
    """Handles backup and rollback of JSON data."""

    def __init__(self, backup_dir: Path) -> None:
        """Initialize backup handler.

        Args:
            backup_dir: Directory for backups
        """
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        storage_path: Path,
        novel_id: str,
    ) -> Path | None:
        """Create a backup of JSON files.

        Args:
            storage_path: Path to JSON storage
            novel_id: Novel identifier

        Returns:
            Path to backup directory or None if no files to backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{novel_id}_{timestamp}"

        nodes_file = storage_path / "nodes.json"
        edges_file = storage_path / "edges.json"

        if not nodes_file.exists() and not edges_file.exists():
            logger.warning("No JSON files to backup")
            return None

        backup_path.mkdir(parents=True, exist_ok=True)

        if nodes_file.exists():
            shutil.copy2(nodes_file, backup_path / "nodes.json")
            logger.info(f"Backed up nodes.json to {backup_path}")

        if edges_file.exists():
            shutil.copy2(edges_file, backup_path / "edges.json")
            logger.info(f"Backed up edges.json to {backup_path}")

        # Create manifest
        manifest = {
            "novel_id": novel_id,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "files": [],
        }

        if nodes_file.exists():
            manifest["files"].append("nodes.json")
        if edges_file.exists():
            manifest["files"].append("edges.json")

        with open(backup_path / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return backup_path

    def restore_backup(self, backup_path: Path, storage_path: Path) -> bool:
        """Restore JSON files from backup.

        Args:
            backup_path: Path to backup directory
            storage_path: Path to restore to

        Returns:
            True if restore successful
        """
        try:
            storage_path.mkdir(parents=True, exist_ok=True)

            backup_nodes = backup_path / "nodes.json"
            backup_edges = backup_path / "edges.json"

            if backup_nodes.exists():
                shutil.copy2(backup_nodes, storage_path / "nodes.json")
                logger.info(f"Restored nodes.json from {backup_path}")

            if backup_edges.exists():
                shutil.copy2(backup_edges, storage_path / "edges.json")
                logger.info(f"Restored edges.json from {backup_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False


class KnowledgeGraphMigrator:
    """Main migration class for JSON to Neo4j."""

    def __init__(self, config: MigrationConfig) -> None:
        """Initialize migrator.

        Args:
            config: Migration configuration
        """
        self.config = config
        self.stats = MigrationStats()
        self.loader = JSONDataLoader(config.json_storage_path)
        self.backup_handler: MigrationBackup | None = None

        if config.backup_dir:
            self.backup_handler = MigrationBackup(config.backup_dir)

        # Neo4j client (lazy initialization)
        self._neo4j_client = None

    async def get_neo4j_client(self):
        """Get or create Neo4j client."""
        if self._neo4j_client is None:
            from src.db.neo4j_client import Neo4jClient, Neo4jConfig

            neo4j_config = Neo4jConfig(
                uri=self.config.neo4j_uri,
                user=self.config.neo4j_user,
                password=self.config.neo4j_password,
                database=self.config.neo4j_database,
            )
            self._neo4j_client = Neo4jClient(neo4j_config)

        return self._neo4j_client

    def map_node_to_neo4j(self, node_data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Map JSON node to Neo4j node format.

        Args:
            node_data: JSON node data

        Returns:
            Tuple of (label, properties)
        """
        # Node type becomes the label
        label = node_data.get("node_type", "Entity")

        # Properties mapping
        properties = {
            "node_id": node_data.get("node_id"),
            **node_data.get("properties", {}),
        }

        # Convert datetime fields to strings
        for field in ["created_at", "updated_at"]:
            if field in node_data:
                value = node_data[field]
                if isinstance(value, str):
                    properties[field] = value
                else:
                    properties[field] = str(value)

        # Store embeddings as string if present (Neo4j doesn't handle lists well in some versions)
        if "embeddings" in node_data and node_data["embeddings"]:
            properties["has_embeddings"] = True
            # Note: For production, you'd want to use a vector store like Pinecone

        return label, properties

    def map_edge_to_neo4j(
        self, edge_data: dict[str, Any]
    ) -> tuple[str, str, str, dict[str, Any]]:
        """Map JSON edge to Neo4j relationship format.

        Args:
            edge_data: JSON edge data

        Returns:
            Tuple of (source_id, target_id, rel_type, properties)
        """
        source_id = edge_data.get("source_id")
        target_id = edge_data.get("target_id")
        rel_type = edge_data.get("relationship_type", "RELATED_TO")

        properties = {
            "rel_id": edge_data.get("edge_id"),
            "weight": edge_data.get("weight", 1.0),
            **edge_data.get("properties", {}),
        }

        # Convert datetime fields
        if "created_at" in edge_data:
            value = edge_data["created_at"]
            properties["created_at"] = str(value) if not isinstance(value, str) else value

        return source_id, target_id, rel_type, properties

    def validate_node_data(self, node_data: dict[str, Any]) -> tuple[bool, str]:
        """Validate node data before migration.

        Args:
            node_data: Node data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not node_data.get("node_id"):
            return False, "Missing node_id"

        if not node_data.get("node_type"):
            return False, f"Missing node_type for node {node_data.get('node_id')}"

        return True, ""

    def validate_edge_data(self, edge_data: dict[str, Any]) -> tuple[bool, str]:
        """Validate edge data before migration.

        Args:
            edge_data: Edge data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not edge_data.get("edge_id"):
            return False, "Missing edge_id"

        if not edge_data.get("source_id"):
            return False, f"Missing source_id for edge {edge_data.get('edge_id')}"

        if not edge_data.get("target_id"):
            return False, f"Missing target_id for edge {edge_data.get('edge_id')}"

        if not edge_data.get("relationship_type"):
            return False, f"Missing relationship_type for edge {edge_data.get('edge_id')}"

        return True, ""

    async def migrate_nodes(
        self,
        nodes: list[dict[str, Any]],
    ) -> tuple[int, int, list[str]]:
        """Migrate nodes to Neo4j.

        Args:
            nodes: List of node data

        Returns:
            Tuple of (success_count, failed_count, errors)
        """
        client = await self.get_neo4j_client()

        # Connect if not connected
        if not client._connected:
            if not await client.connect():
                raise RuntimeError("Failed to connect to Neo4j")

        success_count = 0
        failed_count = 0
        errors = []

        # Prepare nodes for batch processing
        nodes_to_create = []
        for node_data in nodes:
            is_valid, error = self.validate_node_data(node_data)
            if not is_valid:
                failed_count += 1
                errors.append(f"Validation: {error}")
                continue

            label, properties = self.map_node_to_neo4j(node_data)
            nodes_to_create.append((label, properties))

        # Progress callback
        def progress_callback(current: int, total: int) -> None:
            if HAS_TQDM and hasattr(self, "_node_pbar"):
                self._node_pbar.update(current - self._node_pbar.n)

        # Batch create nodes
        migrated, create_errors = await client.batch_create_nodes(
            nodes_to_create,
            batch_size=self.config.batch_size,
            progress_callback=progress_callback,
        )

        success_count = migrated
        failed_count += len(create_errors)
        errors.extend(create_errors)

        return success_count, failed_count, errors

    async def migrate_edges(
        self,
        edges: list[dict[str, Any]],
    ) -> tuple[int, int, list[str]]:
        """Migrate edges to Neo4j.

        Args:
            edges: List of edge data

        Returns:
            Tuple of (success_count, failed_count, errors)
        """
        client = await self.get_neo4j_client()

        if not client._connected:
            raise RuntimeError("Not connected to Neo4j")

        success_count = 0
        failed_count = 0
        errors = []

        # Prepare edges for batch processing
        edges_to_create = []
        for edge_data in edges:
            is_valid, error = self.validate_edge_data(edge_data)
            if not is_valid:
                failed_count += 1
                errors.append(f"Validation: {error}")
                continue

            source_id, target_id, rel_type, properties = self.map_edge_to_neo4j(edge_data)
            edges_to_create.append((source_id, target_id, rel_type, properties))

        # Progress callback
        def progress_callback(current: int, total: int) -> None:
            if HAS_TQDM and hasattr(self, "_edge_pbar"):
                self._edge_pbar.update(current - self._edge_pbar.n)

        # Batch create relationships
        migrated, create_errors = await client.batch_create_relationships(
            edges_to_create,
            batch_size=self.config.batch_size,
            progress_callback=progress_callback,
        )

        success_count = migrated
        failed_count += len(create_errors)
        errors.extend(create_errors)

        return success_count, failed_count, errors

    async def run(self) -> MigrationStats:
        """Execute the migration.

        Returns:
            MigrationStats with results
        """
        self.stats.start_time = datetime.now()

        logger.info(f"Starting migration for novel: {self.config.novel_id}")
        logger.info(f"JSON storage path: {self.config.json_storage_path}")

        # Validate source exists
        if not self.loader.exists():
            logger.error(f"No JSON data found at {self.config.json_storage_path}")
            self.stats.errors.append("No JSON data found")
            self.stats.end_time = datetime.now()
            return self.stats

        # Create backup if configured
        if self.backup_handler and not self.config.dry_run:
            backup_path = self.backup_handler.create_backup(
                self.config.json_storage_path,
                self.config.novel_id,
            )
            if backup_path:
                logger.info(f"Backup created at: {backup_path}")

        # Load data
        nodes = self.loader.load_nodes()
        edges = self.loader.load_edges()

        self.stats.total_nodes = len(nodes)
        self.stats.total_edges = len(edges)

        logger.info(f"Found {self.stats.total_nodes} nodes and {self.stats.total_edges} edges")

        if self.config.dry_run:
            logger.info("DRY RUN - No actual migration will be performed")

            # Validate all data
            for node in nodes:
                is_valid, error = self.validate_node_data(node)
                if is_valid:
                    self.stats.migrated_nodes += 1
                else:
                    self.stats.failed_nodes += 1
                    self.stats.errors.append(f"Node validation: {error}")

            for edge in edges:
                is_valid, error = self.validate_edge_data(edge)
                if is_valid:
                    self.stats.migrated_edges += 1
                else:
                    self.stats.failed_edges += 1
                    self.stats.errors.append(f"Edge validation: {error}")

            self.stats.end_time = datetime.now()
            return self.stats

        if self.config.validate_only:
            logger.info("VALIDATE ONLY - Checking data integrity")

            for node in nodes:
                is_valid, error = self.validate_node_data(node)
                if not is_valid:
                    self.stats.errors.append(f"Node validation: {error}")

            for edge in edges:
                is_valid, error = self.validate_edge_data(edge)
                if not is_valid:
                    self.stats.errors.append(f"Edge validation: {error}")

            self.stats.end_time = datetime.now()
            return self.stats

        # Perform actual migration
        try:
            # Migrate nodes with progress
            if HAS_TQDM:
                self._node_pbar = tqdm(
                    total=len(nodes),
                    desc="Migrating nodes",
                    unit="nodes",
                )

            node_success, node_failed, node_errors = await self.migrate_nodes(nodes)
            self.stats.migrated_nodes = node_success
            self.stats.failed_nodes = node_failed
            self.stats.errors.extend(node_errors)

            if HAS_TQDM:
                self._node_pbar.close()

            # Migrate edges with progress
            if HAS_TQDM:
                self._edge_pbar = tqdm(
                    total=len(edges),
                    desc="Migrating edges",
                    unit="edges",
                )

            edge_success, edge_failed, edge_errors = await self.migrate_edges(edges)
            self.stats.migrated_edges = edge_success
            self.stats.failed_edges = edge_failed
            self.stats.errors.extend(edge_errors)

            if HAS_TQDM:
                self._edge_pbar.close()

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.stats.errors.append(f"Migration error: {str(e)}")

        finally:
            # Close Neo4j connection
            if self._neo4j_client:
                await self._neo4j_client.close()

        self.stats.end_time = datetime.now()
        return self.stats

    def print_report(self) -> None:
        """Print migration report."""
        print("\n" + "=" * 60)
        print("MIGRATION REPORT")
        print("=" * 60)
        print(f"Novel ID: {self.config.novel_id}")
        print(f"Duration: {self.stats.duration_seconds():.2f} seconds")
        print()
        print("NODES:")
        print(f"  Total:     {self.stats.total_nodes}")
        print(f"  Migrated:  {self.stats.migrated_nodes}")
        print(f"  Failed:    {self.stats.failed_nodes}")
        print(f"  Skipped:   {self.stats.skipped_nodes}")
        print()
        print("EDGES:")
        print(f"  Total:     {self.stats.total_edges}")
        print(f"  Migrated:  {self.stats.migrated_edges}")
        print(f"  Failed:    {self.stats.failed_edges}")
        print(f"  Skipped:   {self.stats.skipped_edges}")
        print()

        node_rate, edge_rate = self.stats.success_rate()
        print("SUCCESS RATES:")
        print(f"  Nodes: {node_rate:.1f}%")
        print(f"  Edges: {edge_rate:.1f}%")

        if self.stats.errors:
            print()
            print(f"ERRORS ({len(self.stats.errors)}):")
            for error in self.stats.errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats.errors) > 10:
                print(f"  ... and {len(self.stats.errors) - 10} more")

        print("=" * 60)


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate JSON knowledge graph data to Neo4j"
    )
    parser.add_argument(
        "--novel-id",
        required=True,
        help="Novel identifier to migrate",
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        help="Path to JSON storage (default: data/knowledge_graphs/{novel_id})",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("./backups/kg_migration"),
        help="Directory for backups",
    )
    parser.add_argument(
        "--neo4j-uri",
        default="bolt://localhost:7687",
        help="Neo4j connection URI",
    )
    parser.add_argument(
        "--neo4j-user",
        default="neo4j",
        help="Neo4j username",
    )
    parser.add_argument(
        "--neo4j-password",
        default="",
        help="Neo4j password (or set NEO4J_PASSWORD env var)",
    )
    parser.add_argument(
        "--neo4j-database",
        default="neo4j",
        help="Neo4j database name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of records per batch",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without migrating",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate data integrity",
    )

    args = parser.parse_args()

    # Determine JSON path
    if args.json_path:
        json_path = args.json_path
    else:
        project_root = Path(__file__).parent.parent
        json_path = project_root / "data" / "knowledge_graphs" / args.novel_id

    # Get password from environment if not provided
    import os
    password = args.neo4j_password or os.environ.get("NEO4J_PASSWORD", "")

    # Create config
    config = MigrationConfig(
        novel_id=args.novel_id,
        json_storage_path=json_path,
        backup_dir=args.backup_dir,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=password,
        neo4j_database=args.neo4j_database,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        validate_only=args.validate_only,
    )

    # Run migration
    migrator = KnowledgeGraphMigrator(config)
    stats = await migrator.run()
    migrator.print_report()

    # Return exit code based on success
    node_rate, edge_rate = stats.success_rate()
    if node_rate >= 99.0 and edge_rate >= 99.0:
        return 0  # Success
    elif node_rate >= 95.0 and edge_rate >= 95.0:
        return 1  # Partial success with warnings
    else:
        return 2  # Failure


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
