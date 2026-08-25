from datetime import date, datetime

from pydantic import BaseModel


class ResourceOverview(BaseModel):
    total: int
    running: int
    stopped: int
    other_states: int
    compliant: int
    non_compliant: int


class SeverityOverview(BaseModel):
    total: int
    high: int
    medium: int
    low: int


class CostHistoryPoint(BaseModel):
    cost_date: date
    total_cost: float
    currency: str
    estimated: bool


class DashboardOverviewResponse(BaseModel):
    user_role: str

    resources: ResourceOverview
    recommendations: SeverityOverview
    anomalies: SeverityOverview

    cost_visible: bool
    month_to_date_cost: float | None
    latest_cost_date: date | None
    recent_cost_history: list[CostHistoryPoint]

    resources_last_synced_at: datetime | None
    generated_at: datetime