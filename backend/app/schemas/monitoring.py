from datetime import datetime

from pydantic import BaseModel


class MetricDataPoint(BaseModel):
    timestamp: datetime
    average: float
    maximum: float
    sum: float
    unit: str


class EC2MetricResponse(BaseModel):
    instance_id: str
    metric_name: str
    start_time: datetime
    end_time: datetime
    period_seconds: int
    datapoints: list[MetricDataPoint]