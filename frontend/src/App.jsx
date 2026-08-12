import React from "react";
import {
  Routes,
  Route,
  Navigate,
  useLocation,
  Link,
  useNavigate,
} from "react-router-dom";
import { Home, LayoutDashboard, LogOut, User } from "lucide-react";

import logoMedinote from "./assets/logoo.png";
import RapportExtractionPage from "./pages/RapportExtractionPage.jsx";
import RapportHistoriquePage from "./pages/RapportHistoriquePage.jsx";
import CorrecteurPage from "./pages/CorrecteurPage";
import CoachingPage from "./pages/CoachingPage";
import ChatbotPage from "./pages/ChatbotPage";
import ExtractionPage from "./pages/ExtractionPage";
import PersonaCard from "./pages/PersonaCard";
import HeatMap from "./pages/HeatMap";
import FollowUp from "./pages/FollowUp";
import HomePage from "./pages/HomePage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import AdminDashboardPage from "./pages/AdminDashboardPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import GuestRoute from "./components/GuestRoute.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import LanguageToggle from "./components/LanguageToggle.jsx";
import ThemeToggle from "./components/ThemeToggle.jsx";
import AppSidebar from "./components/AppSidebar.jsx";
import { useLanguage } from "./context/LanguageContext.jsx";
import { useAuth } from "./context/AuthContextHybrid.jsx";

function Navbar() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, isAdmin } = useAuth();

  return (
    <nav className="navbar navbar-top">
      <div className="navbar-left navbar-left-compact">
        <Link to="/" className="navbar-logo">
          <img
            src={logoMedinote}
            alt="MediNote"
            width={44}
            height={44}
            className="h-11 w-11 shrink-0 rounded-xl object-contain"
          />

          <div className="navbar-logo-text">
            <span className="navbar-title">MediNote</span>
            <span className="navbar-subtitle">CRM Médical · IA</span>
          </div>
        </Link>
      </div>

      <div className="navbar-right">
        {isAuthenticated && (
          <div className="navbar-user-section">
            <div className="navbar-quick-actions">
              <button
                type="button"
                onClick={() => navigate("/")}
                className="quick-action-btn"
                title={t("nav.home")}
              >
                <Home className="h-4 w-4" aria-hidden />
                <span className="hidden sm:inline">{t("nav.home")}</span>
              </button>

              <button
                type="button"
                onClick={() => navigate("/profile")}
                className="quick-action-btn"
                title={t("nav.profile")}
              >
                <User className="h-4 w-4" aria-hidden />
                <span className="hidden sm:inline">{t("nav.profile")}</span>
              </button>

              {isAdmin && (
                <button
                  type="button"
                  onClick={() => navigate("/admin/dashboard")}
                  className="quick-action-btn admin"
                  title={t("nav.dashboard")}
                >
                  <LayoutDashboard className="h-4 w-4" aria-hidden />
                  <span className="hidden sm:inline">{t("nav.dashboard")}</span>
                </button>
              )}
            </div>

            <div className="navbar-user-info">
              <span className="user-name" title={user?.email ?? ""}>
                {user?.name ?? user?.email}
              </span>
            </div>

            <div className="navbar-actions">
              <ThemeToggle className="navbar-control shrink-0" compact />
              <LanguageToggle className="navbar-control shrink-0" />

              <button
                type="button"
                onClick={() => {
                  logout();
                  navigate("/login", { replace: true });
                }}
                className="logout-btn"
                title={t("auth.logout")}
              >
                <LogOut className="h-4 w-4" aria-hidden />
                <span className="hidden sm:inline">{t("auth.logout")}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

function App() {
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const path = location.pathname;
  const hideNavbar =
    path === "/" ||
    path === "/login" ||
    path === "/register" ||
    path === "/admin";

  const showSidebar = !hideNavbar && isAuthenticated;

  return (
    <div className="app app-layout">
      {!hideNavbar && <Navbar />}

      <div
        className={
          hideNavbar
            ? "flex min-h-0 flex-1 flex-col"
            : "app-body flex min-h-0 flex-1 flex-row"
        }
      >
        {showSidebar && <AppSidebar />}
        <main
          className={
            hideNavbar
              ? "min-h-screen w-full flex-1"
              : "app-main min-h-0 min-w-0 flex-1"
          }
        >
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <RegisterPage />
              </GuestRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute adminOnly>
                <Navigate to="/admin/dashboard" replace />
              </ProtectedRoute>
            }
          />

          <Route
            path="/correcteur"
            element={
              <ProtectedRoute>
                <CorrecteurPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/extraction"
            element={
              <ProtectedRoute>
                <ExtractionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/coaching"
            element={
              <ProtectedRoute>
                <CoachingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chatbot"
            element={
              <ProtectedRoute>
                <ChatbotPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/rapports"
            element={
              <ProtectedRoute>
                <RapportExtractionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rapport/:reportId/modifier"
            element={
              <ProtectedRoute>
                <RapportExtractionPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rapports/historique"
            element={
              <ProtectedRoute>
                <RapportHistoriquePage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/persona"
            element={
              <ProtectedRoute>
                <PersonaCard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/heatmap"
            element={
              <ProtectedRoute>
                <HeatMap />
              </ProtectedRoute>
            }
          />
          <Route
            path="/followup"
            element={
              <ProtectedRoute>
                <FollowUp />
              </ProtectedRoute>
            }
          />

          {/* Routes Admin */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute adminOnly>
                <AdminDashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Routes Profile */}
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
