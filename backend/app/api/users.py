from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Email ko lowercase aur clean format mein convert karo
    normalized_email = user_data.email.lower().strip()

    # Check karo email pehle se registered toh nahi
    existing_user = db.scalar(
        select(User).where(
            User.email == normalized_email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    # Plain password ko hash karke User object banao
    new_user = User(
        full_name=user_data.full_name.strip(),
        email=normalized_email,
        hashed_password=hash_password(
            user_data.password
        ),
        role=UserRole.STUDENT,
        is_active=True
    )

    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    db.refresh(new_user)

    return new_user