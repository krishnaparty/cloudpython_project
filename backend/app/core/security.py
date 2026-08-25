from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()


# Invalid username ke case mein timing attack reduce karne ke liye
DUMMY_HASH = password_hash.hash("dummy-password")


def hash_password(password: str) -> str:
    """
    Plain password ko Argon2 hash mein convert karta hai.
    """

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Login password ko database hash se compare karta hai.
    """

    return password_hash.verify(
        plain_password,
        hashed_password
    )


def create_access_token(user_id: int) -> str:
    """
    User ID ke saath limited-time JWT token create karta hai.
    """

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    """
    JWT signature aur expiration verify karke payload return karta hai.
    """

    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM]
    )