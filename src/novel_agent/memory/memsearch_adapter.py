# src/memory/memsearch_adapter.py
"""MemSearch adapter implementing BaseMemory interface."""
import asyncio
import logging
from pathlib import Path
from typing import Any

# Optional import for memsearch - allows running without it
try:
    from memsearch import MemSearch
    MEMSEARCH_AVAILABLE = True
except ImportError:
    MEMSEARCH_AVAILABLE = False
    MemSearch = None  # type: ignore[misc,assignment]

from src.novel_agent.memory.base import BaseMemory, MemoryEntry

logger = logging.getLogger(__name__)


class ContextLevel:
    """Context levels for tiered loading."""
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"


class MemSearchAdapter(BaseMemory):
    """Adapter for memsearch providing semantic memory capabilities."""

    DEFAULT_BASE_PATH = "data/openviking"
    DEFAULT_EMBEDDING_PROVIDER = "local"
    DEFAULT_MILVUS_URI = "~/.memsearch/milvus.db"

    def __init__(
        self,
        base_path: str | None = None,
        namespace: str = "default",
        embedding_provider: str | None = None,
        milvus_uri: str | None = None,
        collection: str = "novel_memory",
    ) -> None:
        super().__init__(namespace=namespace)
        self.base_path = Path(base_path or self.DEFAULT_BASE_PATH)
        self._file_lock = asyncio.Lock()
        self._indexed = False
        self._mem = MemSearch(
            paths=[str(self.base_path / "memory")],
            embedding_provider=embedding_provider or self.DEFAULT_EMBEDDING_PROVIDER,
            milvus_uri=milvus_uri or self.DEFAULT_MILVUS_URI,
            collection=collection,
        )
        self._ensure_directories()
        logger.info("MemSearchAdapter initialized")

    def _ensure_directories(self) -> None:
        for d in [
            self.base_path / "memory" / "characters" / "main",
            self.base_path / "memory" / "characters" / "supporting",
            self.base_path / "memory" / "plot",
            self.base_path / "memory" / "world",
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        clean = key.lstrip("/")
        p = self.base_path / clean
        return p.with_suffix(".md") if not p.suffix else p

    def _path_to_key(self, path: Path) -> str:
        # Resolve both paths to absolute to handle WSL2/Windows path differences
        abs_path = path.resolve()
        abs_base = self.base_path.resolve()
        rel = abs_path.relative_to(abs_base)
        k = "/" + str(rel).replace("\\", "/")
        return k[:-3] if k.endswith(".md") else k
        rel = path.relative_to(self.base_path)
        k = "/" + str(rel).replace("\\", "/")
        return k[:-3] if k.endswith(".md") else k

    def _value_to_markdown(self, key: str, value: Any, metadata: dict | None) -> str:
        import yaml
        fm = {"key": key, "namespace": self.namespace}
        if metadata:
            fm["metadata"] = metadata
        lines = ["---", yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip(), "---", ""]
        if isinstance(value, dict):
            title = value.get("name", value.get("title", key.split("/")[-1]))
            lines.append(f"# {title}")
            lines.append("")
            for k, v in value.items():
                if k in ("name", "title"):
                    continue
                lines.append(f"## {k.replace('_', ' ').title()}")
                lines.append("")
                if isinstance(v, list):
                    for item in v:
                        lines.append(f"- {item}")
                elif isinstance(v, dict):
                    for sk, sv in v.items():
                        lines.append(f"- **{sk}**: {sv}")
                else:
                    lines.append(str(v))
                lines.append("")
        else:
            lines.append(str(value))
        return "\n".join(lines)

    def _markdown_to_value(self, content: str) -> tuple[Any, dict | None]:
        import yaml
        metadata = None
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1])
                    metadata = fm.get("metadata")
                    body = parts[2].strip()
                except yaml.YAMLError:
                    pass
        value = self._parse_body(body)
        return value, metadata

    def _parse_body(self, body: str) -> Any:
        lines = body.split("\n")
        result = {}
        section = None
        content = []
        for line in lines:
            if line.startswith("# "):
                if section and content:
                    result[section] = self._parse_content(content)
                section = "name"
                content = [line[2:].strip()]
            elif line.startswith("## "):
                if section and content:
                    result[section] = self._parse_content(content)
                section = line[3:].strip().lower().replace(" ", "_")
                content = []
            else:
                content.append(line)
        if section and content:
            result[section] = self._parse_content(content)
        if len(result) == 1 and "name" in result:
            return result["name"]
        return result if result else body

    def _parse_content(self, lines: list) -> Any:
        items = [l.strip()[2:] for l in lines if l.strip().startswith("- ")]
        if items:
            return items
        return "\n".join(lines).strip()

    async def _ensure_indexed(self) -> None:
        if not self._indexed:
            await self._mem.index()
            self._indexed = True

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        file_path = self._key_to_path(key)
        async with self._file_lock:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = self._value_to_markdown(key, value, metadata)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        await self._mem.index_file(file_path)
        logger.debug(f"Stored: {key}")

    async def retrieve(self, key: str) -> MemoryEntry | None:
        file_path = self._key_to_path(key)
        async with self._file_lock:
            if not file_path.exists():
                return None
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                value, metadata = self._markdown_to_value(content)
                return MemoryEntry(key=key, value=value, metadata=metadata or {})
            except Exception as e:
                logger.warning(f"Failed to load {key}: {e}")
                return None

    async def search(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        await self._ensure_indexed()
        try:
            results = await self._mem.search(query, top_k=limit)
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []
        entries = []
        for r in results:
            sp = Path(r["source"])
            key = self._path_to_key(sp)
            value, metadata = self._markdown_to_value(r["content"])
            if metadata is None:
                metadata = {}
            metadata["score"] = r.get("score", 0)
            entries.append(MemoryEntry(key=key, value=value, metadata=metadata))
        return entries

    async def delete(self, key: str) -> bool:
        file_path = self._key_to_path(key)
        async with self._file_lock:
            if not file_path.exists():
                return False
            file_path.unlink()
        await self._mem.index()
        return True

    async def list_keys(self, prefix: str = "") -> list[str]:
        keys = []
        memory_dir = self.base_path / "memory"
        async with self._file_lock:
            for md_file in memory_dir.rglob("*.md"):
                key = self._path_to_key(md_file)
                if not prefix or key.startswith(prefix):
                    keys.append(key)
        return sorted(keys)

    async def get_context(
        self,
        level: str = ContextLevel.L0,
        context_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        context = {}
        if context_keys:
            for key in context_keys:
                entry = await self.retrieve(key)
                if entry:
                    context[key] = entry.value
        else:
            await self._ensure_indexed()
            if level == ContextLevel.L0:
                queries = ["main character protagonist", "current plot"]
                limit = 5
            elif level == ContextLevel.L1:
                queries = ["characters plot world", "supporting"]
                limit = 15
            else:
                queries = ["all characters plot world settings"]
                limit = 50
            seen = set()
            for q in queries:
                for e in await self.search(q, limit=limit):
                    if e.key not in seen:
                        context[e.key] = e.value
                        seen.add(e.key)
        return context

    async def retrieve_batch(self, keys: list[str]) -> dict[str, MemoryEntry]:
        results = {}
        for key in keys:
            entry = await self.retrieve(key)
            if entry:
                results[key] = entry
        return results

    def close(self) -> None:
        self._mem.close()
