import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute() {
  const { user, loading } = useAuth();
  if (loading) return <div className="grid min-h-screen place-items-center text-muted">Loading MotionGuard...</div>;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

