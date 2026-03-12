# src/studio/chat/message.py
"""Message handling for chat interface."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    """Role of message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """A single chat message."""
    role: MessageRole
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    agent: str | None = None
    command: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_display(self) -> str:
        """Format message for display."""
        if self.role == MessageRole.USER:
            return f"[dim]用户[/dim]: {self.content}"
        elif self.role == MessageRole.ASSISTANT:
            agent_icon = {"romance": "✍️", "scifi": "🚀", "fantasy": "🔮", "editor": "📖", "research": "📊", "publisher": "📤", "orchestrator": "🎯"}.get(self.agent, "🤖")
            agent_name = self.agent or "Assistant"
            return f"[cyan]{agent_icon} {agent_name.title()}[/]: {self.content}"
        else:
            return f"[yellow]System[/]: {self.content}"


@dataclass
class ConversationHistory:
    """Manages conversation history."""
    messages: list[ChatMessage] = field(default_factory=list)
    max_messages: int = 100

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to history."""
        self.messages.append(message)
        # Trim old messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def add_user(self, content: str) -> ChatMessage:
        """Add user message."""
        msg = ChatMessage(role=MessageRole.USER, content=content)
        self.add_message(msg)
        return msg

    def add_assistant(self, content: str, agent: str | None = None) -> ChatMessage:
        """Add assistant message."""
        msg = ChatMessage(role=MessageRole.ASSISTANT, content=content, agent=agent)
        self.add_message(msg)
        return msg

    def add_system(self, content: str) -> ChatMessage:
        """Add system message."""
        msg = ChatMessage(role=MessageRole.SYSTEM, content=content)
        self.add_message(msg)
        return msg

    def get_recent(self, n: int = 20) -> list[ChatMessage]:
        """Get recent messages."""
        return self.messages[-n:]

    def clear(self) -> None:
        """Clear history."""
        self.messages.clear()

    def to_context(self, max_tokens: int = 4000) -> str:
        """Convert to context string for LLM."""
        # Simple token estimation
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # rough estimate
        max_message_chars = 1000  # Limit each message to prevent huge content

        for msg in reversed(self.messages):
            # Truncate message content if too long
            content = msg.content
            if len(content) > max_message_chars:
                content = content[:max_message_chars] + "... [内容截断]"

            msg_str = f"{msg.role.value}: {content}"
            if total_chars + len(msg_str) > max_chars:
                break
            context_parts.insert(0, msg_str)
            total_chars += len(msg_str)

        return "\n".join(context_parts)
