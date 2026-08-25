from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles

# Existing API ka exact get_db import use karo
from app.database import get_db

from app.models.user import User, UserRole
from app.schemas.cost_dataset import (
    CostDatasetCollectionResponse,
    CostDatasetSummaryResponse,
)
from app.services.aws_service import AWSServiceError
from app.services.cost_dataset_service import (
    collect_daily_cost_dataset,
    get_cost_dataset_summary,
)


router = APIRouter(
    prefix="/api/ml/cost-data",
    tags=["ML Cost Dataset"],
)


AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.post(
    "/collect",
    response_model=CostDatasetCollectionResponse,
)
def collect_cost_data(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    lookback_days: int = Query(
        default=90,
        ge=14,
        le=365,
    ),
):
    try:
        return collect_daily_cost_dataset(
            db=db,
            lookback_days=lookback_days,
        )

    except AWSServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get(
    "/summary",
    response_model=CostDatasetSummaryResponse,
)
def cost_data_summary(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    return get_cost_dataset_summary(db)