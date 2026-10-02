"""Authentication: PBKDF2 password hashing + JWT access tokens (cookie or Bearer header)."""
import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status

from . import database
from .config import get_settings

COOKIE_NAME = "access_token"
_PBKDF2_ROUNDS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"{salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _PBKDF2_ROUNDS)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except ValueError:
        return False


def validate_registration(username: str, email: str, password: str) -> Optional[str]:
    """Returns an error message, or None when input is valid."""
    if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", username or ""):
        return "Username must be 3-30 characters: letters, numbers or underscore."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""):
        return "Please enter a valid email address."
    if len(password or "") < 6:
        return "Password must be at least 6 characters."
    return None


def create_access_token(user_id: int, username: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "username": username, "iat": now, "exp": now + timedelta(minutes=s.token_minutes)}
    return jwt.encode(payload, s.secret_key, algorithm="HS256")


def authenticate(username: str, password: str) -> Optional[dict]:
    user = database.get_user_by_username(username)
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def _token_from_request(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get(COOKIE_NAME)


def get_optional_user(request: Request) -> Optional[dict]:
    token = _token_from_request(request)
    if not token:
        return None
    try:
        data = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
        return database.get_user_by_id(int(data["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def get_current_user(user: Optional[dict] = Depends(get_optional_user)) -> dict:
    """Dependency for protected API routes: 401 when not logged in."""
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated. Please log in.")
    return user
