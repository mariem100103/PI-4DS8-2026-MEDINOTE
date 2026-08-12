import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContextHybrid.jsx";

/** Pages connexion / inscription : redirige si déjà connecté. */
export default function GuestRoute({ children }) {
  const { isAuthenticated, isAdmin } = useAuth();

  if (isAuthenticated) {
    return <Navigate to={isAdmin ? "/admin/dashboard" : "/persona"} replace />;
  }
  return children;
}
