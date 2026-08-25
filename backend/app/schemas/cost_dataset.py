from datetime import date

from pydantic import BaseModel


class CostDatasetCollectionResponse(BaseModel):
    start_date: date
    end_date: date
    api_pages_requested: int
    days_fetched: int
    days_saved: int


class CostDatasetSummaryResponse(BaseModel):
    aws_account_id: str | None
    total_days: int
    earliest_date: date | None
    latest_date: date | None
    total_cost: float
    minimum_required_days: int
    ready_for_forecasting: bool