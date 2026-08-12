import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContextHybrid.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import logoMedinote from "../assets/logoo.png";
import LanguageToggle from "../components/LanguageToggle.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";

const REMEMBER_EMAIL_KEY = "alia_crm_remember_email";

export default function LoginPage() {
  const { t } = useLanguage();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(REMEMBER_EMAIL_KEY);
      if (saved) setEmail(saved);
    } catch {
      /* ignore */
    }
  }, []);

  const from =
    location.state?.from?.pathname && location.state.from.pathname !== "/login"
      ? location.state.from.pathname
      : null;

  function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    const result = login(email, password);
    setSubmitting(false);

    if (!result.ok) {
      setError(t(`auth.error.${result.error}`));
      return;
    }

    try {
      if (remember) {
        localStorage.setItem(REMEMBER_EMAIL_KEY, email.trim());
      } else {
        localStorage.removeItem(REMEMBER_EMAIL_KEY);
      }
    } catch {
      /* ignore */
    }

    if (from) {
      navigate(from, { replace: true });
      return;
    }
    navigate(result.user.role === "admin" ? "/admin/dashboard" : "/persona", {
      replace: true,
    });
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-[#f0f9ff] to-[#eef2ff] px-4 py-10 font-sans dark:from-slate-950 dark:to-slate-900">
      <div className="absolute right-4 top-4 flex flex-wrap items-center justify-end gap-2">
        <ThemeToggle compact />
        <LanguageToggle />
      </div>

      <div className="w-full max-w-md rounded-xl border border-slate-100 bg-white p-8 shadow-[0_4px_24px_rgba(0,0,0,0.06)] dark:border-slate-700 dark:bg-slate-800/90 dark:shadow-[0_4px_24px_rgba(0,0,0,0.35)]">
        <div className="mb-8 flex flex-col items-center text-center">
          <img
            src={logoMedinote}
            alt="MediNote"
            width={72}
            height={72}
            className="h-16 w-16 object-contain"
          />
          <h1 className="mt-4 text-xl font-bold text-slate-900 dark:text-slate-50">
            ALIA CRM
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {t("auth.login_subtitle")}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <p
              className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-950/40 dark:text-rose-300"
              role="alert"
            >
              {error}
            </p>
          )}

          <div>
            <label
              htmlFor="login-email"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {t("auth.email")}
            </label>
            <input
              id="login-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-slate-900 outline-none ring-[#2563eb]/30 focus:border-[#2563eb] focus:ring-2 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100 dark:placeholder:text-slate-500"
            />
          </div>

          <div>
            <label
              htmlFor="login-password"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {t("auth.password")}
            </label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-slate-900 outline-none ring-[#2563eb]/30 focus:border-[#2563eb] focus:ring-2 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100"
            />
          </div>

          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="rounded border-slate-300 text-[#2563eb] focus:ring-[#2563eb]"
            />
            {t("auth.remember")}
          </label>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-[#2563eb] py-3 text-sm font-semibold text-white shadow-md transition hover:bg-blue-700 disabled:opacity-60"
          >
            {submitting ? t("common.loading") : t("auth.login")}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-300">
          {t("auth.noAccount")}{" "}
          <Link
            to="/register"
            className="font-semibold text-[#2563eb] hover:underline dark:text-sky-400"
          >
            {t("auth.register")}
          </Link>
        </p>

        <p className="mt-4 text-center">
          <Link
            to="/"
            className="text-sm text-slate-500 hover:text-[#2563eb] dark:text-slate-400 dark:hover:text-sky-400"
          >
            ← {t("common.backHome")}
          </Link>
        </p>

        <p className="mt-6 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:bg-slate-900/50 dark:text-slate-400">
          {t("auth.demo_hint")}
        </p>
      </div>
    </div>
  );
}
