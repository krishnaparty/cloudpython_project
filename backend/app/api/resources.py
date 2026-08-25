from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.cloud_resource import CloudResource
from app.models.user import User, UserRole
from app.schemas.resource import CloudResourceResponse


router = APIRouter(
    prefix="/api/resources",
    tags=["Cloud Resources"]
)


@router.get(
    "/",
    response_model=list[CloudResourceResponse]
)
def get_stored_resources(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ],
    db: Annotated[
        Session,
        Depends(get_db)
    ]
):
    statement = select(
        CloudResource
    ).where(
        CloudResource.state != "terminated"
    )

    # Student ko sirf apne resources milenge
    if current_user.role == UserRole.STUDENT:
        statement = statement.where(
            CloudResource.owner_email == current_user.email
        )

    statement = statement.order_by(
        CloudResource.last_synced_at.desc()
    )

    return list(
        db.scalars(statement).all()
    )