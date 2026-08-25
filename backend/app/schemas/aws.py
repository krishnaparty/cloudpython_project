from datetime import datetime

from pydantic import BaseModel


class AWSAccountResponse(BaseModel):
    account_id: str
    user_id: str
    arn: str
    region: str


class EC2InstanceResponse(BaseModel):
    instance_id: str
    name: str | None
    instance_type: str
    state: str
    availability_zone: str
    launch_time: datetime
    public_ip: str | None
    private_ip: str | None
    tags: dict[str, str]


class ResourceSyncResponse(BaseModel):
    fetched: int
    created: int
    updated: int
    compliant: int
    non_compliant: int