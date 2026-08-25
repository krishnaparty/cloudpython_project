from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.ml_data import (
    DatasetSummaryResponse,
    MetricCollectionResponse,
)
from app.services.aws_service import AWSServiceError
from app.services.ml_data_service import (
    collect_metric_dataset,
    get_dataset_summary,
)


router = APIRouter(
    prefix="/api/ml",
    tags=["ML Dataset"],
)


AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.post(
    "/dataset/collect",
    response_model=MetricCollectionResponse,
)
def collect_dataset(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    lookback_days: int = Query(
        default=7,
        ge=1,
        le=30,
    ),
):
    try:
        return collect_metric_dataset(
            db=db,
            lookback_days=lookback_days,
        )

    except AWSServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get(
    "/dataset/summary",
    response_model=DatasetSummaryResponse,
)
def dataset_summary(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    return get_dataset_summary(db)