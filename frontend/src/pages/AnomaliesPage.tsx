import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router";

import { apiRequest } from "../api/client";
import { isAuthenticated } from "../auth/auth";
import type {
  AnomalyDetectionResponse,
  CurrentUser,
  DatasetSummary,
  MetricAnomaly,
  MetricCollectionResponse,
} from "../types/anomaly";

type SeverityFilter =
  | "ALL"
  | "HIGH"
  | "MEDIUM"
  | "LOW";


export function AnomaliesPage() {
  const navigate = useNavigate();

  const [anomalies, setAnomalies] =
    useState<MetricAnomaly[]>([]);

  const [datasetSummary, setDatasetSummary] =
    useState<DatasetSummary | null>(null);

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);

  const [lookbackDays, setLookbackDays] =
    useState(7);

  const [severityFilter, setSeverityFilter] =
    useState<SeverityFilter>("ALL");

  const [searchText, setSearchText] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(true);

  const [isCollecting, setIsCollecting] =
    useState(false);

  const [isDetecting, setIsDetecting] =
    useState(false);

  const [error, setError] = useState("");

  const [actionMessage, setActionMessage] =
    useState("");


  const loadPageData = useCallback(
    async () => {
      setIsLoading(true);
      setError("");

      try {
        const [
          summaryResponse,
          anomalyResponse,
          userResponse,
        ] = await Promise.all([
          apiRequest<DatasetSummary>(
            "/api/ml/dataset/summary",
          ),

          apiRequest<MetricAnomaly[]>(
            "/api/ml/anomalies?active_only=true&limit=100",
          ),

          apiRequest<CurrentUser>(
            "/api/auth/me",
          ),
        ]);

        setDatasetSummary(summaryResponse);
        setAnomalies(anomalyResponse);
        setCurrentUser(userResponse);
      } catch (requestError) {
        if (!isAuthenticated()) {
          navigate("/login", {
            replace: true,
          });

          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "ML anomaly data load nahi hua.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [navigate],
  );


  useEffect(() => {
    void loadPageData();
  }, [loadPageData]);


  const filteredAnomalies = useMemo(() => {
    const normalizedSearch =
      searchText.trim().toLowerCase();

    return anomalies.filter((anomaly) => {
      const searchableText = [
        anomaly.resource_id,
        anomaly.resource_name,
        anomaly.metric_name,
        anomaly.reason,
        anomaly.model_name,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        normalizedSearch.length === 0 ||
        searchableText.includes(
          normalizedSearch,
        );

      const matchesSeverity =
        severityFilter === "ALL" ||
        anomaly.severity.toUpperCase() ===
          severityFilter;

      return (
        matchesSearch &&
        matchesSeverity
      );
    });
  }, [
    anomalies,
    searchText,
    severityFilter,
  ]);


  const severitySummary = useMemo(
    () => ({
      total: anomalies.length,

      high: anomalies.filter(
        (item) =>
          item.severity.toUpperCase() ===
          "HIGH",
      ).length,

      medium: anomalies.filter(
        (item) =>
          item.severity.toUpperCase() ===
          "MEDIUM",
      ).length,

      low: anomalies.filter(
        (item) =>
          item.severity.toUpperCase() ===
          "LOW",
      ).length,
    }),
    [anomalies],
  );


  const isAdmin =
    currentUser?.role.toUpperCase() === "ADMIN";


  async function collectMetrics() {
    setIsCollecting(true);
    setError("");
    setActionMessage("");

    try {
      const response =
        await apiRequest<MetricCollectionResponse>(
          `/api/ml/dataset/collect?lookback_days=${lookbackDays}`,
          {
            method: "POST",
          },
        );

      setActionMessage(
        `Collection complete: ${response.resources_scanned} resources, ` +
          `${response.datapoints_fetched} fetched, ` +
          `${response.datapoints_saved} saved.`,
      );

      await loadPageData();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Metric collection failed.",
      );
    } finally {
      setIsCollecting(false);
    }
  }


  async function detectAnomalies() {
    setIsDetecting(true);
    setError("");
    setActionMessage("");

    try {
      const response =
        await apiRequest<AnomalyDetectionResponse>(
          "/api/ml/anomalies/detect?contamination=0.05",
          {
            method: "POST",
          },
        );

      setActionMessage(
        `ML detection complete: ${response.resources_trained} trained, ` +
          `${response.resources_skipped} skipped, ` +
          `${response.points_analyzed} points analysed, ` +
          `${response.anomalies_detected} anomalies detected.`,
      );

      await loadPageData();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Anomaly detection failed.",
      );
    } finally {
      setIsDetecting(false);
    }
  }


  if (isLoading) {
    return (
      <div className="loading-card">
        Loading ML dataset...
      </div>
    );
  }


  return (
    <main className="anomalies-page">
      <header className="page-header">
        <div>
          <span className="eyebrow">
            Machine learning
          </span>

          <h1>CPU Anomaly Detection</h1>

          <p>
            Isolation Forest-based unusual EC2
            utilization detection.
          </p>
        </div>

        {isAdmin && (
          <div className="ml-actions">
            <select
              className="filter-select"
              value={lookbackDays}
              onChange={(event) =>
                setLookbackDays(
                  Number(event.target.value),
                )
              }
            >
              <option value={7}>Last 7 days</option>
              <option value={14}>
                Last 14 days
              </option>
              <option value={30}>
                Last 30 days
              </option>
            </select>

            <button
              className="secondary-button"
              disabled={isCollecting}
              onClick={() =>
                void collectMetrics()
              }
            >
              {isCollecting
                ? "Collecting..."
                : "Collect metrics"}
            </button>

            <button
              className="primary-button"
              disabled={isDetecting}
              onClick={() =>
                void detectAnomalies()
              }
            >
              {isDetecting
                ? "Running model..."
                : "Detect anomalies"}
            </button>
          </div>
        )}
      </header>

      {actionMessage && (
        <div className="success-message">
          {actionMessage}
        </div>
      )}

      {error && (
        <div className="inline-error">
          {error}
        </div>
      )}

      {datasetSummary && (
        <div
          className={
            datasetSummary.ready_for_ml
              ? "readiness-banner readiness-ready"
              : "readiness-banner readiness-waiting"
          }
        >
          <div>
            <strong>
              {datasetSummary.ready_for_ml
                ? "Dataset ready for ML"
                : "More data required"}
            </strong>

            <span>
              Minimum points per resource:{" "}
              {
                datasetSummary.minimum_points_per_resource
              }
              {" / "}
              {
                datasetSummary.recommended_minimum_points
              }
            </span>
          </div>

          <span>
            {datasetSummary.resource_count}{" "}
            resources
          </span>
        </div>
      )}

      <section className="compact-metric-grid">
        <article className="compact-metric-card">
          <span>Data points</span>
          <strong>
            {datasetSummary?.total_datapoints ??
              0}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Active anomalies</span>
          <strong>
            {severitySummary.total}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>High</span>
          <strong className="danger-text">
            {severitySummary.high}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Medium</span>
          <strong className="warning-text">
            {severitySummary.medium}
          </strong>
        </article>
      </section>

      <section className="content-card">
        <div className="anomaly-toolbar">
          <input
            className="search-input"
            type="search"
            value={searchText}
            onChange={(event) =>
              setSearchText(event.target.value)
            }
            placeholder="Search resource, metric or model..."
          />

          <select
            className="filter-select"
            value={severityFilter}
            onChange={(event) =>
              setSeverityFilter(
                event.target
                  .value as SeverityFilter,
              )
            }
          >
            <option value="ALL">
              All severity
            </option>

            <option value="HIGH">
              High
            </option>

            <option value="MEDIUM">
              Medium
            </option>

            <option value="LOW">
              Low
            </option>
          </select>
        </div>

        <div className="table-result-count">
          Showing {filteredAnomalies.length}{" "}
          active anomalies
        </div>

        {filteredAnomalies.length === 0 ? (
          <div className="empty-state">
            No active anomalies available.
            Collect metrics and run the model.
          </div>
        ) : (
          <div className="anomaly-list">
            {filteredAnomalies.map(
              (anomaly) => (
                <article
                  className="anomaly-card"
                  key={anomaly.id}
                >
                  <div className="anomaly-card-header">
                    <div>
                      <span
                        className={`severity-badge severity-${anomaly.severity.toLowerCase()}`}
                      >
                        {anomaly.severity}
                      </span>

                      <h2>
                        {anomaly.resource_name ||
                          "Unnamed resource"}
                      </h2>

                      <code>
                        {anomaly.resource_id}
                      </code>
                    </div>

                    <span className="model-badge">
                      {anomaly.model_name}
                    </span>
                  </div>

                  <p>{anomaly.reason}</p>

                  <div className="anomaly-values">
                    <div>
                      <span>Average CPU</span>
                      <strong>
                        {anomaly.average_value.toFixed(
                          2,
                        )}
                        %
                      </strong>
                    </div>

                    <div>
                      <span>Maximum CPU</span>
                      <strong>
                        {anomaly.maximum_value.toFixed(
                          2,
                        )}
                        %
                      </strong>
                    </div>

                    <div>
                      <span>Anomaly score</span>
                      <strong>
                        {anomaly.anomaly_score.toFixed(
                          6,
                        )}
                      </strong>
                    </div>

                    <div>
                      <span>Metric time</span>
                      <strong>
                        {new Date(
                          anomaly.metric_timestamp,
                        ).toLocaleString(
                          "en-IN",
                        )}
                      </strong>
                    </div>
                  </div>
                </article>
              ),
            )}
          </div>
        )}
      </section>
    </main>
  );
}