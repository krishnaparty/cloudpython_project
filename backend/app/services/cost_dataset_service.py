from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.models.daily_cost_snapshot import DailyCostSnapshot
from app.services.aws_service import (
    AWSServiceError,
    create_aws_session,
    get_aws_identity,
)


MINIMUM_FORECAST_DAYS = 14


def collect_daily_cost_dataset(
    db: Session,
    lookback_days: int = 90,
) -> dict[str, Any]:
    """
    AWS Cost Explorer se daily service-wise cost fetch
    karke MySQL mein save karta hai.
    """

    end_date = date.today()

    # End date Cost Explorer mein exclusive hoti hai.
    start_date = end_date - timedelta(days=lookback_days)

    try:
        identity = get_aws_identity()
        aws_account_id = identity["Account"]

        session = create_aws_session()

        # Cost Explorer endpoint us-east-1 mein hota hai.
        cost_client = session.client(
            "ce",
            region_name="us-east-1",
        )

        parameters: dict[str, Any] = {
            "TimePeriod": {
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE",
                }
            ],
        }

        daily_data: dict[str, dict[str, Any]] = {}
        next_page_token: str | None = None
        api_pages_requested = 0

        while True:
            if next_page_token:
                parameters["NextPageToken"] = next_page_token

            response = cost_client.get_cost_and_usage(
                **parameters
            )

            api_pages_requested += 1

            for result in response.get("ResultsByTime", []):
                cost_date = result["TimePeriod"]["Start"]

                if cost_date not in daily_data:
                    daily_data[cost_date] = {
                        "total": Decimal("0"),
                        "currency": "USD",
                        "estimated": False,
                        "services": {},
                    }

                day_entry = daily_data[cost_date]

                day_entry["estimated"] = (
                    day_entry["estimated"]
                    or result.get("Estimated", False)
                )

                for group in result.get("Groups", []):
                    service_name = group["Keys"][0]

                    metric = group["Metrics"]["UnblendedCost"]
                    amount = Decimal(metric["Amount"])
                    currency = metric.get("Unit", "USD")

                    existing_amount = day_entry[
                        "services"
                    ].get(
                        service_name,
                        Decimal("0"),
                    )

                    day_entry["services"][service_name] = (
                        existing_amount + amount
                    )

                    day_entry["total"] += amount
                    day_entry["currency"] = currency

            next_page_token = response.get("NextPageToken")

            if not next_page_token:
                break

        records = []

        for cost_date_string, day_entry in daily_data.items():
            service_breakdown = {
                service_name: round(float(amount), 6)
                for service_name, amount
                in day_entry["services"].items()
            }

            records.append(
                {
                    "aws_account_id": aws_account_id,
                    "cost_date": date.fromisoformat(
                        cost_date_string
                    ),
                    "total_cost": day_entry["total"],
                    "currency": day_entry["currency"],
                    "estimated": day_entry["estimated"],
                    "service_breakdown": service_breakdown,
                }
            )

        if records:
            insert_statement = mysql_insert(
                DailyCostSnapshot
            ).values(records)

            upsert_statement = (
                insert_statement.on_duplicate_key_update(
                    total_cost=insert_statement.inserted.total_cost,
                    currency=insert_statement.inserted.currency,
                    estimated=insert_statement.inserted.estimated,
                    service_breakdown=(
                        insert_statement.inserted.service_breakdown
                    ),
                    updated_at=func.now(),
                )
            )

            db.execute(upsert_statement)

        db.commit()

        return {
            "start_date": start_date,
            "end_date": end_date,
            "api_pages_requested": api_pages_requested,
            "days_fetched": len(daily_data),
            "days_saved": len(records),
        }

    except ClientError as error:
        db.rollback()

        details = error.response.get("Error", {})
        error_code = details.get("Code", "AWSClientError")
        error_message = details.get(
            "Message",
            "Unable to fetch cost data.",
        )

        raise AWSServiceError(
            f"Cost Explorer error "
            f"({error_code}): {error_message}"
        ) from error

    except BotoCoreError as error:
        db.rollback()

        raise AWSServiceError(
            f"AWS connection error: {error}"
        ) from error

    except Exception:
        db.rollback()
        raise


def get_cost_dataset_summary(
    db: Session,
) -> dict[str, Any]:
    """
    Forecasting dataset ki readiness check karta hai.
    """

    total_days = (
        db.query(func.count(DailyCostSnapshot.id))
        .scalar()
        or 0
    )

    earliest_date = (
        db.query(func.min(DailyCostSnapshot.cost_date))
        .scalar()
    )

    latest_date = (
        db.query(func.max(DailyCostSnapshot.cost_date))
        .scalar()
    )

    total_cost = (
        db.query(func.sum(DailyCostSnapshot.total_cost))
        .scalar()
        or Decimal("0")
    )

    aws_account_id = (
        db.query(DailyCostSnapshot.aws_account_id)
        .order_by(DailyCostSnapshot.id.desc())
        .limit(1)
        .scalar()
    )

    return {
        "aws_account_id": aws_account_id,
        "total_days": total_days,
        "earliest_date": earliest_date,
        "latest_date": latest_date,
        "total_cost": round(float(total_cost), 6),
        "minimum_required_days": MINIMUM_FORECAST_DAYS,
        "ready_for_forecasting": (
            total_days >= MINIMUM_FORECAST_DAYS
        ),
    }