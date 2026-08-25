from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.cloud_resource import CloudResource
from app.services.aws_service import (
    get_aws_identity,
    list_ec2_instances
)


# In tags ke bina resource non-compliant maana jayega
REQUIRED_TAGS = (
    "Name",
    "OwnerEmail",
    "Project",
    "Environment"
)


class ResourceSyncError(Exception):
    """Resource synchronization errors."""

    pass


def normalize_datetime(
    value: datetime | None
) -> datetime | None:
    """
    AWS timezone-aware datetime ko MySQL-compatible
    UTC datetime mein convert karta hai.
    """

    if value is None:
        return None

    if value.tzinfo is not None:
        return value.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    return value


def sync_ec2_resources(
    db: Session
) -> dict[str, Any]:
    """
    AWS EC2 resources ko MySQL cloud_resources table
    ke saath synchronize karta hai.
    """

    # AWS calls database transaction se pehle
    identity = get_aws_identity()
    instances = list_ec2_instances()

    account_id = identity["account_id"]
    region = identity["region"]

    instance_ids = [
        instance["instance_id"]
        for instance in instances
    ]

    try:
        # Existing resources ek hi query mein fetch karo
        existing_resources: dict[str, CloudResource] = {}

        if instance_ids:
            statement = select(CloudResource).where(
                CloudResource.aws_account_id == account_id,
                CloudResource.region == region,
                CloudResource.resource_type == "ec2_instance",
                CloudResource.resource_id.in_(instance_ids)
            )

            existing_rows = db.scalars(statement).all()

            existing_resources = {
                resource.resource_id: resource
                for resource in existing_rows
            }

        created_count = 0
        updated_count = 0
        compliant_count = 0
        non_compliant_count = 0

        current_time = datetime.now(
            timezone.utc
        ).replace(tzinfo=None)

                # MySQL ke existing EC2 resources fetch karo
        stored_statement = select(
            CloudResource
        ).where(
            CloudResource.aws_account_id
            == account_id,
            CloudResource.region
            == region,
            CloudResource.resource_type
            == "ec2_instance",
        )

        stored_resources = db.scalars(
            stored_statement
        ).all()

        current_instance_ids = set(
            instance_ids
        )

        # Jo resource AWS mein nahi hai,
        # use terminated mark karo
        for stored_resource in stored_resources:
            if (
                stored_resource.resource_id
                not in current_instance_ids
            ):
                stored_resource.state = "terminated"
                stored_resource.last_synced_at = (
                    current_time
                )

        for instance in instances:
            tags = instance.get("tags", {})

            # Empty tag value bhi missing maana jayega
            missing_tags = [
                required_tag
                for required_tag in REQUIRED_TAGS
                if not str(
                    tags.get(required_tag, "")
                ).strip()
            ]

            is_compliant = len(missing_tags) == 0

            if is_compliant:
                compliant_count += 1
            else:
                non_compliant_count += 1

            owner_email = tags.get("OwnerEmail")

            if owner_email:
                owner_email = owner_email.lower().strip()

            resource = existing_resources.get(
                instance["instance_id"]
            )

            if resource is None:
                resource = CloudResource(
                    aws_account_id=account_id,
                    resource_id=instance["instance_id"],
                    resource_type="ec2_instance",
                    region=region,
                    name=tags.get("Name"),
                    availability_zone=instance.get(
                        "availability_zone"
                    ),
                    instance_type=instance.get(
                        "instance_type"
                    ),
                    state=instance.get("state"),
                    launch_time=normalize_datetime(
                        instance.get("launch_time")
                    ),
                    owner_email=owner_email,
                    project_name=tags.get("Project"),
                    environment=tags.get("Environment"),
                    is_compliant=is_compliant,
                    missing_tags=missing_tags,
                    tags=tags,
                    last_synced_at=current_time
                )

                db.add(resource)
                created_count += 1

            else:
                resource.name = tags.get("Name")
                resource.availability_zone = instance.get(
                    "availability_zone"
                )
                resource.instance_type = instance.get(
                    "instance_type"
                )
                resource.state = instance.get("state")
                resource.launch_time = normalize_datetime(
                    instance.get("launch_time")
                )
                resource.owner_email = owner_email
                resource.project_name = tags.get("Project")
                resource.environment = tags.get("Environment")
                resource.is_compliant = is_compliant
                resource.missing_tags = missing_tags
                resource.tags = tags
                resource.last_synced_at = current_time

                updated_count += 1

        db.commit()

        return {
            "fetched": len(instances),
            "created": created_count,
            "updated": updated_count,
            "compliant": compliant_count,
            "non_compliant": non_compliant_count
        }

    except SQLAlchemyError as error:
        db.rollback()

        raise ResourceSyncError(
            "EC2 resources could not be saved to MySQL."
        ) from error