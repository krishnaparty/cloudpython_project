from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    verify_password
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    db: Annotated[
        Session,
        Depends(get_db)
    ]
):
    # OAuth2 ka username field yahan email ke liye use hoga
    normalized_email = form_data.username.lower().strip()

    user = db.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    # Email exist nahi karta
    if user is None:
        # Similar password-check timing maintain karta hai
        verify_password(
            form_data.password,
            DUMMY_HASH
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # Password incorrect
    if not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        user_id=user.id
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )


@router.get(
    "/me",
    response_model=UserResponse
)
def get_logged_in_user(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
):
    return current_user