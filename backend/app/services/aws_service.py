from typing import Any

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError
)

from app.core.config import settings


class AWSServiceError(Exception):
    """AWS operations ke controlled errors ke liye."""

    pass


def create_aws_session() -> boto3.Session:
    """
    cloudcampus-dev profile se AWS session create karta hai.
    """

    try:
        session = boto3.Session(
            profile_name=settings.aws_profile,
            region_name=settings.aws_region
        )

        if session.get_credentials() is None:
            raise AWSServiceError(
                "AWS credentials not found."
            )

        return session

    except AWSServiceError:
        raise

    except BotoCoreError as error:
        raise AWSServiceError(
            "Unable to create AWS session."
        ) from error


def get_aws_identity() -> dict[str, str]:
    """Connected AWS account aur IAM identity return karta hai."""

    try:
        session = create_aws_session()
        sts_client = session.client("sts")

        response = sts_client.get_caller_identity()

        return {
            "account_id": response["Account"],
            "user_id": response["UserId"],
            "arn": response["Arn"],
            "region": settings.aws_region
        }

    except NoCredentialsError as error:
        raise AWSServiceError(
            "AWS credentials not found."
        ) from error

    except ClientError as error:
        error_code = error.response["Error"].get(
            "Code",
            "UnknownError"
        )

        raise AWSServiceError(
            f"AWS identity request failed: {error_code}"
        ) from error

    except BotoCoreError as error:
        raise AWSServiceError(
            "Unable to connect to AWS."
        ) from error


def list_ec2_instances() -> list[dict[str, Any]]:
    """
    Current region ke non-terminated EC2 instances fetch karta hai.
    """

    try:
        session = create_aws_session()
        ec2_client = session.client("ec2")

        paginator = ec2_client.get_paginator(
            "describe_instances"
        )

        pages = paginator.paginate(
            Filters=[
                {
                    "Name": "instance-state-name",
                    "Values": [
                        "pending",
                        "running",
                        "stopping",
                        "stopped"
                    ]
                }
            ]
        )

        instances: list[dict[str, Any]] = []

        for page in pages:
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):

                    tags = {
                        tag["Key"]: tag["Value"]
                        for tag in instance.get("Tags", [])
                    }

                    instances.append(
                        {
                            "instance_id": instance["InstanceId"],
                            "name": tags.get("Name"),
                            "instance_type": instance["InstanceType"],
                            "state": instance["State"]["Name"],
                            "availability_zone": instance[
                                "Placement"
                            ]["AvailabilityZone"],
                            "launch_time": instance["LaunchTime"],
                            "public_ip": instance.get(
                                "PublicIpAddress"
                            ),
                            "private_ip": instance.get(
                                "PrivateIpAddress"
                            ),
                            "tags": tags
                        }
                    )

        return instances

    except NoCredentialsError as error:
        raise AWSServiceError(
            "AWS credentials not found."
        ) from error

    except ClientError as error:
        error_code = error.response["Error"].get(
            "Code",
            "UnknownError"
        )

        raise AWSServiceError(
            f"EC2 request failed: {error_code}"
        ) from error

    except BotoCoreError as error:
        raise AWSServiceError(
            "Unable to read EC2 instances."
        ) from error