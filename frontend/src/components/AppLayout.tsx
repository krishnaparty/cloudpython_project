import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router";

import { removeToken } from "../auth/auth";

const navigationItems = [
  {
    path: "/dashboard",
    label: "Overview",
  },
  {
    path: "/resources",
    label: "Cloud Resources",
  },
  {
    path: "/recommendations",
    label: "Recommendations",
  },
  {
    path: "/anomalies",
    label: "ML Anomalies",
  },
  {
    path: "/forecast",
    label: "Cost Forecast",
  },
];

export function AppLayout() {
  const navigate = useNavigate();

  function logout() {
    removeToken();

    navigate("/login", {
      replace: true,
    });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">CC</div>

          <div>
            <strong>CloudCampus</strong>
            <span>AI Platform</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navigationItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                isActive
                  ? "nav-link nav-link-active"
                  : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            className="logout-button"
            onClick={logout}
          >
            Sign out
          </button>
        </div>
      </aside>

      <section className="app-main">
        <header className="topbar">
          <div>
            <strong>
              AWS Governance Platform
            </strong>

            <span>
              Monitoring · Optimization · AI
            </span>
          </div>

          <div className="environment-badge">
            ap-south-1
          </div>
        </header>

        <div className="page-content">
          <Outlet />
        </div>
      </section>
    </div>
  );
}
