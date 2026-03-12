"""Authentication API router."""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status
from passlib.context import CryptContext
import jwt

from src.api.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserRegister) -> UserResponse:
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
        "password_hash": pwd_context.hash(user.password),
        "created_at": now,
    }
    users[user_id] = new_user
    _save_users(users)
    
    return UserResponse(id=user_id, email=email, name=user.name, created_at=now)


@router.post("/login", response_model=TokenResponse)
def login(creds: UserLogin, response: Response) -> TokenResponse:
    users = _get_users()
    email = creds.email.lower()
    
    user_data = None
    for u in users.values():
        if u["email"] == email:
            user_data = u
            break
    
    if not user_data or not pwd_context.verify(creds.password, user_data["password_hash"]):
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
