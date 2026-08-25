import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router";

import { apiRequest } from "../api/client";
import { isAuthenticated } from "../auth/auth";
import { CostChart } from "../components/CostChart";
import type {
  DashboardOverview,
} from "../types/dashboard";

export function DashboardPage() {
  const navigate = useNavigate();

  const [dashboard, setDashboard] =
    useState<DashboardOverview | null>(null);

  const [error, setError] = useState("");
  const [isLoading, setIsLoading] =
    useState(true);

  const loadDashboard = useCallback(
    async () => {
      setError("");
      setIsLoading(true);

      try {
        const response =
          await apiRequest<DashboardOverview>(
            "/api/dashboard/overview",
          );

        setDashboard(response);
      } catch (requestError) {
        if (!isAuthenticated()) {
          navigate("/login", {
            replace: true,
          });

          return;
        }

        const message =
          requestError instanceof Error
            ? requestError.message
            : "Dashboard load failed.";

        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [navigate],
  );

  useEffect(() => {
  void loadDashboard();

  const intervalId = window.setInterval(() => {
    void loadDashboard();
  }, 30000);

  return () => {
    window.clearInterval(intervalId);
  };
}, [loadDashboard]);

  if (isLoading) {
    return (
      <div className="loading-card">
        Loading dashboard data...
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="error-card">
        <h2>Dashboard unavailable</h2>
        <p>
          {error || "Dashboard data nahi mila."}
        </p>

        <button
          onClick={() => void loadDashboard()}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <main className="dashboard-page">
      <header className="page-header">
        <div>
          <span className="eyebrow">
            Dashboard
          </span>

          <h1>Cloud overview</h1>

          <p>
            Resource governance and AI-driven
            monitoring summary.
          </p>
        </div>

        <div className="page-header-actions">
          <span className="role-badge">
            {dashboard.user_role}
          </span>

          <button
            className="secondary-button"
            onClick={() =>
              void loadDashboard()
            }
          >
            Refresh
          </button>
        </div>
      </header>

      <section className="metric-grid">
        <article className="metric-card">
          <p>Total Resources</p>
          <h2>{dashboard.resources.total}</h2>
          <span className="positive-text">
            {dashboard.resources.running} running
          </span>
        </article>

        <article className="metric-card">
          <p>Stopped Resources</p>
          <h2>{dashboard.resources.stopped}</h2>
          <span>
            {dashboard.resources.other_states} in
            other states
          </span>
        </article>

        <article className="metric-card">
          <p>Non-compliant</p>
          <h2>
            {dashboard.resources.non_compliant}
          </h2>
          <span className="danger-text">
            Missing governance tags
          </span>
        </article>

        <article className="metric-card">
          <p>Open Recommendations</p>
          <h2>
            {dashboard.recommendations.total}
          </h2>
          <span>
            {dashboard.recommendations.high} high
            severity
          </span>
        </article>

        <article className="metric-card">
          <p>ML Anomalies</p>
          <h2>{dashboard.anomalies.total}</h2>
          <span>
            {dashboard.anomalies.high} high
            severity
          </span>
        </article>

        {dashboard.cost_visible && (
          <article className="metric-card accent-card">
            <p>Month-to-date Cost</p>

            <h2>
              $
              {dashboard.month_to_date_cost?.toFixed(
                2,
              ) ?? "0.00"}
            </h2>

            <span>
              Latest data:{" "}
              {dashboard.latest_cost_date ??
                "Unavailable"}
            </span>
          </article>
        )}
      </section>

      <section className="dashboard-content-grid">
        {dashboard.cost_visible && (
          <article className="content-card chart-card">
            <div className="card-heading">
              <div>
                <h2>Daily AWS Cost</h2>
                <p>
                  Recent Cost Explorer dataset
                </p>
              </div>

              <span className="small-badge">
                USD
              </span>
            </div>

            <CostChart
              data={
                dashboard.recent_cost_history
              }
            />
          </article>
        )}

        <article className="content-card">
          <div className="card-heading">
            <div>
              <h2>Governance status</h2>
              <p>Resource compliance overview</p>
            </div>
          </div>

          <div className="status-list">
            <div className="status-row">
              <span>Compliant resources</span>
              <strong className="positive-text">
                {dashboard.resources.compliant}
              </strong>
            </div>

            <div className="status-row">
              <span>Non-compliant resources</span>
              <strong className="danger-text">
                {
                  dashboard.resources
                    .non_compliant
                }
              </strong>
            </div>

            <div className="status-row">
              <span>High recommendations</span>
              <strong>
                {dashboard.recommendations.high}
              </strong>
            </div>

            <div className="status-row">
              <span>High ML anomalies</span>
              <strong>
                {dashboard.anomalies.high}
              </strong>
            </div>
          </div>
        </article>
      </section>

      <footer className="dashboard-footer">
        Last resource sync:{" "}
        {dashboard.resources_last_synced_at
          ? new Date(
              dashboard.resources_last_synced_at,
            ).toLocaleString("en-IN")
          : "Not synced"}
      </footer>
    </main>
  );
}