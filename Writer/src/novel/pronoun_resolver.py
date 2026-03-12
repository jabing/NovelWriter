"""Pronoun resolution system for novel text.

This module provides functionality to resolve pronouns (he, she, they, etc.)
to specific character names based on context and recent mentions.
"""

import re
from dataclasses import dataclass


@dataclass
class CharacterMention:
    """Represents a character mention in text."""

    name: str
    position: int
    gender: str = "unknown"
    is_plural: bool = False


class PronounResolver:
    """Resolves pronouns to character names based on context."""

    MALE_PRONOUNS = {"he", "him", "his", "himself"}
    FEMALE_PRONOUNS = {"she", "her", "hers", "herself"}
    NEUTRAL_PRONOUNS = {"they", "them", "their", "theirs", "themself"}
    PLURAL_PRONOUNS = {"they", "them", "their", "theirs", "themselves"}

    MALE_INDICATORS = {
        "sir",
        "lord",
        "king",
        "prince",
        "duke",
        "master",
        "mr",
        "mister",
        "father",
        "son",
        "brother",
        "uncle",
    }
    FEMALE_INDICATORS = {
        "lady",
        "queen",
        "princess",
        "duchess",
        "mistress",
        "ms",
        "mrs",
        "miss",
        "madam",
        "mother",
        "daughter",
        "sister",
        "aunt",
    }

    TITLES = {
        "Sir",
        "Lady",
        "Lord",
        "King",
        "Queen",
        "Prince",
        "Princess",
        "Duke",
        "Duchess",
        "Master",
        "Mistress",
        "Doctor",
        "Dr",
        "Captain",
        "Commander",
        "General",
    }

    def __init__(self, max_distance: int = 3):
        self.max_distance = max_distance
        self._mentions: list[CharacterMention] = []

    def extract_characters(self, text: str) -> list[str]:
        """Extract character names from text."""
        characters = []
        sentences = self._split_into_sentences(text)

        for sent_idx, sentence in enumerate(sentences):
            # Pattern 1: Title + Name
            title_pattern = r"\b(Sir|Lady|Lord|King|Queen|Prince|Princess|Duke|Duchess|Master|Mistress|Doctor|Dr|Captain|Commander|General)\s+([A-Z][a-zA-Z]+)"
            for match in re.finditer(title_pattern, sentence, re.IGNORECASE):
                full_name = f"{match.group(1)} {match.group(2)}"
                gender = self._infer_gender_from_title(match.group(1))
                self._add_mention(full_name, sent_idx, gender)
                if full_name not in characters:
                    characters.append(full_name)

            # Pattern 2: Capitalized names (skip if preceded by a title)
            name_pattern = r"\b([A-Z][a-z]+)\b"
            for match in re.finditer(name_pattern, sentence):
                name = match.group(1)
                if name in self.TITLES:
                    continue
                start_pos = match.start()
                context = sentence[max(0, start_pos - 20) : start_pos]
                if re.search(
                    r"\b(Sir|Lady|Lord|King|Queen|Prince|Princess|Duke|Duchess)\s+$",
                    context,
                    re.IGNORECASE,
                ):
                    continue
                if self._is_likely_name(name):
                    gender = self._infer_gender_from_name(name)
                    self._add_mention(name, sent_idx, gender)
                    if name not in characters:
                        characters.append(name)

        return characters

    def resolve_pronouns(self, text: str) -> dict[str, str]:
        """Resolve pronouns in text to character names."""
        self.extract_characters(text)

        resolutions = {}
        sentences = self._split_into_sentences(text)

        for sent_idx, sentence in enumerate(sentences):
            words = re.findall(r"\b\w+\b", sentence)
            for word_idx, word in enumerate(words):
                lower_word = word.lower()
                if self._is_pronoun(lower_word):
                    antecedent = self._find_antecedent(sent_idx, lower_word)
                    if antecedent:
                        context = f"{sent_idx}:{word_idx}"
                        resolutions[f"{word}_{context}"] = antecedent

        return resolutions

    def replace_pronouns(self, text: str, max_replacements: int | None = None) -> str:
        """Replace pronouns with character names in text."""
        self._mentions = []
        sentences = self._split_into_sentences(text)
        result_sentences = []
        replacement_count = 0

        for sent_idx, sentence in enumerate(sentences):
            self._extract_mentions_from_sentence(sentence, sent_idx)
            words = re.findall(r"\b\w+\b", sentence)
            new_words = []

            for word in words:
                lower_word = word.lower()
                if self._is_pronoun(lower_word):
                    if max_replacements is None or replacement_count < max_replacements:
                        antecedent = self._find_antecedent(sent_idx, lower_word)
                        if antecedent:
                            new_words.append(
                                antecedent if word[0].isupper() else antecedent.lower()
                            )
                            replacement_count += 1
                        else:
                            new_words.append(word)
                    else:
                        new_words.append(word)
                else:
                    new_words.append(word)

            result_sentences.append(" ".join(new_words))

        return " ".join(result_sentences)

    def get_last_mention(
        self, gender: str | None = None, position: int | None = None
    ) -> CharacterMention | None:
        """Get the most recent character mention."""
        if position is None:
            position = float("inf")

        candidates = [
            m
            for m in self._mentions
            if m.position < position
            and (gender is None or m.gender == gender or m.gender == "unknown")
        ]

        return max(candidates, key=lambda m: m.position) if candidates else None

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _add_mention(self, name: str, position: int, gender: str = "unknown") -> None:
        """Add a character mention."""
        for mention in self._mentions:
            if mention.name == name and mention.position == position:
                return
        self._mentions.append(CharacterMention(name=name, position=position, gender=gender))

    def _extract_mentions_from_sentence(self, sentence: str, sent_idx: int) -> None:
        """Extract character mentions from a single sentence."""
        title_pattern = r"\b(Sir|Lady|Lord|King|Queen|Prince|Princess|Duke|Duchess|Master|Mistress|Doctor|Dr|Captain|Commander|General)\s+([A-Z][a-zA-Z]+)"
        for match in re.finditer(title_pattern, sentence, re.IGNORECASE):
            full_name = f"{match.group(1)} {match.group(2)}"
            gender = self._infer_gender_from_title(match.group(1))
            self._add_mention(full_name, sent_idx, gender)

        name_pattern = r"\b([A-Z][a-z]+)\b"
        for match in re.finditer(name_pattern, sentence):
            name = match.group(1)
            if name in self.TITLES:
                continue
            start_pos = match.start()
            context = sentence[max(0, start_pos - 20) : start_pos]
            if re.search(
                r"\b(Sir|Lady|Lord|King|Queen|Prince|Princess|Duke|Duchess)\s+$",
                context,
                re.IGNORECASE,
            ):
                continue
            if self._is_likely_name(name):
                gender = self._infer_gender_from_name(name)
                self._add_mention(name, sent_idx, gender)

    def _is_pronoun(self, word: str) -> bool:
        """Check if a word is a pronoun we can resolve."""
        lower = word.lower()
        return (
            lower in self.MALE_PRONOUNS
            or lower in self.FEMALE_PRONOUNS
            or lower in self.NEUTRAL_PRONOUNS
        )

    def _find_antecedent(self, position: int, pronoun: str) -> str | None:
        """Find the most likely antecedent for a pronoun."""
        lower_pronoun = pronoun.lower()

        required_gender = None
        if lower_pronoun in self.MALE_PRONOUNS:
            required_gender = "male"
        elif lower_pronoun in self.FEMALE_PRONOUNS:
            required_gender = "female"

        required_plural = lower_pronoun in self.PLURAL_PRONOUNS

        # Filter candidates by distance and gender compatibility
        candidates = [
            m
            for m in self._mentions
            if m.position < position
            and (position - m.position) <= self.max_distance
            and (required_gender is None or m.gender == required_gender or m.gender == "unknown")
        ]

        if not candidates:
            return None

        def score_mention(mention: CharacterMention) -> float:
            score = 0.0
            distance = position - mention.position
            score -= distance * 10
            if required_gender and mention.gender == required_gender:
                score += 50
            if mention.is_plural == required_plural:
                score += 30
            return score

        candidates.sort(key=score_mention, reverse=True)
        return candidates[0].name if candidates else None

    def _infer_gender_from_title(self, title: str) -> str:
        """Infer gender from a title."""
        lower_title = title.lower()
        if lower_title in self.MALE_INDICATORS:
            return "male"
        elif lower_title in self.FEMALE_INDICATORS:
            return "female"
        return "unknown"

    def _infer_gender_from_name(self, name: str) -> str:
        """Infer gender from a name (heuristic)."""
        lower_name = name.lower()
        if lower_name.endswith(("el", "or", "an", "er", "on")):
            return "male"
        if lower_name.endswith(("a", "e", "i", "y")):
            return "female"
        return "unknown"

    def _is_likely_name(self, word: str) -> bool:
        """Check if a word is likely a name (not a common word)."""
        if word in self.TITLES:
            return False

        common_words = {
            "the",
            "and",
            "but",
            "for",
            "with",
            "from",
            "this",
            "that",
            "these",
            "those",
            "they",
            "them",
            "their",
            "there",
            "then",
            "than",
            "when",
            "where",
            "what",
            "who",
            "how",
            "why",
            "which",
            "while",
            "although",
            "because",
            "since",
            "until",
            "unless",
            "about",
            "above",
            "across",
            "after",
            "against",
            "along",
            "among",
            "around",
            "before",
            "behind",
            "below",
            "beneath",
            "beside",
            "between",
            "beyond",
            "during",
            "inside",
            "outside",
            "under",
            "upon",
            "within",
            "without",
            "chapter",
            "scene",
            "morning",
            "evening",
            "night",
            "day",
            "time",
            "place",
            "way",
        }

        return word.lower() not in common_words and len(word) > 2


def resolve_pronouns_in_text(text: str, max_distance: int = 3) -> dict[str, str]:
    """Convenience function to resolve pronouns in text."""
    resolver = PronounResolver(max_distance=max_distance)
    return resolver.resolve_pronouns(text)


def replace_pronouns_in_text(text: str, max_distance: int = 3) -> str:
    """Convenience function to replace pronouns with names."""
    resolver = PronounResolver(max_distance=max_distance)
    return resolver.replace_pronouns(text)
