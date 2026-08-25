from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    require_roles,
)

# Existing API file se exact get_db import copy karna
from app.database import get_db

from app.models.cloud_resource import CloudResource
from app.models.metric_anomaly import MetricAnomaly
from app.models.resource_metric_snapshot import (
    ResourceMetricSnapshot,
)
from app.models.user import User, UserRole
from app.schemas.anomaly import (
    AnomalyDetectionResponse,
    AnomalyResponse,
)
from app.services.anomaly_detection_service import (
    detect_cpu_anomalies,
)


router = APIRouter(
    prefix="/api/ml/anomalies",
    tags=["ML Anomaly Detection"],
)


AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN)),
]


@router.post(
    "/detect",
    response_model=AnomalyDetectionResponse,
)
def detect_anomalies(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    contamination: float = Query(
        default=0.05,
        ge=0.01,
        le=0.10,
    ),
):
    """
    Isolation Forest model run karta hai.
    """

    return detect_cpu_anomalies(
        db=db,
        contamination=contamination,
    )


@router.get(
    "",
    response_model=list[AnomalyResponse],
)
def list_anomalies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    active_only: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=500),
):
    """
    Detected anomalies return karta hai.
    Students sirf apne resources dekh sakte hain.
    """

    query = (
        db.query(
            MetricAnomaly,
            ResourceMetricSnapshot,
            CloudResource,
        )
        .join(
            ResourceMetricSnapshot,
            ResourceMetricSnapshot.id
            == MetricAnomaly.metric_snapshot_id,
        )
        .join(
            CloudResource,
            CloudResource.id
            == MetricAnomaly.resource_db_id,
        )
    )

    if active_only:
        query = query.filter(
            MetricAnomaly.is_active.is_(True)
        )

    if current_user.role == UserRole.STUDENT:
        query = query.filter(
            CloudResource.owner_email
            == current_user.email
        )

    rows = (
        query.order_by(
            ResourceMetricSnapshot.metric_timestamp.desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": anomaly.id,
            "resource_id": resource.resource_id,
            "resource_name": resource.name,
            "metric_name": snapshot.metric_name,
            "metric_timestamp": snapshot.metric_timestamp,
            "average_value": snapshot.average_value,
            "maximum_value": snapshot.maximum_value,
            "anomaly_score": anomaly.anomaly_score,
            "severity": anomaly.severity,
            "reason": anomaly.reason,
            "model_name": anomaly.model_name,
            "is_active": anomaly.is_active,
            "detected_at": anomaly.detected_at,
        }
        for anomaly, snapshot, resource in rows
    ]