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
  CloudResource,
} from "../types/cloudResource";

type ComplianceFilter =
  | "all"
  | "compliant"
  | "non-compliant";

type StateFilter =
  | "all"
  | "running"
  | "stopped"
  | "other";

export function ResourcesPage() {
  const navigate = useNavigate();

  const [resources, setResources] = useState<
    CloudResource[]
  >([]);

  const [searchText, setSearchText] =
    useState("");

  const [stateFilter, setStateFilter] =
    useState<StateFilter>("all");

  const [
    complianceFilter,
    setComplianceFilter,
  ] = useState<ComplianceFilter>("all");

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] = useState("");

  const loadResources = useCallback(
    async () => {
      setIsLoading(true);
      setError("");

      try {
        const response = await apiRequest<
          CloudResource[]
        >("/api/resources/");

        setResources(response);
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
            : "Resources load nahi ho sake.",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [navigate],
  );

 useEffect(() => {
  void loadResources();

  const intervalId = window.setInterval(() => {
    void loadResources();
  }, 30000);

  return () => {
    window.clearInterval(intervalId);
  };
}, [loadResources]);

  const filteredResources = useMemo(() => {
    const normalizedSearch =
      searchText.trim().toLowerCase();

    return resources.filter((resource) => {
      const state = (
        resource.state ?? ""
      ).toLowerCase();

      const searchableText = [
        resource.resource_id,
        resource.name,
        resource.instance_type,
        resource.owner_email,
        resource.project_name,
        resource.environment,
        resource.region,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch =
        normalizedSearch.length === 0 ||
        searchableText.includes(
          normalizedSearch,
        );

      const matchesState =
        stateFilter === "all" ||
        (stateFilter === "running" &&
          state === "running") ||
        (stateFilter === "stopped" &&
          state === "stopped") ||
        (stateFilter === "other" &&
          state !== "running" &&
          state !== "stopped");

      const matchesCompliance =
        complianceFilter === "all" ||
        (complianceFilter === "compliant" &&
          resource.is_compliant) ||
        (complianceFilter ===
          "non-compliant" &&
          !resource.is_compliant);

      return (
        matchesSearch &&
        matchesState &&
        matchesCompliance
      );
    });
  }, [
    resources,
    searchText,
    stateFilter,
    complianceFilter,
  ]);

  /*
   * Filtering resources change hone par hi dobara
   * calculate hogi. useMemo calculated value ko
   * dependencies ke beech cache karta hai.
   */
  const summary = useMemo(
    () => ({
      total: resources.length,

      running: resources.filter(
        (resource) =>
          resource.state?.toLowerCase() ===
          "running",
      ).length,

      stopped: resources.filter(
        (resource) =>
          resource.state?.toLowerCase() ===
          "stopped",
      ).length,

      nonCompliant: resources.filter(
        (resource) =>
          !resource.is_compliant,
      ).length,
    }),
    [resources],
  );

  if (isLoading) {
    return (
      <div className="loading-card">
        Loading cloud resources...
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-card">
        <h2>Resources unavailable</h2>
        <p>{error}</p>

        <button
          onClick={() =>
            void loadResources()
          }
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <main className="resources-page">
      <header className="page-header">
        <div>
          <span className="eyebrow">
            Inventory
          </span>

          <h1>Cloud Resources</h1>

          <p>
            Synced AWS resources, ownership and
            governance status.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={() =>
            void loadResources()
          }
        >
          Refresh inventory
        </button>
      </header>

      <section className="compact-metric-grid">
        <article className="compact-metric-card">
          <span>Total</span>
          <strong>{summary.total}</strong>
        </article>

        <article className="compact-metric-card">
          <span>Running</span>
          <strong className="positive-text">
            {summary.running}
          </strong>
        </article>

        <article className="compact-metric-card">
          <span>Stopped</span>
          <strong>{summary.stopped}</strong>
        </article>

        <article className="compact-metric-card">
          <span>Non-compliant</span>
          <strong className="danger-text">
            {summary.nonCompliant}
          </strong>
        </article>
      </section>

      <section className="content-card resource-table-card">
        <div className="resource-toolbar">
          <input
            className="search-input"
            type="search"
            value={searchText}
            onChange={(event) =>
              setSearchText(
                event.target.value,
              )
            }
            placeholder="Search ID, name, owner or project..."
          />

          <select
            className="filter-select"
            value={stateFilter}
            onChange={(event) =>
              setStateFilter(
                event.target
                  .value as StateFilter,
              )
            }
          >
            <option value="all">
              All states
            </option>

            <option value="running">
              Running
            </option>

            <option value="stopped">
              Stopped
            </option>

            <option value="other">
              Other states
            </option>
          </select>

          <select
            className="filter-select"
            value={complianceFilter}
            onChange={(event) =>
              setComplianceFilter(
                event.target
                  .value as ComplianceFilter,
              )
            }
          >
            <option value="all">
              All compliance
            </option>

            <option value="compliant">
              Compliant
            </option>

            <option value="non-compliant">
              Non-compliant
            </option>
          </select>
        </div>

        <div className="table-result-count">
          Showing {filteredResources.length} of{" "}
          {resources.length} resources
        </div>

        {filteredResources.length === 0 ? (
          <div className="empty-state">
            Filter ke according koi resource
            nahi mila.
          </div>
        ) : (
          <div className="table-scroll">
            <table className="resource-table">
              <thead>
                <tr>
                  <th>Resource</th>
                  <th>State</th>
                  <th>Configuration</th>
                  <th>Ownership</th>
                  <th>Compliance</th>
                  <th>Last synced</th>
                </tr>
              </thead>

              <tbody>
                {filteredResources.map(
                  (resource) => (
                    <tr key={resource.id}>
                      <td>
                        <div className="resource-primary">
                          <strong>
                            {resource.name ||
                              "Unnamed resource"}
                          </strong>

                          <code>
                            {
                              resource.resource_id
                            }
                          </code>

                          <span>
                            {resource.region}
                          </span>
                        </div>
                      </td>

                      <td>
                        <span
                          className={`state-badge state-${(
                            resource.state ??
                            "unknown"
                          ).toLowerCase()}`}
                        >
                          {resource.state ??
                            "unknown"}
                        </span>
                      </td>

                      <td>
                        <div className="table-stack">
                          <strong>
                            {resource.instance_type ??
                              "N/A"}
                          </strong>

                          <span>
                            {resource.availability_zone ??
                              "No AZ"}
                          </span>
                        </div>
                      </td>

                      <td>
                        <div className="table-stack">
                          <strong>
                            {resource.project_name ??
                              "No project"}
                          </strong>

                          <span>
                            {resource.owner_email ??
                              "No owner"}
                          </span>

                          <span>
                            {resource.environment ??
                              "No environment"}
                          </span>
                        </div>
                      </td>

                      <td>
                        {resource.is_compliant ? (
                          <span className="compliance-badge compliant">
                            Compliant
                          </span>
                        ) : (
                          <div className="missing-tags">
                            <span className="compliance-badge non-compliant">
                              Non-compliant
                            </span>

                            <div className="tag-list">
                              {(
                                resource.missing_tags ??
                                []
                              ).map((tag) => (
                                <span
                                  className="tag-pill"
                                  key={tag}
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </td>

                      <td>
                        {resource.last_synced_at
                          ? new Date(
                              resource.last_synced_at,
                            ).toLocaleString(
                              "en-IN",
                            )
                          : "Never"}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}