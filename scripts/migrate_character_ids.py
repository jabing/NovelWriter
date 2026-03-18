#!/usr/bin/env python
"""Migration script to add role_id to existing projects.

Usage:
    python scripts/migrate_character_ids.py --project <path> [--dry-run] [--rollback]
"""

import argparse
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime

from src.novel_agent.novel.character_registry import CharacterRegistry

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description="Migrate project to add role_id to characters")
    parser.add_argument("--project", required=True, help="Path to project directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--rollback", action="store_true", help="Restore from backup")
    args = parser.parse_args()

    project_path = Path(args.project)

    if args.rollback:
        rollback_migration(project_path)
        return

    migrate_project(project_path, dry_run=args.dry_run)


def migrate_project(project_path: Path, dry_run: bool = False) -> dict:
    """Migrate project to add role_id to characters.

    Args:
        project_path: Path to project directory
        dry_run: If True, preview changes without applying

    Returns:
        Migration report dict
    """
    # Create backup before any changes (unless dry-run)
    if not dry_run:
        backup_path = create_backup(project_path)
        logger.info(f"Backup created at: {backup_path}")
    else:
        backup_path = None

    # Load existing character data
    characters_path = project_path / "characters"
    registry_path = characters_path / "registry.json"

    # Initialize registry
    registry = CharacterRegistry()

    report = {
        "timestamp": datetime.now().isoformat(),
        "project": str(project_path),
        "dry_run": dry_run,
        "characters_processed": 0,
        "role_ids_assigned": [],
        "errors": [],
    }

    if not registry_path.exists():
        logger.info("No registry.json found, creating new one")
    else:
        # Load existing registry
        registry.load(registry_path)
        logger.info(f"Loaded existing registry with {len(registry)} entries")

    # Process individual character files
    if not characters_path.exists():
        report["errors"].append(f"Characters directory not found: {characters_path}")
        logger.error(f"Characters directory not found: {characters_path}")
        return report

    # Find all character files (JSON files in characters directory)
    character_files = list(characters_path.glob("*.json"))
    logger.info(f"Found {len(character_files)} character files")

    for char_file in character_files:
        if char_file.name == "registry.json":
            continue

        try:
            with open(char_file, "r", encoding="utf-8") as f:
                char_data = json.load(f)
        except json.JSONDecodeError as e:
            report["errors"].append(f"Failed to parse {char_file.name}: {e}")
            logger.error(f"Failed to parse {char_file.name}: {e}")
            continue

        # Get character name
        name = char_data.get("name", char_file.stem)
        old_role_id = char_data.get("role_id")

        if old_role_id:
            # Already has role_id, skip
            logger.debug(f"Skipping {name}: already has role_id={old_role_id}")
            continue

        # Generate new role_id
        new_role_id = registry.get_or_create(name=name)
        char_data["role_id"] = new_role_id

        # Save updated character file (unless dry-run)
        if not dry_run:
            with open(char_file, "w", encoding="utf-8") as f:
                json.dump(char_data, f, indent=2, ensure_ascii=False)

        report["characters_processed"] += 1
        report["role_ids_assigned"].append(
            {"file": char_file.name, "name": name, "role_id": new_role_id}
        )

        logger.info(f"Assigned role_id={new_role_id} to {name}")

    # Save updated registry (unless dry-run)
    if not dry_run:
        registry.save(registry_path)

    # Log summary
    logger.info(f"Migration complete: {report['characters_processed']} characters processed")

    return report


def create_backup(project_path: Path) -> Path:
    """Create backup of project data.

    Args:
        project_path: Path to project directory

    Returns:
        Path to backup directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = project_path / "backups" / f"pre_migration_{timestamp}"

    # Copy characters directory to backup
    characters_source = project_path / "characters"
    characters_backup = backup_path / "characters"

    if characters_source.exists():
        shutil.copytree(characters_source, characters_backup)
        logger.info(f"Backed up characters directory to {characters_backup}")
    else:
        logger.warning(f"Characters directory not found: {characters_source}")

    return backup_path


def rollback_migration(project_path: Path) -> bool:
    """Rollback to pre-migration state.

    Args:
        project_path: Path to project directory

    Returns:
        True if rollback succeeded, False otherwise
    """
    backups_path = project_path / "backups"

    if not backups_path.exists():
        logger.error("No backups directory found")
        return False

    # Find most recent backup
    backup_dirs = sorted(backups_path.glob("pre_migration_*"), reverse=True)

    if not backup_dirs:
        logger.error("No backup directories found")
        return False

    latest_backup = backup_dirs[0]
    logger.info(f"Found backup: {latest_backup}")

    # Restore characters directory
    characters_backup = latest_backup / "characters"
    characters_target = project_path / "characters"

    if not characters_backup.exists():
        logger.error(f"Backup characters directory not found: {characters_backup}")
        return False

    # Remove current characters directory
    if characters_target.exists():
        shutil.rmtree(characters_target)
        logger.info(f"Removed current characters directory: {characters_target}")

    # Restore from backup
    shutil.copytree(characters_backup, characters_target)
    logger.info(f"Restored characters from backup: {characters_backup}")

    # Clean up the backup directory after successful restore
    shutil.rmtree(latest_backup)
    logger.info(f"Removed backup after restore: {latest_backup}")

    logger.info("Rollback completed successfully")
    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
