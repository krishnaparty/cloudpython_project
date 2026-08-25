from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    func,
)

# Existing model wala exact Base import use karo
from app.database import Base


class DailyCostSnapshot(Base):
    __tablename__ = "daily_cost_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "aws_account_id",
            "cost_date",
            name="uq_account_cost_date",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    aws_account_id = Column(
        String(20),
        nullable=False,
        index=True,
    )

    cost_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    total_cost = Column(
        Numeric(18, 6),
        nullable=False,
    )

    currency = Column(
        String(10),
        nullable=False,
        default="USD",
    )

    estimated = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Example:
    # {"Amazon EC2": 1.25, "Amazon S3": 0.20}
    service_breakdown = Column(
        JSON,
        nullable=False,
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