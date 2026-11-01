"""Demo credential authentication and JWT bearer-token verification."""

import hmac
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from types import MappingProxyType

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import JWT_ALGO, JWT_SECRET, TOKEN_TTL_HOURS

# Demo-only mock: replace credentials and authentication before deployment.
USERS: Mapping[str, str] = MappingProxyType({"divyansh": "admin123"})

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def authenticate(username: str, password: str) -> bool:
    """Compare a known user's password using a constant-time comparison."""
    stored_password: str | None = USERS.get(username)
    if stored_password is None:
        return False

    return hmac.compare_digest(
        stored_password.encode("utf-8"),
        password.encode("utf-8"),
    )


def create_token(sub: str) -> str:
    """Issue a signed JWT with a UTC expiration time."""
    expires_at: datetime = datetime.now(timezone.utc) + timedelta(
        hours=TOKEN_TTL_HOURS
    )
    payload: dict[str, str | datetime] = {
        "sub": sub,
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Verify a bearer token and return its nonempty subject claim."""
    credentials_error: HTTPException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGO],
        )
    except jwt.PyJWTError as error:
        raise credentials_error from error

    subject: object = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise credentials_error

    return subject