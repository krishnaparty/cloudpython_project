from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

# Existing model se exact Base import copy karna
from app.database import Base


class MetricAnomaly(Base):
    __tablename__ = "metric_anomalies"

    __table_args__ = (
        UniqueConstraint(
            "metric_snapshot_id",
            "model_name",
            name="uq_snapshot_model",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    resource_db_id = Column(
        Integer,
        ForeignKey("cloud_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    metric_snapshot_id = Column(
        Integer,
        ForeignKey(
            "resource_metric_snapshots.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    model_name = Column(
        String(100),
        nullable=False,
        default="IsolationForest-v1",
    )

    anomaly_score = Column(
        Float,
        nullable=False,
    )

    severity = Column(
        String(20),
        nullable=False,
    )

    reason = Column(
        Text,
        nullable=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    detected_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
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