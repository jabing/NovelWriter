"""Version control system for novel generation history.

Provides git-like functionality for tracking changes to chapters, characters,
plot elements, and world-building across the writing process.
"""

import difflib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.novel_agent.novel.schemas import AgentType, VersionMetadata

logger = logging.getLogger(__name__)


class VersionChangeType(str, Enum):
    """Types of changes in a version."""

    CHAPTER_CREATED = "chapter_created"
    CHAPTER_MODIFIED = "chapter_modified"
    CHAPTER_DELETED = "chapter_deleted"
    CHARACTER_UPDATED = "character_updated"
    PLOT_UPDATED = "plot_updated"
    WORLD_UPDATED = "world_updated"
    METADATA_CHANGED = "metadata_changed"
    CONSISTENCY_FIX = "consistency_fix"


@dataclass
class VersionChange:
    """A single change in a version."""

    change_type: VersionChangeType
    target_id: str  # e.g., "chapter/1", "character/alice", "plot/main_arc"
    old_value: Any | None = None
    new_value: Any | None = None
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Version:
    """A complete version snapshot."""

    version_id: str
    parent_version: str | None
    timestamp: datetime
    author: str
    message: str
    changes: list[VersionChange]

    # Content storage references
    chapter_contents: dict[str, str]  # chapter_number -> content
    state_snapshot: dict[str, Any]  # characters, plot, world data

    # Metadata
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_version_metadata(self) -> VersionMetadata:
        """Convert to Pydantic VersionMetadata schema."""
        return VersionMetadata(
            version_id=self.version_id,
            parent_version=self.parent_version,
            agent_type=AgentType.WRITER,  # Default, can be overridden
            timestamp=self.timestamp,
            changes=[c.description for c in self.changes],
            author=self.author,
            tags=self.tags,
            metadata=self.metadata,
        )

    def get_chapter_content(self, chapter_number: int) -> str | None:
        """Get content for a specific chapter."""
        return self.chapter_contents.get(f"chapter_{chapter_number}")

    def get_character_state(self, character_id: str) -> dict[str, Any] | None:
        """Get state for a specific character."""
        characters = self.state_snapshot.get("characters", {})
        return characters.get(character_id)

    def get_plot_state(self) -> dict[str, Any]:
        """Get plot state."""
        return self.state_snapshot.get("plot", {})

    def get_world_state(self) -> dict[str, Any]:
        """Get world state."""
        return self.state_snapshot.get("world", {})


class DiffResult(BaseModel):
    """Result of a diff operation."""

    unified_diff: str
    html_diff: str | None = None
    changes: list[dict[str, Any]]
    similarity_score: float  # 0.0 to 1.0


class VersionControlSystem:
    """Git-like version control system for novel writing.

    Manages version history, diffs, rollbacks, and branching for
    chapter content and story state.
    """

    def __init__(self, base_path: Path, novel_id: str) -> None:
        """Initialize the version control system.

        Args:
            base_path: Base directory for version storage
            novel_id: Unique identifier for the novel
        """
        self.base_path = Path(base_path)
        self.novel_id = novel_id
        self.versions_path = self.base_path / "novels" / novel_id / "versions"
        self.content_path = self.base_path / "novels" / novel_id / "content"
        self.metadata_path = self.base_path / "novels" / novel_id / "metadata"

        # Ensure directories exist
        self.versions_path.mkdir(parents=True, exist_ok=True)
        self.content_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)

        # In-memory version cache
        self._versions: dict[str, Version] = {}
        self._current_version: str | None = None

        # Load existing versions
        self._load_versions()

    def _generate_version_id(self, parent_version: str | None = None) -> str:
        """Generate a unique version ID."""
        timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
        if parent_version:
            short_parent = parent_version[:8] if len(parent_version) > 8 else parent_version
            return f"v{timestamp}_{short_parent}"
        return f"v{timestamp}"

    def _load_versions(self) -> None:
        """Load all versions from disk."""
        version_files = list(self.versions_path.glob("version_*.json"))

        for version_file in version_files:
            try:
                with open(version_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Parse changes
                changes = []
                for change_data in data.get("changes", []):
                    changes.append(
                        VersionChange(
                            change_type=VersionChangeType(change_data["change_type"]),
                            target_id=change_data["target_id"],
                            old_value=change_data.get("old_value"),
                            new_value=change_data.get("new_value"),
                            description=change_data.get("description", ""),
                            metadata=change_data.get("metadata", {}),
                        )
                    )

                # Parse datetime
                timestamp = datetime.fromisoformat(data["timestamp"])

                version = Version(
                    version_id=data["version_id"],
                    parent_version=data.get("parent_version"),
                    timestamp=timestamp,
                    author=data["author"],
                    message=data["message"],
                    changes=changes,
                    chapter_contents=data.get("chapter_contents", {}),
                    state_snapshot=data.get("state_snapshot", {}),
                    tags=data.get("tags", []),
                    metadata=data.get("metadata", {}),
                )

                self._versions[version.version_id] = version

                # Set as current if it's the most recent
                if (
                    not self._current_version
                    or timestamp > self._versions[self._current_version].timestamp
                ):
                    self._current_version = version.version_id

            except Exception as e:
                logger.error(f"Failed to load version from {version_file}: {e}")

        logger.info(f"Loaded {len(self._versions)} versions for novel {self.novel_id}")

    def _save_version(self, version: Version) -> None:
        """Save a version to disk."""
        # Prepare data for JSON serialization
        version_data = {
            "version_id": version.version_id,
            "parent_version": version.parent_version,
            "timestamp": version.timestamp.isoformat(),
            "author": version.author,
            "message": version.message,
            "changes": [
                {
                    "change_type": change.change_type.value,
                    "target_id": change.target_id,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "description": change.description,
                    "metadata": change.metadata,
                }
                for change in version.changes
            ],
            "chapter_contents": version.chapter_contents,
            "state_snapshot": version.state_snapshot,
            "tags": version.tags,
            "metadata": version.metadata,
        }

        # Save version metadata
        version_file = self.versions_path / f"version_{version.version_id}.json"
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)

        # Save chapter content as separate files (git-like)
        for chapter_key, content in version.chapter_contents.items():
            if content:  # Only save non-empty content
                chapter_file = self.content_path / f"{chapter_key}_{version.version_id}.txt"
                with open(chapter_file, "w", encoding="utf-8") as f:
                    f.write(content)

        # Save state snapshot
        state_file = self.metadata_path / f"state_{version.version_id}.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(version.state_snapshot, f, indent=2, ensure_ascii=False)

        # Update cache
        self._versions[version.version_id] = version
        self._current_version = version.version_id

        logger.debug(f"Saved version {version.version_id}")

    async def commit_chapter(
        self,
        chapter_number: int,
        content: str,
        author: str,
        message: str,
        state_snapshot: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Commit a new version of a chapter.

        Args:
            chapter_number: Chapter number (1-indexed)
            content: Chapter content
            author: Author/agent name
            message: Commit message describing changes
            state_snapshot: Optional story state (characters, plot, world)
            tags: Optional version tags
            metadata: Optional additional metadata

        Returns:
            Version ID of the new commit
        """
        # Generate version ID
        parent_version = self._current_version
        version_id = self._generate_version_id(parent_version)

        # Get previous content for diff
        old_content = ""
        if parent_version and parent_version in self._versions:
            old_version = self._versions[parent_version]
            old_content = old_version.get_chapter_content(chapter_number) or ""

        # Create change record
        changes = []

        # Chapter change
        if not old_content and content:
            change_type = VersionChangeType.CHAPTER_CREATED
            description = f"Created chapter {chapter_number}"
        elif old_content and not content:
            change_type = VersionChangeType.CHAPTER_DELETED
            description = f"Deleted chapter {chapter_number}"
        else:
            change_type = VersionChangeType.CHAPTER_MODIFIED
            # Calculate diff for description
            diff_lines = list(
                difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=f"chapter_{chapter_number}_old",
                    tofile=f"chapter_{chapter_number}_new",
                    lineterm="",
                )
            )
            line_changes = len([l for l in diff_lines if l.startswith("+ ") or l.startswith("- ")])
            description = f"Modified chapter {chapter_number} ({line_changes} lines changed)"

        changes.append(
            VersionChange(
                change_type=change_type,
                target_id=f"chapter/{chapter_number}",
                old_value=old_content if old_content else None,
                new_value=content if content else None,
                description=description,
            )
        )

        # Create version
        version = Version(
            version_id=version_id,
            parent_version=parent_version,
            timestamp=datetime.now(),
            author=author,
            message=message,
            changes=changes,
            chapter_contents={f"chapter_{chapter_number}": content},
            state_snapshot=state_snapshot or {},
            tags=tags or [],
            metadata=metadata or {},
        )

        # Save version
        self._save_version(version)

        logger.info(f"Committed version {version_id} for chapter {chapter_number}")
        return version_id

    async def commit_state_change(
        self,
        change_type: VersionChangeType,
        target_id: str,
        new_state: dict[str, Any],
        author: str,
        message: str,
        old_state: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Commit a change to story state (characters, plot, world).

        Args:
            change_type: Type of state change
            target_id: Target identifier (e.g., "character/alice")
            new_state: New state data
            author: Author/agent name
            message: Commit message
            old_state: Optional previous state for diff
            tags: Optional version tags
            metadata: Optional additional metadata

        Returns:
            Version ID of the new commit
        """
        parent_version = self._current_version
        version_id = self._generate_version_id(parent_version)

        # Create change record
        changes = [
            VersionChange(
                change_type=change_type,
                target_id=target_id,
                old_value=old_state,
                new_value=new_state,
                description=f"{change_type.value}: {target_id}",
            )
        ]

        # Get current state snapshot
        state_snapshot = {}
        if parent_version and parent_version in self._versions:
            state_snapshot = self._versions[parent_version].state_snapshot.copy()

        # Update state snapshot based on target_id
        if target_id.startswith("character/"):
            character_id = target_id.replace("character/", "")
            if "characters" not in state_snapshot:
                state_snapshot["characters"] = {}
            state_snapshot["characters"][character_id] = new_state
        elif target_id.startswith("plot/"):
            plot_id = target_id.replace("plot/", "")
            if "plot" not in state_snapshot:
                state_snapshot["plot"] = {}
            state_snapshot["plot"][plot_id] = new_state
        elif target_id.startswith("world/"):
            world_id = target_id.replace("world/", "")
            if "world" not in state_snapshot:
                state_snapshot["world"] = {}
            state_snapshot["world"][world_id] = new_state

        # Create version
        version = Version(
            version_id=version_id,
            parent_version=parent_version,
            timestamp=datetime.now(),
            author=author,
            message=message,
            changes=changes,
            chapter_contents={},  # No chapter content in state-only commits
            state_snapshot=state_snapshot,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Save version
        self._save_version(version)

        logger.info(f"Committed state change version {version_id} for {target_id}")
        return version_id

    async def get_version(self, version_id: str) -> Version | None:
        """Get a specific version by ID."""
        return self._versions.get(version_id)

    async def get_current_version(self) -> Version | None:
        """Get the current version."""
        if self._current_version:
            return self._versions.get(self._current_version)
        return None

    async def get_version_history(self, limit: int = 50) -> list[Version]:
        """Get version history in chronological order."""
        versions = list(self._versions.values())
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        return versions[:limit]

    async def diff_versions(
        self,
        version_a_id: str,
        version_b_id: str,
        target_id: str | None = None,
    ) -> DiffResult | None:
        """Calculate diff between two versions.

        Args:
            version_a_id: First version ID
            version_b_id: Second version ID
            target_id: Optional specific target to diff (e.g., "chapter/1")

        Returns:
            DiffResult or None if versions not found
        """
        version_a = self._versions.get(version_a_id)
        version_b = self._versions.get(version_b_id)

        if not version_a or not version_b:
            return None

        changes = []
        unified_diffs = []

        # Diff chapter contents
        if not target_id or target_id.startswith("chapter/"):
            # Get chapter number from target_id or diff all chapters
            if target_id and target_id.startswith("chapter/"):
                chapter_num = int(target_id.replace("chapter/", ""))
                chapters_to_diff = [f"chapter_{chapter_num}"]
            else:
                # Diff all chapters present in either version
                all_chapters = set(version_a.chapter_contents.keys()) | set(
                    version_b.chapter_contents.keys()
                )
                chapters_to_diff = sorted(all_chapters)

            for chapter_key in chapters_to_diff:
                content_a = version_a.chapter_contents.get(chapter_key, "")
                content_b = version_b.chapter_contents.get(chapter_key, "")

                if content_a != content_b:
                    # Generate unified diff
                    lines_a = content_a.splitlines(keepends=True)
                    lines_b = content_b.splitlines(keepends=True)

                    diff = list(
                        difflib.unified_diff(
                            lines_a,
                            lines_b,
                            fromfile=f"{chapter_key}_v{version_a_id[:8]}",
                            tofile=f"{chapter_key}_v{version_b_id[:8]}",
                            lineterm="",
                        )
                    )

                    if diff:
                        unified_diffs.append("\n".join(diff))

                        # Calculate similarity
                        matcher = difflib.SequenceMatcher(None, content_a, content_b)
                        similarity = matcher.ratio()

                        changes.append(
                            {
                                "target": chapter_key,
                                "type": "content",
                                "similarity": similarity,
                                "added_lines": sum(
                                    1
                                    for line in diff
                                    if line.startswith("+ ") and not line.startswith("+++")
                                ),
                                "removed_lines": sum(
                                    1
                                    for line in diff
                                    if line.startswith("- ") and not line.startswith("---")
                                ),
                            }
                        )

        # Diff state snapshots
        if not target_id or not target_id.startswith("chapter/"):
            state_a = version_a.state_snapshot
            state_b = version_b.state_snapshot

            # Simple JSON comparison for now
            if state_a != state_b:
                # TODO: Implement more sophisticated state diffing
                changes.append(
                    {
                        "target": "state_snapshot",
                        "type": "state",
                        "description": "State snapshot changed",
                    }
                )

        if not changes:
            # No differences found
            return DiffResult(unified_diff="", changes=[], similarity_score=1.0)

        # Combine all diffs
        unified_diff = "\n\n".join(unified_diffs)

        # Calculate overall similarity
        overall_similarity = 0.0
        if changes:
            similarities = [c.get("similarity", 0.0) for c in changes if "similarity" in c]
            if similarities:
                overall_similarity = sum(similarities) / len(similarities)

        return DiffResult(
            unified_diff=unified_diff, changes=changes, similarity_score=overall_similarity
        )

    async def rollback_to_version(
        self, version_id: str, create_new_version: bool = True
    ) -> str | None:
        """Rollback to a previous version.

        Args:
            version_id: Version to rollback to
            create_new_version: Whether to create a new version for the rollback

        Returns:
            New version ID if create_new_version=True, otherwise None
        """
        target_version = self._versions.get(version_id)
        if not target_version:
            logger.error(f"Cannot rollback: version {version_id} not found")
            return None

        if create_new_version:
            # Create a rollback version
            current_version = await self.get_current_version()
            if current_version:
                # Calculate changes for rollback
                changes = []
                for chapter_key, content in target_version.chapter_contents.items():
                    current_content = current_version.chapter_contents.get(chapter_key, "")
                    if content != current_content:
                        changes.append(
                            VersionChange(
                                change_type=VersionChangeType.CHAPTER_MODIFIED,
                                target_id=f"chapter/{chapter_key.replace('chapter_', '')}",
                                old_value=current_content,
                                new_value=content,
                                description=f"Rollback: restored {chapter_key} to version {version_id[:8]}",
                            )
                        )

                # Create rollback version
                rollback_version_id = self._generate_version_id(self._current_version)
                rollback_version = Version(
                    version_id=rollback_version_id,
                    parent_version=self._current_version,
                    timestamp=datetime.now(),
                    author="system",
                    message=f"Rollback to version {version_id[:8]}",
                    changes=changes,
                    chapter_contents=target_version.chapter_contents.copy(),
                    state_snapshot=target_version.state_snapshot.copy(),
                    tags=["rollback"],
                    metadata={"rollback_target": version_id},
                )

                self._save_version(rollback_version)
                logger.info(f"Created rollback version {rollback_version_id} to {version_id}")
                return rollback_version_id
        else:
            # Direct rollback (dangerous - overwrites current)
            self._current_version = version_id
            logger.warning(f"Direct rollback to version {version_id} (no new version created)")

        return None

    async def create_branch(self, branch_name: str, from_version: str | None = None) -> bool:
        """Create a new branch from a specific version.

        Args:
            branch_name: Name of the new branch
            from_version: Version to branch from (default: current)

        Returns:
            True if branch created successfully
        """
        source_version_id = from_version or self._current_version
        if not source_version_id or source_version_id not in self._versions:
            logger.error("Cannot create branch: source version not found")
            return False

        # Create branch metadata
        branch_file = self.metadata_path / f"branch_{branch_name}.json"
        branch_data = {
            "branch_name": branch_name,
            "created_from": source_version_id,
            "created_at": datetime.now().isoformat(),
            "current_version": source_version_id,
        }

        with open(branch_file, "w", encoding="utf-8") as f:
            json.dump(branch_data, f, indent=2)

        logger.info(f"Created branch '{branch_name}' from version {source_version_id[:8]}")
        return True

    async def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch.

        Args:
            branch_name: Name of the branch to switch to

        Returns:
            True if switch successful
        """
        branch_file = self.metadata_path / f"branch_{branch_name}.json"
        if not branch_file.exists():
            logger.error(f"Cannot switch to branch '{branch_name}': branch not found")
            return False

        try:
            with open(branch_file, encoding="utf-8") as f:
                branch_data = json.load(f)

            current_version_id = branch_data.get("current_version")
            if current_version_id and current_version_id in self._versions:
                self._current_version = current_version_id
                logger.info(
                    f"Switched to branch '{branch_name}' (version {current_version_id[:8]})"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to switch to branch '{branch_name}': {e}")

        return False

    async def get_branch_info(self, branch_name: str) -> dict[str, Any] | None:
        """Get information about a branch."""
        branch_file = self.metadata_path / f"branch_{branch_name}.json"
        if not branch_file.exists():
            return None

        try:
            with open(branch_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read branch info for '{branch_name}': {e}")
            return None

    async def list_branches(self) -> list[str]:
        """List all branches."""
        branch_files = list(self.metadata_path.glob("branch_*.json"))
        branches = []

        for branch_file in branch_files:
            branch_name = branch_file.stem.replace("branch_", "")
            branches.append(branch_name)

        return sorted(branches)

    async def merge_branch(
        self,
        source_branch: str,
        target_branch: str,
        author: str,
        message: str,
    ) -> str | None:
        """Merge changes from one branch into another.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            author: Author/agent name
            message: Merge commit message

        Returns:
            New version ID if merge successful, None otherwise
        """
        # TODO: Implement proper three-way merge
        # For now, simple merge by switching to target branch and committing changes
        logger.warning(f"Merge not fully implemented: {source_branch} -> {target_branch}")

        # Get source branch version
        source_info = await self.get_branch_info(source_branch)
        if not source_info:
            logger.error(f"Cannot merge: source branch '{source_branch}' not found")
            return None

        source_version_id = source_info.get("current_version")
        if not source_version_id:
            logger.error(f"Cannot merge: source branch '{source_branch}' has no current version")
            return None

        # Switch to target branch
        original_branch = await self.get_current_branch() or "main"
        if not await self.switch_branch(target_branch):
            logger.error(f"Cannot merge: failed to switch to target branch '{target_branch}'")
            return None

        # Create merge commit
        # Note: This is a placeholder - proper merge logic needed
        merge_version_id = self._generate_version_id(self._current_version)

        # Get source version
        source_version = self._versions.get(source_version_id)
        if not source_version:
            logger.error(f"Cannot merge: source version {source_version_id} not found")
            return None

        # Create merge changes
        changes = [
            VersionChange(
                change_type=VersionChangeType.METADATA_CHANGED,
                target_id="branch/merge",
                description=f"Merged branch '{source_branch}' into '{target_branch}'",
            )
        ]

        merge_version = Version(
            version_id=merge_version_id,
            parent_version=self._current_version,
            timestamp=datetime.now(),
            author=author,
            message=message,
            changes=changes,
            chapter_contents={},  # TODO: Merge actual content
            state_snapshot={},  # TODO: Merge state
            tags=["merge"],
            metadata={
                "merge_source": source_branch,
                "merge_target": target_branch,
                "source_version": source_version_id,
            },
        )

        self._save_version(merge_version)

        # Update target branch current version
        branch_file = self.metadata_path / f"branch_{target_branch}.json"
        if branch_file.exists():
            try:
                with open(branch_file, encoding="utf-8") as f:
                    branch_data = json.load(f)

                branch_data["current_version"] = merge_version_id
                branch_data["last_merge"] = datetime.now().isoformat()
                branch_data["merged_from"] = source_branch

                with open(branch_file, "w", encoding="utf-8") as f:
                    json.dump(branch_data, f, indent=2)

            except Exception as e:
                logger.error(f"Failed to update branch '{target_branch}' after merge: {e}")

        # Switch back to original branch
        await self.switch_branch(original_branch)

        logger.info(
            f"Created merge commit {merge_version_id[:8]} from {source_branch} to {target_branch}"
        )
        return merge_version_id

    async def get_current_branch(self) -> str | None:
        """Get the name of the current branch."""
        # Simple implementation: check which branch file points to current version
        branch_files = list(self.metadata_path.glob("branch_*.json"))

        for branch_file in branch_files:
            try:
                with open(branch_file, encoding="utf-8") as f:
                    branch_data = json.load(f)

                if branch_data.get("current_version") == self._current_version:
                    return branch_file.stem.replace("branch_", "")
            except Exception:
                continue

        return None

    async def cleanup_old_versions(self, keep_last: int = 100) -> int:
        """Clean up old versions, keeping only the most recent ones.

        Args:
            keep_last: Number of most recent versions to keep

        Returns:
            Number of versions deleted
        """
        # Get all versions sorted by timestamp
        versions = list(self._versions.values())
        versions.sort(key=lambda v: v.timestamp, reverse=True)

        if len(versions) <= keep_last:
            return 0

        # Determine which versions to delete
        versions_to_keep = {v.version_id for v in versions[:keep_last]}
        versions_to_delete = [
            v for v in versions[keep_last:] if v.version_id not in versions_to_keep
        ]

        deleted_count = 0

        for version in versions_to_delete:
            try:
                # Delete version file
                version_file = self.versions_path / f"version_{version.version_id}.json"
                if version_file.exists():
                    version_file.unlink()

                # Delete content files
                for chapter_key in version.chapter_contents.keys():
                    content_file = self.content_path / f"{chapter_key}_{version.version_id}.txt"
                    if content_file.exists():
                        content_file.unlink()

                # Delete state file
                state_file = self.metadata_path / f"state_{version.version_id}.json"
                if state_file.exists():
                    state_file.unlink()

                # Remove from cache
                if version.version_id in self._versions:
                    del self._versions[version.version_id]

                deleted_count += 1

            except Exception as e:
                logger.error(f"Failed to delete version {version.version_id}: {e}")

        # Update current version if it was deleted
        if self._current_version and self._current_version not in self._versions:
            if self._versions:
                # Set to most recent version
                remaining_versions = list(self._versions.values())
                remaining_versions.sort(key=lambda v: v.timestamp, reverse=True)
                self._current_version = remaining_versions[0].version_id
            else:
                self._current_version = None

        logger.info(f"Cleaned up {deleted_count} old versions (kept {keep_last} most recent)")
        return deleted_count


# Factory function for easy creation
def create_version_control(novel_id: str, base_path: Path | None = None) -> VersionControlSystem:
    """Create a version control system for a novel.

    Args:
        novel_id: Unique identifier for the novel
        base_path: Optional base path for storage (default: data/version_control)

    Returns:
        Initialized VersionControlSystem
    """
    if base_path is None:
        # Default to data/version_control in project root
        project_root = Path(__file__).parent.parent.parent
        base_path = project_root / "data" / "version_control"

    return VersionControlSystem(base_path, novel_id)


__all__ = [
    "VersionControlSystem",
    "VersionChangeType",
    "VersionChange",
    "Version",
    "DiffResult",
    "create_version_control",
]
