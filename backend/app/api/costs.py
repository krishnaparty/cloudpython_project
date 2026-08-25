from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import require_roles
from app.models.user import User, UserRole
from app.schemas.cost import CostSummaryResponse
from app.services.aws_service import AWSServiceError
from app.services.cost_explorer_service import get_cost_summary


router = APIRouter(
    prefix="/api/costs",
    tags=["Cost Management"],
)


AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.get(
    "/summary",
    response_model=CostSummaryResponse,
)
def read_cost_summary(
    current_user: AdminUser,
    months: int = Query(default=3, ge=1, le=12),
):
    """
    Admin ko AWS ka monthly service-wise cost return karta hai.
    """

    try:
        return get_cost_summary(months=months)

    except AWSServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error