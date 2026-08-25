from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import require_roles
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/api/access",
    tags=["Role Access"]
)


@router.get("/student-dashboard")
def student_dashboard(
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.STUDENT,
                UserRole.FACULTY,
                UserRole.ADMIN
            )
        )
    ]
):
    return {
        "message": "Student dashboard access granted",
        "user": current_user.full_name,
        "role": current_user.role.value
    }


@router.get("/faculty-dashboard")
def faculty_dashboard(
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.FACULTY,
                UserRole.ADMIN
            )
        )
    ]
):
    return {
        "message": "Faculty dashboard access granted",
        "user": current_user.full_name,
        "role": current_user.role.value
    }


@router.get("/admin-dashboard")
def admin_dashboard(
    current_user: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.ADMIN
            )
        )
    ]
):
    return {
        "message": "Admin dashboard access granted",
        "user": current_user.full_name,
        "role": current_user.role.value
    }