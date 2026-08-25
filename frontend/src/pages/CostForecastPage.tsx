import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router";

import { apiRequest } from "../api/client";
import { isAuthenticated } from "../auth/auth";
import { ForecastChart } from "../components/ForecastChart";
import type {
  CostDatasetCollection,
  CostDatasetSummary,
  CostForecast,
  CurrentUser,
} from "../types/costForecast";


export function CostForecastPage() {
  const navigate = useNavigate();

  const [summary, setSummary] =
    useState<CostDatasetSummary | null>(null);

  const [forecast, setForecast] =
    useState<CostForecast | null>(null);

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);

  const [forecastDays, setForecastDays] =
    useState(30);

  const [lookbackDays, setLookbackDays] =
    useState(90);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isCollecting, setIsCollecting] =
    useState(false);

  const [isForecasting, setIsForecasting] =
    useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");


  const loadSummary = useCallback(
    async () => {
      setIsLoading(true);
      setError("");

      try {
        const [
          summaryResponse,
          userResponse,
        ] = await Promise.all([
          apiRequest<CostDatasetSummary>(
            "/api/ml/cost-data/summary",
          ),

          apiRequest<CurrentUser>(
            "/api/auth/me",
          ),
        ]);

        setSummary(summaryResponse);
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
            : "Cost dataset load nahi hua.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [navigate],
  );


  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);


  const isAdmin =
    currentUser?.role.toUpperCase() ===
    "ADMIN";


  async function collectCostData() {
    const confirmed = window.confirm(
      "Cost Explorer API request chargeable ho sakti hai. Continue?",
    );

    if (!confirmed) {
      return;
    }

    setIsCollecting(true);
    setMessage("");
    setError("");

    try {
      const response =
        await apiRequest<CostDatasetCollection>(
          `/api/ml/cost-data/collect?lookback_days=${lookbackDays}`,
          {
            method: "POST",
          },
        );

      setMessage(
        `Cost collection complete: ${response.days_fetched} days fetched, ` +
          `${response.days_saved} saved using ` +
          `${response.api_pages_requested} API page(s).`,
      );

      setForecast(null);
      await loadSummary();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Cost collection failed.",
      );
    } finally {
      setIsCollecting(false);
    }
  }


  async function generateForecast() {
    setIsForecasting(true);
    setMessage("");
    setError("");

    try {
      const response =
        await apiRequest<CostForecast>(
          `/api/ml/cost-forecast?forecast_days=${forecastDays}`,
        );

      setForecast(response);

      setMessage(
        `${forecastDays}-day cost forecast generated successfully.`,
      );
    } catch (requestError) {
      setForecast(null);

      setError(
        requestError instanceof Error
          ? requestError.message
          : "Cost forecasting failed.",
      );
    } finally {
      setIsForecasting(false);
    }
  }


  if (isLoading) {
    return (
      <div className="loading-card">
        Loading cost dataset...
      </div>
    );
  }


  return (
    <main className="forecast-page">
      <header className="page-header">
        <div>
          <span className="eyebrow">
            Machine learning
          </span>

          <h1>AWS Cost Forecast</h1>

          <p>
            Historical billing trend-based future
            cloud cost estimation.
          </p>
        </div>

        {isAdmin && (
          <div className="forecast-actions">
            <select
              className="filter-select"
              value={lookbackDays}
              onChange={(event) =>
                setLookbackDays(
                  Number(event.target.value),
                )
              }
            >
              <option value={30}>
                Collect 30 days
              </option>

              <option value={90}>
                Collect 90 days
              </option>

              <option value={180}>
                Collect 180 days
              </option>
            </select>

            <button
              className="secondary-button"
              disabled={isCollecting}
              onClick={() =>
                void collectCostData()
              }
            >
              {isCollecting
                ? "Collecting..."
                : "Collect cost data"}
            </button>
          </div>
        )}
      </header>

      {message && (
        <div className="success-message">
          {message}
        </div>
      )}

      {error && (
        <div className="inline-error">
          {error}
        </div>
      )}

      {summary && (
        <div
          className={
            summary.ready_for_forecasting
              ? "readiness-banner readiness-ready"
              : "readiness-banner readiness-waiting"
          }
        >
          <div>
            <strong>
              {summary.ready_for_forecasting
                ? "Dataset ready"
                : "More cost history required"}
            </strong>

            <span>
              {summary.total_days} /{" "}
              {summary.minimum_required_days}{" "}
              required days
            </span>
          </div>

          <span>
            Account ending{" "}
            {summary.aws_account_id?.slice(-4) ??
              "N/A"}
          </span>
        </div>
      )}

      <section className="compact-metric-grid">
        <article className="compact-metric-card">
          <span>Historical days</span>
          <strong>
            {summary?.total_days ?? 0}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Historical cost</span>
          <strong>
            $
            {summary?.total_cost.toFixed(2) ??
              "0.00"}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Earliest date</span>
          <strong className="date-value">
            {summary?.earliest_date ??
              "N/A"}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Latest date</span>
          <strong className="date-value">
            {summary?.latest_date ??
              "N/A"}
          </strong>
        </article>
      </section>

      <section className="content-card forecast-control-card">
        <div>
          <h2>Generate prediction</h2>

          <p>
            Select future forecast duration.
          </p>
        </div>

        <div className="forecast-control">
          <select
            className="filter-select"
            value={forecastDays}
            onChange={(event) =>
              setForecastDays(
                Number(event.target.value),
              )
            }
          >
            <option value={7}>Next 7 days</option>
            <option value={30}>
              Next 30 days
            </option>
            <option value={60}>
              Next 60 days
            </option>
            <option value={90}>
              Next 90 days
            </option>
          </select>

          <button
            className="primary-button"
            disabled={
              isForecasting ||
              !summary?.ready_for_forecasting
            }
            onClick={() =>
              void generateForecast()
            }
          >
            {isForecasting
              ? "Training model..."
              : "Generate forecast"}
          </button>
        </div>
      </section>

      {forecast && (
        <>
          <section className="metric-grid">
            <article className="metric-card">
              <p>Projected total</p>

              <h2>
                {forecast.currency}{" "}
                {forecast.projected_total_cost.toFixed(
                  2,
                )}
              </h2>

              <span>
                Next {forecast.forecast_days} days
              </span>
            </article>

            <article className="metric-card">
              <p>Average daily cost</p>

              <h2>
                {forecast.currency}{" "}
                {forecast.projected_average_daily_cost.toFixed(
                  4,
                )}
              </h2>

              <span>Forecast average</span>
            </article>

            <article className="metric-card">
              <p>Trend</p>

              <h2>
                {forecast.trend_direction}
              </h2>

              <span>
                Daily coefficient:{" "}
                {forecast.daily_trend.toFixed(6)}
              </span>
            </article>

            <article className="metric-card">
              <p>Validation MAE</p>

              <h2>
                {forecast.validation_mae.toFixed(
                  4,
                )}
              </h2>

              <span>Lower is better</span>
            </article>
          </section>

          <section className="content-card forecast-chart-card">
            <div className="card-heading">
              <div>
                <h2>Predicted daily cost</h2>

                <p>{forecast.model_name}</p>
              </div>

              <span className="model-badge">
                {forecast.training_days} training
                days
              </span>
            </div>

            <ForecastChart
              predictions={forecast.predictions}
              currency={forecast.currency}
            />
          </section>

          <div className="forecast-warning">
            {forecast.warning}
          </div>
        </>
      )}
    </main>
  );
}