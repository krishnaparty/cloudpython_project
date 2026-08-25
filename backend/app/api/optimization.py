from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.database import get_db  # <--- Update to your actual path
from app.models.cloud_resource import CloudResource
from app.models.optimization_recommendation import (
    OptimizationRecommendation,
)
from app.models.user import User, UserRole
from app.schemas.optimization import (
    OptimizationScanResponse,
    RecommendationResponse,
)
from app.services.aws_service import AWSServiceError
from app.services.optimization_service import run_optimization_scan
from app.models.optimization_recommendation import OptimizationRecommendation

from app.models.cloud_resource import CloudResource
from app.models.optimization_recommendation import (
    OptimizationRecommendation,
)

from app.schemas.optimization import (
    OptimizationScanResponse,
    RecommendationResponse,
    RecommendationStatusUpdate,
)

router = APIRouter(
    prefix="/api/optimization",
    tags=["Optimization"],
)


AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.post(
    "/scan",
    response_model=OptimizationScanResponse,
)
def scan_resources(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    lookback_days: int = Query(default=7, ge=1, le=30),
):
    """
    Sirf Admin optimization scan start kar sakta hai.
    """

    try:
        return run_optimization_scan(
            db=db,
            lookback_days=lookback_days,
        )

    except AWSServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get(
    "/recommendations",
    response_model=list[RecommendationResponse],
)
def get_recommendations(
    recommendation_status: Literal[
        "OPEN",
        "RESOLVED",
        "IGNORED",
    ] = Query(default="OPEN", alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin/Faculty sab recommendations dekh sakte hain.
    Student sirf apne resources ki recommendations dekhega.
    """

    query = (
        db.query(
            OptimizationRecommendation,
            CloudResource,
        )
        .join(
            CloudResource,
            CloudResource.id
            == OptimizationRecommendation.resource_db_id,
        )
        .filter(
            OptimizationRecommendation.status
            == recommendation_status
        )
    )

    if current_user.role == UserRole.STUDENT:
        query = query.filter(
            CloudResource.owner_email == current_user.email
        )

    rows = query.all()

    return [
        {
            "id": recommendation.id,
            "resource_db_id": recommendation.resource_db_id,
            "resource_id": resource.resource_id,
            "resource_name": resource.name,
            "recommendation_type": (
                recommendation.recommendation_type
            ),
            "severity": recommendation.severity,
            "reason": recommendation.reason,
            "average_cpu": recommendation.average_cpu,
            "maximum_cpu": recommendation.maximum_cpu,
            "lookback_days": recommendation.lookback_days,
            "status": recommendation.status,
            "created_at": recommendation.created_at,
            "updated_at": recommendation.updated_at,
        }
        for recommendation, resource in rows
    ]
@router.patch(
    "/recommendations/{recommendation_id}/status",
    response_model=RecommendationResponse,
)
def update_recommendation_status(
    recommendation_id: int,
    status_update: RecommendationStatusUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Admin recommendation ko OPEN, RESOLVED
    ya IGNORED mark kar sakta hai.
    """

    recommendation = (
        db.query(OptimizationRecommendation)
        .filter(
            OptimizationRecommendation.id
            == recommendation_id
        )
        .first()
    )

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found.",
        )

    resource = (
        db.query(CloudResource)
        .filter(
            CloudResource.id
            == recommendation.resource_db_id
        )
        .first()
    )

    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated cloud resource not found.",
        )

    recommendation.status = status_update.status

    db.commit()
    db.refresh(recommendation)

    return {
        "id": recommendation.id,
        "resource_db_id": recommendation.resource_db_id,
        "resource_id": resource.resource_id,
        "resource_name": resource.name,
        "recommendation_type": (
            recommendation.recommendation_type
        ),
        "severity": recommendation.severity,
        "reason": recommendation.reason,
        "average_cpu": recommendation.average_cpu,
        "maximum_cpu": recommendation.maximum_cpu,
        "lookback_days": recommendation.lookback_days,
        "status": recommendation.status,
        "created_at": recommendation.created_at,
        "updated_at": recommendation.updated_at,
    }