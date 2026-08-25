from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.cloud_resource import CloudResource
from app.models.user import User, UserRole
from app.schemas.monitoring import EC2MetricResponse
from app.services.aws_service import AWSServiceError
from app.services.cloudwatch_service import (
    get_ec2_metric_statistics
)


router = APIRouter(
    prefix="/api/monitoring",
    tags=["Monitoring"]
)


MetricName = Literal[
    "CPUUtilization",
    "NetworkIn",
    "NetworkOut",
    "DiskReadBytes",
    "DiskWriteBytes",
    "StatusCheckFailed"
]


@router.get(
    "/ec2/{instance_id}/metrics",
    response_model=EC2MetricResponse
)
def get_instance_metrics(
    instance_id: str,
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],
    db: Annotated[
        Session,
        Depends(get_db)
    ],
    metric_name: MetricName = Query(
        default="CPUUtilization"
    ),
    hours: int = Query(
        default=24,
        ge=1,
        le=24
    ),
    period_seconds: int = Query(
        default=300,
        ge=300,
        le=3600,
        multiple_of=300
    )
):
    # Resource pehle sync hua hona chahiye
    resource = db.scalar(
        select(CloudResource).where(
            CloudResource.resource_id == instance_id,
            CloudResource.resource_type == "ec2_instance"
        )
    )

    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Synced EC2 resource not found. "
                "Run POST /api/aws/sync first."
            )
        )

    # Student sirf apne tagged resource ko monitor karega
    if (
        current_user.role == UserRole.STUDENT
        and resource.owner_email != current_user.email
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot monitor this resource."
        )

    try:
        return get_ec2_metric_statistics(
            instance_id=instance_id,
            metric_name=metric_name,
            hours=hours,
            period_seconds=period_seconds
        )

    except AWSServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        ) from error