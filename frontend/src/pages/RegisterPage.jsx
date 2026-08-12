import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContextHybrid.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import logoMedinote from "../assets/logoo.png";
import LanguageToggle from "../components/LanguageToggle.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";

export default function RegisterPage() {
  const { t } = useLanguage();
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [role, setRole] = useState("delegate");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (password !== password2) {
      setError(t("auth.error.password_mismatch"));
      return;
    }
    if (password.length < 4) {
      setError(t("auth.error.password_short"));
      return;
    }

    setSubmitting(true);
    const result = register(name, email, password, role);
    setSubmitting(false);

    if (!result.ok) {
      setError(t(`auth.error.${result.error}`));
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
            {t("auth.register_subtitle")}
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
              htmlFor="reg-name"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {t("auth.name")}
            </label>
            <input
              id="reg-name"
              type="text"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-slate-900 outline-none ring-[#2563eb]/30 focus:border-[#2563eb] focus:ring-2 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100"
            />
          </div>

          <div>
            <label
              htmlFor="reg-email"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {t("auth.email")}
            </label>
            <input
              id="reg-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-slate-900 outline-none ring-[#2563eb]/30 focus:border-[#2563eb] focus:ring-2 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100"
            />
          </div>

          <div>
            <label
              htmlFor="reg-role"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {t("auth.role")}
            </label>
            <select
              id="reg-role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-slate-900 outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#2563eb]/30 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100"
            >
              <option value="delegate">{t("auth.role.delegate")}</option>
              <option value="admin">{t("auth.role.admin")}</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="reg-password"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {t("auth.password")}
            </label>
            <input
              id="reg-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={4}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-slate-900 outline-none ring-[#2563eb]/30 focus:border-[#2563eb] focus:ring-2 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100"
            />
          </div>

          <div>
            <label
              htmlFor="reg-password2"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              {t("auth.password_confirm")}
            </label>
            <input
              id="reg-password2"
              type="password"
              autoComplete="new-password"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-slate-900 outline-none ring-[#2563eb]/30 focus:border-[#2563eb] focus:ring-2 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-[#2563eb] py-3 text-sm font-semibold text-white shadow-md transition hover:bg-blue-700 disabled:opacity-60"
          >
            {submitting ? t("common.loading") : t("auth.register_submit")}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-300">
          {t("auth.hasAccount")}{" "}
          <Link
            to="/login"
            className="font-semibold text-[#2563eb] hover:underline dark:text-sky-400"
          >
            {t("auth.login")}
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
      </div>
    </div>
  );
}
