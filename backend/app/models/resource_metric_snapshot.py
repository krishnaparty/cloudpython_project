from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.database import Base


class ResourceMetricSnapshot(Base):
    __tablename__ = "resource_metric_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "resource_db_id",
            "metric_name",
            "metric_timestamp",
            name="uq_resource_metric_timestamp",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # cloud_resources table ke internal ID ka reference
    resource_db_id = Column(
        Integer,
        ForeignKey("cloud_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    metric_name = Column(
        String(100),
        nullable=False,
        index=True,
    )

    metric_timestamp = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    average_value = Column(
        Float,
        nullable=False,
    )

    maximum_value = Column(
        Float,
        nullable=False,
    )

    unit = Column(
        String(30),
        nullable=False,
        default="Percent",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )