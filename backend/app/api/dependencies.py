from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User, UserRole


# Swagger ko batata hai ki token login endpoint se milega
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    JWT token verify karke currently logged-in user return karta hai.
    """

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = decode_access_token(token)

        # Token ke 'sub' field mein user ID stored hai
        subject = payload.get("sub")

        if subject is None:
            raise credentials_error

        user_id = int(subject)

    except (InvalidTokenError, ValueError):
        raise credentials_error

    # User ko MySQL se find karo
    user = db.get(User, user_id)

    if user is None:
        raise credentials_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


def require_roles(*allowed_roles: UserRole):
    """
    Check karta hai ki logged-in user ka role
    allowed roles mein present hai ya nahi.
    """

    def role_checker(
        current_user: Annotated[
            User,
            Depends(get_current_user)
        ]
    ) -> User:

        if current_user.role not in allowed_roles:
            allowed_role_names = ", ".join(
                role.value for role in allowed_roles
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Allowed roles: "
                    f"{allowed_role_names}"
                )
            )

        return current_user

    return role_checker