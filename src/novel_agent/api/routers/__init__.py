"""API routers package."""

from .agents import router as agents_router
from .auth import router as auth_router
from .backup import router as backup_router
from .chapters import router as chapters_router
from .characters import router as characters_router
from .monitoring import router as monitoring_router
from .outlines import router as outlines_router
from .projects import router as projects_router
from .publishing import router as publishing_router
from .search import router as search_router
from .tasks import router as tasks_router

__all__ = [
    "agents_router",
    "auth_router",
    "backup_router",
    "chapters_router",
    "characters_router",
    "monitoring_router",
    "outlines_router",
    "projects_router",
    "publishing_router",
    "search_router",
    "tasks_router",
]
