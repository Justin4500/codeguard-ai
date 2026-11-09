import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Spinner } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/useAuth";

export default function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-muted">
        <Spinner className="h-5 w-5" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
