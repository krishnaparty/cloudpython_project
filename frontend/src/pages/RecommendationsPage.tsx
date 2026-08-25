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
  CurrentUser,
  OptimizationRecommendation,
  OptimizationScanResponse,
} from "../types/recommendation";

type RecommendationStatus =
  | "OPEN"
  | "RESOLVED"
  | "IGNORED";

type SeverityFilter =
  | "ALL"
  | "HIGH"
  | "MEDIUM"
  | "LOW";


function formatRecommendationType(
  value: string,
): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}


export function RecommendationsPage() {
  const navigate = useNavigate();

  const [recommendations, setRecommendations] =
    useState<OptimizationRecommendation[]>([]);

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);

  const [statusFilter, setStatusFilter] =
    useState<RecommendationStatus>("OPEN");

  const [severityFilter, setSeverityFilter] =
    useState<SeverityFilter>("ALL");

  const [searchText, setSearchText] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(true);

  const [isScanning, setIsScanning] =
    useState(false);

  const [error, setError] = useState("");
  const [scanMessage, setScanMessage] =
    useState("");


  const loadRecommendations = useCallback(
    async () => {
      setIsLoading(true);
      setError("");

      try {
        const response = await apiRequest<
          OptimizationRecommendation[]
        >(
          `/api/optimization/recommendations?status=${statusFilter}`,
        );

        setRecommendations(response);
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
            : "Recommendations load nahi hui.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [navigate, statusFilter],
  );


  useEffect(() => {
    void loadRecommendations();
  }, [loadRecommendations]);


  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const user =
          await apiRequest<CurrentUser>(
            "/api/auth/me",
          );

        setCurrentUser(user);
      } catch {
        // Recommendations request authentication
        // error ko separately handle karegi.
      }
    }

    void loadCurrentUser();
  }, []);


  const filteredRecommendations =
    useMemo(() => {
      const normalizedSearch =
        searchText.trim().toLowerCase();

      return recommendations.filter(
        (recommendation) => {
          const searchableText = [
            recommendation.resource_id,
            recommendation.resource_name,
            recommendation.recommendation_type,
            recommendation.reason,
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
            recommendation.severity.toUpperCase() ===
              severityFilter;

          return (
            matchesSearch &&
            matchesSeverity
          );
        },
      );
    }, [
      recommendations,
      searchText,
      severityFilter,
    ]);


  const summary = useMemo(
    () => ({
      total: recommendations.length,

      high: recommendations.filter(
        (item) =>
          item.severity.toUpperCase() ===
          "HIGH",
      ).length,

      medium: recommendations.filter(
        (item) =>
          item.severity.toUpperCase() ===
          "MEDIUM",
      ).length,

      low: recommendations.filter(
        (item) =>
          item.severity.toUpperCase() ===
          "LOW",
      ).length,
    }),
    [recommendations],
  );


  const isAdmin =
    currentUser?.role.toUpperCase() === "ADMIN";


  async function runOptimizationScan() {
    setIsScanning(true);
    setScanMessage("");
    setError("");

    try {
      const response =
        await apiRequest<OptimizationScanResponse>(
          "/api/optimization/scan?lookback_days=7",
          {
            method: "POST",
          },
        );

      setScanMessage(
        `Scan complete: ${response.scanned_resources} scanned, ` +
          `${response.recommendations_created} created, ` +
          `${response.recommendations_updated} updated, ` +
          `${response.healthy_resources} healthy.`,
      );

      await loadRecommendations();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Optimization scan failed.",
      );
    } finally {
      setIsScanning(false);
    }
  }


  return (
    <main className="recommendations-page">
      <header className="page-header">
        <div>
          <span className="eyebrow">
            Cost optimization
          </span>

          <h1>Recommendations</h1>

          <p>
            Explainable CloudWatch-based resource
            optimization suggestions.
          </p>
        </div>

        {isAdmin && (
          <button
            className="primary-button"
            disabled={isScanning}
            onClick={() =>
              void runOptimizationScan()
            }
          >
            {isScanning
              ? "Scanning..."
              : "Run optimization scan"}
          </button>
        )}
      </header>

      {scanMessage && (
        <div className="success-message">
          {scanMessage}
        </div>
      )}

      {error && (
        <div className="inline-error">
          {error}
        </div>
      )}

      <section className="compact-metric-grid">
        <article className="compact-metric-card">
          <span>Total</span>
          <strong>{summary.total}</strong>
        </article>

        <article className="compact-metric-card">
          <span>High</span>
          <strong className="danger-text">
            {summary.high}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Medium</span>
          <strong className="warning-text">
            {summary.medium}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Low</span>
          <strong>{summary.low}</strong>
        </article>
      </section>

      <section className="content-card">
        <div className="recommendation-toolbar">
          <input
            className="search-input"
            type="search"
            value={searchText}
            onChange={(event) =>
              setSearchText(event.target.value)
            }
            placeholder="Search resource, type or reason..."
          />

          <select
            className="filter-select"
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target
                  .value as RecommendationStatus,
              )
            }
          >
            <option value="OPEN">
              Open
            </option>

            <option value="RESOLVED">
              Resolved
            </option>

            <option value="IGNORED">
              Ignored
            </option>
          </select>

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
          Showing{" "}
          {filteredRecommendations.length} of{" "}
          {recommendations.length} recommendations
        </div>

        {isLoading ? (
          <div className="empty-state">
            Loading recommendations...
          </div>
        ) : filteredRecommendations.length ===
          0 ? (
          <div className="empty-state">
            Is filter ke liye koi recommendation
            available nahi hai.
          </div>
        ) : (
          <div className="recommendation-list">
            {filteredRecommendations.map(
              (recommendation) => (
                <article
                  className="recommendation-card"
                  key={recommendation.id}
                >
                  <div className="recommendation-header">
                    <div>
                      <span
                        className={`severity-badge severity-${recommendation.severity.toLowerCase()}`}
                      >
                        {recommendation.severity}
                      </span>

                      <h2>
                        {formatRecommendationType(
                          recommendation.recommendation_type,
                        )}
                      </h2>
                    </div>

                    <span className="status-badge">
                      {recommendation.status}
                    </span>
                  </div>

                  <div className="recommendation-resource">
                    <strong>
                      {recommendation.resource_name ||
                        "Unnamed resource"}
                    </strong>

                    <code>
                      {recommendation.resource_id}
                    </code>
                  </div>

                  <p className="recommendation-reason">
                    {recommendation.reason}
                  </p>

                  <div className="recommendation-metrics">
                    <div>
                      <span>Average CPU</span>
                      <strong>
                        {recommendation.average_cpu !==
                        null
                          ? `${recommendation.average_cpu.toFixed(
                              2,
                            )}%`
                          : "N/A"}
                      </strong>
                    </div>

                    <div>
                      <span>Maximum CPU</span>
                      <strong>
                        {recommendation.maximum_cpu !==
                        null
                          ? `${recommendation.maximum_cpu.toFixed(
                              2,
                            )}%`
                          : "N/A"}
                      </strong>
                    </div>

                    <div>
                      <span>Analysis period</span>
                      <strong>
                        {
                          recommendation.lookback_days
                        }{" "}
                        days
                      </strong>
                    </div>

                    <div>
                      <span>Last updated</span>
                      <strong>
                        {new Date(
                          recommendation.updated_at,
                        ).toLocaleDateString(
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