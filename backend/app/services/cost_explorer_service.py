from datetime import date
from decimal import Decimal
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from app.services.aws_service import AWSServiceError, create_aws_session


def _get_start_date(months: int) -> date:
    """
    Current month ko include karke requested months ki
    starting date return karta hai.
    """

    today = date.today()

    month_index = (
        today.year * 12
        + today.month
        - 1
        - (months - 1)
    )

    start_year = month_index // 12
    start_month = month_index % 12 + 1

    start_date = date(start_year, start_month, 1)

    # Month ki first date par Start aur End same na ho.
    if start_date >= today:
        previous_month_index = month_index - 1

        start_date = date(
            previous_month_index // 12,
            previous_month_index % 12 + 1,
            1,
        )

    return start_date


def get_cost_summary(months: int = 3) -> dict[str, Any]:
    """
    AWS Cost Explorer se monthly service-wise cost fetch karta hai.
    """

    start_date = _get_start_date(months)
    end_date = date.today()

    try:
        session = create_aws_session()

        # Cost Explorer ka endpoint us-east-1 mein hota hai.
        client = session.client(
            "ce",
            region_name="us-east-1",
        )

        request_parameters: dict[str, Any] = {
            "TimePeriod": {
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
            "Granularity": "MONTHLY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [
                {
                    "Type": "DIMENSION",
                    "Key": "SERVICE",
                }
            ],
        }

        monthly_data: dict[str, dict[str, Any]] = {}
        next_page_token: str | None = None
        currency = "USD"

        while True:
            if next_page_token:
                request_parameters["NextPageToken"] = next_page_token

            response = client.get_cost_and_usage(
                **request_parameters
            )

            for result in response.get("ResultsByTime", []):
                period_start = result["TimePeriod"]["Start"]
                period_end = result["TimePeriod"]["End"]

                if period_start not in monthly_data:
                    monthly_data[period_start] = {
                        "start_date": period_start,
                        "end_date": period_end,
                        "estimated": False,
                        "total": Decimal("0"),
                        "services": {},
                    }

                month_entry = monthly_data[period_start]

                month_entry["estimated"] = (
                    month_entry["estimated"]
                    or result.get("Estimated", False)
                )

                for group in result.get("Groups", []):
                    service_name = group["Keys"][0]

                    metric = group["Metrics"]["UnblendedCost"]
                    amount = Decimal(metric["Amount"])
                    currency = metric.get("Unit", currency)

                    existing_amount = month_entry["services"].get(
                        service_name,
                        Decimal("0"),
                    )

                    month_entry["services"][service_name] = (
                        existing_amount + amount
                    )

                    month_entry["total"] += amount

            next_page_token = response.get("NextPageToken")

            if not next_page_token:
                break

        months_response: list[dict[str, Any]] = []
        grand_total = Decimal("0")

        for period_start in sorted(monthly_data):
            month_entry = monthly_data[period_start]
            grand_total += month_entry["total"]

            sorted_services = sorted(
                month_entry["services"].items(),
                key=lambda item: item[1],
                reverse=True,
            )

            services = [
                {
                    "service": service_name,
                    "amount": round(float(amount), 6),
                }
                for service_name, amount in sorted_services
            ]

            months_response.append(
                {
                    "start_date": month_entry["start_date"],
                    "end_date": month_entry["end_date"],
                    "total": round(
                        float(month_entry["total"]),
                        6,
                    ),
                    "estimated": month_entry["estimated"],
                    "services": services,
                }
            )

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "currency": currency,
            "total_cost": round(float(grand_total), 6),
            "months": months_response,
        }

    except ClientError as error:
        error_details = error.response.get("Error", {})
        error_code = error_details.get("Code", "AWSClientError")
        error_message = error_details.get(
            "Message",
            "Unable to fetch AWS cost information.",
        )

        raise AWSServiceError(
            f"Cost Explorer error ({error_code}): {error_message}"
        ) from error

    except BotoCoreError as error:
        raise AWSServiceError(
            f"AWS connection error: {error}"
        ) from error