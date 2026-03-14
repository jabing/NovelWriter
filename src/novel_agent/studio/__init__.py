# src/studio/__init__.py
"""Writer Studio - Interactive novel writing management system."""

try:
    from src.novel_agent.studio.chat.flet_app import ChatFletApp, run_flet_chat_studio
except ImportError:
    ChatFletApp = None  # type: ignore
    run_flet_chat_studio = None  # type: ignore

__all__ = ["ChatFletApp", "run_flet_chat_studio"]
