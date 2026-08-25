import math
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.models.metric_anomaly import MetricAnomaly
from app.models.resource_metric_snapshot import (
    ResourceMetricSnapshot,
)


MODEL_NAME = "IsolationForest-v1"
MINIMUM_POINTS = 168


def _build_features(
    snapshots: list[ResourceMetricSnapshot],
) -> np.ndarray:
    """
    Database snapshots ko ML feature matrix mein convert karta hai.

    Features:
    1. Average CPU
    2. Maximum CPU
    3. Maximum aur average ke beech difference
    4. Hour sine
    5. Hour cosine
    """

    features = []

    for snapshot in snapshots:
        hour = snapshot.metric_timestamp.hour

        hour_sin = math.sin(
            2 * math.pi * hour / 24
        )

        hour_cos = math.cos(
            2 * math.pi * hour / 24
        )

        cpu_spread = (
            snapshot.maximum_value
            - snapshot.average_value
        )

        features.append(
            [
                snapshot.average_value,
                snapshot.maximum_value,
                cpu_spread,
                hour_sin,
                hour_cos,
            ]
        )

    return np.asarray(features, dtype=float)


def _get_severity(
    score: float,
    anomaly_scores: list[float],
) -> str:
    """
    Relative anomaly score ke basis par severity decide karta hai.
    Lower score means more abnormal.
    """

    if not anomaly_scores:
        return "LOW"

    lower_quartile = float(
        np.quantile(anomaly_scores, 0.25)
    )

    median_score = float(
        np.quantile(anomaly_scores, 0.50)
    )

    if score <= lower_quartile:
        return "HIGH"

    if score <= median_score:
        return "MEDIUM"

    return "LOW"


def detect_cpu_anomalies(
    db: Session,
    contamination: float = 0.05,
) -> dict[str, Any]:
    """
    Har resource ke CPU dataset par separate Isolation Forest
    train karke anomalies detect karta hai.
    """

    resource_rows = (
        db.query(
            ResourceMetricSnapshot.resource_db_id
        )
        .distinct()
        .all()
    )

    resource_ids = [
        row.resource_db_id
        for row in resource_rows
    ]

    resources_trained = 0
    resources_skipped = 0
    points_analyzed = 0
    anomalies_detected = 0

    try:
        for resource_db_id in resource_ids:
            snapshots = (
                db.query(ResourceMetricSnapshot)
                .filter(
                    ResourceMetricSnapshot.resource_db_id
                    == resource_db_id,
                    ResourceMetricSnapshot.metric_name
                    == "CPUUtilization",
                )
                .order_by(
                    ResourceMetricSnapshot.metric_timestamp
                )
                .all()
            )

            if len(snapshots) < MINIMUM_POINTS:
                resources_skipped += 1
                continue

            features = _build_features(snapshots)

            pipeline = Pipeline(
                steps=[
                    (
                        "scaler",
                        StandardScaler(),
                    ),
                    (
                        "model",
                        IsolationForest(
                            n_estimators=200,
                            contamination=contamination,
                            random_state=42,
                            n_jobs=-1,
                        ),
                    ),
                ]
            )

            predictions = pipeline.fit_predict(features)
            scores = pipeline.decision_function(features)

            points_analyzed += len(snapshots)
            resources_trained += 1

            anomaly_indexes = [
                index
                for index, prediction in enumerate(predictions)
                if prediction == -1
            ]

            anomaly_scores = [
                float(scores[index])
                for index in anomaly_indexes
            ]

            # Previous results inactive mark honge.
            (
                db.query(MetricAnomaly)
                .filter(
                    MetricAnomaly.resource_db_id
                    == resource_db_id,
                    MetricAnomaly.model_name
                    == MODEL_NAME,
                    MetricAnomaly.is_active.is_(True),
                )
                .update(
                    {
                        MetricAnomaly.is_active: False,
                    },
                    synchronize_session=False,
                )
            )

            for index in anomaly_indexes:
                snapshot = snapshots[index]
                score = round(float(scores[index]), 6)

                severity = _get_severity(
                    score=score,
                    anomaly_scores=anomaly_scores,
                )

                reason = (
                    "Isolation Forest ne is hourly CPU pattern "
                    "ko resource ke normal historical behaviour "
                    f"se different detect kiya. Average CPU "
                    f"{snapshot.average_value:.2f}% aur maximum "
                    f"CPU {snapshot.maximum_value:.2f}% tha."
                )

                existing_anomaly = (
                    db.query(MetricAnomaly)
                    .filter(
                        MetricAnomaly.metric_snapshot_id
                        == snapshot.id,
                        MetricAnomaly.model_name
                        == MODEL_NAME,
                    )
                    .first()
                )

                if existing_anomaly:
                    existing_anomaly.anomaly_score = score
                    existing_anomaly.severity = severity
                    existing_anomaly.reason = reason
                    existing_anomaly.is_active = True

                else:
                    db.add(
                        MetricAnomaly(
                            resource_db_id=resource_db_id,
                            metric_snapshot_id=snapshot.id,
                            model_name=MODEL_NAME,
                            anomaly_score=score,
                            severity=severity,
                            reason=reason,
                            is_active=True,
                        )
                    )

                anomalies_detected += 1

        db.commit()

        return {
            "resources_found": len(resource_ids),
            "resources_trained": resources_trained,
            "resources_skipped": resources_skipped,
            "points_analyzed": points_analyzed,
            "anomalies_detected": anomalies_detected,
            "model_name": MODEL_NAME,
        }

    except Exception:
        db.rollback()
        raise