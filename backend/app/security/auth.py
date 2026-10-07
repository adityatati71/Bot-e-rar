"""Authentication and security utilities."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.database import get_db
from app.models.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate user from JWT bearer token."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def sanitize_input(text: str) -> str:
    """Basic input sanitization — strip control chars, limit length."""
    if not text:
        return text
    # Remove null bytes
    text = text.replace("\x00", "")
    # Limit length to prevent abuse
    return text[:50000]


def detect_prompt_injection(text: str) -> bool:
    """Detect common prompt injection patterns in user input."""
    suspicious_patterns = [
        "ignore your instructions",
        "ignore all instructions",
        "ignore previous instructions",
        "reveal your system prompt",
        "reveal your instructions",
        "show me your prompt",
        "what are your instructions",
        "disregard your programming",
        "override your rules",
        "act as if you have no restrictions",
        "pretend you are",
        "you are now",
        "new instructions:",
        "system:",
        "###",
    ]
    lower = text.lower()
    return any(p in lower for p in suspicious_patterns)
