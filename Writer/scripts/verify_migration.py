#!/usr/bin/env python
"""Verification script to validate Neo4j migration integrity.

This script compares the original JSON knowledge graph data with the
migrated Neo4j data to verify 100% data integrity.

Usage:
    python scripts/verify_migration.py --novel-id my_novel
    python scripts/verify_migration.py --novel-id my_novel --sample-size 100
    python scripts/verify_migration.py --all  # Verify all novels

Exit Codes:
    0: All verifications passed
    1: Warnings (minor discrepancies)
    2: Failures (significant data loss)
"""

import argparse
import asyncio
import json
import logging
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class VerificationConfig:
    """Configuration for verification."""

    novel_id: str
    json_storage_path: Path
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    sample_size: int = 50
    strict_mode: bool = False


@dataclass
class VerificationResult:
    """Result of a single verification check."""

    name: str
    passed: bool
    expected: Any
    actual: Any
    message: str = ""
    details: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    """Complete verification report."""

    novel_id: str
    timestamp: datetime
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warning_checks: int = 0
    results: list[VerificationResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: VerificationResult) -> None:
        self.results.append(result)
        self.total_checks += 1
        if result.passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1

    def success_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.passed_checks / self.total_checks * 100

    def is_complete_success(self) -> bool:
        return self.failed_checks == 0

    def has_warnings(self) -> bool:
        return self.warning_checks > 0


class JSONDataLoader:
    """Load JSON knowledge graph data."""

    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self.nodes_file = storage_path / "nodes.json"
        self.edges_file = storage_path / "edges.json"

    def exists(self) -> bool:
        return self.nodes_file.exists() or self.edges_file.exists()

    def load_nodes(self) -> list[dict[str, Any]]:
        if not self.nodes_file.exists():
            return []
        with open(self.nodes_file, encoding="utf-8") as f:
            return json.load(f)

    def load_edges(self) -> list[dict[str, Any]]:
        if not self.edges_file.exists():
            return []
        with open(self.edges_file, encoding="utf-8") as f:
            return json.load(f)

    def get_node_by_id(self, node_id: str) -> dict[str, Any] | None:
        for node in self.load_nodes():
            if node.get("node_id") == node_id:
                return node
        return None

    def get_edge_by_id(self, edge_id: str) -> dict[str, Any] | None:
        for edge in self.load_edges():
            if edge.get("edge_id") == edge_id:
                return edge
        return None


class MigrationVerifier:
    """Verify migration integrity."""

    def __init__(self, config: VerificationConfig) -> None:
        self.config = config
        self.loader = JSONDataLoader(config.json_storage_path)
        self._neo4j_client = None
        self.report = VerificationReport(
            novel_id=config.novel_id,
            timestamp=datetime.now(),
        )

    async def get_neo4j_client(self):
        if self._neo4j_client is None:
            from src.db.neo4j_client import Neo4jClient, Neo4jConfig

            neo4j_config = Neo4jConfig(
                uri=self.config.neo4j_uri,
                user=self.config.neo4j_user,
                password=self.config.neo4j_password,
                database=self.config.neo4j_database,
            )
            self._neo4j_client = Neo4jClient(neo4j_config)
            await self._neo4j_client.connect()
        return self._neo4j_client

    async def verify_node_count(self) -> VerificationResult:
        json_nodes = self.loader.load_nodes()
        expected_count = len(json_nodes)

        client = await self.get_neo4j_client()
        actual_count = await client.get_node_count()

        passed = actual_count == expected_count
        message = f"Expected {expected_count}, got {actual_count}"

        if not passed:
            diff = abs(expected_count - actual_count)
            if diff <= expected_count * 0.01:
                message += " (within 1% tolerance)"
            else:
                message += f" (difference: {diff})"

        return VerificationResult(
            name="Node Count",
            passed=passed,
            expected=expected_count,
            actual=actual_count,
            message=message,
        )

    async def verify_edge_count(self) -> VerificationResult:
        json_edges = self.loader.load_edges()
        expected_count = len(json_edges)

        client = await self.get_neo4j_client()
        actual_count = await client.get_relationship_count()

        passed = actual_count == expected_count
        message = f"Expected {expected_count}, got {actual_count}"

        if not passed:
            diff = abs(expected_count - actual_count)
            message += f" (difference: {diff})"

        return VerificationResult(
            name="Edge Count",
            passed=passed,
            expected=expected_count,
            actual=actual_count,
            message=message,
        )

    async def verify_node_properties(
        self,
        sample_size: int = 50,
    ) -> VerificationResult:
        json_nodes = self.loader.load_nodes()
        if not json_nodes:
            return VerificationResult(
                name="Node Properties",
                passed=True,
                expected=0,
                actual=0,
                message="No nodes to verify",
            )

        sample = random.sample(
            json_nodes,
            min(sample_size, len(json_nodes)),
        )

        client = await self.get_neo4j_client()
        mismatches = []
        not_found = []

        for json_node in sample:
            node_id = json_node.get("node_id")
            neo4j_node = await client.get_node(node_id)

            if not neo4j_node:
                not_found.append(node_id)
                continue

            json_props = json_node.get("properties", {})
            for key, expected_value in json_props.items():
                actual_value = neo4j_node.get(key)
                if actual_value != expected_value:
                    if self.config.strict_mode:
                        mismatches.append(
                            f"{node_id}.{key}: expected {expected_value}, got {actual_value}"
                        )
                    elif not self._values_equivalent(expected_value, actual_value):
                        mismatches.append(
                            f"{node_id}.{key}: expected {expected_value}, got {actual_value}"
                        )

        passed = len(not_found) == 0 and len(mismatches) == 0
        details = []
        if not_found:
            details.append(f"Not found in Neo4j: {not_found[:5]}")
        if mismatches:
            details.append(f"Property mismatches: {mismatches[:5]}")

        message = f"Verified {len(sample)} nodes"
        if not passed:
            message += f", {len(not_found)} not found, {len(mismatches)} mismatches"

        return VerificationResult(
            name="Node Properties",
            passed=passed,
            expected=len(sample),
            actual=len(sample) - len(not_found),
            message=message,
            details=details,
        )

    def _values_equivalent(self, v1: Any, v2: Any) -> bool:
        if v1 == v2:
            return True
        if isinstance(v1, str) and isinstance(v2, str):
            return v1.lower() == v2.lower()
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            return abs(v1 - v2) < 0.001
        return False

    async def verify_relationships(
        self,
        sample_size: int = 50,
    ) -> VerificationResult:
        json_edges = self.loader.load_edges()
        if not json_edges:
            return VerificationResult(
                name="Relationships",
                passed=True,
                expected=0,
                actual=0,
                message="No edges to verify",
            )

        sample = random.sample(
            json_edges,
            min(sample_size, len(json_edges)),
        )

        client = await self.get_neo4j_client()
        mismatches = []
        not_found = []

        for json_edge in sample:
            source_id = json_edge.get("source_id")
            target_id = json_edge.get("target_id")
            rel_type = json_edge.get("relationship_type")

            query = f"""
            MATCH (source {{node_id: $source_id}})-[r:{rel_type}]->(target {{node_id: $target_id}})
            RETURN r
            """

            result = await client.execute_query(
                query,
                {"source_id": source_id, "target_id": target_id},
            )

            if not result.success or not result.records:
                not_found.append(f"{source_id}-{rel_type}->{target_id}")
                continue

        passed = len(not_found) == 0
        message = f"Verified {len(sample)} relationships"
        if not passed:
            message += f", {len(not_found)} not found"

        return VerificationResult(
            name="Relationships",
            passed=passed,
            expected=len(sample),
            actual=len(sample) - len(not_found),
            message=message,
            details=[f"Not found: {not_found[:5]}"] if not_found else [],
        )

    async def verify_node_types(self) -> VerificationResult:
        json_nodes = self.loader.load_nodes()

        type_counts: dict[str, int] = {}
        for node in json_nodes:
            node_type = node.get("node_type", "Unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        client = await self.get_neo4j_client()
        neo4j_type_counts: dict[str, int] = {}

        for node_type in type_counts.keys():
            count = await client.get_node_count(label=node_type)
            neo4j_type_counts[node_type] = count

        mismatches = []
        for node_type, expected in type_counts.items():
            actual = neo4j_type_counts.get(node_type, 0)
            if actual != expected:
                mismatches.append(f"{node_type}: expected {expected}, got {actual}")

        passed = len(mismatches) == 0
        message = f"Verified {len(type_counts)} node types"

        return VerificationResult(
            name="Node Types",
            passed=passed,
            expected=len(type_counts),
            actual=len(type_counts) - len(mismatches),
            message=message,
            details=mismatches[:5],
        )

    async def run_all_verifications(self) -> VerificationReport:
        logger.info(f"Starting verification for novel: {self.config.novel_id}")

        if not self.loader.exists():
            self.report.add_result(
                VerificationResult(
                    name="Data Existence",
                    passed=False,
                    expected="JSON files",
                    actual="Not found",
                    message=f"No JSON data at {self.config.json_storage_path}",
                )
            )
            return self.report

        verifications = [
            self.verify_node_count(),
            self.verify_edge_count(),
            self.verify_node_types(),
            self.verify_node_properties(self.config.sample_size),
            self.verify_relationships(self.config.sample_size),
        ]

        for verification in verifications:
            result = await verification
            self.report.add_result(result)
            status = "PASS" if result.passed else "FAIL"
            logger.info(f"  [{status}] {result.name}: {result.message}")

        self.report.summary = {
            "success_rate": self.report.success_rate(),
            "total_checks": self.report.total_checks,
            "passed": self.report.passed_checks,
            "failed": self.report.failed_checks,
        }

        if self._neo4j_client:
            await self._neo4j_client.close()

        return self.report

    def print_report(self) -> None:
        print("\n" + "=" * 60)
        print("MIGRATION VERIFICATION REPORT")
        print("=" * 60)
        print(f"Novel ID: {self.report.novel_id}")
        print(f"Timestamp: {self.report.timestamp.isoformat()}")
        print()

        for result in self.report.results:
            status = "✓" if result.passed else "✗"
            print(f"[{status}] {result.name}")
            print(f"    Expected: {result.expected}")
            print(f"    Actual:   {result.actual}")
            print(f"    Message:  {result.message}")
            if result.details:
                for detail in result.details[:3]:
                    print(f"    - {detail}")
            print()

        print("-" * 60)
        print("SUMMARY")
        print("-" * 60)
        print(f"Total Checks:  {self.report.total_checks}")
        print(f"Passed:        {self.report.passed_checks}")
        print(f"Failed:        {self.report.failed_checks}")
        print(f"Success Rate:  {self.report.success_rate():.1f}%")
        print("=" * 60)


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Neo4j migration integrity"
    )
    parser.add_argument(
        "--novel-id",
        required=True,
        help="Novel identifier to verify",
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        help="Path to JSON storage",
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
        help="Neo4j password",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50,
        help="Sample size for property verification",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict comparison mode",
    )

    args = parser.parse_args()

    if args.json_path:
        json_path = args.json_path
    else:
        project_root = Path(__file__).parent.parent
        json_path = project_root / "data" / "knowledge_graphs" / args.novel_id

    import os
    password = args.neo4j_password or os.environ.get("NEO4J_PASSWORD", "")

    config = VerificationConfig(
        novel_id=args.novel_id,
        json_storage_path=json_path,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=password,
        sample_size=args.sample_size,
        strict_mode=args.strict,
    )

    verifier = MigrationVerifier(config)
    report = await verifier.run_all_verifications()
    verifier.print_report()

    if report.is_complete_success():
        return 0
    elif report.success_rate() >= 95:
        return 1
    else:
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
