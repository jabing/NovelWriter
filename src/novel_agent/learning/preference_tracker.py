# src/learning/preference_tracker.py
"""Preference Tracker - Track and analyze user preferences."""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Feedback:
    """A user feedback record."""
    content_id: str
    content_type: str
    feedback_type: str
    feedback_value: str
    comment: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StylePreference:
    """A learned style preference."""
    category: str
    preference: str
    strength: float
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PreferenceTracker:
    """Track and analyze user preferences."""

    DEFAULT_STORAGE_PATH = "data/learning/preferences.json"
    POSITIVE_KEYWORDS = ["good", "great", "excellent", "perfect", "like"]
    NEGATIVE_KEYWORDS = ["bad", "poor", "terrible", "hate"]
    MORE_KEYWORDS = ["more", "increase", "add"]
    LESS_KEYWORDS = ["less", "reduce", "decrease"]

    def __init__(self, storage_path: str | None = None):
        self.storage_path = Path(storage_path or self.DEFAULT_STORAGE_PATH)
        self._feedbacks: list[Feedback] = []
        self._style_preferences: list[StylePreference] = []
        self._load()

    def record_feedback(self, content_id: str, feedback: str, content_type: str) -> None:
        fb_type, fb_value = self._parse_feedback(feedback)
        fb = Feedback(content_id, content_type, fb_type, fb_value,
                      feedback if fb_type == "style" else None, datetime.now().isoformat())
        self._feedbacks.append(fb)
        if fb_type == "style":
            self._extract_style_preference(feedback)
        self._save()

    def record_implicit(self, content_id: str, action: str, content_type: str = "unknown") -> None:
        action_map = {"edited": "needs_improvement", "accepted": "good", "rejected": "bad"}
        fb = Feedback(content_id, content_type, "implicit", action_map.get(action, action),
                      None, datetime.now().isoformat())
        self._feedbacks.append(fb)
        self._save()

    def get_preference_hints(self, content_type: str) -> list[str]:
        hints = []
        for p in self._style_preferences:
            if p.strength > 0.3:
                hints.append(f"{'更多' if p.preference == 'more' else '减少' if p.preference == 'less' else p.preference}{p.category}")
        return hints[:5]

    def get_style_adjustments(self) -> dict[str, str]:
        return {p.category: f"{'增加' if p.preference == 'more' else '减少'}{p.category}"
                for p in self._style_preferences if p.strength > 0.3}

    def analyze_preferences(self) -> dict[str, Any]:
        total = len(self._feedbacks)
        if total == 0:
            return {"total_feedbacks": 0}
        pos = sum(1 for f in self._feedbacks if f.feedback_value in ["good", "positive"])
        return {"total_feedbacks": total, "positive_ratio": pos / total}

    def _parse_feedback(self, fb: str) -> tuple[str, str]:
        fb_lower = fb.lower()
        for k in self.POSITIVE_KEYWORDS:
            if k in fb_lower: return ("explicit", "positive")
        for k in self.NEGATIVE_KEYWORDS:
            if k in fb_lower: return ("explicit", "negative")
        return ("style", fb)

    def _extract_style_preference(self, fb: str) -> None:
        fb_lower = fb.lower()
        pref = "more" if any(k in fb_lower for k in self.MORE_KEYWORDS) else \
               "less" if any(k in fb_lower for k in self.LESS_KEYWORDS) else "custom"
        cats = {"dialogue": ["dialogue", "dialog", "talk"], "description": ["description", "detail"],
                "pacing": ["pacing", "speed"], "emotion": ["emotion", "feeling"]}
        cat = next((c for c, ks in cats.items() if any(k in fb_lower for k in ks)), "general")
        existing = next((p for p in self._style_preferences if p.category == cat and p.preference == pref), None)
        if existing:
            existing.strength = min(1.0, existing.strength + 0.1)
        else:
            self._style_preferences.append(StylePreference(cat, pref, 0.5))

    def _load(self) -> None:
        if not self.storage_path.exists(): return
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                d = json.load(f)
            self._feedbacks = [Feedback(**fb) for fb in d.get("feedbacks", [])]
            self._style_preferences = [StylePreference(**sp) for sp in d.get("style_preferences", [])]
        except: pass

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({"feedbacks": [fb.to_dict() for fb in self._feedbacks],
                      "style_preferences": [sp.to_dict() for sp in self._style_preferences]}, f, ensure_ascii=False)
