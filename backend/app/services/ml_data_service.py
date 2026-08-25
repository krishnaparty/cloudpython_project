from datetime import datetime, timedelta, timezone
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.cloud_resource import CloudResource
from app.models.resource_metric_snapshot import (
    ResourceMetricSnapshot,
)
from app.services.aws_service import (
    AWSServiceError,
    create_aws_session,
)


METRIC_NAME = "CPUUtilization"
RECOMMENDED_MINIMUM_POINTS = 168  # 168 five-minute points = approximately 14 hours


def _convert_to_utc_naive(timestamp: datetime) -> datetime:
    """
    CloudWatch timezone-aware timestamp ko MySQL-compatible
    UTC datetime mein convert karta hai.
    """

    return (
        timestamp.astimezone(timezone.utc)
        .replace(tzinfo=None)
    )


def _fetch_cpu_datapoints(
    cloudwatch_client: Any,
    instance_id: str,
    lookback_days: int,
) -> list[dict[str, Any]]:
    """
    Ek EC2 instance ke hourly CPU datapoints fetch karta hai.
    """

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=lookback_days)

    response = cloudwatch_client.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName=METRIC_NAME,
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id,
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=[
            "Average",
            "Maximum",
        ],
        Unit="Percent",
    )

    # CloudWatch datapoints ordered form mein return nahi karta.
    return sorted(
        response.get("Datapoints", []),
        key=lambda point: point["Timestamp"],
    )


def collect_metric_dataset(
    db: Session,
    lookback_days: int = 7,
) -> dict[str, int]:
    """
    Running EC2 instances ke CloudWatch CPU datapoints
    MySQL mein insert/update karta hai.
    """

    resources = (
        db.query(CloudResource)
        .filter(
            CloudResource.resource_id.like("i-%"),
            CloudResource.state == "running",
        )
        .all()
    )

    session = create_aws_session()

    # Har region ke liye ek client reuse hoga.
    cloudwatch_clients: dict[str, Any] = {}

    fetched_count = 0
    saved_count = 0

    try:
        for resource in resources:
            region = resource.region or settings.aws_region

            if region not in cloudwatch_clients:
                cloudwatch_clients[region] = session.client(
                    "cloudwatch",
                    region_name=region,
                )

            cloudwatch_client = cloudwatch_clients[region]

            datapoints = _fetch_cpu_datapoints(
                cloudwatch_client=cloudwatch_client,
                instance_id=resource.resource_id,
                lookback_days=lookback_days,
            )

            fetched_count += len(datapoints)

            records = []

            for point in datapoints:
                records.append(
                    {
                        "resource_db_id": resource.id,
                        "metric_name": METRIC_NAME,
                        "metric_timestamp": (
                            _convert_to_utc_naive(
                                point["Timestamp"]
                            )
                        ),
                        "average_value": round(
                            float(point["Average"]),
                            4,
                        ),
                        "maximum_value": round(
                            float(point["Maximum"]),
                            4,
                        ),
                        "unit": "Percent",
                    }
                )

            if not records:
                continue

            # MySQL-specific upsert:
            # duplicate point aaye toh update ho jayega.
            insert_statement = mysql_insert(
                ResourceMetricSnapshot
            ).values(records)

            upsert_statement = (
                insert_statement.on_duplicate_key_update(
                    average_value=(
                        insert_statement.inserted.average_value
                    ),
                    maximum_value=(
                        insert_statement.inserted.maximum_value
                    ),
                    unit=insert_statement.inserted.unit,
                    updated_at=func.now(),
                )
            )

            db.execute(upsert_statement)
            saved_count += len(records)

        db.commit()

        return {
            "resources_scanned": len(resources),
            "datapoints_fetched": fetched_count,
            "datapoints_saved": saved_count,
        }

    except ClientError as error:
        db.rollback()

        error_details = error.response.get("Error", {})
        error_code = error_details.get(
            "Code",
            "AWSClientError",
        )
        error_message = error_details.get(
            "Message",
            "Unable to fetch CloudWatch metrics.",
        )

        raise AWSServiceError(
            f"CloudWatch error ({error_code}): {error_message}"
        ) from error

    except BotoCoreError as error:
        db.rollback()

        raise AWSServiceError(
            f"AWS connection error: {error}"
        ) from error

    except Exception:
        db.rollback()
        raise


def get_dataset_summary(db: Session) -> dict[str, Any]:
    """
    Collected ML dataset ka summary return karta hai.
    """

    total_datapoints = (
        db.query(func.count(ResourceMetricSnapshot.id))
        .scalar()
        or 0
    )

    earliest_timestamp = (
        db.query(
            func.min(
                ResourceMetricSnapshot.metric_timestamp
            )
        )
        .scalar()
    )

    latest_timestamp = (
        db.query(
            func.max(
                ResourceMetricSnapshot.metric_timestamp
            )
        )
        .scalar()
    )

    resource_point_counts = (
        db.query(
            ResourceMetricSnapshot.resource_db_id,
            func.count(
                ResourceMetricSnapshot.id
            ).label("point_count"),
        )
        .group_by(
            ResourceMetricSnapshot.resource_db_id
        )
        .all()
    )

    resource_count = len(resource_point_counts)

    minimum_points = (
        min(row.point_count for row in resource_point_counts)
        if resource_point_counts
        else 0
    )

    ready_for_ml = (
        resource_count > 0
        and minimum_points >= RECOMMENDED_MINIMUM_POINTS
    )

    return {
        "resource_count": resource_count,
        "total_datapoints": total_datapoints,
        "earliest_timestamp": earliest_timestamp,
        "latest_timestamp": latest_timestamp,
        "minimum_points_per_resource": minimum_points,
        "recommended_minimum_points": (
            RECOMMENDED_MINIMUM_POINTS
        ),
        "ready_for_ml": ready_for_ml,
    }