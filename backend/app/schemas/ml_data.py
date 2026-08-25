from datetime import datetime

from pydantic import BaseModel


class MetricCollectionResponse(BaseModel):
    resources_scanned: int
    datapoints_fetched: int
    datapoints_saved: int


class DatasetSummaryResponse(BaseModel):
    resource_count: int
    total_datapoints: int
    earliest_timestamp: datetime | None
    latest_timestamp: datetime | None
    minimum_points_per_resource: int
    recommended_minimum_points: int
    ready_for_ml: bool