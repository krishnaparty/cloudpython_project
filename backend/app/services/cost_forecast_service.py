import math
from datetime import date, timedelta
from typing import Any

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from sqlalchemy.orm import Session

from app.models.daily_cost_snapshot import DailyCostSnapshot


MODEL_NAME = "LinearRegression-WeeklyTrend-v1"
MINIMUM_TRAINING_DAYS = 14
MINIMUM_NON_ZERO_DAYS = 5


class ForecastDataError(Exception):
    """
    Jab ML training ke liye useful data available na ho.
    """


def _build_features(
    dates: list[date],
    origin_date: date,
) -> np.ndarray:
    """
    Date values ko ML features mein convert karta hai.

    Features:
    1. Time trend
    2. Weekday sine
    3. Weekday cosine
    4. Weekend indicator
    """

    features = []

    for current_date in dates:
        day_index = (
            current_date - origin_date
        ).days

        weekday = current_date.weekday()

        weekday_sin = math.sin(
            2 * math.pi * weekday / 7
        )

        weekday_cos = math.cos(
            2 * math.pi * weekday / 7
        )

        is_weekend = 1 if weekday >= 5 else 0

        features.append(
            [
                day_index,
                weekday_sin,
                weekday_cos,
                is_weekend,
            ]
        )

    return np.asarray(features, dtype=float)


def _validate_training_data(
    costs: np.ndarray,
) -> None:
    """
    Fake ya meaningless forecasting ko prevent karta hai.
    """

    if len(costs) < MINIMUM_TRAINING_DAYS:
        raise ForecastDataError(
            f"Forecasting ke liye minimum "
            f"{MINIMUM_TRAINING_DAYS} daily records chahiye. "
            f"Available records: {len(costs)}."
        )

    non_zero_days = int(
        np.count_nonzero(np.abs(costs) > 0.000001)
    )

    if non_zero_days < MINIMUM_NON_ZERO_DAYS:
        raise ForecastDataError(
            "Dataset mein enough non-zero cost days nahi hain. "
            f"Minimum {MINIMUM_NON_ZERO_DAYS} required hain, "
            f"available {non_zero_days} hain."
        )

    if float(np.std(costs)) < 0.000001:
        raise ForecastDataError(
            "Historical costs constant hain. Model meaningful "
            "trend learn nahi kar sakta."
        )


def generate_cost_forecast(
    db: Session,
    forecast_days: int = 30,
) -> dict[str, Any]:
    """
    Historical daily cost par Linear Regression train karta hai
    aur future cost forecast return karta hai.
    """

    latest_account_id = (
        db.query(DailyCostSnapshot.aws_account_id)
        .order_by(DailyCostSnapshot.cost_date.desc())
        .limit(1)
        .scalar()
    )

    if not latest_account_id:
        raise ForecastDataError(
            "Cost dataset empty hai. Pehle "
            "/api/ml/cost-data/collect endpoint run karo."
        )

    rows = (
        db.query(DailyCostSnapshot)
        .filter(
            DailyCostSnapshot.aws_account_id
            == latest_account_id
        )
        .order_by(DailyCostSnapshot.cost_date.asc())
        .all()
    )

    historical_dates = [
        row.cost_date for row in rows
    ]

    historical_costs = np.asarray(
        [
            float(row.total_cost)
            for row in rows
        ],
        dtype=float,
    )

    _validate_training_data(historical_costs)

    origin_date = historical_dates[0]

    features = _build_features(
        dates=historical_dates,
        origin_date=origin_date,
    )

    # Time-based cross-validation
    time_series_split = TimeSeriesSplit(
        n_splits=3
    )

    validation_errors = []

    for train_indexes, test_indexes in (
        time_series_split.split(features)
    ):
        validation_model = LinearRegression()

        validation_model.fit(
            features[train_indexes],
            historical_costs[train_indexes],
        )

        test_predictions = validation_model.predict(
            features[test_indexes]
        )

        # Negative infrastructure cost useful forecast nahi hai.
        test_predictions = np.maximum(
            test_predictions,
            0,
        )

        fold_mae = mean_absolute_error(
            historical_costs[test_indexes],
            test_predictions,
        )

        validation_errors.append(float(fold_mae))

    validation_mae = float(
        np.mean(validation_errors)
    )

    # Final model complete historical dataset par train hoga.
    final_model = LinearRegression()

    final_model.fit(
        features,
        historical_costs,
    )

    last_historical_date = historical_dates[-1]

    future_dates = [
        last_historical_date + timedelta(days=day_number)
        for day_number in range(1, forecast_days + 1)
    ]

    future_features = _build_features(
        dates=future_dates,
        origin_date=origin_date,
    )

    future_predictions = final_model.predict(
        future_features
    )

    future_predictions = np.maximum(
        future_predictions,
        0,
    )

    prediction_rows = [
        {
            "forecast_date": forecast_date,
            "predicted_cost": round(
                float(predicted_cost),
                6,
            ),
        }
        for forecast_date, predicted_cost
        in zip(
            future_dates,
            future_predictions,
            strict=True,
        )
    ]

    projected_total = float(
        np.sum(future_predictions)
    )

    projected_average = float(
        np.mean(future_predictions)
    )

    historical_average = float(
        np.mean(historical_costs)
    )

    # First coefficient day-index trend ko represent karta hai.
    daily_trend = float(final_model.coef_[0])

    trend_threshold = max(
        historical_average * 0.01,
        0.000001,
    )

    if daily_trend > trend_threshold:
        trend_direction = "INCREASING"

    elif daily_trend < -trend_threshold:
        trend_direction = "DECREASING"

    else:
        trend_direction = "STABLE"

    currency = rows[-1].currency

    return {
        "aws_account_id": latest_account_id,
        "currency": currency,
        "model_name": MODEL_NAME,
        "training_start_date": historical_dates[0],
        "training_end_date": historical_dates[-1],
        "training_days": len(historical_dates),
        "historical_average_daily_cost": round(
            historical_average,
            6,
        ),
        "validation_mae": round(
            validation_mae,
            6,
        ),
        "forecast_days": forecast_days,
        "projected_total_cost": round(
            projected_total,
            6,
        ),
        "projected_average_daily_cost": round(
            projected_average,
            6,
        ),
        "daily_trend": round(
            daily_trend,
            6,
        ),
        "trend_direction": trend_direction,
        "predictions": prediction_rows,
        "warning": (
            "Forecast historical trend par based estimate hai. "
            "Future deployments, credits, pricing changes aur "
            "resource deletion model ko pata nahi hote."
        ),
    }