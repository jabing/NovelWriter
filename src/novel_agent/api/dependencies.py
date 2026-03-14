"""FastAPI dependencies for the API layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

if TYPE_CHECKING:
    from src.novel_agent.studio.core.state import StudioState


security = HTTPBearer(auto_error=False)
SECRET_KEY = "novelwriter-secret-key-change-in-production"
ALGORITHM = "HS256"


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Extract user_id from JWT token in Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_state() -> StudioState:
    """Get the global StudioState singleton."""
    from src.novel_agent.studio.core.state import get_studio_state
    return get_studio_state()
