from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cloud_resource import CloudResource
from app.models.daily_cost_snapshot import DailyCostSnapshot
from app.models.metric_anomaly import MetricAnomaly
from app.models.optimization_recommendation import (
    OptimizationRecommendation,
)
from app.models.user import User


def _get_role_name(user: User) -> str:
    """
    SQLAlchemy Enum aur normal string dono handle karta hai.
    """

    if hasattr(user.role, "value"):
        return str(user.role.value).upper()

    return str(user.role).upper()


def _create_severity_summary(
    rows: list[Any],
) -> dict[str, int]:
    """
    Recommendations/anomalies ka severity-wise count.
    """

    high = 0
    medium = 0
    low = 0

    for row in rows:
        severity = str(row.severity).upper()

        if severity == "HIGH":
            high += 1
        elif severity == "MEDIUM":
            medium += 1
        elif severity == "LOW":
            low += 1

    return {
        "total": len(rows),
        "high": high,
        "medium": medium,
        "low": low,
    }


def get_dashboard_overview(
    db: Session,
    current_user: User,
) -> dict[str, Any]:
    """
    Role-based dashboard overview generate karta hai.
    """

    role_name = _get_role_name(current_user)

    resource_query = db.query(
    CloudResource
).filter(
    CloudResource.state != "terminated"
)

    # Student sirf apne resources dekhega.
    if role_name == "STUDENT":
        resource_query = resource_query.filter(
            CloudResource.owner_email
            == current_user.email
        )

    resources = resource_query.all()

    resource_ids = [
        resource.id for resource in resources
    ]

    running_count = sum(
        1
        for resource in resources
        if str(resource.state).lower() == "running"
    )

    stopped_count = sum(
        1
        for resource in resources
        if str(resource.state).lower() == "stopped"
    )

    other_states_count = (
        len(resources)
        - running_count
        - stopped_count
    )

    compliant_count = sum(
        1
        for resource in resources
        if resource.is_compliant is True
    )

    non_compliant_count = sum(
        1
        for resource in resources
        if resource.is_compliant is False
    )

    recommendations = []

    anomalies = []

    if resource_ids:
        recommendations = (
            db.query(OptimizationRecommendation)
            .filter(
                OptimizationRecommendation.resource_db_id.in_(
                    resource_ids
                ),
                OptimizationRecommendation.status == "OPEN",
            )
            .all()
        )

        anomalies = (
            db.query(MetricAnomaly)
            .filter(
                MetricAnomaly.resource_db_id.in_(
                    resource_ids
                ),
                MetricAnomaly.is_active.is_(True),
            )
            .all()
        )

    resources_last_synced_at = None

    if resources:
        sync_times = [
            resource.last_synced_at
            for resource in resources
            if resource.last_synced_at is not None
        ]

        if sync_times:
            resources_last_synced_at = max(sync_times)

    # Billing data sirf Admin ko show hoga.
    cost_visible = role_name == "ADMIN"

    month_to_date_cost = None
    latest_cost_date = None
    recent_cost_history = []

    if cost_visible:
        current_month_start = date.today().replace(
            day=1
        )

        month_cost = (
            db.query(
                func.sum(DailyCostSnapshot.total_cost)
            )
            .filter(
                DailyCostSnapshot.cost_date
                >= current_month_start
            )
            .scalar()
            or Decimal("0")
        )

        month_to_date_cost = round(
            float(month_cost),
            6,
        )

        recent_cost_rows = (
            db.query(DailyCostSnapshot)
            .order_by(
                DailyCostSnapshot.cost_date.desc()
            )
            .limit(7)
            .all()
        )

        # Frontend chart ke liye oldest-to-newest order.
        recent_cost_rows.reverse()

        recent_cost_history = [
            {
                "cost_date": row.cost_date,
                "total_cost": round(
                    float(row.total_cost),
                    6,
                ),
                "currency": row.currency,
                "estimated": row.estimated,
            }
            for row in recent_cost_rows
        ]

        if recent_cost_rows:
            latest_cost_date = recent_cost_rows[-1].cost_date

    return {
        "user_role": role_name,
        "resources": {
            "total": len(resources),
            "running": running_count,
            "stopped": stopped_count,
            "other_states": other_states_count,
            "compliant": compliant_count,
            "non_compliant": non_compliant_count,
        },
        "recommendations": (
            _create_severity_summary(
                recommendations
            )
        ),
        "anomalies": _create_severity_summary(
            anomalies
        ),
        "cost_visible": cost_visible,
        "month_to_date_cost": month_to_date_cost,
        "latest_cost_date": latest_cost_date,
        "recent_cost_history": recent_cost_history,
        "resources_last_synced_at": (
            resources_last_synced_at
        ),
        "generated_at": datetime.now(timezone.utc),
    }