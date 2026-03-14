# src/learning/pattern_memory.py
"""Pattern Memory - Store and retrieve successful content patterns."""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """A stored pattern from successful content."""
    content_type: str
    role: str | None
    features: list[str]
    score: float
    content_id: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pattern":
        return cls(**data)


class PatternMemory:
    """Store and retrieve successful content patterns."""

    DEFAULT_STORAGE_PATH = "data/learning/patterns.json"

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or self.DEFAULT_STORAGE_PATH)
        self._patterns: list[Pattern] = []
        self._load()
        logger.info(f"PatternMemory initialized with {len(self._patterns)} patterns")

    def store(self, content_type: str, content: dict[str, Any], score: float,
              content_id: str | None = None, role: str | None = None) -> None:
        features = self._extract_features(content, content_type)
        pattern = Pattern(
            content_type=content_type,
            role=role,
            features=features,
            score=score,
            content_id=content_id or f"{content_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now().isoformat(),
        )
        self._patterns.append(pattern)
        self._save()
        logger.info(f"Stored pattern for {content_type} with score {score}")

    def retrieve_patterns(self, content_type: str, role: str | None = None,
                          min_score: float = 0.0, limit: int = 5) -> list[dict[str, Any]]:
        filtered = [p for p in self._patterns
                   if p.content_type == content_type
                   and (role is None or p.role == role)
                   and p.score >= min_score]
        filtered.sort(key=lambda p: p.score, reverse=True)
        return [p.to_dict() for p in filtered[:limit]]

    def get_successful_features(self, content_type: str, role: str | None = None,
                                min_score: float = 8.0, limit: int = 10) -> list[str]:
        patterns = self.retrieve_patterns(content_type, role, min_score)
        all_features: list[str] = []
        for p in patterns:
            all_features.extend(p.get("features", []))
        feature_counts: dict[str, int] = {}
        for f in all_features:
            feature_counts[f] = feature_counts.get(f, 0) + 1
        sorted_features = sorted(feature_counts.keys(), key=lambda f: feature_counts[f], reverse=True)
        return sorted_features[:limit]

    def _extract_features(self, content: dict[str, Any], content_type: str) -> list[str]:
        features: list[str] = []
        if content_type == "character":
            features.extend(self._extract_character_features(content))
        elif content_type == "outline":
            features.extend(self._extract_outline_features(content))
        return features

    def _extract_character_features(self, content: dict[str, Any]) -> list[str]:
        features: list[str] = []
        personality = content.get("personality", {})
        for trait in personality.get("traits", [])[:3]:
            if isinstance(trait, str):
                features.append(f"性格: {trait[:50]}")
        appearance = content.get("appearance", {})
        for feat in appearance.get("distinctive_features", [])[:2]:
            if isinstance(feat, str):
                features.append(f"特征: {feat[:50]}")
        if content.get("secrets"):
            features.append("有秘密设定")
        if len(str(content.get("background", ""))) > 200:
            features.append("详细背景")
        return features

    def _extract_outline_features(self, content: dict[str, Any]) -> list[str]:
        features: list[str] = []
        if content.get("acts"):
            features.append(f"包含{len(content['acts'])}幕结构")
        for theme in content.get("themes", [])[:3]:
            features.append(f"主题: {theme}")
        return features

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
            self._patterns = [Pattern.from_dict(p) for p in data.get("patterns", [])]
        except (json.JSONDecodeError, KeyError):
            self._patterns = []

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"patterns": [p.to_dict() for p in self._patterns]}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
