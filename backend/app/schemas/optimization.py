from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class OptimizationScanResponse(BaseModel):
    scanned_resources: int
    recommendations_created: int
    recommendations_updated: int
    healthy_resources: int


class RecommendationResponse(BaseModel):
    id: int
    resource_db_id: int

    resource_id: str
    resource_name: str | None

    recommendation_type: str
    severity: str
    reason: str

    average_cpu: float | None
    maximum_cpu: float | None
    lookback_days: int

    status: str
    created_at: datetime
    updated_at: datetime


class RecommendationStatusUpdate(BaseModel):
    status: Literal[
        "OPEN",
        "RESOLVED",
        "IGNORED",
    ]