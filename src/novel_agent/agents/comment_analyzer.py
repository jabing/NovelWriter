# src/agents/comment_analyzer.py
"""Comment Analyzer Agent - Reader feedback analysis."""

import re
from collections import Counter
from datetime import datetime
from typing import Any

from src.novel_agent.agents.base import AgentResult, BaseAgent


class CommentAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing reader comments.

    Performs:
    - Comment collection from platforms
    - Sentiment analysis (positive, negative, neutral)
    - Key theme extraction
    - Improvement suggestions generation
    - Reader engagement metrics
    """

    # Positive sentiment indicators
    POSITIVE_WORDS = {
        "love", "amazing", "great", "awesome", "fantastic", "excellent",
        "wonderful", "brilliant", "perfect", "beautiful", "incredible",
        "outstanding", "superb", "magnificent", "enjoyed", "best",
        "favorite", "addictive", "gripping", "captivating", "engaging",
        "can't wait", "hooked", "obsessed", "binge", "recommend",
    }

    # Negative sentiment indicators
    NEGATIVE_WORDS = {
        "hate", "terrible", "awful", "bad", "poor", "boring", "slow",
        "confusing", "disappointing", "waste", "worst", "horrible",
        "annoying", "frustrating", "predictable", "cliche", "dumb",
        "stupid", "weak", "flat", "rushed", "plot hole", "plot holes",
    }

    # Common themes/topics to extract
    THEME_KEYWORDS = {
        "characters": ["character", "protagonist", "villain", "mc", "hero", "heroine", "side character"],
        "plot": ["plot", "story", "storyline", "narrative", "twist", "ending", "climax"],
        "pacing": ["pacing", "fast", "slow", "rushed", "drag", "dragged"],
        "writing": ["writing", "prose", "style", "description", "dialogue", "dialog"],
        "worldbuilding": ["world", "setting", "universe", "magic system", "lore", "background"],
        "romance": ["romance", "ship", "couple", "relationship", "love interest", "chemistry"],
        "action": ["action", "fight", "battle", "combat", "scene", "battles"],
        "emotion": ["emotional", "cry", "tears", "feel", "heart", "sad", "happy"],
    }

    def __init__(self, name: str = "Comment Analyzer Agent", **kwargs: Any) -> None:
        """Initialize Comment Analyzer Agent.

        Args:
            name: Agent name
            **kwargs: Additional configuration
        """
        if "llm" not in kwargs:
            from unittest.mock import MagicMock
            kwargs["llm"] = MagicMock()
        super().__init__(name=name, **kwargs)
        self._last_analysis: dict[str, Any] = {}

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute comment analysis.

        Args:
            input_data: Must contain:
                - comments: list of comment dicts with 'text' field
                Or:
                - platform: platform name
                - story_id: story identifier

        Returns:
            AgentResult with analysis data
        """
        try:
            comments = input_data.get("comments", [])

            if not comments:
                return AgentResult(
                    success=False,
                    data={},
                    errors=["No comments provided for analysis"],
                )

            # Analyze sentiment
            sentiment_analysis = self._analyze_sentiment(comments)

            # Extract themes
            theme_analysis = self._extract_themes(comments)

            # Extract keywords
            keyword_analysis = self._extract_keywords(comments)

            # Calculate engagement metrics
            engagement_metrics = self._calculate_engagement(comments)

            # Generate improvement suggestions
            suggestions = await self._generate_suggestions(
                sentiment_analysis, theme_analysis, keyword_analysis
            )

            result_data = {
                "total_comments": len(comments),
                "sentiment": sentiment_analysis,
                "themes": theme_analysis,
                "keywords": keyword_analysis,
                "engagement": engagement_metrics,
                "suggestions": suggestions,
                "analysis_timestamp": datetime.now().isoformat(),
            }

            self._last_analysis = result_data

            return AgentResult(
                success=True,
                data=result_data,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Comment analysis failed: {str(e)}"],
            )

    def _analyze_sentiment(self, comments: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze sentiment of comments.

        Args:
            comments: List of comment dicts

        Returns:
            Sentiment analysis results
        """
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        sentiment_details = []

        for comment in comments:
            text = comment.get("text", "").lower()
            words = set(re.findall(r'\b\w+\b', text))

            # Count sentiment matches
            positive_matches = len(words & self.POSITIVE_WORDS)
            negative_matches = len(words & self.NEGATIVE_WORDS)

            # Determine sentiment
            if positive_matches > negative_matches:
                sentiment = "positive"
                positive_count += 1
            elif negative_matches > positive_matches:
                sentiment = "negative"
                negative_count += 1
            else:
                sentiment = "neutral"
                neutral_count += 1

            sentiment_details.append({
                "comment_id": comment.get("id"),
                "sentiment": sentiment,
                "positive_words": list(words & self.POSITIVE_WORDS),
                "negative_words": list(words & self.NEGATIVE_WORDS),
            })

        total = len(comments)
        return {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "positive_percentage": round(positive_count / total * 100, 1) if total > 0 else 0,
            "negative_percentage": round(negative_count / total * 100, 1) if total > 0 else 0,
            "neutral_percentage": round(neutral_count / total * 100, 1) if total > 0 else 0,
            "overall_sentiment": self._get_overall_sentiment(
                positive_count, negative_count, neutral_count
            ),
            "details": sentiment_details[:20],  # Limit details for performance
        }

    def _get_overall_sentiment(
        self, positive: int, negative: int, neutral: int
    ) -> str:
        """Determine overall sentiment.

        Args:
            positive: Positive comment count
            negative: Negative comment count
            neutral: Neutral comment count

        Returns:
            Overall sentiment label
        """
        total = positive + negative + neutral
        if total == 0:
            return "unknown"

        positive_ratio = positive / total

        if positive_ratio >= 0.7:
            return "very_positive"
        elif positive_ratio >= 0.5:
            return "positive"
        elif positive_ratio >= 0.3:
            return "mixed"
        elif negative > positive:
            return "negative"
        else:
            return "neutral"

    def _extract_themes(self, comments: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common themes from comments.

        Args:
            comments: List of comment dicts

        Returns:
            Theme analysis results
        """
        theme_counts: dict[str, int] = dict.fromkeys(self.THEME_KEYWORDS, 0)
        theme_examples: dict[str, list[str]] = {theme: [] for theme in self.THEME_KEYWORDS}

        for comment in comments:
            text = comment.get("text", "").lower()

            for theme, keywords in self.THEME_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        theme_counts[theme] += 1
                        if len(theme_examples[theme]) < 3:
                            # Extract snippet around keyword
                            idx = text.find(keyword)
                            start = max(0, idx - 20)
                            end = min(len(text), idx + len(keyword) + 20)
                            snippet = text[start:end].strip()
                            if snippet not in theme_examples[theme]:
                                theme_examples[theme].append(snippet)
                        break  # Only count once per comment

        # Sort by frequency
        sorted_themes = sorted(
            theme_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "theme_counts": dict(sorted_themes),
            "top_themes": [t[0] for t in sorted_themes[:5] if t[1] > 0],
            "theme_examples": theme_examples,
        }

    def _extract_keywords(self, comments: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract common keywords from comments.

        Args:
            comments: List of comment dicts

        Returns:
            Keyword analysis results
        """
        # Collect all words
        all_words: list[str] = []
        for comment in comments:
            text = comment.get("text", "").lower()
            words = re.findall(r'\b[a-z]{3,}\b', text)  # Words with 3+ letters
            all_words.extend(words)

        # Stop words to exclude
        stop_words = {
            "the", "and", "this", "that", "with", "for", "are", "was",
            "were", "been", "have", "has", "had", "will", "would", "could",
            "should", "from", "they", "them", "their", "there", "here",
            "what", "when", "where", "which", "while", "about", "just",
            "really", "very", "much", "some", "more", "also", "into",
        }

        # Filter and count
        filtered_words = [w for w in all_words if w not in stop_words]
        word_counts = Counter(filtered_words)

        # Get top keywords
        top_keywords = word_counts.most_common(20)

        return {
            "top_keywords": [{"word": w, "count": c} for w, c in top_keywords],
            "unique_words": len(word_counts),
            "total_words": len(filtered_words),
        }

    def _calculate_engagement(self, comments: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate engagement metrics.

        Args:
            comments: List of comment dicts

        Returns:
            Engagement metrics
        """
        if not comments:
            return {
                "average_length": 0,
                "total_votes": 0,
                "unique_users": 0,
            }

        # Calculate metrics
        lengths = [len(c.get("text", "")) for c in comments]
        votes = [c.get("votes", c.get("upvotes", 0)) for c in comments]

        unique_users = set()
        for comment in comments:
            user = comment.get("user", comment.get("username", ""))
            if user:
                unique_users.add(user)

        return {
            "average_length": round(sum(lengths) / len(lengths), 1) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "min_length": min(lengths) if lengths else 0,
            "total_votes": sum(votes),
            "unique_users": len(unique_users),
            "comments_per_user": round(len(comments) / len(unique_users), 1) if unique_users else 0,
        }

    async def _generate_suggestions(
        self,
        sentiment: dict[str, Any],
        themes: dict[str, Any],
        keywords: dict[str, Any],
    ) -> list[str]:
        """Generate improvement suggestions based on analysis.

        Args:
            sentiment: Sentiment analysis results
            themes: Theme analysis results
            keywords: Keyword analysis results

        Returns:
            List of suggestions
        """
        suggestions = []

        # Based on sentiment
        overall = sentiment.get("overall_sentiment", "")
        if overall == "negative":
            suggestions.append(
                "Reader sentiment is predominantly negative. "
                "Review recent chapters for common complaints."
            )
        elif overall == "very_positive":
            suggestions.append(
                "Excellent reader reception! Keep doing what you're doing."
            )

        # Based on themes
        top_themes = themes.get("top_themes", [])
        if "pacing" in top_themes:
            suggestions.append(
                "Readers are discussing pacing. Consider reviewing chapter lengths and plot progression."
            )
        if "characters" in top_themes:
            suggestions.append(
                "Character development is a hot topic. Ensure character arcs remain consistent."
            )

        # Based on negative percentage
        neg_pct = sentiment.get("negative_percentage", 0)
        if neg_pct > 20:
            suggestions.append(
                f"High negative feedback ({neg_pct}%). "
                "Consider addressing reader concerns in author notes."
            )

        if not suggestions:
            suggestions.append(
                "Overall feedback is positive. Continue engaging with readers."
            )

        return suggestions

    def get_last_analysis(self) -> dict[str, Any]:
        """Get the last analysis results.

        Returns:
            Last analysis data or empty dict
        """
        return self._last_analysis

    async def analyze_single_comment(self, comment: dict[str, Any]) -> dict[str, Any]:
        """Analyze a single comment.

        Args:
            comment: Comment dict with 'text' field

        Returns:
            Analysis of the single comment
        """
        text = comment.get("text", "").lower()
        words = set(re.findall(r'\b\w+\b', text))

        # Sentiment
        positive_matches = words & self.POSITIVE_WORDS
        negative_matches = words & self.NEGATIVE_WORDS

        if len(positive_matches) > len(negative_matches):
            sentiment = "positive"
        elif len(negative_matches) > len(positive_matches):
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Themes
        detected_themes = []
        for theme, keywords in self.THEME_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                detected_themes.append(theme)

        return {
            "comment_id": comment.get("id"),
            "sentiment": sentiment,
            "positive_words": list(positive_matches),
            "negative_words": list(negative_matches),
            "themes": detected_themes,
            "length": len(text),
        }

    def get_sentiment_trends(
        self,
        comments: list[dict[str, Any]],
        group_by: str = "chapter",
    ) -> dict[str, Any]:
        """Get sentiment trends over time/chapters.

        Args:
            comments: List of comments with metadata
            group_by: How to group ('chapter', 'date')

        Returns:
            Sentiment trends data
        """
        grouped: dict[str, dict[str, int]] = {}

        for comment in comments:
            key = comment.get(group_by, "unknown")
            if key not in grouped:
                grouped[key] = {"positive": 0, "negative": 0, "neutral": 0}

            # Simple sentiment detection
            text = comment.get("text", "").lower()
            words = set(re.findall(r'\b\w+\b', text))

            pos = len(words & self.POSITIVE_WORDS)
            neg = len(words & self.NEGATIVE_WORDS)

            if pos > neg:
                grouped[key]["positive"] += 1
            elif neg > pos:
                grouped[key]["negative"] += 1
            else:
                grouped[key]["neutral"] += 1

        return {
            "grouped_by": group_by,
            "trends": grouped,
        }
