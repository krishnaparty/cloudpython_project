from datetime import date

from pydantic import BaseModel


class DailyCostPrediction(BaseModel):
    forecast_date: date
    predicted_cost: float


class CostForecastResponse(BaseModel):
    aws_account_id: str
    currency: str
    model_name: str

    training_start_date: date
    training_end_date: date
    training_days: int

    historical_average_daily_cost: float
    validation_mae: float

    forecast_days: int
    projected_total_cost: float
    projected_average_daily_cost: float

    daily_trend: float
    trend_direction: str

    predictions: list[DailyCostPrediction]

    warning: str