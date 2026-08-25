from datetime import datetime

from pydantic import BaseModel


class AnomalyDetectionResponse(BaseModel):
    resources_found: int
    resources_trained: int
    resources_skipped: int
    points_analyzed: int
    anomalies_detected: int
    model_name: str


class AnomalyResponse(BaseModel):
    id: int
    resource_id: str
    resource_name: str | None
    metric_name: str
    metric_timestamp: datetime
    average_value: float
    maximum_value: float
    anomaly_score: float
    severity: str
    reason: str
    model_name: str
    is_active: bool
    detected_at: datetime