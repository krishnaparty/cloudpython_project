from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CloudResourceResponse(BaseModel):
    id: int
    aws_account_id: str
    resource_id: str
    resource_type: str
    region: str
    name: str | None
    availability_zone: str | None
    instance_type: str | None
    state: str | None
    launch_time: datetime | None
    owner_email: str | None
    project_name: str | None
    environment: str | None
    is_compliant: bool
    missing_tags: list[str]
    tags: dict[str, str]
    first_seen_at: datetime
    last_synced_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )