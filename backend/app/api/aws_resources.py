from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.aws import (
    AWSAccountResponse,
    EC2InstanceResponse,
    ResourceSyncResponse
)
from app.services.aws_service import (
    AWSServiceError,
    get_aws_identity,
    list_ec2_instances
)
from app.services.resource_sync_service import (
    ResourceSyncError,
    sync_ec2_resources
)


router = APIRouter(
    prefix="/api/aws",
    tags=["AWS Resources"]
)


AdminUser = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN))
]


@router.get(
    "/account",
    response_model=AWSAccountResponse
)
def get_connected_aws_account(
    current_user: AdminUser
):
    try:
        return get_aws_identity()

    except AWSServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        ) from error


@router.get(
    "/ec2/instances",
    response_model=list[EC2InstanceResponse]
)
def get_ec2_instances(
    current_user: AdminUser
):
    try:
        return list_ec2_instances()

    except AWSServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        ) from error


@router.post(
    "/sync",
    response_model=ResourceSyncResponse
)
def synchronize_aws_resources(
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)]
):
    try:
        return sync_ec2_resources(db)

    except (AWSServiceError, ResourceSyncError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        ) from error