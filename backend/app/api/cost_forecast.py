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

# Existing APIs wala exact get_db import use karo
from app.database import get_db

from app.models.user import User, UserRole
from app.schemas.cost_forecast import CostForecastResponse
from app.services.cost_forecast_service import (
    ForecastDataError,
    generate_cost_forecast,
)


router = APIRouter(
    prefix="/api/ml/cost-forecast",
    tags=["ML Cost Forecasting"],
)


AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.get(
    "",
    response_model=CostForecastResponse,
)
def get_cost_forecast(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    forecast_days: int = Query(
        default=30,
        ge=7,
        le=90,
    ),
):
    try:
        return generate_cost_forecast(
            db=db,
            forecast_days=forecast_days,
        )

    except ForecastDataError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error