"""API routers package."""

from .agents import router as agents_router
from .chapters import router as chapters_router
from .characters import router as characters_router
from .graph import router as graph_router
from .monitoring import router as monitoring_router
from .projects import router as projects_router
from .publishing import router as publishing_router
from .tasks import router as tasks_router

__all__ = [
    "agents_router",
    "chapters_router",
    "characters_router",
    "graph_router",
    "monitoring_router",
    "projects_router",
    "publishing_router",
    "tasks_router",
]
