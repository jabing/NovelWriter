# src/deployment/backup.py
"""Backup and recovery system."""

import json
import logging
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backups of novel data and configuration."""

    def __init__(
        self,
        data_dir: str = "data",
        backup_dir: str = "backups",
        max_backups: int = 10,
    ) -> None:
        """Initialize backup manager.

        Args:
            data_dir: Directory containing data to backup
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep
        """
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, name: str | None = None) -> str:
        """Create a backup of all data.

        Args:
            name: Optional backup name (auto-generated if None)

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"

        logger.info(f"Creating backup: {backup_path}")

        with tarfile.open(backup_path, "w:gz") as tar:
            if self.data_dir.exists():
                tar.add(self.data_dir, arcname="data")

        # Create manifest
        manifest = {
            "name": backup_name,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "size_bytes": backup_path.stat().st_size,
        }

        manifest_path = self.backup_dir / f"{backup_name}.manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Cleanup old backups
        self._cleanup_old_backups()

        logger.info(f"Backup created: {backup_path}")
        return str(backup_path)

    def restore_backup(self, backup_name: str) -> bool:
        """Restore from a backup.

        Args:
            backup_name: Name of backup to restore

        Returns:
            True if successful
        """
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"

        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False

        logger.info(f"Restoring from backup: {backup_path}")

        try:
            # Create a backup of current state before restore
            if self.data_dir.exists() and any(self.data_dir.iterdir()):
                self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            # Remove current data
            if self.data_dir.exists():
                shutil.rmtree(self.data_dir)

            # Extract backup
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=self.data_dir.parent)

            logger.info(f"Restore completed: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    def list_backups(self) -> list[dict[str, Any]]:
        """List all available backups.

        Returns:
            List of backup info dictionaries
        """
        backups = []

        for manifest_file in self.backup_dir.glob("*.manifest.json"):
            with open(manifest_file) as f:
                manifest = json.load(f)

            backup_file = self.backup_dir / f"{manifest['name']}.tar.gz"
            if backup_file.exists():
                manifest["file_exists"] = True
                manifest["file_path"] = str(backup_file)
            else:
                manifest["file_exists"] = False

            backups.append(manifest)

        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup.

        Args:
            backup_name: Name of backup to delete

        Returns:
            True if successful
        """
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        manifest_path = self.backup_dir / f"{backup_name}.manifest.json"

        deleted = False

        if backup_path.exists():
            backup_path.unlink()
            deleted = True

        if manifest_path.exists():
            manifest_path.unlink()
            deleted = True

        if deleted:
            logger.info(f"Deleted backup: {backup_name}")

        return deleted

    def get_backup_info(self, backup_name: str) -> dict[str, Any] | None:
        """Get info about a specific backup.

        Args:
            backup_name: Name of backup

        Returns:
            Backup info or None
        """
        manifest_path = self.backup_dir / f"{backup_name}.manifest.json"

        if not manifest_path.exists():
            return None

        with open(manifest_path) as f:
            return json.load(f)

    def _cleanup_old_backups(self) -> None:
        """Remove old backups exceeding max_backups limit."""
        backups = self.list_backups()

        while len(backups) > self.max_backups:
            oldest = backups.pop()
            self.delete_backup(oldest["name"])
            logger.info(f"Removed old backup: {oldest['name']}")

    def get_backup_stats(self) -> dict[str, Any]:
        """Get backup statistics.

        Returns:
            Statistics dictionary
        """
        backups = self.list_backups()

        total_size = sum(
            b.get("size_bytes", 0)
            for b in backups
            if b.get("file_exists")
        )

        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_backups": self.max_backups,
            "oldest_backup": backups[-1]["timestamp"] if backups else None,
            "newest_backup": backups[0]["timestamp"] if backups else None,
        }


async def scheduled_backup(
    backup_manager: BackupManager,
    interval_hours: int = 24,
) -> None:
    """Run scheduled backups.

    Args:
        backup_manager: BackupManager instance
        interval_hours: Hours between backups
    """
    import asyncio

    while True:
        try:
            backup_manager.create_backup()
            logger.info("Scheduled backup completed")
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")

        await asyncio.sleep(interval_hours * 3600)


# Global backup manager
_backup_manager: BackupManager | None = None


def get_backup_manager() -> BackupManager:
    """Get global backup manager."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
