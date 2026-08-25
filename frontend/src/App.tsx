import {
  lazy,
  Suspense,
} from "react";

import {
  Navigate,
  Route,
  Routes,
} from "react-router";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";


const LoginPage = lazy(() =>
  import("./pages/LoginPage").then(
    (module) => ({
      default: module.LoginPage,
    }),
  ),
);


const DashboardPage = lazy(() =>
  import("./pages/DashboardPage").then(
    (module) => ({
      default: module.DashboardPage,
    }),
  ),
);


const ResourcesPage = lazy(() =>
  import("./pages/ResourcesPage").then(
    (module) => ({
      default: module.ResourcesPage,
    }),
  ),
);


const RecommendationsPage = lazy(() =>
  import(
    "./pages/RecommendationsPage"
  ).then((module) => ({
    default: module.RecommendationsPage,
  })),
);


const AnomaliesPage = lazy(() =>
  import("./pages/AnomaliesPage").then(
    (module) => ({
      default: module.AnomaliesPage,
    }),
  ),
);


const CostForecastPage = lazy(() =>
  import("./pages/CostForecastPage").then(
    (module) => ({
      default: module.CostForecastPage,
    }),
  ),
);


function App() {
  return (
    <Suspense
      fallback={
        <div className="center-message">
          Loading CloudCampus AI...
        </div>
      }
    >
      <Routes>
        <Route
          path="/login"
          element={<LoginPage />}
        />

        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route
            path="/dashboard"
            element={<DashboardPage />}
          />

          <Route
            path="/resources"
            element={<ResourcesPage />}
          />

          <Route
            path="/recommendations"
            element={
              <RecommendationsPage />
            }
          />

          <Route
            path="/anomalies"
            element={<AnomaliesPage />}
          />

          <Route
            path="/forecast"
            element={<CostForecastPage />}
          />
        </Route>

        <Route
          path="/"
          element={
            <Navigate
              to="/dashboard"
              replace
            />
          }
        />

        <Route
          path="*"
          element={
            <Navigate
              to="/dashboard"
              replace
            />
          }
        />
      </Routes>
    </Suspense>
  );
}


export default App;