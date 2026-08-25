import type { ReactNode } from "react";
import { Navigate } from "react-router";

import { isAuthenticated } from "../auth/auth";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({
  children,
}: ProtectedRouteProps) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return children;
}