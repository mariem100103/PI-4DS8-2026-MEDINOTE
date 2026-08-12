import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContextHybrid.jsx";

/**
 * @param {{ children: import("react").ReactNode; adminOnly?: boolean }} props
 */
export default function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (adminOnly && !isAdmin) {
    return <Navigate to="/persona" replace />;
  }
  return children;
}
