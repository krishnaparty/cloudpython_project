from datetime import date

from pydantic import BaseModel


class ServiceCost(BaseModel):
    """Ek AWS service ka cost."""

    service: str
    amount: float


class MonthlyCost(BaseModel):
    """Ek month ka complete cost breakdown."""

    start_date: date
    end_date: date
    total: float
    estimated: bool
    services: list[ServiceCost]


class CostSummaryResponse(BaseModel):
    """Cost summary endpoint ka final response."""

    start_date: date
    end_date: date
    currency: str
    total_cost: float
    months: list[MonthlyCost]