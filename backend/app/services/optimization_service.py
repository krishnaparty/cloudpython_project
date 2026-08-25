from datetime import datetime, timedelta, timezone
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.orm import Session

from app.models.cloud_resource import CloudResource
from app.models.optimization_recommendation import (
    OptimizationRecommendation,
)
from app.services.aws_service import (
    AWSServiceError,
    create_aws_session,
)


def _get_cpu_statistics(
    instance_id: str,
    region: str,
    lookback_days: int,
) -> tuple[float | None, float | None]:
    """
    EC2 instance ke last N days ke CPU metrics fetch karta hai.

    Return:
        average_cpu, maximum_cpu
    """

    session = create_aws_session()

    cloudwatch = session.client(
        "cloudwatch",
        region_name=region,
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=lookback_days)

    try:
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {
                    "Name": "InstanceId",
                    "Value": instance_id,
                }
            ],
            StartTime=start_time,
            EndTime=end_time,

            # Har returned point approximately one hour represent karega.
            Period=3600,

            Statistics=[
                "Average",
                "Maximum",
            ],
            Unit="Percent",
        )

        datapoints = response.get("Datapoints", [])

        if not datapoints:
            return None, None

        average_cpu = sum(
            point["Average"] for point in datapoints
        ) / len(datapoints)

        maximum_cpu = max(
            point["Maximum"] for point in datapoints
        )

        return round(average_cpu, 2), round(maximum_cpu, 2)

    except ClientError as error:
        error_details = error.response.get("Error", {})
        error_code = error_details.get("Code", "AWSClientError")
        error_message = error_details.get(
            "Message",
            "Unable to fetch CloudWatch metrics.",
        )

        raise AWSServiceError(
            f"CloudWatch error for {instance_id} "
            f"({error_code}): {error_message}"
        ) from error

    except BotoCoreError as error:
        raise AWSServiceError(
            f"AWS connection error for {instance_id}: {error}"
        ) from error


def _analyse_resource(
    resource: CloudResource,
    lookback_days: int,
) -> dict[str, Any] | None:
    """
    Resource ke state aur CPU metrics ke basis par
    recommendation decide karta hai.
    """

    state = (resource.state or "").lower()

    # Stopped instance compute charge nahi leta,
    # lekin EBS volume ya Elastic IP charge kar sakte hain.
    if state == "stopped":
        return {
            "recommendation_type": "STOPPED_INSTANCE_REVIEW",
            "severity": "MEDIUM",
            "reason": (
                "Instance stopped hai. Check karo ki attached "
                "EBS volumes ya unused Elastic IP ab bhi cost "
                "generate toh nahi kar rahe."
            ),
            "average_cpu": None,
            "maximum_cpu": None,
        }

    # Pending, shutting-down ya terminated resources ignore honge.
    if state != "running":
        return None

    average_cpu, maximum_cpu = _get_cpu_statistics(
        instance_id=resource.resource_id,
        region=resource.region,
        lookback_days=lookback_days,
    )

    if average_cpu is None or maximum_cpu is None:
        return {
            "recommendation_type": "MONITORING_DATA_MISSING",
            "severity": "LOW",
            "reason": (
                "Selected period ke liye CPU metrics available "
                "nahi hain. Instance new ho sakta hai ya monitoring "
                "data publish nahi hua."
            ),
            "average_cpu": None,
            "maximum_cpu": None,
        }

    if average_cpu < 5 and maximum_cpu < 20:
        return {
            "recommendation_type": "IDLE_INSTANCE_REVIEW",
            "severity": "HIGH",
            "reason": (
                f"Last {lookback_days} days mein average CPU "
                f"{average_cpu}% aur maximum CPU {maximum_cpu}% "
                "tha. Instance idle ho sakta hai. Stop schedule "
                "ya removal se pehle owner approval lo."
            ),
            "average_cpu": average_cpu,
            "maximum_cpu": maximum_cpu,
        }

    if average_cpu < 20 and maximum_cpu < 40:
        return {
            "recommendation_type": "DOWNSIZE_INSTANCE",
            "severity": "MEDIUM",
            "reason": (
                f"Last {lookback_days} days mein average CPU "
                f"{average_cpu}% aur maximum CPU {maximum_cpu}% "
                "tha. Smaller instance type evaluate kiya ja sakta hai."
            ),
            "average_cpu": average_cpu,
            "maximum_cpu": maximum_cpu,
        }

    return None


def run_optimization_scan(
    db: Session,
    lookback_days: int = 7,
) -> dict[str, int]:
    """
    MySQL mein synced EC2 resources scan karta hai aur
    recommendations create/update karta hai.
    """

    # EC2 instance IDs normally i- se start hoti hain.
    resources = (
        db.query(CloudResource)
        .filter(CloudResource.resource_id.like("i-%"))
        .all()
    )

    created_count = 0
    updated_count = 0
    healthy_count = 0

    try:
        for resource in resources:
            recommendation_data = _analyse_resource(
                resource=resource,
                lookback_days=lookback_days,
            )

            # Purani OPEN recommendation ko resolve mark karenge.
            previous_recommendations = (
                db.query(OptimizationRecommendation)
                .filter(
                    OptimizationRecommendation.resource_db_id
                    == resource.id,
                    OptimizationRecommendation.status == "OPEN",
                )
                .all()
            )

            for previous in previous_recommendations:
                previous.status = "RESOLVED"

            if recommendation_data is None:
                healthy_count += 1
                continue

            existing_recommendation = (
                db.query(OptimizationRecommendation)
                .filter(
                    OptimizationRecommendation.resource_db_id
                    == resource.id,
                    OptimizationRecommendation.recommendation_type
                    == recommendation_data["recommendation_type"],
                )
                .first()
            )

            if existing_recommendation:
                existing_recommendation.severity = (
                    recommendation_data["severity"]
                )
                existing_recommendation.reason = (
                    recommendation_data["reason"]
                )
                existing_recommendation.average_cpu = (
                    recommendation_data["average_cpu"]
                )
                existing_recommendation.maximum_cpu = (
                    recommendation_data["maximum_cpu"]
                )
                existing_recommendation.lookback_days = lookback_days
                existing_recommendation.status = "OPEN"

                updated_count += 1

            else:
                new_recommendation = OptimizationRecommendation(
                    resource_db_id=resource.id,
                    recommendation_type=(
                        recommendation_data["recommendation_type"]
                    ),
                    severity=recommendation_data["severity"],
                    reason=recommendation_data["reason"],
                    average_cpu=recommendation_data["average_cpu"],
                    maximum_cpu=recommendation_data["maximum_cpu"],
                    lookback_days=lookback_days,
                    status="OPEN",
                )

                db.add(new_recommendation)
                created_count += 1

        db.commit()

        return {
            "scanned_resources": len(resources),
            "recommendations_created": created_count,
            "recommendations_updated": updated_count,
            "healthy_resources": healthy_count,
        }

    except Exception:
        db.rollback()
        raise