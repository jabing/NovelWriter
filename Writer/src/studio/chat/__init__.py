# src/studio/chat/__init__.py
"""Chat-based Writer Studio interface."""

from src.studio.chat.agents import AGENTS, AgentManager, AgentType
from src.studio.chat.commands import CommandRegistry

try:
    from src.studio.chat.flet_app import ChatFletApp, run_flet_chat_studio
except ImportError:
    ChatFletApp = None  # type: ignore
    run_flet_chat_studio = None  # type: ignore

from src.studio.chat.message import ChatMessage, ConversationHistory, MessageRole

__all__ = [
    "ChatMessage",
    "ConversationHistory",
    "MessageRole",
    "AgentManager",
    "AgentType",
    "AGENTS",
    "CommandRegistry",
]

if ChatFletApp is not None:
    __all__.extend(["ChatFletApp", "run_flet_chat_studio"])
