"""Authentication API router."""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status
import bcrypt
import jwt

from src.novel_agent.api.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
SECRET_KEY = "novelwriter-secret-key-change-in-production"
ALGORITHM = "HS256"

USERS_FILE = Path("data/users.json")


def _get_users() -> dict:
    if not USERS_FILE.exists():
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {}
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except:
        return {}


def _save_users(users: dict) -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def _create_token(user_id: str) -> str:
    exp = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": user_id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def _hash_password(password: str) -> str:
    """Hash password using bcrypt, truncating to 72 bytes if needed."""
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')


def _verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash, truncating to 72 bytes if needed."""
    password_bytes = password.encode('utf-8')[:72]
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(user: UserRegister) -> TokenResponse:
    users = _get_users()
    email = user.email.lower()
    
    for u in users.values():
        if u["email"] == email:
            raise HTTPException(400, "Email already exists")
    
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    new_user = {
        "id": user_id,
        "email": email,
        "name": user.name,
        "password_hash": _hash_password(user.password),
        "created_at": now,
    }
    users[user_id] = new_user
    _save_users(users)
    
    # Also create a token for the newly registered user
    token = _create_token(user_id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=email, name=user.name, created_at=now)
    )


@router.post("/login", response_model=TokenResponse)
def login(creds: UserLogin, response: Response) -> TokenResponse:
    users = _get_users()
    email = creds.email.lower()
    
    user_data = None
    for u in users.values():
        if u["email"] == email:
            user_data = u
            break
    
    if not user_data or not _verify_password(creds.password, user_data["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    
    token = _create_token(user_data["id"])
    response.headers["Authorization"] = f"Bearer {token}"
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            created_at=user_data["created_at"],
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(authorization: str = None) -> UserResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except:
        raise HTTPException(401, "Invalid token")
    
    users = _get_users()
    user_data = users.get(user_id)
    if not user_data:
        raise HTTPException(404, "User not found")
    
    return UserResponse(**user_data)
