from sqlalchemy import (
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

from app.database import Base  # <--- Change to your actual path


class OptimizationRecommendation(Base):
    __tablename__ = "optimization_recommendations"

    __table_args__ = (
        UniqueConstraint(
            "resource_db_id",
            "recommendation_type",
            name="uq_resource_recommendation_type",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    # cloud_resources table ke internal database ID ka reference
    resource_db_id = Column(
        Integer,
        ForeignKey("cloud_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recommendation_type = Column(
        String(60),
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

    average_cpu = Column(
        Float,
        nullable=True,
    )

    maximum_cpu = Column(
        Float,
        nullable=True,
    )

    lookback_days = Column(
        Integer,
        nullable=False,
        default=7,
    )

    # OPEN, RESOLVED ya IGNORED
    status = Column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True,
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