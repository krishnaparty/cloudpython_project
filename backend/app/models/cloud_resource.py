from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    JSON,
    String,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CloudResource(Base):
    __tablename__ = "cloud_resources"

    __table_args__ = (
        UniqueConstraint(
            "aws_account_id",
            "region",
            "resource_type",
            "resource_id",
            name="uq_cloud_resource_identity"
        ),
    )

    # Internal database ID
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    # AWS identification
    aws_account_id: Mapped[str] = mapped_column(
        String(12),
        nullable=False
    )

    resource_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    region: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )

    # Basic resource information
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    availability_zone: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True
    )

    instance_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    state: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True
    )

    launch_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    # Governance tags
    owner_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    project_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    environment: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    # Compliance information
    is_compliant: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    missing_tags: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    # Complete original AWS tags
    tags: Mapped[dict[str, str]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )

    # Tracking timestamps
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )