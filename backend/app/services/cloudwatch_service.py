from datetime import datetime, timedelta, timezone
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from app.services.aws_service import (
    AWSServiceError,
    create_aws_session
)


SUPPORTED_METRICS = {
    "CPUUtilization": "Percent",
    "NetworkIn": "Bytes",
    "NetworkOut": "Bytes",
    "DiskReadBytes": "Bytes",
    "DiskWriteBytes": "Bytes",
    "StatusCheckFailed": "Count"
}


def get_ec2_metric_statistics(
    instance_id: str,
    metric_name: str,
    hours: int = 24,
    period_seconds: int = 300
) -> dict[str, Any]:
    """
    EC2 instance ka CloudWatch metric fetch karta hai.
    """

    if metric_name not in SUPPORTED_METRICS:
        raise AWSServiceError(
            f"Unsupported metric: {metric_name}"
        )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    try:
        session = create_aws_session()
        cloudwatch_client = session.client("cloudwatch")

        response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName=metric_name,
            Dimensions=[
                {
                    "Name": "InstanceId",
                    "Value": instance_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=period_seconds,
            Statistics=[
                "Average",
                "Maximum",
                "Sum"
            ]
        )

        # CloudWatch chronological order guarantee nahi karta
        sorted_datapoints = sorted(
            response.get("Datapoints", []),
            key=lambda point: point["Timestamp"]
        )

        datapoints = [
            {
                "timestamp": point["Timestamp"],
                "average": point.get("Average", 0.0),
                "maximum": point.get("Maximum", 0.0),
                "sum": point.get("Sum", 0.0),
                "unit": point.get(
                    "Unit",
                    SUPPORTED_METRICS[metric_name]
                )
            }
            for point in sorted_datapoints
        ]

        return {
            "instance_id": instance_id,
            "metric_name": metric_name,
            "start_time": start_time,
            "end_time": end_time,
            "period_seconds": period_seconds,
            "datapoints": datapoints
        }

    except ClientError as error:
        error_code = error.response["Error"].get(
            "Code",
            "UnknownError"
        )

        raise AWSServiceError(
            f"CloudWatch request failed: {error_code}"
        ) from error

    except BotoCoreError as error:
        raise AWSServiceError(
            "Unable to read CloudWatch metrics."
        ) from error