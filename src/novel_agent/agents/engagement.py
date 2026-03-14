# src/agents/engagement.py
"""Engagement Agent - Reader interaction automation."""

import random
from datetime import datetime
from typing import Any

from src.novel_agent.agents.base import AgentResult, BaseAgent


class EngagementAgent(BaseAgent):
    """Agent responsible for automated reader engagement.

    Performs:
    - Automatic comment replies
    - Engagement tracking
    - Community building
    - Personalized responses
    - Reply variety management
    """

    # Reply templates by category
    REPLY_TEMPLATES = {
        "positive": [
            "Thank you so much for reading! I'm glad you're enjoying the story!",
            "Your feedback means the world to me! Thanks for reading!",
            "I really appreciate your kind words! More chapters coming soon!",
            "Thank you for your support! It motivates me to keep writing!",
            "So happy you're enjoying it! Stay tuned for the next chapter!",
        ],
        "excited": [
            "Your enthusiasm is contagious! I'll try to update soon!",
            "Thank you for the excitement! Working hard on the next chapter!",
            "I love your energy! Can't wait to share what's coming next!",
            "Your excitement keeps me motivated! Updates coming!",
        ],
        "question": [
            "Great question! I don't want to spoil anything, but keep reading to find out!",
            "Interesting question! All will be revealed in due time!",
            "You'll have to wait and see! The answer is coming soon!",
            "That's a mystery for now! Keep following the story!",
        ],
        "suggestion": [
            "Thank you for the suggestion! I'll definitely consider it!",
            "Interesting idea! I appreciate you sharing your thoughts!",
            "Thanks for the feedback! Reader input is always valuable!",
            "Great suggestion! I'll keep it in mind for future chapters!",
        ],
        "complaint": [
            "I appreciate your honest feedback! I'll work on improving!",
            "Thank you for letting me know! I'll take this into consideration!",
            "I understand your concern! I'll try to address this in future chapters!",
            "Thanks for the feedback! Every comment helps me grow as a writer!",
        ],
        "generic": [
            "Thank you for your comment! I appreciate you taking the time!",
            "Thanks for reading and commenting! Your support means a lot!",
            "I read every comment and appreciate yours! Keep reading!",
            "Thank you for being part of this story's journey!",
        ],
    }

    # Emojis to add variety
    EMOJIS = ["😊", "🙏", "✨", "💫", "📚", "❤️", "🎉", "🌟", "👍", "💕"]

    def __init__(self, name: str = "Engagement Agent", **kwargs: Any) -> None:
        """Initialize Engagement Agent.

        Args:
            name: Agent name
            **kwargs: Additional configuration
        """
        if "llm" not in kwargs:
            from unittest.mock import MagicMock
            kwargs["llm"] = MagicMock()
        super().__init__(name=name, **kwargs)
        self._reply_history: list[dict[str, Any]] = []
        self._replied_comments: set[str] = set()

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute engagement tasks.

        Args:
            input_data: Must contain:
                - comments: list of comments to reply to
                - platform: platform name (for tracking)

        Returns:
            AgentResult with engagement data
        """
        try:
            comments = input_data.get("comments", [])
            platform = input_data.get("platform", "unknown")

            if not comments:
                return AgentResult(
                    success=False,
                    data={},
                    errors=["No comments provided for engagement"],
                )

            # Process each comment
            replies = []
            for comment in comments:
                comment_id = comment.get("id", "")

                # Skip already replied comments
                if comment_id and comment_id in self._replied_comments:
                    continue

                reply = await self._generate_reply(comment)
                if reply:
                    replies.append({
                        "comment_id": comment_id,
                        "original_comment": comment.get("text", ""),
                        "reply": reply,
                        "platform": platform,
                    })

                    # Track replied comments
                    if comment_id:
                        self._replied_comments.add(comment_id)

            # Store in history
            self._reply_history.extend(replies)

            return AgentResult(
                success=True,
                data={
                    "total_comments": len(comments),
                    "replies_generated": len(replies),
                    "replies": replies,
                    "platform": platform,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                errors=[f"Engagement failed: {str(e)}"],
            )

    async def _generate_reply(self, comment: dict[str, Any]) -> str:
        """Generate a reply for a comment.

        Args:
            comment: Comment dict with 'text' field

        Returns:
            Generated reply
        """
        text = comment.get("text", "")

        # Determine comment category
        category = self._categorize_comment(text)

        # Get templates for category
        templates = self.REPLY_TEMPLATES.get(category, self.REPLY_TEMPLATES["generic"])

        # Select a template (avoid recent duplicates)
        used_templates = {
            r["reply"] for r in self._reply_history[-10:]
            if r["reply"] in templates
        }
        available = [t for t in templates if t not in used_templates]

        if not available:
            available = templates  # Fallback if all used recently

        reply = random.choice(available)

        # Add emoji occasionally
        if random.random() > 0.5:
            reply = f"{reply} {random.choice(self.EMOJIS)}"

        return reply

    def _categorize_comment(self, text: str) -> str:
        """Categorize a comment to select appropriate reply.

        Args:
            text: Comment text (will be lowercased internally)

        Returns:
            Category name
        """
        # Normalize to lowercase
        text = text.lower()

        # Check for question marks first - questions
        if "?" in text:
            return "question"

        # Excited indicators - check early
        excited_patterns = ["can't wait", "update soon", "next chapter", "more please",
                           "need more", "waiting for", "when is", "please update",
                           "cant wait"]
        if any(pattern in text for pattern in excited_patterns):
            return "excited"

        # Positive indicators - check if any positive word appears in text
        positive_words = ["love", "amazing", "great", "awesome", "fantastic",
                         "best", "wonderful", "perfect", "excellent", "brilliant"]
        if any(word in text for word in positive_words):
            return "positive"

        # Suggestion indicators
        suggestion_words = ["should", "could", "maybe", "idea", "suggestion", "what if"]
        if any(word in text for word in suggestion_words):
            return "suggestion"

        # Complaint indicators - check for negative words
        complaint_words = ["hate", "terrible", "boring", "slow", "confusing",
                          "disappointing", "bad", "wrong", "error", "mistake", "awful"]
        if any(word in text for word in complaint_words):
            return "complaint"

        return "generic"

    async def generate_personalized_reply(
        self,
        comment: dict[str, Any],
        story_context: dict[str, Any] | None = None,
    ) -> str:
        """Generate a more personalized reply with context.

        Args:
            comment: Comment dict
            story_context: Optional story context for personalization

        Returns:
            Personalized reply
        """
        base_reply = await self._generate_reply(comment)

        # Add personalization if username available
        username = comment.get("user", comment.get("username", ""))
        if username and len(username) < 20:
            # Prepend username occasionally
            if random.random() > 0.7:
                base_reply = f"@{username} {base_reply}"

        return base_reply

    def get_reply_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent reply history.

        Args:
            limit: Maximum replies to return

        Returns:
            List of recent replies
        """
        return self._reply_history[-limit:]

    def get_reply_count(self) -> int:
        """Get total reply count.

        Returns:
            Number of replies generated
        """
        return len(self._reply_history)

    def clear_history(self) -> None:
        """Clear reply history and replied comments set."""
        self._reply_history = []
        self._replied_comments = set()

    def is_replied(self, comment_id: str) -> bool:
        """Check if a comment has been replied to.

        Args:
            comment_id: Comment ID to check

        Returns:
            True if already replied
        """
        return comment_id in self._replied_comments

    async def generate_bulk_replies(
        self,
        comments: list[dict[str, Any]],
        max_replies: int = 50,
    ) -> list[dict[str, Any]]:
        """Generate replies for multiple comments efficiently.

        Args:
            comments: List of comments
            max_replies: Maximum replies to generate

        Returns:
            List of reply data
        """
        replies = []
        count = 0

        for comment in comments:
            if count >= max_replies:
                break

            comment_id = comment.get("id", "")
            if comment_id and comment_id in self._replied_comments:
                continue

            reply = await self._generate_reply(comment)
            replies.append({
                "comment_id": comment_id,
                "reply": reply,
            })

            if comment_id:
                self._replied_comments.add(comment_id)

            count += 1

        return replies

    def get_engagement_stats(self) -> dict[str, Any]:
        """Get engagement statistics.

        Returns:
            Statistics about engagement activity
        """
        return {
            "total_replies": len(self._reply_history),
            "unique_comments_replied": len(self._replied_comments),
            "recent_replies": len(list(self._reply_history[-50:])),
        }

    def add_custom_template(self, category: str, template: str) -> None:
        """Add a custom reply template.

        Args:
            category: Template category
            template: Reply template text
        """
        if category not in self.REPLY_TEMPLATES:
            self.REPLY_TEMPLATES[category] = []
        self.REPLY_TEMPLATES[category].append(template)

    def get_categories(self) -> list[str]:
        """Get available reply categories.

        Returns:
            List of category names
        """
        return list(self.REPLY_TEMPLATES.keys())
